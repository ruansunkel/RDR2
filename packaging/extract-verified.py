#!/usr/bin/env python3
"""Safely extract a checksum-pinned media source archive/bottle to a new directory."""
import argparse
import json
import os
from pathlib import Path
import tarfile
from runtime_tools import sha256

ROOT = Path(__file__).resolve().parents[1]


def extract(archive, destination):
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        for member in members:
            path = Path(member.name)
            if path.is_absolute() or '..' in path.parts or member.isdev() or member.islnk():
                raise ValueError('Unsafe archive member')
            if member.issym():
                target = Path(os.path.normpath(destination / path.parent / member.linkname))
                if Path(member.linkname).is_absolute() or not target.is_relative_to(destination):
                    raise ValueError('Escaping archive link')
        # Symlinks last, and no extraction can traverse an earlier link.
        for member in sorted(members, key=lambda item: item.issym()):
            path = destination / member.name
            if any(p.is_symlink() for p in [path, *path.parents] if p.is_relative_to(destination)):
                raise ValueError('Extraction would traverse an existing symlink')
            if not (member.isfile() or member.isdir() or member.issym()):
                raise ValueError('Unsupported archive entry')
            tar.extract(member, destination)


def main():
    sources = json.loads((ROOT / 'config/media-sources.json').read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('component', choices=sorted(sources))
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    dest = args.destination.resolve()
    if dest.exists():
        parser.error('Choose a new destination')
    item = sources[args.component]
    archive = ROOT / 'vendor/downloads' / item['sha256']
    if sha256(archive) != item['sha256']:
        raise ValueError('Input checksum mismatch')
    dest.mkdir(parents=True)
    extract(archive, dest)
    print(f'Verified and extracted {args.component} to {dest}')


if __name__ == '__main__':
    main()
