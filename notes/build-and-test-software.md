# Build and test software inventory — 2026-10-27

This inventory distinguishes project-local downloads and builds from software
that was already on the Mac. It covers the renderer investigation and the earlier
portable runtime preparation. Some local artifacts were prepared on the earlier
build Mac and carried with the project. The latest foliage/rock work reused the
existing toolchain and caches; it did not install a new system toolchain.

## Added locally for the renderer builds

| Software | Exact version or pin | Location and use |
| --- | --- | --- |
| CMake | 3.31.8 | Verified Kitware archive extracted to `vendor/tree-research/tools/cmake-3.31.8-macos-universal/CMake.app`; configures and builds MoltenVK. No global CMake installation. |
| CPM.cmake | 0.40.8 | Downloaded CMake package-management script at `vendor/tree-research/cpm/cpm/CPM_0.40.8.cmake`; fetches pinned source dependencies. |
| MoltenVK | 1.4.2, `db66022459ffb663aa2b50f6b018bc2e124f5edf` | Separate patched source/build trees under `vendor/tree-research/`; x86-64 dylibs copied into the separate diagnostic apps. |
| SPIRV-Cross | `6c09849fe88c48eaed08413aa022aaa136a3a057` | Source cache under `vendor/tree-research/cpm/spirv-cross/`; shader translation library linked into MoltenVK. |
| SPIRV-Tools | `0d6fd73ca73830ccab5fa1f00ed5ed40124e2c55` | Source cache under `vendor/tree-research/cpm/spirv-tools/`; linked build dependency. Its standalone test/executable builds were disabled. |
| SPIRV-Headers | `29981f65241605e08b0ede4cfeb999fe3b723c6a` | Headers cached under `vendor/tree-research/cpm/spirv-headers/`. |
| Vulkan-Headers | `e3b1eec08173d6b825cd3ac88c885a63b621504a` | Headers cached under `vendor/tree-research/cpm/vulkan-headers/`; used by MoltenVK and the native Vulkan probes. |
| cereal | `a56bad8bbb770ee266e930c95d37fff2a5be7fea` | Header-only dependency cached under `vendor/tree-research/cpm/cereal/`. |

Archive checksums and source pins are in
[`experiments/moltenvk-trees/pins.json`](../experiments/moltenvk-trees/pins.json).
Vulkan-Tools and Volk revisions also appear there as upstream revision metadata;
they were not among the five source dependencies fetched/used by this CMake build.

The captured-shader, heap, allocation, query and pixel-reading probes are programs
compiled from this repository into `vendor/tree-research/`. They are local test
executables, rather than separately installed applications.

## Already provided by macOS or the existing Apple tools

Observed on the current physical M1 Max: macOS 27.0.1, selected developer directory
`/Library/Developer/CommandLineTools`. These were used as existing tools; the
agent did not install them for the rendering fixes.

| Software/tool | Observed version | Purpose |
| --- | --- | --- |
| Apple Command Line Tools | Receipt `27.0.0.0.1788430756` | Existing compiler, SDK and command-line developer tools. |
| Apple Clang / Clang++ | 21.0.0, build `clang-2100.3.34.2` | Build MoltenVK and native C/Objective-C++ probes, targeting x86-64 and macOS 14.0 deployment. |
| Swift / Swift Package Manager | Swift 6.4, `swiftlang-6.4.0.34.1`; driver 1.168.6 | Build the native launcher and run its core checks. The Swift package has no external package dependencies. |
| macOS SDK | 27.0 | Existing SDK at the selected CLT SDK path; Foundation, Metal, CoreGraphics, ImageIO and CommonCrypto supply the probe APIs. |
| Python | 3.9.6 via `/usr/bin/python3` | Build, packaging, capture orchestration and standard-library `unittest`. No pip package is required. |
| Git | 2.54.0, Apple Git-157 | Source checkout, patch/provenance checks and requested commit/push. |
| GNU Make | 3.81 via `/usr/bin/make` | CMake's `Unix Makefiles` backend and the earlier FFmpeg build. |
| Apple `gpucapture` | `2027.0.39`, `/usr/bin/gpucapture` | Capture one verified game frame at a time. |
| Apple `gpudebug` | 1.0, `/usr/bin/gpudebug` | Replay saved frames and export draw-stage resources. |
| Rosetta 2 | Existing Apple runtime; x86-64 execution verified | Run x86-64 Wine, MoltenVK and the native GPU probes on Apple Silicon. No Rosetta installation was performed by this agent. |
| Apple/macOS utilities | System/CLT-provided | `codesign`, `otool`, `lipo`, `install_name_tool`, `pkgutil`, `cpio`, `shasum`, `ps`, `lsof`, `sample`, LLDB and the shell utilities used for inspection, extraction and signing. |

Full Xcode and a separately downloaded Graphics Tools application were not
installed for this work. Shader test compilation uses Metal's runtime APIs.
Homebrew, Ninja, Meson and a global Wine installation were not installed for the
build/test workflow. No npm dependencies were added.

## Earlier portable runtime preparation, retained for these app builds

These are runtime components or extraction inputs, rather than new global Mac
applications. Original pins are in
[`config/engine-upstream.json`](../config/engine-upstream.json) and
[`config/media-sources.json`](../config/media-sources.json).

| Component | Version | How it was prepared |
| --- | --- | --- |
| Wine engine | Wine 11.0 / CrossOver 26.3 tree, Highball r27 | Verified prebuilt archive extracted into the portable runtime and app bundles; Wine was not rebuilt or installed globally. The upstream engine includes Wine Mono 10.4.1 and Gecko 2.47.4. |
| DXMT | Highball `20260930T161516Z-a444716` | Prebuilt renderer overlay bundled for the Windows launcher/client path. RDR2 uses Vulkan through the rebuilt MoltenVK. |
| Runtime framework base | Sikarugir Template 1.0.11 | Selected prebuilt libraries extracted into the portable runtime; unused graphics overlays were excluded. |
| NVAPI stub / audio buffer component | NVAPI stub 2; audiobuf 20261008 | Verified prebuilt runtime components extracted from the pinned archives. |
| GStreamer runtime/development packages | 1.28.7 | Official `.pkg` archives expanded/extracted under `vendor/`; selected playback libraries/helpers copied into `vendor/GStreamer-1.28.7.framework` and app bundles. The macOS package installer was not run. |
| FFmpeg libraries | 9.0.2 | Built locally from verified source to `vendor/ffmpeg-install-x86_64/`. Only the required demuxing/parser libraries were enabled; standalone programs, external autodetection and x86 assembly were disabled. `make install` used this project-local prefix. |
| GLib | Observed package 2.88.2, ABI 8801 | Downloaded Homebrew bottle extracted locally. Its source formula is labelled 2.88.3; the actual package version was preserved. Homebrew itself was not installed. |
| PCRE2 | 10.47, bottle revision 1 | Verified bottle extracted under `vendor/pcre2-bottle/`; required GLib dependency copied into the runtime. |
| gettext / libintl | 1.0 | Verified bottle extracted under `vendor/gettext-bottle/`; matching locale library copied into the runtime. |
| Highball source checkouts | Highball `cabadb4cfaaad0ece66f7fad2206fdd7a0b41ffb`; engine `5d6bbe0c83f4592a8798abba48cc7e8f58feb492` | Source provenance, recipes and the engine's `gstreamer/unpkg.py` pbzx-format extractor. This extractor uses Python's standard `lzma` module and system `cpio`; it is not a separate installed pbzx tool. The Highball GUI was not installed for this workflow. |

## Clients installed inside Wine for end-to-end testing

Official Windows Steam and Rockstar Launcher/Social Club are installed in the
private Wine environments used to launch the purchased game. These are
self-updating clients, so their versions are not pinned in the build recipe.
The earlier workflow installed Windows Steam; Steam/game setup supplied Rockstar
components. The rendering work reused those clients, sign-ins and existing RDR2
files. RDR2 is the test application, rather than a build dependency.

Native Mac Steam and Rosetta were already present when the relevant later checks
observed them; their installation is not attributed to this agent. No client,
game, sign-in data or save backup is included in the Git changes.

## Validation and audit sources

Tool versions were read from the local executables and CLT receipt on 2026-10-27.
Build configuration was checked against the final artifact's ignored `build.json`:
Release, x86-64, macOS 14.0 deployment, existing SDK 27.0, CMake/Unix Makefiles,
heaps enabled, argument buffers enabled and Metal private API disabled.

`scripts/check.sh` runs shell syntax checks, the Python suite and Swift core
checks. The publication check passed all 18 Python tests and 17 Swift core checks.
The first attempt encountered a copied Swift module cache referring to the
earlier build Mac's absolute path. A fresh project-local cache/scratch pair
resolved it, without changing the system toolchain or deleting old artifacts:

```sh
RDR2_BUILD_CACHE_ROOT="$PWD/.cache/rendering-commit-20261027" \
RDR2_BUILD_SCRATCH="$PWD/.build/rendering-commit-20261027" scripts/check.sh
```

Both new renderer variants' complete source/patch pins were also reverified.
Exact-driver GPU results, source controls, app signatures/integrity and
the user's scene comparisons are recorded in
[`evidence/remaining-objects.md`](evidence/remaining-objects.md).
