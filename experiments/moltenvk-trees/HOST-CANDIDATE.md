# Paused with partial success — 2026-10-26

After confirming the selected tree works, the user reports rocks and some foliage
still disappear and asks to park the work. Those remaining objects have not yet
been isolated or captured. The positive result below applies to the tested tree
scene, not a complete fix for disappearing scene objects.

Resume from [the checkpoint](../../notes/checkpoints/2026-10-26-rendering.md).

---

# User-confirmed tree workaround — 2026-10-26

The user first confirmed **"Ready in Story Mode near the tree"**, then reported
**"it works"** during the same-scene camera-pan comparison. RDR2 PID68577 maps
the exact diagnostic driver below, and native events independently verify the
captured shader bypass is active. This is the first positive visual result.

Keep using `dist/tree-occlusion/RDR2 Trees Occlusion Diagnostic.app` for this
workaround. The running signed app has not been modified. Heaps remain enabled.
This confirms a useful shader workaround for the tested scene, not the original
heap defect or a general driver correction. No claim is made about other locations,
performance or extended stability. The private acceptance report records the exact
user wording and separates these limits from verified driver activation.

---

# Captured-tree diagnostic — 2026-10-26

A controlled pair now validates the exact failure: same bare tree above Arthur's
hat, visible then absent after a camera turn. The mesh bytes are identical, but
the associated draw has two instances in the visible frame and one in the missing
frame. Its compact IDs change from `[2, 3]` to `[2]`. The producer is the culling
compute dispatch at missing-frame `cb0/ce7/disp56` (API831), not a missing asset.

The captured small inputs were replayed in an isolated native Metal workload.
The selected tree passes frustum, viewport, fade and LOD with HiZ disabled. Uniform
synthetic depth 300 rejects only instance3, matching the observed compact-list
outcome; clear depth keeps it. Precise math gives the same result. **This does not
reproduce the original HiZ texture or establish the underlying defect.** Attempts
to reconstruct float texture data from an aliased heap buffer failed fidelity
checks and are excluded as evidence.

A separate, signed `dist/tree-occlusion/RDR2 Trees Occlusion Diagnostic.app`
uses a deliberately narrow diagnostic workaround. It bypasses only the HiZ
branch of the complete SHA256-matched captured shader. All other shaders and
all other culling branches remain intact. It may draw extra geometry and affect
performance; this is not a general MoltenVK fix. A native disable switch and
changed/unrelated-shader negative controls pass. The same helper retains IDs
`[2, 3]` in six synthetic GPU cases. The new exact driver also passes the seven
allocation/policy checks and the query regression.

Driver SHA256: `f829744a02ed35f3fcf30a2f434a934f0441aa20af45be5f1f0d21b18a72b5cc`.
The candidate clients shut down normally; eight saves were backed up and verified
before opening this diagnostic with the existing local game files. RDR2 PID68577 maps that exact driver. Its fixed per-PID log confirms
`tree-hiz-bypass-applied` for the captured shader, while a different shader hash
remains unchanged. The user's same-scene result is now positive, as recorded above. Original and
control apps/data are preserved. Owned replay112 was released before launch.

---

# Host candidate evidence — 2026-10-26

## Latest result

Direct diagnosis has a valid actual-game capture, in private
`captures/game-b61a51ab3f9744c69c2680ae2d0d647e/rdr2.gputrace` (two presented
frames, 10,071,312,276bytes, capture exit0). Exported final images at
`analysis-root/frame1.png` and `frame2.png` show the same snowy Colter view.
This does not demonstrate the camera-triggered tree transition. Simultaneous live
game/replay caused high memory pressure; replay became ready after the game
closed. Owned replay sessions were released before relaunching.

The user agreed to select a single tree, hold its visible camera pose for one
capture, then turn the camera until that same tree disappears for a second.
Both captures will use the same renderer/process/Arthur position. Relaunched
RDR2 PID26805 and its unchanged driver/capture registration are verified, but
PID/Layer IDs must be rechecked before acting. Visible-state confirmation is
pending; manifest is private `captures/camera-pair-active.json`. No new fix is
involved in this diagnostic pair.

**The user reports that the query-result candidate still has disappearing trees.**
No candidate has produced a visible improvement. The user has challenged the
number of comparisons without progress, correctly. Do not request another visual
comparison just because an unrelated GPU smoke/regression test passes. First
obtain evidence connecting a rendering path to the visible failure.

The final fixed events for recorded RDR2 PID 8704 include `occlusion-query-used`
and `query-range-fix`, but no `query-range-nonzero-first`,
`query-availability-offset-applied` or `query-availability-status-differs`.
Thus query use is real; execution of the specific faulty nonzero GPU-copy case
is not demonstrated. Root cause is still unknown. The whole-memory-buffer
alternative remains unbuilt and untested. No game shutdown/restart was requested
or performed in response to this failure report.

The unsuccessful query candidate backports upstream
[PR2794](https://github.com/KhronosGroup/MoltenVK/pull/2794), commit
`701747d61a0484e91c205e081a24ca592ffa12b4`. The pinned driver treats a query count
as an end index and copies GPU query-availability statuses starting from slot zero
instead of the requested first query. A standalone Vulkan test reproduced the
availability-copy defect on this M1 Max: a completed slot-4 timestamp is available
to the CPU, but both 32-bit and 64-bit GPU copies report unavailable. A separate
slot-zero control passes. The tree connection remains a hypothesis.

The rebuilt candidate now passes that same regression: both copied availability
values are one and both results match the CPU value. Its separate slot-zero
control also passes. All seven existing real-GPU buffer/image/policy cases pass.
The verified candidate driver hash is
`9c0161edaff3b40615a4ae69ac5c71bc3e07389705e2a2291bc3f40c3eb24701`.
The separate signed/integrity-checked app is
`dist/tree-query-results/RDR2 Trees Query Results.app`. It has now launched RDR2
with its exact driver hash verified. The early loading-stage native events show
`query-range-fix` and `argument-buffers-on`; nonzero-query/offset-difference and
occlusion-use events had not yet been observed at that early check. The user then
confirmed the same Story Mode tree issue remains. Eight flushed save files were separately
backed up and hash-verified during the normal scoped client switch. Packaging requires
exact-hash evidence for both this query regression and the allocation/image tests.

`candidate-query-results` keeps Metal argument buffers and heaps enabled, with
the earlier dedicated-buffer option unchanged. Fixed per-process events identify
occlusion query use, nonzero query copies and whether the old offset would have
changed the copied availability/output eligibility. No query values or game
shaders are recorded. The whole-memory-buffer patch is an unbuilt alternative;
it is not included in this candidate.

The user confirmed revision 3 still has the same tree issue. Native RDR2 events
proved `policy-on`, `kind-shared` and `kind-dedicated-image`, with no eligible
dedicated-buffer event. Thus the narrow allocation change was not exercised by
the observed run; it is not a verified fix or a test of all Metal-heap behavior.

The separate argument-buffer comparison ran from
`dist/tree-argument-buffer-off/RDR2 Trees Argument Buffers Off.app`.
It keeps heaps enabled and uses the inspected fork's other default change:
Metal argument buffers off. Driver SHA-256 is
`f5663b4e1516dbe2cd5fa660b8dde36963379f2db18e4ae91dd059b7dd309164`.
It passed configuration/ABI/dependency/signature checks and all seven real-GPU
allocation/policy cases. Its in-game native events prove `argument-buffers-off`
in RDR2, and its exact mapped driver hash is verified. The user explicitly closed
the previous game before a scoped normal Steam/Wine shutdown and switch using
the same candidate game/saves. The user confirmed that trees still disappear or
change shape and that they closed the game intentionally after testing. The
comparison is unsuccessful; argument-buffer disabling alone did not resolve
this scene. The verified mapping is preserved in the private
`candidate-argument-buffer-off-loaded-in-rdr2.json` report.

MoltenVK includes its argument-buffer setting in the pipeline-cache UUID and
serialized shader options; this comparison does not require deleting game
settings or saves. No cache reset was performed. No further debugger attach was
used after the failed candidate-1 attempt.

Candidate 1 did not fix the visible tree problem. The user also confirmed that
the game subsequently exited by itself; Rockstar recorded exit code 1 at
19:38:10 SAST. A debugger attach attempted during this run failed to pause the
Wine/Rosetta process. Its involvement is unresolved, so do not attribute that
exit conclusively to the renderer or treat it as a user-requested quit.

Candidate 1 produced no eligible-allocation event. Revisions 2/3 add a signed
per-library policy fallback plus native startup/allocation-kind events to
distinguish missing launch settings from an allocation path RDR2 never uses.
Revision 3 resolves the loaded library's symlink before finding its settings;
GPU tests cover that route. No additional live debugger attachment is planned.
Revision 3 driver SHA-256:
`fe1b6672eb6e77d3a012db62d2f68ea039401a111ce5d78f3c21d01711185680`.
The user tested it and the same tree issue remained. The original evidence below describes the
first candidate build and should not be read as a successful visual result.

The user tested the signed Control app and reported that trees still disappear.
They authorized a candidate build on the physical M1 Max. No video or historical
RDR2 loaded-library capture was collected for that control run. The builder now
accepts this explicitly labelled user observation after validating the signed
Control app, its driver hash and its control input pins. It does not synthesize
captures or claim stronger control evidence.

## Build and GPU results

Pinned CMake 3.31.8 and the dependencies were installed under
`vendor/tree-research`. Existing Apple CLT were sufficient; full Xcode and a
package manager were not needed. Copied Swift caches had build-Mac absolute paths;
the build scripts now accept separate cache/scratch paths for a clean host build.

- Rebuilt host control SHA-256:
  `510a25231b5f226a4f78b89f5db1536f8736c24f1264891e199c125a0888bdf3`.
  This is a new local build, distinct from the supplied user-tested Control app.
- Candidate SHA-256:
  `085893a6940b26e6e9b2a993d97f65cb10969a57443aeaaca8c90ca754b5396c`.
- The candidate changes only eligible dedicated-buffer allocation when enabled.
  Image heaps, argument buffers, Highball's three patches and disabled Metal
  private API are preserved. Architecture/configuration checks, system-only
  dependency checks, signatures and runtime-integrity checks passed.
- Added a fixed PID allocation event, emitted only when an eligible allocation
  uses the experiment. It records no client/account output. Patch/source hashes
  and build provenance include the instrumentation.
- On the actual M1 Max, control, candidate-off and candidate-on passed a Vulkan
  GPU buffer copy and heap-backed 2D array views of 3D images. The allocation
  event appeared only for candidate-on. `probe-gpu.py` binds results to the exact
  library and probe hashes. This is not a visual game test.
- 13 Python checks and 17 Swift checks passed, including rejection of false
  control acceptance and separate persisted selections/launch variables.

The first GPU probe incorrectly requested a loader-provided portability extension
from the ICD directly. Correcting the probe setup produced the passing results;
no game setting was changed to obtain that result.

## Host integration

The app is `dist/tree-candidate/RDR2 Trees Candidate.app`, using separate data at
`~/Library/Application Support/RDR2Launcher-MoltenVK-Candidate/`. Its own diagnostic
confirms the candidate edition and data directory. Regular-launcher selection is
kept separate; the candidate rejects selecting the regular data root.

Control data/game files were APFS-cloned with clients closed. All 124 game paths
and sizes and the prefix inventory matched; registry hashes matched. Eight save
files were separately backed up. Only the copied Steam library/R: paths were
remapped. No game download was requested; original and Control installs remain.

The candidate requested Play through Steam/Rockstar. Live file mappings and the
driver hash proved that RDR2 loaded the exact candidate library. At the first
inspection, no eligible-allocation PID event was present. A process-environment
query could not observe the switch and is not treated as activation evidence.

## Remaining acceptance

The dedicated-buffer and argument-buffer-off comparisons did not fix the same
Story Mode tree scene. FPS and extended stability remain unmeasured. The unused
dedicated-buffer path does not rule out other heap-related problems.

Reproduce with `build.py`, `probe-gpu.py`, `build-candidate-app.py`,
`prepare-host-test.py` and `inspect-host-game.py`. The app builder's
`--fix-disabled` option prepares the same driver with the allocation switch absent
for a later controlled comparison. No public release or visual-fix claim is made.
