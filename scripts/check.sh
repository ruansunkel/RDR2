#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export CLANG_MODULE_CACHE_PATH="$ROOT/.cache/clang"
export SWIFTPM_MODULECACHE_OVERRIDE="$ROOT/.cache/swift-modules"
export PYTHONPYCACHEPREFIX="$ROOT/.cache/python"
for script in scripts/*.sh packaging/*.sh; do bash -n "$script"; done
python3 -m unittest discover -s Tests -v
swift run --disable-sandbox --cache-path "$ROOT/.cache/swift" \
    --config-path "$ROOT/.cache/swift-config" --security-path "$ROOT/.cache/swift-security" LauncherCoreChecks
