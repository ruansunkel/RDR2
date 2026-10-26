# RDR2 / Highball — Disappearing Trees Fix Plan

## Objective

Investigate and fix **entire trees disappearing and reappearing when rotating the camera** in *Red Dead Redemption 2* running on an **Apple M1 Max** through **Highball → Wine/Rosetta → Vulkan → MoltenVK → Metal**.

Current observations:

- Graphics settings are already at Ultra.
- Tree Tessellation is already disabled.
- Entire trees vanish, rather than merely changing level of detail.
- The problem occurs using Highball's MoltenVK rendering path.

**Working hypothesis:** A MoltenVK rendering or resource-management compatibility issue, possibly involving Metal heaps or culling-related data. This is **not yet a proven root cause**.

**Strategy:** Reproduce the problem, compare Highball's MoltenVK changes with the reported workaround in `whitebelyash/MoltenVK-RDR2`, and test the smallest compatible change in an isolated Highball engine. Never overwrite the known-good engine.

## Source repositories and references

- Highball: <https://github.com/gauthierpiarrette/highball>
- Highball report concerning RDR2 tree flickering: <https://github.com/gauthierpiarrette/highball/issues/93>
- MoltenVK-RDR2 workaround: <https://github.com/whitebelyash/MoltenVK-RDR2>
- Upstream MoltenVK: <https://github.com/KhronosGroup/MoltenVK>

The separate MoltenVK-RDR2 project reports improvements when disabling Metal heaps. However, Highball testing reportedly encountered startup failures with that approach. **Do not assume simply setting `MVK_CONFIG_USE_MTLHEAP=0` will work.**

## Phase 1 — Capture baseline and create rollback

1. Record the macOS version, Highball version, Wine engine revision and bundled MoltenVK version/commit.
2. Record the effective Vulkan/MoltenVK environment variables and launch options.
3. Back up RDR2 saves separately from the Wine environment.
4. Duplicate the Highball game environment/engine if supported. Otherwise, create a fully separate copy of the relevant engine files.
5. Keep all experiments in a separate working directory. Do not alter a shared engine used by other games.
6. Find an in-game location where tree disappearance is reproducible; save there and record a video while rotating the camera without moving.
7. Collect baseline logs, screenshots, FPS and memory usage.

**Deliverable:** Reproducible baseline with a tested rollback path.

## Phase 2 — Compare the MoltenVK implementations

Clone the repositories:

```bash
git clone https://github.com/gauthierpiarrette/highball.git
git clone https://github.com/whitebelyash/MoltenVK-RDR2.git
```

Investigation tasks:

1. Identify the **exact MoltenVK commit/tag** used by the installed Highball engine. Do not assume the current Highball source matches the installed binary.
2. Find Highball's MoltenVK build scripts, patches, flags and library packaging method.
3. Inspect the MoltenVK-RDR2 fork's commits and diffs against its upstream base, especially any changes involving `MTLHeap`, memory allocation, image aliasing or image views.
4. Verify the actual implementation behind the reported tree-flicker fix: is it a global heap disable, a targeted allocation workaround, or another change?
5. Identify conflicts with Highball's own patches (including its image/linear-fallback work, if applicable).
6. Explain why disabling Metal heaps prevents startup in some Highball configurations and which resource usages require them.
7. Choose the smallest testable patch. Prefer targeted fixes over disabling heaps globally.

**Deliverable:** A short technical comparison and candidate patch, with known risks.

## Phase 3 — Build a control MoltenVK

### Prerequisites

- Xcode and Xcode command-line tools
- Git, CMake, Python and any additional tools required by Highball's *actual* build documentation
- Free disk space for source, intermediates, logs and engine backups

First build the **unmodified Highball MoltenVK** at the same version and configuration as the installed engine. Verify that the resulting dylib has the required architecture and dependencies.

Highball has used `Scripts/build-moltenvk.sh` and custom patch arguments. The following is an **illustrative example only**; inspect `--help` / script source and confirm the correct patch names and tag before executing:

```bash
cd highball

MVK_USE_METAL_PRIVATE_API=1 \
MVK_PATCHES="shadow-import linear-fallback" \
Scripts/build-moltenvk.sh v1.4.2 \
  "$PWD/build-mvk-control"
```

**Important:** The tag `v1.4.2`, flags, paths and patch names must be checked against the locally installed Highball engine. They must not be treated as verified instructions for every revision.

Validate the build:

```bash
file /path/to/libMoltenVK.dylib
lipo -info /path/to/libMoltenVK.dylib
otool -L /path/to/libMoltenVK.dylib
```

Check the actual architecture required by the game's Wine/Vulkan loader; Highball's Wine setup may use an x86-64 MoltenVK library under Rosetta. Do not assume an ARM64 dylib can be substituted for it.

**Deliverable:** Reproducible, unmodified control build that launches RDR2 in an isolated environment.

## Phase 4 — Implement the experimental fix

1. Create a separate Git branch and patch file, tentatively `moltenvk-tree-heaps.patch`.
2. Port the minimum relevant changes from the fork to Highball's pinned MoltenVK version, taking care with API changes and patch ordering.
3. Preserve Highball's existing required patches, build flags and any Metal-private-API integration.
4. If global heap disabling prevents launch, investigate selective resource allocation instead: preserve heap-backed images where required and test non-heap allocation only for compatible resource types.
5. Build a modified dylib with the **same ABI and architecture** as the control build.
6. Log the exact source commits, patch checksums and compiler/build settings.

Avoid hiding startup errors or bypassing Vulkan validation as a supposed fix.

**Deliverable:** Reproducible patched MoltenVK library with clear explanation of the changed behaviour.

## Phase 5 — Integrate into Highball safely

Target rendering path:

```text
Red Dead Redemption 2 (Vulkan)
             |
         Highball / Wine
             |
     Custom MoltenVK dylib
             |
        Apple Metal
             |
         M1 Max GPU
```

1. Prefer a **custom isolated Highball engine or environment**, registered through the supported engine mechanism if available.
2. Determine which MoltenVK dylib the Vulkan loader actually opens (there may be more than one copy).
3. Back up the original dylib within the isolated environment before replacement.
4. Replace or redirect **only** that isolated environment's library.
5. Start RDR2 and verify logs or loaded-library inspection prove it is using the patched binary.
6. Confirm that Steam and Rockstar Launcher still work as before.

**Do not** install a modified dylib system-wide, overwrite `/usr/local` or Homebrew libraries, or alter Highball's shared default engine.

**Deliverable:** Launchable test environment with a clearly identified patched MoltenVK build.

## Phase 6 — Controlled regression tests

Use the same save, location, camera rotation, resolution and graphics settings throughout.

| Test | Configuration | Expected observation |
|---|---|---|
| A | Original Highball engine | Reproduce tree disappearance |
| B | Unmodified control rebuild | Confirm same behaviour as A |
| C | Patched MoltenVK engine | Trees remain visible during camera rotation |
| D | Patched engine, multiple starts | No launch failures or new artifacts |
| E | Restore original engine | Return to original baseline |

Also check:

- Nearby and distant trees; panning slowly and rapidly
- Day/night, shadows and lighting
- Water, reflections and transparent vegetation
- Texture streaming and terrain
- GPU memory use and stability
- Average frame rate and frame-time consistency

The reported workaround may cause rendering regressions, including water-related issues. Document them instead of calling the patch successful solely because trees stop disappearing.

If trees are still vanishing, gather fresh MoltenVK validation/debug logs and investigate pipeline differences, geometry submission, occlusion and resource lifetime. Do not assume the Metal-heap hypothesis is correct.

## Phase 7 — Package and document

Prepare:

- `moltenvk-tree-heaps.patch` (or a better name matching the actual fix)
- A pinned, repeatable build script
- An installation script that modifies only an explicit **test** engine directory
- A rollback script that restores original binaries and validates checksums
- A `README.md` with installation, testing, limitations and version compatibility
- Before/after captures and launch logs

If the patch works reliably, prepare a focused Highball pull request or issue comment linking the original report and including reproduction details.

## Acceptance checklist

- [ ] Original Highball environment is backed up and restorable
- [ ] Original tree disappearance is reproducible in a fixed scene
- [ ] Unmodified MoltenVK control build launches RDR2
- [ ] Patched MoltenVK library is confirmed loaded at runtime
- [ ] Entire trees no longer disappear when rotating the camera
- [ ] No new water, reflection, shadow, texture or lighting regressions
- [ ] Startup and prolonged play remain stable
- [ ] Performance and memory use remain acceptable
- [ ] Patch and build are reproducible from pinned source revisions
- [ ] Rollback script successfully restores original behaviour

## Priorities for the implementing agent

1. **Confirm installed versions and reproduce first.**
2. **Inspect the source diffs; do not blindly replace a dylib.**
3. **Build an unmodified control before introducing fixes.**
4. **Use isolated engine copies and preserve rollback.**
5. **Prefer a minimal fix that works with Highball's existing Vulkan resource requirements.**
6. **Test visual quality, not just whether the game launches.**
7. **Clearly report what is proved, what remains a hypothesis and which tests failed.**

## Desired outcome

A locally reproducible Highball-compatible MoltenVK patch that keeps RDR2's trees visible during camera rotation, without compromising game startup, visual correctness or the ability to revert to the original engine.
