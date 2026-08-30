# OPC-CTXR-001 — Mac mini Fact Audit

## Status

`READY_FOR_DISPATCH` after the canonical sync is merged to `main`.

## Control Plane

Existing MomentGrid OPC in `Creatiny/momentgrid`.

## Delivery Repository

`Creatiny/china-tech-x-poc`

## Governing Pack

`03_Packs/PACK-CHINA-TECH-X-RADAR-001.md`

## Canonical Binding

The dispatcher must replace the placeholders below after merge and before execution:

```text
TARGET_CANONICAL_COMMIT=<exact main commit>
PACK_SHA256=<sha256 of exact pack bytes at TARGET_CANONICAL_COMMIT>
```

The issue or dispatch payload is not authoritative. The agent must read the exact target canonical commit before acting.

## Objective

Establish the verified Mac mini execution and source state without assuming that Horizon, TrendRadar, a runner, a checkout, notification credentials, or any service is present.

## Allowed Actions

- read-only system and repository inspection;
- controlled benign command execution;
- process/service/status inspection;
- configuration-key and secret-reference-name inspection without secret values;
- file and directory metadata inspection;
- local database metadata and latest-record-time inspection without destructive writes;
- runner/agent health inspection;
- evidence artifact creation and commit.

## Prohibited Actions During the Audit

- paid API call;
- package or service installation before the initial fact report is complete;
- secret-value output;
- source database modification;
- service deletion;
- port or firewall change;
- automatic X publishing;
- claiming a tool exists based only on past conversation.

## Required Evidence Fields

```text
AUDIT_TIMESTAMP_UTC
MAC_HOST_ID_REDACTED
OS_VERSION
CPU_ARCH
AVAILABLE_DISK
PROJECT_ROOTS
CHINA_TECH_REPO_STATE
MOMENTGRID_OPC_PATH
MOMENTGRID_OPC_HEALTH
EXECUTION_PATH
RUNNER_OR_AGENT_STATUS
HORIZON_STATUS
HORIZON_VERSION
HORIZON_PATH
HORIZON_PROCESS
HORIZON_DATA_PATH
HORIZON_LATEST_DATA_AT
HORIZON_AUTOSTART
TRENDRADAR_STATUS
TRENDRADAR_VERSION
TRENDRADAR_PATH
TRENDRADAR_PROCESS
TRENDRADAR_DATA_PATH
TRENDRADAR_LATEST_DATA_AT
TRENDRADAR_AUTOSTART
DOCKER_OR_PODMAN
PYTHON_UV
NODE_BUN
CRON
LAUNCHD
NOTIFICATION_CHANNELS
SECRET_REFERENCE_NAMES
MODEL_ROUTE_NAMES
PORTS_IN_USE
BACKUP_CONSTRAINTS
BLOCKERS
RECOMMENDED_NEXT_TECHNICAL_ACTION
```

Use `NOT_FOUND`, `NOT_RUNNING`, or `UNKNOWN_WITH_REASON` rather than guessing.

## Deliverables

- `artifacts/fact-audit/MAC_MINI_FACT_AUDIT.json`
- `artifacts/fact-audit/MAC_MINI_FACT_AUDIT.md`
- command transcript with secret redaction
- evidence manifest containing hashes
- next technical slice recommendation

## Completion

The task is complete when an independent verifier confirms that:

- every required field is populated or has a reason;
- reported tools/processes have evidence;
- no secret value is present;
- no paid or publishing action occurred;
- the next action is derived from facts.

After this task passes, OPC continues directly with the next technical slice of the active pack unless a mandatory stop gate is encountered.
