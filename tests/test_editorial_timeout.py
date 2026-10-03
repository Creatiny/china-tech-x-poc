from __future__ import annotations
import json
import tempfile
import unittest
import sys
from pathlib import Path
from china_tech_x_radar.db import connect
from china_tech_x_radar.editorial import _run_codex

class CodexTimeoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.con=connect(self.root/'test.db')
        self.codex=self.root/'fake-codex'
        self.codex.write_text("#!"+sys.executable+"\n"+'''import json,sys,time
from pathlib import Path
print("model: gpt-6.1-sol",file=sys.stderr,flush=True)
print("reasoning effort: high",file=sys.stderr,flush=True)
print("verification started",file=sys.stderr,flush=True)
print("partial stdout",flush=True)
time.sleep(1.15)
path=Path(sys.argv[sys.argv.index("-o")+1])
path.write_text(json.dumps({"decision":"SKIP"}))
print("tokens used",file=sys.stderr)
print("123",file=sys.stderr)
''')
        self.codex.chmod(0o700)
        self.cfg=dict(codex_path=str(self.codex),model='gpt-6.1-sol',reasoning_effort='high',
                      operator_aware_policy=False,call_timeout_seconds=1,final_call_timeout_seconds=3)
    def tearDown(self):
        self.con.close();self.tmp.cleanup()
    def receipt(self):
        files=list((self.root/'runtime/editorial-calls').rglob('receipt.json'))
        self.assertEqual(len(files),1)
        return files[0],json.loads(files[0].read_text())
    def test_final_can_complete_past_legacy_timeout_and_keeps_verified_trace(self):
        result=_run_codex(self.con,self.root,self.cfg,'FINAL','diagnostic test',search=False)
        self.assertEqual(result,{'decision':'SKIP'})
        path,receipt=self.receipt()
        self.assertEqual(receipt['timeout_seconds'],3)
        self.assertGreater(receipt['duration_seconds'],1)
        self.assertEqual(receipt['state'],'COMPLETED')
        self.assertTrue(receipt['invocation_identity_verified'])
        self.assertIn('verification started',(path.parent/'stderr.log').read_text())
        self.assertEqual(self.con.execute('SELECT success,tokens_used FROM model_usage').fetchone()['success'],1)
    def test_gate_timeout_retains_partial_output_and_failed_usage(self):
        with self.assertRaisesRegex(TimeoutError,'codex_timeout:1s:purpose=GATE:logs='):
            _run_codex(self.con,self.root,self.cfg,'GATE','diagnostic test',search=False)
        path,receipt=self.receipt()
        self.assertEqual(receipt['timeout_seconds'],1)
        self.assertEqual(receipt['state'],'TIMED_OUT')
        self.assertTrue(receipt['invocation_identity_verified'])
        self.assertIn('partial stdout',(path.parent/'stdout.log').read_text())
        self.assertIn('verification started',(path.parent/'stderr.log').read_text())
        self.assertEqual(self.con.execute('SELECT success FROM model_usage').fetchone()[0],0)

if __name__=='__main__':unittest.main()
