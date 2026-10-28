# Agent Execution Plan — Portable RDR2 for Apple Silicon (Build Mac → Host Mac, Steam + Wine)

**Prepared:** 2026-10-25  
**Build machine:** A separate Apple Silicon **build Mac** where development tools, Wine components, and packaging tools may be installed  
**Target / host machine:** MacBook Pro with Apple M1 Max, receiving a self-contained launcher  
**Target game:** Red Dead Redemption 2 (RDR2), owned on Steam, **Story Mode first**  
**Constraint:** Do not purchase or install CrossOver, Parallels, commercial Wine wrappers, or a Windows VM. Use freely available tools and legally owned game files only.  
**Objective:** Build and verify a **self-contained macOS `.app` on the build Mac** that can be copied to the host Mac and run without installing Homebrew, Highball, Wine, MoltenVK, DXMT, Xcode, compilers, or other third-party runtimes on the host. Its first-run workflow must initialize its own Wine prefix, start/install Windows Steam, let the user sign in, download the user-owned RDR2 from Steam, authenticate with Rockstar, and start Story Mode. Deliver the packaged app, repeatable build scripts, manifest/SBOM, diagnostics, and test evidence.  
**Important limit:** A `.app` is one drag-and-launch artifact containing many executables/libraries, **not literally one statically linked Mach-O executable**. macOS system libraries and Rosetta 2 are provided by Apple, not copied into the app. If Rosetta is missing, the user must approve macOS installing it; no Wine-based solution can truthfully promise zero system prerequisites in that case. Internet access and Steam/Rockstar authentication are required for first-time download/use.

## Agent operating instructions

You are a coding/terminal agent working **primarily on the build Mac**, with a separate **host Mac** for validation. Execute the plan sequentially, testing and recording evidence at each gate. Don't simply produce instructions: perform the tasks that are possible with your actual access, create scripts/configuration, and accurately report tasks that require the user or cannot be verified.

- Prioritize the **existing verified RDR2 path**. Prove gameplay with a tested engine first, **then packaging a standalone `.app` becomes mandatory**. Do not create a custom Wine fork or graphics translator unless a demonstrable compatibility issue demands it.
- Preserve any existing Doom 2016, Wine, Steam, and game installations. Do **not** modify or delete unrelated Wine prefixes, host files, bottles, or macOS system components.
- Ask for user interaction **only** when required for Apple authorization, Steam/Rockstar authentication (including MFA/CAPTCHA), game ownership, license acceptance, or inaccessible GUI operations. Never request, record, echo or script passwords, tokens, recovery codes or cookies. Never attempt to bypass Steam/Rockstar DRM or anti-cheat.
- Before installing or running third-party binaries, confirm they come from official trusted sources and use supplied signature/checksum verification where supported. Read install scripts before executing; no unreviewed `curl | sh`.
- Avoid `sudo`, security-setting changes, macOS Gatekeeper bypasses, and global mutations unless clearly necessary; disclose the action to the user and get permission first.
- Before modifying configuration files, save a timestamped backup. For uninstall/reset operations, display the exact path and get authorization; don't use broad `rm -rf`.
- Don't claim a game has launched successfully until it has visibly entered Story Mode and interactive gameplay has been verified. **Do not claim portability until the copied bundle has passed a clean-host test with no Highball/Homebrew/Wine installation.** If a task is blocked, leave usable scripts, logs and precise next action.
- **Build Mac workspace:** `~/Games/rdr2-agent/` for source, scripts, vendor artifacts, notes, logs and distribution outputs. Highball manages its own engines and Wine environments under `~/Library/Application Support/Highball/`; use these only as a verified reference/staging source. **The final host `.app` must not reference or require those Highball directories.**
- Record key discoveries and issues in `STATUS.md` as you work. Make scripts repeatable/idempotent, quote paths containing spaces, and avoid hard-coded home directories.

## Non-negotiable delivery contract — build Mac vs. host Mac

- **On the build Mac:** You may install/build development tools, obtain Wine 11 with its matching runtime, patched MoltenVK, DXMT, and other redistributable dependencies; inspect manifests; construct and sign the `.app`; produce `.zip` / `.dmg` release artifacts and SHA-256 checksums.
- **On the host Mac:** The user must only have to copy/download and open `RDR2Launcher.app` (or an equivalently named `.app`). **No Homebrew commands, `brew install`, Highball install, Xcode/CLT install, Wine install, pip/npm install, package managers, or manual environment-variable setup on the host.** App-managed installation of Windows Steam, Rockstar Launcher and game assets in the user's data directory is expected and unavoidable.
- **Already supplied by macOS:** Metal, system frameworks, standard Unix utilities as needed, Gatekeeper, Rosetta 2 **if installed**. The app should detect a missing Rosetta capability and explain the normal macOS approval flow; do not silently change macOS security settings.
- **Bundled in the `.app`:** The complete pinned working Wine engine (binaries, builtin modules, necessary libs), appropriate Wine runtime and loader components, **patched MoltenVK** and Vulkan ICD config/loader dependencies, launcher-compatible DXMT DLL overlays, runtime metadata/recipes, a native arm64 launcher and any other third-party library referenced at runtime. Do **not** bundle macOS system frameworks, copyrighted Steam/Rockstar game binaries without redistribution rights, personal authentication state, or Apple D3DMetal components absent a license permitting redistribution.
- **Downloaded only on first run:** Official Windows Steam installer/client and later RDR2/Rockstar dependencies through their standard vendor channels. The launcher must work without build-Mac-specific accounts, paths, mounts or prefixes.
- **Release acceptance:** A genuinely relocated app on the host runs from an arbitrary user-selected directory; initializes and persists its own prefix; starts Steam; lets the user authenticate; invokes installation for Steam app **1174180**; opens the owned game via Steam and Rockstar; and reaches controllable Story Mode. It must not falsely report success if unverified.

## Technical findings (verified as of 2026-10-25)

1. **Highball** is a free GPL-licensed Apple Silicon Wine frontend/CLI. It supports Windows Steam, Wine 11 and Rockstar sign-in, and has a verified RDR2 entry. Use it as a **free starting runtime**, not a proprietary paid wrapper. Some Wine source used in Highball's Wine 11 build is published by CodeWeavers, but **no CrossOver purchase is required**.
2. **Primary graphics path:** RDR2's **native Vulkan renderer → Wine's Vulkan bridge → patched MoltenVK → Metal**. Select Highball's RDR2-tested Wine 11 `x64-crossover26.3` engine **revision r6 or later**, preferably a recent known-good revision with the patched MoltenVK. Highball's RDR2 game entry currently cites `x64-crossover26.3-r27` and recommends **DXMT** as the environment's graphics mode. **Important:** DXMT translates D3D11 to Metal for launcher components; **RDR2 itself is not running through DXMT**. Do not force RDR2 into a nonexistent Direct3D 11 renderer.
3. **Optional experimental alternative:** RDR2's DX12 renderer → Apple's **D3DMetal** → Metal. A community report dated 2026-10-20 describes success, but it needs specific registry and launcher/Steam graphics workarounds and is not the default verified route. Apple D3DMetal is free to obtain with license conditions, but it is proprietary. Do not use it unless the native Vulkan route is blocked or the user asks to optimize/test alternatives.
4. RDR2 needs a **Rockstar Games Launcher sign-in** in addition to Steam ownership. The Wine 11 engine is necessary for its embedded sign-in browser; the Highball notes describe a Rockstar launcher error **113** fix in Highball 0.10.16 and an installer issue in engine revisions r11–r14 fixed in r15. Favor current versions, not outdated forum recipes.
5. Compatibility does **not** imply smooth performance. Early M1 Pro / 16 GB tests on Vulkan reported ~34 FPS at 720p in an initial section, with substantial frame pacing and memory issues; M1 Max results depend on GPU model, unified memory and software versions. Collect actual evidence rather than promising any FPS.

6. **Packaging is a distinct engineering problem.** Highball normally downloads/manages its Wine engine under Application Support, and its manifests assemble Wine plus dylibs and renderer overlays. The agent must create a **relocatable** bundle, not simply copy a Highball executable and expect its absolute paths or shared runtime to work.
7. **macOS distribution security matters.** For a Gatekeeper-friendly standalone release, sign each nested Mach-O component correctly, then sign the outer app with a Developer ID certificate and notarize where signing credentials are available. No signing identity may be assumed; if absent, deliver an accurately labeled local-test build, and record that clean host launch remains blocked until signing/notarization or explicit approved user action. Never suggest disabling Gatekeeper as a routine setup step.
8. **Steam is not a build artifact.** The final app invokes the real Windows Steam installer/update/login flow and downloads RDR2 under the user's account. For game installation target **Steam app ID 1174180**, verify this ID and the supported Steam invocation at implementation time; Steam's state is authoritative, not just a directory or `appmanifest` file.

### Official references

- Highball: https://github.com/gauthierpiarrette/highball
- Highball install docs: https://gethighball.com/docs/install/
- Highball first-game guide: https://gethighball.com/docs/first-game/
- **RDR2-specific verified notes and issues:** https://gethighball.com/games/red-dead-redemption-2/
- Highball troubleshooting: https://gethighball.com/docs/troubleshooting/
- Highball open compatibility recipes: https://github.com/gauthierpiarrette/highball-db
- Apple GPTK (optional DX12/D3DMetal experiments): https://developer.apple.com/games/game-porting-toolkit/
- Apple packaging and distribution: https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution
- Apple notarization: https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution
- Apple Rosetta 2: https://support.apple.com/en-us/102527

## Phase 0 — Preflight, inventory and non-destructive checks

**Goal:** Establish whether the **build Mac** meets the requirements and collect host OS requirements; repeat read-only checks on the host at deployment. Establish whether the host meets the requirements and gather baseline information without changing anything.

Tasks:

- [ ] On the build Mac, print and save `date`, `sw_vers`, `uname -m`, `sysctl -n machdep.cpu.brand_string` if available, `system_profiler SPHardwareDataType`, and `df -h ~` to `logs/preflight.txt`; optionally summarize RAM without exposing personal serial numbers in shared logs.
- [ ] Require Apple Silicon / `arm64` and macOS **14+** per Highball docs for the working baseline; determine the build and host macOS releases. Verify the chosen Wine engine supports the host OS; the app's minimum deployment target must not exceed the host OS. Note macOS versions in `STATUS.md`.
- [ ] Check free disk space on **both machines**: Highball runtime/environment ~8 GB plus game install and working headroom; prefer **at least 150 GB free on host** before a fresh game download. RDR2's storage requirement can change; verify against Steam/current installed build before proceeding.
- [ ] Check whether Rosetta 2, Xcode Command Line Tools, Homebrew, Highball, Wine and Steam are already present. **Do not reinstall unnecessarily.** Check whether a Steam Windows library has already downloaded RDR2.
- [ ] Inspect existing Doom 2016 installation only to avoid overlap. Do not change its settings.
- [ ] Create `~/Games/rdr2-agent/{scripts,logs,notes,src,packaging,dist,vendor}` on the **build Mac**; start `STATUS.md` with an environment inventory and a precise checklist.

Suggested read-only checks:

```bash
sw_vers
uname -m
system_profiler SPHardwareDataType
df -h "$HOME"
command -v brew || true
command -v git || true
command -v swift || true
ls -ld "/Applications/Highball.app" "$HOME/Library/Application Support/Highball" 2>/dev/null || true
```

**Gate:** Host and disk capacity validated. If insufficient memory or space, report limitations before an expensive installation. If macOS is unsupported, stop before modifying the system.

## Phase 1 — Install and bootstrap the tested Wine environment

**Goal:** Make a working Highball-managed Wine environment while minimizing host changes.

Tasks:

- [ ] Prefer the signed/notarized release from Highball's official site or GitHub. If Homebrew is installed, the official documented command is `brew install --cask highball`. **Do not install Homebrew solely for this task** unless the user approves; download the official DMG instead.
- [ ] Start Highball and allow its first-time setup to install verified/pinned Wine engine components. If Rosetta is missing, obtain user permission before macOS installs it.
- [ ] Choose/install the Wine 11 engine that Highball recommends for RDR2/Rockstar and **verify it contains RDR2's patched MoltenVK fix**. Record exact Highball version, engine identifier, and GPU/runtime versions in `STATUS.md`.
- [ ] Set up a **dedicated RDR2 environment/bottle** if supported. Don't repurpose the Doom 2016 environment. Use Highball's UI/CLI to create/install Steam; verify the resulting environment and engine before modifying it.
- [ ] Keep a copy of any generated configuration, nonsecret engine metadata and selected renderer mode in `notes/environment.md`.

For an agent with Terminal access but no control of the Highball UI, Highball's upstream README describes building a CLI from source. This is a **fallback**, not a mandatory second installation:

```bash
# Execute only if the GUI isn't sufficient, git/swift are available,
# the repo URLs have been reviewed, and the user authorizes a source build.
mkdir -p "$HOME/Games/rdr2-agent/vendor"
cd "$HOME/Games/rdr2-agent/vendor"
git clone https://github.com/gauthierpiarrette/highball.git
git clone https://github.com/gauthierpiarrette/highball-db.git
cd highball
swift build -c release
./.build/release/highball --help
```

The upstream CLI documents commands similar to `engine install`, `bottle create ... --recipe steam`, and `run ... Steam`. **Read the installed CLI's `--help` and engine manifest first**, then select its compatible Wine 11 engine and appropriate Steam/Rockstar recipes. Do not blindly run a sample command that chooses an unsuitable default engine. Do not overwrite a working GUI-created environment with a CLI-created one.

**Gate:** Highball can start the Windows Steam window in an RDR2-specific environment with the required Wine engine selected.

## Phase 2 — Install and sign in to Windows Steam

**Goal:** Use the user's legitimate Steam account and existing RDR2 license.

- [ ] Launch **Windows Steam inside the RDR2 Wine environment** (not native macOS Steam for the Windows game).
- [ ] Allow Steam's first-run update to complete; Highball documentation says initial setup can take 15–25 minutes under Rosetta. Don't incorrectly treat ongoing extraction as a hang.
- [ ] User performs Steam login and Steam Guard interaction on screen. Never automate or log secrets.
- [ ] Confirm the RDR2 Steam page is available in the library. Steam app ID is **1174180**.
- [ ] Download/install from the existing owned Steam library; if there is already a compatible game directory, prefer Steam's supported game-file discovery/verification instead of copying files blindly.
- [ ] Verify installed files with Steam if needed, and record RDR2 install location and available disk capacity.

**Gate:** Steam launches, login works, and the legitimate RDR2 installation is recognized.

## Phase 3 — Rockstar Launcher and the Vulkan/MoltenVK graphics path

**Goal:** Start through the normal Steam → Rockstar → RDR2 chain, without bypassing authentication.

- [ ] Review the **live** Highball RDR2 page before proceeding because the tested engine/recipes can change: https://gethighball.com/games/red-dead-redemption-2/
- [ ] If current recipe/notes require installing Rockstar Games Launcher through Highball before first play, do that in the **same RDR2 environment**. In particular, the documented r7 workaround requires this order. Later engine revisions may automate it.
- [ ] Have the user complete Rockstar login and any 2FA/MFA in the actual launcher window; no credentials in scripts or logs.
- [ ] Configure the game to use **Vulkan**, its default renderer. The graphics-mode picker being labelled DXMT is not proof the game is using D3D11. Keep the launcher-compatible DXMT selection if recommended by Highball.
- [ ] Use **windowed 1280×720** and the Safe/Low preset for the first validation. RDR2's `system.xml` is under the bottle's Windows Documents path, typically `Documents/Rockstar Games/Red Dead Redemption 2/Settings/system.xml`. Locate it under the active Wine prefix; **don't assume a host `~/Documents` path**. Only edit it after the file exists, making a timestamped backup; confirm the actual XML structure/attribute names.
- [ ] Start through Windows Steam/Highball's **Play** operation, not by invoking `RDR2.exe` outside its Steam/Rockstar entitlement chain.
- [ ] Record whether Steam opens, Rockstar authenticates, the game opens, the loading screen completes, the main menu appears, and Story Mode enters controllable gameplay.

**Gate:** Story Mode loads into interactive gameplay, not merely a menu. Record the exact renderer and engine used. If this is blocked, diagnose first rather than continuing to custom launch scripts.

## Phase 4 — Diagnose failures systematically

**Rule:** Change **one variable at a time** and rerun the smallest relevant test. For each failure capture exact error message, reproduction command, Wine/Highball engine versions, relevant sanitized log lines, and the single fix attempted. Save reports under `logs/` and document in `STATUS.md`.

| Symptom | First action |
| --- | --- |
| Windows Steam blank, updating or slow | Check first-launch update status; use Highball Steam compatibility settings and correct renderer; don't force the whole environment onto D3DMetal. |
| Rockstar blank embedded login or crashes | Ensure supported Wine 11 engine; check Highball Rockstar recipe and recent known issues. |
| Rockstar launcher installer says other instances are running | Compare engine revision with documented r11–r14 regression; use fixed r15+ or another documented known-good build. |
| Rockstar error 113 / missing Steam association | Confirm Highball 0.10.16+ fix and correct shared Wine environment; inspect registry non-destructively; don't blindly delete registry keys. |
| Vulkan load reaches ~98% then game exits | Check whether the selected Wine engine includes Highball's **patched MoltenVK** (introduced in RDR2-compatible r6). Generic MoltenVK may fail. |
| `failed to initialize graphics device`, error 18 | Check API setting, DLL loading, launcher/game paths and current Highball RDR2 notes; don't copy DLLs based on Epic-only recipes into the Steam build without evidence. |
| Game launches but trees/grass flicker | Known issue for Vulkan/MoltenVK. Record build and gameplay evidence; test non-destructive graphics settings. Don't set `MVK_CONFIG_USE_MTLHEAP=0` (reported to break startup). |
| Low FPS, stalls, heavy swap | Record RAM/swap pressure and GPU frame timings; reduce resolution and settings, try FSR 2. Avoid guesses based on FPS overlays alone. |
| D3DMetal/DX12 crashes | Return to verified Vulkan baseline. Only attempt the experimental DX12 workaround with explicit backup and user approval. |

Redact usernames, account data, tokens and private paths when publishing logs.

## Phase 5 — Tune M1 Max performance *after* verified gameplay

1. Record a baseline at **1280×720 windowed, Safe/Low**. Observe the same gameplay segment for a few minutes and collect average FPS, visible frame pacing, CPU/GPU usage if available, unified memory and swap.
2. If baseline works, test **1920×1080** at Low/Medium. Lower volumetrics, shadows, reflections and water physics; keep MSAA off. Test FSR 2 Quality or Balanced if accessible.
3. Change **one setting per run**. Save a benchmark table at `notes/benchmarks.md` with scene, resolution, preset, FSR, average FPS, 1% low if measurement is reliable, and memory/swap observations.
4. Test fullscreen or borderless **only after** windowed gameplay works; use Highball's display-mode emulation if available. Maintain a rollback to working 720p configuration.
5. No performance claims based on M5 Max, M1 Pro, or CrossOver results should be stated as an actual M1 Max measurement.

### Planned: automatic macOS Game Mode for RDR2

Enable Game Mode when RDR2 launches and enters macOS full-screen mode. This is
pending implementation and host validation.

- [ ] Determine how macOS identifies the actual RDR2 Wine process in the pinned
  Intel engine, including the Steam → Rockstar → RDR2 launch chain.
- [ ] Add the required game-category and `LSSupportsGameMode` metadata to the
  appropriate app/helper bundle; verify that recognition reaches the game process.
- [ ] Integrate macOS full-screen entry for the game, preserving a way to return
  to the working windowed configuration.
- [ ] On the M1 Max, verify Game Mode activation for RDR2 in Game Overlay, normal
  deactivation after exiting full screen or quitting, and repeat-launch behavior.
  Record activation evidence separately from any measured performance improvement.

References: [Apple Game Mode requirements](https://support.apple.com/en-us/105118),
[Apple's Game Mode metadata](https://developer.apple.com/documentation/bundleresources/information-property-list/lssupportsgamemode),
and [Highball's Intel-engine limitation](https://github.com/gauthierpiarrette/highball/releases/tag/v0.10.17).

## Phase 6 — Create reproducible launch and diagnostic scripts (working build-Mac baseline)

**Goal:** Minimize future GUI steps without breaking Steam/Rockstar authentication or depending on unstable implementation details.

Create these files under `~/Games/rdr2-agent/`:

```text
rdr2-agent/
├── README.md                 # user-friendly steps to play and troubleshoot
├── STATUS.md                 # observed state, versions, progress, blockers
├── plan.md                   # local copy of this plan
├── scripts/
│   ├── preflight.sh          # read-only host validation
│   ├── launch-rdr2.sh        # start with verified Highball Steam/game path
│   └── diagnose.sh           # capture sanitized diagnostics
├── logs/                     # no secrets; timestamped runs
└── notes/
    ├── environment.md
    └── benchmarks.md
```

**Launcher requirements:**

- Invoke the **supported Highball CLI or application** using a confirmed command from its help/source; don't invent an executable path or Wine environment variable format.
- Keep the correct Wine bottle and Steam/Rockstar authentication context; prefer an officially supported Highball game launch command when available.
- Quote shell paths, use `set -euo pipefail` where practical, report errors clearly, and launch only one copy.
- Provide a `--diagnose` or separate diagnostic script that captures reproducible setup info without collecting authentication secrets.
- Do not copy Highball's internal Wine binaries into an independent directory **blindly**. First verify component provenance, licenses, dynamic-library load paths, patched MoltenVK and dependencies. **Repackaging the verified runtime is mandatory in Phases 7–9.**
- Test scripts with `bash -n` and/or `shellcheck` (if already installed), then execute a genuine end-to-end Steam/Rockstar/RDR2 launch. A script that prints success or opens Steam but never starts RDR2 is not finished.

## Phase 7 — Build a truly standalone, relocatable macOS app (MANDATORY)

**Goal:** Build the binary **on the build Mac** and copy one self-contained `.app` to the host. Running on the host must not require Homebrew, Highball, standalone Wine, Wine configuration, a shell setup script, a compiler, or a separately installed Vulkan/graphics layer. The release unit is an `.app` bundle containing native and x86_64 components, not one bare Mach-O file.

### 7.1 Freeze a reproducible runtime and review licenses

- [ ] Starting from the *actually working* Phase 3–5 baseline, pin the exact Highball-compatible Wine 11 engine, Wine runtime dylibs, **RDR2-fixed MoltenVK**, Vulkan loader/ICD, DXMT launcher DLL overlays, Wine services/builtin libraries and supporting tools. Record version, source URL, license, SHA-256, architecture (`file`/`lipo`), and build ID of every redistributed third-party component.
- [ ] Derive the engine file layout, startup parameters, DLL precedence and environment variables from the pinned engine manifest and HighballKit source. Do not guess where Wine dynamically loads its own helpers. Inspect Wine-builtins, runtime libs, font/config dependencies, patch overlay order, Vulkan ICD JSON references, and paths used by `wineserver`, `wineboot`, Steam and Rockstar.
- [ ] Build or stage all components **on the build Mac**. Reuse legally redistributable binary artifacts only if their licensing permits bundling. Keep relevant LGPL/GPL notices, copyright and source/offer obligations in `Contents/Resources/licenses/` and an `SBOM.md` or SPDX/CycloneDX manifest.
- [ ] **Do not assume D3DMetal can be redistributed**. Native RDR2 Vulkan through patched MoltenVK is the release default. Do not bundle proprietary Steam/Rockstar launchers or user-owned game files unless the holder's terms explicitly authorize it.

### 7.2 Create native app binary plus embedded runtime

Build an **arm64 Swift/AppKit macOS `.app`** (or similarly minimal native launcher) that manages the Wine child processes, user prompts, paths, progress display and first-run state. This is the deliverable that the host user double-clicks. Use build tools only on the build Mac.

Suggested release structure (final names are flexible; document exact verified layout):

```text
RDR2Launcher.app/
└── Contents/
    ├── Info.plist                     # identifier, icon, min supported macOS
    ├── MacOS/
    │   └── RDR2Launcher              # compiled arm64 executable
    ├── Frameworks/                    # all non-system macOS dylibs needed at runtime
    └── Resources/
        ├── engine/
        │   ├── bin/                   # Wine executables, wineserver, wineboot etc.
        │   ├── lib/                   # Wine builtin/loader/runtime libraries
        │   └── ...                    # original verified engine structure
        ├── renderers/
        │   ├── patched-moltenvk/      # engine-matched Vulkan→Metal stack
        │   └── dxmt/                  # for Steam/Rockstar launcher components
        ├── recipes/                   # runtime/Steam/Rockstar settings and pinned config
        ├── licenses/                  # third-party notices and required license files
        └── runtime-manifest.json      # SHA-256, versions and relative paths
```

- [ ] Use **bundle-relative runtime paths** derived from the current executable/bundle resource URL. **No dependency on** `/opt/homebrew`, `/usr/local`, the build Mac's `$HOME`, Highball's Application Support directory, its engine cache, Swift build folders, or mounted disk images.
- [ ] Inspect all Mach-O binaries with `file`, `otool -L`, `otool -l` (especially `LC_RPATH`), and `codesign`; replace build-machine-specific non-system load commands using `install_name_tool` / `@rpath` / `@loader_path` / `@executable_path` as appropriate **on the build Mac**. Do not patch third-party binaries unless licenses permit and the need is verified. Re-sign changed binaries.
- [ ] Check external references using `grep` / `strings` as supplemental detection for embedded absolute paths, but do not treat a clean grep result as proof of correctness. Verify all components genuinely load by launching Wine tools from the **relocated** bundle.
- [ ] Keep Wine process architecture compatible with Apple Silicon/Rosetta. Do not attempt to convert Windows x86-64 binaries to arm64 by simple copying. Preserve original Wine engine metadata and renderer overlay selection semantics when necessary.
- [ ] Include only permitted/system-safe resources. Do not redistribute the build machine's keychain, user registry/authenticated prefix, Steam session files, personal game libraries or any account data.

### 7.3 Isolate all mutable state outside the signed app

The app bundle may be read-only or app-translocated; **never write Wine prefixes, Steam updates, caches, logs or RDR2 game files into `Contents/`**.

Use standard writable paths, derived at runtime using Foundation APIs, e.g.:

```text
~/Library/Application Support/RDR2Launcher/
├── prefixes/default/             # user-specific Wine prefix, registry, Steam/Rockstar login
├── downloads/                    # optional official Steam installer cache
├── state/                        # bootstrap/progress/state.json
└── logs/                         # sanitized diagnostic data

~/Games/RDR2/                     # optional user-selectable large game library
```

- [ ] Prefer a user-selectable RDR2 download location, but keep the Steam library correctly mapped into the *same* Windows Wine prefix and preserve it across app updates. If the user doesn't choose, use a documented writable default and preflight free space.
- [ ] Generate the clean user prefix on host first launch via the bundled `wineboot` and verified recipe. If bundling a preinitialized **neutral** prefix for startup speed, strip all build-Mac paths, symlinks, machine/account information, login tokens, keys and cached user data; **prefer fresh initialization unless a sanitized seed has been proven portable**.
- [ ] Preserve user data across `.app` replacement. Store state and provide explicit repair/reset features that cannot accidentally delete the Steam library or saved games. Avoid claiming Wine provides isolation/security.

**Gate 7:** Run the launcher and built-in Wine utilities from an arbitrary copied `.app` path **after removing the build-time runtime environment from `PATH`**, and confirm no missing dylibs/ICD paths/Highball dependencies. The Wine engine is fully included without fetching engine bits.

## Phase 8 — First-run workflow: start Steam, download RDR2, launch (MANDATORY)

**Goal:** The host user's whole normal workflow starts by double-clicking **one app**. The native launcher should act as a small orchestrator; Steam and Rockstar remain official Windows applications running under Wine.

Implement a persisted, crash-resumable state machine, not a brittle sequence of fixed sleeps:

```text
Open RDR2Launcher.app
  → Validate Apple Silicon/macOS/free space/Rosetta
  → Select writable game data/library directory
  → Initialize bundled Wine 11 + patched MoltenVK environment
  → Acquire official Windows Steam installer if Steam absent
  → Run Steam install/update inside Wine (show windows/status)
  → Launch Windows Steam and request user sign-in / Steam Guard
  → Confirm account owns RDR2 (do not assume entitlement)
  → Initiate RDR2 download/install with Steam (app ID 1174180)
  → Wait for Steam to confirm download/verification completed
  → Launch RDR2 using Steam's supported game-launch route
  → Allow Rockstar Games Launcher setup/sign-in/MFA
  → RDR2 → Story Mode → interactive game
  → On subsequent opens: start installed Steam → launch installed RDR2
```

Implement with explicit states such as `missing_rosetta`, `needs_prefix`, `needs_steam`, `steam_updating`, `needs_steam_login`, `needs_rdr2_install`, `rdr2_downloading`, `needs_rockstar_login`, `ready`, `launching`, `running`, `error`. Refresh based on observed process/client/install events, not stale cached assumptions.

### Required user experience

- [ ] No terminal required on host. Provide an understandable native UI with **Install & Play**, **Play**, **Open Steam**, **Repair**, **Choose game folder**, **View logs**, and **Quit**, where appropriate. Controls must operate, not be decorative.
- [ ] The built-in app **must launch the bundled Wine engine**, not discover `wine` with `which` and not call `open -a Highball`.
- [ ] If Rosetta is missing, explain that Apple manages it, request permission, and use Apple's supported installation mechanism or allow the system prompt. An optional system installation of Rosetta is the **only possible OS-managed exception** to zero third-party-install prerequisite. Do not bundle it or hide the need from the user.
- [ ] On first run, download the official **Windows Steam installer from Valve** over HTTPS using the built-in macOS networking APIs (or a macOS-provided networking tool). Record provenance and verify signatures/hashes when reliable official verification exists. Allow Steam's own updater to update its files in the writable prefix. Never use arbitrary unaudited mirrors.
- [ ] Run Steam in the existing prefix and surface its normal GUI for sign-in, Steam Guard, download location confirmation and EULA. Do not read/intercept user credentials or automate CAPTCHA/MFA. Steam Guard must be completed by the user.
- [ ] Use a supported Steam API/URI/command for `1174180` to ask **Steam itself** to install/verify/launch RDR2, e.g., an appropriately quoted `steam://install/1174180` request through the *Windows* Steam client or a verified equivalent. Test the command with the installed Steam version; do not implement custom game downloading, depot unpacking, DRM bypass, or simulated completion signals.
- [ ] Steam performs the actual download and reports its own download progress. The app may summarize state, but must never declare the game ready merely because `appmanifest_1174180.acf` exists; check Steam's observed status and the actual launch result.
- [ ] For **Play**, keep the Steam → Rockstar launcher → game entitlement/process chain (Steam `-applaunch 1174180` or a supported equivalent after validation). If needed, keep the helper client in the Wine prefix active. Have the user complete Rockstar authentication, without extracting or storing its secrets in app logs.
- [ ] Keep RDR2's **Vulkan** default and patched MoltenVK for the actual game, with DXMT graphics handling compatible launcher parts. Implement verified `WINEDLLPATH_PREPEND`, Vulkan loader/ICD settings, Wine prefix and library paths **per process**. Use engine-derived values, not guessed `DYLD_*` overrides or wholesale copying of DLLs.
- [ ] Handle interrupted downloads, Steam self-updates, prefix initialization failures, captive portals, offline use of installed games (when Steam/Rockstar actually allow it), running instances, retries and inconsistent manifests. Never promise DRM-protected offline play.
- [ ] Show useful errors without exposing account credentials in logs. Make bootstrapping idempotent; clicking twice must not start two Steam setup instances.

**Gate 8:** On a fresh macOS user account, one app starts the real Windows Steam GUI and prompts for game install without any host-managed development tools or Wine downloads. A user with an owned copy can then authenticate, download and launch RDR2. Do not mark the entire gate as passed until the real behavior has been seen.

## Phase 9 — Sign, package, transfer and validate on a CLEAN host (MANDATORY)

**Goal:** Produce a release-quality binary on the build Mac and test it on the **separate host Mac** under normal Gatekeeper/security settings. **Build success alone is not acceptance.**

### Release artifacts on the build Mac

- [ ] Implement deterministic scripts: `packaging/build-app.sh`, `packaging/audit-deps.sh`, `packaging/sign-app.sh`, `packaging/package.sh`, `packaging/test-relocation.sh`, with a `BUILD.md` describing build host toolchain, sources, checksums and exact build commands.
- [ ] Compile the **native arm64 launcher** on the build Mac. Copy the complete verified engine and dependencies into `Contents/`, preserving executable permissions and symlinks, and recreate only those symlinks that are genuinely relocation-safe.
- [ ] Verify every nested Mach-O executable and library dependency **resolves to a system library or a resource within the bundle**. Explicitly inspect dependencies with `otool -L` and `dyld` diagnostics; ensure no Homebrew/Linuxbrew/Highball/global Wine paths remain. Test `wine --version`/`wineboot` via the app's own runtime and a new private prefix before signing.
- [ ] Produce `dist/RDR2Launcher.app` and `dist/RDR2Launcher.zip` or `.dmg`, plus `dist/SHA256SUMS`, `dist/SBOM.md`, `dist/BUILD.md`, and `dist/TEST-REPORT.md`. The `.app` **contains all required third-party runtime code**, but no bundled RDR2 game and no copied Steam/other account tokens.
- [ ] If a legitimate **Developer ID Application** identity and notarization credentials are available, sign nested binaries **inside out**, sign the app with an appropriate hardened runtime/entitlements determined through testing, notarize the actual release container and staple/validate the ticket. Some Wine/JIT runtime behaviors require carefully tested entitlements; don't switch off security globally or invent entitlements. Validate via `codesign --verify --deep --strict --verbose=2`, `spctl --assess --verbose`, and `xcrun stapler validate` where applicable.
- [ ] If no Developer ID credentials are available, **do not claim a normal double-click release is Gatekeeper-compatible**. Deliver an explicitly labeled unsigned/ad-hoc **development build** (if it can work locally), and record Developer ID signing/notarization as an unresolved release requirement. Do not recommend blanket `spctl --master-disable` or recursive quarantine removal to sidestep Gatekeeper.
- [ ] Audit licensing/redistribution, preserve required GPL/LGPL notices and corresponding-source obligations. Keep Apple D3DMetal out of the distributed Vulkan-default build unless explicit license permission has been confirmed.

### Host Mac validation, with NO Wine/Highball/Homebrew installation

- [ ] Copy only the built release `.app`/archive from the build Mac onto the host Mac (prefer a macOS-normal download/transfer preserving quarantine for the actual Gatekeeper test). Copy to a different path than the build Mac, with **spaces in the path**; no shell setup script or package-manager installation is allowed.
- [ ] Before host test, inventory existing `brew`, Wine, Highball and Steam and **do not rely on them**, even if present. For a convincing check, test with a fresh standard user and constrained environment; do not delete existing tools, prefixes, games or credentials just to simulate a clean machine.
- [ ] Launch using **Finder double-click**, not a special `PATH` or Terminal setup. Verify Gatekeeper prompts behave normally and no unexpected OS policy changes are needed. If macOS requires Rosetta, record user-managed approval and explicitly distinguish this system prerequisite from a bundled Wine dependency.
- [ ] On host, run initial prefix setup with paths under that user's `~/Library/Application Support/RDR2Launcher`; verify Wine, patched MoltenVK and DXMT load from the `.app`; start Windows Steam using the bundled engine.
- [ ] With the user's help only for Steam/Rockstar authentication, show Steam installing/downloading RDR2 under app ID 1174180, verify and launch through Steam → Rockstar → Vulkan/MoltenVK → Metal; verify actual Story Mode control. Record frame rate only if measured, not inferred.
- [ ] Close and relaunch the `.app`: it should reuse Steam/Rockstar auth if permitted, resume existing downloads if incomplete, and go straight to the existing RDR2 install (without re-downloading).
- [ ] Move the `.app` to a *new directory*; test again without rebuilding/changing user files. Replace `.app` with an updated build; confirm game files, Steam updates, prefix and saves remain intact.
- [ ] Test an ordinary uninstall by removing the `.app` (which **must not** silently delete saves/game files). If offering an explicit “Remove all data” command, enumerate affected paths and require user confirmation.

**Gate 9:** A copied, appropriately signed/notarized bundle runs from Finder under normal macOS security on the separate M1 Max **with no Homebrew/Highball/Wine/etc. installation**, bootstraps Windows Steam, downloads the owned RDR2, signs into Rockstar and plays Story Mode. Report precise results if any part is blocked; do not reduce this to “Steam opens” or “the bundle builds”.

## Optional Phase 10 — Experimental DX12/D3DMetal comparison

**Only perform after the standalone Vulkan baseline works (or is conclusively blocked) AND the user explicitly approves an experimental change.**

- Back up the working environment and `system.xml`, or clone the bottle where supported.
- Review the 2026-10-20 community DX12 report in Highball's RDR2 notes; its working recipe combines `kSettingAPI_DX12`, D3DMetal-specific identifiers, app-scoped DLL overrides, DXMT for Rockstar's launcher, and Steam webview adjustments.
- Use Apple's legitimate Game Porting Toolkit download and license process. No pirated commercial binaries or copied CrossOver app DLLs. **Do not include Apple's D3DMetal binary in a release without confirming its redistribution rights.**
- Verify Steam and Rockstar window rendering independently before running the game. The default D3DMetal mode can break launcher webviews without specific overrides.
- Compare actual time in interactive gameplay, performance and artifacts. If it fails, restore the known-good Vulkan path and report why.
- Do not present community reports as locally verified results.

## Acceptance criteria (all mandatory unless expressly marked optional)

- [ ] **Built on the separate build Mac:** an arm64 `RDR2Launcher.app` with bundled Wine 11, full engine/runtime dylibs, patched MoltenVK, DXMT and native launcher; no build-Mac absolute paths or outside third-party runtime dependencies.
- [ ] **Host is installer-free for third-party prerequisites:** Finder can open a copied bundle without Homebrew, Highball, Xcode, CLT, a Wine package, graphics installers, or shell environment setup. Apple-managed Rosetta may require approval if missing, and the Steam/game download is deliberately performed on the host.
- [ ] **Steam first-run workflow:** official Windows Steam downloads/updates, account sign-in occurs in Steam, game `1174180` downloads/verifies via Steam, and Rockstar launches via the legitimate entitlement chain.
- [ ] **Relocation + persistence:** app works from a different path with spaces; persists Steam/game data outside the signed app and survives app replacement without redownload.
- [ ] **Packaging/security:** correct nested-binary dependencies, signatures and (for normal Gatekeeper distribution) notarization; include licensing, checksums and SBOM. Otherwise clearly mark the release as a development build with unmet signature/notarization gate.
- [ ] **Clean-host evidence:** acceptance on an actual separate Mac or clean account, not just the build Mac; the agent explicitly identifies host tests that could not be performed.

- [ ] No paid software or VM required; no unwanted changes to Doom 2016.
- [ ] Verified current macOS / M1 Max / available unified memory / disk headroom.
- [ ] Correct Highball Wine 11 engine with patched MoltenVK selected and recorded.
- [ ] Windows Steam can authenticate and recognize the user's owned RDR2 installation.
- [ ] Rockstar Games Launcher signs in normally and launches through the Steam entitlement chain.
- [ ] **Story Mode is controllable in-game** (not just launcher or splash screen).
- [ ] Reliable graphics backend documented: native Vulkan over patched MoltenVK as baseline (or explicit evidence for an alternative).
- [ ] `scripts/launch-rdr2.sh` remains repeatable for build-Mac diagnostics, **but final host launch is the double-clicked app**, not a shell command. Documentation identifies required Steam/Rockstar login and any Apple-managed Rosetta prerequisite.
- [ ] `STATUS.md`, `notes/environment.md`, `notes/benchmarks.md`, sanitized diagnostics, `BUILD.md`, source code, `dist/RDR2Launcher.app`, `.zip`/`.dmg`, checksum manifest, SBOM, and host-test report are delivered to the extent verified.
- [ ] If incomplete, report the exact highest completed milestone, problem, attempted fixes and safest next step—**do not mark the game as working**.

## Final report required from agent

Summarize:

1. Build Mac **and** host Mac macOS/RAM/disk summary (omit serial numbers), Wine engine revision, packaged runtime components, graphics backend, Steam/Rockstar state.
2. Which phases and acceptance checks passed and failed.
3. The absolute build output path and **double-clickable `.app` release**, SHA-256, tested macOS compatibility, codesign/notarization status, bundled dependency audit, and host user action (Rosetta if needed, Steam/Rockstar login).
4. At least one real gameplay test with observed graphics settings and FPS if it ran; otherwise the exact error and logs.
5. Build and host files installed/changed, macOS-managed prerequisites, uninstall/rollback procedure, persistence/data location, licensing details, and recommended next experiment if blocked.
6. Confirmation that **host runtime uses zero build-Mac-installed tools**, evidence from the clean-host test, and a concise truthful explanation of anything that prevents a fully install-free release.

**Work through the phases autonomously wherever possible. Stop only at genuine human-interaction or permission gates, then resume once available; never fabricate successful results.**
