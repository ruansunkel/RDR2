# Graphics checks with the existing installation — 2026-10-27

`scripts/build.sh --without-occlusion-fixes` builds
`dist/RDR2GraphicsCheck.app`. Open it and select Play to use the existing
`~/Library/Application Support/RDR2Launcher/` environment. This reuses its
Wine prefix, Steam/Rockstar installation, game files, saves and sign-ins.
There is no new prefix or game copy. The remembered environment selection is
also shared, so a deliberately selected alternative environment applies to
both apps.

Quit RDR2, exit Windows Steam/Rockstar and close the launcher before switching
between apps, so a new native Wine/client session loads the chosen renderer.
The existing prefix lock prevents two launcher windows using that prefix at
once, but it does not replace an already running client's renderer.

The comparison packages the previously built `candidate-query-results` driver:

`9c0161edaff3b40615a4ae69ac5c71bc3e07389705e2a2291bc3f40c3eb24701`

It includes the same pinned MoltenVK 1.4.2 base, Highball patches, dedicated-buffer
allocation option and query correctness backport as the accepted main renderer.
The three captured tree, packed-foliage and rigid-object HiZ helper hooks and
headers were never included in this driver. The build verifies their switch
strings are absent. Heaps and Metal argument buffers remain enabled; Metal
private API remains disabled. This flag is not a general switch for all driver
changes and does not promise coverage of other grass shaders.

The original source pins and current selected-variant pins match; the archived
source tree was reverified against the current pinned patches and source hashes
before retaining this artifact in `vendor/renderer/without-occlusion/`. Its
original build metadata predates the later tree/foliage/rock variants. Comparison
validation requires every common pin and the complete selected variant, while
ignoring unrelated variant records. The regular accepted renderer retains its
full pins-equality check.

The regular `scripts/build.sh` command continues to build
`dist/RDR2Launcher.app` with all three accepted workarounds and renderer hash
`b914dc101ebcc70a415caabc69a2587efcb6770ee0ca27d7db2285935038fdce`.
The comparison has its own bundle identifier and window title. Its default
output preserves the regular app; `--output` can explicitly choose another
destination. The app diagnostic and signed resource metadata record the chosen
profile. Runtime policy still enables the allocation option and writes markers
under the permanent data folder.

Validation passed 20 Python tests and 17 Swift core checks. Both build profiles
were packaged and checked for runtime integrity, deep/strict signing, expected
renderer hashes, helper presence/absence and the same permanent default data
folder. The included-fixes profile was built in a temporary directory and
removed after verification, preserving the existing working main app.
The comparison passed native GPU buffer/image allocation and nonzero-query
regression probes; the expected policy/allocation/query events were recorded
under the permanent data directory without environment overrides. Only the
existing `RDR2Launcher` data directory remained after these checks. No Steam,
Rockstar or RDR2 session was started; gameplay with this comparison build is
for the user's graphics checks.
