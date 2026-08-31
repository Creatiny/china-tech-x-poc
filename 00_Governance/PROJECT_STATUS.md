# Project Status

## Status Timestamp

2026-08-31

## Current Phase

`BUSINESS_VALIDATION_FIRST / MAC_FACT_AUDIT_COMPLETE / MVP_BUILD_READY`

The prior `EXECUTION_BLOCKED` state caused by MomentGrid Stability Gate and external-pack intake is superseded by CP-002. OPC is no longer a prerequisite for the China Tech business experiment.

## Current Objective

Launch the smallest reliable signal -> mobile alert -> human reply -> outcome evidence loop on the Mac mini, then run seven consecutive valid days before adding infrastructure.

## Business Baseline

Latest Eden-connected provisional snapshot available before this correction:

- X account: `@KennyChinaTech`
- Followers: 4
- Tracked posts: 15
- Views: 396
- Likes: 2
- Comments: 0
- Shares: 0
- Total engagements: 2

Eden previously reported incomplete imports and Analytics inconsistencies, so this is a weak baseline. Native X-visible outcomes should be recorded during the experiment whenever available.

## Mac mini Fact Audit Summary

| Capability | Verified state | MVP decision |
|---|---|---|
| MacDeveloperBridge MCP | Running, full-access bridge available, launchd autostart present | Use for direct implementation/inspection when needed |
| Git / GitHub CLI | Available; GitHub account authenticated | Use |
| Python | 3.14.7 and 3.12 available; `uv` available | Use native Python |
| Node / pnpm | Node 22.23.1; pnpm 10.33.2 | Available but not required |
| SQLite | Available locally | Use |
| launchd | Available and already used by multiple services | Use for 5-minute polling |
| cloudflared | Installed; MCP tunnel running | Keep existing; not required in signal path |
| Docker / Colima | Installed; current Colima VM fails to start | Do not repair for MVP |
| TrendRadar | Installed; data exists through 2026-08-30; current source set is mostly Vietnam/Laos/general; no active launchd job after restart | Optional later; do not block MVP |
| Horizon | Not found | Ignore for MVP |
| Feishu | App ID/secret references exist; receive target not found/verified | Preferred alert path after receive target smoke test |
| Existing notification worker | Broken path and configured `dry-run` | Do not reuse as-is |
| Background Chrome automation | Offline | Do not block MVP; direct X resolver deferred |
| GitHub Actions runner | Repo-scoped runner exists for `arbitrage-os` | Do not reuse/assume |
| MLX / mlx-lm | Installed; no China Tech model route verified | Do not use in MVP |
| MomentGrid OPC | Dispatcher running on Mac | Optional; not an MVP dependency |

Detailed evidence: `artifacts/fact-audit/MAC_MINI_FACT_AUDIT.md`.

## Active Experiment

### EXP-001 — Zero-New-Spend Business Validation Shadow Test

Status: `READY_FOR_MVP_BUILD / SHADOW_CLOCK_NOT_STARTED`

The seven-day clock starts only after:

1. at least one live free source completes end-to-end ingestion;
2. exact dedupe works across repeated polls;
3. a real mobile-capable alert reaches the operator;
4. the operator decision/outcome ledger can be written;
5. paid-X and auto-publish guards are confirmed.

A web inbox, OPC, Docker, model scoring, Horizon, and direct X API access are not entry criteria.

## Active Pack

`03_Packs/PACK-CHINA-TECH-X-RADAR-001.md` v1.1 — `APPROVED / ACTIVE / MVP-FIRST`

The existing X API pilot remains `BLOCKED` with authorized spend `$0` and chargeable calls `0`.

## Current Known Gaps

1. No China Tech-specific runtime has yet been implemented in this repository.
2. No mobile receive target has been verified. Feishu application credentials exist, but the operator receive ID/chat ID/webhook is not present in the inspected configuration.
3. Direct X target-post discovery is not automated. The MVP may send a source link plus an X live-search link; only a verified direct target counts as an executable reply opportunity.
4. The current TrendRadar configuration is not China Tech-focused and its Docker/Colima runtime is unhealthy after restart.
5. The exact source allowlist and entity/topic rules still need to be tuned for China AI, semiconductors/AI infrastructure, robotics/hardware, EV/advanced manufacturing, and global-business impact.

## Next Executable Sequence

1. Implement one native Python `run_cycle` with RSS/Atom + GitHub adapters, SQLite exact dedupe, deterministic filtering, and structured logs.
2. Add a small China Tech source allowlist and entity/topic rules; do not attempt broad platform coverage yet.
3. Implement Feishu alert delivery behind configuration. If no valid receive target can be obtained from existing credentials, use one explicitly approved alternative mobile webhook rather than building a notification platform.
4. Add a one-command/manual decision and outcome recorder; no web UI yet.
5. Run a real end-to-end smoke: live source -> stored signal -> qualified alert -> mobile delivery -> manual decision record.
6. Start the seven-day Shadow Test immediately after the smoke passes.
7. At day seven, decide from evidence whether the next bottleneck is source coverage, direct X target discovery, scoring quality, operator workflow, or account/content strategy.
8. Only then decide whether to repair TrendRadar/Colima, add model scoring, add a web inbox, use Eden more heavily, pilot paid X-native data, or reconnect OPC.

## Stop Gates

The current MVP stops for human input only when it needs:

- a requirement or architecture boundary change;
- paid spend or a chargeable API;
- automatic publishing authority;
- a missing account secret/receiver identity that cannot be derived safely;
- a destructive/irreversible external action;
- a material platform-policy ambiguity.

MomentGrid/OPC availability is explicitly not a stop gate for the business experiment.
