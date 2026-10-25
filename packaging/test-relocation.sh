#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="${1:?Usage: test-relocation.sh APP [--wineboot|--launcher-only]}"
APP="$(cd "$(dirname "$APP")" && pwd)/$(basename "$APP")"
TESTROOT="$(mktemp -d "${TMPDIR:-/tmp/}rdr2-relocation.XXXXXX")"
COPY="$TESTROOT/Path With Spaces/RDR2Launcher.app"
mkdir -p "$(dirname "$COPY")"
/usr/bin/ditto "$APP" "$COPY"
"$ROOT/packaging/audit-deps.sh" "$COPY"
DIAGNOSTIC=--diagnose
if [[ "${2:-}" == --launcher-only ]]; then DIAGNOSTIC=--diagnose-launcher; fi
/usr/bin/env -i HOME="$HOME" PATH=/usr/bin:/bin:/usr/sbin:/sbin TMPDIR="$TESTROOT/" \
    "$COPY/Contents/MacOS/RDR2Launcher" "$DIAGNOSTIC"
if [[ "${2:-}" == --wineboot ]]; then
    # Explicit build-only execution with a fresh isolated prefix; never touches user's games.
    python3 "$ROOT/packaging/smoke-runtime.py" "$COPY" "$TESTROOT/private-prefix"
fi
echo "Relocation integrity check passed; retained evidence at $TESTROOT"
echo 'This does not verify Finder, Gatekeeper, clean-host launch or Story Mode.'
