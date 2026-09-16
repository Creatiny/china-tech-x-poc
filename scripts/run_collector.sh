#!/bin/zsh
set -euo pipefail
ROOT="${CHINA_TECH_RADAR_ROOT:-/Users/jh/services/china-tech-x-radar}"
if [[ -f "$HOME/.china-tech-x-radar.env" ]]; then
  set -a
  source "$HOME/.china-tech-x-radar.env"
  set +a
fi
export CHINA_TECH_RADAR_ROOT="$ROOT"
CANONICAL_DB="$ROOT/runtime/china-tech-x.db"
# Production state is single-writer/single-database. Refuse an env override that would fork runtime state.
if [[ "$ROOT" == "/Users/jh/services/china-tech-x-radar" && -n "${CHINA_TECH_RADAR_DB:-}" && "$CHINA_TECH_RADAR_DB" != "$CANONICAL_DB" ]]; then
  print -u2 "refusing_noncanonical_production_db:$CHINA_TECH_RADAR_DB expected:$CANONICAL_DB"
  exit 78
fi
export CHINA_TECH_RADAR_DB="${CHINA_TECH_RADAR_DB:-$CANONICAL_DB}"
# X and other external discovery are not directly reachable from this host; keep the project proxy explicit.
export CHINA_TECH_HTTP_PROXY="${CHINA_TECH_HTTP_PROXY:-http://127.0.0.1:7890}"
exec "$ROOT/.venv/bin/china-tech-x-radar" run --no-send
