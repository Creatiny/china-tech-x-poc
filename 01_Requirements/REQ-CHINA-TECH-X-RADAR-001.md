# REQ-CHINA-TECH-X-RADAR-001

## 1. Requirement Metadata

- Status: `APPROVED`
- Version: `1.2`
- Date: `2026-08-31`
- Change proposals: `CP-001-REALTIME-CHINA-TECH-RADAR`, `CP-002-BUSINESS-VALIDATION-FIRST`, `CP-003-AUDIENCE-FIRST-GROWTH-FORMULA`
- Active pack: `PACK-CHINA-TECH-X-RADAR-001` v1.2
- Paid extension: `PACK-CHINA-TECH-X-XAPI-PILOT-001` (`BLOCKED`)

Version 1.2 makes audience-first follower growth and repeatable growth-formula discovery the explicit business objective. Business validation remains independent of OPC, Docker, web UI, model scoring, Horizon, or paid X APIs.

## 2. Product Goal

Provide one operator with timely, traceable China Tech opportunities and an evidence loop that grows `@KennyChinaTech` from a four-follower baseline, discovers which event/target/timing/angle combinations repeatedly create distribution and follower gains, and keeps human operation near 30 minutes/day.

## 3. Primary User

A single human operator building the English-language `@KennyChinaTech` account.

## 4. Core Jobs

1. Discover material China Tech developments early.
2. Avoid repeatedly alerting the same item.
3. Explain why an item is relevant and time-sensitive.
4. Give the operator the fastest available path to a useful X reply target.
5. Notify the operator outside email.
6. Capture posted/skipped/expired/false-positive decisions.
7. Capture available distribution outcomes.
8. Identify the next proven bottleneck before adding tools or spend.

## 5. MVP Functional Requirements

### Source and ingestion

- **FR-001**: The MVP shall support configurable RSS/Atom sources without requiring a paid service.
- **FR-002**: The MVP shall support GitHub releases/repository events through non-chargeable interfaces available to the deployment.
- **FR-003**: Additional free sources may be added only when they improve China Tech coverage or timeliness and remain traceable.
- **FR-004**: TrendRadar may be used read-only or repaired later, but it is not required for MVP readiness.
- **FR-005**: Horizon is optional and must not be installed merely to satisfy an old architecture assumption.
- **FR-006**: Every signal shall retain source, canonical URL, title/excerpt, original publish time when available, discovery time, and a stable fingerprint.
- **FR-007**: Every source adapter shall expose last-success, last-error, and item count in logs or local state.
- **FR-008**: A source failure shall not corrupt previously accepted signals.

### Deduplication and relevance

- **FR-009**: The MVP shall exact-deduplicate by source-item identity, canonical URL, and/or stable content fingerprint.
- **FR-010**: Near-duplicate clustering is deferred until duplicate-alert evidence shows exact dedupe is insufficient.
- **FR-011**: Deterministic relevance rules shall run before any optional model call.
- **FR-012**: Initial rules shall cover China AI, semiconductors/AI infrastructure, robotics/hardware, EV/advanced manufacturing, and China-tech global-business impact.
- **FR-013**: Qualified items shall be classified at minimum as `P0`, `P1`, `P2`, or `DROP` with a human-readable reason.
- **FR-014**: P0/P1 shall have an expiry/review-by time.
- **FR-015**: Model scoring is optional and shall not be introduced until deterministic-rule quality is measured.

### X target path

- **FR-016**: A direct X target-post link shall be included when verified and available.
- **FR-017**: If no direct target exists, the alert may include a prefilled X live-search link and be labeled `TARGET_SEARCH_REQUIRED`.
- **FR-018**: An item without a verified target post shall not be counted as an executable reply opportunity.
- **FR-019**: Direct X-native discovery, browser automation, Eden lookup, or paid X API access may be added only when target discovery is proven to be the bottleneck.

### Alerting and operator workflow

- **FR-020**: The system shall deliver production China Tech alerts only to the human-verified personal Feishu route. Group-chat delivery is prohibited unless the human owner explicitly changes the spec.
- **FR-021**: Email shall not be the P0 primary channel.
- **FR-022**: P0/P1 signals shall preserve enough urgency for Stage-A early-reply testing; batching may be introduced only if notification noise becomes the measured bottleneck.
- **FR-023**: Alerts shall include source, freshness, reason, source link, target/search link, suggested angle when available, and expiry.
- **FR-024**: The operator shall be able to record `POSTED`, `SKIPPED`, `FALSE_POSITIVE`, `EXPIRED`, or `SAVE_FOR_ORIGINAL` without a web UI.
- **FR-025**: The median daily operator workflow shall fit within 30 minutes during the Shadow Test.

### Outcome evidence

- **FR-026**: The system shall record the published X URL and actual text when supplied by the operator.
- **FR-027**: The system shall distinguish source-published, discovered, alerted, reviewed, and posted timestamps.
- **FR-028**: The system shall record target-post age at reply time when known.
- **FR-029**: Available impressions, engagements, profile visits, follower change, and qualitative outcomes shall be recorded without converting unknowns to zero.
- **FR-030**: A daily KPI/formula summary and milestone decision summaries for Day 3/7/10/15/30 shall be producible from local records.

### Growth formula and follower KPI

- **FR-047**: Every published action shall distinguish `REPLY` vs `ORIGINAL`.
- **FR-048**: Where available, every reply shall capture target account, approximate target follower count, target-post timestamp/age, and visible target impressions at reply time.
- **FR-049**: Every action should classify event/topic, content angle, hook, media treatment, and external-link usage.
- **FR-050**: Outcome snapshots shall support impressions, engagement and available likes/replies/reposts/quotes/bookmarks/profile visits without converting unknowns to zero.
- **FR-051**: Daily account snapshots shall preserve total followers and follower delta.
- **FR-052**: The runtime shall produce a formula report comparing event/topic, target tier, target-post age bucket, angle, hook, media, and link treatment.
- **FR-053**: A single breakout post shall not be classified as a proven growth formula; >=3 repeated wins are required for a candidate and >=5 repeated wins plus follower-positive cohorts for scale bias.
- **FR-054**: The active milestone follower targets are Day 3 >=8, Day 7 >=15, Day 10 >=25, Day 15 >=40, Day 30 >=100, with Day-30 stretch >=200.
- **FR-055**: During Stage A, the operating target is approximately 3–5 qualified strategic replies/day and roughly one differentiated original on active days when material exists; quality/opportunity supply outranks quota completion.

### Runtime and storage

- **FR-031**: The MVP shall run natively on the verified Mac mini using Python and SQLite unless a later architecture change is approved.
- **FR-032**: The MVP shall be schedulable through launchd at an approximately five-minute polling cadence.
- **FR-033**: The MVP shall not require Docker/Colima.
- **FR-034**: Re-running a polling cycle shall be idempotent with respect to accepted signals and sent alerts.
- **FR-035**: Runtime state shall survive process restarts through SQLite/checkpoints.

### OPC integration

- **FR-036**: OPC integration shall not be required to build, deploy, start, or continue the business-validation MVP.
- **FR-037**: If OPC is connected later, it shall remain outside the per-signal runtime path.
- **FR-038**: A future OPC adapter shall receive only high-level lifecycle/evidence events, not raw signal volume.
- **FR-039**: The business runtime shall continue when OPC is unavailable.
- **FR-040**: Reconnecting OPC requires evidence that delivery/governance complexity is a real bottleneck; it does not require a new business hypothesis.
- **FR-041**: No OPC implementation shall be copied into this repository.

### Cost and publishing boundaries

- **FR-042**: Mandatory new software/service spend for the MVP shall be `$0`.
- **FR-043**: No paid X API call, purchase, stream, or auto top-up is authorized.
- **FR-044**: The system shall not automatically publish X posts, replies, or DMs.
- **FR-045**: A separate exact budget gate is required to unblock the X API pilot.
- **FR-046**: Any future model use shall be capped, observable, and downstream of deterministic filtering.

## 6. Deferred Until a Bottleneck Is Proven

The following are explicitly non-blocking for the seven-day Shadow Test:

- full event clustering/semantic deduplication;
- a web inbox/dashboard;
- Dockerized deployment;
- PostgreSQL/Redis;
- Horizon;
- local LLM deployment;
- model-based scoring;
- automated X target resolver;
- MomentGrid OPC integration;
- paid X-native data;
- automatic publishing.

## 7. Non-Functional Requirements

- **NFR-001 — Provenance**: every alert is traceable to stored source data.
- **NFR-002 — Recoverability**: restart does not lose accepted signals or checkpoints.
- **NFR-003 — Security**: secrets are never committed or printed into evidence.
- **NFR-004 — Local-first**: canonical MVP records remain on the Mac mini.
- **NFR-005 — Low cost**: the MVP introduces no mandatory paid service.
- **NFR-006 — Graceful degradation**: one source or optional subsystem failure does not stop the remaining loop.
- **NFR-007 — Human readability**: alerts and reasons are understandable without log inspection.
- **NFR-008 — Auditability**: code/config/evidence changes are Git-addressable.

## 8. MVP Readiness Acceptance

The seven-day Shadow Test may start when:

1. at least one live free source flows into SQLite;
2. repeated polling does not duplicate the same alert;
3. deterministic relevance classification is visible;
4. one real P0/P1 test alert reaches the intended operator personally through the verified Feishu route;
5. the operator can record a decision and later attach an outcome;
6. no paid X or auto-publishing path is active.

## 9. Audience-Growth Decision Criteria

The business experiment is governed by Day 3/7/10/15/30 KPI from `OPERATING_KPI.md`.

At each milestone, evidence must answer:

- current follower count and delta from baseline;
- strategic reply and original-post counts;
- repeated reach thresholds (100/300/1000+ impressions);
- source-to-alert latency and source misses;
- target account/tier and target-post age for replies where known;
- angle/hook/media/link treatment performance;
- whether any combination has reached the growth-formula evidence standard;
- which first growth-funnel stage is broken if KPI is off track.

The Day-30 minimum follower target is 100 from a baseline of 4. If the target is missed, diagnose signal/target/timing/distribution/profile conversion/original-content positioning before adding infrastructure.
