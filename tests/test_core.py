from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from china_tech_x_radar.classify import classify, distribution_opportunity
from china_tech_x_radar.db import connect, insert_signal, update_signal_observation, iso
from china_tech_x_radar.sources import parse_feed, parse_x_profile_html, parse_x_profile_stats_html
from china_tech_x_radar.kpi import diagnose, evaluate_gate
from china_tech_x_radar.formula import age_bucket, follower_tier, build_formula_report, build_creator_feedback_map, creator_acquisition_report
from china_tech_x_radar.alerts import format_publish_packet
from china_tech_x_radar.runner import notification_policy, _reply_copy_score, _outcome_due, _limit_due_x_profiles, _effective_poll_minutes, process_pending_alerts
from china_tech_x_radar.editorial import _reserve_model_call, language_gate_violations, model_usage_today, final_prompt, load_spec_guardrails, require_humanizer_skill, recent_reply_openers, _reply_opener_shape, load_kenny_voice_profile


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

    def test_parse_x_profile_stats_public_ssr(self):
        body = b'<a href="/KennyChinaTech/following"><div class="font-bold">118</div><div>Following</div></a><a href="/KennyChinaTech/verified_followers"><div class="font-bold">26</div><div>Followers</div></a>'
        stats = parse_x_profile_stats_html(body, "KennyChinaTech")
        self.assertEqual(stats["followers"], 26)
        self.assertEqual(stats["following"], 118)
        raw = b'followers:26,following:118,foo:1,screenName:"KennyChinaTech",tweets:174'
        exact = parse_x_profile_stats_html(raw, "KennyChinaTech")
        self.assertEqual(exact["tweets"], 174)

    def test_editorial_worker_recovers_stale_claim_without_source_polling(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            con = connect(Path(d) / "editorial.db")
            old = "2026-09-15T00:00:00Z"
            cur = con.execute(
                "INSERT INTO signal(fingerprint,source_id,source_name,source_kind,title,author,discovered_at,priority,score,reason,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                ("e"*64,"x_test","T","x_profile","Agent test","@a",old,"P1",8,"r",old),
            )
            sid=cur.lastrowid
            con.execute(
                "INSERT INTO alert(signal_id,priority,created_at,status,editorial_status,editorial_at) VALUES(?,?,?,?,?,?)",
                (sid,"P1",old,"EDITORIAL_PROCESSING","PROCESSING",old),
            )
            con.commit()
            root=Path(__file__).resolve().parents[1]
            with patch("china_tech_x_radar.runner.FeishuSender.available", return_value=False):
                result=process_pending_alerts(con,root,max_alerts=1)
            row=con.execute("select status,error from alert where signal_id=?",(sid,)).fetchone()
            self.assertEqual(result["recovered_stale_processing"],1)
            self.assertEqual(result["processed"],0)
            self.assertEqual(row["status"],"PENDING")
            self.assertEqual(row["error"],"channel_not_configured")

    def test_creator_feedback_adapts_poll_cadence_conservatively(self):
        source={"kind":"x_profile","handle":"candidate","poll_minutes":8}
        self.assertEqual(_effective_poll_minutes(source,{}),8)
        self.assertEqual(_effective_poll_minutes(source,{"candidate":{"score":1}}),3)
        self.assertEqual(_effective_poll_minutes(source,{"candidate":{"score":2}}),2)
        fast={"kind":"x_profile","handle":"candidate","poll_minutes":2}
        self.assertEqual(_effective_poll_minutes(fast,{"candidate":{"score":-1}}),8)
        rss={"kind":"rss","poll_minutes":5}
        self.assertEqual(_effective_poll_minutes(rss,{"candidate":{"score":2}}),5)

    def test_collector_bootstrap_has_project_proxy_fallback(self):
        root=Path(__file__).resolve().parents[1]
        for rel in ("scripts/run_collector.sh", "scripts/run_cycle.sh"):
            text=(root/rel).read_text(encoding="utf-8")
            self.assertIn('CHINA_TECH_HTTP_PROXY="${CHINA_TECH_HTTP_PROXY:-http://127.0.0.1:7890}"', text)

    def test_x_profile_due_work_is_bounded_and_oldest_first(self):
        due = [
            ({"id":"rss","kind":"rss"}, {"last_success_at":"2026-09-16T00:00:00Z"}, True),
            ({"id":"x_new","kind":"x_profile"}, {"last_success_at":"2026-09-16T00:03:00Z"}, True),
            ({"id":"x_old","kind":"x_profile"}, {"last_success_at":"2026-09-16T00:01:00Z"}, True),
            ({"id":"x_mid","kind":"x_profile"}, {"last_success_at":"2026-09-16T00:02:00Z"}, True),
        ]
        selected, deferred = _limit_due_x_profiles(due, 2)
        self.assertEqual(deferred, 1)
        self.assertEqual([x[0]["id"] for x in selected], ["rss", "x_old", "x_mid"])

    def test_outcome_capture_schedule_tapers_with_age(self):
        now = datetime.now(timezone.utc)
        self.assertTrue(_outcome_due(now - timedelta(minutes=30), None, now))
        self.assertFalse(_outcome_due(now - timedelta(minutes=30), now - timedelta(minutes=5), now))
        self.assertTrue(_outcome_due(now - timedelta(hours=10), now - timedelta(hours=2), now))
        self.assertFalse(_outcome_due(now - timedelta(days=20), None, now))

    def test_parse_x_profile_public_ssr(self):
        import base64
        tid = "2095207212830671005"
        enc = base64.b64encode(f"Tweet:{tid}".encode()).decode()
        body = (
            f'data-href="/jenzhuscott/status/{tid}" '
            f'client:{enc}:legacy={{retweeted_status_results:null}} '
            f'client:{enc}:counts={{bookmark_count:2,favorite_count:12,reply_count:3,retweet_count:4,quote_count:1}} '
            f'client:{enc}:views={{count:"2048"}} '
            f'client:{enc}:details={{full_text:"China robotics is moving fast.\\nFactory deployment matters.",created_at_ms:1788371301000}}'
        ).encode()
        items = parse_x_profile_html(body, "jenzhuscott")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["canonical_url"], f"https://x.com/jenzhuscott/status/{tid}")
        self.assertEqual(items[0]["metrics"]["views"], 2048)
        self.assertIn("Factory deployment", items[0]["excerpt"])

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

    def test_distribution_opportunity_rewards_fast_rising_x_post(self):
        fast = distribution_opportunity({"metrics": {"views": 1200, "likes": 30, "replies": 8, "reposts": 10, "quotes": 4}}, 2)
        slow = distribution_opportunity({"metrics": {"views": 30, "likes": 1}}, 30)
        self.assertGreaterEqual(fast["distribution_score"], 10)
        self.assertGreater(fast["view_velocity_per_min"], slow["view_velocity_per_min"])
        self.assertGreater(fast["distribution_score"], slow["distribution_score"])

    def test_named_ai_products_are_recognized_as_topics(self):
        now = datetime.now(timezone.utc)
        item = {
            "title": "OpenAI ships AgentKit and Codex integration for developers",
            "excerpt": "Codex automates developer workflows",
            "canonical_url": "https://x.com/example/status/20",
            "published_at": now - timedelta(minutes=8),
            "metrics": {"views": 5000},
        }
        source = {"kind":"x_profile","audience_focused":True,"source_weight":5,"p1_max_age_minutes":120}
        rules = {
            "china_entities": [],
            "topic_terms": ["ai","agent","openai","codex","agentkit"],
            "productivity_terms": ["developer","workflow","workflows","codex","agentkit"],
            "high_impact_terms": [], "noise_terms": [], "p0_max_age_minutes":30,
            "p1_max_age_minutes":360,"max_candidate_age_minutes":1440,
            "x_distribution_min_score":6,"x_early_grace_minutes":5,"x_early_grace_base_score":7,
            "x_breakout_p0_distribution_score":10,
        }
        out = classify(item, source, rules, now=now)
        self.assertIn(out["priority"], {"P0","P1"})
        self.assertIn("topic=openai", out["reason"])

    def test_curated_creator_can_add_source_specific_ai_vocabulary(self):
        now = datetime.now(timezone.utc)
        item = {
            "title": "/retro turns fuzzy rules into deterministic lint and pre-commit checks",
            "excerpt": "It proposes CI workflows after coding mistakes",
            "canonical_url": "https://x.com/example/status/21",
            "published_at": now - timedelta(minutes=5),
            "metrics": {"views": 30000},
        }
        source = {
            "kind":"x_profile","audience_focused":True,"source_weight":5,"p1_max_age_minutes":180,
            "extra_topic_terms":["/retro","lint","pre-commit","ci workflows"],
            "extra_productivity_terms":["lint","pre-commit","ci workflows"],
        }
        rules = {
            "china_entities": [], "topic_terms": ["ai","agent"], "productivity_terms": ["workflow"],
            "high_impact_terms": [], "noise_terms": [], "p0_max_age_minutes":30,
            "p1_max_age_minutes":360,"max_candidate_age_minutes":1440,
            "x_distribution_min_score":6,"x_early_grace_minutes":5,"x_early_grace_base_score":7,
            "x_breakout_p0_distribution_score":10,
        }
        out = classify(item, source, rules, now=now)
        self.assertIn(out["priority"], {"P0","P1"})
        self.assertGreaterEqual(out["score"], 7)

    def test_x_distribution_gate_downgrades_flat_post_after_early_grace(self):
        now = datetime.now(timezone.utc)
        item = {
            "title": "AI agent reliability benchmark", "excerpt": "agent eval reliability",
            "canonical_url": "https://x.com/example/status/2",
            "published_at": now - timedelta(minutes=40),
            "metrics": {"views": 20},
        }
        source = {"kind": "x_profile", "audience_focused": True, "source_weight": 5, "p1_max_age_minutes": 120}
        rules = {
            "china_entities": [], "topic_terms": ["ai", "agent", "benchmark"],
            "productivity_terms": ["agent", "reliability", "eval"],
            "high_impact_terms": [], "noise_terms": [], "p0_max_age_minutes": 30,
            "p1_max_age_minutes": 360, "max_candidate_age_minutes": 1440,
            "x_distribution_min_score": 6, "x_early_grace_minutes": 5, "x_early_grace_base_score": 7,
        }
        out = classify(item, source, rules, now=now)
        self.assertEqual(out["priority"], "P2")
        self.assertLess(out["distribution_score"], 6)

    def test_x_breakout_can_be_p0_without_keyword_impact_marker(self):
        now = datetime.now(timezone.utc)
        item = {
            "title": "AI agent reliability benchmark", "excerpt": "agent eval reliability",
            "canonical_url": "https://x.com/example/status/3",
            "published_at": now - timedelta(minutes=2),
            "metrics": {"views": 5000, "likes": 200, "replies": 30, "reposts": 80, "quotes": 20},
        }
        source = {"kind": "x_profile", "audience_focused": True, "source_weight": 5, "p1_max_age_minutes": 120}
        rules = {
            "china_entities": [], "topic_terms": ["ai", "agent", "benchmark"],
            "productivity_terms": ["agent", "reliability", "eval"],
            "high_impact_terms": [], "noise_terms": [], "p0_max_age_minutes": 30,
            "p1_max_age_minutes": 360, "max_candidate_age_minutes": 1440,
            "x_distribution_min_score": 6, "x_early_grace_minutes": 5, "x_early_grace_base_score": 7,
            "x_breakout_p0_distribution_score": 10,
        }
        out = classify(item, source, rules, now=now)
        self.assertEqual(out["priority"], "P0")
        self.assertGreaterEqual(out["distribution_score"], 10)

    def test_x_profile_signal_is_verified_reply_target(self):
        item = {"title": "China DeepSeek AI model update", "excerpt": "DeepSeek AI model", "canonical_url": "https://x.com/example/status/1", "published_at": datetime.now(timezone.utc)}
        source = {"kind": "x_profile", "china_focused": False, "source_weight": 5, "max_candidate_age_minutes": 120, "p1_max_age_minutes": 120}
        rules = {
            "china_entities": ["china", "deepseek"], "topic_terms": ["ai", "model"],
            "high_impact_terms": [], "noise_terms": [], "p0_max_age_minutes": 30,
            "p1_max_age_minutes": 360, "max_candidate_age_minutes": 1440,
        }
        out = classify(item, source, rules)
        self.assertEqual(out["target_mode"], "VERIFIED_X_TARGET")
        self.assertEqual(out["x_search_url"], item["canonical_url"])
        self.assertEqual(out["priority"], "P1")


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


    def test_pre_gate_diagnosis_does_not_require_reply_volume(self):
        metrics = {
            "cycle_count": 2, "cycle_success_rate": 1.0, "review_worth_rate": 0.8,
            "reply_actions_total": 0, "original_posts_total": 0, "published_actions_total": 0,
            "actions_with_outcome": 0, "max_impressions": None, "followers_total": 4,
        }
        gate = {
            "milestone_is_due": False, "evaluated_milestone_day": 3, "experiment_day": 1,
            "process_pass": False, "business_pass": False,
            "targets": {
                "cycle_success_rate_min": 0.95, "followers_total_min": 8,
                "review_worth_rate_min": 0.5,
            },
        }
        d = diagnose(metrics, gate)
        self.assertEqual(d["bottleneck"], "FOLLOWER_CONVERSION")

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


    def test_creator_feedback_requires_three_samples(self):
        with tempfile.TemporaryDirectory() as d:
            con = connect(Path(d) / "feedback.db")
            now = iso()
            for i, imp in enumerate((120, 180, 220), start=1):
                cur=con.execute("INSERT INTO signal(fingerprint,source_id,source_name,source_kind,title,author,discovered_at,priority,score,reason,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)", ((str(i)*64)[:64],'x_a','A','x_profile',f'T{i}','@creator',now,'P1',8,'r',now))
                sid=cur.lastrowid
                cur=con.execute("INSERT INTO published_action(signal_id,action_type,target_account,published_url,published_text,posted_at) VALUES(?,'REPLY','@creator',?,?,?)", (sid,f'https://x.com/me/{i}','text',now))
                aid=cur.lastrowid
                con.execute("INSERT INTO outcome_snapshot(action_id,captured_at,impressions) VALUES(?,?,?)", (aid,now,imp))
            con.commit()
            fb=build_creator_feedback_map(con,min_samples=3)['creator']
            self.assertEqual(fb['samples'],3)
            self.assertEqual(fb['median_impressions'],180.0)
            self.assertEqual(fb['score'],1)
            acq=creator_acquisition_report(con,min_feedback_samples=3)
            creator=next(x for x in acq if x['creator']=='creator')
            self.assertEqual(creator['reply_samples'],3)
            self.assertEqual(creator['median_reply_impressions'],180.0)

    def test_follower_gap_is_not_falsely_attributed(self):
        with tempfile.TemporaryDirectory() as d:
            con = connect(Path(d) / "followers.db")
            now = iso()
            con.execute("INSERT INTO experiment_state(id,started_at,baseline_followers,baseline_tracked_posts,baseline_total_views,created_at,updated_at) VALUES(1,?,?,?,?,?,?)", (now,4,0,0,now,now))
            con.execute("INSERT INTO account_snapshot(snapshot_date,followers,profile_visits,monetization_signals,notes,captured_at) VALUES('2026-09-01',4,NULL,0,NULL,?)", (now,))
            con.execute("INSERT INTO account_snapshot(snapshot_date,followers,profile_visits,monetization_signals,notes,captured_at) VALUES('2026-09-16',26,NULL,0,NULL,?)", (now,))
            con.commit()
            report=build_formula_report(con)
            latest=report['daily_follower_cohorts'][-1]
            self.assertEqual(latest['raw_follower_delta_since_previous_snapshot'],22)
            self.assertIsNone(latest['follower_delta'])
            self.assertFalse(latest['follower_attribution_eligible'])

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
            self.assertEqual(report['daily_follower_cohorts'][0]['raw_follower_delta_since_previous_snapshot'],2)
            self.assertIsNone(report['daily_follower_cohorts'][0]['follower_delta'])


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

    def test_reply_packet_has_no_legacy_ab_group(self):
        text = format_publish_packet(
            {"id": 10, "priority": "P1", "title": "World model update", "canonical_url": "https://x.com/a/status/1"},
            {"decision": "REPLY", "content_bucket": "WHAT_I_BELIEVE", "confidence": 0.93,
             "reason": "Clear independent position",
             "core_position": "World models need persistent state, not just better video prediction.",
             "target_url": "https://x.com/a/status/1", "target_account": "a",
             "final_copy": "Better video isn't enough. The test is whether the model can keep a stable world state while an agent acts inside it.",
             "source_url": "https://example.com/paper", "angle_type": "THESIS",
             "urgency_minutes": 45, "publish_note": "Reply now.", "image_mode": "NONE"},
            has_asset=False,
        )
        self.assertTrue(text.startswith("【P1｜REPLY｜45分钟内】"))
        self.assertNotIn("实验分组", text)
        self.assertIn("核心观点：", text)


    def test_generic_funding_or_release_are_not_tech_topics(self):
        source = {"china_focused": True, "source_weight": 4}
        rules = {
            "china_entities": ["china", "chinese"],
            "topic_terms": ["ai", "chip", "robot", "ipo", "raises", "launch"],
            "high_impact_terms": ["funding", "release"], "noise_terms": [],
            "p0_max_age_minutes": 30, "p1_max_age_minutes": 360, "max_candidate_age_minutes": 1440,
        }
        movie = {"title": "Can Chinese sleeper hit Dear You conquer the US box office next? release", "excerpt": "", "published_at": datetime.now(timezone.utc)}
        university = {"title": "US university settlement over China ties funding disclosure", "excerpt": "", "published_at": datetime.now(timezone.utc)}
        self.assertEqual(classify(movie, source, rules)["priority"], "DROP")
        self.assertEqual(classify(university, source, rules)["priority"], "DROP")

    def test_chinese_tech_entity_and_topic_can_qualify_non_china_focused_feed(self):
        source = {"china_focused": False, "source_weight": 4}
        rules = {
            "china_entities": ["华为", "宇树", "昇腾"],
            "topic_terms": ["ai", "大模型", "机器人", "芯片"],
            "high_impact_terms": ["采购", "量产"], "noise_terms": [],
            "p0_max_age_minutes": 30, "p1_max_age_minutes": 360, "max_candidate_age_minutes": 1440,
        }
        item = {"title": "范式智能采购华为昇腾 950，用于 AI 大模型落地", "excerpt": "", "published_at": datetime.now(timezone.utc)}
        out = classify(item, source, rules)
        self.assertIn(out["priority"], {"P0", "P1"})
        self.assertGreaterEqual(out["score"], 7)


    def test_p0_packet_header_is_visible(self):
        text = format_publish_packet(
            {"id": 77, "priority": "P0", "title": "Major China AI event", "canonical_url": "https://example.com"},
            {"decision": "POST", "confidence": 0.9, "reason": "High priority", "final_copy": "Copy", "urgency_minutes": 30,
             "source_url": "https://example.com", "angle_type": "CHINA_CONTEXT", "publish_note": "Publish now."},
            has_asset=False,
        )
        self.assertTrue(text.startswith("【🔥 P0｜POST｜立即】"))
        self.assertIn("级别：P0｜最高优先级", text)

    def test_p1_post_daily_slot_throttles_second_packet(self):
        with tempfile.TemporaryDirectory() as d:
            con = connect(Path(d) / "policy.db")
            now = iso()
            cur = con.execute("INSERT INTO signal(fingerprint,source_id,source_name,source_kind,title,discovered_at,priority,score,reason,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", ('1'*64,'s','S','rss','T1',now,'P1',12,'r',now))
            sid = cur.lastrowid
            con.execute("INSERT INTO alert(signal_id,priority,created_at,sent_at,status,editorial_status,editorial_packet_json) VALUES(?,?,?,?,?,?,?)", (sid,'P1',now,now,'SENT','READY','{"decision":"POST"}'))
            con.commit()
            cfg={"p1_min_confidence":0.88,"p1_post_min_score":10,"max_p1_post_packets_per_day":1,"max_p1_reply_packets_per_day":4}
            allowed, reason = notification_policy(con,{"priority":"P1","score":12},{"decision":"POST","confidence":0.95},cfg)
            self.assertFalse(allowed)
            self.assertEqual(reason,"p1_post_daily_slot_used")

    def test_reply_rolling_window_blocks_burst_but_not_old_replies(self):
        with tempfile.TemporaryDirectory() as d:
            con = connect(Path(d) / "rolling.db")
            now_dt = datetime.now(timezone.utc)
            now = iso(now_dt)
            old = iso(now_dt - timedelta(hours=6))
            for i, sent_at in enumerate((now, now, now), start=1):
                cur = con.execute("INSERT INTO signal(fingerprint,source_id,source_name,source_kind,title,discovered_at,priority,score,reason,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (f'{i:064x}','s','S','x_profile',f'T{i}',sent_at,'P1',9,'r',sent_at))
                con.execute("INSERT INTO alert(signal_id,priority,created_at,sent_at,status,editorial_status,editorial_packet_json) VALUES(?,?,?,?,?,?,?)", (cur.lastrowid,'P1',sent_at,sent_at,'SENT','READY','{\"decision\":\"REPLY\"}'))
            con.commit()
            cfg = {"p1_min_confidence":0.88,"p1_reply_min_score":6,"p1_reply_window_hours":4,"max_p1_reply_packets_per_window":3,"max_p1_reply_packets_per_day":12}
            allowed, reason = notification_policy(con,{"priority":"P1","score":9},{"decision":"REPLY","confidence":0.95,"target_url":"https://x.com/a/status/4"},cfg)
            self.assertFalse(allowed)
            self.assertEqual(reason,"p1_reply_window_cap_reached")

            con.execute("UPDATE alert SET sent_at=? WHERE status='SENT'", (old,))
            con.commit()
            allowed, reason = notification_policy(con,{"priority":"P1","score":9},{"decision":"REPLY","confidence":0.95,"target_url":"https://x.com/a/status/5"},cfg)
            self.assertTrue(allowed)
            self.assertEqual(reason,"p1_reply_curated")


    def test_notification_epoch_ignores_old_sent_packets(self):
        with tempfile.TemporaryDirectory() as d:
            con = connect(Path(d) / "epoch.db")
            old = "2026-09-09T01:00:00Z"
            cur = con.execute("INSERT INTO signal(fingerprint,source_id,source_name,source_kind,title,discovered_at,priority,score,reason,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", ('e'*64,'s','S','x_profile','old',old,'P1',9,'r',old))
            con.execute("INSERT INTO alert(signal_id,priority,created_at,sent_at,status,editorial_status,editorial_packet_json) VALUES(?,?,?,?,?,?,?)", (cur.lastrowid,'P1',old,old,'SENT','READY','{\"decision\":\"REPLY\"}'))
            con.commit()
            cfg={"notification_epoch":"2026-09-09T06:55:00Z","p1_min_confidence":0.88,"p1_reply_min_score":7,"max_reply_packets_per_day":4,"max_p1_reply_packets_per_day":4}
            allowed, reason = notification_policy(con,{"priority":"P1","score":9},{"decision":"REPLY","confidence":0.95,"target_url":"https://x.com/a/status/2"},cfg)
            self.assertTrue(allowed)
            self.assertEqual(reason,"p1_reply_curated")

    def test_p1_creator_cooldown_blocks_repeat(self):
        with tempfile.TemporaryDirectory() as d:
            con = connect(Path(d) / "creator-cooldown.db")
            now = iso()
            cur = con.execute("INSERT INTO signal(fingerprint,source_id,source_name,source_kind,title,author,discovered_at,priority,score,reason,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)", ('c'*64,'x_a','A','x_profile','T','@alice',now,'P1',9,'r',now))
            con.execute("INSERT INTO alert(signal_id,priority,created_at,sent_at,status,editorial_status,editorial_packet_json) VALUES(?,?,?,?,?,?,?)", (cur.lastrowid,'P1',now,now,'SENT','READY','{\"decision\":\"REPLY\",\"target_account\":\"@alice\"}'))
            con.commit()
            cfg={"p1_min_confidence":0.88,"p1_reply_min_score":6,"max_p1_replies_per_creator_7d":3,"max_p1_reply_packets_per_window":3,"max_p1_reply_packets_per_day":12}
            allowed,reason=notification_policy(con,{"priority":"P1","score":9,"author":"@alice"},{"decision":"REPLY","confidence":0.95,"target_url":"https://x.com/alice/status/2","target_account":"alice"},cfg)
            self.assertFalse(allowed)
            self.assertTrue(reason.startswith("creator_24h_cooldown:"))

    def test_p1_creator_cooldown_does_not_block_new_creator(self):
        with tempfile.TemporaryDirectory() as d:
            con = connect(Path(d) / "creator-new.db")
            now = iso()
            cur = con.execute("INSERT INTO signal(fingerprint,source_id,source_name,source_kind,title,author,discovered_at,priority,score,reason,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)", ('d'*64,'x_a','A','x_profile','T','@alice',now,'P1',9,'r',now))
            con.execute("INSERT INTO alert(signal_id,priority,created_at,sent_at,status,editorial_status,editorial_packet_json) VALUES(?,?,?,?,?,?,?)", (cur.lastrowid,'P1',now,now,'SENT','READY','{\"decision\":\"REPLY\",\"target_account\":\"@alice\"}'))
            con.commit()
            cfg={"p1_min_confidence":0.88,"p1_reply_min_score":6,"max_p1_replies_per_creator_7d":3,"max_p1_reply_packets_per_window":3,"max_p1_reply_packets_per_day":12}
            allowed,reason=notification_policy(con,{"priority":"P1","score":9,"author":"@bob"},{"decision":"REPLY","confidence":0.95,"target_url":"https://x.com/bob/status/2","target_account":"@bob"},cfg)
            self.assertTrue(allowed)
            self.assertEqual(reason,"p1_reply_curated")

    def test_p0_bypasses_daily_reply_cap(self):
        with tempfile.TemporaryDirectory() as d:
            con = connect(Path(d) / "p0.db")
            now = iso()
            for i in range(4):
                cur=con.execute("INSERT INTO signal(fingerprint,source_id,source_name,source_kind,title,discovered_at,priority,score,reason,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", ((str(i+1)*64)[:64],'s','S','x_profile',f'T{i}',now,'P1',9,'r',now))
                con.execute("INSERT INTO alert(signal_id,priority,created_at,sent_at,status,editorial_status,editorial_packet_json) VALUES(?,?,?,?,?,?,?)", (cur.lastrowid,'P1',now,now,'SENT','READY','{\"decision\":\"REPLY\"}'))
            con.commit()
            cfg={"p0_min_confidence":0.75,"max_reply_packets_per_day":4,"max_p1_reply_packets_per_day":4}
            allowed,reason=notification_policy(con,{"priority":"P0","score":12},{"decision":"REPLY","confidence":0.95,"target_url":"https://x.com/a/status/9"},cfg)
            self.assertTrue(allowed)
            self.assertEqual(reason,"p0_immediate")

    def test_reply_copy_score_handles_x_reply_mentions(self):
        expected = "这个方向的价值不只是把包做小，而是把每种语言维护一套 grammar 改成一个模型按上下文猜 token 类型。"
        actual = "@shao__meng @shuding 这个方向的价值不只是把包做小，而是把每种语言维护一套 grammar 改成一个模型按上下文猜 token 类型。"
        self.assertGreaterEqual(_reply_copy_score(expected, actual), 0.95)

    def test_reply_copy_score_rejects_unrelated_reply(self):
        self.assertLess(_reply_copy_score("AI capacity planning needs the whole system", "Great post, thanks for sharing"), 0.3)

    def test_atomic_budget_reservation_blocks_second_call(self):
        with tempfile.TemporaryDirectory() as d:
            con = connect(Path(d) / "budget.db")
            cfg={"budget_revision":"test-v2","max_gate_calls_per_day":1,"max_final_calls_per_day":1,"max_tokens_per_day":10000,"gate_token_reserve":1000,"final_token_reserve":5000}
            rid=_reserve_model_call(con,cfg,"GATE","test-model")
            self.assertGreater(rid,0)
            self.assertEqual(model_usage_today(con,"test-v2")["gate_calls"],1)
            with self.assertRaises(RuntimeError):
                _reserve_model_call(con,cfg,"GATE","test-model")

    def test_existing_x_signal_observation_can_refresh_without_losing_first_discovery(self):
        with tempfile.TemporaryDirectory() as d:
            con = connect(Path(d) / "refresh.db")
            first = "2026-09-16T00:00:00Z"
            rec = {
                "fingerprint":"a"*64,"source_id":"x_test","source_name":"T","source_kind":"x_profile",
                "source_item_id":"1","canonical_url":"https://x.com/a/status/1","title":"Agent test",
                "excerpt":"Agent test","author":"@a","published_at":first,"discovered_at":first,
                "priority":"P2","score":6,"distribution_score":2,"observed_views":20,
                "view_velocity_per_min":1.0,"engagement_rate":0.0,"reason":"quiet","topic":"agent",
                "x_search_url":"https://x.com/a/status/1","target_mode":"VERIFIED_X_TARGET",
                "suggested_angle":"a","raw_json":"{}","created_at":first,
            }
            sid, created = insert_signal(con, rec)
            self.assertTrue(created)
            rec2 = dict(rec)
            rec2.update({"priority":"P0","distribution_score":11,"observed_views":9000,
                         "view_velocity_per_min":500.0,"reason":"breakout","discovered_at":"2026-09-16T00:10:00Z"})
            previous = update_signal_observation(con, sid, rec2)
            row = con.execute("select priority,distribution_score,observed_views,discovered_at,created_at from signal where id=?", (sid,)).fetchone()
            self.assertEqual(previous,"P2")
            self.assertEqual(row["priority"],"P0")
            self.assertEqual(row["distribution_score"],11)
            self.assertEqual(row["observed_views"],9000)
            self.assertEqual(row["discovered_at"],first)
            self.assertEqual(row["created_at"],first)

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

    def test_language_gate_rejects_ai_template_reply(self):
        packet = {
            "decision": "REPLY",
            "content_bucket": "WHAT_CHANGES",
            "final_copy": "The bigger signal is that China's supply chain is changing. This suggests that the market will follow.",
        }
        violations = language_gate_violations(packet)
        self.assertTrue(any(v.startswith("banned_phrase:the bigger signal") for v in violations))
        self.assertTrue(any(v.startswith("banned_phrase:this suggests that") for v in violations))

    def test_chinese_reply_hard_length_gate(self):
        packet = {"decision":"REPLY","content_bucket":"WHAT_I_BELIEVE","final_copy":"这是一条很长的回复。" * 20}
        self.assertTrue(any(v.startswith("too_long_zh:") for v in language_gate_violations(packet)))

    def test_language_gate_accepts_short_conversational_reply(self):
        packet = {
            "decision": "REPLY",
            "content_bucket": "WHAT_CHANGES",
            "final_copy": "CXMT still hasn't shared yields or stack capacity. If qualification goes well, commercial shipments could start in 2027.",
        }
        self.assertEqual(language_gate_violations(packet), [])

    def test_reply_does_not_require_legacy_content_group(self):
        packet = {
            "decision": "REPLY",
            "content_bucket": "WHAT_I_BELIEVE",
            "core_position": "Verification matters.",
            "final_copy": "I've seen the same failure mode in production. Verification is the hard part after an agent says it's done.",
        }
        self.assertEqual(language_gate_violations(packet), [])


    def test_global_ai_productivity_source_can_qualify_without_china_entity(self):
        item = {"title": "New AI coding agent adds persistent memory and verification", "excerpt": "developer workflow automation", "published_at": datetime.now(timezone.utc)}
        source = {"china_focused": False, "audience_focused": True, "require_productivity_term": True, "source_weight": 5}
        rules = {
            "china_entities": ["china", "qwen"],
            "topic_terms": ["ai", "agent", "coding"],
            "productivity_terms": ["agent", "coding", "developer", "workflow", "verification"],
            "high_impact_terms": ["launch"], "noise_terms": [],
            "p0_max_age_minutes": 30, "p1_max_age_minutes": 360, "max_candidate_age_minutes": 1440,
        }
        out = classify(item, source, rules)
        self.assertIn(out["priority"], {"P0", "P1"})
        self.assertIn("productivity=", out["reason"])


    def test_audience_source_can_apply_stricter_p1_threshold(self):
        item = {"title": "AI agent update", "excerpt": "agent workflow", "published_at": datetime.now(timezone.utc)}
        source = {"china_focused": False, "audience_focused": True, "require_productivity_term": True, "source_weight": 2, "p1_min_score": 9}
        rules = {
            "china_entities": [], "topic_terms": ["ai", "agent"],
            "productivity_terms": ["agent", "workflow"], "high_impact_terms": [], "noise_terms": [],
            "p0_max_age_minutes": 30, "p1_max_age_minutes": 360, "max_candidate_age_minutes": 1440,
        }
        out = classify(item, source, rules)
        self.assertEqual(out["priority"], "P2")

    def test_kenny_voice_profile_is_loaded(self):
        root = Path(__file__).resolve().parents[1]
        voice = load_kenny_voice_profile(root, {"kenny_voice_path":"00_Governance/KENNY_VOICE_FINGERPRINT.md"})
        self.assertIn("像一个真正做过这件事的人", voice)
        prompt = final_prompt(
            {"priority":"P1","title":"x","excerpt":"x","source_name":"S","canonical_url":"u","reason":"r","topic":"agent","target_mode":"VERIFIED_X_TARGET"},
            "SPEC", str(Path.home()/".codex/skills/humanizer/SKILL.md"), voice, []
        )
        self.assertIn("MANDATORY KENNY VOICE FINGERPRINT", prompt)

    def test_canned_ai_reply_openers_are_rejected(self):
        for text in ("The key product detail is the shared session.", "The hard part is reliability.", "这其实把问题说清楚了。", "这章的价值在于拆开 Harness。"):
            packet={"decision":"REPLY","content_bucket":"WHAT_CHANGES","final_copy":text}
            self.assertTrue(any(v.startswith("canned_opener:") for v in language_gate_violations(packet)), text)

    def test_humanizer_skill_is_required_and_prompted(self):
        cfg = {"humanizer_skill_path": str(Path.home() / ".codex/skills/humanizer/SKILL.md")}
        path = require_humanizer_skill(cfg)
        self.assertTrue(path.endswith("humanizer/SKILL.md"))
        prompt = final_prompt(
            {"priority":"P1","title":"AI agent","excerpt":"x","source_name":"S","canonical_url":"u","reason":"r","topic":"agent","target_mode":"VERIFIED_X_TARGET"},
            "SPEC", path, "KENNY VOICE", ["The key product detail is", "This is the benchmark direction"]
        )
        self.assertIn("MANDATORY HUMANIZER PASS", prompt)
        self.assertIn(path, prompt)
        self.assertIn("RECENT REPLY OPENINGS TO AVOID REUSING", prompt)
        self.assertIn("The key product detail is", prompt)

    def test_reply_opener_shape_is_compact(self):
        self.assertEqual(_reply_opener_shape("The hard part is making this reliable in production."), "The hard part is making this reliable")
        self.assertEqual(_reply_opener_shape("@foo @bar 这其实把 Agent 的成本瓶颈说得很清楚：后面还有很多。"), "这其实把 Agent 的成本瓶颈说得很清楚")

    def test_spec_guardrails_are_loaded_fresh(self):
        spec = load_spec_guardrails(Path(__file__).resolve().parents[1])
        self.assertIn("Mandatory Human Voice Gate", spec)
        self.assertIn("Single Reply Standard", spec)
        self.assertIn("Pre-Draft SPEC Check and Brevity Gate", spec)
        prompt = final_prompt({"priority":"P1","title":"AI agent","excerpt":"x","source_name":"S","canonical_url":"u","reason":"r","topic":"agent","target_mode":"VERIFIED_X_TARGET"}, spec)
        self.assertIn("MANDATORY PRE-DRAFT SPEC CHECK", prompt)
        self.assertIn("fewest words", prompt)

    def test_editorial_prompt_enforces_new_language_and_viewpoint_rules(self):
        prompt = final_prompt({"priority":"P1","title":"AI coding agent launch","excerpt":"workflow","source_name":"S","canonical_url":"source","reason":"r","topic":"agent","target_mode":"TARGET_SEARCH_REQUIRED"})
        self.assertIn("Original posts are ALWAYS Chinese", prompt)
        self.assertIn("Replies MUST follow the verified parent-post language", prompt)
        self.assertIn("WHAT_I_BELIEVE", prompt)
        self.assertIn("News is raw material", prompt)

    def test_chinese_template_is_rejected_by_language_gate(self):
        packet = {
            "decision": "POST",
            "content_bucket": "WHAT_I_BELIEVE",
            "final_copy": "真正重要的不是模型参数，而是验证。",
        }
        self.assertTrue(any(v.startswith("banned_phrase:真正重要的不是") for v in language_gate_violations(packet)))


if __name__ == "__main__":
    unittest.main()
