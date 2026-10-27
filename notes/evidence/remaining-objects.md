# Rocks, foliage and heap investigation — 2026-10-27

The selected tree, foliage and rock workarounds are user-confirmed in their
tested scenes. The current accepted app includes all three captured-shader guards.
The sections below preserve the investigation chronologically, including earlier
pending milestones. Original numeric depth and the underlying heap cause remain
unreproduced.

## Capture session

The user confirmed the game was closed. Normal isolated-client shutdown timed out
with a leftover Steam helper. The exact candidate Wine server and its open prefix
directory were verified; eight save files were copied and hash-verified, with
registry backups, before stopping only that idle candidate session. The unrelated
Wine device process was preserved. Private recovery evidence is under
`vendor/tree-research/host-private/before-idle-session-stop-20261027T042709Z/`.

`switch-host-app.py` now checks whether a Wine server actually holds the selected
prefix before requesting Steam/Windows shutdown. Previously, sending `-shutdown`
to Steam in an already closed prefix could boot Steam and leave its helpers
running. The tool still refuses a running game, uninspectable live Wine server or
active candidate session at the backup boundary. Four tests cover the closed
case, exact prefix matching, inspection failure and server-exit race.

The same signed `dist/tree-occlusion/RDR2 Trees Occlusion Diagnostic.app` was
reopened with capture enabled. Eight saves were backed up and verified again.
RDR2 PID78582 was subsequently verified mapping the original working driver
`f829744a02ed35f3fcf30a2f434a934f0441aa20af45be5f1f0d21b18a72b5cc`.
Apple's capture service listed that exact PID and its WineMetalLayer boundary3920.
These are observations at verification time, not a permanent process assertion.
The user selected foliage just above Arthur’s head. Its visible-state one-frame
capture completed successfully (10,200,124,641 bytes) at
`vendor/tree-research/host-private/captures/game-b307789ece8e44b88a4c968c16e59890/`.
Its exact PID/renderer and native tree-shader bypass activation were verified.
A separate `foliage-pair-active.json` preserves the original tree-pair manifest.
The missing pose has been requested; no replay is active.

## Small heap-integrity control

New probe: `experiments/moltenvk-trees/probe-hiz-heap.mm`.

It uses the nine captured 128×72 R32Float textures, seven mips each, at their
recorded placement offsets. It renders a different numeric pattern to every
texture/mip, then reads every texel through a compute shader argument buffer.
Writing all nine textures before reading any also checks for corruption between
those non-overlapping placements. Eight patterns are tested in each mode:

| Allocation | Values checked | Mismatches |
| --- | ---: | ---: |
| Standalone textures | 884,304 | 0 |
| Shared, tracked placement heap | 884,304 | 0 |
| Same heap with allocation-wide aliasable parent buffer | 884,304 | 0 |

Executed as x86-64 under Rosetta on the Apple M1 Max. The parent buffer remains
alive for the GPU work. Its bytes are not used to reconstruct optimized texture
contents. Private numeric report:
`vendor/tree-research/host-private/hiz-heap-probe-20261027.json`.

This synthetic control does **not** reproduce the original depth, complete game
resource layout, allocation reuse, Vulkan barriers, residency sets or concurrent
queue activity. Passing it does not rule out a heap or synchronization fault.
There is no evidence here that the original heap defect is fixed or reproduced.

Reproduce after preparing the existing captured placements, choosing a NEW report:

```sh
clang++ -arch x86_64 -mmacosx-version-min=14.0 -fobjc-arc -Wall -Wextra \
  -framework Foundation -framework Metal \
  experiments/moltenvk-trees/probe-hiz-heap.mm \
  -o vendor/tree-research/probe-hiz-heap
vendor/tree-research/probe-hiz-heap /absolute/path/hiz-placement.json \
  /absolute/path/new-heap-report.json
```

The probe refuses unexpected dimensions, invalid or overlapping placements, GPU
errors and existing report files; mismatching texels produce exit3.

## Next evidence

Capture one rock or foliage patch visibly present, then absent, with the working
tree workaround active. Identify its draw and producer before changing another
shader. The earlier trace includes additional HiZ shader variants; their mere
presence does not identify them as the cause of the remaining disappearance.
Large replay analysis must wait for the game to be saved and closed.

## Foliage producer isolated

The user selected foliage just above Arthur's head, then confirmed it missing
slightly above and to his right after turning the camera. Both one-frame captures
completed with the same RDR2 PID78582, working tree driver and layer3920:

- Visible: `game-b307789ece8e44b88a4c968c16e59890`, 10,200,124,641 bytes.
- Missing: `game-472e5530fc1b4067a5ec39e9f06d7eef`, 10,550,307,524 bytes.

The user then saved and closed the game. Replays were opened sequentially; no
large replay ran alongside RDR2. Exact paths and analysis history are recorded in
the separate private `captures/foliage-pair-active.json`. The original tree pair
is preserved.

A foliage stem at visible pixel(635,325) first appears in
`/commands/cb0/re108/draw32` (API12756, pipeline@rps91). The preceding draw's
pixel is black; the selected draw produces RGBA(206,177,127,255). The selected
mesh has 354 indices/708 bytes and 6,768 bytes of vertex data, both byte-identical
to the matched missing-frame mesh at `/commands/cb0/re111/draw35` (API13357).
Both use the same packed transform table GPU address0x15e6994d00.

| Instance list | IDs |
| --- | --- |
| Visible frame | 7,10,16,17,21,45,75,85,113,131,136,137 |
| Missing frame | 7,10,16,45,63,69,135 |
| Missing inputs, native GPU with HiZ disabled | 7,10,16,17,45,63,69,75,85,135,136,137 |

Five previously visible IDs(17,75,85,136,137) survive the missing camera's other
culling checks. The difference in IDs21,113,131 is not attributed to HiZ.

The exact missing-state producer is `/commands/cb0/ce7/disp80`, API911,
pipeline@cps68. Its descriptor set1 slot2 writes GPU address0x1545258960, precisely
the compact instance list consumed by the selected draw. Set1 slot9 reads the
same packed transform table. The small camera, wind, auxiliary, globals, clump,
LOD, object, transform, extra and indirect-argument buffers were extracted at
that dispatch. The complete shader body SHA256 is
`7d71e03178769c66f09ff9247f18e7d686634b23ca4759521e180ae677b2b739`.

`probe-captured-foliage.mm` compiles that exact shader with those inputs and
synthetic 128×72 R32Float depth with **explicitly seven** mip levels. Six fast/
precise math and depth controls pass. Depth10000 rejects all instances; the new
SHA256-guarded helper retains the same twelve valid instances in all six cases.
Modified-source, unrelated-source and disabled-switch guards leave source
unchanged. Reports are under the missing analysis directory; the private summary
is `host-private/captured-foliage-workaround-results.json`.

This supports an additional diagnostic occlusion workaround. Original numeric
depth and the heap fault remain unreproduced. It does not prove that any rock
uses this shader, and it may increase overdraw.

The separate `candidate-object-occlusion` source applies the new foliage patch
after the existing tree patch. Both complete-source guards remain independent;
the old working app/source/artifact are preserved. Native events distinguish
`foliage-hiz-bypass-applied` from the existing tree marker. Build, exact-driver
regressions, packaging and user visual acceptance follow before claiming a fix.

## Candidate build and scoped switch

The new driver built successfully with SHA256
`e0e54e0efb62103a0bdb3d712ea366215d2ccf60a44a8e4da987aaa53e674668`.
All seven allocation/policy checks and the query regression passed against those
exact bytes. All 17 Python checks pass. The separate app at
`dist/object-occlusion/RDR2 Objects Occlusion Diagnostic.app` passed deep/strict
signature and runtime-integrity verification. The original tree app still has
its original `f829744a...` driver.

The old isolated clients shut down normally. Eight saves were backed up and
hash-verified before the new app was launched with the same local game and
sign-ins. No game redownload or graphics-settings change was made. See private
`switch-object-occlusion.log`, `package-object-occlusion.log` and
`object-occlusion-build-validation.json`. Actual new-game renderer mapping, native
foliage activation and the user’s same-scene visual result are pending.

RDR2 PID4514 subsequently loaded the exact new driver. Native events confirm
`foliage-hiz-source-7d71e03178769c66f09ff9247f18e7d686634b23ca4759521e180ae677b2b739`
and `foliage-hiz-bypass-applied`. A different shader fingerprint79f75409... was
left unchanged. Evidence: private `candidate-object-occlusion-loaded-in-rdr2.json`.
The user subsequently returned to the same scene and confirmed **"Stays visible"**
when asked to repeat the camera turn. This confirms the selected foliage
workaround in that scene. The rock question was not answered; do not infer rock
acceptance. Original numeric depth and the heap root cause remain unreproduced;
other locations, performance and extended stability remain unmeasured.

Private acceptance evidence is
`host-private/object-occlusion-foliage-user-acceptance.json`. The separate foliage
pair manifest records this result. No game/process, renderer, signed bundle or
graphics-settings changes were made while recording acceptance.

## Rock example pending

The user subsequently confirmed that only rocks remain and offered an example.
Read-only checks verified the accepted object renderer in PID4514, but its
`MTL_CAPTURE_ENABLED` flag was absent and Apple reported no capturable processes.
The user has been asked to describe the rock's screen position, save near it and
quit normally before a same-build capture-enabled relaunch. No restart or rock
capture has occurred yet. Private state: `host-private/rock-investigation-state.json`.

The switch tool now has an explicit `--capture-new-app` route for subsequent
candidate builds. It shuts down through the old runtime, then constructs the
capture-enabled launch environment from the new app's runtime. The original
`--capture-session` still requires the same app on both sides. These flags are
mutually exclusive. Five scoped session/environment tests and all 18 Python
checks pass. The signed accepted renderer/app has not been changed.

The user identified the example rock behind Arthur’s face and confirmed the game
saved and closed. The accepted object app was then relaunched capture-enabled
after normal scoped client shutdown and eight verified save backups. RDR2
PID11326 was verified mapping the same e0e54e0e... driver and listed as capturable
with WineMetalLayer3920. The visible-rock pose is pending; no rock frame has been
recorded yet. The rock-pair manifest is separate from the accepted foliage pair.

## Rock draw and culling producer isolated

The user confirmed the example rock visible, then missing after a camera turn,
and saved/closed RDR2. Both one-frame traces use PID11326, the accepted
e0e54e0e... renderer and layer3920. Native events and captured MSL confirm the
tree and foliage bypasses were active throughout this pair:

- Visible: `game-8ece32438bee484da3dcac58bbe9bf70`, 9,155,203,614 bytes.
- Missing: `game-055da369aafe42dfb053bbf42dac85ac`, 9,530,456,432 bytes.

The user briefly paused the investigation, then explicitly resumed it. No replay
had started during the interruption. The game was verified closed and no replay
sessions were active before opening the visible frame. Owned sessions41 and44
were used sequentially and released after evidence export. The separate
`captures/rock-pair-active.json` records authoritative analysis paths.

The large boulder behind Arthur first produces visible pixel(720,360) in
`/commands/cb0/re98/draw76`, API6355. The preceding draw has terrain color
RGBA(236,240,245,255); the boulder changes it to(88,84,83,255).
The matched missing-frame draw is `/commands/cb0/re98/draw77`, API6342.
All three vertex streams and the 5,970 UInt16 indices are byte-identical across
the pair. Both draws read transform table GPU address0x15e6e8da00.

| Observation | Visible | Missing |
| --- | --- | --- |
| Index count | 5,970 | 5,970 |
| Main draw instance count | 1 | 0 |
| Selected compact instance IDs | 73 | none |
| Missing-frame shadow draw | — | Still 1 instance at API2052 |

The exact main-view producer is `/commands/cb0/ce7/disp18`, API646,
pipeline@cps77. Descriptor set1 slot1 writes GPU address0x1543b621e0, exactly
the compact list consumed by the missing draw. Slot8 reads the same transform
table. The complete shader body SHA256 is
`95a4b16527bcfbe7d4818bc0e837d88257ecaf9419be0ac694062d7be2080ad6`.

Small camera(272B), globals(928B), object(132B), transforms(6464B) and draw-argument
(120B) inputs were extracted at that dispatch. Its four compact output lists are
404B each; the transform table has101 entries and the original dispatch uses
two64-thread groups.

`probe-captured-rock.mm` runs this exact shader and captured inputs on the M1 Max
with synthetic 128×72 R32Float depth and explicitly seven mip levels. Disabling
HiZ retains instance73 with the missing camera. Clear depth and depth300 also
retain73; depth10000 rejects it. Fast and precise controls agree. The new
complete-SHA256-guarded rock helper retains73 in all six cases, and its changed-
source, unrelated-source and disabled-switch controls leave source unchanged.
Reports and input hashes are summarized in private
`captured-rock-workaround-results.json`.

The new `candidate-rock-occlusion` source preserves both accepted shader guards
and adds only this third captured rigid-object shader. Its native switch is
`RDR2_MVK_ROCK_HIZ_BYPASS=0` on a future launch; native events distinguish
`rock-hiz-bypass-applied`. Heaps, argument buffers and the remaining culling
checks stay enabled. Original depth, a heap root cause and the user's visual
rock result remain unverified. This may draw extra objects and affect performance.

## Rock candidate build verification

The new renderer built with SHA256
`b914dc101ebcc70a415caabc69a2587efcb6770ee0ca27d7db2285935038fdce`.
All seven exact-driver allocation/policy checks and the query regression pass;
all 18 Python checks pass. The separate app at
`dist/rock-occlusion/RDR2 Rocks Occlusion Diagnostic.app` passes deep/strict
signature and runtime-integrity verification. Its signed profile includes all
three guarded workarounds. The accepted object app retains its original e0e54e0e...
driver. Private validation: `rock-occlusion-build-validation.json`.

The scoped switch is using `--capture-new-app`, which shuts down through the old
runtime and launches capture-enabled through the new app’s runtime. Exact new-game
renderer mapping, native rock activation and user visual acceptance are pending.

The capture-enabled switch completed with normal scoped client shutdown and
eight verified save backups, reusing the same local game and sign-ins. RDR2
PID42980 maps the exact b914dc10... driver. Native events confirm all three
SHA256-guarded bypasses applied, including `rock-hiz-bypass-applied` for the
selected rigid-object shader. The new game is listed as capturable with
WineMetalLayer3920. Private mapping/activation evidence:
`candidate-rock-occlusion-loaded-in-rdr2.json`. User visual acceptance is pending;
keep this running game untouched.

## User confirms the rock result

After returning to the same boulder and being asked to repeat the camera turn,
the user reported **"It is visible now"**. This records a positive same-scene rock
result with the exact driver and all three native bypasses verified above. The
separate `rock-pair-active.json` records this acceptance; private
`rock-occlusion-user-acceptance.json` preserves the exact wording and scope.

The current working app is `dist/rock-occlusion/RDR2 Rocks Occlusion Diagnostic.app`.
It includes all three workarounds; earlier tree and foliage acceptances remain
valid for their tested scenes. Original numeric depth and the heap root cause
remain unreproduced; broad-scene coverage, performance and extended stability
remain unmeasured. Build-time metadata and the signed bundle were preserved. No
game/process, renderer or settings changes were made while recording acceptance.
