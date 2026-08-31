# China Tech X Operating KPI — v1.0

## 1. Authority

- Status: `APPROVED / ACTIVE`
- Effective date: `2026-08-31`
- Governing principle: **business outcome is the highest priority**.
- Applies to: active 30-day China Tech X POC and `PACK-CHINA-TECH-X-RADAR-001`.

KPI exists to force fast learning, not to force low-quality publishing. A missed KPI triggers diagnosis of the first broken funnel stage before new infrastructure or broader automation is added.

## 2. Baseline

The provisional pre-test baseline is:

- followers: `4`;
- tracked posts: `15`;
- tracked views: `396`;
- provisional arithmetic average: `26.4 views / tracked post`.

Eden's historical import is incomplete, so this baseline is directional only. Native X-visible metrics recorded during the Shadow Test supersede it when available.

## 3. Business Funnel

Every daily review follows the same funnel:

```text
SOURCE COVERAGE
    -> SIGNAL LATENCY
    -> ALERT PRECISION
    -> X TARGET DISCOVERY
    -> HUMAN ACTION
    -> REPLY DISTRIBUTION
    -> PROFILE / FOLLOWER CONVERSION
    -> COMMERCIAL INTENT
```

Never optimize a downstream stage while an upstream stage is unmeasured or clearly broken.

## 4. Milestone KPI

### Day 3 — prove the loop can create a business signal

Process targets:

- runtime cycle success rate `>=95%`;
- median source-to-alert latency `<=15 minutes`;
- at least `6` delivered P0/P1 alerts;
- at least `50%` of reviewed alerts judged worth reviewing;
- at least `3` verified executable X reply opportunities;
- at least `3` published test actions when qualified opportunities exist.

Business signal — at least one:

- one published action reaches `>=50 impressions`; or
- net follower change `>=+1`; or
- cumulative profile visits `>=3`.

Decision:

- met: continue current direction;
- missed: diagnose the first broken funnel stage before adding sources/tools.

### Day 7 — prove timing/opportunity selection can beat the old baseline

Process targets:

- runtime success `>=97%`;
- median source-to-alert latency `<=10 minutes`;
- at least `14` delivered P0/P1 alerts;
- review-worth precision `>=70%`;
- at least `7` executable opportunities;
- at least `7` published test actions when qualified opportunities exist;
- median human operating time remains within `30 minutes/day` when recorded.

Business signal — at least one:

- one action reaches `>=100 impressions`; or
- net follower change `>=+2` (followers `>=6`); or
- cumulative profile visits `>=5`.

If process KPI passes but business KPI fails, do **not** build more platform. Diagnose target age/account quality, reply angle, account conversion, and content positioning first.

### Day 10 — prove the lift is repeatable rather than one lucky reply

Targets:

- runtime success `>=97%`;
- alert latency `<=10 minutes`;
- review-worth precision `>=70%`;
- at least `20` delivered P0/P1 alerts;
- at least `10` executable opportunities;
- at least `10` published test actions;
- median operating time `<=30 minutes/day`;
- distribution: at least `2` actions `>=100 impressions` **or** one action `>=300 impressions`;
- growth: net followers `>=+3` **or** cumulative profile visits `>=10`.

Both a distribution signal and a growth/profile signal are required to call Day 10 healthy.

### Day 15 — prove a repeatable growth mechanism is emerging

Targets:

- runtime success `>=98%`;
- alert latency `<=10 minutes`;
- review-worth precision `>=75%`;
- at least `30` delivered P0/P1 alerts;
- at least `15` executable opportunities;
- at least `15` published actions;
- median published-action impressions `>=50`;
- at least `3` actions `>=100 impressions` or a stronger distribution outlier;
- net follower growth `>=+6` (followers `>=10`);
- median operating time `<=30 minutes/day`.

If Day 15 misses both distribution and follower growth after at least two documented corrective iterations, the next review must explicitly consider whether source/target/content strategy or account positioning is wrong. Infrastructure expansion is not the default answer.

### Day 30 — business-direction validation

Operational targets:

- runtime success `>=98%`;
- alert latency `<=10 minutes`;
- review-worth precision `>=80%`;
- at least `60` delivered P0/P1 alerts;
- at least `30` executable reply opportunities;
- at least `25` published qualified actions;
- median operating time `<=30 minutes/day`.

Distribution and growth targets:

- median published-action impressions `>=100`;
- at least `5` actions `>=300 impressions`;
- at least `1` action `>=1,000 impressions`;
- followers `>=20` from the starting baseline of 4.

Commercial-intent target:

- at least `1` measurable monetization-intent signal: inbound collaboration, consulting/research inquiry, sponsor/partner interest, subscriber/lead intent, or another recorded willingness-to-pay/convert signal.

Day 30 can be classified:

- `BUSINESS_DIRECTION_VALIDATED`: distribution + growth + commercial-intent KPI pass;
- `DISTRIBUTION_VALIDATED_NOT_COMMERCIALIZED`: growth/distribution pass but no commercial intent;
- `AUDIENCE_SIGNAL_WEAK`: operating loop works but distribution/growth fails;
- `FUNNEL_NOT_VALIDATED`: upstream source/alert/target loop itself still fails.

## 5. Daily Review Rule

Every calendar day must produce a review even when nothing was published.

The review records:

- runtime/source health;
- delivered P0/P1 count and alert latency;
- reviewed/worth-reviewing count;
- executable target count and target-search time;
- published/skipped/false-positive/expired decisions;
- operator minutes;
- latest per-action impressions/engagement;
- daily follower/profile snapshot when available;
- current milestone progress;
- single primary bottleneck;
- no more than two corrective actions.

## 6. Corrective-Action Discipline

When a target is missed:

1. identify the first broken funnel stage;
2. state one falsifiable reason;
3. change at most **one business variable** before the next daily review;
4. one additional instrumentation fix is allowed if measurement is the blocker;
5. record what metric the change is expected to move;
6. review the effect the next day.

Do not simultaneously change sources, scoring, target strategy, voice, posting time, and architecture. That destroys causal evidence.

## 7. Bottleneck Mapping

| Failure | Default diagnosis before any new tool |
|---|---|
| Too few qualified alerts | source coverage / entity-topic rules |
| Alerts arrive late | source/poll latency |
| Many alerts are not worth seeing | alert precision |
| Good signals but no target post | X target discovery |
| Targets exist but not posted | operator friction / reply selection |
| Replies posted but impressions remain weak | target age/account quality / reply value / account distribution |
| Impressions improve but followers do not | profile positioning / conversion |
| Growth exists but no commercial signal by Day 30 | monetization offer/path missing |

## 8. Infrastructure Admission Rule

A new system is admitted only when a KPI review names the bottleneck it solves.

Examples:

- repair TrendRadar only for proven source-coverage gaps;
- add X-native/browser resolver only for proven target-discovery gaps;
- add LLM scoring only for proven alert-precision gaps;
- add web UI only for proven operator-friction/measurement gaps;
- reconnect OPC only for proven implementation/governance complexity.

Business KPI failure never automatically authorizes more infrastructure.
