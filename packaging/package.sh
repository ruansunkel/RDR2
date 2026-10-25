#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="${1:-$ROOT/dist/RDR2Launcher.app}"
MODE="${2:---development}"
[[ "$MODE" == --development || "$MODE" == --release ]] || { echo 'Use --development or --release' >&2; exit 2; }
[[ -d "$APP" ]] || { echo "Missing app: $APP" >&2; exit 1; }
mkdir -p "$ROOT/dist"
"$ROOT/packaging/audit-deps.sh" "$APP" > "$ROOT/dist/dependency-audit.json"
/usr/bin/codesign --verify --deep --strict "$APP"
if [[ -f "$APP/Contents/Resources/runtime-manifest.json" ]]; then
    "$APP/Contents/MacOS/RDR2Launcher" --diagnose
fi
if [[ "$MODE" == --release ]]; then
    [[ -f "$APP/Contents/Resources/runtime-manifest.json" ]] || { echo 'Release requires a full runtime' >&2; exit 1; }
    [[ -f "$ROOT/notes/evidence/acceptance.json" ]] || { echo 'Release requires real acceptance evidence (see template)' >&2; exit 1; }
    python3 "$ROOT/packaging/release-gate.py" "$ROOT/notes/evidence/acceptance.json"
    /usr/sbin/spctl --assess --type execute --verbose "$APP"
    /usr/bin/xcrun stapler validate "$APP"
    NAME=RDR2Launcher
else
    NAME=RDR2Launcher-development
fi
python3 "$ROOT/packaging/report.py" "$APP" "$ROOT/dist"
cp "$ROOT/BUILD.md" "$ROOT/dist/BUILD.md"
/usr/bin/ditto -c -k --keepParent "$APP" "$ROOT/dist/$NAME.zip"
(cd "$ROOT/dist" && /usr/bin/shasum -a 256 "$NAME.zip" > SHA256SUMS)
echo "Packaged $ROOT/dist/$NAME.zip"
