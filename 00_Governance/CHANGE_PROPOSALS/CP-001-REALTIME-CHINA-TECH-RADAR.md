# CP-001 — Realtime China Tech Radar

## Metadata

- Status: `APPROVED`
- Decision date: `2026-08-30`
- Decision authority: Human product owner
- Supersedes: Eden-only / quota-led daily operating assumptions
- Implements through:
  - `REQ-CHINA-TECH-X-RADAR-001`
  - `ARCH-CHINA-TECH-X-RADAR-001`
  - `PACK-CHINA-TECH-X-RADAR-001`
- Deferred paid extension:
  - `PACK-CHINA-TECH-X-XAPI-PILOT-001`

## 1. Problem

The initial operating design relied too heavily on Eden and a fixed daily publishing routine. It optimized content generation and memory before verifying the capabilities that matter most for a new China Tech X account:

- broad and timely China Tech signal discovery;
- detection of X conversations while they are still early;
- identification of a specific high-leverage post to reply to;
- immediate notification outside email;
- feedback that separates source quality, timing, target selection, and writing quality.

The current canonical runbook also requires at least one original post and two replies each day. This can force low-quality or late publishing and does not directly test the growth hypothesis.

Observed account results are insufficient to justify continuing the same architecture as the sole operating method. Eden has also shown X import and Analytics inconsistencies and unexplained credit consumption during the initial evaluation.

## 2. Expected Benefit

The proposed change creates an opportunity-led operating system:

- diversified China Tech coverage through Horizon, TrendRadar, RSS, and GitHub;
- Eden retained where it is strongest: research, creator intelligence, memory, and retrospective analysis;
- a canonical signal store with provenance;
- cross-source deduplication and event clustering;
- deterministic filtering before model use;
- explicit P0/P1/P2 opportunity scoring;
- timely mobile alerts with source and target links;
- human feedback on posted, skipped, expired, and false-positive opportunities;
- outcome measurement against the original account baseline;
- an evidence gate before any paid X API pilot.

This changes the core question from “Did we post today?” to “Did we identify and act on a qualified distribution opportunity?”

## 3. Cost

### Phase A — Foundation Radar

- New mandatory software spend: `$0`
- Uses existing Mac mini, existing subscriptions, open-source collectors, existing model routing where available, and current notification infrastructure if verified.
- Engineering cost: implementation and validation through the existing MomentGrid OPC control plane.
- Human operating budget: no more than 30 minutes per day.

### Phase B — X API Pilot

- Status: blocked.
- Indicative pilot ceiling after separate approval: 3,000 unique public-post reads and approximately `$15` maximum X data spend.
- No amount is authorized by this proposal.

## 4. Test Method

Run a seven-consecutive-day Shadow Test after the foundation radar reaches runtime readiness.

The system must record:

- source health and collection intervals;
- raw and deduplicated signal counts;
- canonical event clusters;
- alert timestamp, source publish timestamp, and target-post timestamp;
- opportunity score and rationale;
- operator decision;
- false-positive and expiry reasons;
- time spent by the operator;
- available account outcomes.

The Shadow Test uses no paid X API.

## 5. Success Criteria

Foundation Radar is eligible for acceptance when all critical criteria pass:

| Criterion | Threshold |
|---|---:|
| Valid Shadow Test duration | 7 consecutive days |
| Daily deduplicated, relevant China Tech signals | At least 20 on 5 of 7 days, or an evidence-backed lower-volume explanation |
| Daily executable reply opportunities | 2–5 target range; median at least 2 on active-news days |
| Alerts judged worth reviewing | At least 70% |
| Alerts with traceable source and direct target link | 100% |
| P0 external-signal discovery delay | Target ≤10 minutes; all misses measured |
| Operator time | Median ≤30 minutes/day |
| Unobserved full-service outage | 0 |
| Paid X API cost | `$0` |
| Automated publishing | 0 |

A lower signal volume does not automatically fail if the system proves high precision and the market was objectively quiet; the verifier must document evidence rather than invent volume.

## 6. Decision

`APPROVED`.

Execute `PACK-CHINA-TECH-X-RADAR-001` through the existing MomentGrid OPC control plane.

`PACK-CHINA-TECH-X-XAPI-PILOT-001` is created for design continuity but remains `BLOCKED`. It may be unblocked only after:

1. the seven-day Shadow Test completes;
2. evidence identifies an X-native discovery gap;
3. expected read volume and cost are calculated from actual events;
4. the human owner approves an exact monetary ceiling;
5. chargeable use has an automatic hard stop.

## Rejected or Deferred Alternatives

### Eden as the sole core system

Rejected. Eden remains useful but does not cover the entire required realtime opportunity chain.

### Immediate paid X API rollout

Deferred. It would repeat the error of buying capability before proving the exact gap and unit economics.

### Copying MomentGrid OPC into this repository

Rejected. The existing OPC is referenced as the control plane; this repository contains only domain requirements, architecture, packs, runtime code, and a thin adapter.

### Automatic post or reply publishing

Blocked. Manual publishing remains a hard boundary.
