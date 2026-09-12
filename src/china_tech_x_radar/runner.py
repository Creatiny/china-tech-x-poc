from __future__ import annotations

import json
import sqlite3
import tomllib
import difflib
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed

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
from .sources import fetch_source, fingerprint, fetch_account_posts_from_url
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


def _sent_packet_counts_since(con: sqlite3.Connection, start_utc: str) -> dict[str, int]:
    rows = con.execute(
        """SELECT s.priority,a.editorial_packet_json FROM alert a JOIN signal s ON s.id=a.signal_id
           WHERE a.status='SENT' AND a.editorial_status='READY' AND a.sent_at>=?""",
        (start_utc,),
    ).fetchall()
    counts = {
        "p0_post": 0, "p0_reply": 0, "p1_post": 0, "p1_reply": 0,
    }
    for row in rows:
        try:
            packet = json.loads(row["editorial_packet_json"] or "{}")
        except Exception:
            continue
        key = f"{str(row['priority'] or 'P1').lower()}_{str(packet.get('decision') or '').lower()}"
        if key in counts:
            counts[key] += 1
    return counts


def _sent_packet_counts_today(con: sqlite3.Connection, cfg: dict[str, Any] | None = None) -> dict[str, int]:
    tz = ZoneInfo("Asia/Shanghai")
    now_local = datetime.now(tz)
    start_local = datetime.combine(now_local.date(), datetime.min.time(), tzinfo=tz)
    start_utc = start_local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if cfg and cfg.get("notification_epoch"):
        epoch = str(cfg.get("notification_epoch"))
        if epoch > start_utc:
            start_utc = epoch
    return _sent_packet_counts_since(con, start_utc)


def _sent_p1_replies_in_window(con: sqlite3.Connection, cfg: dict[str, Any]) -> int:
    hours = float(cfg.get("p1_reply_window_hours", 4))
    start = datetime.now(timezone.utc) - timedelta(hours=hours)
    start_utc = start.isoformat().replace("+00:00", "Z")
    epoch = str(cfg.get("notification_epoch") or "")
    if epoch and epoch > start_utc:
        start_utc = epoch
    return _sent_packet_counts_since(con, start_utc)["p1_reply"]


def notification_policy(con: sqlite3.Connection, signal: dict[str, Any], packet: dict[str, Any], cfg: dict[str, Any]) -> tuple[bool, str]:
    priority = str(signal.get("priority") or "P1").upper()
    decision = str(packet.get("decision") or "SKIP").upper()
    confidence = float(packet.get("confidence") or 0.0)
    score = int(signal.get("score") or 0)
    if decision not in {"POST", "REPLY"}:
        return False, "not_publishable"
    if decision == "REPLY" and not packet.get("target_url"):
        return False, "reply_without_verified_target"
    # P0 is exceptional by definition and must not be suppressed by ordinary P1 daily caps.
    if priority == "P0":
        if confidence < float(cfg.get("p0_min_confidence", 0.75)):
            return False, f"p0_confidence_below_threshold:{confidence:.2f}"
        return True, "p0_immediate"
    counts = _sent_packet_counts_today(con, cfg)
    # P0 is exceptional and never consumes ordinary P1 notification capacity.
    if decision == "POST" and counts["p1_post"] >= int(cfg.get("max_p1_post_packets_per_day", 1)):
        return False, "p1_post_daily_slot_used"
    if decision == "REPLY":
        window_count = _sent_p1_replies_in_window(con, cfg)
        window_max = int(cfg.get("max_p1_reply_packets_per_window", 3))
        if window_count >= window_max:
            return False, "p1_reply_window_cap_reached"
        daily_safety_max = int(cfg.get("max_p1_reply_packets_per_day", 12))
        if counts["p1_reply"] >= daily_safety_max:
            return False, "p1_reply_daily_safety_cap_reached"
    if confidence < float(cfg.get("p1_min_confidence", 0.88)):
        return False, f"p1_confidence_below_threshold:{confidence:.2f}"
    if decision == "POST":
        if score < int(cfg.get("p1_post_min_score", 10)):
            return False, f"p1_post_score_below_threshold:{score}"
        return True, "p1_post_curated"
    if score < int(cfg.get("p1_reply_min_score", 7)):
        return False, f"p1_reply_score_below_threshold:{score}"
    return True, "p1_reply_curated"


def _normalize_reply_copy(text: str | None) -> str:
    value = str(text or "").casefold()
    value = re.sub(r"https?://\S+", " ", value)
    # X commonly prepends one or more @handles to reply text in rendered timelines.
    value = re.sub(r"^(?:\s*@[-_a-z0-9]+)+\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"[^\w\u3400-\u9fff]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def _reply_copy_score(expected: str | None, actual: str | None) -> float:
    a = _normalize_reply_copy(expected)
    b = _normalize_reply_copy(actual)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return min(len(a), len(b)) / max(len(a), len(b))
    seq = difflib.SequenceMatcher(None, a, b).ratio()
    aset, bset = set(a.split()), set(b.split())
    jaccard = len(aset & bset) / max(1, len(aset | bset))
    return max(seq, jaccard)


def reconcile_sent_replies(con: sqlite3.Connection, *, handle: str = "KennyChinaTech", max_items: int = 3) -> dict[str, int]:
    """Find the user's published replies from the already-known target post URLs.

    No manual reply URL is required. Recently SENT reply alerts are revisited at most once every
    five minutes for up to 48 hours. When a visible @KennyChinaTech reply matches the suggested
    copy, published_action is created/updated automatically.
    """
    now = datetime.now(timezone.utc)
    cutoff = (now.timestamp() - 48 * 3600)
    cutoff_iso = datetime.fromtimestamp(cutoff, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    check_before = datetime.fromtimestamp(now.timestamp() - 5 * 60, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    rows = con.execute(
        """SELECT a.id alert_id,a.signal_id,a.sent_at,a.editorial_packet_json,
                  a.reply_reconcile_attempts,a.reply_reconcile_last_checked_at,
                  s.topic,s.published_at
             FROM alert a JOIN signal s ON s.id=a.signal_id
            WHERE a.status='SENT' AND a.sent_at>=? AND a.matched_published_url IS NULL
              AND json_extract(a.editorial_packet_json,'$.decision')='REPLY'
              AND (a.reply_reconcile_last_checked_at IS NULL OR a.reply_reconcile_last_checked_at<=?)
              AND coalesce(a.reply_reconcile_attempts,0)<24
            ORDER BY a.sent_at DESC LIMIT ?""",
        (cutoff_iso, check_before, max_items),
    ).fetchall()
    checked = matched = 0
    for row in rows:
        checked += 1
        packet = json.loads(row["editorial_packet_json"] or "{}")
        target_url = str(packet.get("target_url") or "").strip()
        expected = str(packet.get("final_copy") or "").strip()
        checked_at = iso()
        try:
            candidates = fetch_account_posts_from_url(target_url, handle) if target_url else []
            best = None
            best_score = 0.0
            for item in candidates:
                score = _reply_copy_score(expected, item.get("excerpt"))
                if score > best_score:
                    best, best_score = item, score
            if best is not None and best_score >= 0.62:
                published_url = str(best.get("canonical_url") or "")
                posted_at = iso(best.get("published_at")) if best.get("published_at") else checked_at
                actual_text = str(best.get("excerpt") or expected)
                existing = con.execute("SELECT id FROM published_action WHERE signal_id=? ORDER BY id DESC LIMIT 1", (row["signal_id"],)).fetchone()
                if existing:
                    con.execute(
                        "UPDATE published_action SET published_url=?,published_text=?,posted_at=? WHERE id=?",
                        (published_url, actual_text, posted_at, existing["id"]),
                    )
                else:
                    con.execute(
                        """INSERT INTO published_action(
                               signal_id,target_url,published_url,published_text,posted_at,action_type,event_type,
                               target_account,target_posted_at,angle_type,media_type,has_external_link
                           ) VALUES(?,?,?,?,?,'REPLY',?,?,?,?, 'NONE',0)""",
                        (row["signal_id"], target_url, published_url, actual_text, posted_at, row["topic"],
                         packet.get("target_account"), row["published_at"], packet.get("angle_type")),
                    )
                con.execute(
                    """UPDATE alert SET matched_published_url=?,matched_at=?,reply_reconcile_last_checked_at=?,
                           reply_reconcile_attempts=coalesce(reply_reconcile_attempts,0)+1 WHERE id=?""",
                    (published_url, checked_at, checked_at, row["alert_id"]),
                )
                matched += 1
            else:
                con.execute(
                    "UPDATE alert SET reply_reconcile_last_checked_at=?,reply_reconcile_attempts=coalesce(reply_reconcile_attempts,0)+1 WHERE id=?",
                    (checked_at, row["alert_id"]),
                )
            con.commit()
        except Exception:
            con.execute(
                "UPDATE alert SET reply_reconcile_last_checked_at=?,reply_reconcile_attempts=coalesce(reply_reconcile_attempts,0)+1 WHERE id=?",
                (checked_at, row["alert_id"]),
            )
            con.commit()
    return {"checked": checked, "matched": matched}


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
        due: list[tuple[dict[str, Any], dict[str, Any] | None, bool]] = []
        for source in sources:
            source_id = source["id"]
            state = get_source_state(con, source_id)
            if not source_due(state, int(source.get("poll_minutes", 5)), now):
                continue
            due.append((source, state, bool(state and state.get("last_success_at"))))
        counters["sources_due"] = len(due)

        workers = max(1, min(int(rules.get("source_fetch_workers", 8)), len(due) or 1))
        fetched: list[tuple[dict[str, Any], dict[str, Any] | None, bool, tuple[list[dict[str, Any]], dict[str, str], bool] | None, Exception | None]] = []
        if due:
            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="china-tech-source") as pool:
                future_map = {pool.submit(fetch_source, source, state): (source, state, initialized_before)
                              for source, state, initialized_before in due}
                for future in as_completed(future_map):
                    source, state, initialized_before = future_map[future]
                    try:
                        fetched.append((source, state, initialized_before, future.result(), None))
                    except Exception as exc:
                        fetched.append((source, state, initialized_before, None, exc))

        # Network I/O above is parallel; all SQLite writes remain serialized on this thread.
        for source, state, initialized_before, fetched_result, fetch_error in fetched:
            source_id = source["id"]
            if fetch_error is not None:
                msg = f"{type(fetch_error).__name__}: {fetch_error}"[:1000]
                save_source_state(con, source_id, success=False, error=msg)
                counters["source_errors"].append({"source_id": source_id, "error": msg})
                continue
            try:
                assert fetched_result is not None
                items, meta, not_modified = fetched_result
                qualified_this_poll = 0
                max_qualified_this_poll = int(source.get("max_qualified_per_poll", 1000000))
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
                    if not initialized_before:
                        if published is None or result["age_minutes"] > float(rules.get("bootstrap_alert_max_age_minutes", 120)):
                            continue
                    if qualified_this_poll >= max_qualified_this_poll:
                        continue
                    ensure_alert(con, signal_id, result["priority"])
                    qualified_this_poll += 1
                    counters["qualified_signals"] += 1
                save_source_state(
                    con, source_id, success=True, item_count=len(items),
                    etag=meta.get("etag") or None, last_modified=meta.get("last_modified") or None,
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
            ORDER BY CASE WHEN s.target_mode='VERIFIED_X_TARGET' THEN 0 ELSE 1 END,
                     CASE s.priority WHEN 'P0' THEN 0 ELSE 1 END,
                     s.score DESC, COALESCE(s.published_at,s.discovered_at) DESC
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

        # Post-publication tracking is secondary to discovery/alerts. Keep it cheap and run it last.
        reconcile_sent_replies(con, max_items=1)

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
