# How to build & run

These commands require the prepared `vendor/` inputs. Fresh-clone setup is
[planned for later implementation](notes/fresh-clone-build-plan.md).

Run these commands from the project folder. Quit RDR2, Windows Steam/Rockstar
and the launcher before switching builds. Both builds reuse the existing game,
prefix, saves and sign-ins.

## With tree, foliage/grass and rock fixes

```sh
scripts/build.sh
open dist/RDR2Launcher.app
```

## Without the tree, foliage/grass and rock occlusion fixes

```sh
scripts/build.sh --without-occlusion-fixes
open dist/RDR2GraphicsCheck.app
```

The comparison keeps the earlier allocation/query changes.

## Water reflection investigation candidate

```sh
scripts/build.sh --water-reflection-candidate
open dist/RDR2WaterCheck.app
```

This separate candidate preserves visibility-pass inversion in the occlusion
workarounds. GPU controls pass; the water comparison is still pending. See
[investigation notes](notes/water-reflection-investigation-2026-10-27.md).
