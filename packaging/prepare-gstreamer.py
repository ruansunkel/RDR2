#!/usr/bin/env python3
"""Extract selected official GStreamer components without installing the .pkg.

Uses the inspected, pinned upstream pbzx extractor, then copies the media playback
dependency closure to a new framework. Unselected files are never shipped.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from runtime_tools import sha256

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = '''coreelements typefindfunctions app playback videoconvertscale videofilter audioconvert
audioresample volume rawparse pbtypes deinterlace isomp4 matroska avi ogg flv asf mpegtsdemux
mpegpsdemux id3demux apetag audioparsers videoparsersbad vorbis theora opus flac mpg123 dav1d libav wavparse'''.split()
LIBS = '''libgstreamer-1.0.0.dylib libgstvideo-1.0.0.dylib libgstaudio-1.0.0.dylib libgsttag-1.0.0.dylib
libgstbase-1.0.0.dylib libgobject-2.0.0.dylib libglib-2.0.0.dylib libintl.8.dylib'''.split()
TOOLS = ['bin/gst-inspect-1.0', 'bin/gst-launch-1.0', 'libexec/gstreamer-1.0/gst-plugin-scanner']
COMPONENTS = ['base-system-1.0', 'base-crypto', 'gstreamer-1.0-core', 'gstreamer-1.0-playback',
              'gstreamer-1.0-codecs', 'gstreamer-1.0-codecs-restricted', 'gstreamer-1.0-effects', 'gstreamer-1.0-libav']


def closure(roots, lib):
    needed = set()
    todo = list(roots)
    while todo:
        path = todo.pop()
        if path in needed:
            continue
        if not path.exists():
            raise ValueError(f'Missing media dependency: {path.name}')
        needed.add(path)
        output = subprocess.check_output(['/usr/bin/otool', '-L', str(path)], text=True)
        for line in output.splitlines():
            ref = line.strip().split(' (compatibility version ', 1)[0]
            if ref.startswith('@rpath/'):
                if Path(ref).name == path.name:
                    continue
                target = lib / Path(ref).name
                if target != path and target not in needed:
                    todo.append(target)
    return needed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path, help='new framework path')
    args = parser.parse_args()
    destination = args.destination.resolve()
    if destination.exists():
        parser.error('Choose a new destination')
    info = json.loads((ROOT / 'config/media-sources.json').read_text())['gstreamer-runtime']
    archive = ROOT / 'vendor/downloads' / info['sha256']
    if sha256(archive) != info['sha256']:
        raise ValueError('GStreamer package checksum mismatch')
    expanded = ROOT / 'vendor/gstreamer-runtime-expanded'
    if not expanded.exists():
        subprocess.run(['/usr/sbin/pkgutil', '--expand', str(archive), str(expanded)], check=True)
    extracted = ROOT / 'vendor/gstreamer-extracted'
    extracted.mkdir(exist_ok=True)
    helper = ROOT / 'vendor/highball-engine-r27/gstreamer/unpkg.py'
    actual = subprocess.check_output(['git', '-C', str(helper.parents[1]), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != '5d6bbe0c83f4592a8798abba48cc7e8f58feb492':
        raise ValueError('pbzx extractor source revision changed')
    for name in COMPONENTS:
        package = expanded / (name + '-1.28.7-universal.pkg')
        subprocess.run(['/usr/bin/python3', str(helper), str(package), str(extracted)], check=True)
    lib = extracted / 'lib'
    roots = [lib / name for name in LIBS] + [extracted / name for name in TOOLS]
    roots += [lib / 'gstreamer-1.0' / ('libgst' + name + '.dylib') for name in PLUGINS]
    needed = closure(roots, lib)
    version = destination / 'Versions/1.0'
    for path in sorted(needed):
        target = version / path.relative_to(extracted)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target, follow_symlinks=True)
    (destination / 'Versions/Current').symlink_to('1.0')
    licenses = version / 'share/licenses'
    licenses.mkdir(parents=True)
    shutil.copy2(expanded / 'Resources/license.txt', licenses / 'gstreamer-installer-license.txt')
    (licenses / 'source-provenance.json').write_text(json.dumps(info, indent=2) + '\n')
    print(f'Copied {len(needed)} playback files to {destination}. No package was installed.')


if __name__ == '__main__':
    main()
