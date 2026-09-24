# AI实战X — Active Traction Experiments

**Status:** ACTIVE  
**Started:** 2026-09-24  
**Source:** `TRACTION_OPERATING_SYSTEM.md` + production review on 2026-09-24

## Current Critical Path

**MEASUREMENT_GAP**

Production review evidence:
- relevant followers recorded: 34, +30 from experiment baseline;
- published actions: 51;
- Replies: 41;
- originals: 10;
- mature outcome coverage exists for 50/51 actions;
- only 1 operator `worth_reviewing` decision exists, so alert precision cannot be inferred safely;
- overall median impressions: 75; max: 2,004.

Immediate rule: do not increase Reply/Post volume and do not tighten discovery solely from the single review sample.

## Bullseye Test A — Targeted Creator / Reply Acquisition

**Hypothesis:** A small number of high-fit technical conversations can provide useful borrowed distribution and creator relationships without a Reply quota.

**Current evidence**
- 41 Replies published;
- 40 have impression outcomes;
- median Reply impressions: 114.5;
- 25% reached >=300 impressions;
- 7.5% reached >=1,000 impressions;
- follower/profile attribution remains incomplete.

**Decision:** `ITERATE`

**Next test**
- keep strict relevance/evidence gate;
- prefer creators with mature own-outcome evidence and strong audience overlap;
- collect at least 3 valid operator worth decisions before changing alert-precision rules;
- judge success by mature distribution + repeat interaction + relevant-follow evidence, not Reply count.

## Bullseye Test B — First-hand Owned Content

**Hypothesis:** Originals built from Kenny's real experiments/projects will outperform generic AI commentary and create a stronger follow reason.

**Current evidence**
- 10 originals with outcomes;
- median original impressions: 24.5;
- max original impressions: 68;
- current owned-content distribution is materially weaker than Reply distribution.

**Decision:** `ITERATE` — change the content input, not the volume.

**Next test**
Use the next owned-content samples only when they originate from first-hand work such as:
- Research Factory / Stagehand experiments;
- OPC / Agent runtime / verification lessons;
- local LLM deployment/model selection;
- measured cost/latency/reliability comparisons.

Each sample must include one clear thesis plus concrete evidence. Do not add filler originals to increase N.

## Bullseye Test C — Engineering as Marketing

**Hypothesis:** A useful public artifact derived from real project work can compound discovery longer than a normal Post.

**Current evidence:** not yet instrumented as a separate channel.

**Decision:** `START`

**Cheapest valid first test**
Package one already-existing real artifact rather than building a marketing toy from scratch. Preferred first candidate:
- a public Research Factory benchmark/scorecard or reproducible checklist derived from the recent real experiment.

Alternative candidates:
- Local LLM Fit Checker;
- Agent Runtime Benchmark;
- model cost/latency/reliability selector.

**Primary evidence**
- qualified uses / saves / citations / shares;
- profile interest and relevant follows where measurable;
- repeat discovery over >=7 days.

**Decision date:** after a valid asset is public and has at least 7 days of observation.

## Bullseye Decision Rule

Do not declare a winner from one breakout.

Promote to `SCALE` only when a tactic shows repeatable evidence on the relevant audience. Otherwise:
- `ITERATE`: a specific variable remains testable;
- `KILL`: consumes attention without useful acquisition evidence;
- `INCONCLUSIVE`: sample/attribution is insufficient.

At most one major growth variable should change between daily reviews unless the parallel change is instrumentation-only.
