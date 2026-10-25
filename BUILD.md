# Build and validation

These commands are **build Mac only**. The host receives one `.app`; its normal
workflow uses no Python, Swift, Homebrew, Highball or separately installed Wine.
Apple supplies Rosetta if needed. Steam/Rockstar sign-in and actual game download
remain official client workflows. STATUS.md contains current observed results.

The user clarified that build-Mac launch preparation comes first and the separate
host will test playability later. The 8 GB build VM is therefore allowed to run
Wine/Steam; no minimum-RAM gate prevents bootstrap. No gameplay is inferred from
build success, client startup, fake downloads, ACF files or process presence.

## Build tools and pinned inputs

Apple Silicon build Mac, macOS 14+, Apple CLT with Swift 5.9+ and Python 3.9+.
Observed toolchain: Swift 6.4 / macOS 27.0.1. The Swift package has no dependencies.
Project caches, sources and outputs stay in `.cache/`, `.build/`, `vendor/`, `dist/`.
No global package manager or Wine installation is performed.

The exact original engine is `x64-crossover26.3-r27` in
`config/engine-upstream.json`; all archives have pinned SHA-256 values. Replacement
media input pins are in `config/media-sources.json`. Upstream code used for build
inspection and the pbzx extractor is pinned as follows:

```sh
git clone https://github.com/gauthierpiarrette/highball.git vendor/highball
git -C vendor/highball checkout cabadb4cfaaad0ece66f7fad2206fdd7a0b41ffb
git clone https://github.com/gauthierpiarrette/highball-engine.git vendor/highball-engine-r27
git -C vendor/highball-engine-r27 checkout 5d6bbe0c83f4592a8798abba48cc7e8f58feb492
```

Do not overwrite existing vendor checkouts; the ones in this workspace are already
present. Review build scripts before executing them. No downloaded installer/script
is run by a curl pipe. The GStreamer packages are **extracted, never installed**.

## Reproduce the runtime

Use new destination paths; preparation/extraction refuses existing destinations.
The original unmodified archive stage is preserved for before/after comparison.

```sh
scripts/preflight.sh
python3 packaging/prepare-runtime.py vendor/rdr2-runtime-r27
python3 packaging/fetch-media.py ffmpeg gstreamer-runtime gstreamer-devel glib-bottle pcre2-bottle gettext-bottle
python3 packaging/extract-verified.py ffmpeg vendor/ffmpeg-source
python3 packaging/extract-verified.py glib-bottle vendor/glib-2.88.3-bottle
python3 packaging/extract-verified.py pcre2-bottle vendor/pcre2-bottle
python3 packaging/extract-verified.py gettext-bottle vendor/gettext-bottle
packaging/build-ffmpeg.sh
python3 packaging/prepare-gstreamer.py vendor/GStreamer-1.28.7.framework
python3 packaging/relocate-runtime.py vendor/rdr2-runtime-r27 vendor/rdr2-runtime-r27-portable-v3 --gstreamer vendor/GStreamer-1.28.7.framework
python3 packaging/collect-runtime-notices.py vendor/rdr2-runtime-r27-portable-v3
```

The official historical GLib formula's bottle contains package version **2.88.2**
with ABI 8801, despite the formula version 2.88.3. Its actual version, exact checksum
and observed load-command versions are retained; no version metadata is falsified.
The PCRE2 and gettext bottles satisfy its actual dependencies. Public GHCR bottle
fetches use the documented anonymous placeholder, with no account credentials.

The original Template GStreamer framework has older media/GLib ABIs than the engine
expects. The portable stage uses the official GStreamer 1.28.7 playback libraries,
matching GLib/PCRE2/libintl and a source-built FFmpeg demux runtime. FFmpeg decoding
for Wine remains in GStreamer's libav plugin. No Wine or graphics translator fork
is introduced. Unused Template renderers, wrapper SDK and alternate MoltenVK are
excluded, including Apple D3DMetal and its alias. DXMT remains in the selected overlay.

`relocate-runtime.py` records every load-command change and before/after checksum.
Short `engine/lib` aliases avoid exceeding upstream Mach-O header padding.
GStreamer helpers are thinned to x86_64 so they load the same Intel library stack
as Wine. Relative DXMT aliases resolve its ntdll/winemac imports to the same engine.
Changes occur only in a new stage and all changed/nested code is re-signed.

Vendor notices and license texts are preserved in `runtime/licenses/`. The mixed
Template libraries, Wine Mono/Gecko/fonts and exact corresponding-source mapping
still require a complete review before public distribution. `REVIEW-PENDING.md`
is retained, and the release gate stays closed. The artifact is for private testing.

## Build a separate transferable app

Keep the current app/prefix untouched while Steam is downloading. Use a different
output path for the updated transferable app:

```sh
scripts/check.sh
RDR2_BUILD_OUTPUT="$PWD/dist/host-test/RDR2Launcher.app" \
  packaging/build-app.sh --runtime "$PWD/vendor/rdr2-runtime-r27-portable-v3"
packaging/sign-app.sh dist/host-test/RDR2Launcher.app -
packaging/test-relocation.sh dist/host-test/RDR2Launcher.app --wineboot
packaging/package.sh dist/host-test/RDR2Launcher.app --development
(cd dist && shasum -a 256 -c SHA256SUMS)
```

For a UI-only preview, `packaging/build-app.sh --launcher-only` remains available;
that mode does not contain an engine and must not be treated as a working-game app.
An existing output app is backed up. Native release builds use project-local
module caches and SwiftPM's native backend with debug info disabled, avoiding CLT
SwiftBuild dSYM restrictions in this environment. Foundation-only checks run without
XCTest/Xcode. SwiftPM's `--disable-sandbox` changes only its build-tool sandbox.
No macOS Gatekeeper or system security setting is changed.

The build removes unused developer-tool RPATHs from our native executable, creates
a per-file/symlink runtime manifest, audits all Mach-O references and ad-hoc signs
the app. `sign-app.sh` signs nested code inside out, then regenerates runtime hashes
before signing the outer app. Pure resource framework directories without an
umbrella binary are not misidentified as signable code containers.

## Actual relocation and bootstrap checks

`test-relocation.sh` copies the complete bundle to a path containing spaces, uses
`env -i` and a system-only PATH, verifies runtime hashes and optionally starts Wine
in a **new private HOME/prefix**. The smoke test runs Wine version, wineboot, Windows
cmd, media registration, GStreamer/libav discovery and x86_64 `dlopen` checks. It
stops only that disposable prefix's services afterwards. Its build-only C probe
and compiler are not shipped as host prerequisites. The automation sandbox may
require approval for Wine's local socket; no sudo is required.

Build-only actual first-run entry (never point this at another game's prefix):

```sh
dist/host-test/RDR2Launcher.app/Contents/MacOS/RDR2Launcher \
  --bootstrap-steam --data-directory "$PWD/vendor/probes/a-new-bootstrap-test"
```

This uses the same coordinator as the GUI, with a private test HOME and persisted
data directory. It downloads the real Valve HTTPS installer, records its observed
SHA-256, installs it and opens Windows Steam. The upstream recipe supplies no
pinned Steam installer hash; HTTP status, final origin, PE header and size are
checked, while Authenticode is not independently verified. No account output is
logged. Steam's client updater remains official and can take 15–25 minutes.

The **currently active build session** already uses `vendor/probes/native-steam/`
and the original `dist/RDR2Launcher.app`. The user has signed in and reports RDR2
actively downloading. Keep using that existing Windows Steam window for Play when
ready. The transferable app contains no copy of this prefix or its credentials.

## Host workflow and remaining tests

Copy only `dist/host-test/RDR2Launcher.app` or the development archive to the host.
Open the app normally. Choose a persistent game folder, select Install & Play,
sign in within Windows Steam, and add/use the mapped R: library through Steam's
Storage settings. When Steam confirms completion, select Play. Steam → Rockstar →
RDR2 remains the entitlement chain. Complete any EULA/MFA in the official windows.
The actual game uses Vulkan over patched MoltenVK; DXMT serves the launcher UI.

The app uses bundle-relative paths and isolates mutable data under Foundation's
Application Support directory. Steam and game updates never write into the signed
bundle. Fresh-prefix document symlinks are backed up and replaced with local folders
so saves stay with app data. Configuration changes have timestamped backups. The
per-user launch lock and serialized setup prevent concurrent installer operations.
Sync is consistently none to avoid killing services when switching modes; msync
performance tuning remains untested. GStreamer scans only bundled plugins and puts
its registry in app data, preventing accidental host-plugin/cache dependencies.

Repair asks Steam to validate app 1174180. Install uses `steam://install/1174180`;
Play uses `-applaunch 1174180` inside Windows Steam. Steam is authoritative for
ownership, progress and readiness. The app never reads login credentials or marks
the game ready from an ACF file. It does not claim DRM-protected offline play.

The host is unavailable in this session. Finder/Gatekeeper, complete Rockstar/game
launch, controls/FPS, clean-host behavior, actual app replacement and resumed game
downloads remain to be observed. No simulated completion substitutes for these.

## Distribution security and removal

Current signatures are ad-hoc; no valid Developer ID identity was found. No normal
Gatekeeper/notarization claim is made. Public release requires a legitimate
Developer ID identity, independently tested Wine/JIT entitlements, inside-out
signing, notarytool submission using your own keychain profile, ticket stapling,
`codesign --verify --deep --strict`, `spctl --assess` and `xcrun stapler validate`.
Never disable Gatekeeper or remove quarantine recursively as a setup shortcut.

Complete `notes/evidence/acceptance.json` from the template only with real
observations and local reports, including licensing/source review. `package.sh
--release` refuses missing evidence/runtime, invalid signatures, failed assessment
or an absent stapled ticket. Build inputs and commands are reproducible; archive
bytes can vary with signatures, toolchain and metadata. SHA256SUMS identifies the
actual development archive.

Removing/replacing the app leaves `~/Library/Application Support/RDR2Launcher/`
and the chosen Steam library intact. Restore a timestamped app backup to roll back
code; never automatically roll a prefix across incompatible engines. No destructive
reset is provided. Native Steam, unrelated Wine/Doom installations, account data
and macOS security settings were not modified.
