# Project Status

## Status Timestamp

2026-09-01

## Canonical Authority

Top-level authority: `PROJECT_SPEC.md` v2.0.

Status: `AUDIENCE_FIRST / PERSONAL_FEISHU_VERIFIED / SHADOW_DAY_1_ACTIVE / GROWTH_FORMULA_SEARCH_ACTIVE`.

## Business Objective

Grow `@KennyChinaTech` from 4 followers into a large, relevant China Tech audience, discover the repeatable follower-growth formula, and monetize audience leverage later through aligned commercial cooperation and platform/affiliate/owned-media paths.

Current North Star: **relevant follower growth**.

## Experiment Clock

Valid audience-first Shadow Test start:

`2026-08-31T12:27:44Z` / `2026-08-31 20:27:44 Asia/Shanghai`.

Baseline followers: `4`.

All earlier bootstrap/misrouted Feishu activity is excluded from this experiment clock.

## Current Production Runtime

- repository main: `Creatiny/china-tech-x-poc`;
- service: `/Users/jh/services/china-tech-x-radar`;
- runtime: native Python + SQLite;
- poll cadence: approximately 5 minutes through launchd;
- daily review: launchd + ChatGPT review workflow;
- personal Feishu: **verified / enabled**;
- Feishu group: **prohibited**;
- paid X API: `0` authorized spend / `0` chargeable calls;
- auto X publishing: disabled;
- OPC: optional/non-blocking;
- Docker/Colima: non-blocking/deferred.

## Active Source Set

Configured free/traceable sources include:

- Pandaily;
- SCMP China;
- focused Reuters China Tech via Google News RSS;
- DeepSeek GitHub releases;
- Qwen GitHub releases;
- GLM GitHub releases;
- disabled fallback sources remain non-authoritative until source health justifies activation.

Reuters was added only after the Nexperia/Wingtech original post exposed a concrete source-coverage miss.

## Formal Published Samples

### Sample #1

- URL: `https://x.com/KennyChinaTech/status/2094405136366047694`;
- type: `ORIGINAL`;
- event: `SEMICONDUCTOR`;
- subject: Nexperia / Wingtech;
- treatment: `CHINA_CONTEXT × CONTRAST × IMAGE × EXTERNAL_LINK`;
- public outcome snapshots are being tracked;
- formula evidence status: `ANECDOTE / SAMPLE_COUNT=1`.

## KPI Authority

`00_Governance/OPERATING_KPI.md` v3.0.

Current gates:

- Day 3 >=8 followers;
- Day 7 >=15;
- Day 10 >=25;
- Day 15 >=40;
- Day 30 >=100, stretch >=200.

## Formula Authority

`00_Governance/GROWTH_FORMULA.md` v1.0.

Priority hypotheses:

1. reply timing `<30m`;
2. target size `100K–1M` vs `>=1M`;
3. China-specific/context/global-implication/comparison angles;
4. China AI / semiconductors / robotics topic concentration;
5. native original vs link-first original treatment.

Evidence rule:

- 1 sample anecdote;
- 2 hypothesis;
- >=3 repeated wins candidate formula;
- >=5 repeated wins + follower-positive cohorts => scale bias.

## Current Execution Priority

1. keep 5-minute discovery and personal Feishu signaling healthy;
2. maximize quality early replies and differentiated originals within the Stage-A plan;
3. capture every published URL and formula variable;
4. capture public outcome snapshots and daily follower count;
5. run daily KPI + formula review;
6. change only the first broken growth variable;
7. expand sources/tools only after observed misses/bottlenecks.

## Current Known Gaps

1. formula sample size is still too small;
2. direct X target-post resolution remains human-assisted;
3. exact per-action follower attribution is impossible when actions overlap, so follower causality is evaluated by daily cohorts;
4. profile-visit metrics may require manual/native-X visibility when public endpoints do not expose them;
5. source coverage can still miss events and must be repaired only from concrete miss evidence.

## Stop Gates

Human approval is required for:

- strategy/spec or architecture boundary change;
- paid spend or chargeable API;
- automatic publishing/DM authority;
- unavailable secret/account permission;
- destructive external change;
- material legal/platform-policy ambiguity.

Ordinary implementation, source repairs backed by observed misses, GitHub PR/merge, tests, and runtime corrections proceed without repeated approval.

## 2026-09-01 Feishu Publish-Packet Upgrade

Operator feedback established that a raw P1 signal with source/search links still creates too much manual work. The production interface is therefore upgraded from raw alerting to **publish-ready personal Feishu packets**.

Active contract:

- raw candidates stay internal;
- generic macro/geopolitical/general-China candidates must be filtered or editorially skipped;
- ambiguous candidates may use a low-reasoning no-search Codex gate;
- final candidates use the locally authenticated ChatGPT/Codex OAuth runtime for fact verification, `POST/REPLY/SKIP` selection, X-target search when relevant, and paste-ready humanized English copy;
- only `POST/REPLY` is sent to personal Feishu;
- `SKIP` is silent and persisted;
- REPLY requires a verified direct X status URL;
- POST keeps source URL separate from native-first final copy;
- when a visual materially helps, the runtime generates an original editorial data card and sends the image after the text packet;
- model calls/token proxies are logged and capped daily; no OpenAI Platform API key is introduced.

The reported yuan/weak-demand Reuters alert is classified as a false positive and now deterministically drops because generic `China/Chinese` alone cannot satisfy curated-source entity-only qualification.

## 2026-09-01 Day-2 Review Correction — Timeliness + Precision

The first partial Day-2 review found two evidence-backed issues before the Day-3 gate:

1. **source timeliness/coverage**: the existing six-source radar did not contain two timely China Tech items visible in IT之家 RSS at review time — a Unitree firefighting robot item published at 2026-09-01T02:06:16Z and a Huawei Ascend 950 AI-model procurement item published at 2026-09-01T01:23:49Z;
2. **classifier precision**: two silent editorial skips were caused by generic `release` and `funding` terms being treated as standalone technology topics (a Chinese film story and a university funding-disclosure settlement).

Approved minimal correction under the one-growth-variable + one-measurement-fix rule:

- add IT之家 RSS as one new evidence-backed China Tech discovery source, polled every five minutes;
- require explicit Chinese China-Tech entities + technology terms on this non-China-focused adapter;
- add only the Chinese entity/topic vocabulary required for AI/chips/robotics/EV discovery;
- stop treating generic `funding` and `release` as standalone `topic_terms` while keeping them available as impact context after a real technology topic matches.

No OPC, browser automation, paid API, web UI, or new infrastructure is introduced.
