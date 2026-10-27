# RDR2 Launcher for Apple Silicon

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
workarounds in `dist/rock-occlusion/RDR2 Rocks Occlusion Diagnostic.app`.
[Exact changes](notes/rendering-changes-2026-10-27.md) describe the three guarded
shader edits, capture/build tooling and remaining limits.
[Build and test software](notes/build-and-test-software.md) lists versions,
locations and which components were added locally or already present.

Rebuild on an Apple Silicon build Mac with command-line developer tools:

```sh
scripts/check.sh
RDR2_BUILD_OUTPUT="$PWD/dist/transfer/RDR2Launcher.app" \
  packaging/build-app.sh --runtime "$PWD/vendor/rdr2-runtime-r27-portable-v3"
packaging/sign-app.sh dist/transfer/RDR2Launcher.app -
packaging/package.sh dist/transfer/RDR2Launcher.app --development
```

The transferable app is `dist/transfer/RDR2Launcher.app`; the archive is
`dist/RDR2Launcher-development.zip` with `dist/SHA256SUMS`. This is ad-hoc signed,
not notarized. No Steam/game files or account state are inside it. The initial
launcher-only preview can still be built with `--launcher-only`.

The full runtime preparation, source pins, signing and remaining distribution
requirements are in [BUILD.md](BUILD.md). Earlier build bundles remain in place for the current Steam/Rockstar session;
use the **transfer** artifact as the updated launcher.

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

User data stays in `~/Library/Application Support/RDR2Launcher/`. Replacing the app
preserves the prefix, Steam updates and saves; a chosen external library persists
separately. Removing the app leaves all game data intact. No destructive reset is
provided. Backups of changed state/registry settings remain in the data directory.

Steam/Rockstar authentication and an owned Steam copy (1174180) are required. Apple
manages Rosetta installation if needed; this project does not install it silently.
No commercial wrapper, Windows VM, Apple D3DMetal or DRM bypass is part of the launcher.

The installed build-Mac game uses the isolated data directory
`vendor/probes/native-steam/`. Keep using **that existing Windows Steam window**
for Play; opening a launcher with a different data directory
creates a separate prefix. Build-Mac sign-in/download state is intentionally excluded
from the transferable app. No development tool or manually configured environment
is needed on the host; Apple-managed Rosetta and normal client sign-ins still apply.

If Steam appears to have lost the game, use **Use existing environment…** and choose
`vendor/probes/native-steam` on this build Mac. The choice is remembered outside
the app; **Show game files** opens the installed RDR2 directory. The game folder
itself is not the launcher data folder. An unavailable remembered environment now
shows an error instead of silently creating an empty replacement prefix.

The completed build-Mac game is at:
`vendor/probes/native-steam/prefixes/default/drive_c/Program Files (x86)/Steam/steamapps/common/Red Dead Redemption 2`.
**Preserve vendor/probes/native-steam**: it now contains the downloaded game and
its private Steam/Rockstar data. It is not disposable runtime build cache.

For an installed Rockstar launcher, Play keeps Steam open and starts its registered
background service when stopped, then verifies RUNNING before asking Steam to play.
This service check does not reinstall the launcher or game or reset data.

On Macs set to Africa/Johannesburg, the launcher corrects this pinned Wine engine's
verified Kaliningrad timezone mismatch using per-environment backups and exact
registry-value checks. It leaves other host timezones alone, does not change macOS
settings and restores original definitions if the correction fails. This resolved
the observed Rockstar #1.000.7 sign-in failure. A build-only restore helper and
backup journals are documented in BUILD.md.
