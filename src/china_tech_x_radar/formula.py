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



def reply_surface_bucket(score: int | None, views_per_reply: float | None) -> str:
    if score is None and views_per_reply is None:
        return "UNKNOWN"
    score_i = int(score or 0)
    vpr = float(views_per_reply or 0.0)
    if score_i >= 6 or vpr >= 3000:
        return "OPEN"
    if score_i >= 3 or vpr >= 300:
        return "MODERATE"
    return "CROWDED"

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
        d["reply_surface_bucket"] = reply_surface_bucket(
            d.get("target_reply_surface_score_at_reply"), d.get("target_views_per_reply_at_reply")
        )
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




def build_creator_feedback_map(con: sqlite3.Connection, *, min_samples: int = 3) -> dict[str, dict[str, Any]]:
    """Build conservative creator-level priors from our own reply outcomes and clean follower days.

    Impression feedback activates after `min_samples`. Follower growth is allowed to contribute only
    when snapshots are on consecutive days and exactly one published action occurred on that day;
    even then it is a +1 maximum weak prior, never a negative penalty.
    """
    rows = con.execute(
        """
        SELECT lower(ltrim(coalesce(p.target_account,s.author,''),'@')) AS creator,
               o.impressions, o.engagements
          FROM published_action p
          JOIN signal s ON s.id=p.signal_id
          JOIN outcome_snapshot o ON o.id=(
              SELECT oo.id FROM outcome_snapshot oo WHERE oo.action_id=p.id ORDER BY oo.captured_at DESC LIMIT 1
          )
         WHERE upper(p.action_type)='REPLY' AND o.impressions IS NOT NULL
        """
    ).fetchall()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        creator = str(row["creator"] or "").strip()
        if creator:
            grouped[creator].append(dict(row))

    # Build conservative follower-growth evidence. Do not attribute multi-action days.
    tz = ZoneInfo("Asia/Shanghai")
    snapshots = con.execute(
        "SELECT snapshot_date,followers FROM account_snapshot WHERE followers IS NOT NULL ORDER BY snapshot_date"
    ).fetchall()
    clean_delta_by_day: dict[str, int] = {}
    previous_day: str | None = None
    previous_followers: int | None = None
    for snap in snapshots:
        day = str(snap["snapshot_date"])
        followers = int(snap["followers"])
        if previous_day is not None and previous_followers is not None:
            try:
                gap = (datetime.fromisoformat(day).date() - datetime.fromisoformat(previous_day).date()).days
            except Exception:
                gap = 0
            if gap == 1:
                clean_delta_by_day[day] = followers - previous_followers
        previous_day, previous_followers = day, followers

    actions_by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    action_rows = con.execute(
        """SELECT p.action_type,p.target_account,p.posted_at,s.author
               FROM published_action p JOIN signal s ON s.id=p.signal_id
               WHERE p.posted_at IS NOT NULL"""
    ).fetchall()
    for row in action_rows:
        dt = _dt(row["posted_at"])
        if dt is None:
            continue
        day = dt.astimezone(tz).date().isoformat()
        actions_by_day[day].append(dict(row))
    growth_by_creator: dict[str, list[int]] = defaultdict(list)
    for day, delta in clean_delta_by_day.items():
        actions = actions_by_day.get(day, [])
        if len(actions) != 1:
            continue
        action = actions[0]
        if str(action.get("action_type") or "").upper() != "REPLY":
            continue
        creator = str(action.get("target_account") or action.get("author") or "").strip().casefold().lstrip("@")
        if creator:
            growth_by_creator[creator].append(int(delta))

    out: dict[str, dict[str, Any]] = {}
    for creator in sorted(set(grouped) | set(growth_by_creator)):
        items = grouped.get(creator, [])
        imps = [int(x["impressions"]) for x in items if x.get("impressions") is not None]
        med = float(statistics.median(imps)) if imps else None
        samples = len(imps)
        impression_score = 0
        if samples >= min_samples and med is not None:
            if med >= 300:
                impression_score = 2
            elif med >= 100:
                impression_score = 1
            elif med < 30:
                impression_score = -1
        growth = growth_by_creator.get(creator, [])
        growth_score = 1 if len(growth) >= 2 and float(statistics.median(growth)) > 0 else 0
        score = max(-1, min(3, impression_score + growth_score))
        out[creator] = {
            "score": score,
            "samples": samples,
            "median_impressions": round(med, 1) if med is not None else None,
            "growth_days": len(growth),
            "follower_gain_on_clean_days": sum(growth),
        }
    return out


def follower_cohorts(con: sqlite3.Connection, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tz=ZoneInfo("Asia/Shanghai")
    exp=con.execute("SELECT baseline_followers FROM experiment_state WHERE id=1").fetchone()
    previous=int(exp[0]) if exp and exp[0] is not None else None
    previous_day: str | None = None
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
        raw_delta=followers-previous if previous is not None else None
        gap_days = None
        if previous_day is not None:
            try:
                gap_days = (datetime.fromisoformat(day).date() - datetime.fromisoformat(previous_day).date()).days
            except Exception:
                gap_days = None
        attribution_eligible = previous_day is not None and gap_days == 1
        delta = raw_delta if attribution_eligible else None
        previous=followers
        previous_day=day
        acts=actions_by_day.get(day,[])
        out.append({
            "date": day,
            "followers": followers,
            "follower_delta": delta,
            "raw_follower_delta_since_previous_snapshot": raw_delta,
            "snapshot_gap_days": gap_days,
            "follower_attribution_eligible": attribution_eligible,
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


def creator_acquisition_report(con: sqlite3.Connection, *, days: int = 30, min_feedback_samples: int = 3) -> list[dict[str, Any]]:
    """Rank monitored X creators by our own reply outcomes + observed parent-post reach.

    This is a reporting surface, not a bypass around editorial gates. It makes expansion/retention
    decisions evidence-based: actual Reply outcomes first, then the creator's observed distribution.
    """
    cutoff = datetime.now(timezone.utc).timestamp() - max(1, int(days)) * 86400
    cutoff_iso = datetime.fromtimestamp(cutoff, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    rows = con.execute(
        """SELECT source_id,author,priority,observed_views,distribution_score,reply_surface_score,reply_acquisition_score,
                      observed_replies,views_per_reply,view_velocity_per_min,discovered_at
               FROM signal
              WHERE source_kind='x_profile' AND discovered_at>=?
              ORDER BY discovered_at DESC""",
        (cutoff_iso,),
    ).fetchall()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        creator = str(row["author"] or "").strip().casefold().lstrip("@")
        if creator:
            grouped[creator].append(dict(row))
    feedback = build_creator_feedback_map(con, min_samples=min_feedback_samples)
    out: list[dict[str, Any]] = []
    for creator in sorted(set(grouped) | set(feedback)):
        items = grouped.get(creator, [])
        views = [int(x.get("observed_views") or 0) for x in items if int(x.get("observed_views") or 0) > 0]
        dist = [int(x.get("distribution_score") or 0) for x in items]
        velocities = [float(x.get("view_velocity_per_min") or 0) for x in items if float(x.get("view_velocity_per_min") or 0) > 0]
        surfaces = [int(x.get("reply_surface_score") or 0) for x in items if x.get("observed_replies") is not None]
        acquisitions = [int(x.get("reply_acquisition_score") or 0) for x in items if int(x.get("reply_acquisition_score") or 0) > 0]
        vprs = [float(x.get("views_per_reply")) for x in items if x.get("views_per_reply") is not None]
        fb = feedback.get(creator, {})
        out.append({
            "creator": creator,
            "observed_posts": len(items),
            "qualified_p0_p1": sum(1 for x in items if str(x.get("priority") or "").upper() in {"P0","P1"}),
            "median_parent_views": round(float(statistics.median(views)), 1) if views else None,
            "max_parent_views": max(views) if views else None,
            "median_distribution_score": round(float(statistics.median(dist)), 1) if dist else None,
            "median_reply_surface_score": round(float(statistics.median(surfaces)), 1) if surfaces else None,
            "median_reply_acquisition_score": round(float(statistics.median(acquisitions)), 1) if acquisitions else None,
            "median_views_per_reply": round(float(statistics.median(vprs)), 1) if vprs else None,
            "median_view_velocity_per_min": round(float(statistics.median(velocities)), 2) if velocities else None,
            "reply_samples": int(fb.get("samples", 0)),
            "median_reply_impressions": fb.get("median_impressions"),
            "feedback_score": int(fb.get("score", 0)),
            "growth_days": int(fb.get("growth_days", 0)),
            "follower_gain_on_clean_days": int(fb.get("follower_gain_on_clean_days", 0)),
            "last_observed_at": max((str(x.get("discovered_at") or "") for x in items), default=None),
        })
    return sorted(
        out,
        key=lambda x: (
            x["feedback_score"],
            x["median_reply_impressions"] if x["median_reply_impressions"] is not None else -1,
            x["median_reply_acquisition_score"] if x["median_reply_acquisition_score"] is not None else -1,
            x["median_views_per_reply"] if x["median_views_per_reply"] is not None else -1,
            x["median_parent_views"] if x["median_parent_views"] is not None else -1,
            x["qualified_p0_p1"],
        ),
        reverse=True,
    )

def build_formula_report(con: sqlite3.Connection, min_samples: int = 2) -> dict[str, Any]:
    rows=latest_action_rows(con)
    dimensions={}
    for key in ["action_type","event_type","signal_topic","target_account","target_tier","target_age_bucket","reply_surface_bucket","angle_type","hook_type","media_type","has_external_link"]:
        dimensions[key]=group_dimension(rows,key)
    combos=combo_report(rows,min_samples=min_samples)
    total=_summary(rows)
    cohorts=follower_cohorts(con,rows)
    positive_patterns=follower_positive_patterns(cohorts)
    creator_acquisition=creator_acquisition_report(con)
    return {
        "status": "INSUFFICIENT_SAMPLES" if len(rows)<5 else "FORMULA_SEARCH_ACTIVE",
        "total": total,
        "dimensions": dimensions,
        "repeated_combinations": combos[:20],
        "daily_follower_cohorts": cohorts[-30:],
        "follower_positive_patterns": positive_patterns,
        "creator_acquisition": creator_acquisition[:50],
        "rule": "Do not declare a growth formula from one breakout post. Prefer combinations with >=3 samples; >=5 is stronger evidence. Follower causality is evaluated at day/cohort level using account snapshots, not falsely attributed to one overlapping action. Reply-surface buckets become actionable only after enough published replies have parent competition snapshots.",
    }
