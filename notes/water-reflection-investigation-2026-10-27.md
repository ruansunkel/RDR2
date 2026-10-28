# Water reflection regression investigation — 2026-10-27

The initial report attributed incorrect reflections to the tree/foliage/rock
build. During the controlled comparison, the user corrected this direction:
**the earlier frame without the occlusion fixes shows the problem, and the
currently running accepted fixed build has correct water**. Both processes'
actual renderer mappings were verified. Both water views have now been captured;
the second image export and detailed comparison are pending. The main accepted
app and its renderer have not been replaced.

## Confirmed defect in the earlier workarounds

All three complete-source-matched culling shaders have this structure:

```text
if (HiZEnabled && survivesOtherCulling) {
    visible = depthTestApplies ? sampleDepthHierarchy() : true;
    result = (flags & 1) ? !visible : visible;
} else {
    result = survivesOtherCulling;
}
```

The accepted helpers replace the entire outer condition with `if (false)`.
This also bypasses the inversion controlled by bit 0 of `_m15`. Consequently,
both normal and inverted modes admit the same selected instances. The prior
six-case probes used captured flags `0xfe`, which never exercised inversion.
The role of this mode in the reported water scene is not established yet.

The new `candidate-pass-safe-occlusion` variant instead replaces only the inner
condition (`_512`, `_564`, `_510` respectively). The existing `visible = true`
fallback avoids unreliable depth rejection while preserving the outer enable
gate, inversion, and all subsequent processing. When enabled, the normal mode
retains the previous workaround's output; the inverse mode excludes those
visible instances. When disabled, behavior matches the original shader.

The original shader SHA256 guards, opt-out variables, earlier patches and
accepted artifacts are preserved. A new patch is applied after the old three
helpers; new helper headers match the separately pinned source variant.

## GPU evidence

`probe-cull-passes.mm` compared original, legacy and revised shaders on the
physical Apple GPU, using the small captured buffers and synthetic depth.
It exercised all three shaders, both math settings, HiZ on/off, inversion
on/off, and depths 0/300/10000: **216 dispatches passed**.

The legacy inverse-mode defect reproduced in all **18** enabled inverse cases.
Revised normal outputs retained tree IDs `[2,3]`, all 12 foliage IDs including
the five previously disappearing IDs `17,75,85,136,137`, and rock ID `[73]`.
All output argument counts matched the original all-visible-depth reference.
Changed-source, unrelated-source, disabled-switch and changed-preamble controls
passed. These tests do not render water or reproduce the game's numeric depth.

The exact new renderer also passed seven GPU allocation/policy comparisons and
the query regression against the control's expected failure. Its configuration
retains heaps and Metal argument buffers and disables Metal private API.

Candidate renderer SHA256:
`9365083cbc918b9541e0726466099eb7b402c7c3407c0ecde3ffb870071432bf`.

Local evidence is in `vendor/water-research/` and
`vendor/tree-research/artifacts/candidate-pass-safe-occlusion/`. Build dependencies
and the candidate source were copied back into the workspace from the private
archive; archived originals and private game/account data were preserved.

## Build and compare

```sh
scripts/build.sh --water-reflection-candidate
open dist/RDR2WaterCheck.app
```

This produces a separately named and signed app using the existing permanent
RDR2 environment. Its packaging requires exact-driver shader, allocation and
query evidence. `scripts/build.sh` still selects the earlier accepted renderer;
`--without-occlusion-fixes` still produces the original graphics comparison.
The build validates common and selected-variant pins for each profile, allowing
an unrelated new experimental variant without invalidating older artifacts.

The capture/session tools now validate both legacy research app profiles and
the current `accepted-renderer.json` profiles, including the actual private
renderer hash and matching data-folder name. This enables captures from both
the original and fixed permanent-environment apps. Switching still refuses a
running game and backs up saves after the selected prefix closes normally.

To reproduce the new GPU controls after building the pinned variant:

```sh
python3 experiments/moltenvk-trees/probe-cull-passes.py \
  --inputs vendor/water-research/inputs \
  --artifact vendor/tree-research/artifacts/candidate-pass-safe-occlusion
```

The private small inputs have `tree/`, `foliage/`, `rock/` subdirectories with
their captured MSL and buffers. They are retained locally, not published in Git.
Use the existing `build.py --mode candidate-pass-safe-occlusion` and GPU allocation
and query probe commands for the renderer build. Historical signed-control
evidence now points to the preserved archive paths in its local relocated copy.

## Original-water capture

The user reached the example and confirmed a stationary camera. This view was
initially described as correct; the user later identified its exported image as
showing the reflection problem. The original comparison process was reverified
against its exact driver and local WineMetalLayer boundary before capture.

The first two-frame request exceeded the historical 55-second timeout while
downloading resources; no trace was produced. The scoped stop reported no active
capture. Its logs remain preserved as an unsuccessful attempt. A subsequent
single-frame request with a 180-second allowance completed in about 44 seconds:
`game-ec52207f81814b299b2e0b5b2025417d/rdr2.gputrace`, 10,334,127,376 bytes.
The capture tool now accepts a bounded `--timeout` (15–300 seconds) and records
the selected limit in its report.

Private frame manifest: `vendor/tree-research/host-private/captures/water-original-frame.json`.
Progress record: `vendor/tree-research/host-private/water-investigation-state.json`.
The user saved and closed RDR2 normally. Owned replay session 41 exported the
original frame and was released before launching another game. The inspected
image shows Arthur beside a snowy stream, with snow-covered boulders, trees,
and reflections along the opposite bank. The output is recorded under the
capture's `analysis-pair-f2372a24e2884546a446367fa2882b06/visible.png`.

The original prefix's clients then closed normally, save backups were verified,
and the accepted fixed build was launched capture-enabled. The user positioned
the camera and reported this version looks correct, then explicitly confirmed
that the earlier exported frame shows the problem. This supersedes the initial
regression-direction report; the observation history is retained in the private
frame manifests and progress record.

RDR2 PID18200 was verified mapping the accepted fixed driver
`b914dc101ebcc70a415caabc69a2587efcb6770ee0ca27d7db2285935038fdce`.
Its single-frame capture completed:
`game-8042b6d712204ddf98647fe18961a0bc/rdr2.gputrace`, 9,809,064,165 bytes.
Private manifest: `vendor/tree-research/host-private/captures/water-fixed-frame.json`.
The user has been asked to quit normally before this second large replay is
opened. The separate pass-preserving candidate has not been used for either
frame and must not be credited with the reported correct water.
