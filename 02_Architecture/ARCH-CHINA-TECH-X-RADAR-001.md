# ARCH-CHINA-TECH-X-RADAR-001

## 1. Architecture Metadata

- Status: `APPROVED`
- Version: `1.2`
- Date: `2026-08-31`
- Requirement: `REQ-CHINA-TECH-X-RADAR-001` v1.2
- Active pack: `PACK-CHINA-TECH-X-RADAR-001` v1.2
- Change proposals: `CP-002-BUSINESS-VALIDATION-FIRST`, `CP-003-AUDIENCE-FIRST-GROWTH-FORMULA`

## 2. Architecture Principle

Use the smallest runtime that can produce business evidence. The MVP is a native one-shot polling cycle scheduled by launchd; it does not require a container platform, web server, model service, message bus, or OPC control plane.

## 3. MVP Data Flow

```text
Curated free sources
RSS/Atom | GitHub | verified zero-cost endpoints
                    |
                    v
          source adapters / poll
                    |
                    v
        normalize + exact dedupe
                    |
                    v
            SQLite evidence DB
                    |
                    v
 deterministic relevance + freshness
                    |
                    v
            P0/P1/P2/DROP
                    |
                    v
       mobile alert adapter (Feishu)
                    |
                    v
       human target selection on X
                    |
                    v
         human publish / skip
                    |
                    v
       decision + outcome recorder
```

Optional systems are added to the side of this loop, never inserted as mandatory dependencies without evidence.

## 4. Verified Deployment Boundary

### Mac mini

Verified 2026-08-31:

- macOS 26.5.2 / arm64 / 16 GB RAM;
- Python 3.14 and 3.12;
- `uv`;
- SQLite;
- launchd;
- Git/GitHub CLI;
- MacDeveloperBridge MCP;
- no healthy Docker/Colima requirement;
- no verified China Tech model route;
- personal Feishu receive target human-verified and active; group delivery prohibited.

### Repository

`Creatiny/china-tech-x-poc` contains domain canonical, MVP runtime code, configuration templates, tests, and evidence references.

### Runtime deployment path

Preferred local deployment path after implementation:

`/Users/jh/services/china-tech-x-radar`

Preferred launchd label:

`com.creatiny.china-tech-x-radar`

These are implementation defaults, not external architecture dependencies.

## 5. MVP Components

### 5.1 `run_cycle`

One idempotent process invocation performs:

1. load configuration;
2. poll enabled sources;
3. normalize items;
4. exact-deduplicate/store;
5. classify new items;
6. queue/send unsent qualified alerts;
7. update source health;
8. emit a structured cycle summary;
9. exit.

launchd executes the cycle approximately every five minutes. A short-lived cycle is preferred over a custom always-on daemon during validation because restart behavior is simpler and observable.

### 5.2 Source adapters

MVP adapters:

- RSS/Atom;
- GitHub releases/repository events;
- optional simple HTTP/JSON endpoints that are free and traceable.

Each adapter returns a common envelope:

```text
source_type
source_name
source_item_id
source_url
canonical_url
title
excerpt
published_at
discovered_at
author
raw_hash
```

TrendRadar is not an MVP adapter until its value is proven. If reused, the first integration is read-only against its existing SQLite outputs.

### 5.3 SQLite store

Minimum tables:

```text
source_state
signal
alert
operator_decision
published_action
outcome_snapshot
account_snapshot
daily_ops
runtime_cycle
experiment_state
```

SQLite uses WAL mode and migrations. No PostgreSQL/Redis is introduced for the POC.

### 5.4 Deterministic classifier

First pass uses:

- source allowlist/weight;
- China-company/entity/topic matches;
- publish/discovery freshness;
- material-event keywords;
- obvious-noise exclusions;
- duplicate suppression.

The classifier stores a reason string and rule revision. Model scoring is a later adapter, not a base dependency.

### 5.5 X target path

Order of preference:

1. verified direct X target URL carried by a source or manually configured watch target;
2. prefilled X live-search link built from the event/entity;
3. human search and selection;
4. only after evidence: browser resolver, Eden lookup, official X-native read path, or another approved resolver.

Only direct verified post URLs count as executable reply opportunities.

### 5.6 Alert adapter

Interface:

```text
send(opportunity) -> delivery_receipt
health() -> status
```

Production adapter: Feishu application message to the matched, human-verified personal `open_id`. Group chat is not an authorized China Tech production destination.

Required alert content:

- priority;
- event title;
- source and age;
- why it matters;
- source URL;
- direct X target or `TARGET_SEARCH_REQUIRED` search link;
- proposed reply angle when deterministic/template logic can provide one;
- expiry/review-by time;
- evidence ID.

The current Deyue notification worker is not reused because it is broken and configured dry-run. Only small reusable Feishu auth/send logic may be copied/refactored if license/ownership is clear, with no secret values copied.

### 5.7 Decision/outcome recorder

No web UI is required. The first interface may be a CLI command or small local command wrapper to record:

```text
POSTED / SKIPPED / FALSE_POSITIVE / EXPIRED / SAVE_FOR_ORIGINAL
published_url
published_text
notes
impressions
engagements
profile_visits
follower_delta
formula variables: event/target tier/target age/angle/hook/media/link treatment
```

Unknown metrics remain null.


### 5.8 Growth-formula analyzer

The runtime computes distribution comparisons by action type, event/topic, target account/tier, target-age bucket, angle, hook, media and external-link treatment.

Daily follower snapshots are joined as cohorts rather than falsely assigning overlapping follower gains to one action. Formula evidence follows `GROWTH_FORMULA.md`: 1 sample anecdote, 2 hypothesis, >=3 repeated wins candidate, >=5 repeated wins plus follower-positive cohorts eligible for scale bias.

## 6. Configuration

Use a repository template plus local ignored runtime config.

Suggested structure:

```text
config/sources.toml
config/rules.toml
config/runtime.example.toml
.local/runtime.toml        # ignored; may reference secret env names
runtime/china-tech-x.db    # ignored
```

Secrets remain in environment/keychain/local ignored config and are never written into Git.

## 7. Reliability

- polling is idempotent;
- source checkpoints are persisted;
- alert uniqueness is enforced in SQLite;
- failed sends remain retryable with bounded retries;
- a source error does not fail the entire cycle;
- launchd restarts future cycles automatically;
- every cycle writes counts, duration, lag, and errors.

## 8. Deferred Architecture

### TrendRadar / Docker

Current Colima VM is unhealthy. Repair is deferred until TrendRadar adds proven value over native polling.

### Browser/X resolver

Background Chrome automation is offline. It is not repaired merely to start the POC. It becomes P0 only if target discovery time is the measured bottleneck.

### Model scoring

`mlx-lm` is installed, but no model route is required or verified. Model scoring is added only if deterministic precision/recall is insufficient.

### Web UI

Deferred until CLI/alert workflow exceeds the operator time budget or produces data-entry quality problems.

### OPC

MomentGrid remains a possible external delivery/governance control plane. It is not part of the MVP runtime or a prerequisite for business validation. If reconnected, only high-level implementation/evidence events cross the boundary.

## 9. Paid X Boundary

No component in this architecture may create a chargeable X read/stream or publish automatically. The separate X API pilot remains blocked behind its existing exact budget gate.
