# MoltenVK source comparison — 2026-10-26

## Physical-host follow-up

The older sections below retain the build-machine investigation. Physical-host
Control, revision 3 and argument-buffer-off visual tests still show the tree
issue; see [current host evidence](HOST-CANDIDATE.md). Revision 3's native
dedicated-buffer policy is enabled, but the game has not exercised eligible
dedicated buffers. Disabling argument buffers was exercised and did not fix it.

A new targeted candidate backports
[upstream query fix PR2794](https://github.com/KhronosGroup/MoltenVK/pull/2794),
which corrects nonzero-first-query range/availability offsets. Its functional
patch is separate from fixed diagnostic markers. The actual M1 GPU reproduces
the baseline GPU-copy defect; this is a driver correctness result, not proof
that RDR2's trees are caused by it. Build/GPU/visual results are recorded in the
host evidence. No global heap disable or image-error suppression is used.

## Reference established from this repository

The repository selects x64-crossover26.3-r27, Wine 11.0 and MoltenVK 1.4.2.
The original Highball component archive SHA-256 is
`7c84c592c023e761994cf4a0f5fb2e0a8a22bac8dfe3f787c4135a735f873e90`.
Its actual dylib, the staged portable runtime and the existing transfer app all
contain the same x86-64 dylib:
`294e9ef77c6036ab4f4d93117d752b6e31fa6c8c4345bc085e062a6ee3ced80a`.
AppleDouble metadata in the tarball is not a second driver.

The cached Highball checkout is cabadb4cfaaad0ece66f7fad2206fdd7a0b41ffb
(`v0.10.22-29-gcabadb4`). This describes source, not an installed host app.
Historical inspection verified that its build script and all three patches are
byte-identical to those at [r27's introduction](https://github.com/gauthierpiarrette/highball/commit/516da2758e699123ceee83b9a116bd28ceaaadf2).
The r27 manifest at that revision names the same component archive hash.

The script clones upstream tag v1.4.2, resolved to
db66022459ffb663aa2b50f6b018bc2e124f5edf. The control applies, in order:

1. shadow-import: optional imported-host-memory copies for 32-bit games;
2. linear-fallback: tolerate specifically identified unsupported linear image
   types by backing them with optimal-tiling textures;
3. shadow-readback: copy tracked GPU-written ranges back to shadowed host memory.

Exact patch hashes and post-patch file hashes are in pins.json. This reconstructs
the recorded recipe; it is not a byte-identical vendor-build attestation. The
published dylib does not expose a source commit through its version query.

A fresh-process, x86-64 query of vkGetMoltenVKConfigurationMVK reports:

| Setting | Bundled reference | Rebuilt control |
| --- | --- | --- |
| Version | 1.4.2 / Vulkan 1.4.357 | same |
| Configuration struct | 184 bytes | same |
| useMTLHeap | 1 | 1 |
| useMetalArgumentBuffers | 1 | 1 |
| useMetalPrivateAPI, even when requested | 0 | 0 |
| liveCheckAllResources | 0 | 0 |

MVKEnvironment.cpp clamps the private-API setting to the compile-time capability.
The observed zero despite requesting one therefore supports a private-API-disabled
reference build. Do not copy the fork's recommendation to enable it into this control.
The probe does not create a Vulkan device or inspect the game's effective launch environment.

## What the fork actually changes

The inspected [fork head](https://github.com/whitebelyash/MoltenVK-RDR2/tree/b86c21db33ee71eb012c0c95dc7b2ff4cf9d2050)
is based on upstream 0ecb1dc5410ed0e12f64fec4f0d381dec8817b1a, an ancestor of
v1.4.2. Its final code diff from that base changes three files, plus its README:

| Change | Exact behavior | Treatment here |
| --- | --- | --- |
| ddb06d66, heap change | Sets the global heap default to zero | Not ported globally |
| 59d34ab4, argument buffers | Disables the default use of Metal argument buffers | Keep enabled for a controlled comparison |
| 6c19b557, coherent images | Permits host-coherent optimal-tiling images on Apple GPUs | Already represented in v1.4.2's Apple-GPU guard |
| MVKImage constructor | Clears configuration errors after image validation | Do not port; it can hide unsupported resource requirements |

The coherent-image guards are not textually identical: v1.4.2 skips the dedicated
coherent-image validation block on Apple GPUs, while the fork changes its inner
error condition and can still create a mapping buffer there. That allocation-timing
difference is not ported into this control.

The [fork README](https://github.com/whitebelyash/MoltenVK-RDR2/blob/b86c21db33ee71eb012c0c95dc7b2ff4cf9d2050/README.md)
attributes tree/object improvement to disabling heaps and also reports missing
water reflections/waves. These are upstream observations, not results reproduced here.
The argument-buffer and error-clearing differences prevent treating a wholesale
fork replacement as a one-variable heap test. The fork's gl_CullDistance conclusion
also does not establish the cause on this M1 Max.

## Why global heap disabling conflicts with this renderer

In v1.4.2, physical-device initialization gates placementHeaps on the heap setting
and GPU support. MVKImage::validateConfig and image-format capability checks reject
2D-on-3D and block-texel-compatible view flags when placement heaps are unavailable.
MVKImagePlane::getMTLTexture also needs an actual heap to create those aliased views.
This is a real resource requirement, not a warning to suppress.

[Highball issue 93](https://github.com/gauthierpiarrette/highball/issues/93)
records the same startup failure with heaps disabled. The issue's later 1.4.2 test
still had disappearing trees. Its primary subject is Epic entitlement handling;
the tree investigation is in the comments. The fork's blanket clearing of image
configuration results is a further reason that its startup behavior cannot be
assumed equivalent to Highball's narrower linear fallback. It does not implement
the missing placement-heap behavior, and will not be used as an error bypass here.

## Proposed narrow experiment, not an established fix

moltenvk-dedicated-buffer-no-heap.patch adds an opt-in diagnostic allocation policy
for Apple GPUs. Only a VkMemoryDedicatedAllocateInfo allocation for a buffer,
without an image, imported host memory, external memory, existing Metal resources
or a requested Metal-buffer export, bypasses initial heap creation. Existing
standalone-buffer allocation is then used. It leaves image allocation, mixed and
suballocated memory, argument buffers and all validation unchanged.

Activation is `RDR2_MVK_DEDICATED_BUFFER_NO_HEAP=1`; it is off otherwise. The first
eligible allocation emits a fixed marker. If no marker appears during the game
run, that scene has not exercised this experiment and its visual result cannot
rule out a broader heap hypothesis. A dedicated buffer can use its standalone
backing without breaking shared buffer/image aliasing, because mixed allocations
are excluded. This does not prove that dedicated buffers cause the tree issue.

Possible outcomes include no effect, additional buffer-allocation pressure or
different performance. It will not fix a fault confined to non-dedicated memory,
image heaps, shader translation, visibility queries or resource lifetime. The
patch applies cleanly to the pinned control but has deliberately not been applied
or compiled: the supplied plan requires a working in-game control first.

## Build deviation and remaining proof

Highball's script uses Xcode packaging. This VM has CLT only. MoltenVK v1.4.2
contains an upstream CMake build path, which successfully produced the control
using the same source/dependency revisions and configuration above. This is a
documented build-backend/toolchain difference, not a claim of exact release parity.
The compiler, SDK, flags and dependency pins are recorded in control/build.json.
The macOS 14 deployment target is a build setting, not compatibility evidence;
upstream code produced availability warnings with the installed macOS 27 SDK.

The new control has the same compatibility major, all original exported Vulkan
entry points, all three patch markers, only system dylib dependencies and a valid
ad-hoc signature. A configuration diagnostic proved the selected copied library
was mapped, and restoring the original checksum in that isolated engine succeeded.
No RDR2 tree scene, host save backup, game launch with the control, FPS or visual
regression result has been collected in this VM. Those are the next gate.
