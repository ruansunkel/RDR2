# Executed evidence — 2026-10-26

## Standalone control app

The native **RDR2 MoltenVK Control.app** is built separately under dist/control-app/.
It contains the complete Wine/DXMT/media runtime and the exact rebuilt control
driver (SHA-256 68d55e39c301e5d4f87f0f2b8b5a940376495c3deade486bc0a533ba85b1ba2a).
Its signed metadata records the replacement and its own edition. The default data
folder and remembered-environment configuration use RDR2Launcher-MoltenVK-Control;
the existing standard selection and Steam state are not automatically reused.

- Native compile and 17 Swift core checks passed, including persisted data/selection
  independence between the standard and control editions. The 17 Python checks pass.
- Static dependency audit: 153 Mach-O files, zero failures. Nested/outer ad-hoc
  signatures and the exact replacement-library runtime hash passed verification.
- A complete copied app ran from a path with spaces and a cleared environment.
  Its own diagnostic selected moltenvk-control and the separate default folder.
- Fresh private Wine boot, Windows cmd, Wine media registration, GStreamer 1.28.7 /
  426 libav features and FFmpeg/GStreamer RTLD_NOW probes passed using that copy.
  Only the smoke test's new prefix/services were stopped afterward.
- The self-contained transfer archive is dist/RDR2-MoltenVK-Control-development.zip.
  It contains no game, prefix, account data or candidate patch. Host Finder/Gatekeeper,
  Steam/Rockstar authentication with this app, gameplay and tree behavior remain unverified.

The app is ad-hoc signed, not notarized. The smaller, earlier control-library ZIP
is separate from this app. Original launcher/runtime/game files remain preserved.

## Source control and isolated engine evidence

This is build-machine evidence. The physical host/tree scene was not accessible.
The user asked to infer the renderer from the current repository; its pinned r27
runtime was used, rather than claiming to inspect the host's installed app.

Machine: macOS 27.0.1, VirtualMac2,1, Apple M1 Max (Virtual), 8 GB RAM. CLT is
selected; full Xcode, system CMake/Ninja and an installed Highball home are absent.
The source control build succeeded using upstream's CMake path and a checksum-
verified local CMake tool, without changing the selected developer directory or
installing package managers, drivers or system libraries.

| Check | Observed result |
| --- | --- |
| Original component provenance | Archive hash matches the r27 manifest; actual dylib matches the staged/runtime-app driver |
| Historical source check | Build script and three patch files match the r27-introduction revision byte-for-byte |
| MoltenVK base | v1.4.2 resolves to db66022459ffb663aa2b50f6b018bc2e124f5edf |
| Fork comparison | Global heap default zero, argument-buffer default zero, coherent-image guard and blanket error clearing identified |
| Control sources | Only the exact three Highball patches; ten changed source files hash-verified |
| Dependencies | Five used CPM repositories at the ExternalRevisions commits; cached edits rejected |
| Control build | Release x86-64 dylib, upstream CMake backend; all three Highball markers present |
| Compatibility/exports | Compatibility major 1; no missing original `_vk*` exports |
| Dependencies/signature | System-only dylibs; normalized leaf install ID; ad-hoc signature verified |
| API configuration | 184-byte structure, 1.4.2 / Vulkan 1.4.357, heaps 1, argument buffers 1, private API 0 |
| Reference private-API capability | Requesting private API still reports 0 in the original driver |
| Isolated engine copy | Created only under vendor/tree-research/isolated-highball-home; no prefix/client/game copied |
| Control install and mapping | Separate test driver installed; lsof proved the exact path/hash in a diagnostic process |
| Real rollback | Original driver restored in test engine; original checksum verified |
| Source/app preservation | Original staged driver and existing app driver retain the original checksum |
| Python regression checks | 17 passed: 8 packaging + 9 experiment-isolation/recovery checks |
| Proposed candidate | Applies cleanly to the pinned patched control; left unapplied and uncompiled |
| Candidate gate | Builder refuses without matching control and recorded host baseline/game evidence |
| Development archive | CRC, control hash, standalone script imports, private-data exclusions and deferred-candidate behavior passed |

Reference dylib SHA-256:
`294e9ef77c6036ab4f4d93117d752b6e31fa6c8c4345bc085e062a6ee3ced80a`.

Control dylib SHA-256:
`68d55e39c301e5d4f87f0f2b8b5a940376495c3deade486bc0a533ba85b1ba2a`.

The machine-readable build.json, including compiler/SDK, exact flags, input hashes,
configuration probe and dependencies, accompanies the control. Raw build logs are
kept locally in logs/moltenvk-control-*.txt. The diagnostic mapping proof explicitly
says it is not an RDR2 process; it cannot satisfy the host-game acceptance gate.

No effective host launch environment, host save backup, same-scene video, game
control run, patched game run, tree improvement, visual regressions, FPS or memory
comparison has been verified. No such reports have been synthesized. The provided
plan's control-in-game gate remains pending; candidate construction and visual
acceptance must follow it. Nothing was posted to an upstream issue or PR.

The development archive contains a **control**, experimental source, instructions
and license notices. It has no candidate binary, game, prefix, account data or
private saves. It is not the existing RDR2Launcher app/ZIP and does not replace it.
