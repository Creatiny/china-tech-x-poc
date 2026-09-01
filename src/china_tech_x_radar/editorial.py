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

GENERIC_ENTITIES = {"china", "chinese"}


def load_editorial_config(root: Path) -> dict[str, Any]:
    with (root / "config" / "editorial.toml").open("rb") as f:
        return tomllib.load(f)


def utc_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


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
    # P1 must always pass the cheap gate; score alone must never create a flood of P1 publish packets.
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


def final_prompt(signal: dict[str, Any]) -> str:
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

Use web search only as needed to verify facts and find one strong current X target post about this exact event. Choose REPLY, POST, or SKIP. Optimize for relevant follower growth, not output quota.

Decision rules:
- REPLY when a strong current target exists, timing is still useful, and @KennyChinaTech can add non-generic value.
- POST when the event deserves owned distribution and no better live target is verified.
- SKIP when weak, late, off-positioning, duplicative, or there is no differentiated angle.

If REPLY or POST, write FINAL English copy ready to paste into X. Make it conversational, concise, specific and human. No AI clichés, no headings inside the copy, no generic praise, no filler, no forced hashtags, no em-dash-heavy prose. Add a concrete China-specific fact, comparison, technical explanation, data point, or second-order global implication. Do not overclaim.

For POST, keep the main copy native-first; do NOT put the source URL in final_copy. Provide source_url separately.
For REPLY, target_url must be a verified direct X status URL; if you cannot verify one, do not return REPLY.

Visual decision:
- REPLY: normally image_mode NONE.
- POST: use EDITORIAL_CARD only when 2-3 verified facts/data points make a visual genuinely useful; otherwise NONE.
- If EDITORIAL_CARD, image_title <=70 chars and each of 2-3 image_points <=55 chars. Use verified facts only.

Return ONLY one-line JSON with exactly these keys:
{{"decision":"REPLY|POST|SKIP","confidence":0.0,"reason":"short editorial reason","target_url":null,"target_account":null,"final_copy":null,"source_url":null,"angle_type":"CHINA_CONTEXT|GLOBAL_IMPLICATION|COMPARISON|DATA_POINT|TECHNICAL_EXPLANATION|CONTRARIAN|FACT_ADD|OTHER","urgency_minutes":0,"image_mode":"NONE|EDITORIAL_CARD","image_title":null,"image_points":[],"publish_note":"one short direct instruction"}}'''


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
    return packet
