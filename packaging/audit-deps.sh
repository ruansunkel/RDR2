#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/packaging/runtime_tools.py" audit "${1:?Usage: audit-deps.sh APP}"
