# RDR2 MoltenVK Control

Copy RDR2 MoltenVK Control.app from the ZIP to the Apple Silicon host and open it.
It contains the native launcher, Wine 11, the rebuilt MoltenVK control, DXMT and
the media runtime. No Highball, Python, Homebrew or developer tools are needed to
run this app. Apple-managed Rosetta is required if it is not already available.

This is a baseline comparison build. **A tree-rendering fix has not been verified.**
The proposed allocation patch is not included. The renderer is MoltenVK 1.4.2 with
the original three Highball patches, rebuilt from pinned source. Heaps and argument
buffers remain enabled; Metal private API remains disabled.

The app uses its own data folder by default:

```text
~/Library/Application Support/RDR2Launcher-MoltenVK-Control/
```

1. Open Steam using the app and sign in inside Windows Steam. Complete Rockstar
   sign-in/consent in its own windows when requested.
2. Use Choose game folder and Steam's Storage settings to select a persistent test
   library. Reuse the Red Dead Redemption 2 folder you already copied: with Steam
   closed, place it under that library's steamapps/common directory. Reopen Steam,
   select Install in the same library and let Steam discover/verify existing files.
   Some missing files or updates may download. The ZIP contains no game or account data.
3. Select Play and complete the normal Steam → Rockstar flow. Compare the same
   save, scene and graphics settings as the original renderer. Record whether it
   reaches Story Mode and whether trees disappear during a stationary camera pan.

Keep a separate backup of your saves before copying them to the test environment.
The default test environment starts fresh; it does not automatically reuse the
normal launcher's remembered prefix. Use test environment allows you to choose an
existing **copied launcher test environment**, containing prefixes/default and Steam.
It does not import Highball bottles directly. To return to the original renderer,
quit the test clients normally and open your original launcher/Highball environment.
The existing launcher app and Highball shared engine are not replaced.

This is an ad-hoc signed development build, not notarized. Host Finder/Gatekeeper
and game startup remain unverified. If macOS blocks it, report the exact dialog;
do not disable Gatekeeper or strip quarantine. Keep credentials inside the clients.

Technical evidence is bundled in Resources/moltenvk-control-build.json and
Resources/tree-control.json. The signed runtime manifest covers the replacement
renderer. The experiment's source and visual test procedure are in the project at
experiments/moltenvk-trees/README.md.
