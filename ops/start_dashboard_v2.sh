#!/usr/bin/env bash
set -euo pipefail
SCREEN_NAME=${XAMS_DASH_V2_SCREEN_NAME:-xams_dashboard_v2}
PORT=${XAMS_DASH_V2_PORT:-8070}
APP_DIR=${XAMS_DASH_APP_DIR:-$HOME/xams-dashboard}
screen -S "$SCREEN_NAME" -X quit >/dev/null 2>&1 || true
screen -S "$SCREEN_NAME" -dm bash -lc "source /data/xenon/xams_v2/setup.sh && export XAMS_CONFIG_FILE=~/.xams_config && cd '$APP_DIR' && python -m v2.app"
echo "Started $SCREEN_NAME on 127.0.0.1:${PORT}"
