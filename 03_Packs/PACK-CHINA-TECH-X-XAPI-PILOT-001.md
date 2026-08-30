# PACK-CHINA-TECH-X-XAPI-PILOT-001

## Pack Header

- Status: `BLOCKED`
- Priority: `DEFERRED`
- Created: `2026-08-30`
- Requirement dependency: `REQ-CHINA-TECH-X-RADAR-001`
- Architecture dependency: `ARCH-CHINA-TECH-X-RADAR-001`
- Control plane: existing MomentGrid OPC
- Authorized spend: `$0`
- Authorized chargeable requests: `0`

## 1. Purpose

Define, but do not execute, a tightly bounded X-native realtime data pilot that may be used only if the foundation radar's seven-day evidence proves a material X discovery gap.

## 2. Block Conditions

This pack remains blocked until every condition is satisfied:

1. `PACK-CHINA-TECH-X-RADAR-001` completes its seven-day Shadow Test.
2. The verifier identifies specific qualified opportunities missed or materially delayed without X-native data.
3. The proposed fixed account and keyword rules are derived from actual evidence.
4. Expected daily and total unique-post volume is calculated.
5. The human owner approves an exact monetary cap.
6. An X developer project/app and required permissions are verified.
7. Automatic usage measurement and shutdown are tested without chargeable traffic where possible.
8. Auto top-up is disabled.
9. No automatic publishing authority is introduced.

No prior discussion, indicative estimate, subscription, or account connection unblocks this pack.

## 3. Indicative Pilot Boundary — Not Yet Authorized

These values are design ceilings only:

- Test duration: 7 days.
- Unique public-post reads: maximum 3,000.
- Indicative data cost: maximum approximately `$15`.
- Fixed Tier-0 accounts: evidence-selected subset.
- Dynamic event rules: TTL 30–120 minutes.
- Publishing: manual only.

The Human Budget Gate may approve lower values. It may not be inferred.

## 4. Planned Components

- `x-stream-worker` using the official permitted realtime/read interface available to the approved X account;
- fixed account rules;
- dynamic event rules created from high-confidence external events;
- rule TTL and automatic deletion;
- usage reconciler;
- hard post-count stop;
- hard monetary stop;
- disconnect and rule cleanup;
- cost-per-qualified-opportunity report.

## 5. Planned Acceptance Criteria

| Criterion | Planned threshold |
|---|---:|
| Processing delay after a matched post | ≤30 seconds |
| Pilot unique public-post reads | ≤ approved ceiling and never above 3,000 |
| Pilot spend | ≤ exact approved ceiling and never above approximately `$15` |
| Auto top-up | Disabled |
| Budget-limit shutdown | Pass |
| Chargeable request ledger | 100% reconciled |
| Incremental qualified opportunities | Must be measurable |
| Automatic publishing | 0 |

## 6. Abort Conditions

Immediately stop, remove dynamic rules, and disconnect when:

- post or monetary ceiling is reached;
- usage cannot be reconciled;
- duplicate billing/reads cannot be understood;
- source terms or app permissions change materially;
- alert quality is below the approved continuation threshold;
- a secret is exposed;
- the human owner revokes the pilot.

## 7. Unblock Record

This section must be completed by a future Human Budget Gate:

```text
Shadow Test verifier:
Evidence commit:
Identified X-native gap:
Approved unique-post ceiling:
Approved monetary ceiling:
Approved start/end date:
Auto-top-up verified disabled:
Human approval record:
Decision: BLOCKED / APPROVED
```

Until completed, all implementation and execution that could create paid X usage is prohibited.
