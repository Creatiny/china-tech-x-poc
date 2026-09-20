"""Operator-aware acquisition policy. Deterministic rules, no new model or scheduler."""
from __future__ import annotations
import json
import math
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo


def parse_time(value: str | None) -> datetime | None:
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except (ValueError, TypeError):
        return None


def utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def active(cfg: dict[str, Any]) -> bool:
    return bool(cfg.get("operator_aware_policy", False))


def clock(cfg: dict[str, Any], now: datetime | None = None) -> datetime:
    return (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(str(cfg.get("operator_timezone", "Asia/Shanghai"))))


def operator_available(cfg: dict[str, Any], now: datetime | None = None) -> bool:
    if not active(cfg):
        return True
    local = clock(cfg, now)
    start = str(cfg.get("operator_active_start", "08:00"))
    end = str(cfg.get("operator_active_end", "22:00"))
    def minutes(s: str) -> int:
        h, m = map(int, s.split(":"))
        if not (0 <= h < 24 and 0 <= m < 60):
            raise ValueError("invalid_operator_window")
        return h * 60 + m
    lo, hi = minutes(start), minutes(end)
    if lo == hi:
        raise ValueError("empty_operator_window")
    point = local.hour * 60 + local.minute
    return lo <= point < hi if lo < hi else point >= lo or point < hi


def next_release(cfg: dict[str, Any], now: datetime | None = None) -> str:
    local = clock(cfg, now)
    for offset in range(2):
        day = local + timedelta(days=offset)
        for h in (8, 12, 18):
            candidate = day.replace(hour=h, minute=0, second=0, microsecond=0)
            if candidate > local:
                return utc_iso(candidate)
    raise ValueError("no_next_release")


def language(text: str | None) -> str:
    value = re.sub(r"https?://\S+|@[-_A-Za-z0-9]+", "", str(text or ""))
    if re.search(r"[\u3040-\u30ff]", value):
        return "other"
    han = len(re.findall(r"[\u3400-\u9fff]", value))
    if han >= 4:
        return "zh"
    if len(re.findall(r"[A-Za-z]", value)) >= 12:
        return "en"
    return "unknown"


def lane_for(signal: dict[str, Any], cfg: dict[str, Any]) -> str:
    direct = signal.get("source_kind") == "x_profile" or signal.get("target_mode") == "VERIFIED_X_TARGET"
    if direct and language(str(signal.get("title") or "") + " " + str(signal.get("excerpt") or "")) == "zh":
        return "REPLY"
    return "POST"


def focus_matches(signal: dict[str, Any]) -> bool:
    value = (str(signal.get("title") or "") + " " + str(signal.get("excerpt") or "")).casefold()
    # Explicit editorial scope, not a claim of semantic-model confidence.
    return bool(re.search(r"(?<![a-z0-9_])(agent(?:s|ic)?|coding|codex|claude|workflow|harness|jev|inference|llm|evals?|mcp|qwen|deepseek|kimi|glm|devin|cursor|automation)(?![a-z0-9_])|智能体|编程|代码|自动化|工作流|推理|评测|大模型|生产力|上下文|知识库|验收|交付", value))


def sent_counts(con: sqlite3.Connection, cfg: dict[str, Any], now: datetime | None = None) -> dict[str, int]:
    local = clock(cfg, now)
    start = utc_iso(local.replace(hour=0, minute=0, second=0, microsecond=0))
    end = utc_iso(local)
    rows = con.execute("SELECT editorial_packet_json FROM alert WHERE status='SENT' AND sent_at>=? AND sent_at<=?", (start, end)).fetchall()
    counts = {"POST": 0, "REPLY": 0}
    for row in rows:
        try:
            decision = json.loads(row[0] or "{}").get("decision")
            if decision in counts:
                counts[decision] += 1
        except (ValueError, TypeError):
            pass
    return counts


def preflight(con: sqlite3.Connection, signal: dict[str, Any], cfg: dict[str, Any], now: datetime | None = None) -> tuple[bool, str, str | None]:
    """Check actionability BEFORE expensive drafting, and repeat immediately before delivery."""
    if not active(cfg):
        return True, "legacy_policy", None
    current = now or datetime.now(timezone.utc)
    if not operator_available(cfg, current):
        return False, "operator_asleep", next_release(cfg, current)
    if str(signal.get("priority")) not in {"P0", "P1"}:
        return False, "not_qualified", None
    if not focus_matches(signal):
        return False, "outside_ai_building_scope", None
    lane = signal.get("operating_lane") or lane_for(signal, cfg)
    pub = parse_time(signal.get("published_at"))
    if pub is None:
        return False, "publication_time_unknown", None
    age = (current - pub).total_seconds() / 60
    if age < -5:
        return False, "future_publication_time", None
    max_age = float(cfg.get("reply_max_age_minutes", 180) if lane == "REPLY" else cfg.get("original_source_max_age_minutes", 720))
    if age > max_age:
        return False, "opportunity_expired", None
    if lane == "REPLY":
        if language(str(signal.get("title") or "") + " " + str(signal.get("excerpt") or "")) != "zh":
            return False, "non_chinese_reply_target", None
        if not signal.get("canonical_url") or signal.get("target_mode") != "VERIFIED_X_TARGET":
            return False, "unverified_reply_target", None
        if int(signal.get("observed_views") or 0) < int(cfg.get("reply_min_observed_views", 300)):
            return False, "awaiting_reach_evidence", utc_iso(current + timedelta(minutes=5))
        if int(signal.get("distribution_score") or 0) < int(cfg.get("reply_min_distribution_score", 6)):
            return False, "awaiting_distribution_evidence", utc_iso(current + timedelta(minutes=5))
        creator = str(signal.get("author") or "").casefold().lstrip("@")
        recent = con.execute("SELECT editorial_packet_json FROM alert WHERE status='SENT' AND sent_at>=? AND json_extract(editorial_packet_json,'$.decision')='REPLY'", (utc_iso(current-timedelta(hours=24)),)).fetchall()
        for row in recent:
            try:
                target = str(json.loads(row[0] or "{}").get("target_account") or "").casefold().lstrip("@")
                if creator and target == creator:
                    return False, "creator_attention_cooldown", utc_iso(current+timedelta(hours=1))
            except (ValueError, TypeError):
                pass
        weekly = con.execute("SELECT editorial_packet_json FROM alert WHERE status='SENT' AND sent_at>=? AND json_extract(editorial_packet_json,'$.decision')='REPLY'",(utc_iso(current-timedelta(days=7)),)).fetchall()
        matches = 0
        for row in weekly:
            try:
                matches += str(json.loads(row[0] or '{}').get('target_account') or '').casefold().lstrip('@') == creator
            except (ValueError,TypeError):
                pass
        if creator and matches >= int(cfg.get('max_p1_replies_per_creator_7d',3)):
            return False, 'creator_weekly_attention_cap', None
        window = con.execute("SELECT count(*) FROM alert WHERE status='SENT' AND sent_at>=? AND json_extract(editorial_packet_json,'$.decision')='REPLY'", (utc_iso(current-timedelta(hours=float(cfg.get("p1_reply_window_hours",4)))),)).fetchone()[0]
        if window >= int(cfg.get("max_p1_reply_packets_per_window",3)):
            return False, "reply_attention_window_full", utc_iso(current+timedelta(minutes=30))
    counts = sent_counts(con, cfg, current)
    hour = clock(cfg, current).hour
    # Cumulative budgets preserve afternoon/evening capacity. P0 has no sleep/cap bypass.
    reply_cap = 3 if hour < 12 else 7 if hour < 18 else int(cfg.get("max_reply_packets_per_day",10))
    post_cap = 1 if hour < 12 else int(cfg.get("max_post_packets_per_day",2))
    if counts[lane] >= (reply_cap if lane == "REPLY" else post_cap):
        return False, "daypart_attention_reserved", next_release(cfg, current)
    return True, "daytime_chinese_acquisition", None


def packet_violations(signal: dict[str, Any], packet: dict[str, Any], cfg: dict[str, Any]) -> list[str]:
    if not active(cfg) or packet.get("decision") == "SKIP":
        return []
    issues = []
    decision = packet.get("decision")
    if decision != (signal.get("operating_lane") or lane_for(signal,cfg)):
        issues.append("wrong_operating_lane")
    if language(packet.get("final_copy")) != "zh":
        issues.append("chinese_copy_required")
    if decision == "REPLY" and packet.get("target_url") != signal.get("canonical_url"):
        issues.append("reply_target_changed")
    evidence = packet.get("added_evidence")
    if not isinstance(evidence,dict) or len(str(evidence.get("detail") or "").strip()) < 12:
        issues.append("concrete_added_evidence_required")
    elif not evidence.get("source_url") and not evidence.get("local_evidence_path"):
        issues.append("evidence_provenance_required")
    subject = str(packet.get("subject_name") or "").strip()
    if decision == "POST" and (not subject or subject.casefold() not in str(packet.get("final_copy") or "").casefold()):
        issues.append("standalone_subject_required")
    try:
        confidence = float(packet.get("confidence"))
        if not math.isfinite(confidence) or not 0 <= confidence <= 1:
            issues.append("invalid_confidence")
    except (ValueError, TypeError):
        issues.append("invalid_confidence")
    return issues


def paced_limits(cfg: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    revised = dict(cfg)
    if not active(cfg):
        return revised
    hour = clock(cfg,now).hour
    fraction = .4 if hour < 12 else .8 if hour < 18 else 1.
    for key in ("max_final_calls_per_day","max_gate_calls_per_day","max_humanize_calls_per_day","max_tokens_per_day"):
        if key in cfg:
            revised[key] = max(1,int(int(cfg[key])*fraction))
    return revised


def health_report(con: sqlite3.Connection, cfg: dict[str, Any]) -> dict[str, Any]:
    """Read-only operational evidence; never substitute recommendations for publications."""
    from .editorial import model_usage_today
    now=datetime.now(timezone.utc)
    cycle=con.execute('SELECT id,started_at,finished_at,success,sources_due,sources_success,error FROM runtime_cycle WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1').fetchone()
    tracking=con.execute("""SELECT COUNT(*) tracked_urls,
      SUM(CASE WHEN p.posted_at<=? THEN 1 ELSE 0 END) older_than_24h,
      SUM(CASE WHEN julianday(o.captured_at)-julianday(p.posted_at)>=1 THEN 1 ELSE 0 END) mature_public_measurements
      FROM published_action p LEFT JOIN outcome_snapshot o ON o.id=(SELECT id FROM outcome_snapshot z WHERE z.action_id=p.id ORDER BY captured_at DESC,id DESC LIMIT 1)
      WHERE p.published_url IS NOT NULL""",(utc_iso(now-timedelta(hours=24)),)).fetchone()
    backoff=con.execute("SELECT * FROM editorial_runtime_state WHERE name='provider_backoff'").fetchone()
    return {
      'observed_at':utc_iso(now),'timezone':cfg.get('operator_timezone','Asia/Shanghai'),
      'policy_enabled':active(cfg),'operator_available':operator_available(cfg,now),
      'notification_window':[cfg.get('operator_active_start'),cfg.get('operator_active_end')],
      'automatic_language':'Chinese originals and Chinese-parent replies',
      'sent_recommendations_today':sent_counts(con,cfg,now),
      'model_usage_today':model_usage_today(con,str(cfg.get('budget_revision') or 'legacy')),
      'paced_limits':{k:v for k,v in paced_limits(cfg,now).items() if k in {'max_final_calls_per_day','max_tokens_per_day'}},
      'queue_counts':dict(con.execute('SELECT status,count(*) FROM alert GROUP BY status').fetchall()),
      'last_completed_collector_cycle':dict(cycle) if cycle else None,
      'outcome_coverage':dict(tracking),
      'recent_capture_errors':[dict(r) for r in con.execute('SELECT action_id,last_attempt_at,error FROM outcome_capture_state WHERE error IS NOT NULL ORDER BY last_attempt_at DESC LIMIT 5')],
      'provider_backoff':dict(backoff) if backoff else None,
      'analytics_limitations':'Public views are not unique viewers. Private profile visits, per-post follows and full historical publication coverage are unavailable.'
    }
