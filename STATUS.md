# Status — 2026-10-25

**Highest execution milestone: read-only build preflight and tested launcher /
packaging implementation. No playable or standalone-runtime release is verified.**

## Observed build environment

macOS 27.0.1 (26A434), arm64, Apple M1 Max **Virtual**, 8 GB RAM, approximately
218 GiB free on a 251 GiB workspace volume. The Apple Command Line Tools and Swift
6.4 are present. Rosetta execution fails with `Bad CPU type in executable`.
No Homebrew, Wine, Highball app/data or Steam app were found. Hardware sysctl
reads are restricted; filtered system_profiler reports the virtual chip and RAM
without serial numbers. Full sanitized preflight is retained in ignored logs/.

The intended separate physical M1 Max host is inaccessible in this session; its
macOS, RAM, disk, Rosetta, signing behavior and game/account state are unverified.
This environment does not meet the game's baseline: 8 GB RAM is insufficient
according to the live upstream compatibility notes, and Rosetta is missing.
No global tools, Apple-managed prerequisites or game binaries were installed.

## Implemented

- Native arm64 Swift/AppKit UI with Install & Play, Play, Open Steam, Choose game
  folder, Repair (Steam validation), View logs and Quit.
- Crash-resumable persisted setup, timestamp/unique backups, per-user launch lock,
  serialized prefix/installer operations and isolated mutable data outside the app.
- Bundle-only Wine invocation, streaming runtime checksum verification, safe
  relative paths and a clean per-process environment from pinned upstream inputs.
- Official Valve HTTPS installer workflow/provenance, private prefix recipe
  settings, app-owned Documents directories and an R: mapping for Steam libraries.
- Steam install/validate/-applaunch requests with no credential interception or
  claim of readiness based on ACF files. Real Steam/Rockstar process behavior is
  untested; the user must press Play after Steam confirms download completion.
- Build-only checksum-pinned runtime staging with archive/symlink validation and
  D3DMetal exclusion; recursive Mach-O dependency/RPATH audit; inside-out signing;
  relocation/Wine smoke scripts; development/release packaging, SBOM/checksums.
- Release gate requiring actual observation reports, signatures, normal
  Gatekeeper assessment and stapled notarization. No security bypass is provided.
- README.md, BUILD.md, provenance/license snapshots, benchmark/evidence templates,
  preflight/diagnostic scripts and a .gitignore covering binary/account/local data.

## Verification

- Python packaging tests: **6 passed** (archive traversal/link escape,
  D3DMetal exclusion, inventory integrity, dependency resolution, release evidence).
- Swift Foundation core checks: **6 passed** (state backup/resume, corrupt state,
  path containment, changed engine bytes, Steam action arguments, relocated env).
- Shell syntax: passed for every shell script via scripts/check.sh.
- Initial builds exposed denied default module-cache paths, missing XCTest in CLT,
  a Swift main-actor entry issue and SwiftBuild dSYM restrictions. Fixed using
  project-local caches, Foundation-only checks, an explicit main-actor UI entry,
  and native SwiftPM release compilation with debug info disabled.
- App, signature, dependency audit, archive and relocation observations are
  recorded in notes/evidence/build-validation.md. Native compilation, ad-hoc
  signature verification, static dependency audit and copied-preview startup
  passed. The copied preview correctly reports no runtime. Release packaging
  rejects the missing engine. No valid signing identities were found.

Automated fixture/core tests do **not** verify Wine, authentication, Vulkan,
gameplay, clean-host operation, offline play, download resume or persistence
across real installed-game updates.

## Phase gates

| Phase | Result |
| --- | --- |
| 0 — Preflight | Build inventory completed; baseline/host gate blocked by 8 GB VM, missing Rosetta and inaccessible host |
| 1 — Tested Wine/Highball environment | Not installed; baseline gate not satisfied |
| 2 — Steam ownership/download | Not run; requires real client and user sign-in |
| 3 — Rockstar/Vulkan/Story Mode | Not run; no success claimed |
| 4–5 — Diagnosis/tuning | No game failure/FPS measurements; environment blockers recorded |
| 6 — Scripts | Implemented/syntax checked; actual game launch unverified |
| 7–8 — Standalone app/workflow | Native development preview and runtime tooling implemented; full runtime/dynamic loads/first-run gate unverified |
| 9 — Distribution/clean host | Development artifact only; Developer ID, notarization and host acceptance unresolved |
| 10 — Experimental DX12 | Not authorized or performed |

## Exact remaining work

Use a suitable physical build Mac and the separate host. Verify RAM/macOS/free
space and user-approved Rosetta, then establish the dedicated Highball r27
gameplay baseline (Steam/Rockstar login by the user). Follow BUILD.md to stage
and license-review the complete Wine/runtime/MoltenVK/DXMT inputs, audit their
real load paths, compile the full development app, execute relocation/Wine smoke
tests and debug any actual failures one variable at a time. Complete real Steam
installation/resume, Rockstar, interactive Story Mode, app move/replacement and
clean-host Finder tests before completing acceptance reports. Developer ID and
notarization credentials are needed for a normal Gatekeeper release.

Current artifact target: `/Users/agent/Projects/RDR2/dist/RDR2Launcher.app` and
`dist/RDR2Launcher-development.zip`. These are **launcher-only development
previews**, with no packaged engine and no assertion of zero external runtime
requirements for a working game. The planned engine is r27, MoltenVK 1.4.2 patched,
DXMT launcher overlay, native game Vulkan; none has been executed here.

All implementation/download/build changes stay in this checkout and ignored
temporary build paths. No existing Doom, Steam, Wine or Highball settings/prefixes
were changed. Removing the development app/checkout does not remove any existing
game installation. In a full app, user data persists under
`~/Library/Application Support/RDR2Launcher/`; an external library stays in the
chosen folder. No destructive reset/uninstall operation was executed.
