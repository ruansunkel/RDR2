#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/preflight.sh"
APP="${RDR2_APP:-$ROOT/dist/RDR2Launcher.app}"
if [[ -d "$APP" ]]; then
    "$ROOT/packaging/audit-deps.sh" "$APP"
    "$APP/Contents/MacOS/RDR2Launcher" --diagnose
else
    echo 'App not built. No account or Wine-prefix files were read.'
fi
