#!/usr/bin/env python3
"""Fetch pinned media build inputs into vendor/downloads. Never install packages."""
import argparse
import json
from pathlib import Path
import subprocess
from runtime_tools import sha256

ROOT = Path(__file__).resolve().parents[1]


def main():
    sources = json.loads((ROOT / 'config/media-sources.json').read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('components', nargs='+', choices=sorted(sources))
    args = parser.parse_args()
    cache = ROOT / 'vendor/downloads'
    cache.mkdir(parents=True, exist_ok=True)
    for name in args.components:
        item = sources[name]
        path = cache / item['sha256']
        if not path.exists():
            partial = path.with_suffix('.partial')
            # GHCR's documented anonymous public-bottle access; this constant is
            # a public placeholder, not an account token or stored credential.
            headers = ['--header', 'Authorization: Bearer QQ=='] if item['url'].startswith('https://ghcr.io/') else []
            subprocess.run(['/usr/bin/curl', '--fail', '--location', '--silent', '--show-error', *headers,
                            '--proto', '=https', '--proto-redir', '=https', '--retry', '2',
                            '--output', str(partial), item['url']], check=True)
            if sha256(partial) != item['sha256']:
                raise ValueError(f'Checksum mismatch: {name}')
            partial.rename(path)
        if sha256(path) != item['sha256']:
            raise ValueError(f'Cached checksum mismatch: {name}')
        print(f'Verified {name}: {path.name}', flush=True)


if __name__ == '__main__':
    main()
