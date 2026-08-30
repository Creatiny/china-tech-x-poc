# PACK-CHINA-TECH-X-RADAR-001

## Pack Header

- Status: `APPROVED / ACTIVE`
- Priority: `P0`
- Date activated: `2026-08-30`
- Change proposal: `CP-001-REALTIME-CHINA-TECH-RADAR`
- Requirement: `REQ-CHINA-TECH-X-RADAR-001`
- Architecture: `ARCH-CHINA-TECH-X-RADAR-001`
- Delivery repository: `Creatiny/china-tech-x-poc`
- Control plane: existing MomentGrid OPC in `Creatiny/momentgrid`
- Runtime target: Mac mini, subject to fact audit
- Human owner: final product, paid-spend, architecture, requirement, and publishing authority

## 1. Objective

Deliver and validate a zero-new-mandatory-spend China Tech realtime opportunity radar through a seven-day Shadow Test.

## 2. Authority

Within the approved requirement and architecture, OPC is authorized to:

- create technical issues and branches;
- implement and refactor code;
- add tests and fixtures;
- create, update, review, and merge technical PRs;
- fix ordinary bugs and CI failures;
- configure verified local services;
- deploy and restart the radar on the Mac mini;
- add bounded health checks, logs, backups, and rollback;
- update implementation evidence and project status;
- choose implementation details that do not alter requirements, architecture boundaries, paid spend, or publishing authority.

Repeated human approval is not required for those activities.

## 3. Mandatory Stop Gates

Stop and report an evidence-backed Human Gate only when any of the following is required:

1. requirement change;
2. architecture boundary change;
3. paid purchase, paid API call, auto top-up, or increased monetary exposure;
4. automatic X post/reply/DM publishing;
5. unavailable secret or account permission that cannot be resolved technically without the owner;
6. destructive or irreversible external action;
7. legal/platform-policy ambiguity with material risk;
8. measured evidence that invalidates the approved product hypothesis.

Do not stop merely because a technical bug, test failure, merge, deployment step, or ordinary configuration change occurs.

## 4. Hard Prohibitions

- No paid X API purchase or call.
- No X API stream connection.
- No automated X post, reply, or DM.
- No OPC copy in this repository.
- No secret value in Git, logs, prompts, PRs, issues, or evidence.
- No assumption that Horizon, TrendRadar, the runner, notification credentials, or project paths exist.
- No fabricated signal, metric, health result, or Shadow Test day.
- No claim of runtime readiness before restart and delivery smoke tests pass.

## 5. Execution Slices

### Slice 0 — Canonical Sync and Mac mini Fact Audit

#### Deliverables

- canonical documents merged to `main`;
- exact canonical commit recorded;
- OPC intake bound to the exact commit and pack content hash;
- `artifacts/fact-audit/MAC_MINI_FACT_AUDIT.json`;
- `artifacts/fact-audit/MAC_MINI_FACT_AUDIT.md`;
- evidence of controlled Mac command execution or an explicit execution-path blocker;
- inventory of Horizon, TrendRadar, runtimes, services, data paths, notification channels, runner/agent path, storage, ports, and model routes;
- no secret values.

#### Acceptance

- audit fields are complete or explicitly `NOT_FOUND` / `UNKNOWN_WITH_REASON`;
- no component is reported present without command/file/process evidence;
- first modification after the audit is tied to an identified fact or gap.

### Slice 1 — Repository and Runtime Foundation

#### Deliverables

- implementation layout;
- configuration templates;
- canonical signal schema;
- SQLite migrations;
- service health contract;
- local development and Mac deployment runbooks;
- test harness;
- cost and paid-X guard assertions.

#### Acceptance

- clean setup is reproducible;
- migrations are idempotent;
- no paid X credential is required;
- no publishing endpoint exists.

### Slice 2 — Verified Source Adapters

#### Deliverables

- adapters only for sources verified or safely installable under the approved architecture;
- Horizon adapter;
- TrendRadar adapter;
- RSS/Atom adapter;
- GitHub adapter;
- checkpoints, health, fixtures, and error handling.

A missing Horizon or TrendRadar installation may be installed or configured as an ordinary technical action only after the audit records the gap and the action creates no new paid commitment or architecture change.

#### Acceptance

- at least one live foundation source flows end-to-end;
- each configured adapter passes contract and idempotency tests;
- source health and lag are visible;
- upstream databases are read-only from adapters unless an official write interface is explicitly required and approved by architecture.

### Slice 3 — Deduplication, Clustering, and Opportunity Scoring

#### Deliverables

- exact and near-duplicate handling;
- canonical event clusters;
- deterministic filter;
- optional bounded model scorer;
- P0/P1/P2/DROP classification;
- rationale and expiry;
- golden-case tests;
- human split/merge correction.

#### Acceptance

- duplicate fixtures do not create duplicate alerts;
- one event can retain multiple sources;
- every P0/P1 contains a traceable rationale;
- no direct X target means no executable reply classification.

### Slice 4 — Alerts, Web Inbox, Feedback, and Outcomes

#### Deliverables

- verified mobile-capable alert integration;
- P0 immediate alerts and P1 digest;
- minimal web inbox;
- decision workflow;
- outcome tracker;
- source health and usage views;
- notification deduplication and bounded retry.

#### Acceptance

- operator receives a test alert on the chosen channel;
- each action is persisted;
- no UI or backend action publishes to X;
- missing outcomes remain unknown rather than zero.

### Slice 5 — Deployment and Runtime Readiness

#### Deliverables

- verified service manager configuration;
- backup and rollback;
- restart/recovery test;
- end-to-end smoke;
- health alert;
- runtime evidence.

#### Acceptance

- Mac restart or service restart recovers without duplicate alerts;
- checkpoints resume correctly;
- failure of one adapter does not stop the pipeline;
- OPC outage simulation does not stop radar runtime.

### Slice 6 — Seven-Day Shadow Test

#### Entry Criteria

- Slices 0–5 accepted;
- runtime health passes;
- notification path verified;
- paid X guard passes;
- operator workflow available.

#### Daily Evidence

- source health and lag;
- raw and canonical signal counts;
- P0/P1/P2 counts;
- reviewed, posted, skipped, false-positive, expired counts;
- discovery and alert delays;
- operator time;
- available outcomes;
- incidents and repairs.

#### Exit Criteria

- seven consecutive valid days;
- verifier report;
- success-criteria table;
- source and scoring recommendations;
- explicit recommendation:
  - keep X API pack blocked; or
  - request a separate Human Budget Gate with exact ceiling and evidence.

## 6. Quality Gates

- lint/type/test appropriate to selected stack;
- migrations test;
- adapter contract test;
- idempotency test;
- cluster golden test;
- score golden test;
- alert dedupe test;
- expiry test;
- restart/recovery smoke;
- static and runtime `NO_PAID_X_API` gate;
- static and runtime `NO_AUTOPUBLISH` gate;
- independent evidence verifier.

## 7. Evidence Contract

Every completion claim must identify:

- exact repository commit;
- exact configuration revision without secret values;
- command or workflow used;
- test and verifier result;
- runtime target;
- artifact path;
- known limitation;
- rollback path.

`DONE` without evidence is invalid.

## 8. OPC Event Boundary

Emit high-level events only:

```text
radar.build.started
radar.build.verified
radar.runtime.ready
radar.opportunity.alerted
radar.reply.posted
radar.reply.skipped
radar.false_positive.recorded
radar.outcome.measured
radar.shadow_test.day_closed
radar.review.ready
radar.health.degraded
```

Raw signals remain in the radar data plane.

## 9. Completion Definition

The pack is complete only when:

1. all slices pass;
2. the seven-day verifier report exists;
3. project status is updated;
4. paid X usage remains zero;
5. automated publishing remains absent;
6. the next decision is stated as an evidence-backed gate, not an assumption.
