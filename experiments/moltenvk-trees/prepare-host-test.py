#!/usr/bin/env python3
"""APFS-clone an idle host control environment into a new candidate data folder."""
from contextlib import ExitStack
from pathlib import Path
import argparse
import datetime
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import time
import uuid


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''): h.update(data)
    return h.hexdigest()


def inventory(root):
    result = {}
    for p in root.rglob('*'):
        if p.is_symlink(): result[str(p.relative_to(root))] = ['link', str(p.readlink())]
        elif p.is_file(): result[str(p.relative_to(root))] = ['file', p.stat().st_size]
        elif p.is_dir(): result[str(p.relative_to(root))] = ['directory']
    return result


def processes():
    rows = subprocess.check_output(['/bin/ps', '-axo', 'pid=,comm='], text=True)
    return {int(p): name for p, name in (line.strip().split(None, 1) for line in rows.splitlines() if line.strip())}


def main():
    support = Path.home() / 'Library/Application Support'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=support / 'RDR2Launcher-MoltenVK-Control')
    parser.add_argument('--destination', type=Path, default=support / 'RDR2Launcher-MoltenVK-Candidate')
    parser.add_argument('--control-app', type=Path, required=True)
    parser.add_argument('--candidate-app', type=Path, required=True)
    parser.add_argument('--launch', action='store_true')
    args = parser.parse_args()
    source, target = args.source.resolve(), args.destination.absolute()
    if (target.exists() or target.is_symlink() or not source.is_dir() or
            target.is_relative_to(source) or source.is_relative_to(target)):
        parser.error('Source must exist and destination must be new and separate')
    source_session = json.loads((source / 'state/session.json').read_text())
    if source_session.get('pendingTimeZoneBackup'):
        parser.error('Finish source timezone repair before copying')
    library = Path(source_session['library']).resolve()
    if library != source / 'SteamLibrary':
        parser.error('This host-copy procedure expects the library inside the control data folder')
    candidate_resources = args.candidate_app.resolve() / 'Contents/Resources'
    profile = json.loads((candidate_resources / 'tree-candidate.json').read_text())
    if profile.get('default_data_directory') != target.name or profile.get('candidate_patch_included') is not True:
        parser.error('Candidate profile does not match the intended destination')
    rows = processes()
    if any(re.search(r'(?:^|[\\/])(?:steam|steamwebhelper|Launcher|SocialClubHelper|RockstarService|PlayRDR2|RDR2)\.exe$', name, re.I) for name in rows.values()):
        parser.error('Close the Windows clients/game normally before copying; none were stopped')
    control_executable = str(args.control_app.resolve() / 'Contents/MacOS/RDR2Launcher')
    for pid, name in rows.items():
        if name == control_executable and processes().get(pid) == control_executable:
            os.kill(pid, signal.SIGTERM)
            for _ in range(30):
                if pid not in processes(): break
                time.sleep(0.1)
            else: raise RuntimeError('Control launcher did not close; no files copied')
    tag = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    stage = target.parent / ('.' + target.name + '-staging-' + tag)
    with (source / 'state/launcher.lock').open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        registry = {name: digest(source / 'prefixes/default' / name) for name in ['system.reg', 'user.reg', 'userdef.reg']}
        source_prefix = inventory(source / 'prefixes')
        source_game = inventory(library / 'steamapps/common/Red Dead Redemption 2')
        subprocess.run(['/bin/cp', '-cR', str(source), str(stage)], check=True)
        if inventory(stage / 'prefixes') != source_prefix or inventory(stage / 'SteamLibrary/steamapps/common/Red Dead Redemption 2') != source_game:
            raise RuntimeError('Copied prefix/game inventory differs; candidate was not activated')
        for name, expected in registry.items():
            if digest(source / 'prefixes/default' / name) != expected or digest(stage / 'prefixes/default' / name) != expected:
                raise RuntimeError('Registry changed during snapshot')
        new_library = target / 'SteamLibrary'
        old_windows, new_windows = ('Z:' + str(p).replace('/', '\\') for p in [library, new_library])
        steam = stage / 'prefixes/default/drive_c/Program Files (x86)/Steam'
        for relative in ['steamapps/libraryfolders.vdf', 'config/libraryfolders.vdf']:
            file = steam / relative
            hits = [0]
            def rewrite(match):
                path = re.sub(r'\\([\\"])', lambda m: m.group(1), match.group(2))
                if path.casefold() != old_windows.casefold(): return match.group(0)
                hits[0] += 1
                return match.group(1) + new_windows.replace('\\', '\\\\') + match.group(3)
            file.write_text(re.sub(r'("path"\s+")((?:[^"\\]|\\.)*)(")', rewrite, file.read_text()))
            if hits[0] != 1: raise RuntimeError('Expected one copied external Steam library')
        drive = stage / 'prefixes/default/dosdevices/r:'
        if not drive.is_symlink() or drive.readlink() != library:
            raise RuntimeError('Copied R: mapping differs')
        drive.unlink(); drive.symlink_to(new_library, target_is_directory=True)
        source_session['library'] = str(new_library)
        source_session['stage'] = 'needs_steam_login'
        (stage / 'state/session.json').write_text(json.dumps(source_session))
        (stage / 'state/selected-environment.json').write_text(json.dumps({'environment': {'dataRoot': str(target), 'usePrivateHome': (stage / 'build-test-home').is_dir()}}))
        save_count = 0
        for user in (source / 'prefixes/default/drive_c/users').iterdir():
            profiles = user / 'Documents/Rockstar Games/Red Dead Redemption 2/Profiles'
            if not profiles.is_dir(): continue
            saved = stage / 'backups' / ('pre-candidate-saves-' + tag) / user.name / 'Profiles'
            saved.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(['/bin/cp', '-cR', str(profiles), str(saved)], check=True)
            for file in profiles.rglob('*'):
                if file.is_file() and not file.is_symlink():
                    if digest(file) != digest(saved / file.relative_to(profiles)):
                        raise RuntimeError('Save backup checksum differs')
                    save_count += 1
        for item in (stage / 'prefixes').rglob('*'):
            if item.is_symlink():
                link = Path(item.readlink())
                if link.is_absolute() and link.is_relative_to(source):
                    raise RuntimeError('Copied prefix still links to the control environment')
        files = [entry for entry in source_game.values() if entry[0] == 'file']
        report = {'source': str(source), 'destination': str(target), 'game_files': len(files),
                  'game_bytes': sum(entry[1] for entry in files), 'save_backup_files': save_count,
                  'prefix_and_game_inventory_verified': True, 'registry_checksums_verified': True,
                  'source_preserved': True, 'candidate_dylib_sha256': profile['candidate_dylib_sha256']}
        (stage / 'state/candidate-host-copy.json').write_text(json.dumps(report, indent=2) + '\n')
        if target.exists(): raise RuntimeError('Candidate destination appeared during preparation')
        stage.rename(target)
    print('Candidate environment ready:', target, flush=True)
    print('Local game files verified:', len(files), '; backed-up save files:', save_count, flush=True)
    if args.launch:
        subprocess.run(['/usr/bin/open', '-n', str(args.candidate_app.resolve()), '--args', '--play-game'], check=True)
        print('Opened the separate candidate launcher and requested Play.', flush=True)


if __name__ == '__main__':
    main()
