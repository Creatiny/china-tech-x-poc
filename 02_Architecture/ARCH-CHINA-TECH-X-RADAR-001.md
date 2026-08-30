# ARCH-CHINA-TECH-X-RADAR-001

## 1. Architecture Metadata

- Status: `APPROVED`
- Version: `1.0`
- Date: `2026-08-30`
- Requirement: `REQ-CHINA-TECH-X-RADAR-001`
- Active pack: `PACK-CHINA-TECH-X-RADAR-001`

## 2. Architecture Summary

The system separates the realtime data plane from the OPC control plane.

```text
Foundation Sources
  Horizon | TrendRadar | RSS/Atom | GitHub
             |
             v
      Source Adapters
             |
             v
  Canonical Signal Store (SQLite)
             |
             v
 Deduplication + Event Clustering
             |
             v
 Deterministic Filter -> Optional Model Scoring
             |
             v
  Opportunity Store + Expiry Engine
       |                 |
       v                 v
 Mobile Alerts       Minimal Web Inbox
       \                 /
        \               /
         Human Publish / Skip
                  |
                  v
          Outcome Tracker
                  |
                  v
      High-level OPC Events Only
```

MomentGrid OPC controls implementation, verification, deployment governance, and reviews. It is not in the per-signal runtime path.

## 3. Deployment Boundary

### Mac mini

Expected deployment target, subject to fact audit:

- collectors or collector adapters;
- signal router;
- SQLite canonical store;
- scoring worker;
- alert gateway;
- web inbox;
- health monitor;
- outcome tracker.

No path, service manager, container runtime, existing checkout, runner, or credential is assumed.

### GitHub

- `Creatiny/china-tech-x-poc`: domain canonical, source code, configuration templates, tests, and evidence references.
- `Creatiny/momentgrid`: existing OPC control plane and its canonical governance.
- Cross-repository execution must bind to exact commits and preserve provenance.
- No OPC source is copied into the China Tech repository.

## 4. Components

### 4.1 Source Adapters

Adapters transform verified source output into `SignalEnvelope`.

Initial adapter classes:

- `horizon`
- `trendradar`
- `rss`
- `github`

Each adapter implements:

```text
poll_or_receive()
normalize()
checkpoint()
health()
```

Adapters must not directly modify another tool's database. Where upstream tools expose only local storage, the adapter uses a documented read-only interface or export.

### 4.2 Canonical Signal Store

Foundation version: SQLite with WAL mode and explicit migrations.

Core tables:

```text
source
source_checkpoint
raw_signal
canonical_event
event_signal_link
opportunity
opportunity_decision
published_action
outcome_snapshot
service_health
config_revision
```

SQLite is selected for a single Mac mini and expected POC volume. PostgreSQL requires a new architecture decision only if measured concurrency or volume proves SQLite insufficient.

### 4.3 Signal Envelope

```text
signal_id
source_type
source_name
source_item_id
source_url
canonical_url
author
title
content_excerpt
published_at
discovered_at
source_timezone
language
entities
topic_hints
raw_hash
payload_ref
```

Raw payloads may be retained locally when permitted, but alerts and model prompts use only the minimum needed content.

### 4.4 Deduplication and Event Clustering

Ordered pipeline:

1. exact source-item identity;
2. canonical URL match;
3. raw fingerprint match;
4. normalized-title similarity;
5. entity and event-type overlap within a time window;
6. optional semantic similarity for unresolved candidates.

The event cluster stores:

- earliest source;
- all source links;
- first-seen and last-updated times;
- entity set;
- event type;
- confidence;
- cluster history.

Human split/merge creates an auditable correction event.

### 4.5 Opportunity Scoring

Version 1 score:

| Dimension | Weight |
|---|---:|
| China Tech relevance | 25 |
| Freshness | 20 |
| X replyability | 20 |
| Source authority | 15 |
| Novelty | 10 |
| Cross-source confirmation | 5 |
| Account positioning fit | 5 |

Deterministic checks run first. Model scoring is optional and limited to the surviving candidate set.

Suggested classes:

- `P0`: immediate, short-lived opportunity;
- `P1`: same-day executable opportunity;
- `P2`: research or original-post candidate;
- `DROP`: no operator notification.

The score is not sufficient by itself. Every opportunity stores a rationale and missing-evidence flags.

### 4.6 Target Resolver

The foundation version may use:

- links already embedded in source items;
- verified non-chargeable source references;
- operator-supplied X links;
- a read-only browser-assisted step where available and compliant.

If no direct X target can be verified, the item cannot be labeled an executable reply opportunity.

Paid X-native search or stream behavior belongs only to the blocked X API pack.

### 4.7 Alert Gateway

Interface:

```text
send_p0(opportunity)
send_p1_digest(opportunities)
send_system_health(alert)
```

Delivery channel is selected only after the audit verifies credentials and user reachability. Preferred order:

1. existing Feishu channel;
2. existing Bark, ntfy, or equivalent mobile channel;
3. generic webhook.

Email is not the primary P0 channel.

### 4.8 Minimal Web Inbox

Required views:

- Live Opportunities
- Event Clusters
- Decision / Reply Log
- Outcomes
- Source Health
- Cost and Model Usage

Required actions:

- `POSTED`
- `SKIPPED`
- `FALSE_POSITIVE`
- `EXPIRED`
- `SAVE_FOR_ORIGINAL`

The UI does not publish to X.

### 4.9 Outcome Tracker

Tracks:

- event and opportunity IDs;
- target account and target URL;
- target age when action was taken;
- actual text and published URL;
- available impressions and engagements;
- profile visits and follower change when available;
- source, topic, timing, and response-style features.

Missing metrics remain `UNKNOWN`; they must not be replaced with zero.

### 4.10 OPC Adapter

Only emits high-level, low-volume events:

```text
radar.opportunity.alerted
radar.reply.posted
radar.reply.skipped
radar.false_positive.recorded
radar.outcome.measured
radar.shadow_test.day_closed
radar.review.ready
radar.health.degraded
```

The adapter is asynchronous and non-blocking. OPC unavailability must not stop collection, scoring, alerting, or local feedback capture.

## 5. Mac mini Fact Audit Contract

The first task is read-only by default and must establish:

- machine identity and operating-system version;
- project directories and existing checkouts;
- Horizon presence, version, path, configuration location, process state, data path, latest data time, startup mode, and health;
- TrendRadar presence, version, path, configuration location, process state, data path, latest data time, startup mode, and health;
- Docker/Podman, Python/uv, Node/Bun, cron, and launchd availability;
- existing notification channels and credential references, without exposing secret values;
- existing MomentGrid OPC agent/runner path and health;
- whether the runner can execute a controlled command on the Mac;
- disk capacity, ports in use, and backup constraints;
- available local or routed models and non-secret endpoint names;
- blockers and safest remediation path.

The audit output is a structured evidence artifact. A missing component is a fact, not a failure and not permission to invent it.

## 6. Security and Privacy

- Secrets remain in existing secret stores or local environment files outside Git.
- Evidence records secret names and presence only.
- Raw private data is not sent to hosted models without an approved data boundary.
- Source licensing and platform rules must be respected.
- The system uses least-privilege access.
- Automatic X publishing and direct messaging remain absent.
- Paid X API code is inactive and has no live credential dependency in the active pack.

## 7. Reliability

- SQLite uses migrations, WAL, backups, and one designated writer per queue.
- Adapters use checkpoints and idempotent upsert.
- Alert delivery retries are bounded and deduplicated.
- A dead-letter table retains failed items.
- Services expose heartbeat and lag.
- Service startup must be reproducible through the verified service manager.
- A restart smoke test is required before runtime readiness.

## 8. Cost Controls

Foundation pack:

- X API read cost: `$0`.
- Mandatory new tool spend: `$0`.
- Model calls are counted and capped.
- Deterministic filtering reduces model volume.
- Cost/usage panel distinguishes local, subscribed, free-tier, and metered providers.

Blocked X API pack, if later approved:

- exact monetary ceiling;
- exact unique-post ceiling;
- automatic shutdown;
- usage reconciliation;
- no auto top-up.

## 9. Key Architecture Decisions

### AD-001 — Opportunity-led, not quota-led

Accepted. Daily posting is conditional.

### AD-002 — Eden as Research/Memory Layer

Accepted. Eden is useful but is not the sole realtime source and alert chain.

### AD-003 — Reuse foundation collectors

Accepted, contingent on Mac audit. Do not rebuild Horizon or TrendRadar capabilities without evidence of a gap.

### AD-004 — SQLite for POC

Accepted. Revisit only with measured evidence.

### AD-005 — Separate OPC control plane and radar data plane

Accepted. Prevents governance latency and OPC downtime from blocking realtime monitoring.

### AD-006 — Manual X publising

Accepted as a hard boundary.

### AD-007 — Paid X API as a blocked extension

Accepted. The pilot is evidence-triggered and budget-gated.

## 10. Failure Modes and Responses

| Failure | Required behavior |
|---|----|
| One source stops | Mark degraded; continue other sources |
| All sources stale | Send system-health alert; do not fabricate opportunities |
| Model unavailable | Continue deterministic scoring and label reduced confidence |
| Notification fails | Retry boundedly; retain unsent alert; show in inbox |
| Duplicate alert | Suppress by opportunity key and channel receipt |
| OPC unavailable | Queue high-level events locally; continue radar |
| No target X post | Reclassify as signal/original candidate |
| Source timestamp absent | Mark unknown; reduce freshness confidence |
| Budgeted service requested | Fail closed unless its pack is unblocked |
| Restart | Resume from checkpoints without duplicate operator alerts |

## 11. Verification Strategy

- schema and migration tests;
- adapter contract tests with fixtures;
- idempotency tests;
- duplicate and cluster golden cases;
- scoring golden cases;
- alert deduplication tests;
- expiry tests;
- failure-injection tests;
- restart/recovery smoke;
- no-paid-X-API static and runtime assertions;
- no-auto-publish assertion;
- seven-day evidence verifier.
