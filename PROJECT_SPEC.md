# China Tech X POC — Canonical Project Spec v3.0

## 0. Authority

**Status:** `APPROVED / ACTIVE / SINGLE SOURCE OF TRUTH`  
**Effective:** `2026-09-09`

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
