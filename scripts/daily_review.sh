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
if [[ "${CHINA_TECH_ALERTS_ENABLED:-0}" == "1" ]]; then
  exec "$ROOT/.venv/bin/china-tech-x-radar" review --notify --output-dir "$ROOT/runtime/reviews"
else
  exec "$ROOT/.venv/bin/china-tech-x-radar" review --output-dir "$ROOT/runtime/reviews"
fi
