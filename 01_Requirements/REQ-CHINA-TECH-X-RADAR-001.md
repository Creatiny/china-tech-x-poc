# REQ-CHINA-TECH-X-RADAR-001

## 1. Requirement Metadata

- Status: `APPROVED`
- Version: `1.0`
- Date: `2026-08-30`
- Change proposal: `CP-001-REALTIME-CHINA-TECH-RADAR`
- Active delivery pack: `PACK-CHINA-TECH-X-RADAR-001`
- Paid extension: `PACK-CHINA-TECH-X-XAPI-PILOT-001` (`BLOCKED`)

## 2. Product Goal

Provide one operator with a reliable, source-diverse, time-sensitive China Tech opportunity radar that identifies what is worth replying to on X, explains why the opportunity is timely, and keeps daily human operation within 30 minutes.

## 3. Primary User

A single human operator building the English-language `@KennyChinaTech` account.

## 4. Core Jobs

1. Discover material China Tech developments early.
2. Merge duplicate coverage into one traceable event.
3. Distinguish news importance from X reply opportunity.
4. Surface a specific target and a useful response angle.
5. Notify the operator quickly outside email.
6. Capture the operator's decision and the eventual outcome.
7. Learn which sources, topics, targets, timing windows, and response types work.
8. Quantify whether paid X-native data would add enough value to justify cost.

## 5. Functional Requirements

### Source and Ingestion

- **FR-001**: The system shall support Horizon as a source adapter when its presence and usable output are verified.
- **FR-002**: The system shall support TrendRadar as a source adapter when its presence and usable output are verified.
- **FR-003**: The system shall support configurable RSS/Atom feeds.
- **FR-004**: The system shall support GitHub release, repository, and project-event signals using non-chargeable interfaces available to the deployment.
- **FR-005**: The system shall not assume any collector, path, process, database, credential, or runner exists before the Mac mini fact audit.
- **FR-006**: Each ingested signal shall retain source name, source type, canonical URL, original publish time, discovery time, title or excerpt, author when available, language, and a raw-content fingerprint.
- **FR-007**: Source adapters shall expose health, last-success time, last-error, and item counts.
- **FR-008**: Collector failure shall not delete or corrupt previously stored signals.

### Normalization, Deduplication, and Clustering

- **FR-009**: The system shall normalize timestamps to UTC while preserving source timezone when known.
- **FR-010**: The system shall deduplicate exact URLs and content fingerprints.
- **FR-011**: The system shall perform near-duplicate title/content detection.
- **FR-012**: The system shall cluster reports about the same event into a canonical event.
- **FR-013**: A canonical event shall preserve every contributing source and identify the earliest known source.
- **FR-014**: The system shall allow a human to split an incorrect cluster or merge duplicate clusters.

### Filtering and Opportunity Scoring

- **FR-015**: Deterministic rules shall filter obvious noise before any LLM call.
- **FR-016**: The first scoring version shall evaluate China Tech relevance, freshness, source authority, novelty, cross-source confirmation, account-position fit, and X replyability.
- **FR-017**: Every surfaced opportunity shall include a human-readable reason.
- **FR-018**: Opportunities shall be classified as `P0`, `P1`, `P2`, or `DROP`.
- **FR-019**: P0 and P1 opportunities shall include an expiry or review-by time.
- **FR-020**: The system shall distinguish an important event from an executable X reply opportunity.
- **FR-021**: An executable reply opportunity shall include a direct target-post link when one is available; otherwise it shall be labeled as a signal or original-post candidate rather than a reply opportunity.
- **FR-022**: Any generated reply draft shall cite or trace back to the supporting event sources internally and shall not invent facts.

### Alerting and Operator Workflow

- **FR-023**: The system shall support an immediate mobile-capable alert channel verified during the audit; Feishu is preferred when existing credentials are usable, with a configurable alternative such as Bark, ntfy, or webhook.
- **FR-024**: P0 alerts shall be sent individually.
- **FR-025**: P1 alerts may be batched to control notification noise.
- **FR-026**: Alerts shall include event, freshness, source, target link, reason, proposed angle, and expiry.
- **FR-027**: The operator shall be able to mark `POSTED`, `SKIPPED`, `FALSE_POSITIVE`, `EXPIRED`, or `SAVE_FOR_ORIGINAL`.
- **FR-028**: The workflow shall not require the operator to spend more than 30 minutes per day at the median during the Shadow Test.

### Web Inbox and Outcome Tracking

- **FR-029**: A minimal web inbox shall show live opportunities ordered by priority and remaining lifetime.
- **FR-030**: The UI shall show canonical event clusters and source provenance.
- **FR-031**: The UI shall show source health.
- **FR-032**: The UI shall record actual published text and URL when provided by the operator.
- **FR-033**: The system shall record target-post age at reply time.
- **FR-034**: The system shall support manual entry or non-chargeable retrieval of available impressions, engagements, profile visits, and follower changes.
- **FR-035**: The system shall produce a daily and seven-day evidence summary.

### OPC Integration

- **FR-036**: MomentGrid OPC shall be used as the external control plane; its implementation shall not be copied into this repository.
- **FR-037**: The radar runtime shall continue collecting and alerting when the OPC control plane is temporarily unavailable.
- **FR-038**: The repository shall expose only high-level OPC events such as `radar.opportunity.alerted`, `radar.reply.posted`, `radar.reply.skipped`, `radar.outcome.measured`, and `radar.review.ready`.
- **FR-039**: Raw signal volume shall not be pushed into the OPC task queue.
- **FR-040**: OPC may autonomously execute technical implementation, tests, repairs, PRs, merges, deployment, and ordinary configuration within the approved requirements and architecture.
- **FR-041**: OPC shall stop at requirement, architecture, paid-spend, publishing-authority, unavailable-secret, destructive/irreversible external, or explicit policy gates.

### Cost and Publishing Boundaries

- **FR-042**: The active radar pack shall make no paid X API call.
- **FR-043**: The active radar pack shall not buy credits, enable auto top-up, or create a chargeable X stream.
- **FR-044**: The system shall not automatically publish posts or replies.
- **FR-045**: A separate budget gate is required to unblock the X API pilot.
- **FR-046**: Model usage shall be capped and observable; deterministic filtering shall precede model use.

## 6. Non-Functional Requirements

- **NFR-001 — Provenance**: Every alert must be traceable to stored source records.
- **NFR-002 — Idempotency**: Re-ingesting the same source item must not create duplicate canonical signals.
- **NFR-003 — Recoverability**: Restarting a collector or router must not lose accepted signals.
- **NFR-004 — Observability**: Services must expose health, last success, lag, error reason, and processing counts.
- **NFR-005 — Security**: Secrets must not be committed, printed in evidence, or sent to LLM prompts.
- **NFR-006 — Local-first storage**: The foundation version shall store canonical signal and feedback data on the Mac mini unless the architecture is explicitly changed.
- **NFR-007 — Portability**: Source and model providers shall be configured through adapters rather than hard-coded.
- **NFR-008 — Low operating cost**: Foundation validation must add no mandatory new paid service.
- **NFR-009 — Graceful degradation**: Failure of one source, model, notification channel, or OPC integration shall not invalidate all other functioning paths.
- **NFR-010 — Auditability**: Build, deployment, configuration changes, and Shadow Test evidence must be commit- or artifact-addressable.
- **NFR-011 — Human readability**: Alerts and scoring rationales must be understandable without opening logs.
- **NFR-012 — Time semantics**: Published, discovered, scored, alerted, reviewed, and posted timestamps must be distinct.

## 7. Out of Scope for the Active Pack

- Paid X API ingestion.
- Automated X publishing or direct messaging.
- Full social media management across multiple brands.
- Replacing Eden's creator research or long-term memory functions.
- Training a custom model.
- Building a general-purpose OPC copy.
- High-availability multi-node deployment.
- Monetization automation.

## 8. Acceptance Criteria

The active pack is complete only when:

1. the Mac mini fact audit is stored with evidence;
2. at least one verified foundation source is running through the canonical pipeline;
3. all configured adapters expose health;
4. deduplication and clustering tests pass;
5. an operator can receive, review, and classify an opportunity;
6. no paid X API or auto-publishing path is active;
7. the seven-day Shadow Test evidence is complete;
8. an independent verifier issues `PASS`, `CONDITIONAL_PASS`, or `FAIL`;
9. the evidence includes a recommendation to keep the X API pack blocked or request an exact budget gate.
