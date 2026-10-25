# Physical-host test

## Story Mode confirmed on the host — 2026-10-25

The user confirmed: **"Story Mode is playable and controls work."** This is a
successful interactive gameplay test on the physical host. FPS, extended-session
stability and subsequent cold starts have not been measured.

- Physical MacBook Pro: Apple M1 Max, 32 GB RAM, 32-core GPU;
  macOS 27.0.1 (26A434). Rosetta execution passed.
- Used `dist/transfer/RDR2Launcher.app`. Deep/strict signature verification
  and the launcher's runtime-integrity diagnostic passed. The app had no
  quarantine attribute; this does not validate quarantined Finder/Gatekeeper delivery.
- Continued the newly initialized host environment at
  `~/Library/Application Support/RDR2Launcher/`; the copied build prefix was not
  reused. An earlier setup attempt had recorded an error. Retrying the packaged
  bootstrap outside the agent sandbox succeeded; the exact earlier error was not
  captured, so its cause remains unknown.
- The host timezone correction verified `South Africa Standard Time`, preserving
  the original registry definitions and a recovery journal. Steam was installed
  from Valve; its bootstrap log records update completion. The user confirmed
  that Steam is signed in and showing the library.
- APFS-cloned only the game folder to
  `~/Games/RDR2/steamapps/common/Red Dead Redemption 2`. All 123 relative file paths
  and sizes match the source (128,281,316,135 bytes). This is a copy inventory
  check, not Steam integrity verification. The original game and build-prefix
  account state remain preserved.
- Mapped host `R:` to `~/Games/RDR2`, saved the host game-library selection and
  opened the transfer launcher with the host environment remembered. The setup
  helper uses this environment's private `build-test-home`, and that selection is
  persisted for subsequent GUI launches.
- Steam's Storage picker did not show `R:`. The user added the host folder through
  `Z:\Users\ruansunkel\Games\RDR2` instead. Both Steam library-folder files now
  register that exact path, and the install dialog offers it as Local Drive (Z:).
  This library contains the copied game files; choose Z: in the install dialog.
- Steam recognized the copied installation and launched through Rockstar; its
  host game manifest reports installed (`StateFlags` 4). The user confirmed
  Rockstar sign-in succeeds on the physical host.
- The first host launch stalled on a black window with a nearly complete loading
  bar. At 19:27 SAST it had been running for over twelve minutes. A five-second
  stack sample showed mostly waiting threads, with limited Windows symbolication;
  no active shader compilation was visible in that sample. Its measured physical
  footprint was 1.7 GB. Graphics cache timestamps had stopped advancing at 19:20.
  These observations do not establish the cause of the stall.
- Stopped only the stalled host game, preserved Steam/Rockstar and requested one
  retry through Steam. Added `-ignorepipelinecache` to a new `commandline.txt` in
  the **host copy** of the game; no prior command-line file existed. This is a
  reversible experiment using Rockstar's documented startup option. It leaves
  the selected graphics backend and the original build-Mac game files unchanged.
- After the retry, the user first reported **"Game is running"**, then confirmed
  **"Story Mode is playable and controls work."** The retry changed both process
  state and the startup option, so the option is not a proven root-cause fix.
  The working session was left untouched for gameplay validation; no FPS result
  is recorded. The user subsequently confirmed they exited the game themselves.
- After the retry, the game wrote its first host `system.xml`, confirming Vulkan,
  1280×720 and windowed mode (`windowed` 1). VSync remains enabled. No graphics
  settings were edited during this diagnostic retry.
- At the user's request, cleaned up five pre-retry processes: the old Steam,
  Steam browser helper, Rockstar launcher, Social Club helper and Wine device
  helper. Each process's identity, host-environment files and disconnected Wine
  server socket were checked before termination. Four exited on SIGTERM; the
  disconnected Wine device helper required SIGKILL. All five targeted PIDs are
  gone. The active game remained alive immediately after cleanup; the user then
  confirmed its later exit was intentional. The final process list contained one
  current Steam client and its Wine/browser/service helpers, with no duplicate
  Rockstar launcher. No prefix, game files, sign-ins or saves were reset.
- Rockstar logged `0x80000003` and an unexpected-exit message at 19:49 SAST.
  The user confirmed they initiated that exit. Preserve that distinction: this
  is not evidence of a spontaneous failure during the confirmed gameplay.

The 8 GB build VM completed the real Steam download and reached successful Rockstar
sign-in. The game subsequently loaded and closed without reaching a verified menu.
The first attempt recorded exit 0x3; the cause is unresolved. The physical M1 Max
reached playable Story Mode after the retry described above. That result does not
establish the cause of the VM failure or the first host loading stall.

## Transfer

For the copied project, use `dist/transfer/RDR2Launcher.app`. Alternatively, copy
`dist/RDR2Launcher-development.zip` and `dist/SHA256SUMS` to the host, extract the
archive and open RDR2Launcher.app. The archive contains the launcher and bundled
runtime, with no game files or account state. The matching archive's SHA-256 is
recorded in SHA256SUMS alongside it.

This is an ad-hoc signed development build, not a notarized release. Normal Finder /
Gatekeeper acceptance on the host remains untested. If macOS blocks opening it,
record the exact dialog; do not disable Gatekeeper or strip quarantine. Rosetta is
an Apple-managed prerequisite if absent. No Homebrew, Wine, Highball or developer
tools should be installed on the host for this test.

## Reuse the completed game download

1. In the host launcher, choose a persistent game folder and open/install Windows
   Steam. Sign in inside Steam. Add the mapped R: folder as a library using Steam's
   Storage settings, and note the actual library directory Steam creates.
2. Copy the completed **Red Dead Redemption 2** game folder from the build Mac to
   the host. The source can be opened using **Show game files** in the build launcher;
   its project-relative path is:

   ```text
   vendor/probes/native-steam/prefixes/default/drive_c/Program Files (x86)/Steam/steamapps/common/Red Dead Redemption 2
   ```

3. With Windows Steam closed normally on the host, place that copied folder at
   `<host Steam library>/steamapps/common/Red Dead Redemption 2`. Preserve the build
   Mac's original files. Transfer the game folder separately from the app; create
   a fresh host environment and sign in there rather than copying the build prefix
   and its private client state.
4. Reopen Windows Steam and select Install for RDR2 in that same library. Steam can
   recognize existing files during installation; let it verify and fetch any missing
   files or updates. Then use Properties → Installed Files → Verify integrity if
   needed. Steam remains authoritative for ownership and completion.

This follows Valve's guidance on [recognizing existing game files](https://help.steampowered.com/en/faqs/view/4578-18A7-C819-8620)
and [verifying installed files](https://help.steampowered.com/en/faqs/view/21F5-8D5D-0141-7A5E).

## Launch and report

Use **Play** through Steam → Rockstar. Complete sign-in, consent and verification
prompts in the official windows. If the menu appears, start with Vulkan, 1280×720
windowed and the lowest available preset. Verify that Story Mode accepts controls.
Leave the current graphics backend in place for the first comparison.

Record the host's macOS version, RAM, M1 Max GPU configuration, whether it reaches
the menu/Story Mode, and any exact error or window closure. FPS is only useful after
interactive gameplay starts. Do not include credentials or account identifiers.
The app's **View logs** opens its application event log; vendor logs may contain
private data and should not be shared wholesale.

The host creates fresh data under `~/Library/Application Support/RDR2Launcher/`.
Replacing/removing the app preserves that data and the chosen game library.
