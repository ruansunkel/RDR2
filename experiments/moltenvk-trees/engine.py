#!/usr/bin/env python3
"""Manage a NEW isolated Highball home; never patch an existing/shared engine."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from build import PINS, digest

TEST_ID = PINS['engine_id'] + '-rdr2-tree-test'
MARKER = '.rdr2-tree-test.json'


def write_json(path, value):
    fd, temporary = tempfile.mkstemp(prefix='.journal-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def contained(path, root):
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError('Path escapes the isolated home: ' + str(path))
    return resolved


def clone(source, home):
    if home.is_symlink():
        raise ValueError('Test home must be a new directory, not a link')
    source, home = source.resolve(), home.resolve()
    if home.exists() or home.is_relative_to(source) or source.is_relative_to(home):
        raise ValueError('Choose a NEW test home separate from the source engine')
    manifest = json.loads((source / 'manifest.json').read_text())
    library = source / 'frameworks/libMoltenVK.dylib'
    if (manifest.get('id') != PINS['engine_id'] or not (source / 'engine/bin/wine').is_file() or
            digest(library) != PINS['moltenvk']['reference_dylib_sha256']):
        raise ValueError('Source is not the pinned r27 engine/dylib; no copy was made')
    for path in source.rglob('*'):
        if path.is_symlink():
            contained(path, source)
    root = home / 'engines' / TEST_ID
    root.parent.mkdir(parents=True, mode=0o700)
    shutil.copytree(source, root, symlinks=True)
    copied = root / 'frameworks/libMoltenVK.dylib'
    if digest(copied) != PINS['moltenvk']['reference_dylib_sha256']:
        raise ValueError('Copied dylib checksum differs')
    shutil.copy2(root / 'manifest.json', root / 'manifest.json.original')
    manifest['id'] = TEST_ID
    write_json(root / 'manifest.json', manifest)
    rollback = home / 'rollback'
    rollback.mkdir(mode=0o700)
    backup = rollback / 'libMoltenVK.original.dylib'
    shutil.copy2(copied, backup)
    value = digest(backup)
    write_json(home / MARKER, {'schema': 1, 'engine_id': TEST_ID, 'source': str(source),
                             'original_sha256': value, 'installed_sha256': value})
    return root


def load(home):
    home = home.resolve()
    journal = json.loads((home / MARKER).read_text())
    if journal.get('schema') != 1 or journal.get('engine_id') != TEST_ID:
        raise ValueError('Not a test home created by this tool')
    library = contained(home / 'engines' / TEST_ID / 'frameworks/libMoltenVK.dylib', home)
    backup = contained(home / 'rollback/libMoltenVK.original.dylib', home)
    if digest(backup) != journal['original_sha256']:
        raise ValueError('Rollback backup checksum differs; no change was made')
    current = digest(library)
    if current not in [journal['installed_sha256'], journal.get('pending_sha256')]:
        raise ValueError('Installed dylib changed outside this journal; no change was made')
    return library, backup, journal


def assert_not_loaded(library):
    result = subprocess.run(['/usr/sbin/lsof', '-t', str(library)], text=True, capture_output=True)
    if result.stdout.strip():
        raise ValueError('Test dylib is in use. Quit only the test environment normally before replacing it.')
    if result.returncode not in (0, 1) or result.stderr.strip():
        raise ValueError('Could not establish that the test dylib is unused')


def replace(home, incoming, expected):
    home = home.resolve()
    library, backup, journal = load(home)
    if digest(incoming) != expected:
        raise ValueError('Incoming dylib checksum differs; no change was made')
    assert_not_loaded(library)
    # Journal before replacing. Rollback accepts old OR pending bytes after an interruption.
    journal['pending_sha256'] = expected
    write_json(home / MARKER, journal)
    fd, temp = tempfile.mkstemp(prefix='.moltenvk-', dir=library.parent)
    os.close(fd)
    try:
        shutil.copy2(incoming, temp)
        if digest(temp) != expected:
            raise ValueError('Copy checksum differs')
        os.replace(temp, library)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    journal['installed_sha256'] = expected
    journal.pop('pending_sha256', None)
    write_json(home / MARKER, journal)


def prove_loaded(home, pid):
    if pid <= 0:
        raise ValueError('Choose the actual game process PID')
    library, _, _ = load(home)
    result = subprocess.run(['/usr/sbin/lsof', '-a', '-p', str(pid), '-Fn'],
                            check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    paths = [Path(line[1:]) for line in result.stdout.splitlines()
             if line.startswith('n') and 'MoltenVK' in line and line[1:].endswith('.dylib')]
    if not paths or not any(path.resolve() == library for path in paths):
        raise ValueError('No loaded mapping of this isolated MoltenVK dylib was found')
    return {'pid': pid, 'loaded_dylib': str(library), 'loaded_dylib_sha256': digest(library)}


def backup_saves(source, destination):
    source = source.resolve()
    destination = destination.resolve()
    if source.name != 'Profiles' or source.parent.name != 'Red Dead Redemption 2':
        raise ValueError('Select only RDR2/Profiles, not a Wine prefix or launcher profile')
    if (not source.is_dir() or destination.exists() or destination.is_relative_to(source) or
            source.is_relative_to(destination)):
        raise ValueError('Profiles must exist and backup destination must be new')
    if any(path.is_symlink() for path in source.rglob('*')):
        raise ValueError('Save backup contains links; inspect them before copying')
    shutil.copytree(source, destination)
    destination.chmod(0o700)
    for path in destination.rglob('*'):
        path.chmod(0o700 if path.is_dir() else 0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    copy = sub.add_parser('clone')
    copy.add_argument('--source', required=True, type=Path)
    copy.add_argument('--test-home', required=True, type=Path)
    for command in ['install', 'rollback', 'prove-loaded']:
        child = sub.add_parser(command)
        child.add_argument('--test-home', required=True, type=Path)
        if command == 'install':
            child.add_argument('--artifact', required=True, type=Path, help='build.py output directory')
        if command == 'prove-loaded':
            child.add_argument('--pid', required=True, type=int)
    saves = sub.add_parser('backup-saves')
    saves.add_argument('--profiles', required=True, type=Path)
    saves.add_argument('--destination', required=True, type=Path)
    args = parser.parse_args()
    if args.command == 'clone':
        print('New isolated engine:', clone(args.source, args.test_home))
    elif args.command == 'backup-saves':
        backup_saves(args.profiles, args.destination)
        print('Private save backup created; no prefix/account data copied.')
    else:
        home = args.test_home.resolve()
        if args.command == 'install':
            metadata = json.loads((args.artifact / 'build.json').read_text())
            library = args.artifact / 'libMoltenVK.dylib'
            if metadata.get('engine_id') != PINS['engine_id'] or metadata.get('architecture') != 'x86_64':
                raise ValueError('Artifact engine/architecture differs')
            if subprocess.check_output(['lipo', '-archs', str(library)], text=True).split() != ['x86_64']:
                raise ValueError('Artifact is not an x86_64 dylib')
            subprocess.run(['codesign', '--verify', '--strict', str(library)], check=True)
            replace(home, library, metadata['sha256'])
            print('Installed only in the new test engine:', load(home)[0])
        elif args.command == 'rollback':
            _, backup, journal = load(home)
            replace(home, backup, journal['original_sha256'])
            print('Original dylib restored; checksum verified:', digest(load(home)[0]))
        else:
            print(json.dumps(prove_loaded(home, args.pid), indent=2))


if __name__ == '__main__':
    try:
        main()
    except ValueError as error:
        sys.exit(str(error))
