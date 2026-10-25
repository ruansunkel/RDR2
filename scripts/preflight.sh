#!/bin/bash
# Read-only. Omit hardware serial numbers, usernames and registry/account contents.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="${1:-$ROOT/logs/preflight-$(date -u +%Y%m%dT%H%M%SZ).txt}"
mkdir -p "$(dirname "$OUTPUT")"
if [[ -e "$OUTPUT" ]]; then cp "$OUTPUT" "$OUTPUT.backup-$(date -u +%Y%m%dT%H%M%SZ)-$$"; fi
{
    date -u
    sw_vers
    uname -m
    for key in machdep.cpu.brand_string hw.memsize; do
        printf '%s: ' "$key"
        sysctl -n "$key" 2>/dev/null || echo unavailable
    done
    system_profiler SPHardwareDataType 2>/dev/null | /usr/bin/awk '/Model Name:|Model Identifier:|Chip:|Memory:/{print}' || true
    df -h "$ROOT" | /usr/bin/awk 'NR == 1 {print "Disk size / used / available / capacity"} NR == 2 {print $2, $3, $4, $5}'
    for tool in brew swift git wine; do
        if command -v "$tool" >/dev/null 2>&1; then printf '%s: present\n' "$tool"; else printf '%s: absent\n' "$tool"; fi
    done
    if /usr/bin/arch -x86_64 /usr/bin/true 2>/dev/null; then echo 'Rosetta: available'; else echo 'Rosetta: unavailable'; fi
    for app in Highball Steam; do
        if [[ -d "/Applications/$app.app" ]]; then echo "$app application: present"; else echo "$app application: absent"; fi
    done
    if [[ -d "$HOME/Library/Application Support/Highball" ]]; then echo 'Highball data: present (not inspected or changed)'; else echo 'Highball data: absent'; fi
} > "$OUTPUT"
cat "$OUTPUT"
[[ "$(uname -m)" == arm64 ]] || { echo 'Unsupported architecture' >&2; exit 1; }
[[ "$(sw_vers -productVersion | cut -d. -f1)" -ge 14 ]] || { echo 'macOS 14+ required' >&2; exit 1; }
