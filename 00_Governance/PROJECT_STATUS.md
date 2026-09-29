# Project Status

## Status Timestamp

2026-09-16

## Canonical Authority

- `PROJECT_SPEC.md` v3.8
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

## Acquisition Pool Batch 2 / Adaptive Cadence — 2026-09-16

- Direct-X creator configuration expanded to 90 total profiles / 81 enabled profiles.
- Batch 2 adds Boris Cherny, Charlie Hills, Ado, 老鬼, 泊舟, Claude, OpenAI, Anthropic, Cognition, Cursor, Google DeepMind, Hugging Face, and Vercel.
- Cadence was rebalanced from an overloaded 26.9 requested polls/min before Batch 2 to 18.83 requested polls/min after expansion, below the 24 polls/min theoretical stagger cap.
- Configured cadence distribution: 1min×1, 2min×15, 4min×14, 6min×11, 8min×40.
- Actual Reply outcome feedback now adapts effective cadence: +2 -> <=2min, +1 -> <=3min, negative mature evidence -> >=8min.
- Collector bootstrap now defaults `CHINA_TECH_HTTP_PROXY=http://127.0.0.1:7890` when not explicitly supplied, preventing LaunchAgent replacement from silently falling back to unreachable direct X access.

## Reply Surface Acquisition — 2026-09-16

- Direct-X signals now persist public direct-reply/quote competition when available.
- New Reply Surface Score rewards high parent reach per existing reply and penalizes saturated threads.
- New Reply Acquisition Score combines Distribution + Reply Surface + conservative Creator Feedback and is now the first ranking dimension among comparable verified-X opportunities.
- Missing public reply counts remain unknown/neutral instead of being treated as zero replies.
- Manual and automatically reconciled published Replies both snapshot parent views/replies/quotes/views-per-reply/surface score for later outcome learning.

## Canonical Runtime Database — 2026-09-16

- The only production SQLite database is `/Users/jh/services/china-tech-x-radar/runtime/china-tech-x.db`.
- The development repository runtime path is a local symlink to the same database; it must not become a second live state store.
- Production launcher scripts now fail closed if a local environment override points `CHINA_TECH_RADAR_DB` anywhere else.
- Reply outcome formula reports now include `reply_surface_bucket` (`OPEN` / `MODERATE` / `CROWDED` / `UNKNOWN`) so future mature samples can test whether open reply surfaces actually increase Kenny impressions.

## 2026-09-20 operational correction (authoritative current policy)

Policy v3.8 supersedes earlier language/cadence/Surface/instant-snapshot claims. Follow the current PROJECT_SPEC sections 2,4,27,28,31–33.

Audit: Sep16–20 follower snapshots 27->30. 84 sent packages, of which 59 were sent 00–08 Beijing; 69 Replies, of which 54 were sent in that overnight window. This is recommendation timing, not complete publishing/click analytics. 7/81 observed creators were predominantly Chinese. The previous outcome scheduler starved newer actions; their early 1–12 view snapshots were not mature results. Exact URLs were re-read: two MaxForAI Replies had 492 and 502 views, one SemiAnalysis Reply 801. These remain view counts, not unique people or attributable followers.

Implemented: Chinese acquisition / global reference separation; 08–22 quiet gate before drafting and sending, including P0; daypart budget reservation without increasing/resetting allowance; preflight before model use; provider backoff; observed-outcome fairness and maturity; original URL reconciliation; timestamped pre-publication snapshots; bounded Surface contribution; ASCII-token boundaries within Chinese text. No X post, Reply, follow, profile edit or deletion is automated.

Deployment evidence and audit data live in `00_Governance/evidence/2026-09-20-growth-audit/`. Code/tests passing does not demonstrate improved follower growth; evaluate subsequent mature outcomes.


## 2026-09-21 creator/routing correction

- SPEC v3.9: Chinese creator coverage target 25 core + 20 exploration; expansion is evidence-gated, not list-filling.
- Reply distribution hard gate reduced from 6 to 4 with 300-view floor; distribution remains ranking evidence.
- Creator 24h / 3-per-week constraints converted to soft ranking penalties; hard safety is 6h / 5-per-week.
- Chinese direct-X material older than the 180-minute Reply window can route to Chinese ORIGINAL consideration until 12h.
- Initial exploration additions: @chenchengpro, @meathill1, @AxtonLiu. Only @chenchengpro currently has strong recent reach evidence, so all enter at exploration/low cadence except future outcome-based promotion.
- Profile is already aligned; pinned-post topic awaits owner selection.


## 2026-09-27 acquisition/runtime repair and measured iteration

- X public profile SSR changed from the prior client:Tweet cache-key shape to TimelineTweet result blocks. Production parser now supports both forms and fails closed when a 200 response contains no parseable posts.
- Quote-post outcome parsing now anchors the outer tweet by status ID + author and excludes nested quoted-tweet metrics. Recent public outcomes were refreshed after this repair.
- Clean Sep20+ evidence: Reply median 131 impressions (7 measured, max 2,019); original median 35 (9 measured, max 70). Reply is the current cold-start distribution lane; originals remain profile-conversion / owned-evidence assets.
- Creator feedback now supports a conservative two-mature-sample provisional prior only when both samples clear a strong acquisition floor; a single breakout cannot change ranking. @vista8 currently qualifies (+1 provisional; 2 samples, median 1,811.5).
- Operator adoption is recorded as a usability/tie-break signal, not follower attribution.
- Classifier and Editorial now share one AI-building scope. Generic macro/politics/business candidates are kept as observations (P2) instead of entering realtime editorial merely because they mention AI.
- Chinese creator discovery remains evidence-gated. Sep27 added @arvin17x, @AI_Jasonyu, and @yanhua1010 to exploration, bringing the enabled Chinese pool to 18 (12 acquisition + 6 exploration).
- Subject grounding no longer requires brittle contiguous-string matching; named products/projects must still be recognizable in standalone copy.


## 2026-09-28 editorial outage repair

- Sep 28 produced 908 signals and 54 current P0/P1 candidates, but zero notifications because the configured Codex binary path had disappeared after a Codex installation/update.
- Root cause: config still pointed at /Users/jh/.codex/plugins/.plugin-appserver/codex; current Codex is available at /opt/homebrew/bin/codex (codex-cli 0.157.1).
- Production now resolves Codex through configured path, CHINA_TECH_CODEX_PATH, PATH, Homebrew/local standard locations, and the legacy plugin path.
- Failed model calls remain auditable but no longer consume daily call/token budget. The 80 failed Gate attempts from Sep 28 therefore do not block later valid work.
- Missing binary / provider infrastructure failures now defer with provider backoff instead of permanently becoming EDITORIAL_ERROR on the first attempt.
- Live health check with gpt-5.6-luna succeeded after the repair.
- Because the repair completed after the 22:00 Beijing notification cutoff, no old packet was force-sent. Only four still-valid outage candidates were restored for the Sep 29 08:00 window; stale failures remain audit history.


## 2026-09-29 launchd Node runtime repair

- Sep 29 morning still had zero delivered signals despite the Sep 28 Codex-path repair. The Homebrew Codex entrypoint is a Node script with shebang /usr/bin/env node, while the launchd job had an empty/minimal PATH.
- Interactive shell health checks therefore passed, but the background Editorial worker failed with: codex_gate_failed: env: node: No such file or directory.
- Production now prepends Homebrew/system binary paths in both run_editorial.sh and the child Codex process environment, so codex and node are resolvable under launchd.
- Node-runtime-missing failures are classified as provider/infrastructure failures and deferred with backoff instead of permanently becoming EDITORIAL_ERROR.
- Existing failed model calls remain audit records but do not consume budget. Sep 29 budget view correctly excludes the 64 failed Gate attempts.
- Production proof: alert 2069 was successfully sent to Feishu at 2026-09-29T02:58:54Z with a valid Feishu receipt after the repair.
