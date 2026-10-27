# How to build & run

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
