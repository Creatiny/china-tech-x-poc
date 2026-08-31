from __future__ import annotations

import json
import sqlite3
import statistics
import tomllib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def _median(values: list[float]) -> float | None:
    return round(float(statistics.median(values)), 2) if values else None


def load_kpi(root: Path) -> dict[str, Any]:
    with (root / "config" / "kpi.toml").open("rb") as f:
        return tomllib.load(f)


def get_experiment(con: sqlite3.Connection) -> dict[str, Any] | None:
    row = con.execute("SELECT * FROM experiment_state WHERE id=1").fetchone()
    return dict(row) if row and row["started_at"] else None


def experiment_day(started_at: str, as_of: date) -> int:
    start = _dt(started_at)
    if not start:
        return 0
    return max(1, (as_of - start.date()).days + 1)


def collect_metrics(con: sqlite3.Connection, start_at: str, as_of: date) -> dict[str, Any]:
    start = _dt(start_at)
    assert start is not None
    end = datetime.combine(as_of + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    start_s = start.isoformat().replace("+00:00", "Z")
    end_s = end.isoformat().replace("+00:00", "Z")

    cycles = con.execute("SELECT success FROM runtime_cycle WHERE started_at>=? AND started_at<?", (start_s, end_s)).fetchall()
    cycle_rate = (sum(int(r["success"]) for r in cycles) / len(cycles)) if cycles else None

    alerts = con.execute(
        """SELECT a.*,s.published_at,s.discovered_at,s.priority FROM alert a JOIN signal s ON s.id=a.signal_id
           WHERE a.created_at>=? AND a.created_at<? AND a.status='SENT'""",
        (start_s, end_s),
    ).fetchall()
    latencies: list[float] = []
    for r in alerts:
        sent = _dt(r["sent_at"])
        published = _dt(r["published_at"])
        discovered = _dt(r["discovered_at"])
        # Bootstrap items published before the experiment existed cannot be charged as runtime latency.
        # Once the experiment is live, new source items are measured from source publish time.
        origin = published if published and published >= start else discovered
        if sent and origin:
            latencies.append(max(0.0, (sent - origin).total_seconds() / 60.0))

    decisions = con.execute("SELECT * FROM operator_decision WHERE reviewed_at>=? AND reviewed_at<?", (start_s, end_s)).fetchall()
    worth = [int(r["worth_reviewing"]) for r in decisions if r["worth_reviewing"] is not None]
    worth_rate = (sum(worth) / len(worth)) if worth else None
    executable = [r for r in decisions if r["target_url"]]
    search_minutes = [float(r["target_search_minutes"]) for r in decisions if r["target_search_minutes"] is not None]

    actions = con.execute("SELECT * FROM published_action WHERE posted_at>=? AND posted_at<?", (start_s, end_s)).fetchall()
    latest_outcomes: list[sqlite3.Row] = []
    for action in actions:
        row = con.execute(
            "SELECT * FROM outcome_snapshot WHERE action_id=? ORDER BY captured_at DESC LIMIT 1", (action["id"],)
        ).fetchone()
        if row:
            latest_outcomes.append(row)
    impressions = [int(r["impressions"]) for r in latest_outcomes if r["impressions"] is not None]
    original_posts = [r for r in actions if (r["action_type"] or "REPLY").upper() == "ORIGINAL"]
    reply_actions = [r for r in actions if (r["action_type"] or "REPLY").upper() == "REPLY"]

    business_events = con.execute(
        "SELECT * FROM business_event WHERE occurred_at>=? AND occurred_at<? ORDER BY occurred_at",
        (start_s, end_s),
    ).fetchall()
    event_types = [str(r["event_type"]).upper() for r in business_events]
    offer_live_total = sum(1 for t in event_types if t == "OFFER_LIVE")
    commercial_intent_stages = {"COMMERCIAL_INTENT", "QUALIFIED_CONVERSATION", "PROPOSAL_SENT", "PAID_CUSTOMER", "REPEAT_PURCHASE", "SPONSOR_PAYMENT"}
    qualified_stages = {"QUALIFIED_CONVERSATION", "PROPOSAL_SENT", "PAID_CUSTOMER", "REPEAT_PURCHASE", "SPONSOR_PAYMENT"}
    proposal_stages = {"PROPOSAL_SENT", "PAID_CUSTOMER", "REPEAT_PURCHASE", "SPONSOR_PAYMENT"}
    commercial_intent_total = sum(1 for t in event_types if t in commercial_intent_stages)
    qualified_conversations_total = sum(1 for t in event_types if t in qualified_stages)
    proposals_sent_total = sum(1 for t in event_types if t in proposal_stages)
    paying_customers_total = sum(1 for t in event_types if t in {"PAID_CUSTOMER", "SPONSOR_PAYMENT"})
    repeat_purchases_total = sum(1 for t in event_types if t == "REPEAT_PURCHASE")
    x_native_payout_events = [r for r in business_events if str(r["event_type"]).upper() == "X_NATIVE_PAYOUT"]
    x_attributed_revenue_cny = round(sum(float(r["amount_cny"] or 0) for r in business_events if str(r["event_type"]).upper() in {"PAID_CUSTOMER", "REPEAT_PURCHASE", "SPONSOR_PAYMENT", "X_NATIVE_PAYOUT"}), 2)
    x_native_payout_cny = round(sum(float(r["amount_cny"] or 0) for r in x_native_payout_events), 2)

    snapshots = con.execute(
        "SELECT * FROM account_snapshot WHERE snapshot_date>=? AND snapshot_date<=? ORDER BY snapshot_date",
        (start.date().isoformat(), as_of.isoformat()),
    ).fetchall()
    latest_account = snapshots[-1] if snapshots else None
    known_profile = [int(r["profile_visits"]) for r in snapshots if r["profile_visits"] is not None]
    profile_visits = sum(known_profile) if known_profile else None
    monetization_signals = sum(int(r["monetization_signals"] or 0) for r in snapshots) if snapshots else None

    ops = con.execute(
        "SELECT operator_minutes FROM daily_ops WHERE ops_date>=? AND ops_date<=? AND operator_minutes IS NOT NULL ORDER BY ops_date",
        (start.date().isoformat(), as_of.isoformat()),
    ).fetchall()
    op_minutes = [float(r["operator_minutes"]) for r in ops]

    exp = get_experiment(con) or {}
    baseline_followers = int(exp.get("baseline_followers") or 0)
    follower_total = int(latest_account["followers"]) if latest_account and latest_account["followers"] is not None else None
    follower_delta = follower_total - baseline_followers if follower_total is not None else None

    return {
        "cycle_count": len(cycles),
        "cycle_success_rate": round(cycle_rate, 4) if cycle_rate is not None else None,
        "qualified_alerts_total": len(alerts),
        "median_alert_latency_minutes": _median(latencies),
        "reviewed_total": len(decisions),
        "review_worth_rate": round(worth_rate, 4) if worth_rate is not None else None,
        "executable_opportunities_total": len(executable),
        "median_target_search_minutes": _median(search_minutes),
        "published_actions_total": len(actions),
        "original_posts_total": len(original_posts),
        "reply_actions_total": len(reply_actions),
        "actions_with_outcome": len(latest_outcomes),
        "offer_live_total": offer_live_total,
        "commercial_intent_total": commercial_intent_total,
        "qualified_conversations_total": qualified_conversations_total,
        "proposals_sent_total": proposals_sent_total,
        "paying_customers_total": paying_customers_total,
        "repeat_purchases_total": repeat_purchases_total,
        "x_attributed_revenue_cny": x_attributed_revenue_cny,
        "x_native_payout_cny": x_native_payout_cny,
        "median_impressions": _median([float(v) for v in impressions]),
        "max_impressions": max(impressions) if impressions else None,
        "actions_over_100_impressions": sum(1 for v in impressions if v >= 100),
        "actions_over_300_impressions": sum(1 for v in impressions if v >= 300),
        "actions_over_1000_impressions": sum(1 for v in impressions if v >= 1000),
        "followers_total": follower_total,
        "follower_delta": follower_delta,
        "profile_visits_total": profile_visits,
        "monetization_signals": monetization_signals,
        "median_operator_minutes_per_day": _median(op_minutes),
        "operator_days_recorded": len(op_minutes),
    }


def _threshold(metric: Any, *, minimum: float | None = None, maximum: float | None = None) -> bool | None:
    if metric is None:
        return None
    if minimum is not None:
        return float(metric) >= float(minimum)
    if maximum is not None:
        return float(metric) <= float(maximum)
    return None


def evaluate_gate(day: int, metrics: dict[str, Any], kpi: dict[str, Any]) -> dict[str, Any]:
    milestone_days = [3, 7, 10, 15, 30]
    due = max([d for d in milestone_days if d <= day], default=None)
    next_due = min([d for d in milestone_days if d >= day], default=30)
    eval_day = due or next_due
    gate = kpi["milestone"][f"day{eval_day}"]

    process_specs = {
        "cycle_success_rate": ("cycle_success_rate_min", "min"),
        "median_alert_latency_minutes": ("median_alert_latency_minutes_max", "max"),
        "review_worth_rate": ("review_worth_rate_min", "min"),
        "reply_actions_total": ("reply_actions_total_min", "min"),
        "original_posts_total": ("original_posts_total_min", "min"),
        "median_operator_minutes_per_day": ("median_operator_minutes_per_day_max", "max"),
    }
    process_checks: dict[str, bool | None] = {}
    for metric_name, (target_name, direction) in process_specs.items():
        if gate.get(target_name) is None:
            continue
        if direction == "min":
            process_checks[metric_name] = _threshold(metrics.get(metric_name), minimum=gate[target_name])
        else:
            process_checks[metric_name] = _threshold(metrics.get(metric_name), maximum=gate[target_name])

    growth_specs = {
        "followers_total": "followers_total_min",
        "max_impressions": "max_impressions_min",
        "actions_over_100_impressions": "actions_over_100_impressions_min",
        "actions_over_300_impressions": "actions_over_300_impressions_min",
        "actions_over_1000_impressions": "actions_over_1000_impressions_min",
    }
    business_checks: dict[str, bool | None] = {}
    for metric_name, target_name in growth_specs.items():
        if gate.get(target_name) is not None:
            business_checks[metric_name] = _threshold(metrics.get(metric_name), minimum=gate[target_name])

    process_pass = bool(process_checks) and all(v is True for v in process_checks.values())
    business_pass = bool(business_checks) and all(v is True for v in business_checks.values())

    if due is None:
        status = "PRE_GATE"
    elif process_pass and business_pass:
        status = "GREEN_GROWTH_CONTINUE"
    elif process_pass:
        status = "AMBER_GROWTH_GAP"
    else:
        status = "RED_FUNNEL_OR_MEASUREMENT"

    return {
        "experiment_day": day,
        "evaluated_milestone_day": eval_day,
        "milestone_is_due": due is not None,
        "status": status,
        "process_pass": process_pass,
        "business_pass": business_pass,
        "business_signal_mode": gate.get("business_signal_mode"),
        "process_checks": process_checks,
        "business_checks": business_checks,
        "targets": gate,
    }


def diagnose(metrics: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
    t = gate["targets"]
    if metrics["cycle_count"] == 0 or metrics["cycle_success_rate"] is None:
        return {"bottleneck": "RUNTIME_OR_MEASUREMENT", "actions": ["Restore live collection/review evidence before changing growth strategy.", "Do not add unrelated infrastructure."]}
    if metrics["cycle_success_rate"] < float(t.get("cycle_success_rate_min", 0)):
        return {"bottleneck": "RUNTIME_RELIABILITY", "actions": ["Fix only the recurring runtime/source error while healthy collectors continue.", "Do not change content strategy until signal delivery is reliable."]}
    if t.get("review_worth_rate_min") is not None and metrics.get("review_worth_rate") is not None and metrics["review_worth_rate"] < float(t["review_worth_rate_min"]):
        return {"bottleneck": "ALERT_PRECISION", "actions": ["Tighten only the false-positive rule/source pattern evidenced by today's review.", "Do not increase alert volume until precision improves."]}

    if not gate.get("milestone_is_due"):
        eval_day = max(1, int(gate.get("evaluated_milestone_day", 1)))
        current_day = max(1, int(gate.get("experiment_day", 1)))
        def paced(target_key: str) -> int:
            target = int(t.get(target_key, 0))
            return max(1, (target * current_day + eval_day - 1) // eval_day) if target else 0
        if t.get("reply_actions_total_min") and metrics["reply_actions_total"] < paced("reply_actions_total_min"):
            return {"bottleneck": "REPLY_ACQUISITION_PACE", "actions": ["Use the next highest-quality personal Feishu signals to publish enough early, useful replies to stay on milestone pace.", "Do not compensate with generic reply volume; target relevance and timing remain mandatory."]}
        if t.get("original_posts_total_min") and metrics["original_posts_total"] < paced("original_posts_total_min"):
            return {"bottleneck": "ORIGINAL_CONTENT_PACE", "actions": ["Convert the strongest current China Tech signal into one differentiated original post.", "Keep the post native/zero-click first and add the source link only secondarily if needed."]}
        if metrics["published_actions_total"] > 0 and metrics["actions_with_outcome"] < max(1, metrics["published_actions_total"] // 2):
            return {"bottleneck": "MEASUREMENT_GAP", "actions": ["Capture current impressions for published replies/originals and update the follower snapshot.", "Unknown outcome metrics must remain null rather than zero."]}
        if t.get("max_impressions_min") is not None and (metrics.get("max_impressions") or 0) < float(t["max_impressions_min"]):
            return {"bottleneck": "DISTRIBUTION", "actions": ["Change one distribution variable: target-post selection/timing for replies or hook/angle for originals.", "Prefer relevant high-attention conversations and native text over link-first posts."]}
        if t.get("followers_total_min") is not None:
            baseline = 4
            target = int(t["followers_total_min"])
            paced_followers = baseline + max(1, ((target - baseline) * current_day + eval_day - 1) // eval_day)
            current_followers = metrics.get("followers_total")
            if current_followers is None:
                return {"bottleneck": "FOLLOWER_MEASUREMENT_GAP", "actions": ["Record today's follower count before making another growth change.", "Follower growth is the primary POC KPI."]}
            if current_followers < paced_followers:
                return {"bottleneck": "FOLLOWER_CONVERSION", "actions": ["Inspect which high-impression actions failed to convert profile visitors into follows; tighten profile promise and topic/target relevance before increasing output.", "Change only one profile/content-positioning variable before the next review."]}

    if gate["process_pass"] and not gate["business_pass"]:
        missing = [k for k, v in gate["business_checks"].items() if v is not True]
        first = missing[0] if missing else "followers_total"
        mapping = {
            "followers_total": ("FOLLOWER_GROWTH_BELOW_TARGET", "Prioritize target accounts/topics that produce relevant follows, and verify the profile gives a clear reason to follow."),
            "max_impressions": ("NO_BREAKOUT_DISTRIBUTION", "Improve one hook/timing/target variable until at least one action materially exceeds the Day-0 reach baseline."),
            "actions_over_100_impressions": ("DISTRIBUTION_NOT_REPEATABLE", "Repeat the topic/target pattern from the strongest action rather than broadening content themes."),
            "actions_over_300_impressions": ("DISTRIBUTION_NOT_SCALING", "Increase concentration on proven target accounts and signature topics; do not broaden the niche."),
            "actions_over_1000_impressions": ("NO_LARGE_REACH_POSTS", "Create stronger original analysis around the highest-attention China Tech events and continue early strategic replies."),
        }
        code, action = mapping.get(first, ("GROWTH_GAP", "Fix the first missing growth-funnel stage before changing infrastructure."))
        return {"bottleneck": code, "actions": [action, "Change at most one growth variable before the next daily review."]}
    if gate["business_pass"]:
        return {"bottleneck": "NONE_PRIMARY", "actions": ["Continue the proven target/topic/content pattern and scale it carefully.", "Do not monetize aggressively before the audience-size readiness gate unless a highly aligned inbound opportunity appears."]}
    return {"bottleneck": "INSUFFICIENT_EVIDENCE", "actions": ["Complete the next missing follower-growth evidence step.", "Do not treat impressions without follower conversion as success."]}


def render_markdown(as_of: date, metrics: dict[str, Any], gate: dict[str, Any], diagnosis: dict[str, Any]) -> str:
    lines = [
        f"# China Tech X Daily Business Review — {as_of.isoformat()}",
        "",
        f"- Experiment day: **{gate['experiment_day']}**",
        f"- KPI status: **{gate['status']}**",
        f"- Evaluated milestone: **Day {gate['evaluated_milestone_day']}**",
        f"- Primary bottleneck: **{diagnosis['bottleneck']}**",
        "",
        "## Funnel Metrics",
        "",
    ]
    for k in [
        "cycle_count","cycle_success_rate","qualified_alerts_total","median_alert_latency_minutes",
        "reviewed_total","review_worth_rate","executable_opportunities_total","median_target_search_minutes",
        "published_actions_total","original_posts_total","reply_actions_total","actions_with_outcome",
        "median_impressions","max_impressions","actions_over_100_impressions","actions_over_300_impressions",
        "actions_over_1000_impressions","followers_total","follower_delta","profile_visits_total",
        "median_operator_minutes_per_day",
    ]:
        lines.append(f"- {k}: `{metrics.get(k)}`")
    lines += ["", "## Gate Checks", ""]
    for k, v in gate["process_checks"].items():
        lines.append(f"- process.{k}: `{v}`")
    for k, v in gate["business_checks"].items():
        lines.append(f"- growth.{k}: `{v}`")
    lines.append(f"- business_pass: `{gate['business_pass']}`")
    lines += ["", "## Corrective Action", ""]
    for a in diagnosis["actions"][:2]:
        lines.append(f"- {a}")
    lines += [
        "",
        "## Operating Rule",
        "",
        "If KPI is GREEN, continue the proven direction. If it is AMBER/RED, diagnose the first broken funnel stage and change at most one business variable plus one instrumentation fix before the next review. Business evidence outranks infrastructure completion.",
        "",
    ]
    return "\n".join(lines)


def build_review(con: sqlite3.Connection, root: Path, as_of: date) -> dict[str, Any]:
    exp = get_experiment(con)
    if not exp:
        return {"status": "SHADOW_NOT_STARTED", "as_of": as_of.isoformat(), "reason": "experiment_state.started_at is empty"}
    day = experiment_day(exp["started_at"], as_of)
    metrics = collect_metrics(con, exp["started_at"], as_of)
    gate = evaluate_gate(day, metrics, load_kpi(root))
    diagnosis = diagnose(metrics, gate)
    return {
        "status": gate["status"],
        "as_of": as_of.isoformat(),
        "metrics": metrics,
        "gate": gate,
        "diagnosis": diagnosis,
        "markdown": render_markdown(as_of, metrics, gate, diagnosis),
    }
