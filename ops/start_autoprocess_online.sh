#!/usr/bin/env bash
set -euo pipefail

SCREEN_NAME=${XAMS_AUTOPROC_SCREEN_NAME:-xams_auto_processing_online}
AMSTRAX_DIR=${XAMS_STBC_AMSTRAX_DIR:-/data/xenon/xams_v2/software/amstrax/amstrax/auto_processing_new}
TARGET=${XAMS_AUTOPROC_TARGET:-raw_records}
ENV_ACTIVATE=${XAMS_DASH_ENV_ACTIVATE:-"source /data/xenon/xams_v2/setup.sh"}

screen -S "$SCREEN_NAME" -X quit || true
screen -S "$SCREEN_NAME" -dm bash -lc "cd '$AMSTRAX_DIR' && $ENV_ACTIVATE && python auto_processing.py --target '$TARGET' --production"

echo "Started auto_processing screen '$SCREEN_NAME' target=$TARGET"
