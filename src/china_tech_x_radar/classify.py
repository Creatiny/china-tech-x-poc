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
        return "Angle: explain the China supply-chain implication, what bottleneck this removes, and what still depends on foreign tooling/compute."
    if any(x in t for x in ("robot", "humanoid")):
        return "Angle: separate demo hype from deployment economics—cost, reliability, production scale, and actual factory use."
    if any(x in t for x in ("ev", "battery", "autonomous")):
        return "Angle: connect the product news to manufacturing scale, cost curve, and global-market impact."
    if any(x in t for x in ("ai", "model", "llm", "agent", "benchmark", "open-source", "open source")):
        return "Angle: compare capability, openness, inference economics, and what this changes for global AI builders—not just benchmark rank."
    if any(x in t for x in ("ipo", "funding", "earnings")):
        return "Angle: focus on what the capital event says about demand, capacity expansion, and the competitive cycle."
    return "Angle: add a China-specific fact or second-order global implication instead of repeating the headline."


def classify(item: dict[str, Any], source: dict[str, Any], rules: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    title_text = item.get("title", "")
    text = f"{title_text} {item.get('excerpt','')}"
    entities = _match_terms(text, list(rules.get("china_entities", [])))
    title_entities = _match_terms(title_text, list(rules.get("china_entities", [])))
    topics = _match_terms(text, list(rules.get("topic_terms", [])))
    title_topics = _match_terms(title_text, list(rules.get("topic_terms", [])))
    high = _match_terms(text, list(rules.get("high_impact_terms", [])))
    noise = _match_terms(text, list(rules.get("noise_terms", [])))
    published = item.get("published_at")
    age = _age_minutes(published, now)

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
    elif not bool(source.get("china_focused")) and not entities:
        priority = "DROP"
        reason = "no_china_entity_match"
    elif published is not None and age > float(source.get("max_candidate_age_minutes", rules.get("max_candidate_age_minutes", 1440))):
        priority = "DROP"
        reason = f"stale:{age:.0f}m"
    else:
        weight = int(source.get("source_weight", 1))
        score = weight + min(len(entities), 2) * 2 + min(len(topics), 3) + min(len(high), 2) * 2
        if age <= float(source.get("p0_max_age_minutes", rules.get("p0_max_age_minutes", 30))) and high and score >= 7:
            priority = "P0"
        elif age <= float(source.get("p1_max_age_minutes", rules.get("p1_max_age_minutes", 360))) and score >= 5:
            priority = "P1"
        else:
            priority = "P2"
        bits = [f"score={score}", f"age={age:.0f}m"]
        if entities:
            bits.append("entity=" + entities[0])
        if topics:
            bits.append("topic=" + topics[0])
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
    direct_x_target = source.get("kind") == "x_profile" and bool(item.get("canonical_url"))
    return {
        "priority": priority,
        "score": locals().get("score", 0),
        "reason": reason,
        "topic": topic,
        "x_search_url": item.get("canonical_url") if direct_x_target else make_x_search_url(item.get("title", ""), entity, topic),
        "target_mode": "VERIFIED_X_TARGET" if direct_x_target else "TARGET_SEARCH_REQUIRED",
        "suggested_angle": angle_for(topic, item.get("title", "")),
        "age_minutes": age,
    }
