# Game Mode integration and launcher icon — 2026-10-28

The launcher now packages a game-enabled Intel Wine bundle and a western-style
app icon. macOS has recognized the packaged Wine processes as games on the M1
Max. RDR2's actual full-screen Game Mode activation and performance are still
pending an in-game check.

The updated app is `dist/RDR2Launcher.app`. The previous working app is retained
at `dist/pre-game-mode/RDR2Launcher.app`. Both use the permanent data directory;
quit the game and its clients before switching apps.

## Implementation

`packaging/game_mode.py` places the private runtime inside
`runtime/RDR2WineGame.app/Contents/Resources/`. Its actual executable is the
existing Wine 11 child loader, with the original address-space reservations and
code. The helper declares `LSApplicationCategoryType = public.app-category.games`
and `LSSupportsGameMode = true`. It is signed as a bundle. No custom Wine fork or
renderer rebuild is involved.

Wine's ntdll derives child launches from its adjacent `wine` path. That path now
links to the helper's real `Contents/MacOS/wine` executable. Its adjacent
`ntdll.so` link stays inside the signed helper. Relative aliases preserve the
existing `runtime/engine`, `frameworks`, `renderers` and license paths. The runtime
manifest selects the helper directly and inventories the nested files and links.
The helper is signed again after the accepted renderer and policy are installed,
before the final runtime inventory and outer app signature.

The launcher registers the helper with Launch Services after relocation. Its
**Game Mode…** button offers optional automatic full screen. Enabling it asks
macOS for Accessibility access; manual full screen does not need that permission.
Automation checks the focused process's real executable against this app's helper,
checks the first Windows executable argument is exactly `RDR2.exe`, and checks the
window title. It requests native full screen once per game process. It does not
repeat the request if the player exits full screen. The launcher must stay open
for automation; macOS manages Game Mode independently afterward. Only command
arguments are inspected, not process environments.

Game Mode remains controlled by macOS and the player's saved Game Mode preference.
The launcher does not report that Game Mode is active just because it requested
full screen. Use **Command–Esc → Settings → Game Mode** while playing to confirm.

The generated icon is in [the artwork directory](../assets/launcher/README.md),
including its master PNG, complete `.icns`, regeneration command and exact prompt.
It appears in the launcher header and is declared for both app bundles.

## Validation

- 25 Python tests and 18 Swift core checks pass, including runtime relocation,
  helper identity, manifest containment and excluding Steam/Rockstar from
  full-screen automation.
- The packaged app and nested helper pass deep/strict signature verification,
  dependency audit and runtime-integrity diagnostics. The accepted MoltenVK
  renderer remains SHA256
  `b914dc101ebcc70a415caabc69a2587efcb6770ee0ca27d7db2285935038fdce`.
- A copy under a path containing spaces passed the 153-Mach-O dependency audit
  with no failures and passed runtime-integrity diagnostics. Local relocated
  evidence is retained at `$TMPDIR/rdr2-relocation.OivFvX`.
- A disposable prefix at `.cache/game-mode-smoke-20261028` passed Wine version,
  initialization, `cmd /c ver`, Wine GStreamer registration, GStreamer libav
  discovery and dynamic FFmpeg/GStreamer loading. Only that prefix's Wine server
  was stopped at the end.
- During that test, the host's Game Mode service logged multiple Wine processes
  with `labelReason=LSSupportsGameMode (Info.plist)`. Local evidence is retained
  in `.cache/game-mode-classification-20261028.txt`. This confirms game
  classification, not full-screen activation or an FPS improvement.
- A separate `cmd → start → Notepad` child-process check in the disposable prefix
  confirmed that the GUI process resolves to the helper executable and its Windows
  executable is identified correctly. Notepad and Explorer were excluded from
  RDR2 automation. Evidence: `.cache/game-mode-native-identity-20261028.txt`.
  The native probe had no Accessibility grant, so it did not test window changes.

Pending: launch RDR2 through Steam/Rockstar, confirm full-screen entry and Game
Mode activation, check leaving full screen and quitting, and repeat the launch.
Automatic full-screen behavior needs a host check after granting Accessibility.
Compare the same scene/settings with Game Mode on and off before making a
performance claim.

## References

- [Apple Game Mode requirements and controls](https://support.apple.com/en-us/105118).
- [Apple's Game Mode metadata](https://developer.apple.com/documentation/bundleresources/information-property-list/lssupportsgamemode).
- [Wine 11 loader path lookup](https://github.com/wine-mirror/wine/blob/wine-11.0/loader/main.c)
  and [ntdll child-loader paths](https://github.com/wine-mirror/wine/blob/wine-11.0/dlls/ntdll/unix/loader.c).
- [Highball's original Intel-loader investigation](https://github.com/gauthierpiarrette/highball/issues/338).
