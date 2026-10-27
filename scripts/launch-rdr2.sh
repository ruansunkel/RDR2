#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="${RDR2_APP:-$ROOT/dist/RDR2Launcher.app}"
[[ -d "$APP" ]] || { echo 'Build the main app first: scripts/build.sh' >&2; exit 1; }
if [[ "${1:-}" == --diagnose ]]; then
    exec "$APP/Contents/MacOS/RDR2Launcher" --diagnose
fi
[[ -f "$APP/Contents/Resources/runtime-manifest.json" ]] || {
    echo 'No full runtime bundle built. Run scripts/build.sh.' >&2; exit 1;
}
if [[ -n "${RDR2_DATA_DIRECTORY:-}" ]]; then
    exec /usr/bin/open "$APP" --args --data-directory "$RDR2_DATA_DIRECTORY" --remember-environment
fi
exec /usr/bin/open "$APP"
