# Observed build validation — 2026-10-25

Environment: macOS 27.0.1, arm64, Apple M1 Max Virtual, 8 GB RAM; Apple CLT/Swift
6.4. No Rosetta, Wine, Highball, Steam or separate host. No serial/account data
was collected. See notes/environment.md for upstream input provenance.

Observed commands and outcomes:

| Check | Actual result |
| --- | --- |
| `scripts/preflight.sh` | Inventory captured; arm64/macOS check passed; Rosetta unavailable; build/host gameplay gate blocked |
| `scripts/check.sh` | 6 Python packaging tests and 6 Foundation Swift checks passed; all shell scripts parse |
| `packaging/build-app.sh --launcher-only` | Compiled native arm64 executable and app; ad-hoc signed |
| `packaging/audit-deps.sh dist/RDR2Launcher.app` | 1 Mach-O, no unresolved dependencies or outside RPATHs |
| `codesign --verify --deep --strict --verbose=2` | Valid on disk; satisfies designated requirement |
| `codesign -dv` | Ad-hoc; no TeamIdentifier; no Developer ID/notarization claim |
| `otool -l` | Native launcher deployment target 14.0, SDK 27.0 |
| `packaging/test-relocation.sh … --launcher-only` | Copied to a path containing spaces; native diagnostic started under env -i / system PATH; runtime correctly reported absent |
| `packaging/package.sh … --development` | App archived; SHA256SUMS, SBOM, build/test docs produced in ignored dist/ |
| `packaging/package.sh … --release` | Expected exit 1: Release requires a full runtime |
| `packaging/build-app.sh --runtime vendor/missing-runtime` | Expected exit 1: Stage a complete engine with reviewed licenses first; existing preview preserved |
| `security find-identity -v -p codesigning` | 0 valid identities found |

The release compiler initially emitted an unused Command Line Tools Swift RPATH.
The build removes non-system absolute RPATHs from **our own native binary**, then
audits and re-signs it. No third-party Wine binaries have been patched or executed.
SwiftPM's native build backend and disabled release debug info avoid this CLT
environment's SwiftBuild dSYM restriction. Build caches stay inside the checkout.

Delivered locally (ignored build products):

- `dist/RDR2Launcher.app` — launcher-only preview, no Wine/graphics runtime.
- `dist/RDR2Launcher-development.zip` — checksum in `dist/SHA256SUMS`.
- `dist/dependency-audit.json`, `SBOM.md`, `BUILD.md`, `TEST-REPORT.md`.

The copied-preview test proves only native executable startup/relative bundle
resource discovery on this same build machine. It does **not** prove Wine dynamic
loading, Finder/Gatekeeper acceptance, a clean host, first-run client bootstrap,
Steam ownership/login/download/resume, Rockstar authentication, controllable Story
Mode, FPS, or persistence across real game/app updates. None of those has been run.
The default complete-runtime relocation test and --wineboot smoke test remain open.

No host installation, Windows VM, commercial wrapper, macOS prerequisite install,
Gatekeeper/quarantine change, account interaction or unrelated prefix modification
was performed. The next execution gate is a capable physical Mac with approved
Rosetta and real Steam/Rockstar user interaction, as described in BUILD.md.
