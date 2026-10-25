# RDR2 Launcher for Apple Silicon

A native macOS launcher and repeatable packaging tools for the Steam edition of
Red Dead Redemption 2, using freely available Wine 11, patched MoltenVK and DXMT.
The game uses Vulkan; DXMT serves Steam/Rockstar launcher components.

**Current deliverable is a launcher-only development preview, not a playable RDR2
distribution.** This environment is an 8 GB Apple virtual machine without Rosetta,
Highball or Wine. Gameplay and the separate clean-host acceptance gates are blocked.
See [STATUS.md](STATUS.md) for observed evidence and outstanding requirements.

Build the preview on an Apple Silicon Mac with command-line developer tools:

```sh
scripts/check.sh
packaging/build-app.sh --launcher-only
packaging/package.sh dist/RDR2Launcher.app --development
```

Open `dist/RDR2Launcher.app`. The preview displays the missing-runtime state and
cannot install or run a game. The full-runtime build procedure, signing and
acceptance requirements are in [BUILD.md](BUILD.md).

With a full verified runtime bundle, choose a persistent game folder and select
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
No commercial wrapper, VM, Apple D3DMetal or DRM bypass is part of the launcher.
