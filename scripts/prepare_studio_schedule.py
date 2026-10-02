#!/usr/bin/env python3
"""Build fresh immutable Studio inputs from the canonical X database, read-only."""
from datetime import datetime, timedelta, timezone
import argparse
import json
from pathlib import Path
import re
import sqlite3
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from china_tech_x_radar.studio_flow import digest, request, review_inputs, write_json

def bundle(con, as_of, run_id):
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', run_id):
        raise ValueError('unsafe run id')
    end = as_of.astimezone(timezone.utc)
    fmt = lambda t: t.isoformat().replace('+00:00', 'Z')
    inputs = review_inputs(con, fmt(end - timedelta(days=7)), fmt(end), fmt(end))
    inputs['method_revision'] = 'observational-description-v2'
    review = request('review', inputs)
    m = inputs['metrics']
    def num(key):
        return '未知' if m[key] is None else str(m[key])
    profile_fact = ('所有动作均缺少主页访问记录，主页访问数未知，不能表述成零。'
                    if m['actions_with_profile_visits'] == 0 else
                    '仅' + num('actions_with_profile_visits') + '个动作有主页访问记录；这是记录覆盖量，并非访问次数。')
    facts = [
        {'id': 'F1', 'text': '近7天原创成熟样本' + num('POST.mature_samples') +
         '条；累计曝光中位数' + num('POST.median_impressions') + '；曝光指标样本' + num('POST.impressions_samples') + '条。',
         'source_label': 'X生产数据库最新快照'},
        {'id': 'F2', 'text': 'Reply成熟样本' + num('REPLY.mature_samples') +
         '条；累计曝光中位数' + num('REPLY.median_impressions') + '；曝光指标样本' + num('REPLY.impressions_samples') +
         '条。小样本且帖龄不同，只作描述，不能证明因果或运营效果。', 'source_label': 'X生产数据库最新快照'},
        {'id': 'F3', 'text': profile_fact +
         '没有记录的值仍为未知；逐帖涨粉归因未知；尚未验证增长效果。', 'source_label': 'X生产数据库最新快照'}]
    card = request('card', {'facts': facts, 'method_revision': 'profile-record-coverage-v2',
        'subtitle': '近7天真实运营快照 · ' + end.astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d'),
        'scope_note': '成熟≥24小时；每条动作仅一个最新快照。小样本、帖龄不同，非因果。主页访问缺失仍未知；逐帖涨粉未知。待人工审阅，未发布。'})
    value = {'schema': 'x-studio-scheduled-bundle-v1', 'run_id': run_id, 'as_of': fmt(end),
             'requests': {'review': review, 'card': card}}
    value['bundle_sha256'] = digest(value)
    return value

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id'); a = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    db = root / 'runtime/china-tech-x.db'
    now = datetime.now(timezone.utc)
    run_id = a.run_id or now.astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d')
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', run_id):
        raise ValueError('unsafe run id')
    destination = root / 'runtime/studio-schedules' / run_id / 'bundle.json'
    if destination.exists():
        print(destination.read_text()); return
    con = sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True); con.row_factory = sqlite3.Row
    try:
        con.execute('BEGIN')
        value = bundle(con, now, run_id)
    finally:
        con.close()
    write_json(destination, value)
    print(json.dumps(value, ensure_ascii=False))

if __name__ == '__main__':
    main()
