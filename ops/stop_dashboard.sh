#!/usr/bin/env bash
set -euo pipefail
SCREEN_NAME=${XAMS_DASH_SCREEN_NAME:-xams_dashboard}
screen -S "$SCREEN_NAME" -X quit || true
echo "Stopped dashboard screen '$SCREEN_NAME'"
