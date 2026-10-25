#!/usr/bin/env python3
"""Preserve available vendor notices; explicitly leave unresolved license review open."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from runtime_tools import sha256

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runtime', type=Path)
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    licenses = runtime / 'licenses'
    licenses.mkdir(exist_ok=True)
    info = json.loads((ROOT / 'config/media-sources.json').read_text())['gstreamer-devel']
    archive = ROOT / 'vendor/downloads' / info['sha256']
    if sha256(archive) != info['sha256']:
        raise ValueError('GStreamer devel checksum mismatch')
    expanded = ROOT / 'vendor/gstreamer-devel-expanded'
    if not expanded.exists():
        subprocess.run(['/usr/sbin/pkgutil', '--expand', str(archive), str(expanded)], check=True)
    helper = ROOT / 'vendor/highball-engine-r27/gstreamer/unpkg.py'
    if subprocess.check_output(['git', '-C', str(helper.parents[1]), 'rev-parse', 'HEAD'], text=True).strip() != '5d6bbe0c83f4592a8798abba48cc7e8f58feb492':
        raise ValueError('Vendor extractor revision changed')
    # These are notice files only; no developer tools, headers or scripts enter the app.
    for name in ['base-system-1.0', 'base-crypto', 'gstreamer-1.0-core', 'gstreamer-1.0-playback',
                 'gstreamer-1.0-codecs', 'gstreamer-1.0-codecs-restricted', 'gstreamer-1.0-effects', 'gstreamer-1.0-libav']:
        package = expanded / (name + '-devel-1.28.7-universal.pkg')
        subprocess.run(['/usr/bin/python3', str(helper), str(package), str(licenses / 'GStreamer'), './share/licenses/*'], check=True)
    for bottle, patterns in [('pcre2-bottle', ['**/LICENCE.md', '**/COPYING']),
                             ('gettext-bottle', ['**/COPYING'])]:
        for pattern in patterns:
            for path in (ROOT / 'vendor' / bottle).glob(pattern):
                if path.is_file():
                    shutil.copy2(path, licenses / (bottle + '-' + path.name))
    for patch in ['moltenvk-shadow-import.patch', 'moltenvk-linear-fallback.patch', 'moltenvk-shadow-readback.patch']:
        shutil.copy2(ROOT / 'vendor/highball/spike/patches' / patch, licenses / patch)
    shutil.copy2(ROOT / 'config/media-sources.json', licenses / 'media-source-provenance.json')
    count = sum(path.is_file() for path in licenses.rglob('*'))
    print(f'Preserved {count} notice/provenance files. REVIEW-PENDING.md remains unresolved for public distribution.')


if __name__ == '__main__':
    main()
