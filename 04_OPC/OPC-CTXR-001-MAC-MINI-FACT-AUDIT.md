# OPC-CTXR-001 — Mac mini Fact Audit

## Status

`COMPLETE_OUTSIDE_OPC` on 2026-08-31.

CP-002 removed OPC dispatch as a prerequisite for the business-validation experiment. The same fact-audit objective was completed directly through the verified MacDeveloperBridge MCP path.

## Evidence

- `artifacts/fact-audit/MAC_MINI_FACT_AUDIT.md`
- `artifacts/fact-audit/MAC_MINI_FACT_AUDIT.json`

## Key Result

The Mac mini has enough native infrastructure to run the MVP with Python + SQLite + launchd. The audit also proved that several previously assumed dependencies are not currently healthy or suitable:

- Colima fails to start;
- TrendRadar is installed but is not currently an active China Tech-specific runtime;
- Horizon was not found;
- the existing Deyue notification worker is broken and dry-run;
- Feishu has app credential references but no verified receive target;
- background Chrome automation is offline.

None of these findings blocks native MVP implementation except the need to verify one real mobile receive target before the Shadow Test starts.

## OPC Re-entry

A future OPC dispatch may reuse the evidence from this task. Repeating the audit is unnecessary unless the infrastructure facts materially change.
