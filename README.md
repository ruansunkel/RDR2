# RDR2 Launcher for Apple Silicon

Quick commands: [How to build & run](BUILD-AND-RUN.md).

A native macOS launcher and repeatable packaging tools for the Steam edition of
Red Dead Redemption 2, using freely available Wine 11, patched MoltenVK and DXMT.
The game uses Vulkan; DXMT serves Steam/Rockstar launcher components.

**Current deliverable is a runtime-inclusive development app.** Its bundled Wine
11 initializes a fresh prefix, and Steam and Rockstar sign-in work. On
2026-10-25, the user confirmed **playable Story Mode with working controls** on a
physical M1 Max (32 GB RAM, 32-core GPU), using a fresh host environment and copied
game files at 1280×720 windowed with Vulkan. The first host launch stalled; a
retry with `-ignorepipelinecache` reached gameplay, without isolating the cause.
FPS, extended-session stability and repeat cold starts remain unmeasured.
See [STATUS.md](STATUS.md) and [HOST-TEST.md](HOST-TEST.md) for evidence and setup.

The tested tree, foliage and rock examples now have confirmed rendering
workarounds in the main app, `dist/RDR2Launcher.app`.
[Exact changes](notes/rendering-changes-2026-10-27.md) describe the three guarded
shader edits, capture/build tooling and remaining limits.
[Build and test software](notes/build-and-test-software.md) lists versions,
locations and which components were added locally or already present.

Quit RDR2 and the launcher, then build and open the latest main app on this Apple Silicon Mac:

```sh
scripts/build.sh
scripts/launch-rdr2.sh
```

You can also open `dist/RDR2Launcher.app` in Finder. The build recompiles the
native launcher and bundles the exact tested MoltenVK driver, including the
tree, foliage and rock workarounds and earlier allocation/query changes.
It verifies the renderer checksum, source pins, runtime integrity and signatures
before replacing the previous main app. A failed build leaves that app intact.
Run `scripts/launch-rdr2.sh --diagnose` for an integrity check without starting the game.

For graphics checks using the same installed game, build the comparison app:

```sh
scripts/build.sh --without-occlusion-fixes
open dist/RDR2GraphicsCheck.app
```

This renderer omits the tree, foliage/grass and rock occlusion workarounds.
The earlier allocation and query changes remain included. Both apps use the
existing `~/Library/Application Support/RDR2Launcher/` prefix, game library,
saves and sign-ins. Rebuilding does not create a new game installation.
Quit RDR2, exit Windows Steam/Rockstar and close the launcher before switching
apps so the new session loads the selected renderer. The comparison app has a
distinct name and bundle identifier; the regular main app is preserved.

The two retained local inputs are `vendor/rdr2-runtime-r27-portable-v3/` and
`vendor/renderer/current/`. The accepted renderer checksum is tracked in
`config/accepted-renderer.json`. Rebuilding the launcher uses Apple command-line
developer tools and Python 3; it needs no GPU captures or network downloads.
Compiling a changed MoltenVK driver remains the separate pinned workflow under
`experiments/moltenvk-trees/`; this command deliberately requires the tested binary.
This app is ad-hoc signed, not notarized. It contains no Steam/game files or
account state. The launcher-only preview remains available with `--launcher-only`.

The comparison build also requires `vendor/renderer/without-occlusion/`, a
retained pinned driver built before the three shader workarounds were added.

The full runtime preparation, source pins, signing and remaining distribution
requirements are in [BUILD.md](BUILD.md). See
[the cleanup record](notes/workspace-cleanup-2026-10-27.md) for archived files and recovery.

On first launch on the host, choose a persistent game folder and select
**Install & Play**. Sign in within Windows Steam, select/add the mapped **R:** drive
using Steam's Storage settings, and let Steam confirm ownership and complete the
download. Then select **Play** to use Steam → Rockstar → RDR2. Complete Rockstar
authentication in its own window. No account credentials belong in this repository.

**Repair** asks Steam to verify RDR2; it does not delete your prefix, game or saves.
**Open Steam** retries the official client after an interrupted update. First-time
client setup can take 15–25 minutes. **View logs** opens application event logs,
which omit client output and account information. macOS tools and package managers
are only used to build; a correctly assembled host app uses its bundled Wine.

The main app uses `~/Library/Application Support/RDR2Launcher/`. The tested
environment, its game library, saves and sign-ins have been moved there; the
previous environment at that name is preserved in the external archive. A
temporary compatibility symlink was removed after a successful game launch and
an audit of Wine's updated paths. The old control folders are also archived;
only `RDR2Launcher` remains in Application Support. The main build uses the
`patched` edition. Replacing the app
preserves the prefix, Steam updates and saves; a chosen external library persists
separately. Removing the app leaves all game data intact. No destructive reset is
provided. Backups of changed state/registry settings remain in the data directory.

Steam/Rockstar authentication and an owned Steam copy (1174180) are required. Apple
manages Rosetta installation if needed; this project does not install it silently.
No commercial wrapper, Windows VM, Apple D3DMetal or DRM bypass is part of the launcher.

The older build-Mac environment formerly at `vendor/probes/native-steam/` is
archived outside this project; it contains a separate downloaded game and private
client state. The current host environment and external game library stay in
their existing locations. **Use existing environment…** can select a different
launcher data folder if needed. The choice is remembered outside the app;
**Show game files** opens its installed game directory. The game folder itself
is not the launcher data folder. An unavailable remembered environment shows an
error instead of silently creating an empty replacement prefix.

For an installed Rockstar launcher, Play keeps Steam open and starts its registered
background service when stopped, then verifies RUNNING before asking Steam to play.
This service check does not reinstall the launcher or game or reset data.

On Macs set to Africa/Johannesburg, the launcher corrects this pinned Wine engine's
verified Kaliningrad timezone mismatch using per-environment backups and exact
registry-value checks. It leaves other host timezones alone, does not change macOS
settings and restores original definitions if the correction fails. This resolved
the observed Rockstar #1.000.7 sign-in failure. A build-only restore helper and
backup journals are documented in BUILD.md.
