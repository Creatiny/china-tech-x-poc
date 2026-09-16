#!/bin/zsh
set -euo pipefail
ROOT="${CHINA_TECH_RADAR_ROOT:-/Users/jh/services/china-tech-x-radar}"
# Delivery configuration is local-only because Feishu open_id/chat_id values are app-scoped.
# Never infer a recipient by mixing IDs and credentials from different Feishu applications.
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
if [[ "${CHINA_TECH_FORCE_NO_SEND:-0}" == "1" ]]; then
  exec "$ROOT/.venv/bin/china-tech-x-radar" run --no-send
elif [[ "${CHINA_TECH_ALERTS_ENABLED:-0}" == "1" ]]; then
  exec "$ROOT/.venv/bin/china-tech-x-radar" run
else
  exec "$ROOT/.venv/bin/china-tech-x-radar" run --no-send
fi
