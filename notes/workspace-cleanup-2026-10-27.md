# Main app and workspace cleanup — 2026-10-27

Follow-up: the tested environment was subsequently migrated to the permanent
`~/Library/Application Support/RDR2Launcher/` name, with the older prefix
archived and a compatibility symlink preserving old paths. The main edition
is now `patched`. See [migration and recovery](data-folder-migration-2026-10-27.md).
The data-directory descriptions below record the initial cleanup state.

The main app is now `dist/RDR2Launcher.app`. Build it with `scripts/build.sh` and
open it with `scripts/launch-rdr2.sh`, or open the app directly in Finder.
It contains the exact driver accepted in the tree, foliage and rock comparisons:
`b914dc101ebcc70a415caabc69a2587efcb6770ee0ca27d7db2285935038fdce`.

The build recompiles the native executable and packages that signed driver;
it does not recompile MoltenVK. It rejects a different binary or different
source pins. It stages and verifies the new bundle before replacing the main
app, without accumulating backup apps. All source patches remain tracked under
`experiments/moltenvk-trees/`. Changing the renderer still requires the separate
pinned source build and GPU-validation workflow there.

Only two local build inputs remain in `vendor/`:

- `rdr2-runtime-r27-portable-v3/`: the complete baseline runtime and licenses.
- `renderer/current/`: the accepted signed driver and its full build metadata.

These inputs are ignored by Git and must be retained for offline rebuilds.
They are recoverable from the archive's original runtime and
`vendor/tree-research/artifacts/candidate-rock-occlusion/` if needed.
The build generates `.build/main/` and `.cache/main/`; both are disposable.

With the user's approval, older files were moved to the private directory:

`/Users/ruansunkel/Personal/RDR2-archive-20261027/`

Relative paths are preserved. Its `ARCHIVE-MANIFEST.json` lists every moved
root, and `README.txt` gives recovery instructions. The archive contains:

- `vendor/probes/`, including the older ~123 GB Steam/game environment and
  private account state. It was preserved rather than deleted as build cache.
- `vendor/tree-research/`, including ~66 GB of captures, private results,
  save backups, downloaded source/dependencies, build tools and driver artifacts.
- Earlier runtime stages, media downloads/extractions and source builds.
- Earlier `dist/` bundles and packages, including the accepted diagnostic app,
  retained for rollback and historical evidence; old `logs/` are also preserved.

The project shrank from about 217 GB to 2.2 GB, including the app and retained
build inputs. Archiving on the same volume does not reclaim the archived disk
space. Regenerable Swift/module/Python caches were removed separately after
verification.

Validation: all 18 Python checks and 17 Swift core checks passed. The main app
rebuilt successfully with the archived research folders absent, including
replacement of an existing main app. Its renderer checksum, dependency audit,
deep/strict signature verification and runtime-integrity diagnostic passed.
The diagnostic also confirmed the existing candidate data directory. No new
gameplay comparison was needed: this packages identical tested renderer bytes.

The active host environment at
`~/Library/Application Support/RDR2Launcher-MoltenVK-Candidate/` and the external
library at `~/Games/RDR2/` were left in place. No game, prefix, account state or
save was deleted. The main app keeps the internal `moltenvk-candidate` edition
and default data directory to reuse that environment, with normal main-app
branding. The launch helper now selects only the main app by default, and no
longer falls back to an older build or the archived build-Mac prefix.

Historical evidence notes intentionally retain their original absolute and
relative paths. To resume a capture investigation, close the game/tools and
move the required archived folders back to those original paths if absent.
Do not run cached source builds directly from the archive: their paths refer
to the old project locations. The archive contains private data and is not a
Git or distribution artifact.
