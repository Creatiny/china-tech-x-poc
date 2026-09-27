# AI实战X — Active Traction Experiments

**Status:** ACTIVE  
**Started:** 2026-09-24  
**Last reviewed:** 2026-09-27
**Source:** TRACTION_OPERATING_SYSTEM.md + production evidence

## Current Critical Path

**EXECUTABLE_OPPORTUNITY_DENSITY + MEASUREMENT_GAP**

The collection/runtime failure that caused zero X-profile supply on Sep 26–27 is fixed. Current work is no longer about increasing raw alert count. It is about concentrating recommendations on creator/audience surfaces that Kenny is likely to use and that have repeatable distribution evidence.

Current evidence:
- relevant followers recorded: 35;
- operator worth_reviewing decisions: 1, so alert-precision and per-action follower attribution remain incomplete;
- clean comparable outcomes since Sep 20: 7 Replies, median 131 impressions, max 2,019;
- clean comparable originals since Sep 20: 9 originals, median 35 impressions, max 70;
- therefore Reply currently functions as the stronger cold-start distribution channel; originals are primarily owned/profile-conversion assets until their distribution improves.

Immediate rule: optimize opportunity quality and creator fit, not recommendation volume.

## Bullseye Test A — Targeted Creator / Reply Acquisition

**Hypothesis:** A small number of high-fit technical conversations can provide useful borrowed distribution and creator relationships without a Reply quota.

**Current evidence**
- clean recent Reply outcomes: 7 measured; median 131; max 2,019;
- @vista8: 2 mature published Replies, median 1,811.5 impressions; 2 recommendations / 2 adopted; provisional creator feedback +1;
- @shao__meng: 13 mature Reply outcomes, median 82 impressions despite high historical recommendation adoption; operator adoption alone is not evidence of distribution value;
- @maxforai: 2 mature outcomes, median 498; insufficient for positive feedback under the two-sample floor because both did not clear the strong-acquisition threshold;
- creator ranking now includes mature own-outcome evidence, a conservative two-sample provisional bridge, and operator adoption as a tie-break / usability signal.

**Decision:** ITERATE

**Next test**
- concentrate on proven high-fit creator clusters rather than broad Reply volume;
- use @vista8-like repeated high-reach outcomes as the pattern to discover adjacent Chinese creators;
- continue evidence-gated creator expansion; never fill the 25 + 20 target with weak accounts;
- judge success by mature Reply distribution, repeated usable opportunities, and relevant-follow evidence where measurable;
- keep one-breakout creators at neutral prior.

## Bullseye Test B — First-hand Owned Content

**Hypothesis:** Originals built from Kenny's real experiments/projects will create a stronger follow reason than generic AI commentary.

**Current evidence**
- clean recent original outcomes: 9 measured; median 35 impressions; max 70;
- current owned-content distribution remains materially weaker than Reply distribution;
- the role of originals at this stage is therefore profile conversion / durable proof, not primary cold-start acquisition.

**Decision:** ITERATE — change the content input, not the volume.

**Next test**
Use owned-content samples only when they originate from first-hand work such as:
- Research Factory / Stagehand experiments;
- OPC / Agent runtime / verification lessons;
- local LLM deployment/model selection;
- measured cost/latency/reliability comparisons.

Each sample must include one clear thesis plus concrete evidence. Do not add filler originals to increase N.

## Bullseye Test C — Engineering as Marketing

**Hypothesis:** A useful public artifact derived from real project work can compound discovery longer than a normal Post.

**Current evidence:** not yet instrumented as a separate channel.

**Decision:** START

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

## 2026-09-27 Data-Quality Repair

X changed its public SSR shape. Two separate defects were corrected before the evidence above was accepted:
1. X profile collection could return HTTP 200 with zero parsed posts and be recorded as healthy. The parser now supports the TimelineTweet SSR shape and fails closed on parse-empty responses.
2. Quote-post pages can embed the quoted parent's metrics inside the outer tweet result. The parser now anchors by outer tweet ID + author and excludes nested quote metrics. Recent public outcome snapshots were refreshed after this repair.

The clean Reply/original figures above use the repaired latest snapshots. Do not use the previously observed 294K / 10K values that belonged to quoted parent posts rather than Kenny's outer posts.

## Bullseye Decision Rule

Do not declare a winner from one breakout.

Promote to SCALE only when a tactic shows repeatable evidence on the relevant audience. Otherwise:
- ITERATE: a specific variable remains testable;
- KILL: consumes attention without useful acquisition evidence;
- INCONCLUSIVE: sample/attribution is insufficient.

At most one major growth variable should change between daily reviews unless the parallel change is instrumentation-only.
