from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from china_tech_x_radar.classify import classify
from china_tech_x_radar.db import connect, insert_signal, iso
from china_tech_x_radar.sources import parse_feed
from china_tech_x_radar.kpi import diagnose, evaluate_gate
from china_tech_x_radar.formula import age_bucket, follower_tier, build_formula_report
from china_tech_x_radar.alerts import format_publish_packet


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


    def test_pre_gate_diagnosis_prioritizes_reply_growth(self):
        metrics = {
            "cycle_count": 2, "cycle_success_rate": 1.0, "review_worth_rate": 0.8,
            "reply_actions_total": 0, "original_posts_total": 0, "published_actions_total": 0,
            "actions_with_outcome": 0, "max_impressions": None, "followers_total": 4,
        }
        gate = {
            "milestone_is_due": False, "evaluated_milestone_day": 3, "experiment_day": 1,
            "process_pass": False, "business_pass": False,
            "targets": {
                "cycle_success_rate_min": 0.95, "reply_actions_total_min": 6,
                "original_posts_total_min": 2, "followers_total_min": 8, "max_impressions_min": 100,
                "review_worth_rate_min": 0.5,
            },
        }
        d = diagnose(metrics, gate)
        self.assertEqual(d["bottleneck"], "REPLY_ACQUISITION_PACE")

    def test_day15_growth_gate_requires_followers_and_distribution(self):
        metrics = {
            "cycle_success_rate": 1.0, "median_alert_latency_minutes": 5.0, "review_worth_rate": 0.8,
            "reply_actions_total": 40, "original_posts_total": 10, "median_operator_minutes_per_day": 20,
            "followers_total": 40, "max_impressions": 1200,
            "actions_over_100_impressions": 8, "actions_over_300_impressions": 3, "actions_over_1000_impressions": 1,
        }
        kpi = {"milestone": {"day15": {
            "cycle_success_rate_min": 0.98, "median_alert_latency_minutes_max": 10,
            "review_worth_rate_min": 0.70, "reply_actions_total_min": 40,
            "original_posts_total_min": 10, "followers_total_min": 40,
            "actions_over_300_impressions_min": 3, "max_impressions_min": 1000,
            "median_operator_minutes_per_day_max": 30, "business_signal_mode": "AUDIENCE_ENGINE",
        }, "day3": {}, "day7": {}, "day10": {}, "day30": {}}}
        gate = evaluate_gate(15, metrics, kpi)
        self.assertTrue(gate["business_pass"])
        self.assertEqual(gate["status"], "GREEN_GROWTH_CONTINUE")


    def test_growth_formula_buckets_and_repeated_combo(self):
        self.assertEqual(age_bucket(8), "0_10M")
        self.assertEqual(age_bucket(45), "30_60M")
        self.assertEqual(follower_tier(250000), "100K_1M")
        with tempfile.TemporaryDirectory() as d:
            con = connect(Path(d) / "formula.db")
            now = iso()
            con.execute("INSERT INTO experiment_state(id,started_at,baseline_followers,baseline_tracked_posts,baseline_total_views,created_at,updated_at) VALUES(1,?,?,?,?,?,?)", (now,4,0,0,now,now))
            con.execute("INSERT INTO account_snapshot(snapshot_date,followers,profile_visits,monetization_signals,notes,captured_at) VALUES('2026-08-31',6,2,0,NULL,?)", (now,))
            for i in (1,2):
                fp=(str(i)*64)[:64]
                cur=con.execute("INSERT INTO signal(fingerprint,source_id,source_name,source_kind,title,discovered_at,priority,score,reason,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (fp,'s','S','rss',f'T{i}',now,'P1',10,'r',now))
                sid=cur.lastrowid
                cur=con.execute("INSERT INTO published_action(signal_id,action_type,event_type,target_account,target_account_followers,target_post_age_minutes,angle_type,media_type,has_external_link,published_url,published_text,posted_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (sid,'REPLY','SEMICONDUCTOR','acct',200000,20,'CHINA_CONTEXT','NONE',0,f'https://x.com/me/{i}','text',now))
                aid=cur.lastrowid
                con.execute("INSERT INTO outcome_snapshot(action_id,captured_at,impressions,engagements) VALUES(?,?,?,?)", (aid,now,300*i,15*i))
            con.commit()
            report=build_formula_report(con,min_samples=2)
            self.assertEqual(len(report['repeated_combinations']),1)
            combo=report['repeated_combinations'][0]
            self.assertEqual(combo['target_tier'],'100K_1M')
            self.assertEqual(combo['target_age_bucket'],'10_30M')
            self.assertEqual(combo['samples'],2)
            self.assertEqual(report['daily_follower_cohorts'][0]['follower_delta'],2)


    def test_curated_source_can_promote_known_entity_without_generic_topic_word(self):
        item = {"title": "Chinese court freezes Nexperia assets in Wingtech case", "excerpt": "", "published_at": datetime.now(timezone.utc)}
        source = {"china_focused": False, "source_weight": 5, "allow_entity_only": True, "default_topic": "china_tech"}
        rules = {
            "china_entities": ["wingtech", "nexperia"], "topic_terms": ["ai", "semiconductor", "chip"],
            "high_impact_terms": [], "noise_terms": [], "p0_max_age_minutes": 30,
            "p1_max_age_minutes": 360, "max_candidate_age_minutes": 1440,
        }
        out = classify(item, source, rules)
        self.assertEqual(out["priority"], "P1")
        self.assertEqual(out["topic"], "china_tech")


    def test_curated_source_does_not_promote_generic_china_only(self):
        item = {"title": "China reins in rising yuan as weak domestic demand clouds outlook", "excerpt": "macro currency demand", "published_at": datetime.now(timezone.utc)}
        source = {"china_focused": False, "source_weight": 5, "allow_entity_only": True, "default_topic": "china_tech"}
        rules = {
            "china_entities": ["china", "chinese", "wingtech", "nexperia"], "topic_terms": ["ai", "semiconductor", "chip", "robot", "ev"],
            "high_impact_terms": ["million"], "noise_terms": [], "p0_max_age_minutes": 30,
            "p1_max_age_minutes": 360, "max_candidate_age_minutes": 1440,
        }
        out = classify(item, source, rules)
        self.assertEqual(out["priority"], "DROP")

    def test_feishu_publish_packet_is_copy_ready(self):
        text = format_publish_packet(
            {"id": 9, "canonical_url": "https://example.com/source"},
            {"decision": "POST", "confidence": 0.91, "reason": "Strong China AI result", "final_copy": "Human-ready final copy.",
             "source_url": "https://example.com/source", "angle_type": "CHINA_CONTEXT", "urgency_minutes": 90,
             "publish_note": "Publish now.", "image_mode": "NONE"},
            has_asset=False,
        )
        self.assertIn("结论：发 ORIGINAL POST", text)
        self.assertIn("【最终文案｜直接复制】", text)
        self.assertIn("Human-ready final copy.", text)
        self.assertIn("来源：https://example.com/source", text)

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
