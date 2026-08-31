#!/bin/zsh
set -euo pipefail
ROOT="${CHINA_TECH_RADAR_ROOT:-/Users/jh/services/china-tech-x-radar}"
# Reuse existing authorized Feishu app credentials without copying secret values.
if [[ -f /Users/jh/.deyue/approval-p0d-real-spike.env ]]; then
  set -a
  source /Users/jh/.deyue/approval-p0d-real-spike.env
  set +a
  export CHINA_TECH_FEISHU_RECEIVE_ID="${CHINA_TECH_FEISHU_RECEIVE_ID:-${DEYUE_APPROVAL_SPIKE_OPERATOR_ID:-}}"
  export CHINA_TECH_FEISHU_RECEIVE_ID_TYPE="${CHINA_TECH_FEISHU_RECEIVE_ID_TYPE:-open_id}"
fi
export CHINA_TECH_RADAR_ROOT="$ROOT"
export CHINA_TECH_RADAR_DB="${CHINA_TECH_RADAR_DB:-$ROOT/runtime/china-tech-x.db}"
exec "$ROOT/.venv/bin/china-tech-x-radar" run
