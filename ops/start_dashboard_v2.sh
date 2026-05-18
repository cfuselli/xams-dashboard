#!/usr/bin/env bash
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
echo "Deprecated: use start_dashboard.sh (forwarding now)."
"$DIR/start_dashboard.sh"
