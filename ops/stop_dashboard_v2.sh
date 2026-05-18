#!/usr/bin/env bash
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
echo "Deprecated: use stop_dashboard.sh (forwarding now)."
"$DIR/stop_dashboard.sh"
