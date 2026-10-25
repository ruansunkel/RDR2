# Environment and upstream provenance

Initial preflight on 2026-10-25 (historical; see current update below):

- macOS 27.0.1 (26A434), arm64.
- Apple Virtual Machine 1 / VirtualMac2,1; Apple M1 Max (Virtual); 8 GB RAM.
- Workspace volume: 251 GiB total, approximately 218 GiB available before builds.
- Swift 6.4 (swiftlang-6.4.0.34.1); existing Apple Command Line Tools.
- Rosetta execution check: `arch -x86_64 /usr/bin/true` fails, Bad CPU type.
- No `brew`, `wine`, /Applications/Highball.app, /Applications/Steam.app or Highball data found.
- Direct sysctl hardware reads are sandbox-restricted; filtered system_profiler supplied RAM/chip.
- Host M1 Max OS/RAM/disk/account availability: unknown; no host connection provided.

Official sources inspected read-only; no downloaded binaries were executed:

- Highball repository https://github.com/gauthierpiarrette/highball at
  `cabadb4cfaaad0ece66f7fad2206fdd7a0b41ffb`.
- Highball DB https://github.com/gauthierpiarrette/highball-db at
  `813666d7901969d683715f662cc686b03fc8267a`.
- Live RDR2 compatibility notes: https://gethighball.com/games/red-dead-redemption-2/.
- Engine manifest copied unchanged from `spike/engines/x64-crossover26.3-r27.json`.
- Runtime environment/layout derived from HighballKit `Bottle.swift` (DXMT overlay,
  sync), `EngineStore.swift` (`linkRuntime`, `baseEnvironment`), and `WineRunner.swift`.
- CC0 recipes copied unchanged from `recipes/launchers/{steam,rockstar}.json` and
  `recipes/games/red-dead-redemption-2.json`. License texts are in `licenses/`.

Selected inputs (not installed or locally gameplay-verified):

| Component | Pin |
| --- | --- |
| Wine | Wine 11 / CrossOver 26.3 tree, Highball r27 |
| MoltenVK | 1.4.2 + shadow-import-1 + linear-fallback-1 + shadow-readback-1 |
| DXMT | Highball 20260930T161516Z-a444716 |
| Runtime frameworks | Sikarugir Template 1.0.11, excluding Apple D3DMetal |
| Additional runtime | nvapi-stub 2, audiobuf 20261008 |
| Steam | Valve Windows installer; HTTPS official CDN; no upstream pinned hash |
| Game | Steam 1174180; Vulkan renderer, target initial test 1280×720 windowed Safe |

Every archive URL/SHA-256 and upstream license declaration is preserved in
`config/engine-upstream.json`. `packaging/report.py` emits an SBOM distinguishing
planned inputs from actually bundled runtime. The runtime contains mixed licenses;
redistribution/source obligations have not been completed here. Apple D3DMetal
and its timestamp shim are excluded. No HighballKit code is linked into the app.

The app uses sync=none consistently rather than automatically restarting Wine
services to toggle msync. This prioritizes a stable Steam/Rockstar environment;
game performance under this choice remains unmeasured. No custom Wine fork or
graphics translator is introduced.

## Current build update — 2026-10-25

The user confirmed this VM is the build Mac and the separate host is unavailable.
Rosetta now passes its execution check and native Steam is already present; neither
was installed by this agent. All six r27 archives were fetched and checksum-verified.
Actual isolated Wine initialization and Windows cmd work. The native bundled app
installed Windows Steam; its updater completed, and the user confirmed sign-in and
RDR2 downloading. No gameplay/host portability claim follows from these observations.

The original runtime's static audit exposed 21 packaging issues. The portable stage
replaces old media libraries with official GStreamer 1.28.7, source-built FFmpeg
9.0.2 demux libraries, and pinned Intel GLib/PCRE2/libintl. Exact pins and formula
revisions are in config/media-sources.json. The GLib bottle's observed version is
2.88.2 / ABI 8801 despite its formula version 2.88.3. Its real metadata is preserved.
No dylib ABI version is falsified. Original and patched binary hashes/load-command
operations are in runtime/relocation-changes.json. Runtime scripts omit the unused
wrapper SDK/graphics overlays and Apple's D3DMetal. GStreamer helpers use x86_64.

A dynamic test found a missing libintl locale symbol despite the static audit.
The matching gettext library fixes actual GStreamer startup. The final copied-app
media/Wine outcomes appear in notes/evidence/runtime-validation.md. A private
bootstrap prefix is retained under vendor/probes/native-steam, separate from every
existing installation and from the transferable app. Account data is not bundled.

157 license/provenance files were preserved from verified vendor packages and source
snapshots. Review of all mixed-runtime components and corresponding source remains
incomplete for public distribution. The development app is ad-hoc signed and has no
Developer ID/notarization claim. The active user download is deliberately untouched.
