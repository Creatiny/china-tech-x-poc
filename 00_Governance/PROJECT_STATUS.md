# Project Status

## Status Timestamp

2026-09-16

## Canonical Authority

- `PROJECT_SPEC.md` v3.5
- `EXECUTION_PLAN.md` v2.0
- `00_Governance/OPERATING_KPI.md` v4.0

## Current Strategy

`AI_PRODUCTIVITY_AUDIENCE / VIEWPOINT_FIRST / CHINESE_ORIGINALS / PARENT_LANGUAGE_REPLIES`

## Current Audience Promise

People who care about AI technology and how AI becomes real productivity.

## What Changed on 2026-09-09

Superseded:

- English-language China-Tech-news identity;
- China entity as universal topic gate;
- Stage-A 3–5 replies/day target;
- ~1 original/day target;
- reply/original milestone counts;
- routine Article cadence;
- reply impressions as a success proxy.

Active:

- news is material, viewpoint is product;
- `WHAT_I_BELIEVE / WHAT_I_LEARNED / WHAT_CHANGES`;
- originals are Chinese;
- replies follow parent language;
- continuous POST + REPLY opportunity discovery remains required;
- China sources remain a differentiation advantage;
- global AI/agent/coding/productivity signals are now in scope;
- KPI funnel is STOP -> ENGAGE -> PROFILE -> FOLLOW REASON -> FOLLOW.

## Current Runtime

- repository: `Creatiny/china-tech-x-poc`;
- production service: `/Users/jh/services/china-tech-x-radar`;
- Python + SQLite + launchd;
- personal Feishu only;
- manual X publishing;
- no paid X API;
- bounded local ChatGPT/Codex editorial enrichment.

## Current Known Evidence

Recent account analysis showed replies can obtain materially more impressions than originals, but high reply impressions frequently produced almost no engagement/follower conversion. This is treated as evidence that distribution exists while follow reason/identity conversion is weak.

## Current Execution Priority

1. align radar/editorial prompts with v3.1;
2. broaden signal discovery beyond China-only gating;
3. continue finding live reply targets under the new value gate;
4. build owned Chinese viewpoint/practice content;
5. measure conversion, not output count.

## Distribution Opportunity Engine — 2026-09-15

- Direct X candidates now persist distribution score, observed views, views/minute, and engagement rate.
- Relevance remains the first gate; virality cannot rescue off-positioning content.
- Fast-rising verified X targets are processed before flat candidates at the same editorial priority.
- A short early-discovery grace window preserves the ability to reply before a strong post fully breaks out.
- Breakout distribution can promote a qualifying direct-X target to P0; editorial value and human voice gates still apply.
- Creator diversity/cooldown remains active for ordinary P1 replies.

## Closed-Loop Outcome Feedback — 2026-09-16

- Published Reply/Post public metrics are now automatically captured from X.
- Public follower count is automatically snapshotted; profile visits remain null unless first-party data is provided.
- Creator outcome feedback activates only after sufficient samples and is a small ranking prior.
- Multi-day snapshot gaps and multi-action days are explicitly blocked from false follower attribution.

- X public-source fetch concurrency is capped at 4 after production evidence showed proxy TLS/read timeouts under an 8-worker burst; stability outranks nominal poll speed.
- To prevent synchronized proxy bursts, at most 6 direct-X profiles are fetched per cycle; overdue profiles roll into subsequent 15-second cycles, oldest-success first.

## Reply-Acquisition Expansion — 2026-09-16

- Direct-X monitored pool expanded from 58 to 77 creators; enabled pool from 49 to 68.
- New admission is evidence-led: actual Reply outcomes first, then current parent-post distribution, audience adjacency, and technical fit.
- High-priority new observation slots include Zephyr, SemiAnalysis, Max For AI, Matt Pocock, Matt Shumer, 歸藏, Damnang, Tencent AI, 花叔, AK, AI Engineer, Georgios Konstantopoulos, Ilir Aliu, Tanay Jaipuria, Pietro Schirano, The Humanoid Hub, swyx, Jeffrey Emanuel, and 刘小排.
- New creators are observation targets only; the live post still has to pass all relevance/distribution/editorial gates.
- Formula reports now include a `creator_acquisition` leaderboard combining parent reach and Kenny's real Reply outcomes.

## Live Distribution Refresh — 2026-09-16

- Existing direct-X signals now refresh views, velocity, engagement, distribution score and classification on every observation instead of freezing the first sample.
- Quiet posts can graduate into P1/P0 when they begin to break out; only signals without a prior editorial decision create a new alert.
- Pending live opportunities expire automatically when the target ages/drops below qualification.
- AI-product vocabulary now explicitly covers OpenAI, Anthropic, Claude, Codex, AgentKit, Cursor, Devin, Hermes, harnesses and subagents; highly curated creators may add narrow source-specific vocabulary such as Matt Pocock's `/retro`/lint/CI workflow terms and Matt Shumer's Astra/Fable terms.

## Realtime Worker Isolation — 2026-09-16

- Realtime Collector and Editorial Worker are now independent launchd loops.
- Collector runs every 15 seconds and never waits for model/editorial work.
- Editorial Worker consumes the SQLite PENDING queue independently, atomically claims items, recovers stale claims, and revalidates the live signal before Feishu send.
- This removes model/search latency as a blocker for high-velocity Reply opportunity discovery.
