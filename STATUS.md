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
