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
# X and other external discovery are not directly reachable from this host; keep the project proxy explicit.
export CHINA_TECH_HTTP_PROXY="${CHINA_TECH_HTTP_PROXY:-http://127.0.0.1:7890}"
exec "$ROOT/.venv/bin/china-tech-x-radar" run --no-send
