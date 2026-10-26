#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
CACHE_ROOT="${RDR2_BUILD_CACHE_ROOT:-$ROOT/.cache}"
SCRATCH="${RDR2_BUILD_SCRATCH:-$ROOT/.build}"
export CLANG_MODULE_CACHE_PATH="$CACHE_ROOT/clang"
export SWIFTPM_MODULECACHE_OVERRIDE="$CACHE_ROOT/swift-modules"
export PYTHONPYCACHEPREFIX="$CACHE_ROOT/python"
for script in scripts/*.sh packaging/*.sh; do bash -n "$script"; done
python3 -m unittest discover -s Tests -v
swift run --disable-sandbox --scratch-path "$SCRATCH" --cache-path "$CACHE_ROOT/swift" \
    --config-path "$CACHE_ROOT/swift-config" --security-path "$CACHE_ROOT/swift-security" LauncherCoreChecks
