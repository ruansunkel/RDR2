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

## Game Mode and launcher icon

New builds include the launcher icon and a Wine helper that macOS recognizes as
a game. Enter macOS full screen in RDR2 to make Game Mode available. Check its
status with **Command–Esc → Settings → Game Mode** while playing.

For automatic full screen, click **Game Mode…** in the launcher, choose
**Enable automatic full screen**, and allow the launcher in **System Settings →
Privacy & Security → Accessibility**. Keep the launcher open. It requests full
screen once for the focused RDR2 window; exiting full screen stays under your
control. Manual full screen works without Accessibility permission.

Game classification has been verified; RDR2 activation and performance checks
remain pending. See [implementation and validation](notes/game-mode-integration-2026-10-28.md).

## Water reflection investigation candidate

```sh
scripts/build.sh --water-reflection-candidate
open dist/RDR2WaterCheck.app
```

This separate candidate preserves visibility-pass inversion in the occlusion
workarounds. GPU controls pass; the water comparison is still pending. See
[investigation notes](notes/water-reflection-investigation-2026-10-27.md).
