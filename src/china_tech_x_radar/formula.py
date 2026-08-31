from __future__ import annotations

import sqlite3
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def follower_tier(n: int | None) -> str:
    if n is None:
        return "UNKNOWN"
    if n < 10_000:
        return "LT_10K"
    if n < 100_000:
        return "10K_100K"
    if n < 1_000_000:
        return "100K_1M"
    return "GE_1M"


def age_bucket(minutes: float | None) -> str:
    if minutes is None:
        return "UNKNOWN"
    if minutes <= 10:
        return "0_10M"
    if minutes <= 30:
        return "10_30M"
    if minutes <= 60:
        return "30_60M"
    if minutes <= 180:
        return "1_3H"
    if minutes <= 360:
        return "3_6H"
    return "GT_6H"


def latest_action_rows(con: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = con.execute(
        """
        SELECT p.*, o.impressions, o.engagements, o.likes, o.replies, o.reposts, o.quotes,
               o.bookmarks, o.profile_visits, o.captured_at AS outcome_captured_at,
               s.topic AS signal_topic, s.source_name
        FROM published_action p
        JOIN signal s ON s.id=p.signal_id
        LEFT JOIN outcome_snapshot o ON o.id=(
            SELECT oo.id FROM outcome_snapshot oo WHERE oo.action_id=p.id ORDER BY oo.captured_at DESC LIMIT 1
        )
        ORDER BY p.posted_at
        """
    ).fetchall()
    out=[]
    for r in rows:
        d=dict(r)
        d["target_tier"] = follower_tier(d.get("target_account_followers"))
        d["target_age_bucket"] = age_bucket(d.get("target_post_age_minutes"))
        imp=d.get("impressions")
        eng=d.get("engagements")
        d["engagement_rate"] = (float(eng)/float(imp)) if imp and eng is not None else None
        out.append(d)
    return out


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    imps=[int(r["impressions"]) for r in rows if r.get("impressions") is not None]
    ers=[float(r["engagement_rate"]) for r in rows if r.get("engagement_rate") is not None]
    return {
        "samples": len(rows),
        "samples_with_impressions": len(imps),
        "median_impressions": round(float(statistics.median(imps)), 1) if imps else None,
        "max_impressions": max(imps) if imps else None,
        "pct_ge_100": round(sum(1 for x in imps if x >= 100)/len(imps), 3) if imps else None,
        "pct_ge_300": round(sum(1 for x in imps if x >= 300)/len(imps), 3) if imps else None,
        "pct_ge_1000": round(sum(1 for x in imps if x >= 1000)/len(imps), 3) if imps else None,
        "median_engagement_rate": round(float(statistics.median(ers)), 4) if ers else None,
    }


def group_dimension(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        value=row.get(key)
        groups[str(value if value not in (None, "") else "UNKNOWN")].append(row)
    result=[]
    for value, items in groups.items():
        result.append({"value": value, **_summary(items)})
    return sorted(result, key=lambda x: ((x["median_impressions"] or -1), x["samples"]), reverse=True)


def combo_report(rows: list[dict[str, Any]], min_samples: int = 2) -> list[dict[str, Any]]:
    keys=("event_type","target_tier","target_age_bucket","angle_type","media_type")
    groups: dict[tuple[str,...], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        combo=tuple(str(r.get(k) or "UNKNOWN") for k in keys)
        groups[combo].append(r)
    out=[]
    for combo,items in groups.items():
        if len(items)<min_samples:
            continue
        out.append({**dict(zip(keys,combo)), **_summary(items)})
    return sorted(out, key=lambda x: ((x["median_impressions"] or -1), x["samples"]), reverse=True)



def follower_cohorts(con: sqlite3.Connection, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tz=ZoneInfo("Asia/Shanghai")
    exp=con.execute("SELECT baseline_followers FROM experiment_state WHERE id=1").fetchone()
    previous=int(exp[0]) if exp and exp[0] is not None else None
    snapshots=con.execute("SELECT snapshot_date,followers,profile_visits FROM account_snapshot WHERE followers IS NOT NULL ORDER BY snapshot_date").fetchall()
    actions_by_day: dict[str,list[dict[str,Any]]]=defaultdict(list)
    for r in rows:
        dt=_dt(r.get("posted_at"))
        if dt:
            actions_by_day[dt.astimezone(tz).date().isoformat()].append(r)
    out=[]
    for snap in snapshots:
        day=str(snap["snapshot_date"])
        followers=int(snap["followers"])
        delta=followers-previous if previous is not None else None
        previous=followers
        acts=actions_by_day.get(day,[])
        out.append({
            "date": day,
            "followers": followers,
            "follower_delta": delta,
            "profile_visits": snap["profile_visits"],
            "actions": len(acts),
            "reply_actions": sum(1 for a in acts if str(a.get("action_type") or "").upper()=="REPLY"),
            "original_posts": sum(1 for a in acts if str(a.get("action_type") or "").upper()=="ORIGINAL"),
            "median_impressions": _summary(acts)["median_impressions"] if acts else None,
            "event_types": sorted({str(a.get("event_type") or "UNKNOWN") for a in acts}),
            "target_tiers": sorted({str(a.get("target_tier") or "UNKNOWN") for a in acts if str(a.get("action_type") or "").upper()=="REPLY"}),
            "target_age_buckets": sorted({str(a.get("target_age_bucket") or "UNKNOWN") for a in acts if str(a.get("action_type") or "").upper()=="REPLY"}),
            "angles": sorted({str(a.get("angle_type") or "UNKNOWN") for a in acts}),
        })
    return out


def follower_positive_patterns(cohorts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result={}
    for field in ["event_types","target_tiers","target_age_buckets","angles"]:
        stats: dict[str,dict[str,int]]=defaultdict(lambda:{"positive_days":0,"nonpositive_days":0,"follower_gain_on_days":0})
        for c in cohorts:
            delta=c.get("follower_delta")
            if delta is None or not c.get("actions"):
                continue
            for value in c.get(field,[]):
                if delta>0:
                    stats[value]["positive_days"]+=1
                    stats[value]["follower_gain_on_days"]+=int(delta)
                else:
                    stats[value]["nonpositive_days"]+=1
        rows=[]
        for value,d in stats.items():
            total=d["positive_days"]+d["nonpositive_days"]
            rows.append({"value":value,**d,"observed_days":total,"positive_day_rate":round(d["positive_days"]/total,3) if total else None})
        result[field]=sorted(rows,key=lambda x:(x["positive_days"],x["follower_gain_on_days"],x["observed_days"]),reverse=True)
    return result

def build_formula_report(con: sqlite3.Connection, min_samples: int = 2) -> dict[str, Any]:
    rows=latest_action_rows(con)
    dimensions={}
    for key in ["action_type","event_type","signal_topic","target_account","target_tier","target_age_bucket","angle_type","hook_type","media_type","has_external_link"]:
        dimensions[key]=group_dimension(rows,key)
    combos=combo_report(rows,min_samples=min_samples)
    total=_summary(rows)
    cohorts=follower_cohorts(con,rows)
    positive_patterns=follower_positive_patterns(cohorts)
    return {
        "status": "INSUFFICIENT_SAMPLES" if len(rows)<5 else "FORMULA_SEARCH_ACTIVE",
        "total": total,
        "dimensions": dimensions,
        "repeated_combinations": combos[:20],
        "daily_follower_cohorts": cohorts[-30:],
        "follower_positive_patterns": positive_patterns,
        "rule": "Do not declare a growth formula from one breakout post. Prefer combinations with >=3 samples; >=5 is stronger evidence. Follower causality is evaluated at day/cohort level using account snapshots, not falsely attributed to one overlapping action.",
    }
