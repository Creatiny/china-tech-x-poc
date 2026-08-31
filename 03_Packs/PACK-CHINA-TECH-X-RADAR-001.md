# PACK-CHINA-TECH-X-RADAR-001

## Pack Header

- Status: `APPROVED / ACTIVE / MVP-FIRST`
- Version: `1.1`
- Priority: `P0`
- Updated: `2026-08-31`
- Change proposals: `CP-001-REALTIME-CHINA-TECH-RADAR`, `CP-002-BUSINESS-VALIDATION-FIRST`
- Requirement: `REQ-CHINA-TECH-X-RADAR-001` v1.1
- Architecture: `ARCH-CHINA-TECH-X-RADAR-001` v1.1
- Delivery repository: `Creatiny/china-tech-x-poc`
- Runtime target: verified Mac mini
- OPC: optional/deferred until business evidence justifies it

## 1. Objective

Launch and validate a zero-new-spend China Tech signal-to-distribution loop with the least engineering necessary to determine whether timely opportunities improve X results.

## 2. Execution Authority

Within the approved requirement and architecture, ordinary technical implementation may proceed without repeated human approval, including:

- code, tests, configuration templates, local deployment, launchd service files, logs, and evidence;
- source adapter fixes;
- exact dedupe and rule tuning;
- Feishu integration using already-authorized credentials once a valid receive target is available;
- GitHub branches/PRs/merges for technical work;
- runtime restart and benign smoke tests.

OPC is one optional way to execute this pack. Direct MCP-assisted implementation is equally valid during business validation.

## 3. Mandatory Human Gates

Stop only for:

1. requirement or architecture boundary change;
2. paid spend, chargeable API, subscription, or auto top-up;
3. automatic X publishing/DM authority;
4. unavailable secret/receiver identity/account permission that cannot be derived safely;
5. destructive or irreversible external action;
6. material platform-policy/legal ambiguity;
7. evidence that invalidates the business hypothesis and requires a strategy decision.

Do not stop for OPC unavailability, Docker failure, lack of a web UI, lack of a local model, technical bugs, tests, merges, or ordinary deployment work.

## 4. Hard Prohibitions

- No paid X API call or stream.
- No automatic X post, reply, or DM.
- No secret values in Git/logs/evidence.
- No fabricated signals or outcomes.
- No new mandatory paid service.
- No Docker/Colima dependency for MVP readiness.
- No OPC copy in this repository.

## 5. Execution Slices

### Slice 0 — Mac mini Fact Audit

Status: `COMPLETE` on 2026-08-31 through direct MCP inspection.

Evidence:

- `artifacts/fact-audit/MAC_MINI_FACT_AUDIT.md`
- `artifacts/fact-audit/MAC_MINI_FACT_AUDIT.json`

The audit established that native Python/SQLite/launchd are available and that Docker/Colima, TrendRadar runtime health, background Chrome, and the existing notification worker must not be treated as ready dependencies.

### Slice 1 — Native MVP Foundation

Deliver:

- Python project/runtime entry point;
- SQLite schema/migration;
- RSS/Atom adapter;
- GitHub adapter;
- exact dedupe;
- deterministic relevance/freshness rules;
- structured cycle/source health logs;
- configuration templates;
- paid-X and auto-publish guard tests.

Accept when one live source can be polled twice without duplicate accepted signals/alerts.

### Slice 2 — Mobile Alert Path

Deliver:

- Feishu alert adapter behind environment/config references;
- bounded retry and alert uniqueness;
- message with source, freshness, reason, source URL, target/search link, and expiry;
- delivery receipt storage.

Accept when one real test alert reaches the operator's mobile-capable channel.

If no Feishu receive target exists, stop only for the minimum receiver/account input. Do not build a notification platform.

### Slice 3 — Decision and Outcome Ledger

Deliver a CLI/simple local command that records:

- decision;
- target URL;
- actual published text;
- posted time;
- available impressions/engagement/profile/follower evidence;
- notes.

Accept when an alert can be linked to one stored operator decision and one nullable outcome record.

### Slice 4 — End-to-End Business Smoke

Run:

```text
live source
 -> accepted signal
 -> dedupe/classification
 -> real mobile alert
 -> human review
 -> stored decision
```

No synthetic signal can satisfy the final smoke, although fixtures may be used before it.

Accept when timestamps and provenance are complete and no paid/publishing boundary was crossed.

### Slice 5 — Seven-Day Shadow Test

Start immediately after Slice 4 passes.

Daily evidence:

- source health and lag;
- new/qualified alert counts;
- P0/P1 review decisions;
- direct-target vs target-search-required counts;
- source-to-alert delay;
- operator time;
- posted reply target age;
- available impressions, engagement, profile, and follower effects;
- false positives/misses/incidents.

Do not pause the test because OPC, Docker, TrendRadar, model scoring, or a web UI is unavailable.

### Slice 6 — Business Decision

At seven valid days, classify the next bottleneck as one of:

- `SOURCE_COVERAGE`
- `TARGET_DISCOVERY`
- `ALERT_PRECISION`
- `OPERATOR_FRICTION`
- `CONTENT_OR_POSITIONING`
- `NO_MEANINGFUL_DISTRIBUTION_LIFT`
- `BUSINESS_SIGNAL_POSITIVE`

Then authorize only the smallest next investment that addresses that bottleneck.

## 6. Success Evidence

Minimum decision evidence includes:

- P0/P1 review precision target >=70%;
- measured source-to-alert delay target <=10 minutes for polled sources;
- median operator time <=30 minutes/day;
- count of verified executable reply opportunities;
- distribution outcomes for every published test action where X exposes them;
- at least one clear distribution lift/profile/follower effect, or an explicit falsification.

A practical early positive signal is a reply with >100 impressions or a measurable profile/follower response. Lack of that signal does not justify more infrastructure by itself.

## 7. Deferred Work

Deferred until evidence proves a bottleneck:

- semantic clustering;
- model scoring;
- web inbox;
- direct browser automation;
- TrendRadar/Colima repair;
- Horizon;
- paid X-native data;
- OPC integration.

The X API pilot remains separately blocked.
