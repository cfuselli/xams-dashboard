#!/usr/bin/env bash
set -euo pipefail
SCREEN_NAME=${XAMS_DASH_V2_SCREEN_NAME:-xams_dashboard_v2}
screen -S "$SCREEN_NAME" -X quit >/dev/null 2>&1 || true
echo "Stopped $SCREEN_NAME"
