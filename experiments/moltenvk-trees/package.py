#!/usr/bin/env python3
"""Package only the control and allowlisted experimental sources; no game/account data."""
import json
from pathlib import Path
import time
import zipfile

from build import HERE, ROOT, PINS, digest

artifact = ROOT / 'vendor/tree-research/artifacts/control'
metadata = json.loads((artifact / 'build.json').read_text())
if (metadata['mode'] != 'control' or metadata['pins'] != PINS or
        digest(artifact / 'libMoltenVK.dylib') != metadata['sha256']):
    raise ValueError('Expected the verified control artifact')
files = {}
for name in ['README.md', 'COMPARISON.md', 'PLAN.md', 'VALIDATION.md', 'pins.json', 'build.py',
             'engine.py', 'probe-config.c', 'package.py', 'control-evidence.example.json']:
    files['experiments/moltenvk-trees/' + name] = HERE / name
patches = [item['file'] for item in PINS['moltenvk']['patches']]
patches += [PINS['candidate']['file'], 'LICENSE-MoltenVK.txt', 'LICENSE-Highball.txt', 'NOTICE.md']
patches += ['LICENSE-SPIRV-Cross.txt', 'LICENSE-SPIRV-Tools.txt', 'LICENSE-cereal.txt']
for name in patches:
    files['experiments/moltenvk-trees/patches/' + name] = HERE / 'patches' / name
for name in ['libMoltenVK.dylib', 'build.json']:
    files['vendor/tree-research/artifacts/control/' + name] = artifact / name
for name in ['extract-verified.py', 'runtime_tools.py']:
    files['packaging/' + name] = ROOT / 'packaging' / name
files['HOST-TEST.md'] = ROOT / 'HOST-TEST.md'
files['config/engine-upstream.json'] = ROOT / 'config/engine-upstream.json'
for source in files.values():
    if not source.is_file() or source.is_symlink():
        raise ValueError('Unexpected package input: ' + str(source))
out = ROOT / 'dist'
out.mkdir(exist_ok=True)
archive = out / 'moltenvk-tree-control-development.zip'
if archive.exists():
    archive.rename(archive.with_name(archive.name + '.backup-' + str(time.time_ns())))
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as package:
    for name, source in sorted(files.items()):
        package.write(source, 'RDR2-MoltenVK-Tree-Experiment/' + name)
with zipfile.ZipFile(archive) as package:
    if package.testzip() is not None:
        raise ValueError('Archive CRC check failed')
    assert len(package.namelist()) == len(files)
checksum = digest(archive)
(out / 'moltenvk-tree-control-SHA256SUMS').write_text(checksum + '  ' + archive.name + '\n')
print(str(archive) + '\nSHA256: ' + checksum + '\nControl only; no candidate binary or game data.')
