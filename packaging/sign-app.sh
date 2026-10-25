#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="${1:?Usage: sign-app.sh APP IDENTITY [TESTED_ENTITLEMENTS_PLIST]}"
IDENTITY="${2:?Supply - for ad-hoc or a Developer ID Application identity}"
ENTITLEMENTS="${3:-}"
ARGS=()
if [[ "$IDENTITY" != - ]]; then
    [[ "$IDENTITY" == 'Developer ID Application:'* && -f "$ENTITLEMENTS" ]] || {
        echo 'Developer ID signing requires a legitimate identity and a tested entitlements plist.' >&2; exit 1;
    }
    ARGS=(--options runtime --timestamp --entitlements "$ENTITLEMENTS")
else
    ARGS=(--preserve-metadata=entitlements)
fi
"$ROOT/packaging/audit-deps.sh" "$APP"
# Depth first: libraries/executables before framework/app containers. No --deep signing.
while IFS= read -r -d '' path; do
    if [[ -f "$path" && ! -L "$path" ]] && /usr/bin/file -b "$path" | /usr/bin/grep -q 'Mach-O'; then
        /usr/bin/codesign --force --sign "$IDENTITY" "${ARGS[@]}" "$path"
    elif [[ -d "$path" && "$path" == *.app && "$path" != "$APP" ]] || \
         [[ -d "$path" && "$path" == *.framework && -e "$path/$(basename "$path" .framework)" ]]; then
        /usr/bin/codesign --force --sign "$IDENTITY" "${ARGS[@]}" "$path"
    fi
done < <(/usr/bin/find "$APP/Contents" -depth -print0)
# Signing changes Mach-O bytes: regenerate hashes AFTER nested signing, BEFORE outer signing.
if [[ -d "$APP/Contents/Resources/runtime" ]]; then
    python3 "$ROOT/packaging/runtime_tools.py" manifest "$APP/Contents/Resources"
fi
/usr/bin/codesign --force --sign "$IDENTITY" "${ARGS[@]}" "$APP"
/usr/bin/codesign --verify --deep --strict --verbose=2 "$APP"
if [[ "$IDENTITY" != - ]]; then
    echo 'Signed. Notarization and Gatekeeper assessment remain required; see BUILD.md.'
fi
