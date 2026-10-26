# Rendering investigation checkpoint — 2026-10-26

**Paused at the user's request.** The user confirmed the selected tree now works,
then reported that rocks and some foliage still disappear. Resume only when
asked. Do not restart or close the game as part of making this checkpoint.

## Working result and remaining problem

- User confirmed Story Mode readiness near the selected tree, then **"it works"**.
- The separate occlusion diagnostic bypasses only HiZ depth rejection in one
  SHA256-matched tree-culling shader. Other culling checks remain active.
- Latest report: **"there are also rocks and some foilage that disappear"**.
  Those objects have not been isolated or captured. Their camera dependence,
  exact draw/shader and relationship to the tree defect remain unverified.
- This is a partial rendering workaround. The underlying heap defect is unproven;
  original numeric depth contents, performance and extended stability are unmeasured.

## Preserve this baseline

- Working app: `dist/tree-occlusion/RDR2 Trees Occlusion Diagnostic.app`.
- Renderer SHA256:
  `f829744a02ed35f3fcf30a2f434a934f0441aa20af45be5f1f0d21b18a72b5cc`.
- Shader body SHA256:
  `90e7d5ac9626967e6be1eaf4e29b4279d792c198f0a557ca321c6a506f4edeb6`.
- Build mode: `candidate-tree-occlusion`. Source and artifact are under
  `vendor/tree-research/candidate-tree-occlusion-source` and
  `vendor/tree-research/artifacts/candidate-tree-occlusion`.
- Patch: `experiments/moltenvk-trees/patches/moltenvk-captured-tree-hiz-bypass.patch`.
  Helper: `experiments/moltenvk-trees/tree-cull-hiz-workaround.h`.
  Build, dependency and file fingerprints are in the experiment's `pins.json`.
- Heaps and Metal argument buffers remain enabled; private Metal API is disabled.
  `RDR2_MVK_TREE_HIZ_BYPASS=0` disables the workaround on a future restart.
- Candidate data: `~/Library/Application Support/RDR2Launcher-MoltenVK-Candidate`.
  Reuse its local game files, sign-ins and saves. No redownload or prefix reset.
  Eight saves were backed up and hash-verified before the successful app switch.
- Last verified game PID: 68577, with exact driver mapping and native
  `tree-hiz-bypass-applied` events. This is historical; revalidate any future PID.
  No owned GPU replay sessions remained at the last check.
- Original, control and unsuccessful candidate apps are preserved. Do not replace
  the signed working app; use a new app destination for further experiments.

## Evidence already saved

Private evidence is under `vendor/tree-research/host-private/`:

- `tree-occlusion-user-acceptance.json`: exact user confirmation and scope limits.
- `candidate-tree-occlusion-story-loaded-in-rdr2.json`: verified driver and activation.
- `captured-cull-workaround-results.json`: synthetic GPU controls and scope guards.
- `captures/camera-pair-active.json`: authoritative paths for the controlled pair.
  Visible trace: `game-5679a6c814f24ab98215f7810211762f/rdr2.gputrace`.
  Missing trace: `game-da4c37e53157424c9aa4c580b9d35ea4/rdr2.gputrace`.
- `captures/tree-instance-comparison.json`: identical mesh, compact IDs `[2, 3]`
  versus `[2]`; selected tree instance 3 disappears before vertex rendering.

Missing-state producer: `/commands/cb0/ce7/disp56`, API831, pipeline `@cps134`.
Selected draw: `/commands/cb0/re107/draw13`. Its exact small input buffers and
shader are saved in the missing analysis directory referenced by the pair manifest.
HiZ descriptor ID `0x6cf` maps to missing texture `@tex1873`, R32Float 128×72,
seven mip levels, heap offset 14,892,800. Mapping evidence is in
`selected-hiz-texture-mapping.json` in that analysis directory.

Six synthetic native GPU controls, changed/unrelated-shader and disable-switch
guards, seven allocation/policy checks, the query regression, app signature and
integrity checks, and five evidence tests passed. Synthetic depth reproduces the
tree rejection; the original numeric depth texture has not been reproduced.
The attempted heap-byte reconstruction failed fidelity checks and is not evidence
of corrupt game data. Normal gpudebug float texture export clips to PNG.

## Resume from here

1. Read this checkpoint, `STATUS.md`, then `experiments/moltenvk-trees/WORKING-STATE.md`.
   Treat older entries there as history; do not repeat failed comparisons.
2. Keep the working shader workaround as the baseline. Select one reliably
   disappearing rock or foliage object and establish its trigger with the user.
3. If a controlled camera pair is needed, use the existing capture workflow with
   the same position and one object visibly present/absent. Verify actual mapped
   driver and capture registration first; this GUI-launched session was not
   separately verified capture-enabled. Never launch another game over it.
4. Replay only after the game is saved and closed. On this 32 GB M1 Max, use one
   large replay at a time; game plus replay previously exhausted memory headroom.
5. Identify that object's exact draw, compact list and producer before extending
   the shader workaround. A different shader hash was deliberately left unchanged
   in the successful tree test; remaining objects are not automatically covered.
6. Investigate heap/depth/aliasing correctness using the identified resources.
   `MVK_CONFIG_USE_MTLHEAP=0` reportedly fixes flicker in the RDR2 fork but prevents
   startup in Highball reports. The earlier dedicated-buffer test never exercised
   its changed path in this game and did not rule out heap faults. Argument-buffer
   disabling and the query-result fix also failed to fix the visible tree issue.

The user subsequently requested committing and pushing this checkpoint and its
source changes. Use Git history to identify the containing checkpoint commit.
`vendor/`, `dist/`, captures and host data are ignored/private; a Git clone alone
will not preserve them. See `WORKING-STATE.md` for full build and capture history.
