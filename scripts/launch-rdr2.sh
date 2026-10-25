#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="${RDR2_APP:-$ROOT/dist/transfer/RDR2Launcher.app}"
if [[ ! -d "$APP" ]]; then APP="${RDR2_APP:-$ROOT/dist/recovered/RDR2Launcher.app}"; fi
if [[ ! -d "$APP" ]]; then APP="${RDR2_APP:-$ROOT/dist/host-test/RDR2Launcher.app}"; fi
if [[ ! -d "$APP" ]]; then APP="${RDR2_APP:-$ROOT/dist/RDR2Launcher.app}"; fi
if [[ "${1:-}" == --diagnose ]]; then
    exec "$APP/Contents/MacOS/RDR2Launcher" --diagnose
fi
[[ -f "$APP/Contents/Resources/runtime-manifest.json" ]] || {
    echo 'No full runtime bundle built. See STATUS.md and BUILD.md; gameplay is unverified.' >&2; exit 1;
}
DATA="${RDR2_DATA_DIRECTORY:-$ROOT/vendor/probes/native-steam}"
if [[ -f "$DATA/prefixes/default/drive_c/Program Files (x86)/Steam/steam.exe" ]]; then
    exec /usr/bin/open -n "$APP" --args --data-directory "$DATA" --remember-environment
fi
exec /usr/bin/open "$APP"
