# RDR2 Launcher for Apple Silicon

A native macOS launcher and repeatable packaging tools for the Steam edition of
Red Dead Redemption 2, using freely available Wine 11, patched MoltenVK and DXMT.
The game uses Vulkan; DXMT serves Steam/Rockstar launcher components.

**Current deliverable is a runtime-inclusive development app.** Its bundled Wine
11 initializes a fresh prefix, and the native launcher installed and updated real
Windows Steam on the build Mac. The user has signed in and reports RDR2 downloading.
Gameplay and a separate-host test remain unverified. See [STATUS.md](STATUS.md).

Rebuild on an Apple Silicon build Mac with command-line developer tools:

```sh
scripts/check.sh
RDR2_BUILD_OUTPUT="$PWD/dist/host-test/RDR2Launcher.app" \
  packaging/build-app.sh --runtime "$PWD/vendor/rdr2-runtime-r27-portable-v3"
packaging/package.sh dist/host-test/RDR2Launcher.app --development
```

The transferable app is `dist/host-test/RDR2Launcher.app`; the archive is
`dist/RDR2Launcher-development.zip` with `dist/SHA256SUMS`. This is ad-hoc signed,
not notarized. No Steam/game files or account state are inside it. The initial
launcher-only preview can still be built with `--launcher-only`.

The full runtime preparation, source pins, signing and remaining distribution
requirements are in [BUILD.md](BUILD.md). The original app at
`dist/RDR2Launcher.app` remains in place for the active build-Mac Steam session;
use the **host-test** artifact for transfer.

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

The active build-Mac download uses the isolated data directory
`vendor/probes/native-steam/`. Keep using **that existing Windows Steam window**
for download completion and Play; opening a launcher with a different data directory
creates a separate prefix. Build-Mac sign-in/download state is intentionally excluded
from the transferable app. No development tool or manually configured environment
is needed on the host; Apple-managed Rosetta and normal client sign-ins still apply.
