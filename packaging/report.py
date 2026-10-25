#!/usr/bin/env python3
import json
from pathlib import Path
import sys
from runtime_tools import sha256

app, output = map(Path, sys.argv[1:])
resources = app / 'Contents/Resources'
runtime = resources / 'runtime-manifest.json'
root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'config/engine-upstream.json').read_text())
bundled = runtime.exists()
rows = ['# Software bill of materials', '',
        'Development artifact. This inventory is not a completed redistribution license review.', '',
        '| Component | Version | Source | License declared upstream | Archive SHA-256 | Bundled |',
        '| --- | --- | --- | --- | --- | --- |']
for name in ('wine', 'runtime', 'moltenvk', 'dxmt', 'nvapi-stub', 'audiobuf'):
    c = manifest['components'][name]
    rows.append(f'| {name} | {c.get("version", manifest["id"])} | {c["url"]} | {c["license"]} | `{c["sha256"]}` | {bundled} |')
media = json.loads((root / 'config/media-sources.json').read_text())
for name in ['ffmpeg', 'gstreamer-runtime', 'glib-bottle', 'pcre2-bottle', 'gettext-bottle']:
    item = media[name]
    version = item.get('observed_package_version', item['version'])
    license_name = {'ffmpeg': 'LGPL-2.1+ demux build (no GPL options)', 'gstreamer-runtime': 'mixed; vendor notices preserved',
                    'glib-bottle': 'LGPL-2.1+', 'pcre2-bottle': 'BSD-3-Clause', 'gettext-bottle': 'LGPL-2.1+ libintl only'}[name]
    rows.append(f'| {name} | {version} | {item["url"]} | {license_name} | `{item["sha256"]}` | {bundled} |')
rows += ['', 'Apple frameworks and Rosetta are system prerequisites, not redistributed.',
         'Steam/Rockstar/RDR2 binaries and account state are not bundled.',
         'Exact bundled file hashes are in Contents/Resources/runtime-manifest.json when present.',
         'Launcher source: this repository. Recipe snapshots: Highball DB, CC0 (see notes/environment.md).',
         'The Template media framework was replaced; unused wrapper SDK/renderer overlays are excluded.',
         'Wine/renderer load-command changes are recorded in runtime/relocation-changes.json.',
         'GStreamer devel archive supplied only license notices; its headers/tools are not bundled.',
         'Public redistribution remains gated by runtime/licenses/REVIEW-PENDING.md and corresponding-source review.']
(output / 'SBOM.md').write_text('\n'.join(rows) + '\n')
text = f'''# Test report

Artifact: {app.name}
Launcher SHA-256: `{sha256(app / 'Contents/MacOS/RDR2Launcher')}`
Runtime included: {bundled}

See dependency-audit.json for the static dependency audit and STATUS.md in the source checkout
for actual test observations. A successful static audit does not prove runtime loading.
This package is a development build unless the explicit release gate was passed.
Minimum deployment target: macOS 14; this does not assert Wine/game compatibility on macOS 14.
Steam/Rockstar authentication, gameplay, FPS, Finder/Gatekeeper, separate clean-host testing,
download resume, app replacement and dynamic relocation are NOT inferred from packaging.
No credentials or user registry data are collected in this report.
'''
(output / 'TEST-REPORT.md').write_text(text)
for name in ['build-validation.md', 'runtime-validation.md', 'recovery-validation.md']:
    observations = root / 'notes/evidence' / name
    if observations.is_file():
        with (output / 'TEST-REPORT.md').open('a') as report:
            report.write('\n' + observations.read_text())
