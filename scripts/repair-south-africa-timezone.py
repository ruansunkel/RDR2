#!/usr/bin/env python3
"""Build-Mac recovery for Wine 11's incorrect UTC+2 Windows timezone selection.

Dry-run by default. --apply moves ONLY the three verified conflicting timezone
definitions to a timestamped backup registry area in the chosen game prefix.
macOS settings, game files, credentials and other prefixes are untouched.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import shlex

SEP = chr(92)
ZONES = r'HKLM\Software\Microsoft\Windows NT\CurrentVersion\Time Zones'
INFO = r'HKLM\System\CurrentControlSet\Control\TimeZoneInformation'
CONFLICTS = ['Kaliningrad Standard Time', 'Libya Standard Time', 'Namibia Standard Time']
TARGET = 'South Africa Standard Time'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--data-directory', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--restore', type=Path, help='restore only the definitions listed in a recovery.json journal')
    args = parser.parse_args()
    if args.apply and args.restore:
        parser.error('Choose apply or restore, not both')
    if not args.restore and not str(Path('/etc/localtime').resolve()).endswith('/Africa/Johannesburg'):
        parser.error('This scoped recovery is only for a Mac set to Africa/Johannesburg')
    root = args.data_directory.resolve()
    prefix = root / 'prefixes/default'
    runtime = args.app.resolve() / 'Contents/Resources/runtime'
    if not (prefix / 'system.reg').is_file() or not (prefix / 'drive_c/Program Files (x86)/Steam/steam.exe').is_file():
        parser.error('Choose the existing launcher data folder containing the game Steam environment')
    env = {'HOME': str(root / 'build-test-home') if (root / 'build-test-home').exists() else str(Path.home()),
           'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'TMPDIR': '/tmp/', 'WINEPREFIX': str(prefix),
           'WINEDEBUG': '-all', 'WINEMSYNC': '0', 'WINEESYNC': '0', 'WINEDLLOVERRIDES': 'winemenubuilder.exe=d',
           'WINEDLLPATH_PREPEND': str(runtime / 'renderers/dxmt/wine')}
    manifest = json.loads((runtime / 'manifest.json').read_text())
    env.update({k: v.replace('${frameworks}', str(runtime / 'frameworks'))
                for k, v in manifest['baseEnv'].items() if k != 'WINEDEBUG'})
    wine = runtime / 'engine/bin/wine'

    def reg(*command, required=True):
        # Wine's desktop/service helpers can retain inherited pipe handles after
        # reg.exe exits. A regular output file does not wait for those helpers' EOF.
        with tempfile.TemporaryFile(mode='w+', encoding='utf-8') as output:
            child = subprocess.run([str(wine), 'reg', *command], env=env, stdout=output,
                                   stderr=subprocess.DEVNULL, timeout=60)
            output.seek(0)
            result = SimpleNamespace(returncode=child.returncode, stdout=output.read())
        if required and result.returncode:
            raise RuntimeError('Registry operation failed: ' + ' '.join(command[:2]))
        return result

    if args.restore:
        saved = json.loads(args.restore.read_text())
        key = saved.get('backup_registry_key', '')
        expected = SEP.join(['HKLM', 'Software', 'RDR2Launcher', 'TimezoneBackups'])
        parent, _, tag = key.rpartition(SEP)
        names = saved.get('moved', [])
        if (Path(saved.get('prefix', '')).resolve() != prefix or parent != expected or not tag
                or not all(c.isascii() and (c.isalnum() or c == '-') for c in tag)
                or not isinstance(names, list) or any(n not in CONFLICTS for n in names)):
            parser.error('Journal does not match the selected prefix or allowed timezone backup')
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        shutil.copy2(prefix / 'system.reg', prefix / ('system.reg.backup-timezone-restore-' + stamp))
        for name in names:
            reg('copy', key + SEP + name, ZONES + SEP + name, '/s', '/f')
        print('Restored only the original timezone definitions; no prefix/game/account reset was performed.')
        return

    before = reg('query', INFO, '/v', 'TimeZoneKeyName').stdout
    print(before.strip(), flush=True)
    if TARGET in before:
        print('Already reports South Africa; no changes needed.')
        return
    if 'Kaliningrad Standard Time' not in before:
        parser.error('Unexpected detected zone; this targeted workaround was not applied')
    reg('query', ZONES + SEP + TARGET, '/v', 'TZI')
    for name in CONFLICTS:
        reg('query', ZONES + SEP + name, '/v', 'TZI')
        print('Proposed move in this prefix only:', ZONES + SEP + name, flush=True)
    if not args.apply:
        print('Dry run only. --apply preserves registry/file backups and verifies the new Windows name.')
        return
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = root / 'state' / ('timezone-repair-' + stamp)
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(prefix / 'system.reg', backup / 'system.reg.backup')
    backup_key = r'HKLM\Software\RDR2Launcher\TimezoneBackups' + SEP + stamp
    moved = []
    journal = {'prefix': str(prefix), 'target': TARGET, 'backup_registry_key': backup_key,
               'moved': moved, 'macos_timezone_unchanged': True}
    try:
        # Make and verify every copy before removing ANY definition from matching.
        for name in CONFLICTS:
            reg('copy', ZONES + SEP + name, backup_key + SEP + name, '/s', '/f')
            original = reg('query', ZONES + SEP + name, '/v', 'TZI').stdout
            copied = reg('query', backup_key + SEP + name, '/v', 'TZI').stdout
            if original.split('REG_BINARY', 1)[1].strip() != copied.split('REG_BINARY', 1)[1].strip():
                raise RuntimeError('Timezone backup verification failed')
        for name in CONFLICTS:
            reg('delete', ZONES + SEP + name, '/f')
            moved.append(name)
        after = reg('query', INFO, '/v', 'TimeZoneKeyName').stdout
        print(after.strip(), flush=True)
        if TARGET not in after:
            raise RuntimeError('Wine did not select South Africa; restoring definitions')
        journal['verified_windows_timezone'] = TARGET
    except Exception:
        for name in moved:
            reg('copy', backup_key + SEP + name, ZONES + SEP + name, '/s', '/f')
        journal['rolled_back'] = True
        raise
    finally:
        (backup / 'recovery.json').write_text(json.dumps(journal, indent=2) + '\n')
    restore = ['Restore only the moved definitions with the correct bundled engine and prefix:',
               shlex.join(['python3', str(Path(__file__).resolve()), '--app', str(args.app.resolve()),
                           '--data-directory', str(root), '--restore', str(backup / 'recovery.json')])]
    (backup / 'RESTORE.txt').write_text('\n'.join(restore) + '\n')
    print('Verified South Africa timezone. Backups:', backup, flush=True)
    print('Restart Rockstar before retrying sign-in; authentication success is not assumed.', flush=True)


if __name__ == '__main__':
    main()
