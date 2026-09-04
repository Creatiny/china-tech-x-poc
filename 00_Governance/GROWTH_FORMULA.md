# China Tech X Growth Formula Discovery — v1.0

## Objective

Find a repeatable follower-growth formula for `@KennyChinaTech`.

```text
EVENT × TARGET ACCOUNT/SIZE × TARGET POST AGE
× ANGLE × FORMAT × TIMING
→ IMPRESSIONS/ENGAGEMENT → PROFILE INTEREST → FOLLOWERS
```

## Record Per Action

For every published reply/original record:

- content group: `A_NEWS_FACT` or `B_OPINION_VALUE`;
- topic and event type;
- target account and approximate follower count;
- target post age when we reply and visible target impressions if available;
- angle: fact add, China context, comparison, data point, contrarian, global implication, technical explanation, question, other;
- hook: breaking, number, contrast, why-it-matters, thesis, question, none;
- media: none/image/video/chart;
- external-link use;
- later impressions, engagements, likes, replies, reposts, quotes, bookmarks and profile visits when available;
- daily total follower snapshots.

The primary A/B comparison is followers, profile visits, bookmarks, meaningful replies, and qualified business interest per 1,000 impressions. Total impressions are a distribution measure, not the sole definition of content value.

## Buckets

Target age: `0–10m`, `10–30m`, `30–60m`, `1–3h`, `3–6h`, `>6h`.

Target account size: `<10K`, `10K–100K`, `100K–1M`, `>=1M`.

This directly tests whether the winning formula is “largest account” or instead “strong topical fit + early reply + specific angle”.

## Evidence Standard

- 1 sample: anecdote;
- 2: hypothesis;
- >=3 repeated wins: candidate formula;
- >=5 repeated wins plus follower-positive days: strong evidence worth scaling.

Never declare a formula from one breakout post. Follower changes are assessed at daily/cohort level when actions overlap; they are not falsely attributed to one action.

## Formula Report

Run:

```bash
china-tech-x-radar formula --min-samples 2
```

The report compares action type, event type, topic, target account, target size, target-age bucket, angle, hook, media, link usage, and repeated multi-variable combinations.

Daily KPI answers **whether we grew**. Formula analysis answers **what caused repeatable growth and what to repeat next**.

## Initial Hypotheses — Ordered by Business Value

The first observations prioritize these hypotheses without intentionally delaying a good action just to fill a test bucket:

1. **H1 — Timing:** useful replies published within 30 minutes of the target post outperform replies after 60 minutes.
2. **H2 — Target size/competition:** highly relevant `100K–1M` target accounts may outperform `>=1M` mega accounts because competition in the reply surface is lower while reach is still large.
3. **H3 — China-specific value:** `CHINA_CONTEXT`, `GLOBAL_IMPLICATION`, and `COMPARISON` angles outperform generic fact restatement.
4. **H4 — Topic concentration:** China AI/model, semiconductor/AI infrastructure, and robotics events may produce stronger follower conversion than generic China business news.
5. **H5 — Native originals:** link-free native original posts with a clear thesis/number/contrast outperform link-first news summaries.

## Sample Phases

### First 10 published actions

Instrumentation and baseline. Do not optimize aggressively from one result.

### 10–20 actions

Look for repeated directional differences by target age, target tier, and angle. A 2-sample pattern is only a hypothesis.

### 20–30 actions

Bias toward combinations that have already produced >=3 repeated distribution wins, while keeping enough variation to test alternatives.

### After >=5 repeated wins

If a combination has >=5 samples, repeatedly stronger distribution, and appears on follower-positive days, promote it to `CANDIDATE_GROWTH_FORMULA` and increase its share of future opportunities.

Never sacrifice a clearly superior real-time business opportunity just to make experiment groups numerically balanced.
