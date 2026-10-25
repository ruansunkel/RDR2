#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export CLANG_MODULE_CACHE_PATH="$ROOT/.cache/clang"
export SWIFTPM_MODULECACHE_OVERRIDE="$ROOT/.cache/swift-modules"
MODE="${1:---runtime}"
RUNTIME="${2:-}"
APP="${RDR2_BUILD_OUTPUT:-$ROOT/dist/RDR2Launcher.app}"
[[ "$APP" == /* ]] || { echo 'RDR2_BUILD_OUTPUT must be an absolute app path' >&2; exit 2; }
mkdir -p "$(dirname "$APP")"
if [[ "$MODE" != --launcher-only && "$MODE" != --runtime ]]; then
    echo 'Usage: build-app.sh --launcher-only | --runtime STAGED_RUNTIME' >&2; exit 2
fi
if [[ "$MODE" == --runtime ]]; then
    [[ -d "$RUNTIME/engine" && -d "$RUNTIME/licenses" ]] || {
        echo 'Stage a complete engine with reviewed licenses/ first. See BUILD.md.' >&2; exit 1;
    }
fi
if [[ -e "$APP" ]]; then
    mv "$APP" "$APP.backup-$(date -u +%Y%m%dT%H%M%SZ)-$$"
fi
swift build -c release --arch arm64 --product RDR2Launcher --build-system native -debug-info-format none --disable-sandbox --cache-path "$ROOT/.cache/swift" \
    --config-path "$ROOT/.cache/swift-config" --security-path "$ROOT/.cache/swift-security"
BIN="$(swift build -c release --arch arm64 --build-system native --show-bin-path --disable-sandbox --cache-path "$ROOT/.cache/swift" --config-path "$ROOT/.cache/swift-config" --security-path "$ROOT/.cache/swift-security")"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources/recipes" "$APP/Contents/Frameworks"
cp "$BIN/RDR2Launcher" "$APP/Contents/MacOS/"
python3 packaging/runtime_tools.py prune-launcher-rpaths "$APP"
cp packaging/Info.plist "$APP/Contents/Info.plist"
cp config/engine-upstream.json "$APP/Contents/Resources/"
cp config/media-sources.json "$APP/Contents/Resources/"
cp config/recipes/*.json "$APP/Contents/Resources/recipes/"
cp BUILD.md "$APP/Contents/Resources/BUILD.md"
/usr/bin/ditto licenses "$APP/Contents/Resources/licenses"
if [[ "$MODE" == --runtime ]]; then
    /usr/bin/ditto "$RUNTIME" "$APP/Contents/Resources/runtime"
    python3 packaging/runtime_tools.py manifest "$APP/Contents/Resources"
else
    echo 'LAUNCHER-ONLY PREVIEW: no Wine/runtime, no Steam/gameplay verification.' > "$APP/Contents/Resources/DEVELOPMENT.txt"
fi
"$ROOT/packaging/audit-deps.sh" "$APP" > "$ROOT/dist/dependency-audit.json"
/usr/bin/codesign --force --sign - "$APP"
/usr/bin/codesign --verify --deep --strict "$APP"
/usr/bin/file "$APP/Contents/MacOS/RDR2Launcher"
echo "Built development app: $APP"
