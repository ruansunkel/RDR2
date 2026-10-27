# Permanent main-app data directory — 2026-10-27

The main app now uses `~/Library/Application Support/RDR2Launcher/`. The tested
prefix and its game copy were migrated from the candidate directory; the older
prefix already at the permanent name was archived. The user then confirmed:
**"I can confirm that the game works now."** After that launch, an audit found
no live symlinks, operational settings or open files depending on the old
candidate/control names. Both unused control folders were moved into the
external archive, and the temporary candidate compatibility symlink was removed.
Only `RDR2Launcher` remains in Application Support. Saves and sign-ins are retained, and
`~/Games/RDR2/` remains untouched. The main edition is now `patched`, with the
same accepted renderer bytes and allocation settings. See
[migration and recovery](notes/data-folder-migration-2026-10-27.md).

---

# Main app rebuilt with all accepted fixes — 2026-10-27

Use `scripts/build.sh` to rebuild `dist/RDR2Launcher.app`, then
`scripts/launch-rdr2.sh` to open it. The main app now includes the exact accepted
tree/foliage/rock renderer, SHA256
`b914dc101ebcc70a415caabc69a2587efcb6770ee0ca27d7db2285935038fdce`,
with the earlier allocation/query changes. It retains the current candidate
environment, saves and client sign-ins. Signature, runtime integrity and
environment selection checks pass. This rebuild changes packaging and launcher
branding; renderer bytes remain the same as the user-tested rock build.

Old private game data, GPU evidence, research inputs and earlier apps were
archived outside the project with approval. The two local inputs needed for
offline main-app rebuilds remain in `vendor/`; regenerable caches were removed.
See [cleanup and recovery](notes/workspace-cleanup-2026-10-27.md).

The entries below are chronological investigation checkpoints. Their app and
evidence paths refer to the original locations, now recorded in the archive.

---

# Tree, foliage and rock examples have confirmed workarounds — 2026-10-27

After the same-scene camera-turn comparison, the user confirmed the selected
boulder: **"It is visible now"**. The current working app is
`dist/rock-occlusion/RDR2 Rocks Occlusion Diagnostic.app`. It includes the
previously confirmed tree and foliage workarounds plus the captured rock shader.
The running game and signed bundle are left untouched.

The selected boulder's mesh and all three vertex streams are byte-identical in
the visible/missing pair. Its main draw changes from instance73 to zero
instances, while its shadow draw still has one. The exact culling producer is
identified. Native captured-input controls restore73 when HiZ rejection is
disabled; all six rock helper cases and source/disable guards pass.

The separately built `candidate-rock-occlusion` preserves both user-confirmed
tree and foliage shader workarounds and adds this third complete-source SHA256
guard. Driver SHA256:
`b914dc101ebcc70a415caabc69a2587efcb6770ee0ca27d7db2285935038fdce`.
All seven exact-driver allocation checks and the query regression pass, along
with all 18 Python checks. The separate app passes deep/strict signature and
runtime-integrity checks. RDR2's exact driver mapping and all three native bypass
activation events were verified before the user's positive rock result. The
accepted object and tree apps are preserved.
No large replay remains open. See [current evidence](notes/evidence/remaining-objects.md).

This confirms targeted workarounds in the tested scenes. Original numeric depth
and the underlying heap cause remain unreproduced; broad-scene coverage,
performance and extended stability remain unmeasured. Acceptance is recorded
outside the signed bundle in private `rock-occlusion-user-acceptance.json`.

---

# Foliage workaround confirmed in the tested scene — 2026-10-27

The user requested continuation. A controlled visible/missing pair of foliage
above Arthur's head has been captured and its exact packed-foliage culling
dispatch identified. The matched mesh drops from 12 instances to 7. With the
missing frame's small inputs, disabling HiZ restores five previously visible
instances that pass all remaining checks.

The separately signed `dist/object-occlusion/RDR2 Objects Occlusion Diagnostic.app`
retains the working tree workaround and adds only this additional complete-source
SHA256-matched shader. Six native foliage controls, scope/disable guards, all
seven exact-driver allocation checks and the query regression pass. Its driver
SHA256 is `e0e54e0efb62103a0bdb3d712ea366215d2ccf60a44a8e4da987aaa53e674668`.
RDR2 has loaded that exact driver and native events confirm the captured-foliage
bypass is applied. After returning to the same scene and repeating the camera
turn, the user confirmed **"Stays visible"**. This establishes the foliage
workaround in that scene. Rock status was not answered; other locations,
performance and extended stability remain unmeasured. The original tree app is
preserved, and the running game is left untouched.

The user now confirms only rocks remain and has an example. The current game
was launched without capture enabled, so a same-build capture restart is needed.
The user identified the rock behind Arthur’s face, saved and closed the game.
The same build was relaunched capture-enabled after eight verified save backups.
The exact new-game renderer mapping and capture registration are verified; the
visible-rock pose is pending. No rock capture has been recorded yet.

A new native GPU test compares the captured HiZ texture dimensions and heap
placements against standalone allocation. All three modes pass, with 884,304
numeric values checked per mode. This synthetic test does not reproduce the
game's original depth, resource reuse or synchronization and does not rule out
heap faults. A closed-session relaunch issue was also corrected and covered by
four tests. A further selected-runtime environment check covers capture-enabled
switches to a new candidate; all 18 Python checks pass. Original numeric depth and a heap root
cause remain unreproduced; rock coverage is unverified. See
[current evidence](notes/evidence/remaining-objects.md).

---

# Paused checkpoint — rocks and foliage remain — 2026-10-26

The user asked to park the investigation. The selected-tree workaround is
confirmed, but **rocks and some foliage still disappear**. This is a partial
result; those remaining objects have not yet been isolated or captured.

Resume from [the rendering checkpoint](notes/checkpoints/2026-10-26-rendering.md).
It records the working app and hashes, saved evidence, failed comparisons,
remaining uncertainties and next investigation steps. No further game/process,
renderer or settings changes were made while creating the checkpoint.

---

# Tree workaround confirmed in the tested Story Mode scene — 2026-10-26

The user confirmed Story Mode readiness, then reported **"it works"** with
`dist/tree-occlusion/RDR2 Trees Occlusion Diagnostic.app`. The exact mapped
driver and native shader-bypass activation were independently verified. This
is a user-confirmed workaround in the tested scene; performance, other locations
and extended stability remain unmeasured. The running game is left untouched.

The earlier controlled pair showed the same tree visible and then absent after a camera turn.
Both one-frame GPU captures and final scene images are saved. The exact tree
mesh is unchanged, but its compacted instance list drops from `[2, 3]` to `[2]`.
The compute dispatch that produces that list has been identified, and its camera,
object, transform and culling inputs were extracted with the game closed.

An isolated Metal test with those inputs retains the tree when HiZ occlusion is
disabled. Synthetic depth controls can reproduce the rejection; the original
numeric depth texture has **not** been reproduced, so this is not proof of the
underlying driver fault. Fast and precise math controls give the same outcome.

A separate diagnostic driver bypasses only the HiZ check in the complete,
SHA256-matched captured shader. It preserves frustum, distance and LOD checks;
unmatched or modified shaders remain untouched. All six synthetic GPU cases
retain the tree with this workaround. Negative guard controls and the new
driver's seven allocation/policy checks plus query regression pass. RDR2 has loaded the exact driver, and native per-process events confirm the
SHA256-matched shader bypass is applied. The user has now confirmed the same-scene result. This may draw extra objects
and affect performance.
The original/control/query-results apps and local game/save copy are preserved.
See [working evidence](experiments/moltenvk-trees/WORKING-STATE.md).

---

# Initial game capture recorded; camera comparison pending — 2026-10-26

The actual game produced a valid two-frame GPU trace (10.1GB). Its final images
were replayed and exported successfully after the game closed. Both show
essentially the same Colter camera angle, so this capture does not demonstrate
the disappearance/reappearance transition. No tree cause or fix is established.

The user agreed to a controlled pair with Arthur stationary: capture one chosen
tree visible, then the same tree absent after turning the camera. The same
renderer has been relaunched with capture enabled; readiness for the visible
state is pending. No new rendering patch was added. A confirmed leftover
PlayRDR2 bootstrap that resisted normal shutdown was terminated by exact PID
after verifying the game was closed and backing up eight save files.

---

# Direct GPU capture route verified — 2026-10-26

The user authorized direct rendering diagnosis and confirmed the game was closed.
Apple's CLI captured and replayed an independent x86-64 Vulkan workload under
Rosetta on this M1 Max. Command-tree buffer fetches returned the expected GPU-copy
contents. No full Xcode installation was needed.

The same query-results renderer was relaunched with `MTL_CAPTURE_ENABLED=1`
after normal scoped client shutdown and verified save backups. RDR2 PID17289
is registered as capturable, maps the exact unchanged driver, and exposes one
WineMetalLayer frame boundary. The user has been asked to position Story Mode
near the affected trees. An actual tree-scene capture and root cause remain
pending. This is diagnostic preparation, not a rendering fix.

---

# Query-result candidate unsuccessful; tree cause still unknown — 2026-10-26

A separate candidate backports upstream [MoltenVK PR2794](https://github.com/KhronosGroup/MoltenVK/pull/2794).
A real-M1 GPU regression reproduces the baseline error and passes with the patch:
completed nonzero-slot queries now copy the correct result and availability for
both 32-bit and 64-bit outputs. All seven buffer/image/policy checks also pass.
The signed app is `dist/tree-query-results/RDR2 Trees Query Results.app`, using
the same candidate game/save copy. RDR2 maps the exact new driver, and native
query-range activation is observed. The user confirmed that trees still disappear.
The later native events show occlusion query use, but no nonzero-first-query or
availability-offset/difference events. The specific faulty GPU-copy case has not
been demonstrated in this game. GPU regression success is not progress toward a
verified tree fix. Further visual comparison builds are deferred while gathering
evidence of the actual failing rendering path. The current game is left alone.
See [host evidence](experiments/moltenvk-trees/HOST-CANDIDATE.md).

---

# Argument-buffer-off comparison unsuccessful — 2026-10-26

Revision 3 still flickers, as confirmed by the user. Its native policy is on, but
RDR2 has reported only shared allocations and dedicated images, not the dedicated
buffers targeted by that patch. A separate argument-buffer-off comparison ran
with heaps still enabled. Real-GPU checks passed, and its exact driver
mapping plus native `argument-buffers-off` event are verified in RDR2. The user
closed the prior game before a normal, scoped test-client shutdown. No game
redownload or settings reset was needed. The user confirmed that trees still
disappear or change shape and then closed the game intentionally. No fix is
verified. Investigation now includes upstream query-result correctness fixes.

---

# First tree candidate unsuccessful; activation diagnostics prepared — 2026-10-26

The user reports that candidate 1 still shows disappearing/changing trees and
subsequently exited by itself (Rockstar exit code 1). A failed debugger attach is
a confounder; the exit's cause is unproven. No eligible-allocation event appeared.
A separate revision with signed per-library policy fallback and native allocation
diagnostics is built to distinguish configuration loss from an unused narrow
allocation path. Its GPU checks pass, including Wine-style symlink loading; a new
in-game comparison is pending. No tree fix is claimed. See
[candidate evidence](experiments/moltenvk-trees/HOST-CANDIDATE.md) and
[working checkpoint](experiments/moltenvk-trees/WORKING-STATE.md).

---

# Host tree-rendering candidate launched — 2026-10-26

The user confirmed the rebuilt Control still shows disappearing trees and
authorized a local candidate build. Local pinned CMake and the existing CLT built
the candidate; full Xcode was unnecessary. Real-GPU allocation checks passed for
control, candidate-off and candidate-on. A separate candidate app/data folder was
prepared using local game/save copies, and RDR2 was verified mapping the exact
patched driver. Its in-game allocation marker and same-scene visual result remain
pending; no fix is claimed. See
[host candidate evidence](experiments/moltenvk-trees/HOST-CANDIDATE.md).

---

# Tree flicker under investigation — 2026-10-26

The user reports nearby and distant trees disappearing/reappearing and changing
shape on Ultra, persisting after the suggested Tree Quality High comparison.
Similar tree flicker remains unresolved in the upstream reports reviewed;
reviewed Highball r28/r29 manifests use the same MoltenVK component as this r27
build. No graphics settings or runtime binaries were changed during this
investigation; no fix is claimed. See
[tree-flicker evidence](notes/evidence/tree-flicker.md).

---

# Physical-host Story Mode confirmed — 2026-10-25

**The user confirmed: "Story Mode is playable and controls work."** The transfer
app has now reached interactive gameplay on the physical M1 Max with a fresh host
environment and reused game files.

- The copied transfer app passed deep/strict signature and runtime-integrity
  checks on the physical M1 Max (32 GB RAM, 32-core GPU), macOS 27.0.1 (26A434).
  Rosetta is available. No runtime rebuild or new system tools were required.
- Used the fresh host environment under Application Support, preserving the
  copied build-Mac prefix. Retrying bootstrap outside the agent sandbox completed
  the South Africa timezone correction and official Windows Steam setup/update.
  The user confirmed Steam is signed in and displaying the library.
- Cloned only the downloaded game to `~/Games/RDR2/steamapps/common/Red Dead
  Redemption 2`; all 123 paths and sizes match the original. Mapped this host
  library to `R:` and remembered the host environment in the transfer launcher.
- Steam library registration is verified at `Z:\Users\ruansunkel\Games\RDR2`;
  Steam recognized the installed game and launched through Rockstar. The user
  confirmed successful Rockstar sign-in on the physical host.
- The first host launch stalled near the end of its initial loading bar. After
  sampling the stalled process, stopped only that game and retried through Steam
  with a new host-game `commandline.txt` containing `-ignorepipelinecache`.
  The user then confirmed playable Story Mode with working controls. The
  successful retry does not isolate whether the restart, warmed caches or the
  option changed the outcome.
- FPS, extended-session stability and repeat cold-start reliability remain
  unmeasured. The user subsequently exited the game intentionally. See
  HOST-TEST.md for host evidence, including the launcher's exit diagnostic.
- The newly written host graphics settings confirm Vulkan, 1280×720 windowed,
  with VSync enabled; these settings were not edited during the retry.
- Removed five confirmed disconnected processes left from before the retry,
  verifying each process before termination. The current game was preserved
  during cleanup; its later exit was user initiated. The final process list has
  one current Steam client with its normal Wine/browser/service helpers and no
  duplicate Rockstar launcher. No client state or game files were reset.

---

# Latest verified recovery — 2026-10-25

- The completed RDR2 installation was recovered in its original native-steam
  environment. The user confirmed that Steam shows the installed game again.
- Rockstar's registered background service remains RUNNING with Steam open; its
  log confirms the service handshake. The user reached the sign-in page.
- Sign-in failed with #1.000.7 while browser sign-in on the same Mac worked. Wine
  reported Kaliningrad for the host's Africa/Johannesburg timezone. Verified,
  backed-up moves of only the three conflicting timezone definitions made Wine
  report South Africa Standard Time. After a Rockstar-only restart through Steam,
  **the user confirmed Rockstar sign-in works**. A later process-name query found Steam without RDR2/Rockstar, and the
  launcher recorded RDR2 exiting with code 0x3 after about 51 seconds. A single
  retry through Steam was requested after verifying the installed service RUNNING.
  Wine's subsequent process list shows Launcher.exe, RockstarService.exe and
  PlayRDR2.exe running; RDR2.exe was not yet listed. The user saw a sign-in/consent
  prompt on retry and subsequently confirmed loading continued before the window
  closed by itself. Startup on this VM remains unsuccessful.
  No main menu, gameplay or FPS claim is made; the exit's cause is unresolved.
- No game files, sign-in data or macOS settings were reset. Backup journal:
  vendor/probes/native-steam/state/timezone-repair-20261025T151114Z/recovery.json.
- The updated native app remembers the existing environment, reveals game files,
  checks/starts the installed Rockstar service and includes the validated,
  host-specific timezone correction with verification and rollback.
- Source validation: 8 Python tests + 16 Swift checks pass, including environment
  recovery, command-output lifetime, timezone applicability, verified backups and
  rollback after partial failure and recovery after an interrupted move. Final updated artifact is dist/transfer/RDR2Launcher.app.
- The updated bundle passed ad-hoc signature/runtime verification and relocation
  integrity at a path with spaces. Its archive passed SHA-256, per-entry CRC and
  private client/game/account path exclusion checks. Recovery evidence is appended
  to dist/TEST-REPORT.md. Full dynamic Wine/media smoke evidence from the unchanged
  runtime remains recorded in notes/evidence/runtime-validation.md.
- The active Steam/Rockstar/game environment is preserved; older bundles are not
  replaced while its processes are using them. Developer ID/notarization, full
  public redistribution review, separate-host validation and gameplay remain open.
- Next useful validation is the physical host with its native GPU and actual RAM
  budget. This is a change of test environment, not proof that memory or the VM GPU
  caused exit 0x3. See HOST-TEST.md for the archive, game-file reuse and observations
  needed. No new game launches or configuration changes were made for this handoff.

The earlier progress history below is historical and retained for diagnosis.

---

# Current recovery update — 2026-10-25

The user completed the RDR2 download. The files remain at
`vendor/probes/native-steam/prefixes/default/drive_c/Program Files (x86)/Steam/steamapps/common/Red Dead Redemption 2`.
RDR2.exe is present (89,562,608 bytes). No game data was moved, deleted or downloaded
again. Reopening the old GUI had selected the different default Application Support
prefix, which is why Steam appeared to lose the game.

The corrected GUI now remembers a selected existing environment outside the app,
accepts an explicit data directory, shows that data folder and provides Show game
files. A missing remembered folder cannot silently produce a new empty Steam prefix.
The selection was saved for this user to the existing native-steam environment with
its original private HOME. The user confirmed that RDR2 is restored in Steam.

Rockstar's service is installed in that same prefix. Its logs showed an initial
service setup/start failure. Starting the installed service with Steam open produced
and retained STATE 4 RUNNING; subsequent Rockstar logs confirmed a service handshake.
The updated Play route performs that non-destructive service check/start before
launching through Steam. The user then saw the sign-in page; keyboard interaction
became sufficient to submit sign-in, which returned #1.000.7. Game startup and
controllable gameplay remain unverified.

Clock checks: UTC clock agrees with the tool clock. macOS timezone is
Africa/Johannesburg, but Wine names its UTC+2 zone Kaliningrad Standard Time.
A process-local TZ/TZDIR probe did not fix the name. Registry/system files were
backed up before probes; no timezone definitions, authentication state or macOS
settings were changed. Browser sign-in comparison is pending. The user's supplied
correlation identifier is not copied into diagnostic reports.

Validation for this change: 8 Python packaging tests and 11 Swift checks pass,
including remembered-environment persistence, missing-path fail-safe behavior,
preserved game files when switching, selection backups and actual service-state
parsing. The corrected development app is dist/recovered/RDR2Launcher.app. Public
redistribution, Developer ID/notarization and clean-host/gameplay gates remain open.

Preserve vendor/probes/native-steam: it now contains the downloaded game and private
client state. Do not treat it as disposable build cache. The earlier build history
below is retained; its downloading/old-artifact statements are historical.

---

# Status — 2026-10-25

**Current milestone: runtime-inclusive development app; real Windows Steam installed
and updated through the native launcher. The user has signed in and reports RDR2
actively downloading on the build Mac. Gameplay and clean-host validation remain open.**

The user clarified that this is the build Mac, the host is unavailable, and the
immediate objective is a launchable bundle for transfer; host playability follows.
The build workflow therefore proceeds without requiring gameplay on this 8 GB VM.
No simulated download or fixture is counted as a real Steam/game success.

## Environment

macOS 27.0.1 (26A434), arm64, Apple M1 Max Virtual, 8 GB RAM; initially approximately
217 GiB free after source builds. Existing Apple CLT / Swift 6.4. On this turn,
Rosetta's x86_64 execution check **passed** and native Steam was already present.
Those are changes since the earlier preflight; this agent did not install either.
No Homebrew, global Wine or Highball app/data was found. Native Steam is untouched.
The separate physical M1 Max host's OS, RAM, disk and security behavior are unknown.

## Executed

- Downloaded and SHA-256 verified all six pinned Highball r27 runtime archives.
  Wine reports `wine-11.0`; patched MoltenVK's linear-fallback markers are present.
- Ran actual Wine prefix initialization and `cmd /c ver` with a system-only PATH
  and a private HOME/prefix. Wine reports Windows 10.0.19045; MoltenVK initializes
  on the Apple Paravirtual GPU. Initial sandbox socket denial was resolved with
  an approved unsandboxed execution of the same isolated test, without sudo.
- Audited the real upstream runtime: found 21 issues, including absolute build
  paths, a broken Apple graphics alias, missing FFmpeg ABI versions and stale media.
- Prepared the official GStreamer 1.28.7 playback dependency closure; built only
  FFmpeg 9.0.2's x86_64 demuxing libraries from verified source, without GPL flags
  or external codec packages. Added verified Intel GLib/PCRE2/libintl libraries.
- Corrected load commands/IDs and recorded original/relocated hashes and operations
  in `runtime/relocation-changes.json`. Uses short relative library aliases to
  respect existing Mach-O header space. No ABI compatibility version is falsified.
- Removed unused Template renderer overlays, wrapper SDK and alternate MoltenVK.
  No Apple D3DMetal or client/game/account files are bundled. The initial full app
  passes a static audit of **153 Mach-O files** with no unresolved outside references.
- A dynamic GStreamer probe caught `_libintl_newlocale` missing from the old runtime.
  Replacing libintl with the matching pinned gettext bottle fixes it; actual
  `gst-inspect-1.0 --version` reports GStreamer 1.28.7 successfully.
- The bundled native app initialized its own test prefix, downloaded the official
  Valve installer, installed Windows Steam and started its real self-update.
  Steam's updater reported completion; steam.exe and five steamwebhelper.exe
  processes were observed. The user subsequently confirmed sign-in and RDR2 downloading.
- Preserved 157 vendor notice/provenance files. Complete mixed-runtime notices and
  corresponding-source review remain required before public distribution.

## Data and artifacts

The **active build-Mac Steam session** uses:

`vendor/probes/native-steam/prefixes/default/`

Its launcher is the existing `dist/RDR2Launcher.app`. Keep that Steam window and
prefix for the current download and subsequent Play. Do not start a different
prefix and assume it contains this installation. No authentication files are read,
exported or copied into the transferable app. Only app-defined status events,
public installer provenance and nonsecret updater/process summaries were inspected.

The final transferable development artifact is built separately to avoid replacing
files used by the active Steam session:

- `dist/host-test/RDR2Launcher.app`
- `dist/RDR2Launcher-development.zip`
- `dist/SHA256SUMS`, `SBOM.md`, `BUILD.md`, `TEST-REPORT.md`, `dependency-audit.json`

Final copied-bundle/media smoke outcomes are recorded in
`notes/evidence/runtime-validation.md`: runtime hashes, relocated Wine initialization,
Windows cmd, media registration, GStreamer/libav discovery and dynamic library loads
all passed. Eight Python tests and six Swift checks passed. These are ad-hoc development artifacts;
there is no Developer ID identity, notarization or Gatekeeper distribution claim.
Build products and all client/game/account state remain ignored by Git.

## Remaining acceptance

| Check | State |
| --- | --- |
| Native app, pinned engine, patched MoltenVK, DXMT bundled | Passed build and copied-bundle checks on build Mac |
| Static outside-dependency/symlink audit | Final complete bundle passed, 153 Mach-O files |
| Real Wine prefix and Windows utilities | Passed on build Mac |
| Official Windows Steam bootstrap/update | Passed on build Mac |
| Steam sign-in and RDR2 download | User confirmed; download still in progress |
| RDR2 installed/verified | Not yet confirmed by Steam/user |
| Rockstar sign-in / entitlement launch | Not yet verified |
| Story Mode, controls and FPS | Not measured; no gameplay claim |
| Copied bundle on separate host / Finder / normal Gatekeeper | Host unavailable; not tested |
| Developer ID / notarization | No valid signing identity found; unresolved |
| Full redistribution/source compliance | Review remains incomplete; release gate closed |

The next game step is to let the existing download finish, use Steam's Play in
that same prefix, complete Rockstar setup/sign-in/EULAs in its windows, and observe
launch. The native launcher's Play uses Steam `-applaunch 1174180`; install and
repair use Steam URIs. File/manifest presence never proves ownership or readiness.

User data on the host persists under `~/Library/Application Support/RDR2Launcher/`
and an optional selected external library. Replacing/removing the app preserves
those files. No reset/uninstall or unrelated-prefix mutation was performed. Build
smoke tests stop only their own newly created disposable wineservers. The active
Steam/RDR2 download is left running.
