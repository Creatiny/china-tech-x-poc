# PACK-CHINA-TECH-X-RADAR-001

## Pack Header

- Status: `APPROVED / ACTIVE / MVP-FIRST`
- Version: `1.3`
- Priority: `P0`
- Updated: `2026-08-31`
- Change proposals: `CP-001-REALTIME-CHINA-TECH-RADAR`, `CP-002-BUSINESS-VALIDATION-FIRST`, `CP-003-AUDIENCE-FIRST-GROWTH-FORMULA`
- Requirement: `REQ-CHINA-TECH-X-RADAR-001` v1.3
- Architecture: `ARCH-CHINA-TECH-X-RADAR-001` v1.3
- Delivery repository: `Creatiny/china-tech-x-poc`
- Runtime target: verified Mac mini
- OPC: optional/deferred until business evidence justifies it

## 1. Objective

Operate the zero-new-spend China Tech growth loop, reach the active follower KPI, and discover the repeatable event/target/timing/angle formula that produces relevant follower growth.

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


### Slice 2.5 — Editorial Publishing Packet

Deliver:

- deterministic false-positive hardening so generic `China` alone cannot qualify entity-only Reuters items;
- bounded ChatGPT OAuth/Codex editorial gate and final enrichment;
- `POST / REPLY / SKIP` decision contract;
- silent persisted `SKIP`;
- verified direct X target requirement for `REPLY`;
- final humanized English copy ready to paste;
- personal Feishu publish packet formatting;
- original editorial-card renderer and Feishu image upload/send path;
- local model usage/call/token proxy logging and daily caps.

Accept when a known macro false positive is suppressed, a real China Tech candidate produces a structured publish-ready packet, and visual upload works without a paid Platform API key.

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

### Slice 5 — Audience-First 30-Day Growth Test

The valid experiment clock starts only after the intended operator has human-confirmed the personal Feishu route.

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

### Slice 6 — Milestone Growth Decisions

At Day 3/7/10/15/30, classify the first broken growth stage as one of:

- `SOURCE_COVERAGE`
- `TARGET_DISCOVERY`
- `ALERT_PRECISION`
- `OPERATOR_FRICTION`
- `CONTENT_OR_POSITIONING`
- `NO_MEANINGFUL_DISTRIBUTION_LIFT`
- `FOLLOWER_CONVERSION`
- `ORIGINAL_DISTRIBUTION`
- `GROWTH_FORMULA_CANDIDATE`
- `GROWTH_SIGNAL_POSITIVE`

Then authorize only the smallest next investment that addresses that bottleneck.

## 6. Success Evidence

Active success evidence is defined by `PROJECT_SPEC.md` and `OPERATING_KPI.md` v3.0.

Minimum Day-30 POC success requires:

- followers >=100 from baseline 4;
- >=90 strategic replies and >=25 differentiated originals, subject to qualified opportunity supply/quality;
- repeated distribution: >=10 actions >=300 impressions, >=3 >=1,000, >=1 >=5,000;
- measured runtime health and median operator time near the <=30 min/day design constraint;
- formula evidence showing repeated winning combinations or a clear falsification/next bottleneck;
- personal Feishu alert reliability;
- zero paid X API and no automatic X publishing unless separately approved.

One viral post alone does not satisfy the growth-formula objective.

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
