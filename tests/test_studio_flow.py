import sqlite3
import unittest
from copy import deepcopy

from china_tech_x_radar.studio_flow import accept, digest, request, review_inputs, validate_request


class StudioFlowTests(unittest.TestCase):
    def database(self):
        con = sqlite3.connect(":memory:"); con.row_factory = sqlite3.Row
        con.executescript("CREATE TABLE published_action(id,action_type,posted_at);"
                          "CREATE TABLE outcome_snapshot(id,action_id,captured_at,impressions,engagements,profile_visits);"
                          "INSERT INTO published_action VALUES(1,'REPLY','2026-10-01T00:00:00Z');"
                          "INSERT INTO published_action VALUES(2,'POST','2026-10-02T00:00:00Z');"
                          "INSERT INTO published_action VALUES(3,'ORIGINAL','2026-10-01T00:00:00Z');"
                          "INSERT INTO outcome_snapshot VALUES(1,1,'2026-10-01T01:00:00Z',10,1,NULL);"
                          "INSERT INTO outcome_snapshot VALUES(2,1,'2026-10-02T01:00:00Z',100,NULL,NULL);"
                          "INSERT INTO outcome_snapshot VALUES(3,1,'2026-10-03T01:00:00Z',1000,50,10);"
                          "INSERT INTO outcome_snapshot VALUES(4,2,'2026-10-02T01:00:00Z',20,0,NULL);"
                          "INSERT INTO outcome_snapshot VALUES(5,3,'2026-10-02T01:00:00Z',70,7,NULL);")
        return con

    def test_latest_per_action_cutoff_maturity_and_unknown(self):
        value = review_inputs(self.database(), "2026-10-01T00:00:00Z", "2026-10-02T02:00:00Z", "2026-10-02T02:00:00Z")
        self.assertEqual(value["metrics"]["unique_actions"], 3)
        self.assertEqual(value["metrics"]["mature_actions"], 2)
        self.assertEqual(value["actions"][0]["snapshot_id"], 2)
        self.assertIsNone(value["actions"][0]["engagement_rate"])
        self.assertEqual(value["actions"][1]["engagement_rate"], 0)
        self.assertEqual(value["metrics"]["POST.median_impressions"], 70)
        self.assertEqual(value["actions"][2]["action_type"], "ORIGINAL")
        self.assertEqual(value["actions"][2]["cohort"], "POST")
        self.assertIsNone(value["metrics"]["post_follower_attribution"])

    def test_policy_and_input_mutation_fail(self):
        value = request("review", {"metrics": {"samples": 1}})
        value["policy"]["audit_model"] = "gpt-5.6-luna"
        with self.assertRaises(ValueError): validate_request(value)
        value = request("review", {"metrics": {"samples": 1}})
        value["inputs"]["metrics"]["samples"] = 99
        with self.assertRaises(ValueError): validate_request(value)

    def test_rejection_wrong_hash_and_failed_layout_block_acceptance(self):
        req = request("card", {"facts": [{"id": "F1"}]})
        draft = {"title": "本地实测", "points": [{"text": "事实一", "fact_ids": ["F1"]}, {"text": "事实二", "fact_ids": ["F1"]}]}
        audit = {"model": "gpt-6.1-sol", "effort": "high", "request_sha256": req["request_sha256"],
                 "draft_sha256": digest(draft), "verdict": {"decision": "APPROVE", "issues": []}}
        self.assertFalse(accept(req, draft, audit, {"schema": True})["published"])
        for key, value in [("effort", "low"), ("draft_sha256", "bad"), ("verdict", {"decision": "REJECT", "issues": ["unsupported fact"]})]:
            changed = deepcopy(audit); changed[key] = value
            with self.assertRaises(ValueError): accept(req, draft, changed, {"schema": True})
        with self.assertRaises(ValueError): accept(req, draft, audit, {"layout": False})


if __name__ == "__main__": unittest.main()
