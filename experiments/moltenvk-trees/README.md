# RDR2 tree-rendering experiment

**Paused at the user's request.** The selected tree is fixed in the tested scene,
but rocks and some foliage still disappear. Resume from
[the checkpoint](../../notes/checkpoints/2026-10-26-rendering.md); remaining objects
have not yet been isolated or captured.

The user has confirmed that **RDR2 Trees Occlusion Diagnostic.app** fixes the tree
problem in the tested Story Mode scene. Use the already built app at
`dist/tree-occlusion/RDR2 Trees Occlusion Diagnostic.app`; it reuses the candidate
Application Support environment and existing local game files and saves.

The driver bypasses only HiZ depth rejection in the complete SHA256-matched
captured tree-culling shader. Frustum, viewport, fade and LOD checks remain.
RDR2's exact driver mapping and native shader activation were verified before the
user's positive result. Heaps and Metal argument buffers remain enabled. This is
a narrow workaround; the underlying heap defect is unproven, and performance,
other locations and extended stability are unmeasured. Extra geometry may be drawn.
See [HOST-CANDIDATE.md](HOST-CANDIDATE.md) for evidence and limitations.

The reproducing build mode is `candidate-tree-occlusion`. Its pinned patch and
helper fingerprints are in `pins.json`; packaging requires exact-driver allocation
and query checks plus the captured-shader GPU controls. The original, control and
previous candidate apps are preserved. Acceptance is recorded separately from the
signed app bundle, which is unchanged after the user's confirmation.

## Earlier comparisons

Revision 3, argument-buffers-off and query-results candidates all retained the
visible tree issue. The earlier dedicated-buffer bypass never exercised its
changed allocation path in RDR2, so it did not rule out a heap problem. The query
candidate backports [upstream PR2794](https://github.com/KhronosGroup/MoltenVK/pull/2794),
which passes its own GPU regression but did not fix the visible trees.

With the pinned dependencies, reference runtime and truthful host control evidence
prepared, reproduce that separate candidate using:

```sh
python3 experiments/moltenvk-trees/build.py --mode candidate-query-results \
  --control-evidence vendor/tree-research/host-private/control-evidence.json --jobs 6
python3 experiments/moltenvk-trees/probe-queries.py \
  --candidate-artifact vendor/tree-research/artifacts/candidate-query-results
python3 experiments/moltenvk-trees/probe-gpu.py \
  --candidate-artifact vendor/tree-research/artifacts/candidate-query-results
python3 experiments/moltenvk-trees/build-candidate-app.py \
  --artifact vendor/tree-research/artifacts/candidate-query-results \
  --output 'dist/tree-query-results/RDR2 Trees Query Results.app'
```

GPU probes require the physical host GPU. App packaging requires their exact
driver/source hashes and refuses an existing output app. Reuse the already copied
candidate game/data folder; do not rerun the initial clone to switch drivers.
The query test has fixed native events for actual query use and for an observed
availability difference that the old copy offset would have produced.

The earlier handoff below describes the build-machine control stage. The host
builder additionally accepts `user-reported-signed-control-app` evidence with a
recorded observation and verified Control app/input hashes, without claiming
video or historical game mappings. The capture-based evidence path remains.

For a double-clickable host test, use **dist/RDR2-MoltenVK-Control-development.zip**.
It contains **RDR2 MoltenVK Control.app**, with the full bundled runtime and rebuilt
control driver. Its default Steam/data folder is separate from the regular launcher.
The app requires no Python, Highball or developer tools on the host. See
[CONTROL-APP.md](CONTROL-APP.md) for opening it and reusing the game download.
This remains a control comparison, with no proposed tree-fix patch included.

To reproduce the standalone app from the complete project and prepared runtime:

```sh
python3 experiments/moltenvk-trees/build-app.py
```

The builder refuses existing app/archive destinations; use new --output and
--archive paths for another build. It regenerates integrity metadata, signs nested
code and the outer app, and verifies that the bundled control bytes are unchanged.
The earlier small moltenvk-tree-control-development.zip contains the library/tools,
rather than this full launcher; the app builder requires the complete project.

The control library is built and its isolated install/rollback is tested. **No tree
fix is verified.** The candidate patch remains unbuilt until the control launches
RDR2 and reproduces the scene on the physical host. The original launcher ZIP,
runtime, Steam installation, game files and account state are unchanged.

See [COMPARISON.md](COMPARISON.md) for the findings, [pins.json](pins.json) for exact
inputs and [PLAN.md](PLAN.md) for the supplied plan. The reference is inferred from
this repository: r27 Wine 11, x86-64 MoltenVK 1.4.2 with three Highball patches.
No Highball app version or effective in-game environment was inferred from source alone.

## Reproduce the control

Run from the project root on an Apple Silicon build Mac with Rosetta, Apple CLT
and Python 3.9+. All fetched tools, sources and caches stay under vendor/tree-research.
No package manager or global installation is performed. Full Xcode is not needed
for this upstream CMake backend; Highball's release uses a different Xcode backend.

```sh
python3 experiments/moltenvk-trees/build.py --prepare-only
python3 experiments/moltenvk-trees/build.py --jobs 2
```

The output is `vendor/tree-research/artifacts/control/`, containing the ad-hoc
signed libMoltenVK.dylib and build.json. CMake 3.31.8 and CPM 0.40.8 are downloaded
from their publishers and hash-checked. Source and dependency commits, patch hashes,
modified file hashes, compiler, SDK and configure flags are pinned/recorded. The
script rejects unexpected source edits and mismatched reused dependencies.

The control preserves heaps and argument buffers and keeps private API disabled,
matching the inspected binary. It does not copy the fork's validation-error bypass.
The configuration probe is built for x86-64 from the actual upstream headers.
It establishes loading/configuration, not Vulkan rendering or gameplay.

`python3 experiments/moltenvk-trees/package.py` creates
`dist/moltenvk-tree-control-development.zip` and a separate
`dist/moltenvk-tree-control-SHA256SUMS`. It includes the control, pinned experimental
sources, build/install/rollback tools and notices, with the same relative project
layout. Extract it and run commands from its top-level directory. The original
launcher archive/checksum is preserved. The experiment archive contains no game,
prefix, account state, test home or build-tool/dependency caches.

## Prepare the host test and preserve saves

Before copying an active game environment, close that environment's game and
Windows clients normally so its registry/saves are flushed. Back up the host's
actual RDR2 Profiles directory separately; no host saves have been backed up here.
Use a private new destination, such as vendor/tree-research/host-private/save-backup:

```sh
python3 experiments/moltenvk-trees/engine.py backup-saves \
  --profiles '/actual/Documents/Rockstar Games/Red Dead Redemption 2/Profiles' \
  --destination "$PWD/vendor/tree-research/host-private/save-backup"
```

Set `TEST_HOME` to a NEW absolute directory, separate from the normal Highball home.
Set `SOURCE_ENGINE` to the installed r27 engine directory (containing manifest.json,
engine/ and frameworks/). This project's portable r27 stage is also accepted:

```sh
TEST_HOME="$PWD/vendor/tree-research/host-tree-test"
SOURCE_ENGINE="$PWD/vendor/rdr2-runtime-r27-portable-v3"
python3 experiments/moltenvk-trees/engine.py clone \
  --source "$SOURCE_ENGINE" --test-home "$TEST_HOME"
python3 experiments/moltenvk-trees/engine.py install \
  --test-home "$TEST_HOME" --artifact "$PWD/vendor/tree-research/artifacts/control"
```

The tool creates a separately named engine and checksum-verified rollback copy
inside the new home. Existing destinations, unexpected source hashes and outside
runtime links are refused. Only a home created by this tool can be modified. It
refuses replacement of a loaded test dylib, keeps a pending-operation journal and
can roll back an interrupted replacement. The original shared engine is untouched.

Highball's inspected source supports `HIGHBALL_HOME` and enumerates installed engine
directories by their manifests. Start a **separate test Highball process** with
`HIGHBALL_HOME` set to this new home; select x64-crossover26.3-r27-rdr2-tree-test.
Do not change Highball's normal home setting or allow an already-running normal
instance to route the test into its original home. Confirm the test application's
displayed storage location before proceeding. This separate-home UI/game workflow
has not been exercised here because Highball is not installed in this VM.

Create a test game environment in that home. Highball's duplicate-bottle code copies
the prefix but leaves its engine selection to settings; duplicating a bottle alone
does not clone a shared engine. If reusing a copied bottle, use a copy made with its
clients closed, and explicitly select the test engine. Keep private client data out
of patches, reports and the experimental archive. Reuse the separately copied game
files through Steam verification as described in the project's HOST-TEST.md.

## Baseline, control and loaded-library evidence

Record macOS, RAM/GPU, actual Highball version/engine, resolution, graphics settings,
the complete effective MVK variables and launch options. The allowlisted environment
in config/engine-upstream.json is the launcher's default, not proof of host Highball
variables. Record variable names/values from that test environment without copying
its account data or complete client logs.

Choose a fixed save/location. With the original engine, record a stationary camera
pan showing entire trees vanish. Repeat with the control, identical settings and
same scene. Verify Steam/Rockstar sign-in, menu and Story Mode controls. Keep water,
reflections, shadows, vegetation and terrain visible for comparisons.

While the control game is running, obtain the actual RDR2 macOS process PID and run:

```sh
python3 experiments/moltenvk-trees/engine.py prove-loaded \
  --test-home "$TEST_HOME" --pid ACTUAL_RDR2_PID \
  > "$PWD/vendor/tree-research/host-private/control-loaded-in-rdr2.json"
```

This examines only MoltenVK file mappings and hashes; it does not inspect command
arguments or authentication. The loaded path must be in this test engine. The
provided diagnostic-process proof is explicitly **not** RDR2 loaded-library evidence.

Copy control-evidence.example.json into that private directory. Fill it only with
observed results, the actual control/loaded hashes and absolute capture/report
paths. A failed or untested control does not permit the candidate build.

## Candidate, only after the control succeeds

```sh
python3 experiments/moltenvk-trees/build.py --mode candidate \
  --control-evidence "$PWD/vendor/tree-research/host-private/control-evidence.json"
```

The builder first requires matching control bytes, reported controllable Story Mode,
a reproduced baseline and existing capture/loaded-report files. This is a recorded
human gate; the builder cannot itself judge video content or interactive controls.
It then prepares a separate candidate source/build and uses the same configuration.
There is no candidate binary in the current handoff.

Install only into the test home with clients closed. First compare the candidate
with its new variable absent; then set only `RDR2_MVK_DEDICATED_BUFFER_NO_HEAP=1`
in the test environment. This bypasses heaps only for eligible dedicated buffers,
preserving image heaps, external resources, argument buffers and validation. Do
not set MVK_CONFIG_USE_MTLHEAP=0. Confirm the dedicated-buffer marker appears and
prove the candidate library is loaded in RDR2; otherwise the experiment was not
demonstrated to run. The candidate's effectiveness and rendering safety are unknown.

| Run | Required observation | Current evidence |
| --- | --- | --- |
| A: original engine | Reproducible same-scene tree disappearance | User report only; no capture here |
| B: rebuilt control | Starts Story Mode, same scene/behavior | Build/loader passed; host gameplay pending |
| C0: candidate, flag absent | Behavior matches control | Deferred |
| C1: candidate, flag 1 | Trees remain visible; allocation marker appears | Deferred; hypothesis |
| D: repeat C1 | Multiple starts and prolonged play without regressions | Deferred |
| E: rollback | Original behavior returns | Dylib bytes restored here; game behavior pending |

Measure the same scene's frame times, FPS and memory, plus nearby/distant trees,
slow/fast pans, day/night, water/reflections, shadows, lighting, transparent foliage
and terrain streaming. Report adverse effects. A shader/culling/resource-lifetime
investigation remains necessary if the controlled experiment does not explain it.

## Roll back

With test clients closed:

```sh
python3 experiments/moltenvk-trees/engine.py rollback --test-home "$TEST_HOME"
```

The original driver is restored only inside the copied engine, after validating
the backup, current/journaled bytes and that it is not loaded. Its hash must match
pins.json's reference_dylib_sha256. The existing transfer app and normal Highball
home require no restore because this experiment never modifies them.

Only development artifacts are provided. The library is ad-hoc signed, not notarized.
The macOS 14 deployment setting does not assert compatibility there; the build was
performed with the installed macOS 27 SDK. Apache-2.0 MoltenVK and Highball license
texts/source attribution accompany the patch set. Public distribution and an
upstream PR remain inappropriate before source/licensing review and visual acceptance.
