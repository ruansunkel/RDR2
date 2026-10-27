# Exact rendering and diagnostic changes — 2026-10-27

The current app is `dist/RDR2Launcher.app`, rebuilt by `scripts/build.sh` with
the exact renderer accepted in the rock diagnostic app. The original diagnostic
bundle is preserved in the external workspace archive.
The user confirmed the selected tree, foliage and rock examples in their
respective camera-turn comparisons. The latest app includes all three guarded
workarounds; native events verified all three active in its RDR2 process.

Renderer SHA256:
`b914dc101ebcc70a415caabc69a2587efcb6770ee0ca27d7db2285935038fdce`.

This changeset follows checkpoint `51f5318`. The tree workaround was already in
that checkpoint. The new functional renderer changes add foliage and rock
coverage to the same approach. These are targeted occlusion workarounds; the
original numeric depth texture and a heap root cause have not been reproduced.

## What the renderer changes

The driver is built from MoltenVK 1.4.2, upstream commit
`db66022459ffb663aa2b50f6b018bc2e124f5edf`, with the existing Highball patches.

At `MVKShaderLibrary::compileLibrary()` in `MVKShaderModule.mm`, each helper:

1. Finds its exact generated Metal Shading Language (MSL) branch.
2. Calculates SHA256 over the entire MSL body, starting at
   `#include <metal_stdlib>` and ending at the end of the source string.
3. Requires the corresponding captured-shader fingerprint below.
4. Replaces only that HiZ branch condition with `if (false)`. The shader then
   follows its existing path for disabled depth occlusion.

HiZ is the hierarchical depth test used to reject objects considered hidden.
Frustum, screen-rectangle, distance, fade and LOD checks remain in the shader.
The generated preamble before the first Metal standard-library include is
outside the fingerprint. A nonmatching MSL body or disabled helper is unchanged.
The hook also runs when cached MSL is decompressed and compiled.

| Target | Complete MSL body SHA256 | Branch replaced | Change relative to `51f5318` |
| --- | --- | --- | --- |
| Captured tree | `90e7d5ac9626967e6be1eaf4e29b4279d792c198f0a557ca321c6a506f4edeb6` | `if (((*spvDescriptorSet0.m_12)._m0[0u]._m5 != 0u) && _544)` | Existing helper retained |
| Packed foliage | `7d71e03178769c66f09ff9247f18e7d686634b23ca4759521e180ae677b2b739` | `if (((*spvDescriptorSet0.m_45)._m0[0u]._m5 != 0u) && _596)` | New helper and compiler hook |
| Rigid objects, isolated from the rock | `95a4b16527bcfbe7d4818bc0e837d88257ecaf9419be0ac694062d7be2080ad6` | `if (((*spvDescriptorSet0.m_12)._m0[0u]._m5 != 0u) && _542)` | New helper and compiler hook |

The rigid-object shader may serve other objects using that same shader. Its
guard identifies the complete shader, rather than a particular rock asset.

The new source is in
[`foliage-cull-hiz-workaround.h`](../experiments/moltenvk-trees/foliage-cull-hiz-workaround.h),
[`rock-cull-hiz-workaround.h`](../experiments/moltenvk-trees/rock-cull-hiz-workaround.h)
and their corresponding patches under `experiments/moltenvk-trees/patches/`.
`pins.json` records patch hashes, modified source hashes and added-header hashes.

| Native launch variable | Effect when set to `0` before starting Wine |
| --- | --- |
| `RDR2_MVK_TREE_HIZ_BYPASS` | Disable the existing tree workaround |
| `RDR2_MVK_FOLIAGE_HIZ_BYPASS` | Disable the new foliage workaround |
| `RDR2_MVK_ROCK_HIZ_BYPASS` | Disable the new rigid-object workaround |

These switches default on in the corresponding diagnostic builds. The GUI does
not inherit arbitrary shell variables; the variable must reach the native Wine
child. Fixed per-process events record each matching source fingerprint and
whether its bypass applied.

## Evidence behind the changes

| Example | Captured failure | Isolated GPU control | User result |
| --- | --- | --- | --- |
| Tree, earlier checkpoint | Compact IDs `[2,3]` became `[2]` | Disabling HiZ retains the selected instance 3 | "it works" |
| Foliage, this changeset | Matching mesh dropped from 12 instances to 7 | Five previously visible IDs 17,75,85,136,137 pass the missing camera's other checks | "Stays visible" |
| Rock, this changeset | Identical indices and all three vertex streams; main instance73 disappeared while its shadow still drew | Instance73 survives with HiZ disabled | "It is visible now" |

The new foliage and rock probes each exercise six depth/fast/precise-math cases,
plus changed-source, unrelated-source and disable-switch guards. They use the
captured small input buffers and synthetic depth with seven mip levels. They
do not reproduce the original numeric depth.

The new heap-integrity probe compares nine captured texture placements across
standalone textures, placement heaps and placement heaps with an aliasable
parent buffer. All three modes checked 884,304 values with zero mismatches. This
does not reproduce the game's complete resource reuse or synchronization.

## Build, packaging and capture tools

- `build.py` adds pinned `candidate-object-occlusion` and
  `candidate-rock-occlusion` variants in separate source/build/artifact folders.
- `build-candidate-app.py` packages each into a new app, requires the applicable
  captured-shader controls, and checks the exact candidate's allocation/query
  results. The rock app retains all three guards.
- `replay-camera-pair.py --pair` accepts a separate pair manifest, preserving
  the original tree pair while analyzing foliage or rocks.
- `switch-host-app.py` checks for a Wine server holding the exact selected prefix
  before asking Steam to shut down. This avoids starting Steam in an already
  closed environment just to send it a shutdown request.
- `--capture-session` restarts the same diagnostic app capture-enabled.
  `--capture-new-app` switches apps and explicitly launches the new app's native
  runtime capture-enabled. The flags are mutually exclusive. Both refuse a
  running game, use scoped client shutdown and verify save backups before launch.
- Five session/environment tests cover closed-prefix behavior, exact prefix
  matching, inspection failures, a server-exit race and selection of the new
  runtime's environment. The Python suite now contains 18 tests.
- `.gitattributes` treats the experiment's `.patch` files as preserved diff data
  for whitespace checking, keeping checksum-pinned upstream context bytes intact.

All seven allocation/policy runs, the query-result regression, signature and
runtime-integrity checks passed against the final driver. Existing reports are
in the ignored private evidence folder. Before publication, the full repository
check passed 18 Python tests and 17 Swift core checks with fresh project-local
caches, and both new variants' source/patch pins were reverified. See
[the software inventory](build-and-test-software.md).

## Scope and preserved baseline

Heaps and Metal argument buffers remain enabled; Metal private API is disabled.
The earlier query-range/availability correction and dedicated-buffer allocation
experiment are retained from the previous checkpoint. RDR2 still has not
exercised that experiment's eligible dedicated-buffer path, so it provides no
proof of a heap fix.

The accepted tree-only and tree/foliage apps, game files, sign-ins and saves are
preserved. No graphics-settings adjustment was used to obtain the new results.
The final acceptance reports are stored separately from immutable build-time
metadata and the signed app. Performance, broad-scene coverage and extended
stability remain unmeasured; bypassing occlusion can draw extra objects.

Git contains the patches, helper/probe sources, tools, tests and documentation.
Apps, third-party caches, captures, save backups and private client state remain
local and ignored. Full investigative evidence is summarized in
[`evidence/remaining-objects.md`](evidence/remaining-objects.md).
