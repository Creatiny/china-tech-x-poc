from __future__ import annotations
import json
import tempfile
import tomllib
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch,MagicMock
from china_tech_x_radar import operating_policy as policy
from china_tech_x_radar.daytime_editorial import process
from china_tech_x_radar.db import connect,insert_signal,ensure_alert,iso,update_signal_observation
from china_tech_x_radar.runner import capture_published_outcomes,reconcile_sent_originals,_sent_packet_counts_since,notification_policy
from china_tech_x_radar.formula import build_creator_feedback_map
from china_tech_x_radar.classify import _match_terms,classify

ROOT=Path(__file__).resolve().parents[1]
CFG=tomllib.loads((ROOT/'config/editorial.toml').read_text())
NOW=datetime(2026,9,20,10,0,tzinfo=timezone.utc)
class Clock(datetime):
    current=NOW
    @classmethod
    def now(cls,tz=None):
        return cls.current.astimezone(tz) if tz else cls.current.replace(tzinfo=None)

class GrowthPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.con=connect(Path(self.tmp.name)/'test.db')
        Clock.current=NOW
    def tearDown(self):
        self.con.close();self.tmp.cleanup()
    def signal(self,index=1,**changes):
        d=dict(fingerprint=f'{index:064x}',source_id='x_test',source_name='Test',source_kind='x_profile',author=f'@creator{index}',title='Codex编程工具的验证流程',excerpt='验证真实工作流',canonical_url=f'https://x.com/creator{index}/status/{index}',published_at=iso(NOW-timedelta(minutes=10)),discovered_at=iso(NOW),created_at=iso(NOW),priority='P1',score=10,reason='test',target_mode='VERIFIED_X_TARGET',observed_views=1200,distribution_score=8,reply_acquisition_score=9,metrics_observed_at=iso(NOW),raw_json='{}')
        d.update(changes);sid,_=insert_signal(self.con,d);d['id']=sid;return d
    def queue(self,**changes):
        d=self.signal(**changes);d['alert_id']=ensure_alert(self.con,d['id'],d['priority']);return d
    def packet(self,signal):
        return dict(decision='REPLY',content_bucket='WHAT_I_LEARNED',confidence=.95,final_copy='Codex的验收先独立跑一次，别拿同一份执行日志互相证明。',target_url=signal['canonical_url'],target_account=signal['author'],image_mode='NONE',added_evidence=dict(detail='项目的独立验收记录提供具体可复现的对照步骤。',source_url='https://example.test/evidence'))
    def test_beijing_sleep_boundaries(self):
        for time,allowed in [('2026-09-20T23:59:00+08:00',False),('2026-09-20T07:59:00+08:00',False),('2026-09-20T08:00:00+08:00',True),('2026-09-20T21:59:00+08:00',True),('2026-09-20T22:00:00+08:00',False)]:
            self.assertEqual(policy.operator_available(CFG,datetime.fromisoformat(time)),allowed)
    def test_p0_does_not_wake_operator_or_call_model(self):
        self.queue(priority='P0');Clock.current=datetime(2026,9,19,18,tzinfo=timezone.utc)
        with patch('china_tech_x_radar.daytime_editorial.datetime',Clock),patch('china_tech_x_radar.operating_policy.datetime',Clock),patch('china_tech_x_radar.runner.enrich_signal') as model,patch('china_tech_x_radar.runner.FeishuSender') as sender:
            result=process(self.con,ROOT,CFG,3)
        self.assertEqual(result['state'],'QUIET_HOURS');model.assert_not_called();sender.assert_not_called()
    def test_budgets_are_reserved_for_later_dayparts(self):
        for hour,limit in [(1,20),(6,40),(11,50)]:
            self.assertEqual(policy.paced_limits(CFG,NOW.replace(hour=hour))['max_final_calls_per_day'],limit)
    def test_actual_reservation_enforces_cumulative_budget_without_reset(self):
        from china_tech_x_radar.editorial import _reserve_model_call
        Clock.current=NOW.replace(hour=1)
        cfg={**CFG,'final_token_reserve':1}
        with patch('china_tech_x_radar.operating_policy.datetime',Clock),patch('china_tech_x_radar.editorial.datetime',Clock):
            for _ in range(20):_reserve_model_call(self.con,cfg,'FINAL','test-only')
            with self.assertRaisesRegex(RuntimeError,'editorial_budget_exhausted'):
                _reserve_model_call(self.con,cfg,'FINAL','test-only')
            Clock.current=NOW.replace(hour=6)
            _reserve_model_call(self.con,cfg,'FINAL','test-only')
        self.assertEqual(self.con.execute('SELECT count(*) FROM model_usage').fetchone()[0],21)
        self.assertEqual(cfg['max_final_calls_per_day'],50)

    def test_missing_or_low_reach_is_deferred_not_sent(self):
        s=self.signal(observed_views=2,priority='P0')
        allowed,reason,retry=policy.preflight(self.con,s,CFG,NOW)
        self.assertFalse(allowed);self.assertEqual(reason,'awaiting_reach_evidence');self.assertIsNotNone(retry)
    def test_english_source_is_chinese_original_not_reply(self):
        s=self.signal(title='New coding agent for software teams',excerpt='New agent benchmark')
        self.assertEqual(policy.lane_for(s,CFG),'POST')
        packet=self.packet(s)
        self.assertIn('wrong_operating_lane',policy.packet_violations(s,packet,CFG))
    def test_english_copy_blocked_even_for_p0(self):
        s=self.signal(priority='P0');packet=self.packet(s);packet['final_copy']='This needs testing on real workflows.'
        self.assertIn('chinese_copy_required',policy.packet_violations(s,packet,CFG))
    def test_subject_and_evidence_are_required(self):
        s=self.signal(title='New coding agent',excerpt='Agent coding tools');p=self.packet(s);p.update(decision='POST',subject_name='Qwen')
        self.assertIn('standalone_subject_required',policy.packet_violations(s,p,CFG));p.pop('added_evidence')
        self.assertIn('concrete_added_evidence_required',policy.packet_violations(s,p,CFG))
    def test_nan_confidence_is_rejected(self):
        s=self.signal();p=self.packet(s);p['confidence']=float('nan')
        self.assertIn('invalid_confidence',policy.packet_violations(s,p,CFG))
    def test_parent_target_cannot_silently_change(self):
        s=self.signal();p=self.packet(s);p['target_url']='https://x.com/other/status/123'
        self.assertIn('reply_target_changed',policy.packet_violations(s,p,CFG))
    def test_chinese_adjacent_latin_tokens_match_without_subword_matches(self):
        self.assertEqual(_match_terms('Codex发布AI工具，Jev做判断',['codex','ai','jev']),['codex','ai','jev'])
        self.assertEqual(_match_terms('betrayal reveals',['ai','ev']),[])
    def test_daypart_attention_prefilter_precedes_llm(self):
        s=self.queue();self.con.execute("UPDATE alert SET status='SENT',sent_at=?,editorial_packet_json=? WHERE id=?",(iso(NOW-timedelta(minutes=10)),json.dumps(self.packet(s)),s['alert_id']));self.con.commit()
        other=self.queue(index=2,author=s['author'])
        with patch('china_tech_x_radar.daytime_editorial.datetime',Clock),patch('china_tech_x_radar.operating_policy.datetime',Clock),patch('china_tech_x_radar.runner.enrich_signal') as model:
            result=process(self.con,ROOT,CFG,3)
        model.assert_not_called();self.assertEqual(result['deferred'],1)
    def test_budget_failure_is_deferred_and_circuit_blocks_retry_storm(self):
        self.queue()
        with patch('china_tech_x_radar.daytime_editorial.datetime',Clock),patch('china_tech_x_radar.operating_policy.datetime',Clock),patch('china_tech_x_radar.runner.FeishuSender') as sender,patch('china_tech_x_radar.runner.enrich_signal',side_effect=RuntimeError('editorial_budget_exhausted:FINAL')) as model:
            sender.return_value.available.return_value=True
            first=process(self.con,ROOT,CFG,3);second=process(self.con,ROOT,CFG,3)
        self.assertEqual(first['deferred'],1);self.assertEqual(second['state'],'PROVIDER_BACKOFF');self.assertEqual(model.call_count,1)
        self.assertEqual(self.con.execute('SELECT status FROM alert').fetchone()[0],'EDITORIAL_DEFERRED')
    def test_sleep_boundary_crossing_prevents_delivery(self):
        s=self.queue()
        def draft(*args):
            Clock.current=NOW.replace(hour=14) # 22:00 Beijing
            return self.packet(s)
        with patch('china_tech_x_radar.daytime_editorial.datetime',Clock),patch('china_tech_x_radar.operating_policy.datetime',Clock),patch('china_tech_x_radar.runner.FeishuSender') as sender,patch('china_tech_x_radar.runner.enrich_signal',side_effect=draft):
            sender.return_value.available.return_value=True
            result=process(self.con,ROOT,CFG,3)
            sender.return_value.send_text.assert_not_called()
        self.assertEqual(result['held'],1)
    def test_delivery_persists_receipt_and_frozen_snapshot(self):
        s=self.queue()
        with patch('china_tech_x_radar.daytime_editorial.datetime',Clock),patch('china_tech_x_radar.operating_policy.datetime',Clock),patch('china_tech_x_radar.runner.FeishuSender') as sender,patch('china_tech_x_radar.runner.enrich_signal',return_value=self.packet(s)):
            sender.return_value.available.return_value=True;sender.return_value.send_text.return_value='mock-receipt'
            result=process(self.con,ROOT,{**CFG,'render_editorial_cards':False},3)
        row=self.con.execute('SELECT status,receipt_id,opportunity_snapshot_json FROM alert').fetchone()
        self.assertEqual(result['sent'],1);self.assertEqual(row['status'],'SENT');self.assertEqual(row['receipt_id'],'mock-receipt');self.assertEqual(json.loads(row['opportunity_snapshot_json'])['metrics_observed_at'],iso(NOW))
    def test_ambiguous_feishu_send_is_not_automatically_retried(self):
        s=self.queue()
        with patch('china_tech_x_radar.daytime_editorial.datetime',Clock),patch('china_tech_x_radar.operating_policy.datetime',Clock),patch('china_tech_x_radar.runner.FeishuSender') as sender,patch('china_tech_x_radar.runner.enrich_signal',return_value=self.packet(s)):
            sender.return_value.available.return_value=True;sender.return_value.send_text.side_effect=TimeoutError('timed out')
            process(self.con,ROOT,{**CFG,'render_editorial_cards':False},3)
            process(self.con,ROOT,{**CFG,'render_editorial_cards':False},3)
            self.assertEqual(sender.return_value.send_text.call_count,1)
        self.assertEqual(self.con.execute('SELECT status FROM alert').fetchone()[0],'DELIVERY_UNKNOWN')

    def test_sent_budget_uses_frozen_priority_not_live_priority(self):
        s=self.queue(priority='P0');self.con.execute("UPDATE alert SET status='SENT',editorial_status='READY',sent_at=?,editorial_packet_json=? WHERE id=?",(iso(NOW),json.dumps({'decision':'REPLY'}),s['alert_id']));self.con.execute("UPDATE signal SET priority='DROP' WHERE id=?",(s['id'],));self.con.commit()
        self.assertEqual(_sent_packet_counts_since(self.con,iso(NOW-timedelta(hours=1)))['p0_reply'],1)
    def test_observation_timestamp_is_updated_without_changing_discovery(self):
        s=self.signal();s['metrics_observed_at']=iso(NOW+timedelta(minutes=2));update_signal_observation(self.con,s['id'],s)
        row=self.con.execute('SELECT metrics_observed_at,discovered_at FROM signal').fetchone()
        self.assertEqual(row['metrics_observed_at'],s['metrics_observed_at']);self.assertEqual(row['discovered_at'],iso(NOW))
    def actions(self,n=4):
        now=datetime.now(timezone.utc);rows=[]
        for i in range(n):
            s=self.signal(index=i+1);url=f'https://x.com/KennyChinaTech/status/{i+100}'
            aid=self.con.execute("INSERT INTO published_action(signal_id,published_url,published_text,posted_at,target_account) VALUES(?,?,?,?,?)",(s['id'],url,'test',iso(now-timedelta(days=3)),s['author'])).lastrowid
            self.con.execute('INSERT INTO outcome_snapshot(action_id,captured_at,impressions) VALUES(?,?,?)',(aid,iso(now-timedelta(days=2)),10));rows.append((aid,url))
        self.con.commit();return rows
    def test_unchanged_outcomes_do_not_starve_newer_actions(self):
        rows=self.actions()
        def fetch(url,handle):return [dict(canonical_url=url,metrics={'views':10})]
        with patch('china_tech_x_radar.runner.fetch_account_posts_from_url',side_effect=fetch) as f:
            one=capture_published_outcomes(self.con,max_items=2);two=capture_published_outcomes(self.con,max_items=2)
        self.assertEqual(one['captured'],2);self.assertEqual(two['captured'],2);self.assertEqual(len({c.args[0] for c in f.call_args_list}),4)
    def test_missing_outcomes_do_not_monopolize_capture_slots(self):
        self.actions()
        with patch('china_tech_x_radar.runner.fetch_account_posts_from_url',return_value=[]) as f:
            capture_published_outcomes(self.con,max_items=2);capture_published_outcomes(self.con,max_items=2)
        self.assertEqual(len({c.args[0] for c in f.call_args_list}),4)
    def test_minute_old_measurements_never_teach_creator_penalties(self):
        now=datetime.now(timezone.utc)
        for i in range(3):
            s=self.signal(index=i+1);posted=now-timedelta(days=2)
            aid=self.con.execute("INSERT INTO published_action(signal_id,published_text,posted_at,target_account) VALUES(?,?,?,'@same')",(s['id'],'copy',iso(posted))).lastrowid
            self.con.execute('INSERT INTO outcome_snapshot(action_id,captured_at,impressions) VALUES(?,?,1)',(aid,iso(posted+timedelta(minutes=1))))
        self.con.commit();self.assertNotIn('same',build_creator_feedback_map(self.con))
    def test_original_reconciliation_is_measured_not_assumed_and_idempotent(self):
        now=datetime.now(timezone.utc);s=self.queue();packet={'decision':'POST','final_copy':'Codex的工作流现在可以独立验收，下面是具体运行记录。','angle_type':'FIRSTHAND_PRACTICE'}
        self.con.execute("UPDATE alert SET status='SENT',sent_at=?,editorial_packet_json=? WHERE id=?",(iso(now-timedelta(hours=1)),json.dumps(packet,ensure_ascii=False),s['alert_id']));self.con.commit()
        item=dict(canonical_url='https://x.com/KennyChinaTech/status/99',excerpt=packet['final_copy'],published_at=now-timedelta(minutes=10))
        with patch('china_tech_x_radar.sources.fetch_x_profile',return_value=([item],{},False)):
            first=reconcile_sent_originals(self.con);second=reconcile_sent_originals(self.con)
        self.assertEqual(first['matched'],1);self.assertEqual(second['matched'],0);self.assertEqual(self.con.execute("SELECT count(*) FROM published_action WHERE action_type='ORIGINAL'").fetchone()[0],1)
    def test_production_does_not_admit_using_surface_alone(self):
        rules=tomllib.loads((ROOT/'config/rules.toml').read_text());self.assertFalse(rules['allow_surface_gate_rescue']);self.assertEqual(rules['surface_ranking_weight'],.25)
    def test_poll_budget_and_chinese_discovery_allocation(self):
        sources=tomllib.loads((ROOT/'config/sources.toml').read_text())['source'];xs=[x for x in sources if x.get('kind')=='x_profile' and x.get('enabled',True)]
        self.assertLess(sum(1/x['poll_minutes'] for x in xs),10)
        self.assertGreaterEqual(sum(x.get('acquisition_role')=='chinese_acquisition' for x in xs),12)

if __name__=='__main__':unittest.main()
