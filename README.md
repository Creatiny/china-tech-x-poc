# China Tech X POC

## Purpose

This repository is the canonical product, experiment, and operating definition for the China Tech X POC.

## Single Source of Truth

`PROJECT_SPEC.md` v2.0 is the top-level product and operating authority. `00_Governance/CANONICAL_INDEX.md` defines document precedence.

## North Star

Build a large, relevant English-language China Tech audience on X, discover the repeatable follower-growth formula, then monetize audience leverage through aligned commercial cooperation and platform/affiliate/owned-media opportunities. During the current POC, **relevant follower growth is the primary business KPI**.

## Current Priority — Business Validation First

The current execution order is deliberately minimal:

1. discover timely, relevant China Tech signals;
2. alert the operator quickly on a mobile-capable channel;
3. turn the best signals into timely human-published replies or occasional original posts;
4. record distribution outcomes and follower/profile effects;
5. only add infrastructure when evidence identifies a real bottleneck.

A business experiment must not wait for OPC integration, Docker repair, a web inbox, local-model deployment, or a generalized agent platform when those capabilities are not required to test the growth hypothesis.

## Current MVP Runtime

The approved pre-validation architecture is:

```text
Free RSS/Atom + GitHub + verified free sources
                    |
                    v
         Python polling cycle (5 min)
                    |
                    v
            SQLite + exact dedupe
                    |
                    v
       deterministic relevance rules
                    |
                    v
         mobile-capable alert channel
                    |
                    v
      human X search / reply / publish
                    |
                    v
          outcome evidence ledger
```

No Docker, model API, web UI, or OPC is required for this MVP.

## Verified Mac mini Baseline — 2026-08-31

- macOS 26.5.2, Apple Silicon, 16 GB RAM.
- GitHub CLI, Node 22, pnpm, Python 3.14/3.12, `uv`, SQLite, launchd, cloudflared, and MacDeveloperBridge are available.
- Docker and Colima are installed, but the existing Colima VM currently fails to start. They are not an MVP dependency.
- TrendRadar is installed and produced data through 2026-08-30, but its current source configuration is primarily Vietnam/Laos/general-news oriented and its launch path is not currently active after restart. It is an optional reusable asset, not the MVP foundation.
- Horizon was not found.
- Personal Feishu delivery has been human-verified and is the only authorized China Tech production alert path; group delivery is prohibited.
- Background Chrome automation is currently offline.
- A self-hosted GitHub Actions runner exists for `Creatiny/arbitrage-os`; it is not assumed to be reusable by this repository.
- MomentGrid OPC is running on the Mac, but it is not required to start or continue the business-validation experiment.

See `artifacts/fact-audit/MAC_MINI_FACT_AUDIT.md` for evidence.

## Active Canonical

- Single source of truth: `PROJECT_SPEC.md` v2.0
- Execution plan: `EXECUTION_PLAN.md` v1.0
- Canonical precedence: `00_Governance/CANONICAL_INDEX.md`
- KPI: `00_Governance/OPERATING_KPI.md` v3.0
- Growth formula: `00_Governance/GROWTH_FORMULA.md` v1.0
- Constitution: `00_Governance/POC_CONSTITUTION.md`
- Current status: `00_Governance/PROJECT_STATUS.md`
- Business-first correction: `00_Governance/CHANGE_PROPOSALS/CP-002-BUSINESS-VALIDATION-FIRST.md`
- Requirement: `01_Requirements/REQ-CHINA-TECH-X-RADAR-001.md` v1.2
- Architecture: `02_Architecture/ARCH-CHINA-TECH-X-RADAR-001.md` v1.2
- Active pack: `03_Packs/PACK-CHINA-TECH-X-RADAR-001.md` v1.2 — `APPROVED / ACTIVE / MVP-FIRST`
- Paid X API pack: `03_Packs/PACK-CHINA-TECH-X-XAPI-PILOT-001.md` — `BLOCKED`

## Hard Boundaries

- No paid X API call or purchase without an explicit evidence-backed budget gate.
- No automatic X post, reply, or DM publishing.
- No secret values in Git, logs, issues, or evidence.
- No new infrastructure dependency may be introduced merely because it is technically attractive.
- OPC integration is optional before business validation and may not block the signal-to-publish loop.
- Human publishing remains the final authority.

All execution follows the Constitution, Change Control, current Project Status, and the active pack.

## Native MVP Commands

The current runtime is standard-library Python + SQLite and is intentionally independent of OPC/Docker.

```bash
python -m venv .venv
.venv/bin/pip install -e .
china-tech-x-radar run
china-tech-x-radar list
china-tech-x-radar decide <signal-id> POSTED --worth yes --target-url <x-target> --published-url <your-x-post>
china-tech-x-radar outcome --published-url <your-x-post> --impressions 123 --engagements 4
china-tech-x-radar account-snapshot --followers 5 --profile-visits 2
china-tech-x-radar ops-time --minutes 24
china-tech-x-radar review --notify
```

Production Mac launchd definitions live under `deploy/`. KPI authority is `00_Governance/OPERATING_KPI.md`.
