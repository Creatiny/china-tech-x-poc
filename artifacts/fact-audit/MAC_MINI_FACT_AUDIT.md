# Mac mini Fact Audit — 2026-08-31

## Scope

Read-only or benign runtime inspection performed through MacDeveloperBridge MCP to determine which existing Mac mini capabilities are actually usable for the China Tech X business-validation MVP. No secret values are included.

Audit timestamp: `2026-08-31T08:48:35Z`

## Verified Host

- OS: macOS 26.5.2 (Build 25F84)
- Architecture: arm64
- RAM: 16 GB
- Root filesystem: 228 GiB logical volume; approximately 82 GiB reported available at audit time
- Shell: `/bin/zsh`

## Execution and Development Infrastructure

| Capability | Evidence state | Conclusion |
|---|---|---|
| MacDeveloperBridge | bridge v0.2.0 running; full-access unlock active | usable |
| Bridge autostart/tunnel | launchd jobs present; cloudflared tunnel and MCP HTTP/node processes running | usable |
| Git | 2.50.1 | usable |
| GitHub CLI | 2.92.0; authenticated to GitHub | usable |
| Node | 22.23.1 | usable |
| pnpm | 10.33.2 | usable |
| Python | Homebrew Python 3.14.7 and 3.12 available | usable |
| uv | 0.12.5 | usable |
| SQLite | system/Homebrew capability available | usable |
| launchd | multiple active user LaunchAgents | usable |
| Docker CLI | 29.4.3 installed | installed only |
| Colima | 0.10.1 installed; existing VM fails with `ha.sock connection refused` | not usable without repair |
| MLX | installed | available but not needed |
| mlx-lm | Homebrew 0.31.3_2 CLI installed | available but no China Tech model route verified |

## Existing Services Relevant to Reuse

### TrendRadar

- Install path: `/Users/jh/deyue/trendradar`
- Docker compose image: `wantcat/trendradar:latest`
- Output paths: `/Users/jh/deyue/trendradar/output/news` and `/Users/jh/deyue/trendradar/output/rss`
- Latest verified output inspected: `2026-08-30.db`
- 2026-08-30 news DB: 344 `news_items`
- 2026-08-30 RSS DB: 621 `rss_items`
- Historical launch schedule: 02:00, 06:00, 08:00, 22:00 Asia/Shanghai
- Last inspected launch log series ended 2026-08-27; the launchd label was not loaded during the audit
- Current source logs are largely Vietnam/Laos/general-news oriented and include multiple broken/timeout feeds
- The crawler script depends on Colima/Docker, which currently fails to start

Conclusion: **real asset, not currently suitable as the MVP runtime**. It may later be reused read-only or repaired if evidence shows it adds coverage.

### Horizon

No Horizon-specific project, process, launch agent, or useful installation was found. Name-search results were unrelated library/theme files.

Conclusion: `NOT_FOUND`; not an MVP dependency.

### Existing notification worker

LaunchAgent: `com.deyue.notification-outbox-worker`.

Observed state:

- last launch status indicates failure;
- configured command points to a missing Python file;
- configured sender is `dry-run`;
- repeated error log: target script file does not exist.

Conclusion: **not usable as a real alert channel**.

### Feishu capability

Secret-reference names found in local Deyue configuration:

- `FEISHU_API_BASE`
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_TENANT_ACCESS_TOKEN`

Presence check:

- API base: non-empty
- app ID: non-empty
- app secret: non-empty
- tenant token: missing/empty, but existing code can obtain one from app credentials
- no non-empty `FEISHU_TEST_RECEIVE_ID` or equivalent operator receive target was found

Conclusion: **application authentication appears provisionable, but end-user delivery is not yet verified**. One receive target/chat identity is the only known alert-channel blocker.

### Background Chrome

MacDeveloperBridge reports `CHROME_EXTENSION_OFFLINE`; ChatGPT extension status call also errored.

Conclusion: browser-assisted X resolution is not an MVP-ready dependency.

### GitHub Actions runner

An active self-hosted Actions runner exists under `/Users/jh/actions-runner/arbitrage-os` and is registered for the arbitrage project.

Conclusion: not assumed reusable by China Tech; launchd + direct local execution are cheaper for the MVP.

### MomentGrid OPC

`com.momentgrid.opc-dispatcher` is loaded and a dispatcher process was running from `/Users/jh/ops/momentgrid-runtime` during the audit.

Conclusion: technically present, but CP-002 makes OPC optional and non-blocking for China Tech business validation.

### Other running services

Unrelated services include OpenClaw gateway, Deyue APIs, arbitrage-os service, cloudflared/MacDeveloperBridge, and macOS system services. The China Tech MVP must avoid their occupied ports and data paths but does not depend on them.

Observed relevant occupied local ports included 18789, 18080, 18081, 8787, 8765, and 20241.

## GitHub Repository State

- Repository: `Creatiny/china-tech-x-poc`
- Visibility: public
- Default branch: `main`
- Main at audit start: `043f9e991c65c3da12499b4d0664beba2afd4e15`
- Local clone created: `/Users/jh/projects/china-tech-x-poc`
- No China Tech runtime source code existed at audit start; repository contained governance/requirements/architecture/packs/OPC documents only.

## Facts That Changed the Plan

1. Native Python + SQLite + launchd are healthy and sufficient for the first experiment.
2. Docker/Colima is unhealthy and unnecessary for the MVP.
3. TrendRadar has useful historical assets but is configured for another domain and currently depends on the broken container path.
4. Existing notification infrastructure cannot actually deliver; a small direct Feishu adapter is lower cost than repairing the Deyue outbox stack.
5. No verified browser/X-native resolver exists, so target discovery must begin human-assisted and be measured as a possible bottleneck.
6. OPC exists but was blocking business progress for reasons unrelated to the X growth hypothesis; it must remain optional until justified.

## Recommended Immediate Technical Action

Implement `PACK-CHINA-TECH-X-RADAR-001` v1.1 as a native Python/SQLite/launchd MVP with RSS/Atom + GitHub inputs, deterministic filtering, direct Feishu alerts, and a simple outcome ledger. Start the seven-day Shadow Test immediately after one real end-to-end mobile alert smoke passes.

## Command Families Used

The audit used only local inspection or benign runtime status commands, including:

- `sw_vers`, `uname`, `sysctl`, `df`
- `command -v`, tool version commands
- `ps`, `lsof`, `launchctl`, `plutil`
- `brew services`, `colima status/start`, `docker info/ps`
- filesystem discovery and SQLite metadata/count queries
- `gh repo view`, `gh api`, `gh auth status`
- MacDeveloperBridge status and Chrome workspace status

No secret values were printed into this artifact. The Colima start attempt failed and did not establish a working Docker runtime.
