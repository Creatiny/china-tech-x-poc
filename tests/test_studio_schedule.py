import importlib.util
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import unittest

from china_tech_x_radar.studio_flow import digest

def load(name):
    p = Path(__file__).resolve().parents[1] / 'scripts' / (name + '.py')
    spec = importlib.util.spec_from_file_location(name, p)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

prepare = load('prepare_studio_schedule')
runner = load('run_studio_scheduled_bundle')

class ScheduledStudioTests(unittest.TestCase):
    def sample(self):
        con = sqlite3.connect(':memory:'); con.row_factory = sqlite3.Row
        con.executescript("CREATE TABLE published_action(id,action_type,posted_at);"
                          "CREATE TABLE outcome_snapshot(id,action_id,captured_at,impressions,engagements,profile_visits);"
                          "INSERT INTO published_action VALUES(1,'ORIGINAL','2026-10-01T00:00:00Z');"
                          "INSERT INTO outcome_snapshot VALUES(1,1,'2026-10-02T01:00:00Z',NULL,NULL,NULL);")
        try:
            return prepare.bundle(con, datetime(2026,10,2,2,tzinfo=timezone.utc), '2026-10-02')
        finally:
            con.close()

    def test_missing_metrics_are_unknown_in_card_and_review(self):
        value = self.sample(); self.assertTrue(runner.validate_bundle(value))
        self.assertIsNone(value['requests']['review']['inputs']['metrics']['POST.median_impressions'])
        facts = value['requests']['card']['inputs']['facts']
        self.assertIn('中位数未知', facts[0]['text'])
        self.assertIn('没有记录的值仍为未知', facts[2]['text'])

    def test_rehashed_old_model_and_unsafe_paths_still_rejected(self):
        value = self.sample()
        changed = deepcopy(value); changed['run_id'] = '../../another-project'
        changed['bundle_sha256'] = digest({k:v for k,v in changed.items() if k!='bundle_sha256'})
        with self.assertRaises(ValueError): runner.validate_bundle(changed)
        changed = deepcopy(value); req = changed['requests']['review']
        req['policy']['audit_model'] = 'gpt-5.6-luna'
        req['request_sha256'] = digest({k:v for k,v in req.items() if k!='request_sha256'})
        changed['bundle_sha256'] = digest({k:v for k,v in changed.items() if k!='bundle_sha256'})
        with self.assertRaises(ValueError): runner.validate_bundle(changed)

    def test_verbatim_json_roundtrip_preserves_float_hashes(self):
        value = self.sample(); req = value['requests']['review']
        req['inputs']['metrics']['POST.median_engagement_rate'] = 0.0
        req['request_sha256'] = digest({k:v for k,v in req.items() if k!='request_sha256'})
        value['bundle_sha256'] = digest({k:v for k,v in value.items() if k!='bundle_sha256'})
        self.assertTrue(runner.validate_bundle(json.loads(json.dumps(value))))
        changed = deepcopy(value)
        changed['requests']['review']['inputs']['metrics']['POST.median_engagement_rate'] = 0
        with self.assertRaises(ValueError): runner.validate_bundle(changed)

if __name__ == '__main__': unittest.main()
