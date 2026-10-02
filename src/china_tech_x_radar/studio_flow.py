"""File-based Studio pilot: immutable inputs, local draft, independent GPT audit.

This module has no publishing or notification capability. The initial operator
is ChatGPT via the existing Mac bridges, not a second scheduler.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path

LOCAL_MODEL = "qwen3.8-27b-4bit"
AUDIT_MODEL = "gpt-6.1-sol"
AUDIT_EFFORT = "high"
SCHEMA = "x-studio-flow-v1"


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(path)


def dt(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone required")
    return parsed.astimezone(timezone.utc)


def request(kind, inputs):
    if kind not in ("card", "review"):
        raise ValueError("unknown task kind")
    result = {"schema": SCHEMA, "kind": kind, "inputs": inputs,
              "policy": {"local_model": LOCAL_MODEL, "audit_model": AUDIT_MODEL,
                         "audit_effort": AUDIT_EFFORT, "fallback": False,
                         "publish": False}}
    result["request_sha256"] = digest(result)
    return result


def validate_request(value):
    body = {k: v for k, v in value.items() if k != "request_sha256"}
    if value != request(value.get("kind"), value.get("inputs")) or digest(body) != value.get("request_sha256"):
        raise ValueError("input or model policy drift")


def review_inputs(con, start, end, as_of):
    start_dt, end_dt, cutoff = dt(start), dt(end), dt(as_of)
    if not start_dt < end_dt <= cutoff:
        raise ValueError("invalid review window")
    # Compare parsed UTC timestamps rather than mixed SQLite timestamp strings.
    # Pick one latest snapshot per unique published action at the cutoff.
    actions = [dict(r) for r in con.execute("SELECT id,action_type,posted_at FROM published_action ORDER BY id")
               if start_dt <= dt(r["posted_at"]) < end_dt]
    latest = {}
    for row in con.execute("SELECT id,action_id,captured_at,impressions,engagements,profile_visits FROM outcome_snapshot"):
        row = dict(row)
        captured = dt(row["captured_at"])
        if captured > cutoff:
            continue
        key = row["action_id"]
        order = (captured, row["id"])
        if key not in latest or order > latest[key][0]:
            latest[key] = (order, row)
    rows = []
    for action in actions:
        snapshot = latest.get(action["id"], (None, {}))[1]
        captured = snapshot.get("captured_at")
        mature = captured is not None and (dt(captured) - dt(action["posted_at"])).total_seconds() >= 86400
        imp, eng = snapshot.get("impressions"), snapshot.get("engagements")
        # Canonical DB calls originals ORIGINAL; editorial packets call them POST.
        lane = str(action["action_type"]).upper()
        cohort = "POST" if lane in ("ORIGINAL", "POST") else "REPLY" if lane == "REPLY" else "UNKNOWN"
        rows.append({**action, "cohort": cohort, "snapshot_id": snapshot.get("id"), "captured_at": captured,
                     "mature": mature, "impressions": imp, "engagements": eng,
                     "engagement_rate": eng / imp if imp and eng is not None else None,
                     "profile_visits": snapshot.get("profile_visits")})
    metrics = {"unique_actions": len(rows), "mature_actions": sum(r["mature"] for r in rows),
               "actions_with_impressions": sum(r["impressions"] is not None for r in rows),
               "actions_with_engagements": sum(r["engagements"] is not None for r in rows),
               "actions_with_profile_visits": sum(r["profile_visits"] is not None for r in rows),
               "unknown_cohort_actions": sum(r["cohort"] == "UNKNOWN" for r in rows),
               "post_follower_attribution": None}
    for lane in ("POST", "REPLY"):
        cohort = [r for r in rows if r["cohort"] == lane and r["mature"]]
        metrics[lane + ".mature_samples"] = len(cohort)
        for field in ("impressions", "engagement_rate"):
            numbers = [r[field] for r in cohort if r[field] is not None]
            metrics[lane + "." + field + "_samples"] = len(numbers)
            metrics[lane + ".median_" + field] = statistics.median(numbers) if numbers else None
    return {"window": {"start": start, "end_exclusive": end, "as_of": as_of},
            "metrics": metrics, "actions": rows,
            "limits": ["One latest snapshot per published action; snapshots are not independent samples.",
                       "Mature means snapshot captured at least 24 hours after posting.",
                       "Missing values remain null; rates use recorded aggregate engagements/impressions.",
                       "POST and REPLY are separate cohorts; this is observational, not a causal experiment.",
                       "Per-post follower attribution is unknown; SENT does not mean POSTED."]}


def validate_draft(req, draft):
    validate_request(req)
    if req["kind"] == "card":
        if not isinstance(draft.get("title"), str) or not 1 <= len(draft["title"]) <= 22:
            raise ValueError("card title length")
        points = draft.get("points")
        if not isinstance(points, list) or not 2 <= len(points) <= 3:
            raise ValueError("card requires 2-3 points")
        known = {f["id"] for f in req["inputs"]["facts"]}
        for p in points:
            if not isinstance(p.get("text"), str) or not 1 <= len(p["text"]) <= 50:
                raise ValueError("card point length")
            if not isinstance(p.get("fact_ids"), list) or not p["fact_ids"] or not set(p["fact_ids"]) <= known:
                raise ValueError("unbound card fact")
    else:
        observations = draft.get("observations")
        if not isinstance(observations, list) or not 1 <= len(observations) <= 4:
            raise ValueError("review observations")
        known = set(req["inputs"]["metrics"])
        for o in observations:
            if o.get("metric_key") not in known or not isinstance(o.get("interpretation"), str) or not o["interpretation"]:
                raise ValueError("unbound review metric")
            if req["inputs"].get("method_revision") == "observational-description-v2":
                if re.search(r"[0-9]|显著|初始可见性|导致", o["interpretation"]):
                    raise ValueError("unsupported precision or causal wording")
        if not isinstance(draft.get("next_experiment"), str) or not draft["next_experiment"]:
            raise ValueError("review experiment missing")
    return True


def local_prompt(req):
    validate_request(req)
    if req["kind"] == "card":
        contract = '只输出JSON {"title":"中文标题22字以内","points":[{"text":"50字以内的事实摘要","fact_ids":["F1"]}]}。共2-3个要点。只使用给定事实；保留未完成、未知及建议的限定，不新增效果、成本或增长宣称。'
    else:
        contract = '只输出JSON {"observations":[{"metric_key":"输入中存在的指标键","interpretation":"简短中文观察"}],"hypotheses":["待验证假设"],"next_experiment":"一个可验证的下一步","limits":["数据限制"]}。1-4个观察。只分析给定真实数据，未知保持未知。小样本不能推导因果，不能归因单条帖子的涨粉。不要把1594次快照当1594条帖子。'
        if req["inputs"].get("method_revision") == "observational-description-v2":
            contract += '指标数值和样本数由程序原样展示，interpretation不要重复写数字。不要使用显著、初始可见性、导致等措辞。这些是不同帖龄的成熟累计快照，不能比较初始分发或同龄增长。REPLY只有少量样本，任何曝光对比只能是观察线索，不能据此确定运营策略。hypotheses可以为空；缺少证据时不要猜算法或粉丝规模原因。limits必须保留全部输入限制。下一步优先补齐可比较帖龄的数据，而非宣称已验证原因。'
    return contract + "\n输入：" + json.dumps(req["inputs"], ensure_ascii=False)


def audit_prompt(req, draft, checks):
    validate_draft(req, draft)
    return ("你是独立审核员。审查原始输入、本地模型候选与确定性检查。不要调用工具或重写成果。"
            "配图需核对实际图片是否可读、溢出、事实与来源、结论限定；复盘需核对去重、时间窗、成熟样本、空值、指标口径及观察和因果。"
            "事实错误、数字编造、来源不支持、布局不合格或数据限制丢失必须REJECT。只能输出JSON "
            '{"decision":"APPROVE或REJECT","issues":["有证据的具体问题"],"reason":"短理由"}。'
            "\n原始请求：" + json.dumps(req, ensure_ascii=False)
            + "\n候选：" + json.dumps(draft, ensure_ascii=False)
            + "\n检查：" + json.dumps(checks, ensure_ascii=False))


def accept(req, draft, audit, checks):
    validate_draft(req, draft)
    if audit.get("model") != AUDIT_MODEL or audit.get("effort") != AUDIT_EFFORT:
        raise ValueError("audit model drift")
    if audit.get("request_sha256") != req["request_sha256"] or audit.get("draft_sha256") != digest(draft):
        raise ValueError("audit is not bound to these bytes")
    verdict = audit.get("verdict", {})
    if not checks or not all(v is True for v in checks.values()) or verdict.get("decision") != "APPROVE" or verdict.get("issues") != []:
        raise ValueError("review required; candidate not accepted")
    return {"status": "APPROVED_FOR_HUMAN_REVIEW", "request_sha256": req["request_sha256"],
            "draft_sha256": digest(draft), "local_model": LOCAL_MODEL,
            "audit_model": AUDIT_MODEL, "audit_effort": AUDIT_EFFORT, "published": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True); p.add_argument("--start", required=True)
    p.add_argument("--end", required=True); p.add_argument("--as-of", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    con = sqlite3.connect(Path(args.db).resolve().as_uri() + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    with con:
        con.execute("BEGIN")
        result = request("review", review_inputs(con, args.start, args.end, args.as_of))
    con.close()
    write_json(args.out, result)
    print(json.dumps({"request_sha256": result["request_sha256"], "metrics": result["inputs"]["metrics"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
