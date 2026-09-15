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
    update_signal_observation,
    iso,
    json_text,
    record_cycle_finish,
    record_cycle_start,
    save_source_state,
)
from .sources import fetch_source, fingerprint, fetch_account_posts_from_url, fetch_x_profile_stats
from .visuals import render_editorial_card
from .formula import build_creator_feedback_map


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


def _normalize_target_creator(value: str | None) -> str:
    v = str(value or "").strip().casefold()
    if v.startswith("@"):
        v = v[1:]
    return v


def _sent_replies_to_creator_since(con: sqlite3.Connection, creator: str, start_utc: str) -> int:
    creator = _normalize_target_creator(creator)
    if not creator:
        return 0
    rows = con.execute(
        """SELECT a.editorial_packet_json,s.author
             FROM alert a JOIN signal s ON s.id=a.signal_id
            WHERE a.status='SENT' AND a.editorial_status='READY' AND a.sent_at>=?
              AND json_extract(a.editorial_packet_json,'$.decision')='REPLY'""",
        (start_utc,),
    ).fetchall()
    count = 0
    for row in rows:
        try:
            packet = json.loads(row["editorial_packet_json"] or "{}")
        except Exception:
            packet = {}
        target = _normalize_target_creator(packet.get("target_account") or row["author"])
        if target == creator:
            count += 1
    return count


def _creator_reply_counts(con: sqlite3.Connection, creator: str) -> tuple[int, int]:
    now = datetime.now(timezone.utc)
    day_start = (now - timedelta(hours=24)).isoformat().replace("+00:00", "Z")
    week_start = (now - timedelta(days=7)).isoformat().replace("+00:00", "Z")
    return (
        _sent_replies_to_creator_since(con, creator, day_start),
        _sent_replies_to_creator_since(con, creator, week_start),
    )


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
        target_creator = _normalize_target_creator(packet.get("target_account") or signal.get("author"))
        if target_creator:
            creator_24h, creator_7d = _creator_reply_counts(con, target_creator)
            if creator_24h >= 1:
                return False, f"creator_24h_cooldown:{target_creator}"
            if creator_7d >= int(cfg.get("max_p1_replies_per_creator_7d", 3)):
                return False, f"creator_7d_cap:{target_creator}"
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



def _tweet_id(url: str | None) -> str:
    match = re.search(r"/status/(\d+)", str(url or ""))
    return match.group(1) if match else ""


def _outcome_due(posted_at: datetime | None, last_captured_at: datetime | None, now: datetime) -> bool:
    if posted_at is None:
        return False
    age_hours = max(0.0, (now - posted_at).total_seconds() / 3600.0)
    if age_hours > 14 * 24:
        return False
    if last_captured_at is None:
        return True
    since_hours = max(0.0, (now - last_captured_at).total_seconds() / 3600.0)
    if age_hours <= 2:
        return since_hours >= 0.25
    if age_hours <= 24:
        return since_hours >= 1
    if age_hours <= 7 * 24:
        return since_hours >= 6
    return since_hours >= 24


def capture_published_outcomes(con: sqlite3.Connection, *, handle: str = "KennyChinaTech", max_items: int = 2) -> dict[str, int]:
    """Capture public X outcome metrics for our published replies/posts without paid API access."""
    now = datetime.now(timezone.utc)
    rows = con.execute(
        """
        SELECT p.*, MAX(o.captured_at) AS last_captured_at
          FROM published_action p
          LEFT JOIN outcome_snapshot o ON o.action_id=p.id
         WHERE p.published_url IS NOT NULL AND p.posted_at>=?
         GROUP BY p.id
         ORDER BY CASE WHEN MAX(o.captured_at) IS NULL THEN 0 ELSE 1 END,
                  COALESCE(MAX(o.captured_at),p.posted_at) ASC
        """,
        ((now - timedelta(days=14)).isoformat().replace("+00:00", "Z"),),
    ).fetchall()
    checked = captured = errors = 0
    for row in rows:
        if checked >= max_items:
            break
        posted_at = _parse_iso(row["posted_at"])
        last_at = _parse_iso(row["last_captured_at"])
        if not _outcome_due(posted_at, last_at, now):
            continue
        checked += 1
        try:
            items = fetch_account_posts_from_url(str(row["published_url"]), handle)
            wanted = _tweet_id(row["published_url"])
            item = next((x for x in items if _tweet_id(x.get("canonical_url")) == wanted), None)
            if not item:
                continue
            metrics = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}
            impressions = metrics.get("views")
            if impressions is None:
                continue
            component_keys = ("likes", "replies", "reposts", "quotes", "bookmarks")
            known_components = [int(metrics[k]) for k in component_keys if k in metrics and metrics[k] is not None]
            engagements = sum(known_components) if known_components else None
            latest = con.execute(
                "SELECT * FROM outcome_snapshot WHERE action_id=? ORDER BY captured_at DESC LIMIT 1",
                (row["id"],),
            ).fetchone()
            changed = latest is None or any(
                latest[k] != v for k, v in {
                    "impressions": int(impressions),
                    "engagements": engagements,
                    "likes": metrics.get("likes"),
                    "replies": metrics.get("replies"),
                    "reposts": metrics.get("reposts"),
                    "quotes": metrics.get("quotes"),
                    "bookmarks": metrics.get("bookmarks"),
                }.items()
            )
            if not changed:
                continue
            con.execute(
                """INSERT INTO outcome_snapshot(
                       action_id,captured_at,impressions,engagements,likes,replies,reposts,quotes,bookmarks,profile_visits,notes
                   ) VALUES(?,?,?,?,?,?,?,?,?,NULL,?)""",
                (row["id"], iso(), int(impressions), engagements, metrics.get("likes"), metrics.get("replies"),
                 metrics.get("reposts"), metrics.get("quotes"), metrics.get("bookmarks"),
                 "Auto-captured from public X SSR; profile visits are not publicly exposed."),
            )
            con.commit()
            captured += 1
        except Exception:
            errors += 1
    return {"checked": checked, "captured": captured, "errors": errors}


def capture_account_snapshot(con: sqlite3.Connection, rules: dict[str, Any]) -> dict[str, Any]:
    handle = str(rules.get("account_handle") or "KennyChinaTech").lstrip("@")
    poll_minutes = int(rules.get("account_snapshot_poll_minutes", 30))
    source_id = f"__account_profile__:{handle.casefold()}"
    now = datetime.now(timezone.utc)
    state = get_source_state(con, source_id)
    if not source_due(state, poll_minutes, now):
        return {"polled": False}
    try:
        stats = fetch_x_profile_stats(handle)
        day = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
        note = f"Auto public X profile snapshot; following={stats.get('following')}; posts={stats.get('tweets')}. Profile visits unavailable."
        con.execute(
            """INSERT INTO account_snapshot(snapshot_date,followers,profile_visits,monetization_signals,notes,captured_at)
               VALUES(?,?,NULL,0,?,?)
               ON CONFLICT(snapshot_date) DO UPDATE SET followers=excluded.followers,notes=excluded.notes,captured_at=excluded.captured_at""",
            (day, int(stats["followers"]), note, iso()),
        )
        con.commit()
        save_source_state(con, source_id, success=True, item_count=1)
        return {"polled": True, **stats}
    except Exception as exc:
        save_source_state(con, source_id, success=False, error=f"{type(exc).__name__}: {exc}"[:1000])
        return {"polled": True, "error": f"{type(exc).__name__}: {exc}"}

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




def process_pending_alerts(
    con: sqlite3.Connection,
    root: Path,
    *,
    max_alerts: int | None = None,
) -> dict[str, Any]:
    """Consume the editorial queue without performing any source discovery.

    This is deliberately separated from the collector so slow model/search work can never delay
    the 15-second signal polling loop.
    """
    rules = load_toml(root / "config" / "rules.toml")
    limit = int(max_alerts if max_alerts is not None else rules.get("max_alerts_per_cycle", 3))
    result: dict[str, Any] = {
        "processed": 0, "sent": 0, "skipped": 0, "held": 0, "errors": 0,
        "recovered_stale_processing": 0,
    }

    # Crash recovery for a worker that died after claiming an item. Normal model calls are bounded
    # below this window, so ten minutes is safely beyond expected processing time.
    stale_before = iso(datetime.now(timezone.utc) - timedelta(minutes=10))
    cur = con.execute(
        """UPDATE alert SET status='PENDING',editorial_status=NULL,error='recovered_stale_editorial_processing'
             WHERE status='EDITORIAL_PROCESSING' AND editorial_at IS NOT NULL AND editorial_at<?""",
        (stale_before,),
    )
    result["recovered_stale_processing"] = int(cur.rowcount or 0)
    con.commit()

    pending = con.execute(
        """
        SELECT a.id AS alert_id, s.*
        FROM alert a JOIN signal s ON s.id=a.signal_id
        WHERE a.status='PENDING'
        ORDER BY CASE s.priority WHEN 'P0' THEN 0 ELSE 1 END,
                 CASE WHEN s.target_mode='VERIFIED_X_TARGET' THEN 0 ELSE 1 END,
                 s.distribution_score DESC, s.feedback_score DESC, s.view_velocity_per_min DESC,
                 s.score DESC, COALESCE(s.published_at,s.discovered_at) DESC
        LIMIT ?
        """,
        (max(1, limit),),
    ).fetchall()
    if not pending:
        return result

    sender = FeishuSender()
    if not sender.available():
        for row in pending:
            con.execute("UPDATE alert SET error=? WHERE id=? AND status='PENDING'", ("channel_not_configured", row["alert_id"]))
        con.commit()
        result["channel_available"] = False
        return result
    result["channel_available"] = True
    editorial_cfg = load_editorial_config(root)

    for row in pending:
        claim_at = iso()
        claimed = con.execute(
            """UPDATE alert SET status='EDITORIAL_PROCESSING',editorial_status='PROCESSING',editorial_at=?,error=NULL
                 WHERE id=? AND status='PENDING'""",
            (claim_at, row["alert_id"]),
        )
        con.commit()
        if not claimed.rowcount:
            continue
        result["processed"] += 1
        signal = dict(row)
        try:
            packet = enrich_signal(con, root, signal)

            # Collector may have refreshed the live target while the model was working. Re-read the
            # signal before any send so a target that has aged out cannot leak through the queue.
            live = con.execute(
                """SELECT a.id AS alert_id,a.status AS current_alert_status,s.*
                     FROM alert a JOIN signal s ON s.id=a.signal_id WHERE a.id=?""",
                (signal["alert_id"],),
            ).fetchone()
            if not live or str(live["current_alert_status"] or "") != "EDITORIAL_PROCESSING":
                continue
            live_signal = dict(live)
            if str(live_signal.get("priority") or "").upper() not in {"P0", "P1"}:
                con.execute(
                    """UPDATE alert SET status='EXPIRED',editorial_status='HOLD',error=?
                         WHERE id=? AND status='EDITORIAL_PROCESSING'""",
                    (f"signal_no_longer_qualified:{live_signal.get('priority')}", signal["alert_id"]),
                )
                con.commit()
                result["held"] += 1
                continue

            decision = str(packet.get("decision") or "SKIP").upper()
            editorial_now = iso()
            if decision == "SKIP":
                con.execute(
                    """UPDATE alert SET status='EDITORIAL_SKIP', editorial_status='SKIP', editorial_packet_json=?,
                       editorial_at=?, editorial_model=?, error=NULL
                       WHERE id=? AND status='EDITORIAL_PROCESSING'""",
                    (json.dumps(packet, ensure_ascii=False), editorial_now, str(editorial_cfg.get("model") or "codex"), signal["alert_id"]),
                )
                con.commit()
                result["skipped"] += 1
                continue

            allowed, policy_reason = notification_policy(con, live_signal, packet, editorial_cfg)
            packet["notification_policy"] = policy_reason
            if not allowed:
                con.execute(
                    """UPDATE alert SET status='EDITORIAL_HOLD', editorial_status='HOLD', editorial_packet_json=?,
                       editorial_at=?, editorial_model=?, error=?
                       WHERE id=? AND status='EDITORIAL_PROCESSING'""",
                    (json.dumps(packet, ensure_ascii=False), editorial_now, str(editorial_cfg.get("model") or "codex"), policy_reason, signal["alert_id"]),
                )
                con.commit()
                result["held"] += 1
                continue

            asset = None
            if bool(editorial_cfg.get("render_editorial_cards", True)):
                try:
                    asset = render_editorial_card(root, live_signal, packet)
                except Exception as asset_exc:
                    packet["asset_error"] = f"{type(asset_exc).__name__}: {asset_exc}"[:500]
                    asset = None

            text = format_publish_packet(live_signal, packet, has_asset=bool(asset))
            receipt = sender.send_text(text)
            if asset:
                sender.send_image(asset)
            con.execute(
                """UPDATE alert SET status='SENT',sent_at=?,channel='feishu',receipt_id=?,error=NULL,
                   editorial_status='READY', editorial_packet_json=?, editorial_at=?, editorial_model=?, asset_path=?
                   WHERE id=? AND status='EDITORIAL_PROCESSING'""",
                (iso(), receipt, json.dumps(packet, ensure_ascii=False), editorial_now,
                 str(editorial_cfg.get("model") or "codex"), str(asset) if asset else None, signal["alert_id"]),
            )
            con.commit()
            result["sent"] += 1
        except Exception as exc:
            con.execute(
                """UPDATE alert SET status='EDITORIAL_ERROR', editorial_status='ERROR', editorial_at=?, error=?
                     WHERE id=? AND status='EDITORIAL_PROCESSING'""",
                (iso(), f"{type(exc).__name__}: {exc}"[:1000], signal["alert_id"]),
            )
            con.commit()
            result["errors"] += 1
    return result


def _effective_poll_minutes(source: dict[str, Any], creator_feedback: dict[str, dict[str, Any]]) -> int:
    base = max(1, int(source.get("poll_minutes", 5)))
    if source.get("kind") != "x_profile":
        return base
    creator = _normalize_target_creator(source.get("handle"))
    fb = creator_feedback.get(creator, {})
    score = int(fb.get("score", 0))
    if score >= 2:
        return min(base, 2)
    if score >= 1:
        return min(base, 3)
    if score < 0:
        return max(base, 8)
    return base

def _limit_due_x_profiles(
    due: list[tuple[dict[str, Any], dict[str, Any] | None, bool]], max_x_profiles: int
) -> tuple[list[tuple[dict[str, Any], dict[str, Any] | None, bool]], int]:
    """Bound X-profile work per cycle to avoid synchronized proxy bursts."""
    non_x = [x for x in due if x[0].get("kind") != "x_profile"]
    x_due = [x for x in due if x[0].get("kind") == "x_profile"]

    def oldest_key(entry: tuple[dict[str, Any], dict[str, Any] | None, bool]) -> str:
        state = entry[1] or {}
        return str(state.get("last_polled_at") or state.get("last_success_at") or "")

    x_due.sort(key=oldest_key)
    cap = max(1, int(max_x_profiles))
    selected_x = x_due[:cap]
    return non_x + selected_x, max(0, len(x_due) - len(selected_x))

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
        creator_feedback = build_creator_feedback_map(
            con, min_samples=int(rules.get("creator_feedback_min_samples", 3))
        )
        due: list[tuple[dict[str, Any], dict[str, Any] | None, bool]] = []
        for source in sources:
            source_id = source["id"]
            state = get_source_state(con, source_id)
            poll_minutes = _effective_poll_minutes(source, creator_feedback)
            if not source_due(state, poll_minutes, now):
                continue
            due.append((source, state, bool(state and state.get("last_success_at"))))
        due, x_deferred = _limit_due_x_profiles(due, int(rules.get("max_x_profiles_per_cycle", 6)))
        counters["sources_due"] = len(due)
        counters["x_profiles_deferred"] = x_deferred

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
                source_for_classify = source
                if source.get("kind") == "x_profile":
                    creator = _normalize_target_creator(source.get("handle"))
                    fb = creator_feedback.get(creator, {})
                    source_for_classify = dict(source)
                    source_for_classify["outcome_feedback_score"] = int(fb.get("score", 0))
                    source_for_classify["outcome_feedback_samples"] = int(fb.get("samples", 0))
                    source_for_classify["outcome_feedback_median_impressions"] = fb.get("median_impressions")
                    source_for_classify["outcome_feedback_growth_days"] = int(fb.get("growth_days", 0))
                    source_for_classify["outcome_feedback_follower_gain"] = int(fb.get("follower_gain_on_clean_days", 0))
                for item in items:
                    result = classify(item, source_for_classify, rules, now)
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
                        "distribution_score": int(result.get("distribution_score", 0)),
                        "observed_views": int(result.get("observed_views", 0)),
                        "view_velocity_per_min": float(result.get("view_velocity_per_min", 0.0)),
                        "engagement_rate": float(result.get("engagement_rate", 0.0)),
                        "feedback_score": int(result.get("feedback_score", 0)),
                        "feedback_samples": int(result.get("feedback_samples", 0)),
                        "feedback_median_impressions": result.get("feedback_median_impressions"),
                        "feedback_growth_days": int(result.get("feedback_growth_days", 0)),
                        "feedback_follower_gain": int(result.get("feedback_follower_gain", 0)),
                        "reason": result["reason"],
                        "topic": result.get("topic"),
                        "x_search_url": result.get("x_search_url"),
                        "target_mode": result.get("target_mode", "TARGET_SEARCH_REQUIRED"),
                        "suggested_angle": result.get("suggested_angle"),
                        "raw_json": json_text(item),
                        "created_at": discovered,
                    }
                    signal_id, created = insert_signal(con, record)
                    if created:
                        counters["new_signals"] += 1
                    elif source.get("kind") == "x_profile":
                        # Exact content is deduped, but public distribution changes over time. Refresh
                        # metrics/classification so a post can graduate from quiet -> breakout.
                        update_signal_observation(con, signal_id, record)
                    else:
                        continue

                    if result["priority"] not in ("P0", "P1"):
                        # A once-qualified live target can age out before editorial processing. Do not
                        # let stale pending work survive merely because it was queued earlier.
                        con.execute(
                            "UPDATE alert SET status='EXPIRED',error=? WHERE signal_id=? AND status='PENDING'",
                            (f"signal_no_longer_qualified:{result['priority']}", signal_id),
                        )
                        con.commit()
                        continue
                    if created and not initialized_before:
                        if published is None or result["age_minutes"] > float(rules.get("bootstrap_alert_max_age_minutes", 120)):
                            continue
                    # Existing SENT/SKIP/HOLD alerts are not re-opened. The graduation path is for
                    # signals that had no alert because their first observation was too quiet.
                    existing_alert = con.execute("SELECT status FROM alert WHERE signal_id=?", (signal_id,)).fetchone()
                    if existing_alert:
                        if str(existing_alert["status"] or "") == "PENDING":
                            con.execute("UPDATE alert SET priority=? WHERE signal_id=?", (result["priority"], signal_id))
                            con.commit()
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

        if send_alerts:
            editorial_result = process_pending_alerts(
                con, root, max_alerts=int(rules.get("max_alerts_per_cycle", 3))
            )
            counters["alerts_sent"] += int(editorial_result.get("sent", 0))

        # Post-publication tracking is secondary to discovery/alerts. Keep it cheap and run it last.
        reconcile_sent_replies(con, max_items=1)
        capture_published_outcomes(
            con,
            handle=str(rules.get("account_handle") or "KennyChinaTech"),
            max_items=int(rules.get("outcome_capture_max_items_per_cycle", 2)),
        )
        capture_account_snapshot(con, rules)

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
