# China Tech X POC — Canonical Project Spec v3.7

## 0. Authority

**Status:** `APPROVED / ACTIVE / SINGLE SOURCE OF TRUTH`  
**Effective:** `2026-09-16`

This file is the top-level product and operating authority for `Creatiny/china-tech-x-poc`.
If another repository document, old issue, old PR, conversation, historical change proposal, runtime comment, or old KPI conflicts with this file, **this file wins** unless the human owner explicitly approves a newer revision.

Historical files remain for auditability only. They do not control current execution.

## 1. Business Goal

Build `@KennyChinaTech` into a trusted X account for people who:

- care about AI technology;
- care more about what AI changes than about launch-news itself;
- want to turn AI into real productivity, products, better workflows, lower cost, or new business models.

The account is no longer operated as an English-language China-tech news account.

The operating sequence is:

```text
Useful viewpoint / real practice / consequential change
    -> right audience stops and reads
    -> trust + recognizable point of view
    -> profile interest
    -> relevant follows
    -> durable audience asset
```

**North Star:** relevant follower growth caused by a clear follow reason, not posting volume or raw impressions.

## 2. Audience and Positioning

### Audience

One coherent audience:

> People who follow AI technology and care about turning AI into real productivity.

Typical members include AI builders, developers, founders, product people, operators, investors, and serious AI users.

### Positioning

Internal positioning:

> **不报道 AI，判断 AI 正在改变什么。**

English shorthand:

> **Don’t report AI. Think about what AI changes.**

China technology remains an important source of differentiated evidence and first-hand context, but **China is no longer a hard boundary for topic selection**.

A China-related item is worth publishing only when it matters to the target audience. A global AI/agent/coding/productivity item may be worth publishing even when it has no China entity.

## 3. Content Product

News is raw material. **The product is Kenny's point of view.**

Every publishable item should fit at least one of these three buckets:

1. **WHAT I BELIEVE** — a clear judgment/thesis;
2. **WHAT I LEARNED** — a conclusion from real research, testing, building, or operating work;
3. **WHAT CHANGES** — a new development that materially changes cost, capability, workflow, product design, business model, or competitive dynamics.

A candidate that only answers “what happened?” is normally `SKIP`.

### So-What Test

For `WHAT CHANGES`, the content must answer at least one:

- What cost falls?
- What old workflow becomes obsolete?
- What previously impossible task becomes possible?
- What changes for builders/developers?
- What changes for founders/companies?
- What changes for individual productivity?
- What common interpretation is probably wrong or incomplete?

## 4. Language Policy

### Original content

**All original posts, threads, and X Articles are published in Chinese.**

This is a hard rule. Do not split the account into parallel Chinese and English original-content tracks.

### Replies

Reply language follows the parent post:

- Chinese parent post -> Chinese reply;
- English parent post -> English reply;
- other languages -> follow the parent language when practical, otherwise only reply when a natural high-quality response is possible.

X translation is treated as sufficient for cross-language discovery. Language is not used to split the target audience.

## 5. Editorial Priority

Priority order:

1. **Own viewpoint**;
2. **Real practice / learned insight**;
3. **Consequential new technology/change**;
4. ordinary news summary — normally skip.

The system should prefer one memorable judgment over ten generic news updates.

## 6. Reply Policy

Replies remain an acquisition/distribution channel, but are not a quota.

A reply is worth surfacing only when it adds at least one of:

1. first-hand / primary-source information;
2. a key number or factual correction;
3. a relevant corresponding case/comparison;
4. a real practice result or lesson.

Generic agreement, generic “deeper implication” commentary, praise, filler, and AI-style restatement are `SKIP`.

Repeated template structures should be avoided, especially:

- “真正重要的不是 X，而是 Y”;
- “The interesting part isn’t X. It’s Y.”;
- “The real shift isn’t X. It’s Y.”;
- “The biggest takeaway isn’t X. It’s Y.”

These are not forbidden as language, but repeated use is a quality failure.

## 7. Original Content Policy

An original post should normally contain:

- a clear thesis in Kenny's voice;
- evidence, a real case, or explicit reasoning;
- a useful consequence for the target audience;
- a reason to remember/follow the account for similar thinking later.

China-side evidence is a differentiation advantage, not a publishing requirement.

## 8. Article Policy

X Article is no longer a routine output target.

Preferred progression:

```text
idea / practice observation
 -> short post or reply test
 -> repeated audience interest / richer evidence
 -> thread or series
 -> Article only when the thesis deserves durable long-form treatment
```

No Article quota exists.

## 9. Publishing-Volume Policy

There is **no minimum daily post quota** and **no minimum daily reply quota**.

Reply notifications use a **rolling attention window**, not a hard all-day cutoff: P0 never consumes P1 capacity; P1 can send up to 3 qualified Reply packets in any rolling 4-hour window, with a 12/day safety ceiling. Overnight activity must not exhaust the daytime opportunity budget.

Explicitly removed as operating requirements:

- “must publish one original every day”;
- “must publish 2/3/5 replies every day”;
- hotspot/news-count targets;
- Article-count targets;
- milestone pass/fail based on number of posts or replies.

The system must still continuously discover and surface strong `POST` and `REPLY` opportunities. Quality gates determine output, not a quota.

Notification ceilings may exist to protect operator attention/model cost; a ceiling is not a publishing target.

## 10. Follow-Reason Funnel

Every review evaluates:

```text
STOP -> ENGAGE -> PROFILE INTEREST -> FOLLOW REASON -> RELEVANT FOLLOW
```

Interpretation:

- **STOP**: does the opening make the right person stop?
- **ENGAGE**: likes/replies/bookmarks/reposts or meaningful reading signal;
- **PROFILE INTEREST**: does the post make the reader want to know who Kenny is?
- **FOLLOW REASON**: does the profile/content history promise more of the same value?
- **RELEVANT FOLLOW**: did the account gain the intended audience?

Reply impressions without engagement/profile/follow conversion are distribution evidence only, not success.

## 11. Publication Gate

Before recommending `POST`, answer:

1. Is there a real Kenny viewpoint?
2. Is it useful to people turning AI into productivity?
3. Is it more than information they can obtain from the headline/search?
4. Is there evidence, practice, data, or a concrete case?
5. Will a reader understand how Kenny thinks after reading it?
6. Does it strengthen a future follow reason?

If most are no -> `SKIP`.

Before recommending `REPLY`, additionally require one of the four reply-value types in Section 6 and a verified direct X target.

## 12. Discovery Scope

The discovery system must cover both:

### A. Global AI-productivity signals

- AI agents / agent runtime;
- AI coding / software development;
- model capability/cost changes that alter real workflows;
- automation / AI-native workflows;
- multi-agent systems / verification / evals / reliability;
- AI products and business-model shifts;
- world models when they change real capabilities;
- robotics when AI moves from demo to useful deployment.

### B. China differentiation signals

- Chinese models, agents, AI coding and developer ecosystem;
- China-side primary sources not widely seen in English;
- semiconductors/compute when they alter AI economics/capability;
- robotics/manufacturing when deployment, cost, or scale matters;
- China/global comparisons that materially change the target audience's understanding.

Pure macro, politics, generic finance, ordinary company news, or generic China business remains out of scope unless the AI/productivity consequence is concrete.

## 13. Operating Roles

### ChatGPT

- continuously find strong topics and live X reply targets under this spec;
- verify facts when needed;
- develop the point of view instead of rewriting headlines;
- draft all originals in Chinese;
- draft replies in the parent-post language;
- review analytics and identify follow-reason failures;
- use the user's real projects/research as a source of `WHAT I LEARNED` content when relevant.

### Mac mini radar

- continuous low-cost signal collection;
- deterministic prefiltering;
- editorial enrichment;
- personal Feishu publish-ready opportunity packets;
- outcome/evidence capture;
- no automatic X publishing.

### Human operator

- final judgment/edit;
- manual X publishing;
- provides published URLs/outcomes when practical.

## 14. Feishu Publishing Packet Contract

Personal Feishu remains the only production alert route.

Raw candidates stay internal. Operator-facing packets must be high-value `POST` or `REPLY` opportunities.

Each packet contains:

- `P0/P1` priority;
- `POST` or `REPLY` recommendation;
- content bucket: `WHAT_I_BELIEVE | WHAT_I_LEARNED | WHAT_CHANGES`;
- short reason and “why this matters to AI productivity”;
- verified X target for `REPLY`;
- final paste-ready copy using the language policy;
- source/provenance kept separate;
- visual recommendation only when useful.

`SKIP` remains silent.

## 15. KPI Authority

`00_Governance/OPERATING_KPI.md` defines measurement details.

Hard principle: **no KPI rewards publishing volume for its own sake**.

Track:

- relevant follower total/delta;
- impressions by action type as distribution evidence;
- engagements and saves when available;
- profile visits when available;
- follow conversion / follow-reason evidence;
- recurring topic/thesis patterns that create the intended audience;
- alert precision and operator time as system-health metrics.

## 16. Costs / Publishing Boundaries

- mandatory new paid spend: `$0` unless separately approved;
- paid X API remains blocked;
- no automatic post/reply/DM publishing;
- model usage remains capped and observable;
- tools/infrastructure are added only when they solve a measured bottleneck.

## 17. Explicitly Superseded Rules

The following no longer control execution:

- “English-language China Tech audience” as the account definition;
- “China Tech Intelligence” as a news-first positioning;
- China entity as a universal prerequisite for a publishable signal;
- Stage-A `3–5 replies/day` target;
- `~1 original/day` target;
- milestone minimum counts for replies/originals;
- reply-led cold start as the dominant identity strategy;
- paste-ready English copy for every publish packet;
- routine Article production;
- optimizing for news volume/hotspot coverage;
- treating high reply impressions as success without conversion.

## 18. Current Strategic Thesis

The account should become known for:

> **Kenny 对“AI 如何真正变成生产力”的持续判断。**

The durable asset is not the number of posts. It is an accumulating thesis library built through:

```text
belief -> evidence -> practice -> correction -> stronger belief
```

The operating question is no longer:

> 今天有什么新闻可以发？

It is:

> **今天有什么东西，值得告诉这群真正想把 AI 变成生产力的人？**


## 19. Mandatory Human Voice Gate

This is a publishing gate, not a stylistic preference. It applies to Chinese originals and replies in any language.

Final copy must sound like Kenny joining a real conversation, not a report, press release, research memo, or AI summary. Lead with the actual judgment, useful fact, or experience; make one main point; remove generic filler, formal conclusions, forced rhetorical symmetry, and repetitive house templates; and contain no internal heading, label, process note, or source note inside paste-ready copy.

A Reply must respond to the exact claim, normally use 1–3 short sentences, and add one of the four approved reply-value types. An original Post must be Chinese and must contain a real thesis or useful conclusion; a news summary is not publishable owned content.

Avoid by default, in either language: `One caveat`, `The bigger signal`, `The bigger question`, `What caught my eye`, `Worth noting`, `This suggests that`, `This points to`, `The key test is`, `This isn't just`, `In other words`, `The real story`, `The interesting part isn't X. It's Y.`, `The real shift isn't X. It's Y.`, `The biggest takeaway isn't X. It's Y.`, `真正重要的不是X，而是Y`, `真正值得关注的不是X，而是Y`, `更大的信号是`, `更大的问题是`, repeated `not X, but Y` / `不是X，而是Y`, and em-dash-heavy prose.

If a draft fails the voice gate, rewrite once. If it still fails, `SKIP`.

## 20. Single Reply Standard

The legacy A/B Reply experiment is retired. There is no A/B reply split or A/B quota. Every Reply is judged by one standard: **does this add something worth reading from Kenny for the AI → productivity audience?**

A Reply is publishable only when it contributes at least one of:
- a primary-source fact or factual correction that materially changes the discussion;
- a key number/metric that changes the conclusion;
- a corresponding China/global case that adds useful context;
- a first-hand result from Kenny's own research, testing, building, or operations;
- a clear judgment about what changes for capability, cost, reliability, workflow, product design, business model, or real productivity.

A factual addition is not a separate content strategy. If it does not strengthen Kenny's worldview, help the target cohort, or create a reason to follow, `SKIP`. Reply value is tracked through `angle_type`, not an experiment group.

## 21. Article Owner Authority

Article topics, core questions, and theses are selected by Kenny after sufficient research or after a shorter idea has demonstrated value. The realtime radar must not schedule, quota, or derive Article topics from daily news. Once Kenny assigns an Article topic, the system may support research, evidence collection, fact checking, Chinese drafting, visuals, and publication packaging.


## 22. Creator Monitoring Quality Gate

Direct X creator monitoring is intentionally curated. The objective is not maximum coverage; it is high-signal access to people who can improve Kenny's understanding and create worthwhile conversations with the AI-productivity audience.

### Core technical creator admission

Prefer people who meet at least one:
- active AI/ML researcher publishing or discussing original research;
- engineer/builder working directly on agents, AI coding, harnesses, evals, reliability, inference, world models, robotics, or AI systems;
- creator with repeated first-hand experiments, code, benchmarks, system design, or deployment lessons;
- primary technical leader whose posts expose important research direction before it becomes generic news.

### Exclusion / downgrade

Do not directly monitor accounts whose dominant value is:
- stock-price/ticker commentary or trading calls;
- get-rich-with-AI, side-hustle, automated-income, or exaggerated money claims;
- engagement farming / hype reposting without original technical evidence;
- generic AI tool lists with no real testing;
- partisan/geopolitical content unrelated to the target audience;
- broad lifestyle/creator content with only occasional AI mentions.

Such accounts can still appear through event-specific global search when a particular post is independently valuable, but they do not deserve a persistent creator slot.

### Monitoring tiers
- `core_technical`: direct high-frequency monitoring;
- `technical_fact`: lower-priority first-hand industry/engineering source;
- `global_search_only`: not persistently monitored; eligible only when a specific post/event passes the editorial gate.

For direct creator monitoring, technical quality outranks follower count and virality.


## 23. Pre-Draft SPEC Check and Brevity Gate

This is a hard publishing rule. Before generating any paste-ready X Post or Reply, the editorial runtime MUST read the current `PROJECT_SPEC.md` and apply at least Sections 19, 20, and 23. Do not rely on remembered or cached wording. If the current SPEC cannot be read, do not generate publish-ready copy.

### Brevity is the default

Write like a real person replying on X, not like someone trying to complete an essay. Use the fewest words that preserve the point.

For Reply copy:
- default to **one short sentence**; use two only when a fact/correction genuinely needs support;
- lead directly with the point; no setup paragraph, recap, throat-clearing, generic praise, or formal conclusion;
- use everyday words and natural spoken phrasing;
- do not restate the parent post unless needed to correct it;
- one clear point beats a complete explanation;
- if two versions say the same thing, publish the shorter one.

For original Posts, concise is also preferred. Do not add paragraphs merely to make a post look complete. Depth belongs in a Thread/Article only when the idea actually requires it.

Internal target, not a quota: an English Reply should usually fit within about 35 words; a Chinese Reply should usually fit within about 60 Chinese characters. Exceed this only when the extra words materially improve accuracy or usefulness.


## 24. Humanizer and Opening-Diversity Gate

Before any paste-ready Post/Reply is drafted, the runtime MUST load the installed Humanizer skill at `~/.codex/skills/humanizer/SKILL.md` in addition to the current SPEC. If the skill cannot be read, do not produce publish-ready copy.

For Replies, the runtime must also inspect recent sent Reply openings and avoid repeating the same opening shape, cadence, or stock framing. Do not solve this by rotating through a new set of templates. The wording should follow the actual thought.

After drafting, run one Humanizer self-audit internally: ask what still sounds machine-written, cut it, and return only the revised copy. Prefer ordinary spoken language, uneven natural rhythm, and fewer words.


## 25. Kenny Voice Fingerprint

`00_Governance/KENNY_VOICE_FINGERPRINT.md` is the canonical personal-voice profile for X copy. Before drafting paste-ready content, the runtime MUST freshly read this file together with the current SPEC and Humanizer skill. If it cannot be read, do not produce publish-ready copy.

The profile is based primarily on Kenny's natural working/conversation language. Existing AI-generated Replies are negative examples, not positive training data. Humanizer makes the copy human; the Kenny profile makes it sound like Kenny.


## 26. Creator Expansion and Reply Diversity

The monitored creator pool must keep expanding. Do not optimize Reply volume around a small familiar cluster. Maintain two layers: a stable `core_technical` pool and a growing `expansion_technical` pool discovered from adjacent technical communities.

Expansion priorities: agent/harness/evals, AI coding and developer tools, inference/AI systems, world models/robotics/physical AI, and China/global builders with first-hand technical evidence. Prefer practitioners and researchers over news aggregators, hype accounts, finance/ticker accounts, and generic AI-tool curators.

For growth, creator diversity is an operating constraint: ordinary P1 Replies should not repeatedly target the same creator. Default cooldown is one P1 Reply per creator per 24 hours and at most three P1 Replies per creator in seven days. P0 may bypass this when the opportunity is genuinely exceptional. At similar quality, prefer a creator Kenny has not engaged with recently.

Creator discovery is ongoing maintenance, not a one-time list build. Add qualified creators regularly; do not wait for the existing pool to become stale.

## 27. Distribution Opportunity Signal Engine

Direct X reply discovery must optimize for **distribution opportunity after relevance**, not for news importance alone. The engine exists to identify conversations that are both worth joining and already showing audience movement.

Hard ordering of concerns:

```text
audience/topic relevance
 -> Kenny can add real value
 -> live distribution opportunity
 -> creator diversity
 -> operator attention
```

Virality never rescues an off-audience or low-value candidate. A high-view post that fails the topic/value gate remains `DROP/SKIP`.

For verified direct X targets, capture observable public metrics at discovery time when available: views, likes, replies, reposts, quotes, and bookmarks. Derive and persist at least:

- `distribution_score`;
- `observed_views`;
- `view_velocity_per_min`;
- `engagement_rate`.

The deterministic distribution score combines freshness, view velocity, current view scale, engagement rate, and reply/quote conversation activity. Configuration thresholds live in `config/rules.toml` and may be calibrated from outcome evidence without changing the editorial identity.

Exact post deduplication must **not** freeze distribution evidence. Every subsequent observation of the same direct-X status refreshes public metrics and re-runs classification while preserving the original discovery timestamp. A post may graduate from `DROP/P2` to `P1/P0` when it begins to break out; if no alert existed before, that graduation creates the normal editorial opportunity. Conversely, a still-pending alert is expired if the live target no longer qualifies by the time it is re-observed. Existing `SENT/SKIP/HOLD` editorial decisions are not automatically reopened merely because views later increase.

A normal direct-X P1 candidate must pass the relevance score and either show sufficient distribution momentum or fall inside a short early-discovery grace window with strong relevance. This prevents waiting until a post is already saturated while still suppressing flat posts that never begin to move.

A clearly breakout direct-X target may be promoted to P0 by distribution evidence even without a keyword-based “high impact” marker. P0 remains exceptional; editorial quality still controls whether anything is sent.

Pending editorial work is ordered by:

1. P0 before P1;
2. verified direct X targets before search-required candidates at the same priority;
3. higher `distribution_score`;
4. higher `view_velocity_per_min`;
5. relevance score and recency.

The editorial model must see the distribution evidence but treat it only as **timing/distribution evidence**. REPLY is still allowed only when Kenny adds an approved value type from Section 20. Do not send generic commentary merely because a parent post is viral.

Creator diversity rules in Section 26 remain active. Distribution opportunity is a reason to join the right conversation early, not a reason to repeatedly farm one large account.


## 28. Closed-Loop Outcome Feedback

The signal engine must learn from Kenny's actual published outcomes, not only from parent-post virality. Public X data is used at $0 cost to close the loop.

### Automatic post outcome capture

For published X posts/replies with a known URL, automatically capture public metrics when available: views, likes, replies, reposts, quotes, and bookmarks. Sampling frequency tapers with age: relatively frequent shortly after publishing, then hourly/daily as the post matures. Profile visits are **not** publicly exposed and must remain `null` unless supplied from first-party analytics; never infer or fabricate them.

### Automatic account snapshots

Read the public `@KennyChinaTech` profile periodically and persist follower count. Follower deltas are evaluated at cohort/day level. A gap of more than one calendar day between snapshots is not eligible for causal attribution to that day's content.

### Creator feedback prior

Actual Reply outcomes may influence future creator ranking only conservatively:

- at least 3 Reply outcome samples are required before impression-based feedback activates;
- median Reply impressions are used instead of one breakout maximum;
- the creator feedback score is a small ranking prior and never bypasses relevance, distribution, editorial-value, voice, or creator-diversity gates;
- follower growth may add at most a weak positive prior only on clean evidence days where consecutive daily follower snapshots exist and exactly one published action occurred; multi-action days are not attributed to one creator;
- insufficient evidence remains neutral rather than being treated as failure.

The ranking sequence for comparable direct-X candidates is therefore:

```text
relevance/value gate
 -> live distribution opportunity
 -> conservative historical outcome feedback
 -> current view velocity
 -> base relevance/recency
```

This feedback loop optimizes for durable relevant-audience growth, not raw impressions alone.

## 29. Reply-Acquisition Creator Expansion

Creator monitoring is an acquisition system, not a static celebrity list. The objective is to find more technical conversations where a small account can earn meaningful Reply distribution and convert that attention into relevant followers.

Expansion evidence is evaluated in this order:

1. Kenny's actual mature Reply impressions on that creator, when at least three samples exist;
2. the creator's observed parent-post distribution on X (recent median/maximum views, live view velocity, distribution score);
3. audience overlap with proven acquisition creators;
4. technical/content quality and ability for Kenny to add a differentiated fact, correction, China/global comparison, or first-hand practice result.

Follower count by itself is not an admission rule. A 20K-follower creator whose current posts reliably reach 10K-30K relevant readers can be more useful than a 500K-follower account whose current posts do not move or whose audience does not overlap.

New creators normally enter `expansion_technical` or `technical_fact`. They do not receive automatic Reply recommendations. Every post still passes topical relevance, the Distribution Opportunity engine, Creator Feedback, creator cooldown/diversity, the editorial value gate, and the human-voice gate.

The runtime must expose a `creator_acquisition` report combining:

- observed parent-post count and P0/P1 opportunities;
- median/max observed parent views;
- distribution score / view velocity evidence;
- Kenny's Reply sample count and median Reply impressions;
- conservative historical feedback score;
- clean follower-growth evidence when available.

Creator expansion should continuously explore adjacent communities around proven creators, especially:

- AI coding / harness / evals / developer workflows;
- China AI builders and Chinese-language AI technical creators;
- AI compute / HBM / semiconductors where it materially affects AI;
- world models / robotics / physical AI;
- primary technical accounts and high-signal technical synthesis accounts.

Avoid engagement farms, generic AI-tool spam, side-hustle accounts, finance/ticker accounts, and broad viral accounts with weak target-audience overlap even when their raw views are high.

## 30. Collector / Editorial Worker Isolation

Realtime discovery and slow editorial reasoning are separate production loops. A model search, capacity delay, humanizer pass, or Feishu delivery attempt must never block direct-X polling.

Production topology:

```text
Collector (15s launchd)
  -> fetch / refresh live sources
  -> classify + Distribution Opportunity
  -> create/expire PENDING alerts
  -> outcome/account snapshots
  -> SQLite WAL

Editorial Worker (15s launchd, non-overlapping per worker)
  -> atomically claim PENDING alert
  -> editorial gate / verification / humanizer
  -> re-read live signal before send
  -> SENT / SKIP / HOLD / ERROR
  -> Feishu
```

Hard rules:

- Collector runs with no publishing/notification work and must remain independent of model latency.
- Editorial Worker performs no source discovery.
- Claim state is `EDITORIAL_PROCESSING`; two workers must not process the same alert.
- A processing claim older than ten minutes is recoverable back to `PENDING`.
- Before notification, Editorial Worker re-reads the current signal. If Collector has downgraded it below P0/P1, it expires rather than sending stale advice.
- SQLite WAL and busy timeout remain the shared-state coordination mechanism.
- Manual integrated `run` may remain available for diagnostics, but production launchd uses the isolated collector and editorial commands.

## 31. Adaptive Creator Observation Budget

A larger creator pool must not degrade discovery latency. Monitoring cadence is a scarce acquisition budget and is allocated by evidence.

Static observation tiers provide the cold-start prior:

- `1–2 min`: proven or very high-reach acquisition creators and high-value primary AI/coding accounts;
- `4 min`: core technical creators with strong audience fit;
- `6 min`: technical-fact / ecosystem sources;
- `8 min`: broad exploration layer.

The aggregate configured X polling demand must remain below the staggered collector capacity (`max_x_profiles_per_cycle` / collector interval), with material headroom for network variance. Expansion that would overload the collector must first rebalance lower-value cadence.

Actual Kenny Reply outcomes override the cold-start cadence conservatively:

- Creator Feedback `>= +2` -> effective interval no slower than 2 minutes;
- Creator Feedback `+1` -> effective interval no slower than 3 minutes;
- Creator Feedback `< 0` -> effective interval at least 8 minutes;
- neutral/insufficient evidence -> configured tier remains unchanged.

This cadence adjustment changes observation frequency only. It never bypasses content relevance, live Distribution Opportunity, creator diversity/cooldown, editorial value, or human-voice gates.

## 32. Reply Surface / Competition Opportunity

Parent-post reach alone is not enough for Reply acquisition. A small account benefits most when a relevant post is already moving but its direct-reply surface is not yet saturated.

For direct-X posts, when public metrics expose a reply count, persist:

- `observed_replies`;
- `observed_quotes`;
- `views_per_reply = observed_views / (observed_replies + 1)`;
- `reply_surface_score`;
- `reply_acquisition_score`.

If the public page does not expose reply count, competition is **unknown**, not zero. Missing reply count must stay neutral and must never be interpreted as an empty thread.

### Reply Surface Score

The score rewards audience available per existing direct reply and penalizes saturated threads. Conceptually:

```text
higher parent views per existing reply
+ low direct-reply count while reach is already meaningful
- heavily saturated reply threads
= higher Reply Surface Score
```

A 30K-view post with ~10 direct replies should normally outrank a 300K-view post with thousands of direct replies when relevance and freshness are comparable. Tiny posts are capped so zero replies on a low-reach thread cannot look artificially attractive.

### Reply Acquisition Score

For direct-X targets:

```text
Reply Acquisition Score
  = Distribution Opportunity
  + Reply Surface Score
  + conservative Creator Feedback
```

This score is the primary ordering signal among comparable verified X reply opportunities, followed by Distribution Opportunity, Reply Surface, Creator Feedback, current view velocity, base relevance, and recency. A relevant post may pass the normal P1 distribution gate when its Reply Acquisition Score is sufficiently high even if raw distribution momentum alone is just below the standard threshold.

Reply Surface does **not** relax the content-value requirement. A large open reply window with nothing useful for Kenny to add is still `SKIP`.

### Learning snapshot at publication

When Kenny publishes a Reply, automatically snapshot the parent post's observed views, direct replies, quotes, views-per-reply, and Reply Surface Score into `published_action`. The same snapshot must be recorded whether the action is manually registered or automatically reconciled from the target thread. This becomes the training evidence for learning which reply-surface conditions actually produce Kenny impressions/followers.
