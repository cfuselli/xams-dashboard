#!/usr/bin/env bash
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
"$DIR/stop_dashboard.sh"
"$DIR/start_dashboard.sh"
