# Fresh-clone build setup — implementation backlog

Recorded 2026-10-27. This is planned work; no setup command has been implemented.

The intended outcome is that an Apple Silicon Mac can clone this repository
without `vendor/`, prepare its public dependencies, and build either app. No
copy of this machine's archive, game installation, sign-ins, saves or GPU
captures should be required to compile and package the documented recipes.

## Current limitation

`scripts/build.sh` rebuilds the Swift launcher and packages already staged local
inputs. It does not download or prepare them. It requires:

- `vendor/rdr2-runtime-r27-portable-v3/`: the portable baseline runtime.
- `vendor/renderer/current/`: the accepted renderer with all three workarounds.
- `vendor/renderer/without-occlusion/`: the comparison renderer, when requested.

Runtime reproduction steps exist in `BUILD.md`. Pinned MoltenVK sources, patches
and build/probe tools exist under `experiments/moltenvk-trees/`. Two gaps prevent
these pieces being a supported fresh-clone workflow:

- Candidate compilation currently requires local recorded host-control
  acceptance, including files and app paths unavailable in a fresh checkout.
- Packaging requires the exact historical tested renderer hashes in
  `config/accepted-renderer.json`. A new compiler, SDK, source path or signing
  operation may produce different bytes despite using the same source recipe.

## Implementation checklist

1. **Add a setup entry point.** Proposed name: `scripts/setup.sh` (not currently
   available). Check Apple Silicon/macOS support, Apple command-line developer
   tools, Python and the requirements for Intel GPU probes. Report missing
   prerequisites clearly. Keep downloaded tools, sources and caches local to
   the project; do not install a global package manager or Wine.
2. **Prepare the portable runtime.** Orchestrate the existing pinned Highball
   checkouts, runtime/media downloads, safe extraction, FFmpeg build, GStreamer
   preparation, relocation and notice collection. Verify archive checksums and
   exact source revisions. Produce the current baseline runtime layout. Keep
   excluded components excluded and preserve required licenses/provenance.
3. **Build both renderer recipes.** Produce `candidate-rock-occlusion` for the
   regular app and `candidate-query-results` for the comparison app. Both retain
   the common allocation/query changes; only the first includes the three HiZ
   workarounds. Verify base revision, dependency revisions, patch checksums,
   modified/added source hashes, architecture and build configuration. Record
   the actual compiler/SDK, commands and resulting binary hashes.
4. **Separate compilation from gameplay acceptance.** Refactor the supported
   pinned-recipe build path so it does not require this machine's private
   control report, signed diagnostic app or capture files. Retain the distinct
   research workflow's acceptance checks for experimental variants. Successful
   compilation must not mark a renderer as gameplay verified or claim that a
   historical user test covered newly compiled bytes.
5. **Support validated local artifacts in packaging.** Keep the exact-hash path
   for the retained tested binaries. Define a separate source-build receipt
   bound to the selected source recipe, dependencies, toolchain, configuration,
   produced bytes and current verification results. Package locally built
   artifacts only through that validated path. Do not silently overwrite the
   historical accepted hashes, accept an arbitrary replacement library by
   regenerating metadata, or introduce a blanket skip-verification option.
6. **Run checks against the produced artifacts.** Verify dynamic dependencies,
   configuration, signatures and runtime inventory. Check that the regular
   binary includes all three helpers and the comparison binary includes none.
   Run applicable allocation/policy and query GPU probes against the exact new
   binaries. Keep probe logs/state in disposable setup directories rather than
   requiring a user's existing Application Support folder. Keep host gameplay
   acceptance separate and explicitly pending until tested.
7. **Make setup repeatable and recoverable.** Reuse only verified cache entries,
   support retry after interrupted downloads/builds, and stage replacements
   before promotion. Preserve working apps and existing inputs on failure.
   Never touch Wine prefixes, game libraries, saves or client/account state.
   Derive paths from the checkout rather than a username or the old archive.
8. **Document the supported sequence.** Once implemented and tested, update
   `BUILD-AND-RUN.md`, `BUILD.md` and `README.md` with the real setup command,
   prerequisites, both build options, cache cleanup and recovery instructions.
   Continue to distinguish running a complete app from building it from source.

## Acceptance checks

- Start from a clean checkout with no `vendor/`, `dist/`, build caches or
  access to the existing external archive. Fetch the required public inputs
  and produce both apps using only the documented commands.
- Run again with verified local inputs and confirm the documented offline
  rebuild path works. Exercise an interrupted setup and a corrupted cached
  input; verify safe retry or clear rejection without losing a working app.
- Confirm packaging validates new source-built bytes without treating them as
  the historical tested binaries. Reject wrong source/patch/dependency pins,
  changed artifact bytes, and mismatched comparison/helper profiles.
- Pass the repository checks, both app diagnostics, dependency/signature/runtime
  checks and the applicable native GPU probes. Record exact artifacts/results.
- Confirm setup/build does not create or alter an Application Support prefix
  or require Steam/Rockstar credentials or game files.
- Separately test first-run setup and gameplay on a new Mac when available.
  That validates the finished app's Wine/Steam/client workflow, beyond the
  fresh-clone build acceptance above.

Until this work is implemented, rebuild from the prepared workspace or copy
the retained `vendor/` inputs alongside a fresh clone. Running the finished app
does not require the repository, `vendor/` or developer tools.
