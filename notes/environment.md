# Environment and upstream provenance

Observed 2026-10-25, not a separate-host test:

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
