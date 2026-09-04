from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import tempfile
import textwrap
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

GENERIC_ENTITIES = {"china", "chinese"}

BANNED_AI_PHRASES = (
    "one caveat",
    "one data caveat",
    "the bigger signal",
    "the bigger question",
    "what caught my eye",
    "worth noting",
    "it is worth noting",
    "this suggests that",
    "this points to",
    "the key test is",
    "the key test is not",
    "this isn't just",
    "this is not just",
    "in other words",
    "the real story",
    "one concrete datapoint missing",
)


def load_editorial_config(root: Path) -> dict[str, Any]:
    with (root / "config" / "editorial.toml").open("rb") as f:
        return tomllib.load(f)


def utc_date() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()


def model_usage_today(con: sqlite3.Connection, budget_revision: str | None = None) -> dict[str, int]:
    where = "usage_date=?"
    params: list[Any] = [utc_date()]
    if budget_revision is not None:
        where += " AND budget_revision=?"
        params.append(budget_revision)
    row = con.execute(
        f"""SELECT COUNT(*) calls,
                  SUM(CASE WHEN purpose='GATE' THEN 1 ELSE 0 END) gate_calls,
                  SUM(CASE WHEN purpose='FINAL' THEN 1 ELSE 0 END) final_calls,
                  COALESCE(SUM(tokens_used),0) tokens
           FROM model_usage WHERE {where}""",
        params,
    ).fetchone()
    return {
        "calls": int(row["calls"] or 0),
        "gate_calls": int(row["gate_calls"] or 0),
        "final_calls": int(row["final_calls"] or 0),
        "tokens": int(row["tokens"] or 0),
    }


def _reserve_model_call(con: sqlite3.Connection, cfg: dict[str, Any], purpose: str, model: str) -> int:
    revision = str(cfg.get("budget_revision") or "legacy")
    max_tokens = int(cfg.get("max_tokens_per_day", 180000))
    max_calls = int(cfg.get("max_gate_calls_per_day" if purpose == "GATE" else "max_final_calls_per_day", 8 if purpose == "GATE" else 5))
    reserve = int(cfg.get("gate_token_reserve" if purpose == "GATE" else "final_token_reserve", 6000 if purpose == "GATE" else 30000))
    call_key = "gate_calls" if purpose == "GATE" else "final_calls"

    # BEGIN IMMEDIATE makes the check+reservation atomic even if two launchd/manual runs overlap.
    con.execute("BEGIN IMMEDIATE")
    try:
        usage = model_usage_today(con, revision)
        if usage[call_key] >= max_calls or usage["tokens"] + reserve > max_tokens:
            con.rollback()
            raise RuntimeError(
                f"editorial_budget_exhausted:{purpose}:revision={revision}:calls={usage[call_key]}/{max_calls}:tokens={usage['tokens']}+{reserve}/{max_tokens}"
            )
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        cur = con.execute(
            """INSERT INTO model_usage(usage_date,used_at,purpose,model,budget_revision,tokens_used,success,error)
               VALUES(?,?,?,?,?,?,-1,NULL)""",
            (utc_date(), now, purpose, model, revision, reserve),
        )
        reservation_id = int(cur.lastrowid)
        con.commit()
        return reservation_id
    except Exception:
        if con.in_transaction:
            con.rollback()
        raise


def _parse_tokens(stderr: str) -> int | None:
    m = re.search(r"tokens used\s*\n\s*([0-9,]+)", stderr)
    return int(m.group(1).replace(",", "")) if m else None


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        obj = json.loads(text[start : end + 1])
        if isinstance(obj, dict):
            return obj
    raise ValueError("Codex final message was not a JSON object")


def _run_codex(
    con: sqlite3.Connection,
    root: Path,
    cfg: dict[str, Any],
    purpose: str,
    prompt: str,
    *,
    search: bool,
) -> dict[str, Any]:
    codex = str(cfg.get("codex_path") or "/Users/jh/.codex/plugins/.plugin-appserver/codex")
    model = str(cfg.get("model") or "gpt-5.6-luna")
    effort = str(cfg.get("reasoning_effort") or "low")
    timeout = int(cfg.get("call_timeout_seconds", 90))
    reservation_id = _reserve_model_call(con, cfg, purpose, model)
    try:
        with tempfile.TemporaryDirectory(prefix="china-tech-editorial-") as td:
            out_path = Path(td) / "last.json"
            cmd = [codex]
            if search:
                cmd.append("--search")
            cmd += [
                "-a", "never", "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
                "--sandbox", "read-only", "-m", model, "-c", f'model_reasoning_effort="{effort}"',
                "-C", str(root), "-o", str(out_path), prompt,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            final = out_path.read_text(encoding="utf-8", errors="replace") if out_path.exists() else proc.stdout
            tokens = _parse_tokens(proc.stderr)
            con.execute(
                "UPDATE model_usage SET tokens_used=?,success=?,error=? WHERE id=?",
                (tokens if tokens is not None else 0, 1 if proc.returncode == 0 else 0, None if proc.returncode == 0 else proc.stderr[-1200:], reservation_id),
            )
            con.commit()
            if proc.returncode != 0:
                raise RuntimeError(f"codex_{purpose.lower()}_failed:{proc.stderr[-500:]}")
            return _extract_json(final)
    except Exception as exc:
        con.execute("UPDATE model_usage SET success=0,error=? WHERE id=?", (f"{type(exc).__name__}: {exc}"[:1200], reservation_id))
        con.commit()
        raise


def _specific_entity_present(signal: dict[str, Any]) -> bool:
    reason = str(signal.get("reason") or "")
    m = re.search(r"entity=([^;]+)", reason)
    return bool(m and m.group(1).strip().casefold() not in GENERIC_ENTITIES)


def should_direct_final(signal: dict[str, Any], cfg: dict[str, Any]) -> bool:
    # Verified X targets are already narrow, timely reply candidates; skip the generic-news gate.
    if str(signal.get("target_mode") or "") == "VERIFIED_X_TARGET":
        return int(signal.get("score") or 0) >= int(cfg.get("p1_reply_min_score", 7)) and str(signal.get("priority") or "").upper() in {"P0", "P1"}
    # P1 news candidates still pass the cheap gate to avoid flooding owned-post review.
    if str(signal.get("priority") or "").upper() != "P0":
        return False
    topic = str(signal.get("topic") or "").casefold()
    tech_topics = {"ai", "llm", "agent", "benchmark", "chip", "gpu", "semiconductor", "memory", "dram", "nand", "robot", "robotics", "humanoid", "ev", "battery", "autonomous"}
    return int(signal.get("score") or 0) >= int(cfg.get("p0_direct_final_min_score", 10)) and (topic in tech_topics or _specific_entity_present(signal))


def gate_prompt(signal: dict[str, Any]) -> str:
    return f'''Editorial gate only for @KennyChinaTech. Positioning: China Tech Intelligence — China AI, semiconductors/AI infrastructure, robotics/hardware, EV/advanced manufacturing, and global implications of technology. Current stage: 4->100 followers, reply-led cold start.

Return ONLY JSON {{"decision":"PASS|SKIP","confidence":0.0,"reason":"short concrete reason"}}. Do not browse. Do not invent facts. Macro economy, general geopolitics, airlines, politics, or generic China business without a material technology/advanced-manufacturing angle must be SKIP.

Title: {signal.get('title','')}
Excerpt: {signal.get('excerpt','')}
Source: {signal.get('source_name','')}
Published: {signal.get('published_at') or 'unknown'}
Classifier: {signal.get('reason','')}
Topic: {signal.get('topic') or 'unknown'}'''


def language_gate_violations(packet: dict[str, Any]) -> list[str]:
    decision = str(packet.get("decision") or "").upper()
    if decision not in {"REPLY", "POST"}:
        return []
    copy = str(packet.get("final_copy") or "").strip()
    if not copy:
        return ["missing_copy"]

    lowered = copy.casefold()
    violations = [f"banned_phrase:{phrase}" for phrase in BANNED_AI_PHRASES if phrase in lowered]
    word_count = len(re.findall(r"\b[\w’'-]+\b", copy))
    max_words = 80 if decision == "REPLY" else 130
    if word_count > max_words:
        violations.append(f"too_long:{word_count}>{max_words}")
    if copy.count("—") > 1:
        violations.append("em_dash_heavy")
    if re.search(r"(?im)^\s*(reply|post|analysis|takeaway|conclusion)\s*:", copy):
        violations.append("label_inside_copy")
    if decision == "REPLY":
        group = str(packet.get("content_group") or "").upper()
        if group not in {"A_NEWS_FACT", "B_OPINION_VALUE"}:
            violations.append("missing_content_group")
        if group == "B_OPINION_VALUE" and not str(packet.get("core_position") or "").strip():
            violations.append("b_group_missing_core_position")
    return violations

def final_prompt(signal: dict[str, Any]) -> str:
    direct_target = str(signal.get("target_mode") or "") == "VERIFIED_X_TARGET"
    if direct_target:
        target_instruction = (
            f"This candidate is itself a verified direct X target post: {signal.get('canonical_url')}. "
            "Do not search for a different target. Decide REPLY or SKIP only; do not turn this X target into an ORIGINAL POST. "
            "If you choose REPLY, copy this exact URL into target_url and use web search only to verify evidence for the selected A fact contribution or B owner position."
        )
    else:
        target_instruction = "Use web search only as needed to verify facts and find one strong current X target post about this exact event. Choose REPLY, POST, or SKIP."
    return f'''You are the final editorial operator for @KennyChinaTech, an English X account in Stage A (4->100 followers). Positioning: China Tech Intelligence — China AI, semiconductors/AI infrastructure, robotics/hardware, EV/advanced manufacturing, and global implications of China technology.

Candidate priority: {signal.get('priority') or 'unknown'}
Candidate priority: {signal.get('priority') or 'unknown'}
Candidate:
Title: {signal.get('title','')}
Excerpt: {signal.get('excerpt','')}
Published: {signal.get('published_at') or 'unknown'}
Source: {signal.get('source_name','')}
Source URL: {signal.get('canonical_url') or 'unknown'}
Classifier: {signal.get('reason','')}
Topic: {signal.get('topic') or 'unknown'}
Target mode: {signal.get('target_mode') or 'unknown'}

Strategic positioning override: Independent views and practical intelligence on China's AI, chips, robotics, and manufacturing. News is discovery material and evidence, not the account identity.

Content strategy and experiment:
- A_NEWS_FACT is the acquisition/control group: a timely China-side fact, number, scope correction, or industry implication.
- B_OPINION_VALUE is the strategic mainline: a clear personal judgment, disagreement/agreement, missing variable, conditional prediction, practical lesson, or deeper technical/business interpretation.
- Do not assume a China fact is automatically the best contribution. For B, state the actual position first and support it with at most one verified fact.
- If a topic can become a useful guide, comparison, map, framework, entrepreneurship lesson, or deep argument that readers would save, add a concise article_seed. Otherwise return null.

{target_instruction} Optimize for relevant follower growth, bookmarks, profile interest, and future product/business trust, not news coverage or output quota.

Decision rules:
- REPLY when a strong current target exists, timing is still useful, and @KennyChinaTech can add either a qualified A contribution or, preferably, a qualified B contribution.
- POST when the topic deserves owned distribution because it contains an independent thesis or durable practical value. A news summary alone is not enough.
- SKIP when weak, late, off-positioning, duplicative, or there is no differentiated angle.

If REPLY or POST, write FINAL English copy ready to paste into X and obey PROJECT_SPEC.md Section 17 as a mandatory gate. Sound like a knowledgeable person joining a conversation, never a report, press release, analyst note, or AI summary. Lead with the reaction or strongest fact. Use short ordinary words, natural contractions, one main point, and at most two supporting facts. No headings, labels, generic praise, filler, forced hashtags, formal conclusion, forced cleverness, repeated template structure, or more than one em dash.

REPLY must answer the target post's exact claim, read as a continuation of the conversation, use 1-3 short sentences, and stay at or below 80 words. Classify it as A_NEWS_FACT or B_OPINION_VALUE. For B, core_position is mandatory and the English copy must lead with that position rather than a data dump. POST must contain an independent thesis or useful conclusion, use 2-5 short paragraphs, and stay at or below 130 words.

Never use these default phrases: "One caveat", "One data caveat", "The bigger signal", "The bigger question", "What caught my eye", "Worth noting", "It is worth noting", "This suggests that", "This points to", "The key test is", "The key test is not", "This isn't just", "This is not just", "In other words", "The real story", or "One concrete datapoint missing". Avoid contrived "X is new. Y isn't." and repeated "not X, but Y" framing. Read the copy aloud mentally and rewrite it before returning JSON if it does not sound natural. Add a concrete China-specific fact, correction, comparison, technical explanation, data point, or useful global implication. Do not overclaim.

For POST, keep the main copy native-first; do NOT put the source URL in final_copy. Provide source_url separately.
For REPLY, target_url must be a verified direct X status URL; if you cannot verify one, do not return REPLY.

Visual decision:
- REPLY: normally image_mode NONE.
- POST: use EDITORIAL_CARD only when 2-3 verified facts/data points make a visual genuinely useful; otherwise NONE.
- If EDITORIAL_CARD, image_title <=70 chars and each of 2-3 image_points <=55 chars. Use verified facts only.

Return ONLY one-line JSON with exactly these keys:
{{"decision":"REPLY|POST|SKIP","content_group":"A_NEWS_FACT|B_OPINION_VALUE","confidence":0.0,"reason":"short editorial reason","core_position":null,"target_url":null,"target_account":null,"final_copy":null,"source_url":null,"angle_type":"CHINA_CONTEXT|GLOBAL_IMPLICATION|COMPARISON|DATA_POINT|TECHNICAL_EXPLANATION|CONTRARIAN|FACT_ADD|OTHER","article_seed":null,"urgency_minutes":0,"image_mode":"NONE|EDITORIAL_CARD","image_title":null,"image_points":[],"publish_note":"one short direct instruction"}}'''


def enrich_signal(con: sqlite3.Connection, root: Path, signal: dict[str, Any]) -> dict[str, Any]:
    cfg = load_editorial_config(root)
    if not bool(cfg.get("enabled", True)):
        raise RuntimeError("editorial_enrichment_disabled")
    if not should_direct_final(signal, cfg):
        gate = _run_codex(con, root, cfg, "GATE", gate_prompt(signal), search=False)
        if str(gate.get("decision") or "").upper() != "PASS":
            return {"decision": "SKIP", "confidence": gate.get("confidence"), "reason": gate.get("reason"), "gate": gate}
    packet = _run_codex(con, root, cfg, "FINAL", final_prompt(signal), search=True)
    decision = str(packet.get("decision") or "SKIP").upper()
    if decision not in {"POST", "REPLY", "SKIP"}:
        decision = "SKIP"
    packet["decision"] = decision
    violations = language_gate_violations(packet)
    if violations:
        return {
            "decision": "SKIP",
            "confidence": packet.get("confidence"),
            "reason": "language_gate_failed:" + ",".join(violations),
            "source_url": packet.get("source_url"),
            "gate": packet,
        }
    return packet
