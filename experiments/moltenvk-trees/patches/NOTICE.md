# Patch and source attribution

MoltenVK v1.4.2: Copyright The Brenwill Workshop Ltd. and contributors;
Apache-2.0, see LICENSE-MoltenVK.txt and the upstream source headers.

The three moltenvk-shadow-import, moltenvk-linear-fallback and
moltenvk-shadow-readback patch files are preserved byte-for-byte from Highball
at cabadb4cfaaad0ece66f7fad2206fdd7a0b41ffb. Their historical equality to the
r27-introduction revision 516da2758e699123ceee83b9a116bd28ceaaadf2 is recorded
in pins.json. Highball's license text is preserved in LICENSE-Highball.txt.
Source: https://github.com/gauthierpiarrette/highball

The proposed dedicated-buffer-no-heap patch was written for this investigation,
against that patched MoltenVK source. Its added code is provided under Apache-2.0.
It has been built and GPU-tested, but RDR2 did not exercise its eligible
dedicated-buffer path and it did not fix the observed trees.

The captured-tree HiZ bypass and query diagnostics were written for this
investigation; their added code is provided under Apache-2.0. The captured-tree
workaround is user-confirmed in the tested Story Mode scene. Disappearing rocks
and some foliage remain unresolved. The whole-memory-buffer alternative remains
an unbuilt experiment. See HOST-CANDIDATE.md and WORKING-STATE.md for evidence.

The captured-foliage HiZ bypass was also written for this investigation; its
added code is provided under Apache-2.0. It targets one additional complete-source
SHA256-matched shader, identified from the remaining foliage camera pair. Native
synthetic-depth controls pass; in-game visual acceptance and rock coverage remain
pending. Captured game shaders and assets are private evidence and are not
included in these patches or the app bundle.

The captured-rock HiZ bypass is likewise original diagnostic code under
Apache-2.0. It targets one additional complete-source SHA256-matched rigid-object
shader isolated from a disappearing-boulder camera pair. Captured-input GPU
controls restore the selected instance; in-game visual acceptance is pending.
The original depth texture and heap root cause remain unreproduced. Captured
game shaders/assets remain private evidence and are not bundled.

The query-result range/availability backport derives from upstream MoltenVK
commit 701747d61a0484e91c205e081a24ca592ffa12b4, PR2794, under Apache-2.0:
https://github.com/KhronosGroup/MoltenVK/pull/2794

The MoltenVK-RDR2 fork was inspected for comparison, not copied wholesale into
this build. Its global heap disable, argument-buffer default change and blanket
image-configuration-result clearing are not included in the control or candidate.
Source: https://github.com/whitebelyash/MoltenVK-RDR2

Build-only tools/dependencies are not bundled into the runtime library as separate
executables. Source/tool versions and exact dependency commits are recorded in
pins.json/build.json. The static SPIRV-Cross/SPIRV-Tools components are Apache-2.0;
cereal headers are BSD-3-Clause. Preserve their upstream notices/corresponding
source as appropriate before any public redistribution. This is a private
development/control artifact; public distribution review is incomplete.
