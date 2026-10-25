# Installation and sign-in recovery — 2026-10-25

This supersedes the download/authentication status in the earlier reports. These
observations concern the 8 GB build VM, not the unavailable physical host.

- The user confirmed download completion. RDR2.exe (89,562,608 bytes) remains in
  vendor/probes/native-steam/prefixes/default/drive_c/Program Files (x86)/Steam/
  steamapps/common/Red Dead Redemption 2. No game files were moved or downloaded again.
- The earlier GUI opened the separate default Application Support environment.
  Reopening the original native-steam environment restored Steam's installed game;
  the user confirmed it was visible again. The GUI now remembers an existing
  environment outside the signed app, displays its data folder and reveals game
  files. Missing remembered folders fail explicitly rather than silently creating
  another prefix. Its private build HOME is preserved when that environment is selected.
- The installed Rockstar Service was stopped. Starting it while Steam remained
  open produced STATE 4 RUNNING; the Rockstar log confirmed its service handshake.
  The updated native Play path checks/starts that installed service through Wine
  before requesting Steam app 1174180. No service reinstall or prefix reset occurred.
- The user reached Rockstar sign-in, then reported #1.000.7. Browser sign-in on
  the same Mac worked. The UTC clock was correct, macOS used Africa/Johannesburg,
  and Wine reported Kaliningrad Standard Time. Process-only TZ/TZDIR overrides did
  not change that reported Windows zone.
- The build-only helper backed up system.reg and copied/verified all three
  conflicting Windows timezone definitions (Kaliningrad, Libya and Namibia) under
  HKLM/Software/RDR2Launcher/TimezoneBackups before removing them from Wine's matching
  list. A fresh query verified South Africa Standard Time. The registry copies,
  system hive snapshot, recovery.json and restore instructions remain under
  vendor/probes/native-steam/state/timezone-repair-20261025T151114Z/.
  macOS settings, account data and game files were unchanged. After retrying the
  failed Rockstar frontend through Steam, **the user confirmed sign-in works**.
- The updated native app implements the same scoped correction using bundled Wine,
  with current-year definition checks, backup verification, rollback and a persisted
  interruption-recovery marker. Its failure/interruption paths are tested with a
  simulated registry; this already-corrected live prefix did not need a second
  native correction. Other geographic host zones are left alone. A build-only
  restore helper validates the selected prefix and allowed registry backup namespace.
- Wine children retained stdout descriptors after short registry commands exited.
  Native queries now read private temporary output files after the command process
  exits, avoiding indefinite pipe-EOF waits. Client/account output remains uncollected.
- Source checks passed: **8 Python packaging tests + 16 Swift core checks** and
  shell syntax checks. Regression coverage includes environment persistence,
  missing-folder behavior, preserved game files, actual service-state parsing,
  inherited-output lifetime, backup corruption, rollback and interrupted moves.
- A separate updated app was built at dist/transfer/RDR2Launcher.app. The active
  older runtime bundles and native recovery GUI were preserved. Static audit:
  **153 Mach-O files, zero failures**. Nested and outer ad-hoc signing passed;
  the native diagnostic verified the complete runtime manifest and Rosetta.
  A complete copied app passed audit/manifest verification at a path with spaces
  and a cleared environment. The unchanged runtime's earlier dynamic Wine/media
  smoke test was not repeated during the live game attempt. The development archive
  passed per-entry CRC, SHA-256 and private client/game/account path exclusions.
  The matching archive hash is delivered in dist/SHA256SUMS.

## Game startup remains unresolved

The user's last visual report was that the game was starting/loading. Later
read-only process-name queries found Steam but no RDR2.exe, Rockstar frontend or
service. Sanitized launcher events show a launch at 17:31:08 local time and game
exit **0x3** at 17:31:59. No game Settings/system.xml was created. The code alone
does not establish whether the cause is graphics, memory or another startup fault.
After verifying no game/frontend remained and the installed service was RUNNING,
one additional launch was requested through the same Steam installation. Wine's
subsequent process list shows Launcher.exe, RockstarService.exe and PlayRDR2.exe
running, with no RDR2.exe yet. A macOS process-name query missed those Windows
processes; Wine's own tasklist is the authoritative observation. The current
visual result is pending. No direct executable/entitlement bypass was used.

Controllable Story Mode, FPS, the physical host, Finder/Gatekeeper, Developer ID /
notarization and full public redistribution/source review remain unverified.
No credentials, login registry entries, browser storage or correlation identifiers
are included in this report or the app/archive.
