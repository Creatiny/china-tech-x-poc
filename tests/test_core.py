from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from china_tech_x_radar.classify import classify
from china_tech_x_radar.db import connect, insert_signal, iso
from china_tech_x_radar.sources import parse_feed


class CoreTests(unittest.TestCase):
    def test_parse_rss(self):
        body = b'''<?xml version="1.0"?><rss><channel><item><title>Qwen launches model</title><link>https://e/x</link><guid>1</guid><pubDate>Mon, 31 Aug 2026 08:03:28 GMT</pubDate><description>AI model</description></item></channel></rss>'''
        items = parse_feed(body)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Qwen launches model")
        self.assertIsNotNone(items[0]["published_at"])

    def test_parse_atom(self):
        body = b'''<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><entry><id>r1</id><title>DeepSeek V4</title><updated>2026-08-31T08:00:00Z</updated><link href="https://github.com/x/releases/tag/v4"/><summary>release</summary></entry></feed>'''
        items = parse_feed(body)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["source_item_id"], "r1")

    def test_classify_material_china_ai(self):
        item = {"title": "Zhipu AI launches GLM-5.3 model benchmark", "excerpt": "China AI model release", "published_at": datetime.now(timezone.utc)}
        source = {"china_focused": True, "source_weight": 5}
        rules = {
            "china_entities": ["zhipu", "china", "glm"],
            "topic_terms": ["ai", "model", "benchmark"],
            "high_impact_terms": ["launch", "benchmark"],
            "noise_terms": [],
            "p0_max_age_minutes": 30,
            "p1_max_age_minutes": 360,
            "max_candidate_age_minutes": 1440,
        }
        out = classify(item, source, rules)
        self.assertIn(out["priority"], ("P0", "P1"))
        self.assertIn("x.com/search", out["x_search_url"])


    def test_short_tokens_do_not_match_inside_words(self):
        item = {"title": "Dual defence betrayal: China reveals a spying case", "excerpt": "security investigation", "published_at": datetime.now(timezone.utc)}
        source = {"china_focused": True, "source_weight": 4}
        rules = {
            "china_entities": ["china", "nio"],
            "topic_terms": ["ai", "ev"],
            "high_impact_terms": [],
            "noise_terms": [],
            "p0_max_age_minutes": 30, "p1_max_age_minutes": 360, "max_candidate_age_minutes": 1440,
        }
        out = classify(item, source, rules)
        self.assertEqual(out["priority"], "DROP")

    def test_exact_dedupe(self):
        with tempfile.TemporaryDirectory() as d:
            con = connect(Path(d) / "x.db")
            rec = {
                "fingerprint": "a" * 64, "source_id": "s", "source_name": "S", "source_kind": "rss",
                "source_item_id": "1", "canonical_url": "https://e", "title": "T", "excerpt": "", "author": "",
                "published_at": None, "discovered_at": iso(), "priority": "P2", "score": 1, "reason": "r", "topic": "ai",
                "x_search_url": "https://x.com", "target_mode": "TARGET_SEARCH_REQUIRED", "suggested_angle": "a",
                "raw_json": "{}", "created_at": iso(),
            }
            _, c1 = insert_signal(con, rec)
            _, c2 = insert_signal(con, rec)
            self.assertTrue(c1)
            self.assertFalse(c2)
            self.assertEqual(con.execute("select count(*) from signal").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
