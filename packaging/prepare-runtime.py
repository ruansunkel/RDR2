#!/usr/bin/env python3
"""Download checksum-pinned official components; never execute vendor code.

This creates a NEW staging directory only. It does not import any Wine prefix.
"""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile
from urllib.parse import urlparse
from runtime_tools import sha256

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ('wine', 'runtime', 'dxmt', 'moltenvk', 'nvapi-stub', 'audiobuf')


def excluded(parts):
    return any(p.lower() in {'d3dmetal', 'd3dmetal.framework', 'd3dmetal-tsshim'} for p in parts)


def extract_component(archive, component, destination):
    """Extract only selected subtree; reject traversal, devices and escaping links."""
    subpath = PurePosixPath(component['extract']['subpath'])
    into = PurePosixPath(component['extract']['into'])
    if any(p.is_absolute() or '..' in p.parts for p in [subpath, into]):
        raise ValueError('Unsafe extraction mapping')
    with tarfile.open(archive) as tar:
        selected = []
        for member in tar.getmembers():
            name = PurePosixPath(member.name)
            if name.is_absolute() or '..' in name.parts:
                raise ValueError('Unsafe archive member')
            try:
                suffix = name.relative_to(subpath)
            except ValueError:
                continue
            target = destination / into / suffix
            if excluded(target.relative_to(destination).parts):
                continue
            if not (member.isfile() or member.isdir() or member.issym()):
                raise ValueError(f'Unsupported archive member type: {name}')
            if member.issym():
                link = PurePosixPath(member.linkname)
                resolved = Path(os.path.normpath(target.parent / str(link)))
                if link.is_absolute() or not resolved.is_relative_to(destination):
                    raise ValueError(f'Escaping archive link: {name}')
            selected.append((member, target))
        if not selected:
            raise ValueError(f'Archive lacks {subpath}')
        # Files/directories first, symlinks last; no write can traverse an archive-created link.
        for member, target in sorted(selected, key=lambda item: item[0].issym()):
            parent = target.parent
            parent.mkdir(parents=True, exist_ok=True)
            if any(p.is_symlink() for p in [target, *target.parents] if p.is_relative_to(destination)):
                raise ValueError(f'Extraction would overwrite/traverse symlink: {target}')
            if member.isdir():
                target.mkdir(exist_ok=True)
            elif member.issym():
                target.symlink_to(member.linkname)
            else:
                with tar.extractfile(member) as src, target.open('wb') as dst:
                    shutil.copyfileobj(src, dst)
                target.chmod(member.mode & 0o777)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path, help='new runtime directory (must not exist)')
    parser.add_argument('--cache', type=Path, default=ROOT / 'vendor/downloads')
    args = parser.parse_args()
    dest = args.destination.absolute()
    if dest.exists():
        parser.error('Destination already exists. Choose a new staging directory; no files will be deleted.')
    manifest = json.loads((ROOT / 'config/engine-upstream.json').read_text())
    cache = args.cache.absolute()
    cache.mkdir(parents=True, exist_ok=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='rdr2-stage-', dir=dest.parent) as scratch:
        stage = Path(scratch) / 'runtime'
        stage.mkdir()
        for name in sorted(COMPONENTS, key=lambda n: (manifest['components'][n].get('order', 0), n)):
            component = manifest['components'][name]
            url = component['url']
            parsed = urlparse(url)
            if parsed.scheme != 'https' or parsed.hostname != 'github.com':
                raise ValueError('Component source is not the pinned official GitHub release')
            archive = cache / component['sha256']
            if not archive.exists():
                partial = archive.with_suffix('.partial')
                subprocess.run(['/usr/bin/curl', '--fail', '--location', '--proto', '=https',
                                '--proto-redir', '=https', '--retry', '2', '--output', str(partial), url], check=True)
                if sha256(partial) != component['sha256']:
                    raise ValueError(f'Checksum mismatch: {name}')
                partial.rename(archive)
            if sha256(archive) != component['sha256']:
                raise ValueError(f'Cached checksum mismatch: {name}')
            print(f'Verified {name}: {component["sha256"]}', flush=True)
            extract_component(archive, component, stage)
        # Match Highball EngineStore.linkRuntime: patched framework dylibs win over GStreamer copies.
        lib = stage / 'engine/lib'
        for directory in [stage / 'frameworks', stage / 'frameworks/GStreamer.framework/Versions/1.0/lib']:
            for path in sorted(directory.glob('*.dylib')):
                target = lib / path.name
                if not target.exists() and not target.is_symlink():
                    target.symlink_to(os.path.relpath(path, lib))
        framework = lib / 'GStreamer.framework'
        if not framework.exists() and not framework.is_symlink():
            framework.symlink_to('../../frameworks/GStreamer.framework')
        # Explicit source/notice review remains required before build-app accepts this stage.
        shutil.copy2(ROOT / 'config/engine-upstream.json', stage / 'manifest.json')
        stage.rename(dest)
    print(f'Staged {dest}. Review notices/corresponding source, add licenses/, then audit and validate.')


if __name__ == '__main__':
    main()
