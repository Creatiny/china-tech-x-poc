from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None = None) -> str:
    dt = dt or utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def connect(path: str | Path) -> sqlite3.Connection:
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA busy_timeout=5000")
    migrate(con)
    return con


def migrate(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS source_state (
            source_id TEXT PRIMARY KEY,
            last_polled_at TEXT,
            last_success_at TEXT,
            last_error TEXT,
            etag TEXT,
            last_modified TEXT,
            last_item_count INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS signal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint TEXT NOT NULL UNIQUE,
            source_id TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            source_item_id TEXT,
            canonical_url TEXT,
            title TEXT NOT NULL,
            excerpt TEXT,
            author TEXT,
            published_at TEXT,
            discovered_at TEXT NOT NULL,
            priority TEXT NOT NULL,
            score INTEGER NOT NULL DEFAULT 0,
            reason TEXT NOT NULL,
            topic TEXT,
            x_search_url TEXT,
            target_mode TEXT NOT NULL DEFAULT 'TARGET_SEARCH_REQUIRED',
            suggested_angle TEXT,
            raw_json TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_signal_discovered_at ON signal(discovered_at);
        CREATE INDEX IF NOT EXISTS idx_signal_priority ON signal(priority);

        CREATE TABLE IF NOT EXISTS alert (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER NOT NULL UNIQUE REFERENCES signal(id) ON DELETE CASCADE,
            priority TEXT NOT NULL,
            created_at TEXT NOT NULL,
            sent_at TEXT,
            channel TEXT,
            status TEXT NOT NULL DEFAULT 'PENDING',
            receipt_id TEXT,
            error TEXT,
            editorial_status TEXT,
            editorial_packet_json TEXT,
            editorial_at TEXT,
            editorial_model TEXT,
            asset_path TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_alert_status ON alert(status);

        CREATE TABLE IF NOT EXISTS operator_decision (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER NOT NULL UNIQUE REFERENCES signal(id) ON DELETE CASCADE,
            decision TEXT NOT NULL,
            worth_reviewing INTEGER,
            reviewed_at TEXT NOT NULL,
            target_url TEXT,
            target_search_minutes REAL,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS published_action (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER NOT NULL REFERENCES signal(id) ON DELETE CASCADE,
            action_type TEXT NOT NULL DEFAULT 'REPLY',
            event_type TEXT,
            target_url TEXT,
            target_account TEXT,
            target_account_followers INTEGER,
            target_posted_at TEXT,
            target_post_age_minutes REAL,
            target_post_impressions_at_reply INTEGER,
            angle_type TEXT,
            hook_type TEXT,
            media_type TEXT NOT NULL DEFAULT 'NONE',
            has_external_link INTEGER NOT NULL DEFAULT 0,
            published_url TEXT UNIQUE,
            published_text TEXT,
            posted_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_published_action_posted_at ON published_action(posted_at);

        CREATE TABLE IF NOT EXISTS outcome_snapshot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_id INTEGER NOT NULL REFERENCES published_action(id) ON DELETE CASCADE,
            captured_at TEXT NOT NULL,
            impressions INTEGER,
            engagements INTEGER,
            likes INTEGER,
            replies INTEGER,
            reposts INTEGER,
            quotes INTEGER,
            bookmarks INTEGER,
            profile_visits INTEGER,
            notes TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_outcome_action ON outcome_snapshot(action_id, captured_at);

        CREATE TABLE IF NOT EXISTS account_snapshot (
            snapshot_date TEXT PRIMARY KEY,
            followers INTEGER,
            profile_visits INTEGER,
            monetization_signals INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            captured_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS daily_ops (
            ops_date TEXT PRIMARY KEY,
            operator_minutes REAL,
            notes TEXT,
            captured_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS business_event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurred_at TEXT NOT NULL,
            event_type TEXT NOT NULL,
            source_url TEXT,
            amount_cny REAL,
            currency TEXT NOT NULL DEFAULT 'CNY',
            notes TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_business_event_occurred ON business_event(occurred_at);
        CREATE INDEX IF NOT EXISTS idx_business_event_type ON business_event(event_type);

        CREATE TABLE IF NOT EXISTS model_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usage_date TEXT NOT NULL,
            used_at TEXT NOT NULL,
            purpose TEXT NOT NULL,
            model TEXT NOT NULL,
            budget_revision TEXT NOT NULL DEFAULT 'legacy',
            tokens_used INTEGER,
            success INTEGER NOT NULL,
            error TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_model_usage_date ON model_usage(usage_date, purpose);

        CREATE TABLE IF NOT EXISTS runtime_cycle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            success INTEGER NOT NULL DEFAULT 0,
            sources_due INTEGER NOT NULL DEFAULT 0,
            sources_success INTEGER NOT NULL DEFAULT 0,
            new_signals INTEGER NOT NULL DEFAULT 0,
            qualified_signals INTEGER NOT NULL DEFAULT 0,
            alerts_sent INTEGER NOT NULL DEFAULT 0,
            error TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_runtime_cycle_started ON runtime_cycle(started_at);

        CREATE TABLE IF NOT EXISTS experiment_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            started_at TEXT,
            baseline_followers INTEGER,
            baseline_tracked_posts INTEGER,
            baseline_total_views INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )
    cols = {r[1] for r in con.execute("PRAGMA table_info(signal)")}
    if "score" not in cols:
        con.execute("ALTER TABLE signal ADD COLUMN score INTEGER NOT NULL DEFAULT 0")
    action_cols = {r[1] for r in con.execute("PRAGMA table_info(published_action)")}
    action_migrations = {
        "action_type": "TEXT NOT NULL DEFAULT 'REPLY'",
        "event_type": "TEXT",
        "target_account": "TEXT",
        "target_account_followers": "INTEGER",
        "target_posted_at": "TEXT",
        "target_post_age_minutes": "REAL",
        "target_post_impressions_at_reply": "INTEGER",
        "angle_type": "TEXT",
        "hook_type": "TEXT",
        "media_type": "TEXT NOT NULL DEFAULT 'NONE'",
        "has_external_link": "INTEGER NOT NULL DEFAULT 0",
    }
    for name, decl in action_migrations.items():
        if name not in action_cols:
            con.execute(f"ALTER TABLE published_action ADD COLUMN {name} {decl}")
    alert_cols = {r[1] for r in con.execute("PRAGMA table_info(alert)")}
    alert_migrations = {
        "editorial_status": "TEXT",
        "editorial_packet_json": "TEXT",
        "editorial_at": "TEXT",
        "editorial_model": "TEXT",
        "asset_path": "TEXT",
    }
    for name, decl in alert_migrations.items():
        if name not in alert_cols:
            con.execute(f"ALTER TABLE alert ADD COLUMN {name} {decl}")
    usage_cols = {r[1] for r in con.execute("PRAGMA table_info(model_usage)")}
    if "budget_revision" not in usage_cols:
        con.execute("ALTER TABLE model_usage ADD COLUMN budget_revision TEXT NOT NULL DEFAULT 'legacy'")
    outcome_cols = {r[1] for r in con.execute("PRAGMA table_info(outcome_snapshot)")}
    outcome_migrations = {
        "likes": "INTEGER", "replies": "INTEGER", "reposts": "INTEGER", "quotes": "INTEGER",
        "bookmarks": "INTEGER", "profile_visits": "INTEGER",
    }
    for name, decl in outcome_migrations.items():
        if name not in outcome_cols:
            con.execute(f"ALTER TABLE outcome_snapshot ADD COLUMN {name} {decl}")
    con.commit()


def get_source_state(con: sqlite3.Connection, source_id: str) -> dict[str, Any] | None:
    row = con.execute("SELECT * FROM source_state WHERE source_id=?", (source_id,)).fetchone()
    return dict(row) if row else None


def save_source_state(
    con: sqlite3.Connection,
    source_id: str,
    *,
    success: bool,
    item_count: int = 0,
    error: str | None = None,
    etag: str | None = None,
    last_modified: str | None = None,
) -> None:
    now = iso()
    con.execute(
        """
        INSERT INTO source_state(source_id,last_polled_at,last_success_at,last_error,etag,last_modified,last_item_count)
        VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(source_id) DO UPDATE SET
          last_polled_at=excluded.last_polled_at,
          last_success_at=CASE WHEN ? THEN excluded.last_success_at ELSE source_state.last_success_at END,
          last_error=excluded.last_error,
          etag=COALESCE(excluded.etag, source_state.etag),
          last_modified=COALESCE(excluded.last_modified, source_state.last_modified),
          last_item_count=excluded.last_item_count
        """,
        (source_id, now, now if success else None, error, etag, last_modified, item_count, 1 if success else 0),
    )
    con.commit()


def insert_signal(con: sqlite3.Connection, record: dict[str, Any]) -> tuple[int, bool]:
    cols = [
        "fingerprint","source_id","source_name","source_kind","source_item_id","canonical_url",
        "title","excerpt","author","published_at","discovered_at","priority","score","reason","topic",
        "x_search_url","target_mode","suggested_angle","raw_json","created_at",
    ]
    vals = [record.get(c) for c in cols]
    cur = con.execute(
        f"INSERT OR IGNORE INTO signal({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",
        vals,
    )
    con.commit()
    if cur.rowcount:
        return int(cur.lastrowid), True
    row = con.execute("SELECT id FROM signal WHERE fingerprint=?", (record["fingerprint"],)).fetchone()
    return int(row["id"]), False


def ensure_alert(con: sqlite3.Connection, signal_id: int, priority: str) -> int:
    now = iso()
    con.execute(
        "INSERT OR IGNORE INTO alert(signal_id,priority,created_at,status) VALUES(?,?,?,'PENDING')",
        (signal_id, priority, now),
    )
    con.commit()
    row = con.execute("SELECT id FROM alert WHERE signal_id=?", (signal_id,)).fetchone()
    return int(row["id"])


def record_cycle_start(con: sqlite3.Connection) -> int:
    cur = con.execute("INSERT INTO runtime_cycle(started_at) VALUES(?)", (iso(),))
    con.commit()
    return int(cur.lastrowid)


def record_cycle_finish(con: sqlite3.Connection, cycle_id: int, **fields: Any) -> None:
    allowed = {"success","sources_due","sources_success","new_signals","qualified_signals","alerts_sent","error"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    updates["finished_at"] = iso()
    set_sql = ",".join(f"{k}=?" for k in updates)
    con.execute(f"UPDATE runtime_cycle SET {set_sql} WHERE id=?", [*updates.values(), cycle_id])
    con.commit()


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)
