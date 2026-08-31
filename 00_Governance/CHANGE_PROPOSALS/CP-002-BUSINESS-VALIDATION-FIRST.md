# CP-002 — Business Validation First

## Metadata

- Status: `APPROVED`
- Decision date: `2026-08-31`
- Decision authority: Human product owner
- Supersedes: the implementation-order and mandatory-OPC assumptions in CP-001
- Preserves: China Tech positioning, human publishing, zero-paid-X boundary, and evidence-driven experimentation

## 1. Problem

The realtime-radar direction in CP-001 is still valid, but its execution path became over-coupled to infrastructure work. The first Shadow Test was blocked by MomentGrid OPC stability and cross-repository intake concerns before the Mac mini fact audit or any China Tech runtime had actually started.

The original pack also required several capabilities before the business experiment could begin, including full clustering, a web inbox, control-plane integration, deployment governance, and a broader runtime foundation. Those capabilities may become useful, but they do not answer the immediate business question: can earlier China Tech signals and better-timed replies produce materially better X distribution?

The account is still at a very small baseline. Additional architecture without a live distribution experiment increases cost and delay while producing little business evidence.

## 2. Expected Benefit

This change makes business evidence the sequencing authority:

- the first runnable system is a small native Mac process rather than a platform project;
- the first goal is a delivered, reviewable signal and a human-published action;
- the first evidence is alert latency, actionability, reply timing, impressions, profile effects, and follower change;
- OPC, Docker, local models, a web UI, and paid X-native data are added only when measured evidence identifies the bottleneck they solve;
- existing infrastructure can be reused when healthy, but unrelated infrastructure failures cannot block the experiment.

## 3. Cost

### Mandatory new spend

`$0`.

### Reused assets

- Mac mini;
- Python and SQLite;
- launchd;
- GitHub and `gh`;
- free RSS/Atom and GitHub endpoints;
- existing Feishu application credentials if a valid receive target can be verified.

### Explicitly not required before validation

- MomentGrid OPC integration;
- Docker/Colima repair;
- Horizon installation;
- a web inbox;
- a local LLM or paid model API;
- a paid X API plan;
- automatic publishing.

## 4. Test Method

The minimum business loop is:

1. poll a small, curated set of China Tech sources every five minutes;
2. normalize and exact-deduplicate items locally;
3. apply deterministic China Tech relevance and freshness rules;
4. send qualified alerts to a verified mobile-capable channel;
5. the operator manually selects an X target, writes/uses an AI-assisted reply, and publishes;
6. record the target URL, signal age, publish time, impressions/engagements/profile/follower effects when available;
7. run the loop for seven consecutive valid days before increasing system complexity.

An alert without a direct target X post can still be useful as a signal, but it does not count as an executable reply opportunity until the operator or a future resolver identifies a target.

## 5. Business Success Criteria

The seven-day experiment must answer four questions with evidence:

| Question | Validation signal |
|---|---|
| Are signals early enough? | P0/P1 source-to-alert delay is measured; target is <=10 minutes for polled sources. |
| Are alerts worth attention? | >=70% of P0/P1 alerts reviewed are judged worth reviewing, or the failure causes are explicit. |
| Can the operator act fast enough? | Median daily operator time <=30 minutes and reply timing is recorded. |
| Does better timing improve distribution? | Published replies are compared with the pre-test account baseline; at least one clear distribution lift, profile/follower effect, or a clear falsification must be observable. |

A practical early proof point is at least one reply exceeding 100 impressions or producing a measurable profile/follower response during the seven-day test. This is a decision aid, not a guarantee of product-market fit.

If the system cannot produce qualified opportunities or the replies still receive no meaningful distribution, the next action is strategy/source/target correction, not more infrastructure.

## 6. Decision

`APPROVED`.

- Continue using `PACK-CHINA-TECH-X-RADAR-001`, updated to v1.1 MVP-first execution.
- The Mac mini fact audit may be executed directly through the available MCP bridge and does not require OPC dispatch.
- MomentGrid OPC is optional until business evidence justifies reconnecting the implementation/governance control plane.
- Docker/Colima repair is deferred because the MVP does not need containers.
- A web inbox and model scoring are deferred until operator friction or alert quality proves they are needed.
- The X API pilot remains blocked.

## 7. Re-entry Conditions for Deferred Infrastructure

### Add OPC when

- implementation work has become multi-step enough that autonomous delivery/review materially reduces human effort; or
- multiple runtime services, deployments, and recurring change-control operations create a demonstrated governance bottleneck.

### Repair/use TrendRadar container path when

- native free-source polling misses material signals that TrendRadar can demonstrably add; or
- its source-management capabilities reduce maintenance cost enough to justify repair.

### Add model scoring when

- deterministic filtering produces too many false positives or misses that cannot be solved by source/keyword tuning.

### Add direct X-native discovery when

- external signals are timely but target-post discovery is the measured bottleneck.

### Add a web UI when

- alert + simple evidence ledger becomes slower than the 30-minute human budget or materially harms data quality.
