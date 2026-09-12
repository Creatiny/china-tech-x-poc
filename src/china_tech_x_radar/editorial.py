from __future__ import annotations

import json
import os
import re
import signal
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
    "the interesting part isn't",
    "the real shift isn't",
    "the biggest takeaway isn't",
    "真正重要的不是",
    "真正值得关注的不是",
    "更大的信号是",
    "更大的问题是",
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
            env = os.environ.copy()
            env["NO_COLOR"] = "1"
            proxy = str(env.get("CHINA_TECH_HTTP_PROXY") or "").strip()
            if proxy:
                env["HTTP_PROXY"] = proxy
                env["HTTPS_PROXY"] = proxy
                env["http_proxy"] = proxy
                env["https_proxy"] = proxy
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, start_new_session=True
            )
            try:
                stdout_text, stderr_text = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                stdout_text, stderr_text = proc.communicate()
                raise TimeoutError(f"codex_timeout:{timeout}s") from exc
            final = out_path.read_text(encoding="utf-8", errors="replace") if out_path.exists() else stdout_text
            tokens = _parse_tokens(stderr_text)
            con.execute(
                "UPDATE model_usage SET tokens_used=?,success=?,error=? WHERE id=?",
                (tokens if tokens is not None else 0, 1 if proc.returncode == 0 else 0, None if proc.returncode == 0 else stderr_text[-1200:], reservation_id),
            )
            con.commit()
            if proc.returncode != 0:
                raise RuntimeError(f"codex_{purpose.lower()}_failed:{stderr_text[-500:]}")
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
    return f'''Editorial gate for @KennyChinaTech.
Audience: people who care about AI technology and how AI becomes real productivity, products, better workflows, lower costs, or new business models.
Core rule: news is material; viewpoint is the product. China-side evidence is a differentiation advantage, not a mandatory topic boundary.

Return ONLY JSON {{"decision":"PASS|SKIP","confidence":0.0,"reason":"short concrete reason"}}. Do not browse. Do not invent facts.
PASS only if the candidate can support at least one of:
- WHAT_I_BELIEVE: a defensible thesis/judgment;
- WHAT_I_LEARNED: a useful lesson from real research/testing/building/operations;
- WHAT_CHANGES: a development that materially changes AI capability, cost, workflow, reliability, product design, business model, or competitive dynamics.
SKIP generic macro/politics/general business, ordinary funding/earnings, headline restatements, generic China news, or AI news with no concrete productivity consequence.

Title: {signal.get('title','')}
Excerpt: {signal.get('excerpt','')}
Source: {signal.get('source_name','')}
Published: {signal.get('published_at') or 'unknown'}
Classifier: {signal.get('reason','')}
Topic: {signal.get('topic') or 'unknown'}'''


def load_spec_guardrails(root: Path) -> str:
    """Freshly read mandatory editorial sections before every final draft."""
    path = root / "PROJECT_SPEC.md"
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"project_spec_unreadable:{exc}") from exc
    parts: list[str] = []
    for section in (19, 20, 23):
        match = re.search(rf"(?ms)^## {section}\. .*?(?=^## \d+\.|\Z)", text)
        if not match:
            raise RuntimeError(f"project_spec_missing_section:{section}")
        parts.append(match.group(0).strip())
    return "\n\n".join(parts)


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
    if decision == "REPLY" and word_count > 60:
        violations.append(f"too_long:{word_count}>60")
    if decision == "REPLY" and re.search(r"[\u3400-\u9fff]", copy) and len(copy) > 140:
        violations.append(f"too_long_zh:{len(copy)}>140")
    bucket = str(packet.get("content_bucket") or "").upper()
    if bucket not in {"WHAT_I_BELIEVE", "WHAT_I_LEARNED", "WHAT_CHANGES"}:
        violations.append("missing_content_bucket")
    if copy.count("—") > 1:
        violations.append("em_dash_heavy")
    if re.search(r"(?im)^\s*(reply|post|analysis|takeaway|conclusion)\s*:", copy):
        violations.append("label_inside_copy")
    return violations

def final_prompt(signal: dict[str, Any], spec_guardrails: str = "") -> str:
    direct_target = str(signal.get("target_mode") or "") == "VERIFIED_X_TARGET"
    if direct_target:
        target_instruction = (
            f"This candidate is itself a verified direct X target post: {signal.get('canonical_url')}. "
            "Do not search for a different target. Decide REPLY or SKIP only; do not turn this X target into an ORIGINAL POST. "
            "If you choose REPLY, copy this exact URL into target_url and use web search only to verify evidence for the reply."
        )
    else:
        target_instruction = "Use web search only as needed to verify facts and find one strong current X target about this exact topic/event. Choose REPLY, POST, or SKIP."
    return f'''You are the final editorial operator for @KennyChinaTech.

Audience: people who follow AI technology and care about turning AI into real productivity.
Positioning: 不报道 AI，判断 AI 正在改变什么。 News is raw material; Kenny's viewpoint is the product.
Original posts are ALWAYS Chinese. Replies MUST follow the verified parent-post language.
China technology is a differentiation source, not a mandatory boundary.

MANDATORY PRE-DRAFT SPEC CHECK:
The following text was freshly read from the current PROJECT_SPEC.md for this draft. Obey it before writing final_copy. If there is any conflict with generic writing habits, the SPEC wins.

{spec_guardrails}

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

Content buckets:
- WHAT_I_BELIEVE: a clear Kenny judgment/thesis.
- WHAT_I_LEARNED: a useful lesson from real research/testing/building/operations.
- WHAT_CHANGES: a development that materially changes capability, cost, workflow, reliability, product design, business model, or competitive dynamics. Even here, a POST still needs a Kenny thesis; a news summary alone is not enough.

Single Reply standard:
- There are no A/B Reply groups.
- A REPLY must add at least one of: a primary-source fact/correction that changes the discussion, a key metric, a corresponding case, a first-hand practice result, or a clear AI→productivity judgment.
- A factual addition is not enough if it is generic or does not strengthen Kenny's identity/follow reason.
- Prefer FIRSTHAND_PRACTICE, THESIS, PRODUCTIVITY_IMPACT, PRIMARY_SOURCE, KEY_NUMBER, or CORRESPONDING_CASE.

OWNER OVERRIDE: Article topics, questions, and theses are selected by Kenny after deep research or validated shorter content. Do not propose, schedule, or derive Article topics from realtime news; article_seed must be null.

{target_instruction}
Optimize for audience fit, useful reaction, profile interest, and follow reason—not news coverage, output quota, or raw impressions.

Decision rules:
- REPLY only when a strong current target exists, timing is useful, and the reply adds one of: primary-source fact, key number/factual correction, corresponding case/comparison, or real practice result.
- POST only when the topic deserves owned distribution and contains a clear thesis + evidence/reasoning + concrete consequence for the target audience.
- SKIP weak, late, duplicative, generic, off-audience, headline-restatement, or me-too commentary.

Language rules:
- POST final_copy MUST be natural Chinese, even if the source is English.
- REPLY MUST follow the parent post language. English target -> English reply. Chinese target -> Chinese reply.

Voice gate:
- sound like Kenny joining a real conversation, never a report, press release, analyst note, or AI summary;
- lead with the judgment, useful fact, or experience;
- one main point, only necessary supporting facts;
- no headings, labels, generic praise, filler, forced hashtags, formal conclusion, forced cleverness, or repeated house templates;
- avoid “The interesting part isn't...”, “The real shift isn't...”, “The biggest takeaway isn't...”, “真正重要的不是X，而是Y”, and repeated not-X-but-Y constructions;
- do not overclaim;
- use the fewest words that preserve the point;
- no setup, recap, throat-clearing, generic praise, or formal conclusion;
- if two drafts mean the same thing, choose the shorter one.

REPLY defaults to one short, conversational sentence. Use a second sentence only when the point would otherwise lose accuracy or useful evidence. Aim for <=35 English words or about <=60 Chinese characters; never add words for completeness. POST should also be as short as the idea allows.

For POST, do NOT put the source URL in final_copy. Provide source_url separately.
For REPLY, target_url must be a verified direct X status URL; if you cannot verify one, do not return REPLY.

Visual decision:
- REPLY: normally NONE.
- POST: EDITORIAL_CARD only when 2-3 verified facts/data points materially improve comprehension.

Return ONLY one-line JSON with exactly these keys:
{{"decision":"REPLY|POST|SKIP","content_bucket":"WHAT_I_BELIEVE|WHAT_I_LEARNED|WHAT_CHANGES","confidence":0.0,"reason":"short editorial reason","core_position":null,"target_url":null,"target_account":null,"final_copy":null,"source_url":null,"angle_type":"PRIMARY_SOURCE|KEY_NUMBER|CORRESPONDING_CASE|FIRSTHAND_PRACTICE|PRODUCTIVITY_IMPACT|THESIS|OTHER","article_seed":null,"urgency_minutes":0,"image_mode":"NONE|EDITORIAL_CARD","image_title":null,"image_points":[],"publish_note":"one short direct instruction"}}'''


def enrich_signal(con: sqlite3.Connection, root: Path, signal: dict[str, Any]) -> dict[str, Any]:
    cfg = load_editorial_config(root)
    if not bool(cfg.get("enabled", True)):
        raise RuntimeError("editorial_enrichment_disabled")
    if not should_direct_final(signal, cfg):
        gate = _run_codex(con, root, cfg, "GATE", gate_prompt(signal), search=False)
        if str(gate.get("decision") or "").upper() != "PASS":
            return {"decision": "SKIP", "confidence": gate.get("confidence"), "reason": gate.get("reason"), "gate": gate}
    spec_guardrails = load_spec_guardrails(root)
    packet = _run_codex(con, root, cfg, "FINAL", final_prompt(signal, spec_guardrails), search=True)
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
