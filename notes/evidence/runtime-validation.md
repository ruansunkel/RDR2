# Runtime validation — 2026-10-25

This supersedes the launcher-only artifact status in the earlier build-validation
report. The user clarified that the current VM is the build Mac and the unavailable
host will test playability after transfer. No simulated download counts as acceptance.

## Observed preparation and bootstrap

- Current build environment: macOS 27.0.1, Apple M1 Max Virtual, 8 GB RAM. Rosetta
  now executes x86_64 code; native Steam was already present. Neither was installed
  by this agent. Existing native Steam/account data is left untouched.
- All six r27 archives were downloaded from pinned upstream URLs and verified
  against config/engine-upstream.json SHA-256 values before extraction/execution.
- Wine loader: wine-11.0. Fresh private wineboot and Windows cmd passed; cmd reports
  Microsoft Windows 10.0.19045. Logs show patched MoltenVK initialized against the
  Apple Paravirtual device. Its RDR2 linear-fallback marker strings were inspected.
- Static inspection of the unmodified assembled runtime found 21 packaging issues.
  These included Homebrew media dependencies, stale framework ABIs, external IDs,
  RPATHs and the dangling Apple graphics alias. No outside dylib was silently accepted.
- The new portable stage uses GStreamer 1.28.7, matching Intel GLib/PCRE2/libintl,
  and source-built FFmpeg 9.0.2 demux libraries. Load-path changes, original/patched
  hashes and exact operations are retained in runtime/relocation-changes.json.
- The first dynamic GStreamer test found missing _libintl_newlocale; matching
  gettext/libintl fixed actual gst-inspect startup. The helper reports 1.28.7.
  No ABI version was falsified. All packages remain local, not globally installed.
- Wine media registration succeeded. winedmo.dll has no DllRegisterServer export,
  so regsvr32 is not used as its acceptance test; direct media-library load checks
  in the final smoke test verify the FFmpeg loader dependency closure instead.
- The actual bundled native app initialized its private prefix, downloaded Valve's
  official Windows Steam installer over HTTPS and installed Windows Steam.
  App-defined status output was retained without client/account output.
- Steam's updater reported completion. steam.exe and five steamwebhelper.exe
  processes were observed. The user confirmed sign-in and an active RDR2 download.
  A nonsecret manifest progress sample reported 121,031,398,992 bytes to download
  and 128,413,911,887 bytes to stage. Neither manifest presence nor progress proves
  completion, ownership, game readiness or gameplay; Steam/user confirmation is authoritative.
- Active build data: vendor/probes/native-steam/. The client/download is not stopped,
  reset, copied into the app or replaced by another prefix. No passwords, tokens,
  cookies, login registry entries or account identifiers were collected or exported.
  Only allowlisted nonsecret installation/progress fields were summarized.
- 157 vendor notice/provenance files are preserved. Mixed-runtime corresponding-source
  review remains incomplete, with REVIEW-PENDING.md retained. No public release is claimed.
- Source checks: 8 Python packaging tests and 6 Swift Foundation checks passed;
  all shell scripts parse. Source extraction rejects traversal, escaping links
  and existing destination symlinks. The runtime environment disables system
  GStreamer plugin discovery and writes its registry into app data.

## Final transferable bundle checks

The updated app is built separately at dist/host-test/RDR2Launcher.app so the active
Windows Steam client keeps its original runtime path. It contains the selected engine,
renderer and media stack, but no game/client/account files. The final copied-bundle,
media, signature and archive verification results are recorded below after execution.

Observed final results:

| Check | Actual outcome |
| --- | --- |
| Runtime-inclusive app | 1.1 GiB bundle at dist/host-test/RDR2Launcher.app |
| Static dependency audit | 153 Mach-O files; zero failures |
| Nested/outer ad-hoc signing | codesign deep/strict verification passed |
| Runtime checksums in relocated app | Passed; engine x64-crossover26.3-r27; Rosetta available |
| Path with spaces + cleared environment | Complete copied bundle starts its own Wine |
| Fresh private wineboot + Windows cmd | Passed; Windows 10.0.19045 reported |
| Wine media registration | winegstreamer.dll registered successfully |
| GStreamer helper and bundled libav discovery | Passed; version 1.28.7, 426 plugin features |
| x86_64 RTLD_NOW probes | FFmpeg and GStreamer libraries loaded successfully |
| Disposable service cleanup | Only the smoke test's new prefix stopped; active download preserved |
| Source checks | 8 Python tests + 6 Swift checks passed; shell syntax passed |
| Development archive | SHA-256 and per-entry CRC verified; account/game/client exclusion checked |
| Public release gate | Expected refusal: real acceptance evidence is incomplete |

The copied test lives under a temporary Path With Spaces directory. It proves the
selected runtime executes from its relocated bundle on this build Mac, not a
separate-host Finder/Gatekeeper result. No Highball/Homebrew/global Wine tool or
developer PATH was used to run Wine. The build-only dlopen probe compiler is not
part of the host app or a host prerequisite.

## Acceptance still open

RDR2 download/verification completion, Rockstar sign-in, game startup, controllable
Story Mode/FPS, separate-host Finder/Gatekeeper, real app replacement persistence,
Developer ID/notarization and complete redistribution/source compliance remain open.
The host app needs no separately installed build tools; a separate clean-host test
is required to prove that property in actual use. Apple-managed Rosetta and official
client authentication/download remain expected first-run steps.
