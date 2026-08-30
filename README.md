# China Tech X POC

## Purpose

This repository is the canonical governance, product definition, and operating system for the China Tech X POC.

## North Star

Validate whether one person, using AI-assisted workflows and a timely China Tech signal radar, can build and monetize an English-language X account focused on China technology within 30 days.

## Current Strategy

The POC is now opportunity-led rather than quota-led:

1. Discover high-value China Tech signals early.
2. Identify time-sensitive X reply opportunities.
3. Deliver actionable alerts within the user's 30-minute daily operating budget.
4. Publish manually and measure outcomes.
5. Improve source, scoring, and response strategy from evidence.

There is no mandatory daily original-post quota. Original posts are created only when the account has a timely signal, unique evidence, or a differentiated thesis.

## System Roles

- **Horizon, TrendRadar, RSS, and GitHub**: foundation information sources.
- **Eden**: research, creator intelligence, memory, and retrospective analysis layer; not the sole real-time discovery system.
- **China Tech Radar**: normalization, deduplication, clustering, opportunity scoring, alerting, feedback, and outcome tracking.
- **MomentGrid OPC (`Creatiny/momentgrid`)**: control plane for implementation, verification, deployment governance, budget gates, and reviews. OPC is referenced, not copied into this repository.
- **Human operator**: final publishing authority for posts and replies.

## Active Packs

- [`PACK-CHINA-TECH-X-RADAR-001`](03_Packs/PACK-CHINA-TECH-X-RADAR-001.md) — **APPROVED / ACTIVE**
- [`PACK-CHINA-TECH-X-XAPI-PILOT-001`](03_Packs/PACK-CHINA-TECH-X-XAPI-PILOT-001.md) — **BLOCKED**

## Hard Boundaries

- No paid X API purchase or paid X API call before the 7-day Shadow Test is complete and an explicit budget Human Gate is approved.
- No automatic X post or reply publishing.
- The first execution action is a fact-only Mac mini audit. Horizon, TrendRadar, runners, credentials, and notification channels must not be assumed.
- Ordinary implementation, testing, bug fixes, technical PRs, and merges do not require repeated human approval unless they change requirements, architecture, paid spend, publishing authority, or another irreversible external boundary.

All execution must follow `00_Governance/POC_CONSTITUTION.md`, `00_Governance/CHANGE_CONTROL.md`, and the approved pack.
