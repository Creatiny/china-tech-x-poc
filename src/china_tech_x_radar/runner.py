from __future__ import annotations

import json
import sqlite3
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .alerts import FeishuSender, format_publish_packet
from .classify import classify
from .editorial import enrich_signal, load_editorial_config
from .db import (
    ensure_alert,
    get_source_state,
    insert_signal,
    iso,
    json_text,
    record_cycle_finish,
    record_cycle_start,
    save_source_state,
)
from .sources import fetch_source, fingerprint
from .visuals import render_editorial_card


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def source_due(state: dict[str, Any] | None, poll_minutes: int, now: datetime) -> bool:
    if not state or not state.get("last_polled_at"):
        return True
    last = _parse_iso(state.get("last_polled_at"))
    if not last:
        return True
    return (now - last).total_seconds() >= poll_minutes * 60


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        return tomllib.load(f)


def _sent_packet_counts_today(con: sqlite3.Connection) -> dict[str, int]:
    tz = ZoneInfo("Asia/Shanghai")
    now_local = datetime.now(tz)
    start_local = datetime.combine(now_local.date(), datetime.min.time(), tzinfo=tz)
    start_utc = start_local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    rows = con.execute(
        """SELECT s.priority,a.editorial_packet_json FROM alert a JOIN signal s ON s.id=a.signal_id
           WHERE a.status='SENT' AND a.editorial_status='READY' AND a.sent_at>=?""",
        (start_utc,),
    ).fetchall()
    counts = {"p0_post": 0, "p0_reply": 0, "p1_post": 0, "p1_reply": 0}
    for row in rows:
        try:
            packet = json.loads(row["editorial_packet_json"] or "{}")
        except Exception:
            continue
        key = f"{str(row['priority'] or 'P1').lower()}_{str(packet.get('decision') or '').lower()}"
        if key in counts:
            counts[key] += 1
    return counts


def notification_policy(con: sqlite3.Connection, signal: dict[str, Any], packet: dict[str, Any], cfg: dict[str, Any]) -> tuple[bool, str]:
    priority = str(signal.get("priority") or "P1").upper()
    decision = str(packet.get("decision") or "SKIP").upper()
    confidence = float(packet.get("confidence") or 0.0)
    score = int(signal.get("score") or 0)
    if decision not in {"POST", "REPLY"}:
        return False, "not_publishable"
    if decision == "REPLY" and not packet.get("target_url"):
        return False, "reply_without_verified_target"
    counts = _sent_packet_counts_today(con)
    if priority == "P0":
        if confidence < float(cfg.get("p0_min_confidence", 0.75)):
            return False, f"p0_confidence_below_threshold:{confidence:.2f}"
        return True, "p0_immediate"
    if confidence < float(cfg.get("p1_min_confidence", 0.88)):
        return False, f"p1_confidence_below_threshold:{confidence:.2f}"
    if decision == "POST":
        if score < int(cfg.get("p1_post_min_score", 10)):
            return False, f"p1_post_score_below_threshold:{score}"
        if counts["p1_post"] >= int(cfg.get("max_p1_post_packets_per_day", 1)):
            return False, "p1_post_daily_slot_used"
        return True, "p1_post_curated"
    if score < int(cfg.get("p1_reply_min_score", 7)):
        return False, f"p1_reply_score_below_threshold:{score}"
    if counts["p1_reply"] >= int(cfg.get("max_p1_reply_packets_per_day", 4)):
        return False, "p1_reply_daily_cap_reached"
    return True, "p1_reply_curated"


def run_cycle(con: sqlite3.Connection, root: Path, *, send_alerts: bool = True) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    source_cfg = load_toml(root / "config" / "sources.toml")
    rules = load_toml(root / "config" / "rules.toml")
    sources = [s for s in source_cfg.get("source", []) if s.get("enabled", True)]
    cycle_id = record_cycle_start(con)
    counters = {
        "cycle_id": cycle_id,
        "sources_due": 0,
        "sources_success": 0,
        "new_signals": 0,
        "qualified_signals": 0,
        "alerts_sent": 0,
        "source_errors": [],
    }

    try:
        for source in sources:
            source_id = source["id"]
            state = get_source_state(con, source_id)
            if not source_due(state, int(source.get("poll_minutes", 5)), now):
                continue
            counters["sources_due"] += 1
            initialized_before = bool(state and state.get("last_success_at"))
            try:
                items, meta, not_modified = fetch_source(source, state)
                if not_modified:
                    save_source_state(con, source_id, success=True, item_count=0)
                    counters["sources_success"] += 1
                    continue
                for item in items:
                    result = classify(item, source, rules, now)
                    published = item.get("published_at")
                    discovered = iso(now)
                    record = {
                        "fingerprint": fingerprint(source_id, item),
                        "source_id": source_id,
                        "source_name": source.get("name", source_id),
                        "source_kind": source.get("kind", "unknown"),
                        "source_item_id": item.get("source_item_id"),
                        "canonical_url": item.get("canonical_url"),
                        "title": item.get("title") or "(untitled)",
                        "excerpt": item.get("excerpt") or "",
                        "author": item.get("author") or "",
                        "published_at": iso(published) if published else None,
                        "discovered_at": discovered,
                        "priority": result["priority"],
                        "score": int(result.get("score", 0)),
                        "reason": result["reason"],
                        "topic": result.get("topic"),
                        "x_search_url": result.get("x_search_url"),
                        "target_mode": result.get("target_mode", "TARGET_SEARCH_REQUIRED"),
                        "suggested_angle": result.get("suggested_angle"),
                        "raw_json": json_text(item),
                        "created_at": discovered,
                    }
                    signal_id, created = insert_signal(con, record)
                    if not created:
                        continue
                    counters["new_signals"] += 1
                    if result["priority"] not in ("P0", "P1"):
                        continue
                    # First-poll safety: only alert genuinely recent items with a source timestamp.
                    if not initialized_before:
                        if published is None or result["age_minutes"] > float(rules.get("bootstrap_alert_max_age_minutes", 120)):
                            continue
                    ensure_alert(con, signal_id, result["priority"])
                    counters["qualified_signals"] += 1
                save_source_state(
                    con,
                    source_id,
                    success=True,
                    item_count=len(items),
                    etag=meta.get("etag") or None,
                    last_modified=meta.get("last_modified") or None,
                )
                counters["sources_success"] += 1
            except Exception as exc:
                msg = f"{type(exc).__name__}: {exc}"[:1000]
                save_source_state(con, source_id, success=False, error=msg)
                counters["source_errors"].append({"source_id": source_id, "error": msg})

        sender = FeishuSender()
        max_alerts = int(rules.get("max_alerts_per_cycle", 3))
        pending = con.execute(
            """
            SELECT a.id AS alert_id, s.*
            FROM alert a JOIN signal s ON s.id=a.signal_id
            WHERE a.status='PENDING'
            ORDER BY CASE s.priority WHEN 'P0' THEN 0 ELSE 1 END, s.score DESC, COALESCE(s.published_at,s.discovered_at) DESC
            LIMIT ?
            """,
            (max_alerts,),
        ).fetchall()
        editorial_cfg = load_editorial_config(root)
        for row in pending:
            signal = dict(row)
            if not send_alerts:
                continue
            if not sender.available():
                con.execute("UPDATE alert SET error=? WHERE id=?", ("channel_not_configured", signal["alert_id"]))
                con.commit()
                continue
            try:
                packet = enrich_signal(con, root, signal)
                decision = str(packet.get("decision") or "SKIP").upper()
                editorial_now = iso()
                if decision == "SKIP":
                    con.execute(
                        """UPDATE alert SET status='EDITORIAL_SKIP', editorial_status='SKIP', editorial_packet_json=?,
                           editorial_at=?, editorial_model=?, error=NULL WHERE id=?""",
                        (json.dumps(packet, ensure_ascii=False), editorial_now, str(editorial_cfg.get("model") or "codex"), signal["alert_id"]),
                    )
                    con.commit()
                    continue

                allowed, policy_reason = notification_policy(con, signal, packet, editorial_cfg)
                packet["notification_policy"] = policy_reason
                if not allowed:
                    con.execute(
                        """UPDATE alert SET status='EDITORIAL_HOLD', editorial_status='HOLD', editorial_packet_json=?,
                           editorial_at=?, editorial_model=?, error=? WHERE id=?""",
                        (json.dumps(packet, ensure_ascii=False), editorial_now, str(editorial_cfg.get("model") or "codex"), policy_reason, signal["alert_id"]),
                    )
                    con.commit()
                    continue

                asset = None
                if bool(editorial_cfg.get("render_editorial_cards", True)):
                    try:
                        asset = render_editorial_card(root, signal, packet)
                    except Exception as asset_exc:
                        packet["asset_error"] = f"{type(asset_exc).__name__}: {asset_exc}"[:500]
                        asset = None

                text = format_publish_packet(signal, packet, has_asset=bool(asset))
                receipt = sender.send_text(text)
                if asset:
                    sender.send_image(asset)
                con.execute(
                    """UPDATE alert SET status='SENT',sent_at=?,channel='feishu',receipt_id=?,error=NULL,
                       editorial_status='READY', editorial_packet_json=?, editorial_at=?, editorial_model=?, asset_path=?
                       WHERE id=?""",
                    (iso(), receipt, json.dumps(packet, ensure_ascii=False), editorial_now,
                     str(editorial_cfg.get("model") or "codex"), str(asset) if asset else None, signal["alert_id"]),
                )
                con.commit()
                counters["alerts_sent"] += 1
            except Exception as exc:
                con.execute(
                    "UPDATE alert SET status='EDITORIAL_ERROR', editorial_status='ERROR', editorial_at=?, error=? WHERE id=?",
                    (iso(), f"{type(exc).__name__}: {exc}"[:1000], signal["alert_id"]),
                )
                con.commit()

        record_cycle_finish(
            con,
            cycle_id,
            success=1,
            sources_due=counters["sources_due"],
            sources_success=counters["sources_success"],
            new_signals=counters["new_signals"],
            qualified_signals=counters["qualified_signals"],
            alerts_sent=counters["alerts_sent"],
            error=json.dumps(counters["source_errors"], ensure_ascii=False) if counters["source_errors"] else None,
        )
        counters["success"] = True
        return counters
    except Exception as exc:
        record_cycle_finish(
            con,
            cycle_id,
            success=0,
            sources_due=counters["sources_due"],
            sources_success=counters["sources_success"],
            new_signals=counters["new_signals"],
            qualified_signals=counters["qualified_signals"],
            alerts_sent=counters["alerts_sent"],
            error=f"{type(exc).__name__}: {exc}"[:2000],
        )
        raise
