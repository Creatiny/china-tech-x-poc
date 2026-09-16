from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus
from typing import Any
import re


def _match_terms(text: str, terms: list[str]) -> list[str]:
    text = text.casefold()
    out: list[str] = []
    for term in terms:
        t = term.casefold()
        # Latin/alphanumeric short tokens need word boundaries (AI in betrayal, EV in reveals, NIO in innovation).
        # CJK words are normally adjacent without whitespace, so substring matching is required for terms such as 华为/机器人/大模型.
        if re.search(r"[\u3400-\u9fff]", t):
            matched = t in text
        else:
            pattern = r"(?<!\w)" + re.escape(t) + r"(?!\w)"
            matched = bool(re.search(pattern, text))
        if matched:
            out.append(term)
    return out


def _age_minutes(published_at: datetime | None, now: datetime) -> float:
    if published_at is None:
        return 0.0
    return max(0.0, (now - published_at).total_seconds() / 60.0)


def _safe_metric(metrics: dict[str, Any], key: str) -> int:
    try:
        return max(0, int(metrics.get(key) or 0))
    except Exception:
        return 0


def distribution_opportunity(item: dict[str, Any], age_minutes: float) -> dict[str, float | int]:
    """Deterministic pre-editorial distribution signal for direct X posts.

    This is deliberately not a content-quality score. It measures whether a relevant post is
    fresh and already showing signs of entering a larger distribution graph, so a small account
    can spend scarce reply attention where there is actual audience movement.
    """
    metrics = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}
    views = _safe_metric(metrics, "views")
    likes = _safe_metric(metrics, "likes")
    replies = _safe_metric(metrics, "replies")
    reposts = _safe_metric(metrics, "reposts")
    quotes = _safe_metric(metrics, "quotes")
    bookmarks = _safe_metric(metrics, "bookmarks")
    interactions = likes + replies + reposts + quotes + bookmarks
    velocity = float(views) / max(1.0, float(age_minutes))
    engagement_rate = (float(interactions) / float(views)) if views > 0 else 0.0

    freshness = 3 if age_minutes <= 10 else 2 if age_minutes <= 30 else 1 if age_minutes <= 60 else 0
    if velocity >= 500:
        velocity_pts = 6
    elif velocity >= 150:
        velocity_pts = 5
    elif velocity >= 50:
        velocity_pts = 4
    elif velocity >= 15:
        velocity_pts = 3
    elif velocity >= 5:
        velocity_pts = 2
    elif velocity >= 1:
        velocity_pts = 1
    else:
        velocity_pts = 0
    scale_pts = 3 if views >= 10_000 else 2 if views >= 1_000 else 1 if views >= 300 else 0
    engagement_pts = 3 if engagement_rate >= 0.10 else 2 if engagement_rate >= 0.05 else 1 if engagement_rate >= 0.02 else 0
    conversation = replies + quotes
    conversation_pts = 2 if conversation >= 20 else 1 if conversation >= 3 else 0
    score = freshness + velocity_pts + scale_pts + engagement_pts + conversation_pts
    return {
        "distribution_score": int(score),
        "views": views,
        "view_velocity_per_min": round(velocity, 2),
        "engagement_rate": round(engagement_rate, 4),
        "interactions": interactions,
    }



def reply_surface_opportunity(item: dict[str, Any]) -> dict[str, float | int | None]:
    """Estimate how much parent-post audience is available per competing direct reply.

    Missing reply counts are treated as unknown/neutral, never as zero competition. The score is
    intentionally bounded and complements (rather than replaces) distribution momentum.
    """
    metrics = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}
    views = _safe_metric(metrics, "views")
    reply_known = "replies" in metrics and metrics.get("replies") is not None
    quote_known = "quotes" in metrics and metrics.get("quotes") is not None
    replies = _safe_metric(metrics, "replies") if reply_known else None
    quotes = _safe_metric(metrics, "quotes") if quote_known else None
    if not reply_known or views <= 0 or replies is None:
        return {
            "reply_surface_score": 0,
            "reply_competition_known": 0,
            "observed_replies": replies,
            "observed_quotes": quotes,
            "views_per_reply": None,
        }

    views_per_reply = float(views) / float(replies + 1)
    if views_per_reply >= 10_000:
        ratio_pts = 6
    elif views_per_reply >= 3_000:
        ratio_pts = 5
    elif views_per_reply >= 1_000:
        ratio_pts = 4
    elif views_per_reply >= 300:
        ratio_pts = 3
    elif views_per_reply >= 100:
        ratio_pts = 2
    elif views_per_reply >= 30:
        ratio_pts = 1
    else:
        ratio_pts = 0

    low_competition_bonus = 2 if replies <= 2 and views >= 3_000 else 1 if replies <= 10 and views >= 1_000 else 0
    saturation_penalty = 3 if replies >= 1_000 else 2 if replies >= 300 else 1 if replies >= 100 else 0
    score = ratio_pts + low_competition_bonus - saturation_penalty
    # Tiny threads should not look exceptional merely because nobody has replied yet.
    if views < 300:
        score = min(score, 1)
    elif views < 1_000:
        score = min(score, 2)
    score = max(0, min(8, score))
    return {
        "reply_surface_score": int(score),
        "reply_competition_known": 1,
        "observed_replies": int(replies),
        "observed_quotes": int(quotes) if quotes is not None else None,
        "views_per_reply": round(views_per_reply, 1),
    }

def make_x_search_url(title: str, entity: str | None, topic: str | None) -> str:
    if entity and topic:
        q = f'"{entity}" {topic}'
    elif entity:
        q = f'"{entity}"'
    else:
        q = title[:90]
    return f"https://x.com/search?q={quote_plus(q)}&src=typed_query&f=live"


def angle_for(topic: str | None, title: str) -> str:
    t = (topic or "").casefold()
    if any(x in t for x in ("chip", "gpu", "semiconductor", "memory", "dram", "nand")):
        return "Angle: explain what this changes for AI capability, cost, reliability, or deployment; use China supply-chain context only when it materially changes the conclusion."
    if any(x in t for x in ("robot", "humanoid")):
        return "Angle: separate demo hype from deployment economics—cost, reliability, production scale, and actual factory use."
    if any(x in t for x in ("ev", "battery", "autonomous")):
        return "Angle: focus on whether AI/automation is moving from demo to useful deployment, and what changes in cost, reliability, or workflow."
    if any(x in t for x in ("ai", "model", "llm", "agent", "benchmark", "open-source", "open source")):
        return "Angle: judge what this changes for builders and real productivity—capability, cost, reliability, workflow, or verification—not just benchmark rank."
    if any(x in t for x in ("ipo", "funding", "earnings")):
        return "Angle: focus on what the capital event says about demand, capacity expansion, and the competitive cycle."
    return "Angle: do not repeat the headline; identify the concrete consequence for people using AI to build, work, automate, or make decisions."


def classify(item: dict[str, Any], source: dict[str, Any], rules: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    title_text = item.get("title", "")
    text = f"{title_text} {item.get('excerpt','')}"
    entities = _match_terms(text, list(rules.get("china_entities", [])))
    productivity_terms = list(rules.get("productivity_terms", [])) + list(source.get("extra_productivity_terms", []))
    topic_terms = list(rules.get("topic_terms", [])) + list(source.get("extra_topic_terms", []))
    productivity = _match_terms(text, productivity_terms)
    title_entities = _match_terms(title_text, list(rules.get("china_entities", [])))
    topics = _match_terms(text, topic_terms)
    title_topics = _match_terms(title_text, topic_terms)
    high = _match_terms(text, list(rules.get("high_impact_terms", [])))
    noise = _match_terms(text, list(rules.get("noise_terms", [])))
    published = item.get("published_at")
    age = _age_minutes(published, now)
    direct_x_source = source.get("kind") == "x_profile"
    feedback_score = int(source.get("outcome_feedback_score", 0)) if direct_x_source else 0
    feedback_samples = int(source.get("outcome_feedback_samples", 0)) if direct_x_source else 0
    feedback_median = source.get("outcome_feedback_median_impressions") if direct_x_source else None
    feedback_growth_days = int(source.get("outcome_feedback_growth_days", 0)) if direct_x_source else 0
    feedback_follower_gain = int(source.get("outcome_feedback_follower_gain", 0)) if direct_x_source else 0
    dist = distribution_opportunity(item, age) if direct_x_source else {
        "distribution_score": 0, "views": 0, "view_velocity_per_min": 0.0, "engagement_rate": 0.0, "interactions": 0
    }
    surface = reply_surface_opportunity(item) if direct_x_source else {
        "reply_surface_score": 0, "reply_competition_known": 0, "observed_replies": None,
        "observed_quotes": None, "views_per_reply": None,
    }
    reply_acquisition_score = max(0, int(dist["distribution_score"]) + int(surface["reply_surface_score"]) + feedback_score) if direct_x_source else 0

    generic_entities = {"china", "chinese"}
    specific_entities = [e for e in entities if e.casefold() not in generic_entities]
    entity_only_ok = bool(source.get("allow_entity_only")) and bool(specific_entities)

    if noise:
        priority = "DROP"
        reason = f"noise:{noise[0]}"
    elif bool(source.get("require_title_entity")) and not title_entities:
        priority = "DROP"
        reason = "no_title_china_entity_match"
    elif bool(source.get("require_title_topic")) and not title_topics:
        priority = "DROP"
        reason = "no_title_tech_topic_match"
    elif not topics and not entity_only_ok:
        priority = "DROP"
        reason = "no_tech_topic_match"
    elif not bool(source.get("china_focused")) and not bool(source.get("audience_focused")) and not entities:
        priority = "DROP"
        reason = "no_china_entity_match"
    elif bool(source.get("require_productivity_term")) and not productivity:
        priority = "DROP"
        reason = "no_ai_productivity_match"
    elif published is not None and age > float(source.get("max_candidate_age_minutes", rules.get("max_candidate_age_minutes", 1440))):
        priority = "DROP"
        reason = f"stale:{age:.0f}m"
    else:
        weight = int(source.get("source_weight", 1))
        score = weight + min(len(entities), 2) * 2 + min(len(topics), 3) + min(len(productivity), 2) * 2 + min(len(high), 2) * 2
        p0_min_score = int(source.get("p0_min_score", 7))
        p1_min_score = int(source.get("p1_min_score", 5))
        x_distribution_min = int(source.get("x_distribution_min_score", rules.get("x_distribution_min_score", 6)))
        x_reply_acquisition_min = int(source.get("x_reply_acquisition_min_score", rules.get("x_reply_acquisition_min_score", 10)))
        x_early_grace_minutes = float(source.get("x_early_grace_minutes", rules.get("x_early_grace_minutes", 5)))
        x_early_grace_base_score = int(source.get("x_early_grace_base_score", rules.get("x_early_grace_base_score", 7)))
        distribution_ok = (
            not direct_x_source
            or int(dist["distribution_score"]) >= x_distribution_min
            or reply_acquisition_score >= x_reply_acquisition_min
            or (age <= x_early_grace_minutes and score >= x_early_grace_base_score)
        )
        x_breakout_p0 = direct_x_source and int(dist["distribution_score"]) >= int(rules.get("x_breakout_p0_distribution_score", 10))
        if age <= float(source.get("p0_max_age_minutes", rules.get("p0_max_age_minutes", 30))) and score >= p0_min_score and (bool(high) or x_breakout_p0):
            priority = "P0"
        elif age <= float(source.get("p1_max_age_minutes", rules.get("p1_max_age_minutes", 360))) and score >= p1_min_score and distribution_ok:
            priority = "P1"
        else:
            priority = "P2"
        bits = [f"score={score}", f"age={age:.0f}m"]
        if direct_x_source:
            bits.extend([
                f"dist={int(dist['distribution_score'])}",
                f"views={int(dist['views'])}",
                f"vel={float(dist['view_velocity_per_min']):.1f}/m",
                f"surface={int(surface['reply_surface_score'])}",
                f"replies={surface['observed_replies'] if surface['observed_replies'] is not None else 'unknown'}",
                f"vpr={surface['views_per_reply'] if surface['views_per_reply'] is not None else 'unknown'}",
                f"acq={reply_acquisition_score}",
                f"feedback={feedback_score}/{feedback_samples}",
                f"growthdays={feedback_growth_days}",
            ])
        if entities:
            bits.append("entity=" + entities[0])
        if topics:
            bits.append("topic=" + topics[0])
        if productivity:
            bits.append("productivity=" + productivity[0])
        if high:
            bits.append("impact=" + high[0])
        reason = "; ".join(bits)

    # For target search, title entities outrank entities mentioned only in article body/context.
    entity = next((e for e in title_entities if e.casefold() not in generic_entities), None)
    if entity is None and title_entities:
        entity = title_entities[0]
    # If the title has no known entity, use the title itself instead of an unrelated company mentioned in the excerpt.
    generic_topics = {"ai", "model"}
    topic_pool = title_topics or topics
    topic = next((t for t in topic_pool if t.casefold() not in generic_topics), topic_pool[0] if topic_pool else None)
    if topic is None and entity_only_ok:
        topic = str(source.get("default_topic") or "china_tech")
    direct_x_target = direct_x_source and bool(item.get("canonical_url"))
    return {
        "priority": priority,
        "score": locals().get("score", 0),
        "reason": reason,
        "topic": topic,
        "x_search_url": item.get("canonical_url") if direct_x_target else make_x_search_url(item.get("title", ""), entity, topic),
        "target_mode": "VERIFIED_X_TARGET" if direct_x_target else "TARGET_SEARCH_REQUIRED",
        "suggested_angle": angle_for(topic, item.get("title", "")),
        "age_minutes": age,
        "distribution_score": int(dist["distribution_score"]),
        "observed_views": int(dist["views"]),
        "view_velocity_per_min": float(dist["view_velocity_per_min"]),
        "engagement_rate": float(dist["engagement_rate"]),
        "reply_surface_score": int(surface["reply_surface_score"]),
        "reply_competition_known": int(surface["reply_competition_known"]),
        "observed_replies": surface["observed_replies"],
        "observed_quotes": surface["observed_quotes"],
        "views_per_reply": surface["views_per_reply"],
        "reply_acquisition_score": reply_acquisition_score,
        "feedback_score": feedback_score,
        "feedback_samples": feedback_samples,
        "feedback_median_impressions": feedback_median,
        "feedback_growth_days": feedback_growth_days,
        "feedback_follower_gain": feedback_follower_gain,
    }
