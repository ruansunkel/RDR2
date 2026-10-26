#!/usr/bin/env python3
"""Close only an idle candidate Wine session and launch a new candidate app."""
import argparse
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import hashlib
import re


def processes():
    rows = subprocess.check_output(['/bin/ps', '-axo', 'pid=,comm='], text=True).splitlines()
    return {int(pid): name for pid, name in (line.strip().split(None, 1) for line in rows if line.strip())}


def refuse_running_game(idle_candidate=None):
    for pid, name in processes().items():
        base = name.replace('\\', '/').rsplit('/', 1)[-1].lower()
        if base not in ['rdr2.exe', 'playrdr2.exe']:
            continue
        if base == 'playrdr2.exe' and idle_candidate and idle_candidate.name in name:
            # Rockstar can leave this bootstrap process after RDR2 exits. Only
            # permit an old candidate bootstrap during an explicit diagnostic
            # relaunch; a real RDR2 or recent/other-prefix launch still refuses.
            elapsed = subprocess.check_output(['/bin/ps', '-p', str(pid), '-o', 'etime='], text=True).strip()
            days, clock = elapsed.split('-', 1) if '-' in elapsed else ('0', elapsed)
            fields = [int(value) for value in clock.split(':')]
            seconds = int(days) * 86400 + sum(value * (60 ** i) for i, value in enumerate(reversed(fields)))
            if seconds >= 180 and processes().get(pid) == name:
                print('An old candidate PlayRDR2 bootstrap remains; requesting normal client shutdown.', flush=True)
                continue
        raise RuntimeError('A game is running/launching. Save and quit it normally before switching.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-app', required=True, type=Path)
    parser.add_argument('--to-app', required=True, type=Path)
    parser.add_argument('--data-root', type=Path, default=Path.home() / 'Library/Application Support/RDR2Launcher-MoltenVK-Candidate')
    parser.add_argument('--capture-session', action='store_true',
                        help='relaunch the same isolated renderer with Apple capture enabled; no automatic capture or debugger')
    args = parser.parse_args()
    old, new, data = args.from_app.resolve(), args.to_app.resolve(), args.data_root.resolve()
    if (old == new and not args.capture_session) or data.name != 'RDR2Launcher-MoltenVK-Candidate':
        parser.error('Choose distinct candidate apps (or --capture-session) and the explicit candidate data folder')
    if args.capture_session and old != new:
        parser.error('A capture session preserves the current app/renderer; use matching from/to apps')
    for app in [old, new]:
        profile = json.loads((app / 'Contents/Resources/tree-candidate.json').read_text())
        if profile.get('default_data_directory') != data.name or profile.get('candidate_patch_included') is not True:
            parser.error('App profile does not match the isolated candidate environment')
    selection = json.loads((data / 'state/selected-environment.json').read_text())['environment']
    if Path(selection['dataRoot']).resolve() != data:
        parser.error('Candidate selection points outside the expected test environment')
    refuse_running_game(idle_candidate=data if args.capture_session else None)
    subprocess.run([str(new / 'Contents/MacOS/RDR2Launcher'), '--diagnose'],
                   stdout=subprocess.DEVNULL, check=True, timeout=40)
    resources = old / 'Contents/Resources'
    manifest = json.loads((resources / 'runtime-manifest.json').read_text())
    frameworks = str(resources / 'runtime/frameworks')
    env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
           'HOME': str(data / 'build-test-home') if selection.get('usePrivateHome') else str(Path.home()),
           'TMPDIR': tempfile.gettempdir(), 'WINEPREFIX': str(data / 'prefixes/default'),
           'WINEDEBUG': '-all', 'WINEMSYNC': '0', 'WINEESYNC': '0',
           'WINEDLLOVERRIDES': 'winemenubuilder.exe=d',
           'WINEDLLPATH_PREPEND': str(resources / 'runtime/renderers/dxmt/wine')}
    env.update({k: v.replace('${frameworks}', frameworks) for k, v in manifest['baseEnv'].items() if k != 'WINEDEBUG'})
    wine = resources / manifest['wine']
    server = resources / 'runtime/engine/bin/wineserver'
    steam = data / 'prefixes/default/drive_c/Program Files (x86)/Steam/steam.exe'
    common = {'env': env, 'cwd': data, 'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}
    print('Requesting a normal shutdown of the candidate Steam client.', flush=True)
    subprocess.run([str(wine), str(steam), '-shutdown'], timeout=30, **common)
    refuse_running_game(idle_candidate=data if args.capture_session else None)
    print('Requesting Windows shutdown only inside the candidate prefix.', flush=True)
    subprocess.run([str(wine), 'wineboot', '--shutdown'], timeout=35, check=True, **common)
    subprocess.run([str(server), '-w'], timeout=20, check=True, **common)
    print('Candidate Wine session closed; registry/saves flushed.', flush=True)
    old_executable = str(old / 'Contents/MacOS/RDR2Launcher')
    for pid, name in processes().items():
        if name == old_executable and processes().get(pid) == old_executable:
            os.kill(pid, signal.SIGTERM)
            for _ in range(30):
                if pid not in processes(): break
                time.sleep(0.1)
            else: raise RuntimeError('Old native launcher remains open; no new launch attempted')
    tag = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    checkpoint = data / 'backups' / ('before-app-switch-' + tag)
    checkpoint.mkdir(parents=True, mode=0o700)
    for name in ['system.reg', 'user.reg', 'userdef.reg']:
        subprocess.run(['/bin/cp', '-c', str(data / 'prefixes/default' / name), str(checkpoint / name)], check=True)
    save_count = 0
    for user in (data / 'prefixes/default/drive_c/users').iterdir():
        profiles = user / 'Documents/Rockstar Games/Red Dead Redemption 2/Profiles'
        if not profiles.is_dir(): continue
        saved = checkpoint / 'saves' / user.name / 'Profiles'
        saved.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['/bin/cp', '-cR', str(profiles), str(saved)], check=True)
        for file in profiles.rglob('*'):
            if file.is_file() and not file.is_symlink():
                original = hashlib.sha256(file.read_bytes()).digest()
                copied = hashlib.sha256((saved / file.relative_to(profiles)).read_bytes()).digest()
                if original != copied: raise RuntimeError('Flushed save backup checksum differs; no new launch attempted')
                save_count += 1
    (checkpoint / 'switch.json').write_text(json.dumps({'from_app': str(old), 'to_app': str(new),
        'data_root': str(data), 'game_was_not_running': True, 'candidate_session_closed_normally': True,
        'verified_save_backup_files': save_count, 'capture_session': args.capture_session}, indent=2) + '\n')
    if args.capture_session:
        # Set the native Wine child's environment explicitly. The GUI intentionally
        # does not inherit arbitrary shell variables. Never wait-for-signal in a game.
        env.update(MTL_CAPTURE_ENABLED='1', MVK_CONFIG_AUTO_GPU_CAPTURE_SCOPE='0',
                   RDR2_MVK_DEDICATED_BUFFER_NO_HEAP='1' if profile.get('allocation_option_enabled') else '0',
                   RDR2_MVK_ALLOCATION_MARKER_FILE=str(data / 'state/tree-allocation-events.log'),
                   GST_PLUGIN_SYSTEM_PATH_1_0='',
                   GST_PLUGIN_SCANNER=frameworks + '/GStreamer.framework/Versions/1.0/libexec/gstreamer-1.0/gst-plugin-scanner',
                   GST_REGISTRY_1_0=str(data / 'state/gstreamer-registry.bin'))
        subprocess.Popen([str(wine), str(steam)], start_new_session=True, **common)
        service_args = [str(wine), 'sc', 'query', 'Rockstar Service']
        query = subprocess.run(service_args, env=env, cwd=data, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, timeout=25)
        running = lambda text: re.search(r'\bSTATE\s*:\s*4\s+RUNNING\b', text) is not None
        if not running(query.stdout):
            subprocess.run([str(wine), 'sc', 'start', 'Rockstar Service'], timeout=25, check=True, **common)
            deadline = time.monotonic() + 12
            while time.monotonic() < deadline:
                query = subprocess.run(service_args, env=env, cwd=data, stdout=subprocess.PIPE,
                                       stderr=subprocess.DEVNULL, text=True, timeout=15)
                if running(query.stdout):
                    break
                time.sleep(0.3)
            if not running(query.stdout):
                raise RuntimeError('Rockstar service did not start; no game launch requested')
        subprocess.Popen([str(wine), str(steam), '-applaunch', '1174180'], start_new_session=True, **common)
        (data / 'state/gpu-capture-session.json').write_text(json.dumps({
            'app': str(new), 'renderer_sha256': hashlib.sha256((new / 'Contents/Resources/runtime/frameworks/libMoltenVK.dylib').read_bytes()).hexdigest(),
            'capture_enabled_requested': True, 'automatic_capture_scope': 0,
            'debugger_attached': False, 'verified_save_backup_files': save_count,
            'capturable_game_verified': False}, indent=2) + '\n')
        print('Requested the same game/renderer with Apple capture enabled. Actual capturability still needs verification.', flush=True)
    else:
        subprocess.run(['/usr/bin/open', '-n', str(new), '--args', '--play-game'], check=True)
        print('Opened the new candidate app using the same local game/save copy.', flush=True)


if __name__ == '__main__':
    main()
