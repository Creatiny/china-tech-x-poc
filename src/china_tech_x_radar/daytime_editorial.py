"""Execution of the existing editorial queue under operator-aware rules."""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from .operating_policy import operator_available, preflight, lane_for, next_release, utc_iso, parse_time, packet_violations


def process(con: sqlite3.Connection, root: Path, cfg: dict[str,Any], limit: int) -> dict[str,Any]:
    # Lazy imports avoid a cycle: this module changes policy, not the runtime authority.
    from .runner import FeishuSender, enrich_signal, notification_policy, format_publish_packet, render_editorial_card
    result = dict(processed=0,sent=0,skipped=0,held=0,errors=0,deferred=0,recovered_stale_processing=0)
    now = datetime.now(timezone.utc)
    if not operator_available(cfg,now):
        return {**result,"state":"QUIET_HOURS","next_eligible_at":next_release(cfg,now)}
    breaker = con.execute("SELECT retry_at,reason FROM editorial_runtime_state WHERE name='provider_backoff'").fetchone()
    if breaker and parse_time(breaker['retry_at']) and parse_time(breaker['retry_at']) > now:
        return {**result,"state":"PROVIDER_BACKOFF","next_eligible_at":breaker['retry_at'],"reason":breaker['reason']}
    con.execute("UPDATE alert SET status='DELIVERY_UNKNOWN',editorial_status='HOLD',error='delivery_receipt_reconciliation_required' WHERE status='EDITORIAL_PROCESSING' AND delivery_started_at IS NOT NULL AND editorial_at<?",(utc_iso(now-timedelta(minutes=10)),))
    cur = con.execute("UPDATE alert SET status='EDITORIAL_DEFERRED',editorial_status=NULL,retry_at=?,error='recovered_stale_claim' WHERE status='EDITORIAL_PROCESSING' AND delivery_started_at IS NULL AND editorial_at<?",(utc_iso(now),utc_iso(now-timedelta(minutes=10))))
    result['recovered_stale_processing'] = cur.rowcount
    con.commit()
    rows = con.execute("""SELECT a.id AS alert_id,a.priority AS queued_priority,s.* FROM alert a JOIN signal s ON s.id=a.signal_id
      WHERE a.status IN ('PENDING','EDITORIAL_DEFERRED') AND (a.retry_at IS NULL OR a.retry_at<=?)
      ORDER BY CASE s.priority WHEN 'P0' THEN 0 ELSE 1 END,s.reply_acquisition_score DESC,s.distribution_score DESC,COALESCE(s.published_at,s.discovered_at) DESC LIMIT 120""",(utc_iso(now),)).fetchall()
    candidates=[]
    for row in rows:
        signal=dict(row); signal['operating_lane']=lane_for(signal,cfg)
        allowed,reason,retry=preflight(con,signal,cfg,now)
        if not allowed:
            status='EDITORIAL_DEFERRED' if retry else 'EXPIRED' if reason in {'opportunity_expired','not_qualified','publication_time_unknown','future_publication_time'} else 'EDITORIAL_HOLD'
            con.execute("UPDATE alert SET status=?,retry_at=?,error=? WHERE id=? AND status IN ('PENDING','EDITORIAL_DEFERRED')",(status,retry,reason,signal['alert_id']))
            result['deferred' if retry else 'held']+=1
        else:
            candidates.append(signal)
    con.commit()
    candidates.sort(key=lambda s:(s['operating_lane']!='REPLY',s.get('priority')!='P0',-int(s.get('reply_acquisition_score') or 0)))
    sender=FeishuSender()
    if candidates and not sender.available():
        return {**result,'state':'CHANNEL_UNAVAILABLE'}
    for signal in candidates[:max(0,limit)]:
        now=datetime.now(timezone.utc)
        allowed,reason,retry=preflight(con,signal,cfg,now)
        if not allowed:
            con.execute("UPDATE alert SET status='EDITORIAL_DEFERRED',retry_at=?,error=? WHERE id=? AND status IN ('PENDING','EDITORIAL_DEFERRED')",(retry or utc_iso(now+timedelta(minutes=15)),reason,signal['alert_id']))
            con.commit();result['deferred']+=1;continue
        claimed=con.execute("UPDATE alert SET status='EDITORIAL_PROCESSING',editorial_status='PROCESSING',editorial_at=?,retry_at=NULL,error=NULL WHERE id=? AND status IN ('PENDING','EDITORIAL_DEFERRED')",(utc_iso(now),signal['alert_id']));con.commit()
        if not claimed.rowcount:continue
        result['processed']+=1
        delivered=False
        send_attempted=False
        try:
            packet=enrich_signal(con,root,signal)
            live=con.execute("SELECT a.id AS alert_id,a.status AS current_alert_status,s.* FROM alert a JOIN signal s ON s.id=a.signal_id WHERE a.id=?",(signal['alert_id'],)).fetchone()
            if not live or live['current_alert_status']!='EDITORIAL_PROCESSING':continue
            current=dict(live);current['operating_lane']=signal['operating_lane']
            if packet.get('decision')=='SKIP':
                con.execute("UPDATE alert SET status='EDITORIAL_SKIP',editorial_status='SKIP',editorial_packet_json=?,editorial_at=?,error=NULL WHERE id=?",(json.dumps(packet,ensure_ascii=False),utc_iso(datetime.now(timezone.utc)),signal['alert_id']));con.commit();result['skipped']+=1;continue
            allowed,reason=notification_policy(con,current,packet,cfg)
            packet['notification_policy']=reason
            if not allowed:
                retry=next_release(cfg) if reason=='operator_asleep' else None
                con.execute("UPDATE alert SET status=?,editorial_status='HOLD',editorial_packet_json=?,retry_at=?,error=? WHERE id=?",('EDITORIAL_DEFERRED' if retry else 'EDITORIAL_HOLD',json.dumps(packet,ensure_ascii=False),retry,reason,signal['alert_id']));con.commit();result['held']+=1;continue
            # Freeze evidence at recommendation time; it is not an exact publication-time measurement.
            snapshot={k:current.get(k) for k in ('canonical_url','metrics_observed_at','observed_views','observed_replies','observed_quotes','views_per_reply','reply_surface_score','distribution_score','reply_acquisition_score')}
            con.execute("UPDATE alert SET opportunity_snapshot_json=? WHERE id=?",(json.dumps(snapshot),signal['alert_id']));con.commit()
            asset=None
            if cfg.get('render_editorial_cards',True):
                try:asset=render_editorial_card(root,current,packet)
                except Exception as exc:packet['asset_error']=type(exc).__name__
            # Rendering can span the sleep boundary. Recheck immediately before the external send.
            if not operator_available(cfg):raise RuntimeError('operator_asleep')
            con.execute("UPDATE alert SET delivery_started_at=? WHERE id=?",(utc_iso(datetime.now(timezone.utc)),signal['alert_id']));con.commit()
            send_attempted=True
            receipt=sender.send_text(format_publish_packet(current,packet,has_asset=bool(asset)))
            delivered=True
            con.execute("UPDATE alert SET status='SENT',sent_at=?,priority=?,channel='feishu',receipt_id=?,editorial_status='READY',editorial_packet_json=?,editorial_at=?,editorial_model=?,error=NULL,asset_path=? WHERE id=? AND status='EDITORIAL_PROCESSING'",(utc_iso(datetime.now(timezone.utc)),current['priority'],receipt,json.dumps(packet,ensure_ascii=False),utc_iso(datetime.now(timezone.utc)),cfg.get('model'),str(asset) if asset else None,signal['alert_id']));con.commit();result['sent']+=1
            if asset and operator_available(cfg):
                try:sender.send_image(asset)
                except Exception as exc:
                    con.execute("UPDATE alert SET error=? WHERE id=?",('image_delivery_failed:'+type(exc).__name__,signal['alert_id']));con.commit()
        except Exception as exc:
            message=str(exc)
            capacity=not send_attempted and ('editorial_budget_exhausted' in message or 'operator_asleep' in message)
            provider=not send_attempted and ('usage limit' in message.lower() or 'rate limit' in message.lower() or 'codex_timeout' in message.lower() or 'timed out' in message.lower() or isinstance(exc,TimeoutError))
            retry=next_release(cfg) if capacity else utc_iso(datetime.now(timezone.utc)+timedelta(minutes=60)) if provider else None
            reason='operator_or_daypart_budget_deferred' if capacity else 'provider_unavailable_backoff' if provider else type(exc).__name__+':'+message[:700]
            if not delivered:
                con.execute("UPDATE alert SET status=?,editorial_status=?,retry_at=?,error=?,editorial_at=? WHERE id=? AND status='EDITORIAL_PROCESSING'",('DELIVERY_UNKNOWN' if send_attempted else 'EDITORIAL_DEFERRED' if retry else 'EDITORIAL_ERROR','HOLD' if send_attempted else 'DEFERRED' if retry else 'ERROR',retry,reason,utc_iso(datetime.now(timezone.utc)),signal['alert_id']));con.commit()
            if retry:
                result['deferred']+=1
                con.execute("INSERT INTO editorial_runtime_state(name,retry_at,reason,updated_at) VALUES('provider_backoff',?,?,?) ON CONFLICT(name) DO UPDATE SET retry_at=excluded.retry_at,reason=excluded.reason,updated_at=excluded.updated_at",(retry,reason,utc_iso(datetime.now(timezone.utc))));con.commit();break
            result['errors']+=1
    return result
