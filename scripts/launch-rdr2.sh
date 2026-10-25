#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="${RDR2_APP:-$ROOT/dist/RDR2Launcher.app}"
if [[ "${1:-}" == --diagnose ]]; then
    exec "$APP/Contents/MacOS/RDR2Launcher" --diagnose
fi
[[ -f "$APP/Contents/Resources/runtime-manifest.json" ]] || {
    echo 'No full runtime bundle built. See STATUS.md and BUILD.md; gameplay is unverified.' >&2; exit 1;
}
exec /usr/bin/open "$APP"
