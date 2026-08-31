# Project Status

## Status Timestamp

2026-08-31

## Current Phase

`BUSINESS_VALIDATION_FIRST / SHADOW_TEST_DAY_1_RUNNING / NATIVE_MVP_LIVE`

The prior `EXECUTION_BLOCKED` state caused by MomentGrid Stability Gate and external-pack intake is superseded by CP-002. OPC is no longer a prerequisite for the China Tech business experiment.

## Current Objective

Run the live signal -> Feishu alert -> human X reply -> outcome evidence loop, review business KPI every day, and use Day 3 / 7 / 10 / 15 / 30 gates to decide whether to continue, correct, or change direction.

## Business Baseline

Latest Eden-connected provisional snapshot available before this correction:

- X account: `@KennyChinaTech`
- Followers: 4
- Tracked posts: 15
- Views: 396
- Likes: 2
- Comments: 0
- Shares: 0
- Total engagements: 2

Eden previously reported incomplete imports and Analytics inconsistencies, so this is a weak baseline. Native X-visible outcomes should be recorded during the experiment whenever available.

## Mac mini Fact Audit Summary

| Capability | Verified state | MVP decision |
|---|---|---|
| MacDeveloperBridge MCP | Running, full-access bridge available, launchd autostart present | Use for direct implementation/inspection when needed |
| Git / GitHub CLI | Available; GitHub account authenticated | Use |
| Python | 3.14.7 and 3.12 available; `uv` available | Use native Python |
| Node / pnpm | Node 22.23.1; pnpm 10.33.2 | Available but not required |
| SQLite | Available locally | Use |
| launchd | Available and already used by multiple services | Use for 5-minute polling |
| cloudflared | Installed; MCP tunnel running | Keep existing; not required in signal path |
| Docker / Colima | Installed; current Colima VM fails to start | Do not repair for MVP |
| TrendRadar | Installed; data exists through 2026-08-30; current source set is mostly Vietnam/Laos/general; no active launchd job after restart | Optional later; do not block MVP |
| Horizon | Not found | Ignore for MVP |
| Feishu | App ID/secret references exist; receive target not found/verified | Preferred alert path after receive target smoke test |
| Existing notification worker | Broken path and configured `dry-run` | Do not reuse as-is |
| Background Chrome automation | Offline | Do not block MVP; direct X resolver deferred |
| GitHub Actions runner | Repo-scoped runner exists for `arbitrage-os` | Do not reuse/assume |
| MLX / mlx-lm | Installed; no China Tech model route verified | Do not use in MVP |
| MomentGrid OPC | Dispatcher running on Mac | Optional; not an MVP dependency |

Detailed evidence: `artifacts/fact-audit/MAC_MINI_FACT_AUDIT.md`.

## Active Experiment

### EXP-001 — Zero-New-Spend Business Validation Shadow Test

Status: `DAY_1_RUNNING`

Shadow Test start: `2026-08-31T09:25:41.405504Z`.

First production cycle: 5/5 enabled sources succeeded, 71 signals were accepted, 3 recent P1 bootstrap opportunities were delivered to the real Feishu operator channel, and no source error occurred.

Production service: `/Users/jh/services/china-tech-x-radar`.

launchd:

- `com.creatiny.china-tech-x-radar` — 5-minute polling;
- `com.creatiny.china-tech-x-daily-review` — daily KPI review at 22:30 local time.

KPI authority: `00_Governance/OPERATING_KPI.md`.

The seven-day clock starts only after:

1. at least one live free source completes end-to-end ingestion;
2. exact dedupe works across repeated polls;
3. a real mobile-capable alert reaches the operator;
4. the operator decision/outcome ledger can be written;
5. paid-X and auto-publish guards are confirmed.

A web inbox, OPC, Docker, model scoring, Horizon, and direct X API access are not entry criteria.

## Active Pack

`03_Packs/PACK-CHINA-TECH-X-RADAR-001.md` v1.1 — `APPROVED / ACTIVE / MVP-FIRST`

The existing X API pilot remains `BLOCKED` with authorized spend `$0` and chargeable calls `0`.

## Current Known Gaps

1. Direct X target-post discovery remains human-assisted; the first three alerts include live X search links, and target-search time must now be measured.
2. Operator decisions and X outcome metrics have not yet been entered for Day 1; this is the next business evidence dependency.
3. Source coverage is intentionally narrow and must expand only when a daily review records a specific missed event/source class.
4. TrendRadar/Colima remain deferred and non-blocking.
5. The active deterministic rule set will be tuned from false-positive/miss evidence, not from feature ambition.

## Next Executable Sequence

1. Keep the 5-minute native runtime live and observe source/alert health.
2. For each delivered P0/P1, record `worth_reviewing`, direct X target URL when found, target-search minutes, and posted/skipped outcome.
3. Record impressions/engagement for published actions and a daily follower/profile snapshot when available.
4. Generate the daily KPI review; GREEN continues the direction, AMBER/RED diagnoses the first broken funnel stage before any tool expansion.
5. Evaluate Day 3, 7, 10, 15, and 30 against `OPERATING_KPI.md`.
6. Admit TrendRadar, model scoring, browser/X-native target discovery, UI, or OPC only when a KPI review names the specific bottleneck they solve.

## Stop Gates

The current MVP stops for human input only when it needs:

- a requirement or architecture boundary change;
- paid spend or a chargeable API;
- automatic publishing authority;
- a missing account secret/receiver identity that cannot be derived safely;
- a destructive/irreversible external action;
- a material platform-policy ambiguity.

MomentGrid/OPC availability is explicitly not a stop gate for the business experiment.

## 2026-08-31 Feishu Delivery Correction

User-visible delivery invalidated the earlier Feishu assumption: the operator reported receiving none of the three messages marked `SENT` by the first runtime cycle.

Root cause evidence:

- the Mac contains at least two distinct Feishu application credential sets;
- the first China Tech sender used an `open_id` from the approval-spike application;
- another established daily-report path uses a different application and a group `chat_id`;
- Feishu `open_id` values are application-scoped; attempting the report-leader `open_id` with the approval-spike application returns `open_id cross app`;
- therefore HTTP/code=0 from the original sender proves API acceptance to some valid app-scoped recipient, not delivery to the intended operator.

Correction:

- the original three alert records are classified `MISROUTED` and must not count toward KPI;
- automated P0/P1 sending is paused while collection continues;
- local alert configuration must use one matched app-credential + recipient pair;
- a test has been sent through the established daily-report application + its historically verified group chat;
- the channel remains `DELIVERY_UNVERIFIED` until the human operator confirms seeing the test;
- only after human confirmation may `CHINA_TECH_ALERTS_ENABLED=1` be set and production alert sending resume.

This incident also changes the delivery acceptance contract: **API acceptance is not user delivery evidence**. Initial channel verification requires explicit human-visible confirmation.

## 2026-08-31 Money-First KPI Decision

The human owner changed the highest-level objective from account growth to **making money through X operations**.

Canonical consequence:

- X-attributable cash revenue is now the North Star;
- followers/impressions are leading indicators;
- Day 15 requires first cash (`>=¥500`, at least one payer);
- Day 30 target requires at least 2 paying customers and `>=¥2,000` cumulative X-attributable revenue;
- direct China Tech research/intelligence monetization is P0; X-native creator payout is a later parallel track;
- reply acquisition and original-content distribution must be measured separately because current X Original Content Rewards excludes reply impressions from its qualified-impression eligibility threshold.

## 2026-08-31 Personal Feishu Routing / Shadow Clock

The operator confirmed the group-chat test was visible but explicitly requires China Tech alerts to be delivered only to the operator personally.

Current state:

- group delivery is not an authorized production alert destination;
- a matched Feishu application + `REPORT_DEFAULT_LEADER_OPEN_ID` personal route has been tested with provider API acceptance;
- production local config now points only to that personal `open_id` with the matching application;
- `CHINA_TECH_ALERTS_ENABLED=0` remains in effect until the operator explicitly confirms seeing the personal smoke message;
- collection continues while outbound China Tech alerts remain paused;
- the prior three misrouted records remain excluded from KPI;
- the Shadow Test clock has been cleared/paused and will restart only after personal delivery is human-verified.

Status: `COLLECTION_LIVE / PERSONAL_DELIVERY_UNVERIFIED / SHADOW_CLOCK_PAUSED / MONEY_FIRST_KPI_ACTIVE`.

## 2026-08-31 Audience-First Commercial Strategy Correction

The human owner rejected premature money-first service monetization and clarified the intended business sequence:

1. obtain a large, relevant China Tech follower base;
2. convert follower scale and authority into commercial collaboration and other audience monetization;
3. treat direct X platform payouts as one downstream revenue stream, not the sole business.

`OPERATING_KPI.md` v3.0 supersedes the earlier money-first Day-15/Day-30 cash gates.

The personal Feishu route has now been explicitly confirmed by the intended human recipient. Production alerts are enabled for personal Feishu only; group chat is prohibited. The Shadow Test clock restarts from the verified personal-delivery activation on 2026-08-31.

## 2026-08-31 Growth Formula Discovery Activation

The runtime now records the variables required to discover a repeatable follower-growth formula rather than relying on anecdotal post review.

Formula authority: `00_Governance/GROWTH_FORMULA.md`.

Tracked per action: event type, target account/size, target-post age, visible target impressions at reply time, reply/original angle, hook, media/link treatment, and later distribution/engagement outcomes. Daily follower snapshots are evaluated as cohorts so overlapping actions are not falsely assigned individual follower causality.

Evidence standard: one breakout is anecdotal; >=3 repeated wins form a candidate formula; >=5 repeated wins plus follower-positive cohorts justify scaling the combination.
