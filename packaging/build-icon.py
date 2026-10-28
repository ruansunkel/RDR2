#!/usr/bin/env python3
"""Build a complete macOS .icns from the checked-in artwork using system tools."""
import argparse
from pathlib import Path
import subprocess
import tempfile


def build(source, output):
    with tempfile.TemporaryDirectory(prefix='rdr2-icon-') as temporary:
        iconset = Path(temporary) / 'RDR2Launcher.iconset'
        iconset.mkdir()
        for points in [16, 32, 128, 256, 512]:
            for scale in [1, 2]:
                pixels = points * scale
                name = f'icon_{points}x{points}' + ('@2x' if scale == 2 else '') + '.png'
                subprocess.run(['/usr/bin/sips', '-s', 'format', 'png', '-z', str(pixels), str(pixels),
                                str(source), '--out', str(iconset / name)],
                               check=True, stdout=subprocess.DEVNULL)
        subprocess.run(['/usr/bin/iconutil', '-c', 'icns', str(iconset), '-o', str(output)], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build(args.source.resolve(strict=True), args.output.absolute())
