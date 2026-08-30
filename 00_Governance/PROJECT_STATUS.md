# Project Status

## Status Timestamp

2026-08-30

## Current Phase

Canonical Radar Pack is active; external OPC intake is accepted but runtime execution is blocked by the current MomentGrid Stability Gate and repository-local mission authority.

## Current Objective

Build and validate a source-diverse, time-sensitive China Tech opportunity radar that reliably produces actionable X reply opportunities while keeping daily human operation within 30 minutes.

## Verified Baseline

Latest Eden-connected account snapshot available during the strategy review:

- X account: `@KennyChinaTech`
- Followers: 4
- Tracked posts: 15
- Views: 396
- Likes: 2
- Comments: 0
- Shares: 0
- Total engagements: 2

Data-quality caveat: Eden previously reported incomplete X imports and Analytics inconsistencies. This snapshot is a provisional baseline, not a complete source of truth.

## Canonical and OPC Binding

- Canonical Radar strategy merged to `main`: `d5f6b41182aff0dc927c5f47c886d3d90f95a86d`.
- Active pack: `03_Packs/PACK-CHINA-TECH-X-RADAR-001.md`.
- Active pack SHA-256 at that commit: `b0a8585eb64dd953dd1e533ffe241011b7bf9eb5543ab32175e3784e41453f43`.
- MomentGrid intake: `Creatiny/momentgrid#121`.
- Intake state: `ACCEPTED / EXECUTION_BLOCKED`.
- Mac mini fact audit state: `NOT_DISPATCHED`.
- Paid X API spend: `$0`.
- Chargeable X API requests: `0`.
- Automatic X publishing: disabled.

The existing MomentGrid Command Bus and trusted Mac execution path were independently proven responsive by a focused stability-repair mission (`Creatiny/momentgrid#123`), which received real `ACKED` and `RUNNING` receipts. Its generated Plan Gate was bound to the wrong legacy Delivery Loop authority and omitted part of the requested file scope, so the gate was rejected fail-closed and the run completed as cancelled. No writer, verifier, repository mutation, Radar task, or Mac mini fact audit was executed by that rejected run.

## Active Experiment

### EXP-001 — Zero-New-Spend China Tech Radar Shadow Test

Status: `BLOCKED_BEFORE_BUILD`

Execution pack: `PACK-CHINA-TECH-X-RADAR-001`

Planned test sequence:

1. Mac mini fact audit.
2. Foundation-source ingestion and normalization.
3. Deduplication and event clustering.
4. Opportunity scoring and alert delivery.
5. Human feedback and outcome capture.
6. Seven consecutive days of Shadow Test evidence.
7. Recommendation on whether the blocked X API pilot is justified.

The Shadow Test has not started. Its seven-day clock must not begin until runtime readiness and notification delivery are verified.

## Pack Status

| Pack | Status | Execution |
|---|---|---|
| `PACK-CHINA-TECH-X-RADAR-001` | `APPROVED / ACTIVE` | Canonical and accepted by the OPC intake; execution is blocked before the first Mac audit |
| `PACK-CHINA-TECH-X-XAPI-PILOT-001` | `BLOCKED` | No purchase, chargeable request, credential setup that creates spend, or live stream connection |

## Decisions

- Eden is retained as a Research/Memory Layer, not the sole discovery or realtime-growth system.
- Horizon, TrendRadar, RSS, and GitHub are the foundation information-source classes.
- Reply opportunity quality and timeliness take priority over mandatory output quotas.
- Original posts are conditional; no daily original-post minimum remains.
- Existing MomentGrid OPC is the control plane; no OPC copy is created in this repository.
- Radar runtime remains an independent data plane so monitoring does not stop when the OPC control plane is unavailable.
- Human publishing remains mandatory.
- Paid X API activity remains blocked until a separate evidence-backed budget gate.
- An external-pack adapter must not be silently added while MomentGrid's architecture freeze remains active; it requires the existing Stability Gate to pass or a separate explicit architecture decision.

## Current Blockers

1. MomentGrid's current mission runtime, authority reader, worktrees, verifier, and promoter are scoped to the `Creatiny/momentgrid` checkout. They cannot yet safely consume and mutate an exact pack from `Creatiny/china-tech-x-poc`.
2. The current mission-to-Delivery compatibility adapter generated a Plan Gate with legacy `PACK-OPC-DELIVERY-LOOP-001` source references instead of the focused Stability authority. This gate-integrity defect was rejected rather than approved.
3. MomentGrid remains under its Stability Gate / architecture-freeze decision. The known deterministic verifier-environment defect must be repaired and the Stability Pack completed before adding a nonessential external-repository control-plane adapter, unless the owner explicitly changes that architecture decision.
4. Because the first Mac audit has not run, Horizon, TrendRadar, runner/agent paths, notification credentials, services, data paths, and model routes remain unverified.

## Next Executable Sequence

1. Repair and verify the existing MomentGrid deterministic verifier environment under its current Stability requirements.
2. Complete or explicitly change the MomentGrid Stability Gate decision.
3. Implement and independently verify a minimal exact-commit/exact-pack-hash external-pack intake adapter without arbitrary remote shell access.
4. Re-read the latest China Tech canonical and supersede the intake if its commit or active-pack hash changed.
5. Dispatch `OPC-CTXR-001 — Mac mini Fact Audit` first and require real Command Bus `ACKED` plus `RUNNING` or terminal evidence.
6. Continue the active Radar pack only after the fact audit establishes the actual Mac mini state.

Until step 5 occurs, the accurate status is: PACK written and active, OPC intake accepted, Mac mini Radar execution not started.
