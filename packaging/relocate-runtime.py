#!/usr/bin/env python3
"""Create a new relocatable development stage from verified upstream artifacts.

Changes are restricted to load paths/IDs, recorded with before/after hashes, and
ad-hoc re-signed. No machine-wide files, existing prefixes or game files change.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from runtime_tools import macho, sha256, system_path

ROOT = Path(__file__).resolve().parents[1]


def copy_runtime(source, destination):
    def ignore(directory, names):
        path = Path(directory)
        if path == source / 'frameworks':
            return set(names) & {'renderer', 'GStreamer.framework', 'SikarugirSdk.framework', 'moltenvkcx'}
        # Recreate framework aliases from the replacement libraries, preserving Wine's own links.
        if path == source / 'engine/lib':
            return {name for name in names if (path / name).is_symlink()
                    and os.readlink(path / name).startswith('../../frameworks/')}
        return set()
    shutil.copytree(source, destination, symlinks=True, ignore=ignore)


def relocate(binary, stage, changes):
    before = sha256(binary)
    operations = []
    output = subprocess.check_output(['/usr/bin/otool', '-L', str(binary)], text=True)
    ids = subprocess.check_output(['/usr/bin/otool', '-D', str(binary)], text=True).splitlines()[1:]
    for original in [line.strip().split(' (compatibility version ', 1)[0]
                     for line in output.splitlines() if ' (compatibility version ' in line]:
        if original in [s.strip() for s in ids]:
            if (original.startswith('/') and not system_path(original)) or original.startswith('@@HOMEBREW'):
                operations.append(['-id', '@rpath/' + binary.name])
            continue
        replacement = None
        leaf = Path(original).name
        if original.startswith('/usr/local/opt/ffmpeg/'):
            replacement = stage / 'engine/lib' / leaf
        elif original.startswith(('/usr/local/opt/gstreamer/', '/usr/local/opt/glib/', '/usr/local/opt/gettext/')):
            replacement = stage / 'engine/lib' / leaf
        elif original.startswith('@@HOMEBREW'):
            replacement = binary.parent / leaf
        elif 'ffmpeg' in binary.parts and original.startswith('@rpath/'):
            replacement = binary.parent / leaf
        if replacement:
            if not replacement.is_file():
                raise ValueError(f'Missing replacement for {original}')
            operations.append(['-change', original, '@loader_path/' + os.path.relpath(replacement, binary.parent)])
    loads = subprocess.check_output(['/usr/bin/otool', '-l', str(binary)], text=True).splitlines()
    for i, line in enumerate(loads):
        if line.strip() == 'cmd LC_RPATH':
            for following in loads[i + 1:i + 5]:
                if following.strip().startswith('path '):
                    value = following.strip()[5:].rsplit(' (offset ', 1)[0]
                    if value.startswith('/') and not system_path(value):
                        operations.append(['-delete_rpath', value])
    if operations:
        # One atomic rewrite avoids temporary header growth when removing RPATHs.
        subprocess.run(['/usr/bin/install_name_tool', *[arg for operation in operations for arg in operation], str(binary)], check=True)
        subprocess.run(['/usr/bin/codesign', '--force', '--sign', '-', '--preserve-metadata=entitlements', str(binary)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        changes.append({'path': str(binary.relative_to(stage)), 'upstream_sha256': before,
                        'relocated_sha256': sha256(binary), 'load_command_operations': operations})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path, help='new destination; must not exist')
    parser.add_argument('--gstreamer', type=Path, required=True, help='locally extracted official framework')
    parser.add_argument('--ffmpeg', type=Path, default=ROOT / 'vendor/ffmpeg-install-x86_64')
    args = parser.parse_args()
    stage = args.destination.resolve()
    if stage.exists():
        parser.error('Choose a new destination; no existing stage is removed')
    if not (args.gstreamer / 'Versions/1.0/lib/libgstreamer-1.0.0.dylib').is_file():
        parser.error('Extract the verified GStreamer runtime first')
    copy_runtime(args.source.resolve(), stage)
    shutil.copytree(args.gstreamer, stage / 'frameworks/GStreamer.framework', symlinks=True)
    gstlib = stage / 'frameworks/GStreamer.framework/Versions/1.0/lib'
    # The engine was built against GLib's 8801 ABI; the official GStreamer
    # framework carries 8201. Replace the five GLib libraries with verified Intel
    # bottles and matching PCRE2; never falsify dylib compatibility versions.
    glibdirs = list((ROOT / 'vendor/glib-2.88.3-bottle/glib').glob('*/lib'))
    pcredirs = list((ROOT / 'vendor/pcre2-bottle/pcre2').glob('*/lib'))
    gettextdirs = list((ROOT / 'vendor/gettext-bottle/gettext').glob('*/lib'))
    if any(len(paths) != 1 for paths in [glibdirs, pcredirs, gettextdirs]):
        raise ValueError('Extract the pinned GLib, PCRE2 and gettext bottles first')
    replacements = [p for p in glibdirs[0].glob('*.dylib')
                    if p.name.startswith(('libglib-', 'libgobject-', 'libgmodule-', 'libgthread-', 'libgio-'))]
    replacements += list(pcredirs[0].glob('libpcre2-8*.dylib'))
    replacements += list(gettextdirs[0].glob('libintl*.dylib'))
    for path in replacements:
        target = gstlib / path.name
        # Replace only files in this NEW private staging directory.
        if target.exists() or target.is_symlink():
            target.unlink()
        if path.is_symlink():
            target.symlink_to(os.readlink(path))
        else:
            shutil.copy2(path, target)
    ffdir = stage / 'frameworks/ffmpeg'
    ffdir.mkdir()
    for path in args.ffmpeg.glob('lib/*.dylib'):
        if path.is_symlink():
            (ffdir / path.name).symlink_to(os.readlink(path))
        else:
            shutil.copy2(path, ffdir / path.name)
    lib = stage / 'engine/lib'
    for directory in [stage / 'frameworks', gstlib, ffdir]:
        for path in sorted(directory.glob('*.dylib')):
            target = lib / path.name
            if not target.exists() and not target.is_symlink():
                target.symlink_to(os.path.relpath(path, lib))
    (lib / 'GStreamer.framework').symlink_to('../../frameworks/GStreamer.framework')
    overlay = stage / 'renderers/dxmt/wine/x86_64-unix'
    for name in ['ntdll.so', 'winemac.so']:
        (overlay / name).symlink_to(os.path.relpath(stage / 'engine/lib/wine/x86_64-unix' / name, overlay))
    changes = []
    for binary in sorted(stage.rglob('*')):
        if binary.is_file() and not binary.is_symlink() and macho(binary):
            if 'GStreamer.framework' in binary.parts:
                archs = subprocess.check_output(['/usr/bin/lipo', '-archs', str(binary)], text=True).split()
                if 'arm64' in archs and 'x86_64' in archs:
                    subprocess.run(['/usr/bin/lipo', str(binary), '-thin', 'x86_64', '-output', str(binary)], check=True)
            relocate(binary, stage, changes)
    (stage / 'relocation-changes.json').write_text(json.dumps(changes, indent=2) + '\n')
    licenses = stage / 'licenses'
    licenses.mkdir()
    shutil.copy2(ROOT / 'vendor/highball-engine-r27/LICENSE', licenses / 'Wine-LGPL-2.1.txt')
    shutil.copy2(ROOT / 'vendor/highball-engine-r27/NOTICE.md', licenses / 'Highball-engine-NOTICE.md')
    for name in ['COPYING.LGPLv2.1', 'LICENSE.md', 'config.h', 'config.mak']:
        shutil.copy2(args.ffmpeg / name, licenses / ('FFmpeg-' + name))
    shutil.copy2(ROOT / 'vendor/highball/spike/patches/moltenvk-linear-fallback.patch', licenses)
    shutil.copy2(ROOT / 'vendor/rdr2-runtime-r27/frameworks/renderer/dxmt/LICENSE', licenses / 'DXMT-MIT.txt')
    (licenses / 'REVIEW-PENDING.md').write_text(
        'Private development test build. Licensing/corresponding-source review is incomplete.\n'
        'The mixed Template dylibs and Wine Mono/Gecko/fonts require complete notices/source mapping before public distribution.\n'
        'Wine patch source: https://github.com/gauthierpiarrette/highball-engine/tree/5d6bbe0c83f4592a8798abba48cc7e8f58feb492\n'
        'FFmpeg 9.0.2 source/build inputs: see config/media-sources.json and packaging/build-ffmpeg.sh.\n')
    print(f'Relocated {len(changes)} Mach-O files in {stage}. Run audit and dynamic tests; license review remains open.')


if __name__ == '__main__':
    main()
