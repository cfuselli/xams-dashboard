#!/usr/bin/env bash
set -euo pipefail

SCREEN_NAME=${XAMS_DASH_SCREEN_NAME:-xams_dashboard}
APP_DIR=${XAMS_DASH_APP_DIR:-$HOME/xams-dashboard}
HOST=${XAMS_DASH_HOST:-127.0.0.1}
PORT=${XAMS_DASH_PORT:-8050}
ENV_ACTIVATE=${XAMS_DASH_ENV_ACTIVATE:-"source /data/xenon/xams_v2/setup.sh"}

screen -S "$SCREEN_NAME" -X quit || true
screen -S "$SCREEN_NAME" -dm bash -lc "cd '$APP_DIR' && $ENV_ACTIVATE && export XAMS_DASH_HOST='$HOST' XAMS_DASH_PORT='$PORT' && python -m app.main"

echo "Started dashboard screen '$SCREEN_NAME' on ${HOST}:${PORT}"
