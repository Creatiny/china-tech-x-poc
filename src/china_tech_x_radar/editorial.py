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

from .operating_policy import active, operator_available, paced_limits, lane_for, packet_violations

GENERIC_ENTITIES = {"china", "chinese"}

CANNED_REPLY_OPENERS = (
    "the key ", "the hard part ", "this is the ", "a useful test ", "the most important ",
    "the speed is ", "the ai piece matters", "the displacement story",
    "这其实", "这章的价值在于", "真正重要的是", "重点不是",
)

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
                  SUM(CASE WHEN purpose='HUMANIZE' THEN 1 ELSE 0 END) humanize_calls,
                  COALESCE(SUM(tokens_used),0) tokens
           FROM model_usage WHERE {where}""",
        params,
    ).fetchone()
    return {
        "calls": int(row["calls"] or 0),
        "gate_calls": int(row["gate_calls"] or 0),
        "final_calls": int(row["final_calls"] or 0),
        "humanize_calls": int(row["humanize_calls"] or 0),
        "tokens": int(row["tokens"] or 0),
    }


def _reserve_model_call(con: sqlite3.Connection, cfg: dict[str, Any], purpose: str, model: str) -> int:
    if active(cfg) and not operator_available(cfg):
        raise RuntimeError("operator_asleep")
    cfg = paced_limits(cfg)
    revision = str(cfg.get("budget_revision") or "legacy")
    max_tokens = int(cfg.get("max_tokens_per_day", 180000))
    if purpose == "GATE":
        max_calls = int(cfg.get("max_gate_calls_per_day", 8))
        reserve = int(cfg.get("gate_token_reserve", 6000))
        call_key = "gate_calls"
    elif purpose == "HUMANIZE":
        max_calls = int(cfg.get("max_humanize_calls_per_day", 50))
        reserve = int(cfg.get("humanize_token_reserve", 5000))
        call_key = "humanize_calls"
    else:
        max_calls = int(cfg.get("max_final_calls_per_day", 5))
        reserve = int(cfg.get("final_token_reserve", 30000))
        call_key = "final_calls"

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
    if active(cfg):
        return False  # Cheap editorial qualification now precedes every expensive final draft.
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
Audience: Chinese-speaking developers, independent builders and small teams delivering real work with AI agents and coding tools.
Core rule: news is material; viewpoint is the product. China-side evidence is a differentiation advantage, not a mandatory topic boundary.

Return ONLY JSON {{"decision":"PASS|SKIP","confidence":0.0,"reason":"short concrete reason"}}. Do not browse. Do not invent facts.
PASS only if the candidate can support at least one of:
- WHAT_I_BELIEVE: a defensible thesis/judgment;
- WHAT_I_LEARNED: a useful lesson from real research/testing/building/operations;
- WHAT_CHANGES: a development that materially changes AI capability, cost, workflow, reliability, product design, business model, or competitive dynamics.
SKIP generic macro/politics/general business, ordinary funding/earnings, headline restatements, generic China news, or AI news with no concrete productivity consequence.

Intended lane: {signal.get('operating_lane','legacy')}. English reference material may support a named-subject CHINESE original; do not assess it as an English reply when the lane is POST. A generic caveat without a concrete added fact is SKIP.
Title: {signal.get('title','')}
Excerpt: {signal.get('excerpt','')}
Source: {signal.get('source_name','')}
Published: {signal.get('published_at') or 'unknown'}
Classifier: {signal.get('reason','')}
Topic: {signal.get('topic') or 'unknown'}
Distribution opportunity: {signal.get('distribution_score',0)} | reply acquisition: {signal.get('reply_acquisition_score',0)} | reply surface: {signal.get('reply_surface_score',0)} | observed views: {signal.get('observed_views',0)} | observed competing replies: {signal.get('observed_replies')} | views per existing reply: {signal.get('views_per_reply')} | view velocity/min: {signal.get('view_velocity_per_min',0)} | engagement rate: {signal.get('engagement_rate',0)} | creator feedback: {signal.get('feedback_score',0)} from {signal.get('feedback_samples',0)} reply samples (median impressions {signal.get('feedback_median_impressions')}); clean follower-growth days: {signal.get('feedback_growth_days',0)} / net {signal.get('feedback_follower_gain',0)}'''


def load_spec_guardrails(root: Path) -> str:
    """Freshly read mandatory editorial sections before every final draft."""
    path = root / "PROJECT_SPEC.md"
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"project_spec_unreadable:{exc}") from exc
    parts: list[str] = []
    for section in (2, 4, 19, 20, 23, 33):
        match = re.search(rf"(?ms)^## {section}\. .*?(?=^## \d+\.|\Z)", text)
        if not match:
            raise RuntimeError(f"project_spec_missing_section:{section}")
        parts.append(match.group(0).strip())
    return "\n\n".join(parts)


def require_humanizer_skill(cfg: dict[str, Any]) -> str:
    raw = str(cfg.get("humanizer_skill_path") or "~/.codex/skills/humanizer/SKILL.md")
    path = Path(raw).expanduser()
    if not path.is_file():
        raise RuntimeError(f"humanizer_skill_missing:{path}")
    return str(path)


def load_kenny_voice_profile(root: Path, cfg: dict[str, Any]) -> str:
    raw = str(cfg.get("kenny_voice_path") or "00_Governance/KENNY_VOICE_FINGERPRINT.md")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        raise RuntimeError(f"kenny_voice_profile_missing:{path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise RuntimeError(f"kenny_voice_profile_empty:{path}")
    return text


def _reply_opener_shape(text: str | None) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if not value:
        return ""
    value = re.sub(r"^(?:@[-_A-Za-z0-9]+\s*)+", "", value).strip()
    if re.search(r"[\u3400-\u9fff]", value):
        first = re.split(r"[。！？!?：:]", value, maxsplit=1)[0].strip()
        return first[:24]
    words = value.split()
    return " ".join(words[:7])


def recent_reply_openers(con: sqlite3.Connection, limit: int = 12) -> list[str]:
    rows = con.execute(
        """SELECT json_extract(editorial_packet_json,'$.final_copy') AS copy
             FROM alert
            WHERE status='SENT' AND json_extract(editorial_packet_json,'$.decision')='REPLY'
              AND json_extract(editorial_packet_json,'$.final_copy') IS NOT NULL
            ORDER BY sent_at DESC LIMIT ?""",
        (max(1, int(limit)),),
    ).fetchall()
    out: list[str] = []
    for row in rows:
        shape = _reply_opener_shape(row["copy"])
        if shape and shape.casefold() not in {x.casefold() for x in out}:
            out.append(shape)
    return out


def language_gate_violations(packet: dict[str, Any]) -> list[str]:
    decision = str(packet.get("decision") or "").upper()
    if decision not in {"REPLY", "POST"}:
        return []
    copy = str(packet.get("final_copy") or "").strip()
    if not copy:
        return ["missing_copy"]

    lowered = copy.casefold()
    violations = [f"banned_phrase:{phrase}" for phrase in BANNED_AI_PHRASES if phrase in lowered]
    normalized_open = re.sub(r"^(?:@[-_a-z0-9]+\s*)+", "", lowered).lstrip()
    for opener in CANNED_REPLY_OPENERS:
        if decision == "REPLY" and normalized_open.startswith(opener.casefold()):
            violations.append(f"canned_opener:{opener.strip()}")
            break
    word_count = len(re.findall(r"\b[\w’'-]+\b", copy))
    if decision == "REPLY" and word_count > 45:
        violations.append(f"too_long:{word_count}>45")
    if decision == "REPLY" and re.search(r"[\u3400-\u9fff]", copy) and len(copy) > 100:
        violations.append(f"too_long_zh:{len(copy)}>100")
    if decision == "REPLY" and (";" in copy or "；" in copy):
        violations.append("semicolon_in_reply")
    bucket = str(packet.get("content_bucket") or "").upper()
    if bucket not in {"WHAT_I_BELIEVE", "WHAT_I_LEARNED", "WHAT_CHANGES"}:
        violations.append("missing_content_bucket")
    if copy.count("—") > 1:
        violations.append("em_dash_heavy")
    if re.search(r"(?im)^\s*(reply|post|analysis|takeaway|conclusion)\s*:", copy):
        violations.append("label_inside_copy")
    return violations

def final_prompt(signal: dict[str, Any], spec_guardrails: str = "", humanizer_path: str = "", kenny_voice: str = "", recent_openers: list[str] | None = None) -> str:
    direct_target = str(signal.get("target_mode") or "") == "VERIFIED_X_TARGET"
    if signal.get("operating_lane") == "POST":
        target_instruction = ("This is REFERENCE MATERIAL for a CHINESE original post, not a reply target. "
                              "Decide POST or SKIP only. Do not search for or recommend an English reply. "
                              "The original needs a named subject, one concrete finding and what a small team can do with it.")
    elif direct_target:
        target_instruction = (
            f"This candidate is itself a verified direct X target post: {signal.get('canonical_url')}. "
            "Do not search for a different target. Decide REPLY or SKIP only; do not turn this X target into an ORIGINAL POST. "
            "If you choose REPLY, copy this exact URL into target_url and use web search only to verify evidence for the reply."
        )
    else:
        target_instruction = "Use web search only as needed to verify facts and find one strong current X target about this exact topic/event. Choose REPLY, POST, or SKIP."
    recent_openers = recent_openers or []
    opener_block = "\n".join(f"- {x}" for x in recent_openers) if recent_openers else "- none available"
    return f'''You are the final editorial operator for @KennyChinaTech.

Audience: Chinese-speaking developers, independent builders and small teams using AI agents and coding tools to deliver real work.
Positioning: 实测 AI 怎么帮小团队把事情做成：成本、踩坑、验收和交付。 News is raw material; concrete experience and evidence are the product.
Original posts are ALWAYS Chinese. The automated acquisition lane recommends replies ONLY to Chinese-language parent posts. English primary sources are research material, not an English reply quota.
China technology is a differentiation source, not a mandatory boundary.

MANDATORY PRE-DRAFT SPEC CHECK:
The following text was freshly read from the current PROJECT_SPEC.md for this draft. Obey it before writing final_copy. If there is any conflict with generic writing habits, the SPEC wins.

{spec_guardrails}

MANDATORY HUMANIZER PASS:
Before drafting final_copy, read `{humanizer_path}` in full. Apply it, especially: trust the reader, cut over-explaining, avoid neat AI rhythms, use ordinary spoken language, and leave natural texture. Draft internally, then ask: "What still sounds machine-written here?" Fix that before returning JSON. Do not mention this process in final_copy.

MANDATORY KENNY VOICE FINGERPRINT:
Match this voice profile. Use the negative examples only as things to avoid.

{kenny_voice}

RECENT REPLY OPENINGS TO AVOID REUSING:
{opener_block}
Do not reuse their opening shape, cadence, or stock framing. Do not replace them with another fixed template; let the actual thought determine the opening.

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
Distribution opportunity: {signal.get('distribution_score',0)} | reply acquisition: {signal.get('reply_acquisition_score',0)} | reply surface: {signal.get('reply_surface_score',0)} | observed views: {signal.get('observed_views',0)} | observed competing replies: {signal.get('observed_replies')} | views per existing reply: {signal.get('views_per_reply')} | view velocity/min: {signal.get('view_velocity_per_min',0)} | engagement rate: {signal.get('engagement_rate',0)} | creator feedback: {signal.get('feedback_score',0)} from {signal.get('feedback_samples',0)} reply samples (median impressions {signal.get('feedback_median_impressions')}); clean follower-growth days: {signal.get('feedback_growth_days',0)} / net {signal.get('feedback_follower_gain',0)}

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
For a direct X target, treat distribution opportunity as timing evidence only: a fast-rising post is valuable because it already has audience movement, but virality NEVER compensates for a weak Kenny contribution. Prefer a high-distribution target when Kenny can add a correction, key number, corresponding case, first-hand practice, or sharp AI→productivity judgment.

Decision rules:
- REPLY only when a strong current target exists, timing is useful, and the reply adds one of: primary-source fact, key number/factual correction, corresponding case/comparison, or real practice result.
- POST only when the topic deserves owned distribution and contains a clear thesis + evidence/reasoning + concrete consequence for the target audience.
- SKIP weak, late, duplicative, generic, off-audience, headline-restatement, or me-too commentary.

Language rules:
- POST final_copy MUST be natural Chinese, even if the source is English.
- In this automatic acquisition lane, REPLY targets must be Chinese and the reply must be Chinese. English references may support Chinese originals only.

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

Do not append a generic "needs real testing / verification / reliability" caveat to every topic. It is not information gain by itself.
An added fact must materially change the parent discussion; give the exact fact, result or reproducible check and provenance in added_evidence. Never invent Kenny's experiments.
For POST, name the model/tool/project IN the actual copy, not just metadata. Use two or three short paragraphs when needed: concrete observation, evidence, usable conclusion. An anonymous number or generic industry maxim is SKIP.
REPLY defaults to one short, conversational sentence. Use a second sentence only when the point would otherwise lose accuracy or useful evidence. Aim for <=35 English words or about <=60 Chinese characters; never add words for completeness. POST should also be as short as the idea allows.

For POST, do NOT put the source URL in final_copy. Provide source_url separately.
For REPLY, target_url must be a verified direct X status URL; if you cannot verify one, do not return REPLY.

Visual decision:
- REPLY: normally NONE.
- POST: EDITORIAL_CARD only when 2-3 verified facts/data points materially improve comprehension.

Return ONLY one-line JSON. Include added_evidence as an object with detail and source_url (or local_evidence_path for an actually supplied local source), and subject_name. Required base keys:
{{"decision":"REPLY|POST|SKIP","content_bucket":"WHAT_I_BELIEVE|WHAT_I_LEARNED|WHAT_CHANGES","confidence":0.0,"reason":"short editorial reason","core_position":null,"target_url":null,"target_account":null,"final_copy":null,"source_url":null,"angle_type":"PRIMARY_SOURCE|KEY_NUMBER|CORRESPONDING_CASE|FIRSTHAND_PRACTICE|PRODUCTIVITY_IMPACT|THESIS|OTHER","article_seed":null,"urgency_minutes":0,"image_mode":"NONE|EDITORIAL_CARD","image_title":null,"image_points":[],"publish_note":"one short direct instruction"}}'''


def humanize_copy_prompt(signal: dict[str, Any], packet: dict[str, Any], humanizer_path: str, kenny_voice: str, recent_openers: list[str]) -> str:
    opener_block = "\n".join(f"- {x}" for x in recent_openers) if recent_openers else "- none"
    return f'''Rewrite only the publishable copy below so it sounds like Kenny, not an AI analyst.

Read `{humanizer_path}` in full first. Then follow this Kenny voice profile:

{kenny_voice}

Parent/source text:
{signal.get("excerpt") or signal.get("title") or ""}

Current draft:
{packet.get("final_copy") or ""}

Recent opening shapes to avoid:
{opener_block}

Hard rules:
- Preserve the original stance and factual meaning. Do not invent or strengthen facts, numbers, claims, or first-hand experience.
- Keep the same language as the draft.
- Default to one short sentence; two only if the second genuinely earns its place.
- Plain spoken words. No analyst/report tone. No semicolon. Avoid em dash.
- Do not recap the parent post. Do not add a conclusion.
- Do not start with a stock framing such as The key, The hard part, This is the, A useful test, 这其实, 这章的价值在于.
- If a specific fact is not needed for the point, cut it.
- Ask internally: would Kenny actually type this in a chat? If not, rewrite again.

Return ONLY JSON: {{"final_copy":"..."}}'''


def enrich_signal(con: sqlite3.Connection, root: Path, signal: dict[str, Any]) -> dict[str, Any]:
    cfg = load_editorial_config(root)
    if not bool(cfg.get("enabled", True)):
        raise RuntimeError("editorial_enrichment_disabled")
    if not should_direct_final(signal, cfg):
        gate = _run_codex(con, root, cfg, "GATE", gate_prompt(signal), search=False)
        if str(gate.get("decision") or "").upper() != "PASS":
            return {"decision": "SKIP", "confidence": gate.get("confidence"), "reason": gate.get("reason"), "gate": gate}
    spec_guardrails = load_spec_guardrails(root)
    humanizer_path = require_humanizer_skill(cfg)
    kenny_voice = load_kenny_voice_profile(root, cfg)
    openers = recent_reply_openers(con, int(cfg.get("recent_reply_opener_limit", 12)))
    packet = _run_codex(con, root, cfg, "FINAL", final_prompt(signal, spec_guardrails, humanizer_path, kenny_voice, openers), search=True)
    decision = str(packet.get("decision") or "SKIP").upper()
    if decision not in {"POST", "REPLY", "SKIP"}:
        decision = "SKIP"
    packet["decision"] = decision
    if decision in {"POST", "REPLY"} and str(packet.get("final_copy") or "").strip() and (not cfg.get("humanize_only_on_violation",False) or bool(language_gate_violations(packet))):
        rewrite = _run_codex(
            con, root, cfg, "HUMANIZE",
            humanize_copy_prompt(signal, packet, humanizer_path, kenny_voice, openers),
            search=False,
        )
        rewritten_copy = str(rewrite.get("final_copy") or "").strip()
        if not rewritten_copy:
            raise RuntimeError("humanizer_empty_copy")
        packet["final_copy"] = rewritten_copy
    violations = language_gate_violations(packet) + packet_violations(signal, packet, cfg)
    if violations:
        return {
            "decision": "SKIP",
            "confidence": packet.get("confidence"),
            "reason": "language_gate_failed:" + ",".join(violations),
            "source_url": packet.get("source_url"),
            "gate": packet,
        }
    return packet
