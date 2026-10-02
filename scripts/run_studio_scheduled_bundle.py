#!/usr/bin/env python3
"""Execute a fresh X bundle once; models and existing acceptance gates are fixed."""
from datetime import datetime, timezone
import argparse
import fcntl
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from china_tech_x_radar.studio_flow import digest, dt, validate_request, write_json

def validate_bundle(value):
    if value.get('schema') != 'x-studio-scheduled-bundle-v1' or not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', value.get('run_id', '')):
        raise ValueError('bundle schema or run id invalid')
    if digest({k:v for k,v in value.items() if k != 'bundle_sha256'}) != value.get('bundle_sha256'):
        raise ValueError('bundle bytes changed')
    if set(value['requests']) != {'review', 'card'}:
        raise ValueError('bundle task set invalid')
    for kind, req in value['requests'].items():
        validate_request(req)
        if req['kind'] != kind:
            raise ValueError('bundle task kind drift')
    if value['requests']['review']['inputs'].get('method_revision') != 'observational-description-v2':
        raise ValueError('review method drift')
    return True

def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--bundle', required=True); p.add_argument('--status', action='store_true'); a=p.parse_args()
    value=json.loads(Path(a.bundle).read_text()); validate_bundle(value)
    root=Path(__file__).resolve().parents[1]; out=root/'scheduled/results'/value['run_id']; state_path=out/'receipt.json'
    if a.status:
        print(state_path.read_text() if state_path.exists() else json.dumps({'state':'NOT_STARTED'})); return
    age=(datetime.now(timezone.utc)-dt(value['as_of'])).total_seconds()
    if age < -300 or age > 5400:
        raise ValueError('bundle is stale; prepare fresh canonical inputs')
    out.parent.mkdir(parents=True,exist_ok=True)
    with (out.parent/'.schedule.lock').open('a') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({'state':'BUSY','run_id':value['run_id']})); return
        if state_path.exists():
            prior=json.loads(state_path.read_text())
            if prior['bundle_sha256'] != value['bundle_sha256']:
                raise ValueError('period already bound to different input; do not replay')
            if prior['state']=='RUNNING':
                prior['state']='BLOCKED_RECOVERY_REQUIRED';write_json(state_path,prior)
            print(json.dumps(prior,ensure_ascii=False));return
        out.mkdir()
        state={'state':'RUNNING','run_id':value['run_id'],'bundle_sha256':value['bundle_sha256'],
               'local_model':'qwen3.8-27b-4bit','audit_model':'gpt-6.1-sol','audit_effort':'high',
               'published':False,'business_state_authority':False,'results':{}}
        write_json(state_path,state)
        for kind, req in value['requests'].items():
            request_path=out/(kind+'-request.json');write_json(request_path,req)
            destination=out/kind
            try:
                proc=subprocess.run([sys.executable,str(root/'scripts/studio_local_worker.py'),
                    '--request',str(request_path),'--out',str(destination)],capture_output=True,text=True,timeout=650)
                (out/(kind+'-stdout.log')).write_text(proc.stdout);(out/(kind+'-stderr.log')).write_text(proc.stderr)
                accepted=destination/'accepted.json'
                if proc.returncode or not accepted.exists():
                    raise RuntimeError('candidate rejected or execution failed; inspect '+str(destination))
                receipt=json.loads(accepted.read_text())
                if receipt['audit_model']!='gpt-6.1-sol' or receipt['audit_effort']!='high' or receipt['published'] is not False:
                    raise ValueError('acceptance policy drift')
                state['results'][kind]={'state':receipt['status'],'path':str(destination),**receipt}
            except Exception as exc:
                state['results'][kind]={'state':'BLOCKED','path':str(destination),'reason':str(exc)}
            write_json(state_path,state)
        state['state']='APPROVED_FOR_HUMAN_REVIEW' if all(x['state']=='APPROVED_FOR_HUMAN_REVIEW' for x in state['results'].values()) else 'BLOCKED'
        state['finished_at']=datetime.now(timezone.utc).isoformat();write_json(state_path,state)
        print(json.dumps(state,ensure_ascii=False))

if __name__=='__main__':main()
