from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from china_tech_x_radar.db import connect, insert_signal, iso
from china_tech_x_radar.runner import reconcile_sent_replies


class ReplySurfaceReconcileTests(unittest.TestCase):
    def test_auto_reply_reconcile_persists_parent_surface_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            con = connect(Path(d) / "reconcile.db")
            now = iso()
            rec = {
                "fingerprint": "r" * 64,
                "source_id": "x_test",
                "source_name": "T",
                "source_kind": "x_profile",
                "canonical_url": "https://x.com/target/status/1",
                "title": "AI agent test",
                "excerpt": "agent",
                "author": "@target",
                "published_at": now,
                "discovered_at": now,
                "priority": "P1",
                "score": 8,
                "distribution_score": 9,
                "observed_views": 30000,
                "view_velocity_per_min": 300.0,
                "engagement_rate": 0.03,
                "reply_surface_score": 5,
                "reply_competition_known": 1,
                "observed_replies": 10,
                "observed_quotes": 2,
                "views_per_reply": 2727.3,
                "reply_acquisition_score": 14,
                "feedback_score": 0,
                "feedback_samples": 0,
                "feedback_growth_days": 0,
                "feedback_follower_gain": 0,
                "reason": "r",
                "topic": "agent",
                "x_search_url": "https://x.com/target/status/1",
                "target_mode": "VERIFIED_X_TARGET",
                "suggested_angle": "a",
                "raw_json": "{}",
                "created_at": now,
            }
            sid, _ = insert_signal(con, rec)
            packet = {
                "decision": "REPLY",
                "target_url": "https://x.com/target/status/1",
                "target_account": "@target",
                "final_copy": "Good point — validation matters.",
                "angle_type": "DATA_POINT",
            }
            con.execute(
                "INSERT INTO alert(signal_id,priority,created_at,sent_at,status,editorial_packet_json) VALUES(?,?,?,?,?,?)",
                (sid, "P1", now, now, "SENT", json.dumps(packet)),
            )
            con.execute("UPDATE alert SET opportunity_snapshot_json=? WHERE signal_id=?",(json.dumps({**rec,"metrics_observed_at":now}),sid))
            con.commit()
            reply_item = {
                "canonical_url": "https://x.com/KennyChinaTech/status/9",
                "excerpt": "@target Good point — validation matters.",
                "published_at": datetime.now(timezone.utc),
                "metrics": {"views": 5},
            }
            with patch("china_tech_x_radar.runner.fetch_account_posts_from_url", return_value=[reply_item]):
                out = reconcile_sent_replies(con, max_items=1)
            self.assertEqual(out["matched"], 1)
            row = con.execute(
                "select target_post_impressions_at_reply,target_post_replies_at_reply,target_post_quotes_at_reply,target_views_per_reply_at_reply,target_reply_surface_score_at_reply from published_action"
            ).fetchone()
            self.assertEqual(row["target_post_impressions_at_reply"], 30000)
            self.assertEqual(row["target_post_replies_at_reply"], 10)
            self.assertEqual(row["target_post_quotes_at_reply"], 2)
            self.assertAlmostEqual(row["target_views_per_reply_at_reply"], 2727.3)
            self.assertEqual(row["target_reply_surface_score_at_reply"], 5)


if __name__ == "__main__":
    unittest.main()
