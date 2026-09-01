# China Tech X POC — Execution Plan v1.2

## Authority

Status: `APPROVED / ACTIVE`

Top-level strategy authority: `PROJECT_SPEC.md` v2.2.

This file defines **how the current spec is executed**. If execution here conflicts with the strategy/spec, `PROJECT_SPEC.md` wins and this plan must be corrected.

## 1. Current Stage

`STAGE_A / 4_TO_100_FOLLOWERS / REPLY_LED_COLD_START`

Valid experiment start: `2026-08-31 20:27:44 Asia/Shanghai`.

Baseline: `4 followers`.

Primary Day-30 target: `>=100 relevant followers`; stretch: `>=200`.

## 2. Division of Work

### Mac mini runtime — automatic

Every ~5 minutes:

1. poll active free/traceable China Tech sources;
2. normalize and exact-dedupe;
3. classify relevance/freshness;
4. identify P0/P1 opportunities;
5. send qualified publishing signals to **personal Feishu only**;
6. persist source/signal/alert evidence;
7. keep operating if one source fails.

### ChatGPT — analysis/operator support

For qualified opportunities:

1. verify the event/source when needed;
2. choose whether the opportunity is better for `REPLY`, `ORIGINAL`, or `SKIP`;
3. identify the best available X target when possible;
4. draft natural English copy with a differentiated China-specific angle;
5. recommend image/link treatment;
6. record the final published URL and formula variables once supplied;
7. track outcomes and daily formula evidence;
8. diagnose the first broken growth stage.

### Human operator — manual authority

Only the human:

1. receives personal Feishu publishing signals;
2. opens/selects the X target;
3. performs final judgment/edit;
4. manually publishes reply/original;
5. returns the published X URL to ChatGPT when practical.

No automatic X publishing is authorized.

## 3. Stage-A Daily Operating Target

When qualified opportunities exist:

- **3–5 strategic replies/day**;
- **~1 differentiated original post on active days**;
- replies should favor early, relevant conversations already attracting attention;
- no publishing simply to hit a quota if quality is insufficient.

Target human time: approximately `<=30 minutes/day` median once the workflow stabilizes.

## 4. Signal-to-Publish Workflow

```text
SOURCE EVENT
    ↓
5-min radar
    ↓
P0/P1 qualification
    ↓
personal Feishu
    ↓
REPLY / ORIGINAL / SKIP decision
    ↓
human publish
    ↓
published X URL
    ↓
formula metadata + outcome snapshots
    ↓
daily KPI/formula review
```

### Feishu signal must contain

- what happened;
- why it matters;
- freshness;
- source URL;
- direct X target if known, otherwise a live-search route;
- suggested action: reply/original/skip;
- suggested angle;
- urgency/expiry.

## 5. Formula Data Captured

For each published action, record as available:

- event type/topic;
- `REPLY` or `ORIGINAL`;
- target account;
- target follower count/tier;
- target-post age at reply;
- target impressions at reply time;
- angle;
- hook;
- media treatment;
- external-link usage;
- impressions/engagement later;
- daily account followers/profile visits when available.

Formula authority: `00_Governance/GROWTH_FORMULA.md`.

## 6. First Formula Search Sequence

### Samples 1–10 — baseline

Goal: instrumentation quality and natural variance.

Do not chase a single winner. Collect clean metadata while prioritizing the best business opportunity.

Primary observations:

- `<30m` vs later replies;
- `100K–1M` vs `>=1M` target accounts;
- China-context/global-implication/comparison vs generic angles;
- AI/chips/robotics topic performance;
- native/no-link vs link-containing originals.

### Samples 10–20 — hypothesis formation

Identify directional differences. Two wins are still only a hypothesis.

Bias nothing strongly unless quality is obvious.

### Samples 20–30 — candidate formula

If one combination has >=3 repeated wins, label it `CANDIDATE_GROWTH_FORMULA` and modestly increase its share of future opportunities.

### >=5 repeated wins + follower-positive cohorts

Promote to `SCALE_BIAS`:

- prioritize matching events;
- prioritize proven target tier/accounts;
- prefer proven timing window;
- default to the proven angle/treatment unless the event clearly requires another approach.

Continue retaining some alternative samples so the formula can be falsified.

## 7. Daily Review

Every day review:

1. follower count and delta;
2. replies/originals completed;
3. action impressions and repeated reach thresholds;
4. source misses and notification latency;
5. strongest/weakest target/timing/angle combinations;
6. formula sample count/status;
7. first broken growth stage;
8. one adjustment for the next day.

Allowed response to a miss:

- **one growth/business variable change**;
- optionally **one measurement repair**.

Not allowed by default:

- adding infrastructure because KPI is bad;
- changing multiple content variables at once;
- broadening sources without a concrete miss;
- lowering content quality to create samples.

## 8. Milestone Gates

### Day 3

Target: `>=8 followers`.

If missed, inspect in order:

1. enough quality replies/originals?
2. replies early enough?
3. targets have relevant attention?
4. impressions above Day-0 baseline?
5. impressions exist but no follows -> profile/positioning conversion problem.

### Day 7

Target: `>=15 followers` plus repeated distribution evidence.

Need first meaningful target/timing/angle hypotheses.

### Day 10

Target: `>=25 followers`.

Need evidence that growth is not one isolated post.

### Day 15

Target: `>=40 followers`.

If volume/distribution are healthy but followers are weak, strategy/positioning/target selection becomes the priority review—not infrastructure.

### Day 30

Minimum: `>=100 followers`; stretch `>=200`.

Need repeated distribution and a candidate/proven growth formula or a clearly falsified hypothesis with a specific next bottleneck.

## 9. Source Expansion Rule

A source may be added/tuned only when one of these occurs:

- a material China Tech event was missed;
- an event arrived materially too late;
- active source reliability degrades;
- formula evidence identifies a topic/target area with insufficient discovery coverage.

Example already applied: Nexperia/Wingtech exposed a Reuters coverage miss, so a focused Reuters China Tech path was added. This does **not** authorize generic news-source expansion.

## 10. Tool Admission Rule

OPC, TrendRadar repair, browser automation, model scoring, Web UI, local LLMs, Eden expansion, or paid X APIs are admitted only if daily/milestone evidence names the bottleneck they solve.

The default response to weak follower growth is to improve:

`signal → target → timing → angle → distribution → profile conversion`.

## 11. Commercialization Transition

The current Stage-A plan does not optimize revenue.

Readiness checkpoints:

- 500 followers: monitor aligned inbound and X-native eligibility progress;
- 1,000: prepare media kit;
- 2,000: actively test highly aligned brand/sponsor/affiliate collaborations;
- 10,000+: target a repeatable commercial partnership pipeline.

If a high-quality inbound commercial opportunity appears earlier, it can be evaluated without changing the primary growth strategy.

## 12. Current Immediate Actions

1. keep six-source production radar healthy;
2. personal Feishu remains the only realtime signal channel;
3. accumulate the first 10 clean formula samples;
4. prioritize quality early replies because the account is still at Stage A;
5. continue originals when a material event supports a differentiated thesis;
6. capture outcomes and follower snapshots;
7. perform daily review and change no more than one growth variable;
8. evaluate Day-3 KPI first, then Day 7/10/15/30.

## 13. Feishu Publish-Packet Execution

Do not send raw classifier output to the operator.

For a new qualified candidate:

1. deterministic rules remove obvious noise;
2. generic/ambiguous candidates run a low-reasoning editorial gate without web search;
3. obvious high-quality tech candidates or gate `PASS` candidates run final editorial enrichment with web verification/search as needed;
4. final model selects `REPLY`, `POST`, or `SKIP`;
5. `SKIP` is stored silently;
6. `REPLY` requires a verified direct X status target and receives final paste-ready reply copy;
7. `POST` receives final native-first copy, source kept separate, and an original editorial card when the model says a visual adds value;
8. only `POST/REPLY` packets go to personal Feishu.

Current quota-protection defaults:

- low reasoning;
- maximum 12 gate calls/day;
- maximum 10 final/search calls/day;
- maximum 240,000 logged model tokens/day as an internal proxy stop;
- no OpenAI Platform API key or paid X API is introduced.

If enrichment budget is exhausted, the item is held/error-recorded rather than degrading back to a raw Feishu signal.

## 14. P0/P1 Feishu Handling

Feishu priority is operator-visible in the first line.

- `P0`: immediate publish packet after editorial validation; treat before P1.
- `P1 REPLY`: only when a verified direct X target exists and the configured score/confidence threshold passes; maximum 4/day.
- `P1 POST`: only when score/confidence threshold passes; maximum 1/day.
- excess qualified P1 candidates are held silently for analysis and are not pushed to the operator.

The goal is to send the operator an **action queue**, not a candidate queue. The operator should never need to infer whether a package is P0 or P1.

Editorial quota enforcement uses atomic reservations. Current policy defaults: max 8 gate calls/day, max 5 final/search calls/day, 180K token-proxy/day, with 6K/30K reservation estimates for gate/final calls.
