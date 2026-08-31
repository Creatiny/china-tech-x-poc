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
        origin = _dt(r["published_at"]) or _dt(r["discovered_at"])
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

    snapshots = con.execute(
        "SELECT * FROM account_snapshot WHERE snapshot_date>=? AND snapshot_date<=? ORDER BY snapshot_date",
        (start.date().isoformat(), as_of.isoformat()),
    ).fetchall()
    latest_account = snapshots[-1] if snapshots else None
    profile_visits = sum(int(r["profile_visits"] or 0) for r in snapshots)
    monetization_signals = sum(int(r["monetization_signals"] or 0) for r in snapshots)

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
        "actions_with_outcome": len(latest_outcomes),
        "median_impressions": _median([float(v) for v in impressions]),
        "max_impressions": max(impressions) if impressions else None,
        "actions_over_100_impressions": sum(1 for v in impressions if v >= 100),
        "actions_over_300_impressions": sum(1 for v in impressions if v >= 300),
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

    process_checks: dict[str, bool | None] = {
        "cycle_success_rate": _threshold(metrics["cycle_success_rate"], minimum=gate.get("cycle_success_rate_min")),
        "median_alert_latency_minutes": _threshold(metrics["median_alert_latency_minutes"], maximum=gate.get("median_alert_latency_minutes_max")),
        "review_worth_rate": _threshold(metrics["review_worth_rate"], minimum=gate.get("review_worth_rate_min")),
        "qualified_alerts_total": _threshold(metrics["qualified_alerts_total"], minimum=gate.get("qualified_alerts_total_min")),
        "executable_opportunities_total": _threshold(metrics["executable_opportunities_total"], minimum=gate.get("executable_opportunities_total_min")),
        "published_actions_total": _threshold(metrics["published_actions_total"], minimum=gate.get("published_actions_total_min")),
    }
    if gate.get("median_operator_minutes_per_day_max") is not None:
        process_checks["median_operator_minutes_per_day"] = _threshold(
            metrics["median_operator_minutes_per_day"], maximum=gate["median_operator_minutes_per_day_max"]
        )

    mode = gate.get("business_signal_mode")
    imp_max = _threshold(metrics["max_impressions"], minimum=gate.get("max_impressions_min")) if gate.get("max_impressions_min") is not None else None
    follower_delta = _threshold(metrics["follower_delta"], minimum=gate.get("follower_delta_min")) if gate.get("follower_delta_min") is not None else None
    profile = _threshold(metrics["profile_visits_total"], minimum=gate.get("profile_visits_total_min")) if gate.get("profile_visits_total_min") is not None else None
    over100 = _threshold(metrics["actions_over_100_impressions"], minimum=gate.get("actions_over_100_impressions_min")) if gate.get("actions_over_100_impressions_min") is not None else None
    median_imp = _threshold(metrics["median_impressions"], minimum=gate.get("median_impressions_min")) if gate.get("median_impressions_min") is not None else None
    over300 = _threshold(metrics["actions_over_300_impressions"], minimum=gate.get("actions_over_300_impressions_min")) if gate.get("actions_over_300_impressions_min") is not None else None
    follower_total = _threshold(metrics["followers_total"], minimum=gate.get("follower_total_min")) if gate.get("follower_total_min") is not None else None
    monetization = _threshold(metrics["monetization_signals"], minimum=gate.get("monetization_signals_min")) if gate.get("monetization_signals_min") is not None else None

    business_checks: dict[str, Any] = {
        "max_impressions": imp_max,
        "follower_delta": follower_delta,
        "profile_visits": profile,
        "actions_over_100": over100,
        "median_impressions": median_imp,
        "actions_over_300": over300,
        "followers_total": follower_total,
        "monetization_signals": monetization,
    }
    if mode == "ANY":
        candidates = [x for x in (imp_max, follower_delta, profile) if x is not None]
        business_pass = any(candidates) if candidates else None
    elif mode == "ANY_GROWTH_PLUS_DISTRIBUTION":
        distribution = any(x for x in (over100, imp_max) if x is not None)
        growth_candidates = [x for x in (follower_delta, profile) if x is not None]
        growth = any(growth_candidates) if growth_candidates else False
        business_pass = distribution and growth
    elif mode == "DISTRIBUTION_AND_GROWTH":
        distribution = bool(median_imp) and any(x for x in (over100, imp_max) if x is not None)
        business_pass = distribution and bool(follower_delta)
    else:
        business_pass = bool(median_imp) and bool(over300) and bool(imp_max) and bool(follower_total) and bool(monetization)

    process_known = [v for v in process_checks.values() if v is not None]
    process_pass = bool(process_known) and all(process_known) and len(process_known) == len(process_checks)

    if due is None:
        status = "PRE_GATE"
    elif process_pass and business_pass:
        status = "GREEN_CONTINUE"
    elif process_pass:
        status = "AMBER_BUSINESS_SIGNAL"
    else:
        status = "RED_FUNNEL_OR_MEASUREMENT"

    return {
        "experiment_day": day,
        "evaluated_milestone_day": eval_day,
        "milestone_is_due": due is not None,
        "status": status,
        "process_pass": process_pass,
        "business_pass": business_pass,
        "process_checks": process_checks,
        "business_checks": business_checks,
        "targets": gate,
    }


def diagnose(metrics: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
    t = gate["targets"]
    if metrics["cycle_count"] < 5:
        return {"bottleneck": "RUNTIME_OR_MEASUREMENT", "actions": ["Verify launchd cycles and review DB path before changing content strategy.", "Do not add sources until runtime evidence is complete."]}
    if metrics["cycle_success_rate"] is not None and metrics["cycle_success_rate"] < float(t.get("cycle_success_rate_min", 0)):
        return {"bottleneck": "RUNTIME_RELIABILITY", "actions": ["Fix the top recurring source/runtime error; keep other healthy sources running.", "Do not change scoring/content until cycle reliability recovers."]}
    if metrics["qualified_alerts_total"] < int(t.get("qualified_alerts_total_min", 0)):
        return {"bottleneck": "SOURCE_COVERAGE", "actions": ["Inspect missed China Tech events and add/tune only the source class that would have caught them.", "Do not broaden keywords indiscriminately; preserve precision."]}
    if metrics["review_worth_rate"] is not None and metrics["review_worth_rate"] < float(t.get("review_worth_rate_min", 0)):
        return {"bottleneck": "ALERT_PRECISION", "actions": ["Review false-positive reasons and tighten source/entity/material-event rules.", "Change at most one scoring/rule family before the next daily review."]}
    if metrics["executable_opportunities_total"] < int(t.get("executable_opportunities_total_min", 0)):
        return {"bottleneck": "TARGET_DISCOVERY", "actions": ["Measure target-search time and which entities repeatedly lack a strong X target.", "Only then prioritize target-account watching/browser/X-native discovery."]}
    if metrics["published_actions_total"] < int(t.get("published_actions_total_min", 0)):
        return {"bottleneck": "HUMAN_EXECUTION_OR_REPLY_SELECTION", "actions": ["Compare executable opportunities with skipped decisions and operator time.", "Reduce decision friction before increasing alert volume."]}
    if metrics["published_actions_total"] > 0 and metrics["actions_with_outcome"] < max(1, metrics["published_actions_total"] // 2):
        return {"bottleneck": "MEASUREMENT_GAP", "actions": ["Capture current impressions/engagement for published test actions.", "Record daily followers/profile visits so business KPI can be evaluated."]}
    if gate["process_pass"] and not gate["business_pass"]:
        return {"bottleneck": "DISTRIBUTION_REPLY_QUALITY_OR_ACCOUNT_CONVERSION", "actions": ["Compare winning vs weak targets by target-post age, account size, topic, and reply angle; change one variable next.", "Prioritize earlier/high-authority targets and sharper China-specific evidence before adding infrastructure."]}
    if gate["business_pass"]:
        return {"bottleneck": "NONE_PRIMARY", "actions": ["Continue the current direction without broad architecture changes.", "Scale only the source/target patterns already producing distribution."]}
    return {"bottleneck": "INSUFFICIENT_EVIDENCE", "actions": ["Complete today's decisions and outcome inputs.", "Avoid strategic changes until the missing funnel stage is observed."]}


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
        "published_actions_total","actions_with_outcome","median_impressions","max_impressions",
        "actions_over_100_impressions","actions_over_300_impressions","followers_total","follower_delta",
        "profile_visits_total","monetization_signals","median_operator_minutes_per_day",
    ]:
        lines.append(f"- {k}: `{metrics.get(k)}`")
    lines += ["", "## Gate Checks", ""]
    for k, v in gate["process_checks"].items():
        lines.append(f"- process.{k}: `{v}`")
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
