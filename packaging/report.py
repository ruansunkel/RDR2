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
rows += ['', 'Apple frameworks and Rosetta are system prerequisites, not redistributed.',
         'Steam/Rockstar/RDR2 binaries and account state are not bundled.',
         'Exact bundled file hashes are in Contents/Resources/runtime-manifest.json when present.',
         'Launcher source: this repository. Recipe snapshots: Highball DB, CC0 (see notes/environment.md).']
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
observations = root / 'notes/evidence/build-validation.md'
if observations.is_file():
    with (output / 'TEST-REPORT.md').open('a') as report:
        report.write('\n' + observations.read_text())
