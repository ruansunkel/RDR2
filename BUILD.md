# Build and validation

All commands below are **build Mac only**. The host receives one `.app`; it must
never need Swift, Python, Homebrew, Highball or a separate Wine installation.
Current status and actual checks are in STATUS.md. No working-game baseline has
been observed, so a full engine bundle is deliberately not represented as tested.

## Toolchain and workspace

Apple Silicon, macOS 14+, Apple Command Line Tools with Swift 5.9+ and Python 3.9+.
The observed build uses Swift 6.4 / macOS 27.0.1. No Swift package dependencies.
Use this checkout as the build workspace; `vendor/`, `logs/`, `.build/`, `.cache/`
and `dist/` are ignored. This intentionally keeps work in the authorized repository
instead of creating `~/Games/rdr2-agent` outside the workspace.

```sh
scripts/preflight.sh
scripts/check.sh
packaging/build-app.sh --launcher-only
packaging/test-relocation.sh dist/RDR2Launcher.app --launcher-only
packaging/package.sh dist/RDR2Launcher.app --development
```

The preview is an arm64 native UI with no Wine runtime. Its checksum, SBOM and
test report are produced in `dist/`. It has only an ad-hoc signature and has not
passed Gatekeeper, notarization, Finder, game or separate-host acceptance.
Swift checks use a Foundation-only executable because CLT does not ship XCTest.
Module/build caches stay inside the checkout. `--disable-sandbox` is a SwiftPM
build-tool option; it does not alter macOS Gatekeeper or host security settings.

## Establish the gameplay baseline first

On a suitable physical build Mac, follow plan.md phases 0–5 using the official
Highball release and a dedicated environment. Obtain Apple-managed Rosetta with
the user's approval if absent. Do not repurpose Doom or any other game prefix.
Use the pinned RDR2 Wine 11 engine, DXMT launcher mode and native Vulkan game
renderer. The source/recipe revision and exact upstream archive hashes are in
`notes/environment.md` and `config/engine-upstream.json`.

The intended host is a separate M1 Max; its actual macOS, RAM, free space and
Rosetta capability remain unknown. Check at least 150 GiB free for a fresh
download and current Steam storage requirements. The upstream RDR2 notes identify
8 GB as insufficient; the current 8 GB virtual machine cannot validate this game.
Record controllable Story Mode, renderer, resolution and any measured FPS in
`notes/benchmarks.md` and evidence reports. Never convert upstream reports into
local successes.

## Stage the pinned redistributable runtime

After the baseline gate, this build-time command downloads the six selected
archives from pinned official GitHub release URLs and verifies each SHA-256
**before extracting it**. It does not execute third-party binaries or install
anything globally. Review the script before running it.

```sh
python3 packaging/prepare-runtime.py vendor/rdr2-runtime-r27
```

The destination must be new. Extraction rejects traversal, escaping links, devices
and unsupported archive structures. It omits D3DMetal and its shim from the
Template runtime instead of redistributing Apple code. The preserved structure is
`engine/`, `frameworks/`, `renderers/dxmt/wine/`; `engine/lib` contains relative
runtime links matching Highball's EngineStore. Patched MoltenVK replaces the
runtime's stock copy and takes precedence over GStreamer's copy.

Before distributing, add a reviewed `licenses/` directory to the staged runtime:
all notices, component licenses, source locations, exact corresponding source /
patches or compliant source offer, including the mixed LGPL runtime. Record the
review and supplied files in an evidence report. Upstream license labels in the
manifest alone are **insufficient** for this gate. No Steam/game binaries,
authenticated prefix, registry, personal files or Apple D3DMetal may be staged.
The staging/downloading pipeline has fixture coverage but has not assembled real
archives here. An unsupported archive/link or failed audit requires investigation;
do not skip it or blindly rewrite third-party binaries.

```sh
packaging/build-app.sh --runtime "$PWD/vendor/rdr2-runtime-r27"
packaging/audit-deps.sh dist/RDR2Launcher.app
packaging/test-relocation.sh dist/RDR2Launcher.app --wineboot
packaging/sign-app.sh dist/RDR2Launcher.app -
packaging/package.sh dist/RDR2Launcher.app --development
```

`build-app.sh` backs up an existing app, compiles the launcher, copies only the
staged runtime, creates per-file/symlink integrity metadata and audits Mach-O
dependencies/RPATHs. It removes unused toolchain RPATHs from its own freshly
compiled native launcher, then signs it. Vendor binaries are never rewritten.
It fails on outside dependencies and unsafe symlinks; it does not assume a
`DYLD_*` override proves relocation. Auditing is conservative: inherited RPATHs,
dynamic loads and plugins still require actual runtime diagnostics. The relocation
script copies to a path containing spaces, clears the environment and optionally
runs `wine --version`, fresh `wineboot`, and `cmd /c ver`; it retains a new private
test prefix. It never touches existing game prefixes.

## Native first-run behavior and limitations

The app uses Foundation URLs for all mutable state. Runtime paths come from
Bundle.main, never PATH lookup or Highball directories. It initializes a fresh
prefix, applies the pinned registry settings with backups, and maps the selected
folder to R:. Wine's newly created document-folder host symlinks are backed up
and replaced with local directories to keep saves inside app data.

Wine processes use the upstream base environment and DXMT overlay. Sync is
consistently `none` for Steam and games to avoid killing a user's running game
when switching wineserver modes. This is a conservative compatibility choice;
the upstream msync performance optimization remains unverified and unimplemented.
The app does not add guessed Vulkan ICD overrides; r27's bridge/relative runtime
links locate patched MoltenVK. Dynamic Wine/MoltenVK/DXMT loading remains to test.

SteamSetup comes from the Valve HTTPS URL in the pinned CC0 recipe. The app checks
HTTP status, final origin, PE header and size, records its observed SHA-256, then
runs the normal installer. Valve's recipe supplies no pinned installer hash;
Authenticode is not independently verified. Steam's client updater remains official.
Installer windows/sign-in are visible; output is not logged. Prefix/client setup
is serialized and a per-user advisory lock rejects concurrent launcher instances.

Steam handles ownership, EULAs, library selection, progress and readiness. Install
uses `steam://install/1174180`, Repair uses `steam://validate/1174180`, and Play uses
`-applaunch 1174180`, through **Windows Steam inside the same prefix**. These routes
must still be tested against the installed client. A detected RDR2 process prevents
another Play request, but does not prove controllable gameplay. No manifest file
or cached state produces a fake ready/running/gameplay milestone. The UI asks the
user to select Play after Steam confirms completion; it does not scrape login data
or infer entitlement. Rockstar setup is delegated to Steam's first-run chain on
r27; standalone Rockstar recipe installation and the older-prefix error-113 fix
remain untested. No destructive registry repair or process killing is automated.

Network/client errors retain user data for retry. Steam itself resumes downloads.
Existing cached game authentication/offline behavior belongs to Steam/Rockstar.
No offline entitlement is promised. Fully automatic client-progress integration,
GUI end-to-end behavior, interruption recovery and app replacement await real tests.

## Signing, notarization and release

Ad-hoc development signing is supported. For Developer ID signing, supply your
legitimate identity and an independently tested entitlements plist; this project
does not invent Wine/JIT entitlements. `sign-app.sh` signs nested code inside out,
regenerates runtime hashes after binary signing, then signs the outer app.

```sh
packaging/sign-app.sh dist/RDR2Launcher.app 'Developer ID Application: YOUR IDENTITY' /path/to/tested-entitlements.plist
```

Use Apple's `xcrun notarytool submit` with an already configured keychain profile
on the actual zip, then `xcrun stapler staple` the app, validate it, and repackage
the stapled bundle. No credentials are stored in these scripts. Validate using
`codesign --verify --deep --strict`, `spctl --assess --type execute` and
`xcrun stapler validate`. Keep normal Gatekeeper/quarantine behavior intact.

Copy `notes/evidence/acceptance.template.json` to `acceptance.json`, complete its
observations and local report files only after real testing: clean-host Finder,
Steam sign-in/install/resume, Rockstar, controllable Story Mode, dynamic dependency
loads, moved bundle with spaces, replacement/persistence and licensing. The reports
are human observations; booleans are not automated proof.

```sh
packaging/package.sh dist/RDR2Launcher.app --release
```

Release packaging refuses missing evidence/runtime, invalid signatures, failed
Gatekeeper assessment or missing stapled notarization. Deliver the app/zip,
SHA256SUMS, SBOM.md, BUILD.md, TEST-REPORT.md and dependency-audit.json. The archive
is not bit-for-bit deterministic (signing timestamps, Swift toolchain and zip
metadata vary); inputs, ordering, checksums and commands are pinned/repeatable.

## Host acceptance and removal

The separate host must receive only the app, open it from Finder with normal
security, and authenticate within the real clients. Confirm no third-party
runtime loads from Homebrew/Highball/global Wine paths. Reopen after interrupted
download, move the app to another directory, replace it, and verify the existing
library and saves remain. Record actual failures and measured results.

Removing the app leaves `~/Library/Application Support/RDR2Launcher/` and the
chosen library intact. To roll back a build, restore its timestamped `.app` backup;
never automatically roll a prefix back across incompatible Wine versions. No
uninstall or data-deletion command is supplied. Existing Doom/Steam/Highball
installations and macOS security settings are untouched by the build scripts.
