# Checkpoint publication requested — 2026-10-26

The user subsequently requested committing and pushing the paused checkpoint and
source changes. This changeset includes the launcher isolation, renderer patches,
build/capture tools, tests and checkpoint. The check script passed 13 Python tests
and 17 Swift core checks before committing. See Git history for the containing
commit and the push receipt in the conversation. Ignored game/runtime/app/capture
and account data remain local; preserve the full project copy when transferring.
The rendering investigation remains paused; no game/process actions were taken.

---

# PAUSED — checkpoint requested by the user, 2026-10-26

The latest instruction is to park the investigation and resume later. User report:
"there are also rocks and some foilage that disappear". The selected tree works,
but this remains a PARTIAL workaround. Rocks and remaining foliage have not been
isolated; do not assume their shader or root cause matches the selected tree.

Resume entry: `notes/checkpoints/2026-10-26-rendering.md`. It includes working
app/driver/shader fingerprints, evidence paths, test results and concrete next
steps. Last verified PID68577 is historical, not a current process assertion.
No new captures, builds, process changes, settings changes or Git commit/push were
made for this checkpoint. Do not resume diagnostics until asked.

---

# Current state — user confirms the tree workaround works

The user answered "Ready in Story Mode near the tree", then "it works" in the
same-scene comparison. Record this as user-confirmed success of the narrow
occlusion workaround, not proof of the original heap defect or all-scene coverage.

RDR2 PID68577 was verified still using driver SHA256
f829744a02ed35f3fcf30a2f434a934f0441aa20af45be5f1f0d21b18a72b5cc
from `dist/tree-occlusion/RDR2 Trees Occlusion Diagnostic.app`. Native events
confirm the exact captured shader's HiZ bypass is applied. Do not restart,
rebuild, replace or close this working game unless the user requests it. Future
process actions must revalidate PID/path. No GPU replay sessions are active.

Private evidence: `tree-occlusion-user-acceptance.json` and
`candidate-tree-occlusion-story-loaded-in-rdr2.json` under host-private.
Public STATUS, HOST-CANDIDATE and experiment README now record the positive result.
The signed app and build-time metadata are unchanged; acceptance is stored outside
its signed bundle. Tests already passed: six native culling controls, negative
scope/disable guards, seven allocation/policy checks, query regression, packaging
signature/integrity checks and five evidence tests. No retest needed for docs.

User also asked about MVK_CONFIG_USE_MTLHEAP=0. We verified and explained this was
already in initial research: fork reports a fix, Highball reports startup failures.
Earlier dedicated-buffer bypass did NOT exercise RDR2's allocation path and did
NOT rule out heap defects; image heaps always stayed enabled. Current shader
bypass tests where rejection happens, not why heap-backed depth is wrong. Preserve
that distinction. Numeric original HiZ data remains unreproduced; performance,
other scenes and extended stability are unmeasured. Do not enable global heap-off
or start another speculative build in response to this successful user report.

No commit/push performed for this result; current edits remain local. Earlier
commit/push requests predate this experiment and were already handled.

---

# LIVE continuation — diagnostic ACTIVE in real game

**RDR2 IS RUNNING PID68577. Do not close it or restart anything.** App:
`dist/tree-occlusion/RDR2 Trees Occlusion Diagnostic.app`; actualmappedSHA verified
f829744a02ed35f3fcf30a2f434a934f0441aa20af45be5f1f0d21b18a72b5cc.
Nativeevents for68577 confirm capturedshaderhash90e7d5... matched and
`tree-hiz-bypass-applied` seven times. Differenthash80ecbc... remains unchanged.
Actualactivation PROVEN, visualresult stillPENDING. Report saved privately as
candidate-tree-occlusion-loaded-in-rdr2.json. No GPU replay sessions active.

User async readinessquestion sent: load sameStoryMode nearselectedtree, tellready.
No answer yet. Final handoff asks same camera pan, especiallytree abovehat, and
whether that tree now staysvisible. This is ONE exactshaderdiagnostic, NOT a
provenrootcause or generalfix. If other trees stillpop, that alone doesn't falsify
this narrow bypass; selectedtreeinstance3 result matters. AllsixnativeGPUcontrols
plus guards+7allocationchecks+queryregressionpassed, app signed+diagnoseverified.
Eight saves backedup/hashverified before normal scopedclientshutdown/switch.

New useful offline finding: original descriptorGPUResourceID0x6cf is nowmapped
PROVEN to missing @tex1873 (R32Float128x72x7) via serializedproperty records.
Originaltexturepointer0x7fbe7477ef50, heapoffset0xe33f00=14892800,
allocation2151858. Mapping report in missinganalysis
selected-hiz-texture-mapping.json. THREEidpropertyrecords match +heapoffset unique.
Still no actualnumerictexturecontents; export clippedPNGonly, heaprebuildfailed
fidelity. Do NOT say actualdepthsourcewasreproduced. Gamecurrentlyrunningso do
NOT open hugeGPUreplay alongside it. Futuretraceanalysisrequiresgameclosedfirst.

---

# Latest continuation — captured-tree occlusion diagnostic, 2026-10-26

Game is CLOSED, saved intentionally by user. Owned replay112 was verified against
missing trace then TERMINATED after evidence export; no owned replay remains.
All paired capture paths/instance mapping below remain valid.

Completed isolated GPU probe `probe-captured-cull.mm` using exact missing-state
small buffers and synthetic uniform128x72x7 R32Float depth. Controls:
HiZoff -> IDs[2,3]; depth0 -> [2,3]; depth300 -> [2]; depth10000 -> [];
precise-math HiZoff->[2,3], precise-depth300->[2]. Instance3 passes all pre-HiZ
checks. This narrows a targeted comparison, but ORIGINAL DEPTH INPUT NOT REPRODUCED.
FastMath difference not observed in these controls. Reports in missing analysis:
`isolated-cull-controls.json`, `isolated-cull-bypass.json`.

Prepared `candidate-tree-occlusion` driver (same prior query-results baseline plus
one SHA256 guarded MSL transform at compileLibrary; applies also decompressed MSL
cache). Exact MSL body from #include<metal_stdlib> through end SHA:
90e7d5ac9626967e6be1eaf4e29b4279d792c198f0a557ca321c6a506f4edeb6.
Only that shader's branch testing globals.m5 is replaced with `if(false)`, so
frustum/rect/fade/LOD remain. `RDR2_MVK_TREE_HIZ_BYPASS=0` disables; default ON
only in this separate diagnostic binary. NOT A GENERAL DRIVER FIX. May overdraw.
Guard negative controls modifiedshader/unrelatedshader/off all pass. Same helper
native GPU test preserves IDs[2,3] in all6cases. Fixed per-PID activation markers:
`tree-hiz-source-<sha>`, `tree-hiz-bypass-applied` or `...-not-applied` in existing
candidate state/tree-allocation-events.log. MUST see applied for actualRDR2 before
asking user to interpret tree test; hash mismatch means ineffective comparison.

Driver f829744a02ed35f3fcf30a2f434a934f0441aa20af45be5f1f0d21b18a72b5cc.
Builtsource candidate-tree-occlusion-source, pinned mode/patch/header fingerprints
in pins.json. Artifact vendor/tree-research/artifacts/candidate-tree-occlusion.
7allocationchecks + queryregression pass for exactdriver. Helper GPU control
summary host-private/captured-cull-workaround-results.json; game_hiz_data_reproduced
explicitFALSE. App packaging COMPLETE at dist/tree-occlusion/
RDR2 Trees Occlusion Diagnostic.app, signed+integritydiagnosticpassed. Scoped switch
from query app COMPLETE: clients shutdownnormally,8savesbackedup+verified, newGUI
launched with --play-game. Switchlog host-private/switch-tree-occlusion.log.
ActualRDR2 PID68577 started, not yet rendererloaded at lastinspection. Need verify
exactmappedhash and appliedmarker, then ask user sameColter camera pan only. Do not claim visual fix yet.

Failed numeric export route: gpudebug normalfetch clips float to PNG; typed
GTDebugFetchTextureRequest formats0/1/2/3+mip6 via localcopiedCLI still ignored,
response remained mip0PNG. No numeric-data fidelity claim. Exploratory companion
source removed; private copiedCLI remains ignored. No system tool/game injection.

---

# Compact working checkpoint — 2026-10-26

## Post-checkpoint update

**NEWEST: Exact compute producer found in missing capture.**
Active owned replay remains session112 missing capture, game CLOSED. Selected
tree culling dispatch missing API831 = `/commands/cb0/ce7/disp56`, @cps134.
It reads transform table0x15e8eeb200 and writes selected compact-list pointer
0x15458368e0 exactly (not a guess). Pipeline source exported to missing analysis
`compute-sources/cps134.metal` (1320lines/64KB). It performs frustum, screen-rect,
HiZ occlusion, LOD, then atomic instance-count and compact-list writes. Related
sources cps80/81/125/135/124/68/69 also exported; several are duplicates. Later
ce101/disp0 source is shadow atlas allocation, NOT selected tree producer.

Compute descriptor bindingDS0=@buf21 offset73480, DS1=@buf21 offset73528,
snapshot `cull-pool-buf21.bin`. DS0 slots8B each: id1 frame272B pointer
0x15078403b0; id2 cullingGlobals928B pointer0x1507840010; id3 aux252B pointer
0x154570a610. DS1 id0 points size constants; id1 LOD0list0x15458368b0,
id2 LOD1(selected)list0x15458368e0, id3/id4 dummy4B0x15098afc00,
id5 extraList0x1545836910, id6 drawArgs320B0x1545836940,
id7 texture GPUResourceID0x6cf (NOT gpudebug resourceIndex),
id8 object132B0x1545836a80, id9 transforms640B0x15e8eeb200.
Sizes [0,40,40,4,4,40,320,0,132,640] (check actual captured inline words).
Args slot10 corresponds tree4881indices, count1. All slots0..8 count0; slots9..12
count1, so central instance3 was not moved to LOD0. Need finish distinguishing
HiZ rejection/other LOD/fade before asserting cause.

Captured missing small inputs saved: tree-cull-camera.bin272B,
tree-cull-globals.bin928B, tree-cull-object.bin132B, tree-cull-aux.bin252B,
tree-cull-args.bin320B, tree-cull-transforms.bin640B. Exact GPU stage snapshots
also cull-frame-constant-pool.bin128MiB (parent@buf2960/@2961 GPU0x1501840000),
tree-buffer-at-cull.bin83.4MiB(parent@buf3283), cull-pool-buf{18,20,21,24}.bin.
Selected culling jobs recorded in selected-tree-cull-dispatches.json: API495 cps135
also reads transforms but wrongoutput, API831 cps134 correctoutput, API1278 other.

CPU partial evaluation in tree-cull-cpu-stages.json: camera(-1343.181,2433.719,
308.485). For central instance3 frustum-AABB distances allPOSITIVE
[27.95,46.03,27.31,35.46,9959.05,53.04], screen rect within unrestricted viewport;
occlusion enabled (globals.m5=1). Globals offsets: scale0,planeCount4,22planes8,
camera360, flagsm4=372(0), m5=376(1), m6=380(.0001000005),m7=384(1),
m14=888(0),m15=892(254),2rectangles896=full viewport. Camera struct matrices
view64/proj128/origin256. Central tree3 projected HiZ rectxywh(.2065,.1417,
.2892,.5141), depth reference279.55. Righttree2 ref449.23. These are CPU math
checks, not full compute emulation. Need actual depth input or isolated shader
probe with exact small inputs to locate failing condition; don't patch blindly.

Texture metadata6392 float resources in float-texture-metadata.json, all catalogue
texture-catalogue.log. Only mippedR32Float128x72 level7 candidates are @tex1871..1879,
all heap4 allocationID2151858 offsets in hiz-placement.json. Their GPUdebug PNGs
at cull dispatch saved hiz-tex1871.png...1879.png (binary-looking depth silhouettes).
ResourceIndex property is trace object index, NOT Metal GPUResourceID0x6cf, so
the exact texture mapping is not yet proven. GPUDebug fetch textures outputs PNG
only, mip0; no raw/mip options in installed help. This limits direct numeric HiZ.

Tried reconstruction of texture placements from captured heap parent@buf3260
(32MiB, GPU0x150b850000) in separate Metal workload decode-captured-hiz.mm.
Compiled/runs, BUT OUTPUT INVALID (NaNs/implausiblefloat values, wrong fidelity).
Decoded-hiz-fidelity.json explicitly marks not usable/root-cause evidence. Do
NOT mistake decoded-* hugefloats for game bug. Need alternate rawtexture route
or isolated shader control inputs. Header source unchanged game; no build/test
requested from user. Last user-facing update: exact culling inputs saved, preparing
small isolated test to investigate without more game relaunches.

**LATEST ACTUAL FAILURE IS CAPTURED AND DRAW IS IDENTIFIED (no fix yet).**
User confirmed first visible tree “just ontop of arthurs hat”, then SAME tree
missing with camera held still, then game saved/closed. Pair manifest:
`vendor/tree-research/host-private/captures/camera-pair-active.json`.
Visible trace `game-5679a6c814f24ab98215f7810211762f` (10,001,189,773bytes);
missing trace `game-da4c37e53157424c9aa4c580b9d35ea4` (10,108,490,510bytes).
Both one frame, same RDR2 PID26805 and same driver9c0161..., exit0. Exported
final images VALIDATE actual central bare tree above hat visible then absent.

Pair latest analysis_paths resolve directories (use manifest, not stale guesses):
visible `...game-5679.../analysis-pair-9a0c6eef0a8049d2b6c91a016d3fd745`;
missing `...game-da4.../analysis-pair-864a2160d5b24d9889974ce36eb11b42`.
Visible owned session109 was closed. Current ONLY owned large replay session112
is missing trace, ready, idle timeout600. Do NOT open another large replay without
closing112 (validate ownership/trace). Game is CLOSED. Root performs analysis;
agents unavailable and spawning forbidden by latest developer instruction.

Root isolated exact tree draw via per-draw GBuffer color0 snapshots and pixel
(600,270), binary search over83 draws: BEFORE visible API12982 no central tree;
AFTER API12990 central tree and another right tree appear. Images
draw-api12982.png / draw-api12990.png viewed and confirmed. Exact command is
visible `/commands/cb0/re107/draw13`, pipeline@rps65, indexBuffer@buf4440,
indirectBuffer@buf3110 offset1,400,648. 4,881 UInt16 indices,1,431 vertices.
Matching mesh identified by GPUaddress0x1634cf6100, allocationID2158503.
Missing draw API13239 uses indexBuffer@buf4620, indirectBuffer@buf3283,
offset30,534,152. Its navigation path ALSO cb0/re107/draw13 in this trace.
GPU buffers have different @refs per trace; match gpuAddress+allocationID,
not arbitrary ref suffix. Index and vertex bytes are IDENTICAL across states.

Visible indirect args `<IIIiI>`=(4881,2,0,0,0); missing=(4881,1,0,0,0).
Actual compacted instance IDs: visible[2,3], missing[2]. The selected central
tree is instance3, removed before vertex rendering. Both draw commands exist;
not a missing mesh file/changed vertex blob. ROOT CAUSE STILL UNKNOWN: trace
the GPU compute producer of the compacted list/instanceCount before new patch.
Evidence `host-private/captures/tree-instance-comparison.json`.

Visible resources saved: tree-indirect-visible.bin (83.4MiB/87,490,560 bytes),
tree-indices-visible.bin (9762bytes), tree-vertices-visible.bin (62964bytes),
tree-descriptors-visible.bin (1,523,712bytes), tree-vertex.metal (981lines),
tree-visibility-visible.bin(256bytes allzero), tree-transforms-visible.bin(640B).
All-buffer metadata8692 records and pipeline metadata299 records available.
Missing corresponding indirect/indices/vertices/descriptors binaries saved.
Missing tree shader source child `lib293-source` listed but NOT fetched yet;
visible source lib296-source has generated _vars, actual behavior:
MSL line818 _249 = DS1.m99[instanceID].m0 &65535; DS0.m102 transforms[_249];
line965 shader also suppresses if DS1.m77 bit[_249] set. Visible mask all0.
Instance3 world translation(-1348.1,2386.3,306.3293), scale0.75; instance2
(-1372.5,2410.433,306.831). Ignore NaNs when float-decoding uint flags in record.

Both indirect buffers share capturedGPUbase0x1543b18000, allocationID2153110,
heap21. Visible buffer@3110 and full-memory alias@3109 share address/length.
Visible DS0 @buf25 offset266408, DS1 @buf25 offset266952. Missing DS0 @buf22
offset89352, DS1 @buf22 offset89896. Argument-buffer slots are8bytes each.
DS0id10 transform pointer0x15e8eeb200 BOTH. DS1id10 mask0x1509a14600 BOTH.
DS1id13 compact-list pointer: visible0x1543c6de20 (offset1,400,352),
missing0x15458368e0(offset30,533,856). Raw IDs ffff0002,ffff0003 / ffff0002.
Visible mask@buf2819 (256B) GPU0x1509a14600, parent@buf2792(32MiB),
visible transforms@buf3159(640B) GPU0x15e8eeb200, parent@buf3156(32MiB).
Camera/material constants pointers in DS0/DS1 live inside128MiB @buf2790/2791
GPUbase0x1501840000; offsets110113856 /110114960 for visible. Missing pointers
differ and not resolved yet. Do not fetch from API/root context for mutable data;
navigate COMMAND draw/dispatch first. Info queries pretty-print multi-line JSON,
lists/status compact JSON; parse streams with JSONDecoder.raw_decode.

New replay-camera-pair.py exports images/staticAPI and owns one session, skips
known emptyCB (go empty emits spurious info error), logs every request. Initial
closed sessions100/103, missing106closed aftermetadata, visible109closed;112active.
read-capture-pixel.c compiled to vendor/tree-research/read-capture-pixel reads
numericRGBA only, no image edits. Root told user concrete2→1instance finding;
continue tracing compute producer without further user gameplay for now.

**LATEST pair first state SAVED:** User explicitly confirmed “Visible, just ontop
of arthurs hat”. One-frame capture of PID26805 completed successfully at
`host-private/captures/game-5679a6c814f24ab98215f7810211762f/rdr2.gputrace`,
10,001,189,773bytes, capture exit0, exact same driver9c0161... . Linked as
visible_capture in camera-pair-active.json, status awaiting_user_missing_pose.
No replay yet (game open; avoid memory pressure). User told first capture done,
keep Arthur in same spot, turn until SAME tree disappears, hold for second.
Pending async options: “Missing now; camera held still”, “It only disappears
while the camera is moving”, “I can’t make it disappear right now”. DO NOT
capture second until actual missing-state response; adjust protocol if motion-only.
If missing held pose ready, run capture-host-game.py --capture --frames1, validate
samePID26805/hash and link missing_capture. Then both captures stored; user can
save/quit to free memory. Replay each separately, never two sessions at once.
Current visible target is tree immediately above Arthur’s hat, not arbitrarily
another pine. Root must inspect actual scene images before asserting transition.

**LATEST / paired camera capture pending:** The first actual game capture succeeded
at `vendor/tree-research/host-private/captures/game-b61a51ab3f9744c69c2680ae2d0d647e/rdr2.gputrace`.
It contains two presented frames, 7CB/988encoders/7061draws/1734dispatches,
10,071,312,276bytes; capture46s, exit0. Recorded exact query driver remains
`9c0161edaff3b40615a4ae69ac5c71bc3e07389705e2a2291bc3f40c3eb24701`.
Initial replay session62 stalled under simultaneous game/replay memory pressure
(26GiBwired); it later expired. Root reopened owned session65 with game closed,
replay became READY, fetched both actual final images:
`.../game-b61.../analysis-root/frame1.png` and `frame2.png`.
They show Colter snowy camp at essentially SAME CAMERA ANGLE, no tree transition.
Root told user plainly initial capture did not demonstrate camera-triggered bug.
The images and static exports are valid baseline only, no causal/fix claim.
Root terminated ONLY owned session65 before relaunching game.

User said “Go on”, then agreed to controlled pair: keep Arthur in ONE spot,
choose ONE tree that reliably vanishes; FIRST hold camera with tree visible and
confirm, THEN after first capture finishes turn until same tree disappears and
confirm again, capture second. One frame each (`capture-host-game.py --capture
--frames 1`). User's latest answer is COMMITMENT (“I can do that; I’ll confirm
when the tree is visible”), NOT yet actual visible-state readiness. Do not capture
until readiness arrives. Pair manifest `host-private/captures/camera-pair-active.json`,
pairid c13028e113e74205a5f5daa76ffd0c29, both captures pending.

Relaunch initially blocked by leftover candidate PlayRDR2 bootstrap16941 (old23min),
actual RDR2 absent. Normal Steam shutdown and scoped wineboot shutdown did not
clear it; wineserver-w timed out20s. Copied/hash-verified eight save files to
private `before-idle-bootstrap-cleanup-*`, revalidated exact PID/comm and absence
of ANY RDR2, SIGTERM only bootstrap16941; it exited. Retried normal scoped
`switch-host-app.py --capture-session` successfully, fresh save backup8 verified.
Same renderer relaunched; current RDR2 PID/Layer IDs NEED REVALIDATION. Old17289
is from earlier capture, never assume still current. Native launcher GUI stays
closed for direct diagnostic session. User told game launch requested and to
confirm chosen tree visible. No new speculative patch/build.

Post-relaunch read-only helper verifies current RDR2 PID26805, unchanged library
hash and capturable Layer3920. Pending required async input asks user to reply
Visible plus approximate on-screen tree location, then hold camera. User has
only committed to preparing that pose, not yet confirmed it ready. Do not capture
merely because the game is running.

`switch-host-app.py` capture mode now allows only old(>=180s), same-candidate
PlayRDR2 bootstrap through preflight for NORMAL shutdown; real RDR2/recent or
other-prefix launches still refuse. Hard termination above was explicit one-off
exact PID after failed normal shutdown and backups, NOT generic auto-kill.
All agents are inactive/errored usage limit; latest developer disallows spawning
unless explicitly requested. Root owns subsequent GPU replay. Never run two large
replay sessions or replay while game open on32GiB if avoidable.

**Current diagnostic state:** user said “Ok go ahead” and then confirmed game
closed. `validate-gpu-capture.py --method external` now PASSES on a separate
x86-64 Vulkan probe: CLI capture, correct GPU copy, replay/command inspection.
The initial external attempt timed out while service initialized; programmatic
capture then worked, and subsequent external tests pass. Full Xcode not needed.
Strict helper checks reject `error:` despite CLI exit0. Evidence latest at
`vendor/tree-research/host-private/capture-validation-result.json`.

`switch-host-app.py --capture-session --from-app QUERY_APP --to-app QUERY_APP`
normally closed candidate clients, backed up/hash-verified eight saves and
restarted same driver with native Wine `MTL_CAPTURE_ENABLED=1`, automatic scope0.
No WAIT_FOR_SIGNAL in game, no shader/graphics change, no debugger. GUI stays
closed in this direct diagnostic session; Steam/Rockstar/game are running.
New RDR2 PID17289 is capturable; helper verified exact unchanged driver SHA
`9c0161edaff3b40615a4ae69ac5c71bc3e07389705e2a2291bc3f40c3eb24701`.
Frame boundary Layer3920 (`WineMetalLayer: WineMetalView`), queue3923, scope3925.
Always revalidate IDs/PID before capture. Capture-session private summary at
`vendor/tree-research/host-private/capture-session.json`.

User asked via async if ready in Story Mode near trees; answer pending. Do NOT
capture an unrelated menu/loading scene as tree evidence. `capture-host-game.py`
default read-only is proven on actual game; `--capture --frames 2` will capture
its unique Layer only after scene ready. This has NOT yet been run. It validates
PID/renderer/registration, writes unique private trace/report, bounded55s with
only verified PID scoped-stop on timeout. No global stop/kill.

Actual independent gpudebug persistence/fetch proof:
`host-private/probe-analysis-6a082803116548d0a358e7e17d5edd1b/result.json`.
CLI `--json` still starts `Session N created.`; regex anchored to parse. Use
`gpudebug -t TRACE --timeout 180 --json -c status`, reuse `-s N` for subsequent
calls. Navigate COMMAND tree, e.g. `/commands/cb0/be0/blit0`, then fetch refs.
Root/API/resource contexts may say empty buffer. Own probe source/dest both
4096 bytes0xa7 after copy, but before-copy state not demonstrated. Terminate
ONLY owned replay session when done. All service calls need escalated exec;
sandbox default can print “Cannot connect” while exit0. On M1 do not depend on
profile heatmaps (M3/A17+). No game trace inspected yet.

Direct GPU diagnosis preparation: macOS27 `/usr/bin/gpucapture` and
`/usr/bin/gpudebug` both exist; `--help` works without full Xcode. Official
Apple tools page and WWDC26 session357 document CLI capture/inspection. A
sandboxed read-only `gpucapture list` exited0 but did not list recorded PID8704
or an RDR2 name. This does NOT establish unsupported Wine capture: current
process existence, enumeration permissions and capture enablement remain
unverified. No capture/attach/config/start/stop command was issued. Validate
the route independently before requesting another game restart. Prior LLDB
failure remains a reason to avoid live debugger attachment.

**Latest user result:** query-results build still has disappearing trees; user
is frustrated by serial comparisons without visible progress. Acknowledge that
root cause remains unknown. Defer further visual-test builds until there is
evidence tying the proposed change to the actual failure. Do not launch the
reserved whole-memory patch merely as the next guess.

Reading the existing PID8704 fixed-event log now additionally shows
`occlusion-query-used`, but still NO nonzero-first-query, availability-offset or
availability-difference events. Thus the real upstream query bug was reproduced
and fixed in the GPU probe, yet its affected copy case was not demonstrated in
this RDR2 run. Record the visual test as failed, not a near fix. No process
actions taken this turn; whether the user has closed the current game is unknown.

Query-result candidate is now built and signed at
`dist/tree-query-results/RDR2 Trees Query Results.app`; driver SHA256
`9c0161edaff3b40615a4ae69ac5c71bc3e07389705e2a2291bc3f40c3eb24701`. Query GPU regression: real control fails
with the precise expected bug, candidate passes both 32/64-bit nonzero-query
results, independent slot-zero control passes. Existing seven GPU cases pass.
Build mode `candidate-query-results` adds exact upstream PR2794 functional patch
and fixed query diagnostics; AB1/heaps1/private0. Build logs
`/private/tmp/rdr2-host-query-results-build.log` and `-app-build.log`.
The user confirmed intentional exit after failed AB-off test.
`switch-host-app.py` normally shut down only the candidate clients and backed
up/hash-verified eight flushed save files. The new query app launched; RDR2
PID8704 maps the exact driver above. Native events include policy-on,
argument-buffers-on, kind-shared, kind-dedicated-image, query-range-fix. Nonzero
query/offset-difference and occlusion-use events are not yet observed at this
early loading-stage check. The mapping report is preserved in private
`candidate-query-results-loaded-in-rdr2.json`. The same-scene visual test failed,
as described above. Leave the game alone; no debugger or further speculative builds.


The user has now confirmed revision 3 still flickers. Its native policy is on,
but only shared/dedicated-image allocations occur; no eligible buffer event.
The user explicitly closed the game, then `switch-host-app.py` normally closed
the candidate clients and launched the argument-buffer-off comparison:
`dist/tree-argument-buffer-off/RDR2 Trees Argument Buffers Off.app`.
Driver hash `f5663b4e1516dbe2cd5fa660b8dde36963379f2db18e4ae91dd059b7dd309164`.
RDR2 PID 86846 was proved mapping that driver with native `argument-buffers-off`.
The user confirmed trees still disappear/change shape, then closed the game
intentionally. A fresh scoped process check found no candidate RDR2 process.
Preserve `candidate-argument-buffer-off-loaded-in-rdr2.json` as the mapping/report
for that failed visual test. Do not attach a debugger.

Next investigation: upstream PR2794 fixes a confirmed query availability range
and copy-offset defect present in the pinned driver. Backport and demonstrate
with a control-failing, patched-passing GPU regression before an in-game test.
No tree-root-cause claim is made. Sections below retain historical checkpoints;
this top update supersedes their running-state and pending-test descriptions.

Build mode `candidate-argument-buffer-off` uses the same candidate patch plus
compile definitions setting only `MVK_CONFIG_USE_METAL_ARGUMENT_BUFFERS=0` for
CXX/OBJCXX. Heaps remain 1, private API 0. The native allocation event now records
the actual device argument-buffer configuration. All seven GPU cases passed.
`probe-gpu.py --candidate-artifact .../artifacts/candidate-argument-buffer-off`
produces hash-bound evidence; `build-candidate-app.py --artifact ...` packages it.
Original candidate artifact files and running app files are not overwritten.

Candidate 3 now builds with canonicalized library-path lookup for its signed
policy fallback. SHA-256 is
`fe1b6672eb6e77d3a012db62d2f68ea039401a111ce5d78f3c21d01711185680`.
All seven GPU cases, including loading through a Wine-style symlink, pass.
Its app is being packaged at `dist/tree-candidate-v3/RDR2 Trees Candidate.app`;
log `/private/tmp/rdr2-host-candidate-v3-app-build.log`. Revisions 2/3 have not yet
run in RDR2. `switch-host-app.py` now performs a scoped normal Steam/Wine shutdown,
backs up the flushed candidate registries and opens a new app with the same test
data. It refuses if any RDR2/PlayRDR2 game is running. Revalidate live PIDs.

## Current objective and authorization

Fix whole nearby/distant trees disappearing and changing shape in RDR2 on the
physical M1 Max. The user authorized local build-tool installation and testing.
Preserve the original/Control installs and saves, and reuse local game files.
No fix has been verified. Latest user report: candidate 1 still flickers and the
game **exited by itself**. User requested compaction, then continued work.

## Repository and tools

- Workspace `/Users/ruansunkel/Personal/RDR2`, branch `main`, last pushed commit
  `779f03f`. `git pull --ff-only` was up to date before these changes.
- User copied `experiments/moltenvk-trees/` from the build machine. It is currently
  untracked; preserve it. Source, tests, build scripts and STATUS also have local
  changes. No commit/push is requested for this new implementation yet.
- No manual conversation-compaction tool is exposed in this session. This file
  is the concise persistent checkpoint.
- Pinned CMake 3.31.8/CPM/dependencies now exist under `vendor/tree-research`.
  Existing CLT successfully built everything; no full Xcode/Homebrew was needed.
- Swift's copied build-Mac caches contained absolute paths. `scripts/check.sh`
  and `packaging/build-app.sh` now support `RDR2_BUILD_CACHE_ROOT` and
  `RDR2_BUILD_SCRATCH`; host values are `.cache/physical-host` and its `build/`.

## Artifacts and actual results

| Artifact | Driver SHA-256 | Result |
| --- | --- | --- |
| Original r27 | `294e9ef77c6036ab4f4d93117d752b6e31fa6c8c4345bc085e062a6ee3ced80a` | User verified Story Mode/controls; tree flicker |
| Supplied Control app | `68d55e39c301e5d4f87f0f2b8b5a940376495c3deade486bc0a533ba85b1ba2a` | User verified flicker persists |
| Host control rebuild | `510a25231b5f226a4f78b89f5db1536f8736c24f1264891e199c125a0888bdf3` | GPU/config checks only |
| Candidate 1 | `085893a6940b26e6e9b2a993d97f65cb10969a57443aeaaca8c90ca754b5396c` | Loaded in RDR2 PID 33498; no allocation event; user reports flicker persists and spontaneous exit |
| Candidate 2 | `db161ecd3be0615092dc449e505d65c6e9efbad1829593c6b7a83e8ecd16033f` | Built/signed, six GPU policy tests pass; **not launched yet** |

Candidate 1 app: `dist/tree-candidate/RDR2 Trees Candidate.app`.
Candidate 2 app: `dist/tree-candidate-v2/RDR2 Trees Candidate.app`.
Supplied Control: `dist/RDR2 MoltenVK Control.app`.

All candidate source/patch hashes are updated in `experiments/moltenvk-trees/pins.json`.
Both candidates preserve image heaps, Metal argument buffers and Highball's three
patches. They only bypass heaps for eligible dedicated, nonexternal buffers.

## Why candidate 2 exists

Candidate 1 emitted no eligible-allocation event in the actual game. macOS ps could
not observe the experimental environment variable; that is unknown propagation,
not proof it was absent. A debugger attempt against PID 33498 failed with:
`attached to process, but could not pause execution; attach failed`.
The game exited with code 1 at 19:38:10 SAST. The user says it exited by itself.
Debugger involvement is a confounder; do not claim a proven renderer crash cause.
The debugger is no longer running. Avoid another live attach.

Candidate 2 adds a signed/inventoried per-library `rdr2-tree-policy.conf` beside
the dylib as a fallback when native environment variables do not survive Windows
launchers. Explicit env 0/1 still wins. The policy file enables the experiment
and supplies the candidate data-directory basename for a safe per-user event
path. Defaults remain off when neither policy nor env specifies activation.

It also emits fixed PID events on first memory allocation: `policy-on/off`, the
allocation kinds (`kind-dedicated-buffer`, `kind-dedicated-image`, `kind-shared`),
and `dedicated-buffer-no-heap` only when the changed path actually runs.
No client/account output is captured. This will distinguish inactive configuration
from a narrow allocation policy the game does not exercise.

## Host data and running state at interruption

Original data: `~/Library/Application Support/RDR2Launcher/`.
Control data: `~/Library/Application Support/RDR2Launcher-MoltenVK-Control/`.
Candidate data: `~/Library/Application Support/RDR2Launcher-MoltenVK-Candidate/`.
Candidate contains an APFS copy of Control, including 124 game files and eight
separately backed-up save files. Steam library/R: point to its own `SteamLibrary`.
No game download was needed. Do not clone or reset it again unnecessarily.

At the last process check, no RDR2 or Rockstar launcher remained, but candidate 1
native GUI PID 32549, Steam PID 32645, wineserver PID 32579 and its Windows helpers
were still running. These PIDs must be revalidated, never assumed current.
An old orphan `winedevice.exe` PID 15337 also existed; do not kill it by name.

Before candidate 2 launch, verify no candidate game is running, close only the
old candidate clients normally (scoped Wine env / Steam shutdown / wineboot
shutdown), and close the old candidate native GUI so its launcher lock is free.
Use the existing candidate data. Do not use a global wineserver kill/pkill.
Then open the NEW candidate 2 app with `--args --play-game`.

## Tests and useful commands

- 13 Python and 17 Swift checks passed before v2. Re-run appropriate source checks
  after further edits; no need to repeat unchanged broad checks indefinitely.
- `probe-gpu.py` compiles the native x86-64 `probe-gpu.c` and validates real GPU
  buffer copies plus heap-backed 2D array views of 3D images. V2 passed all six
  cases: control, candidate env off/on, bundle off/on, env overriding bundle.
  Exact driver/probe hashes and logs live under ignored `vendor/tree-research/host-private`.
- The first probe incorrectly requested loader portability enumeration directly
  from the ICD; corrected, and all GPU results above are from the corrected probe.
- `build.py --mode candidate --control-evidence vendor/tree-research/host-private/control-evidence.json --jobs 6`
  builds the pinned candidate. A truthful user-reported signed-Control branch was
  added to the gate; no fake videos or historical mappings were produced.
- `build-candidate-app.py --output 'dist/tree-candidate-v2/RDR2 Trees Candidate.app'`
  packaged v2. Its deep/strict signature, integrity diagnostic, edition and
  separate data-root diagnostic all passed. Do not overwrite existing apps.
- `inspect-host-game.py --app 'dist/tree-candidate-v2/RDR2 Trees Candidate.app'`
  verifies exact RDR2 mappings/hash, fixed native allocation events and the one
  optional process experiment variable (never prints/saves the complete env).
- V1 live report: `vendor/tree-research/host-private/candidate-loaded-in-rdr2.json`.
  Preserve it before v2 inspection overwrites it.
- Build logs: `/private/tmp/rdr2-host-control-build.log`,
  `/private/tmp/rdr2-host-candidate-v2-build.log`,
  `/private/tmp/rdr2-host-candidate-v2-app-build.log`.

## Next decisions

1. Record the failed v1 visual result and spontaneous exit accurately in host
   evidence/STATUS, preserving the debugger confounder.
2. Start v2 after a scoped clean client shutdown; verify native policy and
   allocation-kind events, then request the same-scene visual result.
3. If policy is on but no eligible buffers occur, this narrow hypothesis did not
   exercise the relevant resources. Do not claim global heap problems disproved.
4. A separate argument-buffer-off experiment is a plausible later comparison:
   the inspected fork disables both heaps and argument buffers. Global heap
   disabling is known to prevent this Highball renderer from starting; do not use it.
   No argument-buffer-off build has been started. Avoid arbitrary setting churn.

The active goal remains an actual visual fix with verified loaded bytes and
activation, preserved rollback, and checks for water/shadow/terrain regressions.
