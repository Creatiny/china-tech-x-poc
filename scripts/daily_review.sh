#!/bin/zsh
set -euo pipefail
ROOT="${CHINA_TECH_RADAR_ROOT:-/Users/jh/services/china-tech-x-radar}"
if [[ -f "$HOME/.china-tech-x-radar.env" ]]; then
  set -a
  source "$HOME/.china-tech-x-radar.env"
  set +a
fi
export CHINA_TECH_RADAR_ROOT="$ROOT"
export CHINA_TECH_RADAR_DB="${CHINA_TECH_RADAR_DB:-$ROOT/runtime/china-tech-x.db}"
if [[ "${CHINA_TECH_ALERTS_ENABLED:-0}" == "1" ]]; then
  exec "$ROOT/.venv/bin/china-tech-x-radar" review --notify --output-dir "$ROOT/runtime/reviews"
else
  exec "$ROOT/.venv/bin/china-tech-x-radar" review --output-dir "$ROOT/runtime/reviews"
fi
