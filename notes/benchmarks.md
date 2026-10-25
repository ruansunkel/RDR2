# Gameplay evidence

No game has run locally. The user confirmed Windows Steam sign-in and an active
RDR2 download. Rockstar sign-in, main menu, controllable Story Mode and FPS remain
**unverified**. Patched MoltenVK initializes in Wine utilities; game renderer use is unverified.
Upstream reports are references only and are not measurements on this machine.

| Date / machine | Engine / renderer | Scene / controls | Resolution / preset / FSR | FPS / frame pacing / memory | Result |
| --- | --- | --- | --- | --- | --- |
| 2026-10-25 / 8 GB Apple VM | None installed | Not run | Not run | Not measured | Blocked: no Rosetta, insufficient RAM for baseline, no physical-host access |

For the first actual test use 1280×720 windowed Safe/Low with Vulkan. Record
interactive control in Story Mode, elapsed time, exact engine and loaded graphics
libraries. Measure the same scene before changing one setting. Back up any
existing system.xml before changing its actual observed XML structure.

Build/host scope clarified: the build VM prepares and launches the runtime; gameplay/playability testing on the separate host follows transfer. No FPS was measured.
