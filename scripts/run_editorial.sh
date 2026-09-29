#!/bin/zsh
set -euo pipefail
ROOT="${CHINA_TECH_RADAR_ROOT:-/Users/jh/services/china-tech-x-radar}"
if [[ -f "$HOME/.china-tech-x-radar.env" ]]; then
  set -a
  source "$HOME/.china-tech-x-radar.env"
  set +a
fi
export CHINA_TECH_RADAR_ROOT="$ROOT"
# launchd may provide an empty/minimal PATH. Homebrew Codex is a Node entrypoint,
# so both codex and node must be resolvable.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
CANONICAL_DB="$ROOT/runtime/china-tech-x.db"
# Production state is single-writer/single-database. Refuse an env override that would fork runtime state.
if [[ "$ROOT" == "/Users/jh/services/china-tech-x-radar" && -n "${CHINA_TECH_RADAR_DB:-}" && "$CHINA_TECH_RADAR_DB" != "$CANONICAL_DB" ]]; then
  print -u2 "refusing_noncanonical_production_db:$CHINA_TECH_RADAR_DB expected:$CANONICAL_DB"
  exit 78
fi
export CHINA_TECH_RADAR_DB="${CHINA_TECH_RADAR_DB:-$CANONICAL_DB}"
if [[ "${CHINA_TECH_ALERTS_ENABLED:-0}" != "1" || "${CHINA_TECH_FORCE_NO_SEND:-0}" == "1" ]]; then
  print '{"editorial":"disabled"}'
  exit 0
fi
exec "$ROOT/.venv/bin/china-tech-x-radar" editorial
