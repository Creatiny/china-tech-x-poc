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

### Day 30 — growth-mechanism validation

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

Original-content target:

- at least `8` differentiated original posts during the 30-day window, unless the daily reviews document insufficient qualified signals;
- original-post results must be reported separately from reply results;
- at least one original post should materially exceed the Day-0 average-view baseline.

Commercial-intent target:

- at least `1` measurable monetization-intent signal: inbound collaboration, consulting/research inquiry, sponsor/partner interest, subscriber/lead intent, or another recorded willingness-to-pay/convert signal.

Day 30 can be classified:

- `GROWTH_MECHANISM_VALIDATED`: reply acquisition + original distribution + growth evidence pass;
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

## 9. Alert Delivery Evidence

A notification API returning HTTP 200 or provider `code=0` is `API_ACCEPTED`, not proof that the intended human received it.

For KPI purposes:

- messages sent before a recipient/channel has been human-confirmed are not counted as delivered opportunities;
- a new app/recipient pairing requires at least one explicit human-visible smoke confirmation;
- app-scoped identity types such as Feishu `open_id` must never be reused across different applications;
- misrouted messages are excluded from alert-count and latency KPI.

## 10. KPI Basis and Success Horizon — 2026-08-31 Calibration

### What the Day 3/7/10/15/30 KPI is

These are **POC falsification and learning gates**, not an industry promise that the account is "successful" by Day 30.

They are based on three evidence classes:

1. **Own-account baseline**: 4 followers, 15 tracked posts, 396 provisional tracked views, or about 26.4 views per tracked post. Early distribution thresholds are deliberately set as multiples of this weak baseline rather than generic large-account averages.
2. **Operating constraints**: <=30 minutes/day, <=10-minute live-source alert latency once warmed, and enough reviewed opportunities to diagnose the funnel rather than rely on a single lucky post.
3. **External platform reality**: X is a high-variance network where most posts receive low engagement, consistent participation matters over months, and current X native monetization increasingly rewards original content rather than reply-only reach.

Therefore Day 30 means **growth mechanism validated or falsified**, not "mature account achieved."

### External benchmark context

Current external research is used as context, not copied as a target for this tiny account:

- Buffer's 2026 benchmark reports X median engagement around the low-single-digit percentage range, with text posts leading and substantial Premium/non-Premium distribution differences.
- Buffer's consistency study found creators posting at least weekly for 20+ of 26 weeks earned materially more engagement per post than highly inconsistent creators; this supports a multi-month stabilization horizon.
- X is highly skewed: typical posts can remain small while occasional posts produce very large distribution, so one viral post cannot validate the system by itself.

### Current X native monetization constraint

As of 2026-08-31, X is retiring Creator Revenue Sharing and moving toward Original Content Rewards.

X's published Original Content Rewards eligibility currently requires, among other conditions:

- active eligible Premium subscription;
- at least **500 verified followers**;
- at least **500,000 Home Timeline impressions from verified users in the last 90 days**;
- **reply impressions are excluded** from that impressions threshold;
- active original content.

Implication: replies are a discovery/acquisition channel, but the account must develop an **original-content distribution engine** to become sustainably monetizable on X itself.

### Required two-track measurement

From Day 7 onward, reviews must separate:

**Reply acquisition track**

- target-post age;
- reply impressions and engagement;
- profile visits / follower conversion attributed when observable;
- target accounts and topics producing follows.

**Original distribution track**

- number of differentiated original posts;
- original-post impressions;
- median and max original-post impressions;
- verified-user/Home Timeline metrics when X exposes them;
- follower/profile conversion;
- recurring thesis/topic performance.

A strategy that produces reply impressions but no growth in original-post distribution is not sufficient for long-term success.

## 11. How Long Should Success Take?

Use staged definitions rather than one date:

### 0–30 days — mechanism validation

Question: can this account repeatedly earn distribution above its own baseline and convert some of that attention into relevant followers/profile interest?

This is the current experiment. Day 30 is a go/correct/stop decision, not mature success.

### 31–90 days — audience traction

If Day 30 is positive, the next 60 days should demonstrate that growth is repeatable across multiple topics and original posts, not dependent on one target account or viral event.

The exact Day-90 follower target must be set from the observed Day-30 conversion rate rather than invented in advance. Planning bands may be used, but actual Day-30 data is the authority.

### 3–6 months — credible niche account

A successful path should by then show:

- a repeatable source -> thesis -> original-post engine;
- multiple posts with materially larger reach than the Day-0 baseline;
- a meaningful base of relevant followers;
- recurring profile/follower conversion;
- at least early commercial-intent evidence if consulting/research/business monetization is part of the goal.

This is the first realistic horizon for saying the account is "operating successfully" rather than merely showing a promising POC.

### 6–12+ months — platform-scale monetization

X-native monetization eligibility is a much higher bar because 500 verified followers alone is insufficient; the 90-day qualified original-content impression threshold is also required. The timeline depends strongly on whether original posts begin producing thousands to tens of thousands of Home Timeline impressions.

Business monetization outside X's native payout programs may occur earlier with a smaller but high-value China Tech audience; this must be measured separately from X payout eligibility.

## 12. Day-30 Interpretation Bands

The existing `followers >=20` target is a **minimum direction signal**, not the definition of account success.

At Day 30:

- `<20 followers` plus weak distribution: growth mechanism has not been proven;
- `20–49 followers` with several above-baseline posts: early signal, but trajectory is still too slow for near-term X-native monetization;
- `50–99 followers` with repeatable original-post lift: strong cold-start evidence and a plausible multi-month path;
- `>=100 followers` with repeatable original-post lift: strong Month-1 traction; scale the proven topic/target patterns while protecting quality.

These bands are planning heuristics. They do not override actual follower quality, original-post reach, conversion, or commercial-intent evidence.
