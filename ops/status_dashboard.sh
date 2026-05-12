#!/usr/bin/env bash
set -euo pipefail
SCREEN_NAME=${XAMS_DASH_SCREEN_NAME:-xams_dashboard}
screen -ls | grep "$SCREEN_NAME" || echo "Screen '$SCREEN_NAME' not running"
