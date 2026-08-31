# China Tech X Shadow Test — Day 1 Runtime Activation Evidence

## Timestamp

2026-08-31 (Asia/Shanghai)

## Canonical deployed

- GitHub main at deployment: `ea4e707ed94d0ebccfc3c9ed5d710b4d7b21c401`
- Service path: `/Users/jh/services/china-tech-x-radar`
- Runtime: native Python 3.14 + SQLite + launchd
- Paid X API calls: `0`
- Automatic X publishing: disabled

## Verified alert channel

A direct Feishu application-message smoke to the existing operator open-id reference returned:

- HTTP: 200
- Feishu code: 0
- result: success
- message ID: present (value intentionally not recorded)

No receiver ID, application secret, or token is stored in repository evidence.

## First production cycle

```text
sources_due=5
sources_success=5
new_signals=71
bootstrap_qualified_P1=3
alerts_sent=3
source_errors=0
cycle_success=true
```

The first three real alerts were sourced from current Pandaily items and delivered through the production Feishu adapter. Initial false-positive checks were completed before live delivery.

## Source corrections discovered during implementation

- China Daily Business RSS returned HTTP 200 but contained stale historical content; removed from the active set.
- ChinaTechNews returned HTTP 429 during repeated live probing; retained disabled rather than treated as healthy.
- SCMP China feed is active with deterministic tech-topic filtering.
- Pandaily is active and produced the first real qualified signals.
- DeepSeek/Qwen/GLM GitHub release adapters are active with longer poll intervals.

## Classifier corrections before production

- short tokens use boundary-aware matching, preventing `AI` inside `betrayal` and `EV` inside `reveals`;
- title entities are preferred over contextual entities mentioned only in article body;
- alert order is priority then business score, not source insertion order;
- first-run alerts are limited to recent timestamped items.

## launchd

Installed and loaded:

- `com.creatiny.china-tech-x-radar` — `StartInterval=300` seconds;
- `com.creatiny.china-tech-x-daily-review` — daily local review at 22:30.

Immediate launchd kickstart completed with exit status 0 and produced no duplicate alert.

## Shadow Test start

Experiment state started at:

`2026-08-31T09:25:41.405504Z`

Baseline followers: `4`.

The Shadow Test is now live. Business/operator outcomes remain human-generated and must not be inferred from alert delivery alone.
