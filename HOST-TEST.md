# Physical-host test

The 8 GB build VM completed the real Steam download and reached successful Rockstar
sign-in. The game subsequently loaded and closed without reaching a verified menu.
The first attempt recorded exit 0x3; the cause is unresolved. Testing the physical
M1 Max will establish whether the same build starts with its native GPU and actual
memory budget. It does not establish the cause of the VM failure by itself.

## Transfer

Copy `dist/RDR2Launcher-development.zip` and `dist/SHA256SUMS` to the host. Extract
the archive and open RDR2Launcher.app. The archive contains the launcher and bundled
runtime, with no game files or account state. The matching archive's SHA-256 is
recorded in SHA256SUMS alongside it.

This is an ad-hoc signed development build, not a notarized release. Normal Finder /
Gatekeeper acceptance on the host remains untested. If macOS blocks opening it,
record the exact dialog; do not disable Gatekeeper or strip quarantine. Rosetta is
an Apple-managed prerequisite if absent. No Homebrew, Wine, Highball or developer
tools should be installed on the host for this test.

## Reuse the completed game download

1. In the host launcher, choose a persistent game folder and open/install Windows
   Steam. Sign in inside Steam. Add the mapped R: folder as a library using Steam's
   Storage settings, and note the actual library directory Steam creates.
2. Copy the completed **Red Dead Redemption 2** game folder from the build Mac to
   the host. The source can be opened using **Show game files** in the build launcher;
   its project-relative path is:

   ```text
   vendor/probes/native-steam/prefixes/default/drive_c/Program Files (x86)/Steam/steamapps/common/Red Dead Redemption 2
   ```

3. With Windows Steam closed normally on the host, place that copied folder at
   `<host Steam library>/steamapps/common/Red Dead Redemption 2`. Preserve the build
   Mac's original files. Transfer the game folder separately from the app; create
   a fresh host environment and sign in there rather than copying the build prefix
   and its private client state.
4. Reopen Windows Steam and select Install for RDR2 in that same library. Steam can
   recognize existing files during installation; let it verify and fetch any missing
   files or updates. Then use Properties → Installed Files → Verify integrity if
   needed. Steam remains authoritative for ownership and completion.

This follows Valve's guidance on [recognizing existing game files](https://help.steampowered.com/en/faqs/view/4578-18A7-C819-8620)
and [verifying installed files](https://help.steampowered.com/en/faqs/view/21F5-8D5D-0141-7A5E).

## Launch and report

Use **Play** through Steam → Rockstar. Complete sign-in, consent and verification
prompts in the official windows. If the menu appears, start with Vulkan, 1280×720
windowed and the lowest available preset. Verify that Story Mode accepts controls.
Leave the current graphics backend in place for the first comparison.

Record the host's macOS version, RAM, M1 Max GPU configuration, whether it reaches
the menu/Story Mode, and any exact error or window closure. FPS is only useful after
interactive gameplay starts. Do not include credentials or account identifiers.
The app's **View logs** opens its application event log; vendor logs may contain
private data and should not be shared wholesale.

The host creates fresh data under `~/Library/Application Support/RDR2Launcher/`.
Replacing/removing the app preserves that data and the chosen game library.
