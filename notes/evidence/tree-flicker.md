# Tree flicker investigation — 2026-10-26

The user reports trees disappearing and reappearing on Ultra. The suggested
comparison with Tree Quality High did not resolve the reported symptom. The
user clarified: **"Both nearby and distant trees pop in and out of existence.
Also change shape."** This is broader than leaf-edge shimmer or a report limited
to distant LOD transitions; the exact rendering defect remains unconfirmed.

The saved host configuration inspected during investigation has Vulkan selected
and Tree Tessellation disabled. Tree Quality is saved as Ultra; this snapshot
does not establish the live setting during the user's comparison test. No game
settings, runtime binaries, prefixes, sign-ins or saves were changed for this
investigation.

The selected runtime contains MoltenVK
`1.4.2+shadow-import-1+linear-fallback-1+shadow-readback-1` from the pinned component
in `config/engine-upstream.json`. The linear fallback is necessary for the
previously verified game startup; a stock MoltenVK replacement is not equivalent.
The reviewed Highball r28 and r29 manifests pin the identical MoltenVK checksum.
In particular, [r29's manifest](https://raw.githubusercontent.com/gauthierpiarrette/highball/main/spike/engines/x64-crossover26.3-r29.json)
describes r29 as identical archives to r27. A revision-number-only upgrade does
not supply a tree-rendering fix.

## Upstream evidence

- [Highball issue 93](https://github.com/gauthierpiarrette/highball/issues/93):
  another player reports nearby disappearing trees during otherwise smooth
  gameplay. Disabling Metal heaps prevented startup. Testing MoltenVK 1.4.2
  subsequently did not resolve that player's tree flicker. The issue's closed
  state refers to its original Epic entitlement problem, not a confirmed tree fix.
- [Highball issue 261](https://github.com/gauthierpiarrette/highball/issues/261):
  the maintainer suggests Tree Tessellation Off as an unconfirmed experiment and
  retracts the heap-disable suggestion because it prevented startup.
- [MoltenVK-RDR2 fork](https://github.com/whitebelyash/MoltenVK-RDR2):
  its README reports that disabling Metal heaps fixed tree/object flicker in that
  fork. This is a lead for a separate renderer experiment, not evidence that the
  same change works in the pinned Highball component. The fork publishes no
  release binaries. Its documented build uses full Xcode; this host currently
  has Command Line Tools, without full Xcode or CMake.

There is no validated renderer fix from this investigation. The similar upstream
reports make a rendering compatibility problem plausible, but the local cause
has not been established. Global heap-disable variables, runtime replacement and
DirectX 12 have not been applied or tested on the user's installation.
