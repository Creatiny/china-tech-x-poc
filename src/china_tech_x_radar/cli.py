from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

from .alerts import FeishuSender
from .db import connect, iso
from .kpi import build_review
from .runner import run_cycle


def project_root() -> Path:
    env = os.environ.get("CHINA_TECH_RADAR_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def db_path(root: Path) -> Path:
    env = os.environ.get("CHINA_TECH_RADAR_DB")
    return Path(env).expanduser() if env else root / "runtime" / "china-tech-x.db"


def parse_day(value: str | None) -> date:
    return date.fromisoformat(value) if value else datetime.now().astimezone().date()


def cmd_run(args: argparse.Namespace) -> int:
    root = project_root()
    con = connect(db_path(root))
    result = run_cycle(con, root, send_alerts=not args.no_send)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = project_root()
    con = connect(db_path(root))
    sources = [dict(r) for r in con.execute("SELECT * FROM source_state ORDER BY source_id")]
    counts = {
        "signals": con.execute("SELECT COUNT(*) FROM signal").fetchone()[0],
        "p0": con.execute("SELECT COUNT(*) FROM signal WHERE priority='P0'").fetchone()[0],
        "p1": con.execute("SELECT COUNT(*) FROM signal WHERE priority='P1'").fetchone()[0],
        "alerts_sent": con.execute("SELECT COUNT(*) FROM alert WHERE status='SENT'").fetchone()[0],
        "alerts_pending": con.execute("SELECT COUNT(*) FROM alert WHERE status='PENDING'").fetchone()[0],
        "decisions": con.execute("SELECT COUNT(*) FROM operator_decision").fetchone()[0],
        "published_actions": con.execute("SELECT COUNT(*) FROM published_action").fetchone()[0],
    }
    exp = con.execute("SELECT * FROM experiment_state WHERE id=1").fetchone()
    print(json.dumps({"db": str(db_path(root)), "counts": counts, "sources": sources, "experiment": dict(exp) if exp else None}, ensure_ascii=False, indent=2))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    root = project_root()
    con = connect(db_path(root))
    rows = con.execute(
        """
        SELECT s.id,s.priority,s.title,s.source_name,s.published_at,s.discovered_at,s.reason,s.canonical_url,s.x_search_url,
               a.status AS alert_status,a.sent_at
        FROM signal s LEFT JOIN alert a ON a.signal_id=s.id
        WHERE s.priority IN ('P0','P1','P2')
        ORDER BY s.discovered_at DESC LIMIT ?
        """,
        (args.limit,),
    ).fetchall()
    print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
    return 0


def _worth(value: str | None) -> int | None:
    if value is None:
        return None
    return 1 if value.lower() in ("yes", "y", "true", "1") else 0


def cmd_decide(args: argparse.Namespace) -> int:
    root = project_root()
    con = connect(db_path(root))
    now = iso()
    signal = con.execute("SELECT * FROM signal WHERE id=?", (args.signal_id,)).fetchone()
    if not signal:
        raise SystemExit(f"signal {args.signal_id} not found")
    con.execute(
        """
        INSERT INTO operator_decision(signal_id,decision,worth_reviewing,reviewed_at,target_url,target_search_minutes,notes)
        VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(signal_id) DO UPDATE SET
          decision=excluded.decision,worth_reviewing=excluded.worth_reviewing,reviewed_at=excluded.reviewed_at,
          target_url=excluded.target_url,target_search_minutes=excluded.target_search_minutes,notes=excluded.notes
        """,
        (args.signal_id, args.decision, _worth(args.worth), now, args.target_url, args.target_search_minutes, args.notes),
    )
    action_id = None
    if args.decision == "POSTED":
        if not args.published_url:
            raise SystemExit("POSTED requires --published-url")
        posted_at = args.posted_at or now
        con.execute(
            """
            INSERT INTO published_action(signal_id,target_url,published_url,published_text,posted_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(published_url) DO UPDATE SET
              target_url=excluded.target_url,published_text=excluded.published_text,posted_at=excluded.posted_at
            """,
            (args.signal_id, args.target_url, args.published_url, args.published_text, posted_at),
        )
        row = con.execute("SELECT id FROM published_action WHERE published_url=?", (args.published_url,)).fetchone()
        action_id = row["id"] if row else None
    con.commit()
    print(json.dumps({"signal_id": args.signal_id, "decision": args.decision, "action_id": action_id}, ensure_ascii=False))
    return 0


def cmd_outcome(args: argparse.Namespace) -> int:
    root = project_root()
    con = connect(db_path(root))
    action_id = args.action_id
    if not action_id and args.published_url:
        row = con.execute("SELECT id FROM published_action WHERE published_url=?", (args.published_url,)).fetchone()
        action_id = row["id"] if row else None
    if not action_id:
        raise SystemExit("provide --action-id or a known --published-url")
    con.execute(
        "INSERT INTO outcome_snapshot(action_id,captured_at,impressions,engagements,notes) VALUES(?,?,?,?,?)",
        (action_id, iso(), args.impressions, args.engagements, args.notes),
    )
    con.commit()
    print(json.dumps({"action_id": action_id, "recorded": True}, ensure_ascii=False))
    return 0


def cmd_account(args: argparse.Namespace) -> int:
    root = project_root()
    con = connect(db_path(root))
    d = args.date or datetime.now().astimezone().date().isoformat()
    con.execute(
        """
        INSERT INTO account_snapshot(snapshot_date,followers,profile_visits,monetization_signals,notes,captured_at)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(snapshot_date) DO UPDATE SET followers=excluded.followers,profile_visits=excluded.profile_visits,
          monetization_signals=excluded.monetization_signals,notes=excluded.notes,captured_at=excluded.captured_at
        """,
        (d, args.followers, args.profile_visits, args.monetization_signals, args.notes, iso()),
    )
    con.commit()
    print(json.dumps({"date": d, "recorded": True}, ensure_ascii=False))
    return 0


def cmd_ops(args: argparse.Namespace) -> int:
    root = project_root()
    con = connect(db_path(root))
    d = args.date or datetime.now().astimezone().date().isoformat()
    con.execute(
        """
        INSERT INTO daily_ops(ops_date,operator_minutes,notes,captured_at) VALUES(?,?,?,?)
        ON CONFLICT(ops_date) DO UPDATE SET operator_minutes=excluded.operator_minutes,notes=excluded.notes,captured_at=excluded.captured_at
        """,
        (d, args.minutes, args.notes, iso()),
    )
    con.commit()
    print(json.dumps({"date": d, "minutes": args.minutes, "recorded": True}, ensure_ascii=False))
    return 0


def cmd_experiment_start(args: argparse.Namespace) -> int:
    root = project_root()
    con = connect(db_path(root))
    started = args.started_at or iso()
    existing = con.execute("SELECT started_at FROM experiment_state WHERE id=1").fetchone()
    if existing and existing["started_at"] and not args.force:
        print(json.dumps({"started_at": existing["started_at"], "already_started": True}, ensure_ascii=False))
        return 0
    now = iso()
    con.execute(
        """
        INSERT INTO experiment_state(id,started_at,baseline_followers,baseline_tracked_posts,baseline_total_views,created_at,updated_at)
        VALUES(1,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET started_at=excluded.started_at,baseline_followers=excluded.baseline_followers,
          baseline_tracked_posts=excluded.baseline_tracked_posts,baseline_total_views=excluded.baseline_total_views,updated_at=excluded.updated_at
        """,
        (started, args.followers, args.tracked_posts, args.total_views, now, now),
    )
    con.commit()
    print(json.dumps({"started_at": started, "baseline_followers": args.followers}, ensure_ascii=False))
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    root = project_root()
    con = connect(db_path(root))
    as_of = parse_day(args.date)
    review = build_review(con, root, as_of)
    out_dir = Path(args.output_dir).expanduser() if args.output_dir else root / "artifacts" / "reviews"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{as_of.isoformat()}.json"
    md_path = out_dir / f"{as_of.isoformat()}.md"
    safe = {k: v for k, v in review.items() if k != "markdown"}
    json_path.write_text(json.dumps(safe, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    if review.get("markdown"):
        md_path.write_text(review["markdown"], encoding="utf-8")
    if args.notify:
        sender = FeishuSender()
        if not sender.available():
            raise SystemExit("Feishu channel not configured")
        if review.get("markdown"):
            m = review["metrics"]
            d = review["diagnosis"]
            text = (
                f"[China Tech X Daily Review] {as_of.isoformat()}\n"
                f"Status: {review['status']} | Day {review['gate']['experiment_day']}\n"
                f"Alerts: {m['qualified_alerts_total']} | Worth: {m['review_worth_rate']} | Executable: {m['executable_opportunities_total']} | Posted: {m['published_actions_total']}\n"
                f"Max impressions: {m['max_impressions']} | Followers: {m['followers_total']} (delta {m['follower_delta']})\n"
                f"Bottleneck: {d['bottleneck']}\n"
                f"Next: {d['actions'][0]}"
            )
        else:
            text = f"[China Tech X Daily Review] {as_of.isoformat()}\n{review.get('status')}: {review.get('reason')}"
        sender.send_text(text)
    print(json.dumps({"review": safe, "json_path": str(json_path), "md_path": str(md_path) if review.get("markdown") else None}, ensure_ascii=False, indent=2, default=str))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="china-tech-x-radar")
    sub = p.add_subparsers(dest="cmd", required=True)

    x = sub.add_parser("run")
    x.add_argument("--no-send", action="store_true")
    x.set_defaults(func=cmd_run)

    x = sub.add_parser("status")
    x.set_defaults(func=cmd_status)

    x = sub.add_parser("list")
    x.add_argument("--limit", type=int, default=20)
    x.set_defaults(func=cmd_list)

    x = sub.add_parser("decide")
    x.add_argument("signal_id", type=int)
    x.add_argument("decision", choices=["POSTED", "SKIPPED", "FALSE_POSITIVE", "EXPIRED", "SAVE_FOR_ORIGINAL"])
    x.add_argument("--worth", choices=["yes", "no"])
    x.add_argument("--target-url")
    x.add_argument("--target-search-minutes", type=float)
    x.add_argument("--published-url")
    x.add_argument("--published-text")
    x.add_argument("--posted-at")
    x.add_argument("--notes")
    x.set_defaults(func=cmd_decide)

    x = sub.add_parser("outcome")
    x.add_argument("--action-id", type=int)
    x.add_argument("--published-url")
    x.add_argument("--impressions", type=int)
    x.add_argument("--engagements", type=int)
    x.add_argument("--notes")
    x.set_defaults(func=cmd_outcome)

    x = sub.add_parser("account-snapshot")
    x.add_argument("--date")
    x.add_argument("--followers", type=int)
    x.add_argument("--profile-visits", type=int)
    x.add_argument("--monetization-signals", type=int, default=0)
    x.add_argument("--notes")
    x.set_defaults(func=cmd_account)

    x = sub.add_parser("ops-time")
    x.add_argument("--date")
    x.add_argument("--minutes", type=float, required=True)
    x.add_argument("--notes")
    x.set_defaults(func=cmd_ops)

    x = sub.add_parser("experiment-start")
    x.add_argument("--started-at")
    x.add_argument("--followers", type=int, default=4)
    x.add_argument("--tracked-posts", type=int, default=15)
    x.add_argument("--total-views", type=int, default=396)
    x.add_argument("--force", action="store_true")
    x.set_defaults(func=cmd_experiment_start)

    x = sub.add_parser("review")
    x.add_argument("--date")
    x.add_argument("--output-dir")
    x.add_argument("--notify", action="store_true")
    x.set_defaults(func=cmd_review)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
