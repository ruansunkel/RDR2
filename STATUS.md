# Tree flicker under investigation — 2026-10-26

The user reports nearby and distant trees disappearing/reappearing and changing
shape on Ultra, persisting after the suggested Tree Quality High comparison.
Similar tree flicker remains unresolved in the upstream reports reviewed;
reviewed Highball r28/r29 manifests use the same MoltenVK component as this r27
build. No graphics settings or runtime binaries were changed during this
investigation; no fix is claimed. See
[tree-flicker evidence](notes/evidence/tree-flicker.md).

---

# Physical-host Story Mode confirmed — 2026-10-25

**The user confirmed: "Story Mode is playable and controls work."** The transfer
app has now reached interactive gameplay on the physical M1 Max with a fresh host
environment and reused game files.

- The copied transfer app passed deep/strict signature and runtime-integrity
  checks on the physical M1 Max (32 GB RAM, 32-core GPU), macOS 27.0.1 (26A434).
  Rosetta is available. No runtime rebuild or new system tools were required.
- Used the fresh host environment under Application Support, preserving the
  copied build-Mac prefix. Retrying bootstrap outside the agent sandbox completed
  the South Africa timezone correction and official Windows Steam setup/update.
  The user confirmed Steam is signed in and displaying the library.
- Cloned only the downloaded game to `~/Games/RDR2/steamapps/common/Red Dead
  Redemption 2`; all 123 paths and sizes match the original. Mapped this host
  library to `R:` and remembered the host environment in the transfer launcher.
- Steam library registration is verified at `Z:\Users\ruansunkel\Games\RDR2`;
  Steam recognized the installed game and launched through Rockstar. The user
  confirmed successful Rockstar sign-in on the physical host.
- The first host launch stalled near the end of its initial loading bar. After
  sampling the stalled process, stopped only that game and retried through Steam
  with a new host-game `commandline.txt` containing `-ignorepipelinecache`.
  The user then confirmed playable Story Mode with working controls. The
  successful retry does not isolate whether the restart, warmed caches or the
  option changed the outcome.
- FPS, extended-session stability and repeat cold-start reliability remain
  unmeasured. The user subsequently exited the game intentionally. See
  HOST-TEST.md for host evidence, including the launcher's exit diagnostic.
- The newly written host graphics settings confirm Vulkan, 1280×720 windowed,
  with VSync enabled; these settings were not edited during the retry.
- Removed five confirmed disconnected processes left from before the retry,
  verifying each process before termination. The current game was preserved
  during cleanup; its later exit was user initiated. The final process list has
  one current Steam client with its normal Wine/browser/service helpers and no
  duplicate Rockstar launcher. No client state or game files were reset.

---

# Latest verified recovery — 2026-10-25

- The completed RDR2 installation was recovered in its original native-steam
  environment. The user confirmed that Steam shows the installed game again.
- Rockstar's registered background service remains RUNNING with Steam open; its
  log confirms the service handshake. The user reached the sign-in page.
- Sign-in failed with #1.000.7 while browser sign-in on the same Mac worked. Wine
  reported Kaliningrad for the host's Africa/Johannesburg timezone. Verified,
  backed-up moves of only the three conflicting timezone definitions made Wine
  report South Africa Standard Time. After a Rockstar-only restart through Steam,
  **the user confirmed Rockstar sign-in works**. A later process-name query found Steam without RDR2/Rockstar, and the
  launcher recorded RDR2 exiting with code 0x3 after about 51 seconds. A single
  retry through Steam was requested after verifying the installed service RUNNING.
  Wine's subsequent process list shows Launcher.exe, RockstarService.exe and
  PlayRDR2.exe running; RDR2.exe was not yet listed. The user saw a sign-in/consent
  prompt on retry and subsequently confirmed loading continued before the window
  closed by itself. Startup on this VM remains unsuccessful.
  No main menu, gameplay or FPS claim is made; the exit's cause is unresolved.
- No game files, sign-in data or macOS settings were reset. Backup journal:
  vendor/probes/native-steam/state/timezone-repair-20261025T151114Z/recovery.json.
- The updated native app remembers the existing environment, reveals game files,
  checks/starts the installed Rockstar service and includes the validated,
  host-specific timezone correction with verification and rollback.
- Source validation: 8 Python tests + 16 Swift checks pass, including environment
  recovery, command-output lifetime, timezone applicability, verified backups and
  rollback after partial failure and recovery after an interrupted move. Final updated artifact is dist/transfer/RDR2Launcher.app.
- The updated bundle passed ad-hoc signature/runtime verification and relocation
  integrity at a path with spaces. Its archive passed SHA-256, per-entry CRC and
  private client/game/account path exclusion checks. Recovery evidence is appended
  to dist/TEST-REPORT.md. Full dynamic Wine/media smoke evidence from the unchanged
  runtime remains recorded in notes/evidence/runtime-validation.md.
- The active Steam/Rockstar/game environment is preserved; older bundles are not
  replaced while its processes are using them. Developer ID/notarization, full
  public redistribution review, separate-host validation and gameplay remain open.
- Next useful validation is the physical host with its native GPU and actual RAM
  budget. This is a change of test environment, not proof that memory or the VM GPU
  caused exit 0x3. See HOST-TEST.md for the archive, game-file reuse and observations
  needed. No new game launches or configuration changes were made for this handoff.

The earlier progress history below is historical and retained for diagnosis.

---

# Current recovery update — 2026-10-25

The user completed the RDR2 download. The files remain at
`vendor/probes/native-steam/prefixes/default/drive_c/Program Files (x86)/Steam/steamapps/common/Red Dead Redemption 2`.
RDR2.exe is present (89,562,608 bytes). No game data was moved, deleted or downloaded
again. Reopening the old GUI had selected the different default Application Support
prefix, which is why Steam appeared to lose the game.

The corrected GUI now remembers a selected existing environment outside the app,
accepts an explicit data directory, shows that data folder and provides Show game
files. A missing remembered folder cannot silently produce a new empty Steam prefix.
The selection was saved for this user to the existing native-steam environment with
its original private HOME. The user confirmed that RDR2 is restored in Steam.

Rockstar's service is installed in that same prefix. Its logs showed an initial
service setup/start failure. Starting the installed service with Steam open produced
and retained STATE 4 RUNNING; subsequent Rockstar logs confirmed a service handshake.
The updated Play route performs that non-destructive service check/start before
launching through Steam. The user then saw the sign-in page; keyboard interaction
became sufficient to submit sign-in, which returned #1.000.7. Game startup and
controllable gameplay remain unverified.

Clock checks: UTC clock agrees with the tool clock. macOS timezone is
Africa/Johannesburg, but Wine names its UTC+2 zone Kaliningrad Standard Time.
A process-local TZ/TZDIR probe did not fix the name. Registry/system files were
backed up before probes; no timezone definitions, authentication state or macOS
settings were changed. Browser sign-in comparison is pending. The user's supplied
correlation identifier is not copied into diagnostic reports.

Validation for this change: 8 Python packaging tests and 11 Swift checks pass,
including remembered-environment persistence, missing-path fail-safe behavior,
preserved game files when switching, selection backups and actual service-state
parsing. The corrected development app is dist/recovered/RDR2Launcher.app. Public
redistribution, Developer ID/notarization and clean-host/gameplay gates remain open.

Preserve vendor/probes/native-steam: it now contains the downloaded game and private
client state. Do not treat it as disposable build cache. The earlier build history
below is retained; its downloading/old-artifact statements are historical.

---

# Status — 2026-10-25

**Current milestone: runtime-inclusive development app; real Windows Steam installed
and updated through the native launcher. The user has signed in and reports RDR2
actively downloading on the build Mac. Gameplay and clean-host validation remain open.**

The user clarified that this is the build Mac, the host is unavailable, and the
immediate objective is a launchable bundle for transfer; host playability follows.
The build workflow therefore proceeds without requiring gameplay on this 8 GB VM.
No simulated download or fixture is counted as a real Steam/game success.

## Environment

macOS 27.0.1 (26A434), arm64, Apple M1 Max Virtual, 8 GB RAM; initially approximately
217 GiB free after source builds. Existing Apple CLT / Swift 6.4. On this turn,
Rosetta's x86_64 execution check **passed** and native Steam was already present.
Those are changes since the earlier preflight; this agent did not install either.
No Homebrew, global Wine or Highball app/data was found. Native Steam is untouched.
The separate physical M1 Max host's OS, RAM, disk and security behavior are unknown.

## Executed

- Downloaded and SHA-256 verified all six pinned Highball r27 runtime archives.
  Wine reports `wine-11.0`; patched MoltenVK's linear-fallback markers are present.
- Ran actual Wine prefix initialization and `cmd /c ver` with a system-only PATH
  and a private HOME/prefix. Wine reports Windows 10.0.19045; MoltenVK initializes
  on the Apple Paravirtual GPU. Initial sandbox socket denial was resolved with
  an approved unsandboxed execution of the same isolated test, without sudo.
- Audited the real upstream runtime: found 21 issues, including absolute build
  paths, a broken Apple graphics alias, missing FFmpeg ABI versions and stale media.
- Prepared the official GStreamer 1.28.7 playback dependency closure; built only
  FFmpeg 9.0.2's x86_64 demuxing libraries from verified source, without GPL flags
  or external codec packages. Added verified Intel GLib/PCRE2/libintl libraries.
- Corrected load commands/IDs and recorded original/relocated hashes and operations
  in `runtime/relocation-changes.json`. Uses short relative library aliases to
  respect existing Mach-O header space. No ABI compatibility version is falsified.
- Removed unused Template renderer overlays, wrapper SDK and alternate MoltenVK.
  No Apple D3DMetal or client/game/account files are bundled. The initial full app
  passes a static audit of **153 Mach-O files** with no unresolved outside references.
- A dynamic GStreamer probe caught `_libintl_newlocale` missing from the old runtime.
  Replacing libintl with the matching pinned gettext bottle fixes it; actual
  `gst-inspect-1.0 --version` reports GStreamer 1.28.7 successfully.
- The bundled native app initialized its own test prefix, downloaded the official
  Valve installer, installed Windows Steam and started its real self-update.
  Steam's updater reported completion; steam.exe and five steamwebhelper.exe
  processes were observed. The user subsequently confirmed sign-in and RDR2 downloading.
- Preserved 157 vendor notice/provenance files. Complete mixed-runtime notices and
  corresponding-source review remain required before public distribution.

## Data and artifacts

The **active build-Mac Steam session** uses:

`vendor/probes/native-steam/prefixes/default/`

Its launcher is the existing `dist/RDR2Launcher.app`. Keep that Steam window and
prefix for the current download and subsequent Play. Do not start a different
prefix and assume it contains this installation. No authentication files are read,
exported or copied into the transferable app. Only app-defined status events,
public installer provenance and nonsecret updater/process summaries were inspected.

The final transferable development artifact is built separately to avoid replacing
files used by the active Steam session:

- `dist/host-test/RDR2Launcher.app`
- `dist/RDR2Launcher-development.zip`
- `dist/SHA256SUMS`, `SBOM.md`, `BUILD.md`, `TEST-REPORT.md`, `dependency-audit.json`

Final copied-bundle/media smoke outcomes are recorded in
`notes/evidence/runtime-validation.md`: runtime hashes, relocated Wine initialization,
Windows cmd, media registration, GStreamer/libav discovery and dynamic library loads
all passed. Eight Python tests and six Swift checks passed. These are ad-hoc development artifacts;
there is no Developer ID identity, notarization or Gatekeeper distribution claim.
Build products and all client/game/account state remain ignored by Git.

## Remaining acceptance

| Check | State |
| --- | --- |
| Native app, pinned engine, patched MoltenVK, DXMT bundled | Passed build and copied-bundle checks on build Mac |
| Static outside-dependency/symlink audit | Final complete bundle passed, 153 Mach-O files |
| Real Wine prefix and Windows utilities | Passed on build Mac |
| Official Windows Steam bootstrap/update | Passed on build Mac |
| Steam sign-in and RDR2 download | User confirmed; download still in progress |
| RDR2 installed/verified | Not yet confirmed by Steam/user |
| Rockstar sign-in / entitlement launch | Not yet verified |
| Story Mode, controls and FPS | Not measured; no gameplay claim |
| Copied bundle on separate host / Finder / normal Gatekeeper | Host unavailable; not tested |
| Developer ID / notarization | No valid signing identity found; unresolved |
| Full redistribution/source compliance | Review remains incomplete; release gate closed |

The next game step is to let the existing download finish, use Steam's Play in
that same prefix, complete Rockstar setup/sign-in/EULAs in its windows, and observe
launch. The native launcher's Play uses Steam `-applaunch 1174180`; install and
repair use Steam URIs. File/manifest presence never proves ownership or readiness.

User data on the host persists under `~/Library/Application Support/RDR2Launcher/`
and an optional selected external library. Replacing/removing the app preserves
those files. No reset/uninstall or unrelated-prefix mutation was performed. Build
smoke tests stop only their own newly created disposable wineservers. The active
Steam/RDR2 download is left running.
