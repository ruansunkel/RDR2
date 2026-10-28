#!/usr/bin/env python3
"""Run the pass regression and bind its results to the pinned candidate artifact.

Inputs are private, small captured buffers, arranged in tree/, foliage/, rock/
directories with <kind>-cull.metal and <kind>-cull-<buffer>.bin files.
"""
import argparse
import json
from pathlib import Path
import subprocess
import uuid

from build import HERE, ROOT, PINS, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--artifact', type=Path, required=True)
    args = parser.parse_args()
    artifact = args.artifact.resolve()
    metadata = json.loads((artifact / 'build.json').read_text())
    library_hash = digest(artifact / 'libMoltenVK.dylib')
    variant = PINS['candidate']['variants']['candidate-pass-safe-occlusion']
    helpers = {path.name: digest(path) for path in HERE.glob('*-cull-pass-safe-hiz-workaround.h')}
    if (metadata.get('mode') != 'candidate-pass-safe-occlusion' or metadata.get('pins') != PINS or
            metadata.get('sha256') != library_hash or len(helpers) != 3):
        raise ValueError('Artifact differs from the pinned pass-preserving candidate')
    for kind, label in [('tree', 'Tree'), ('foliage', 'Foliage'), ('rock', 'Rock')]:
        header = 'MoltenVK/MoltenVK/GPUObjects/MVKRDR2' + label + 'Occlusion.h'
        if helpers[kind + '-cull-pass-safe-hiz-workaround.h'] != variant['added_files'][header]:
            raise ValueError('Probe helper differs from the compiled renderer source')
    work = ROOT / 'vendor/water-research' / ('pass-probe-' + uuid.uuid4().hex)
    work.mkdir(parents=True)
    binary = work / 'probe-cull-passes'
    subprocess.run(['clang++', '-std=c++17', '-Wno-deprecated-declarations',
                    '-framework', 'Foundation', '-framework', 'Metal',
                    str(HERE / 'probe-cull-passes.mm'), '-o', str(binary)], check=True)
    raw = work / 'cull-pass-results.json'
    subprocess.run([str(binary), str(args.inputs.resolve()), str(raw)], check=True, timeout=120)
    report = json.loads(raw.read_text())
    if (report.get('cases') != 216 or report.get('legacy_inverse_failures') != 18 or
            any(report.get(key) is not True for key in
                ['pass_controls_passed', 'guard_controls_passed', 'original_instances_retained', 'synthetic_depth'])):
        raise ValueError('Captured-shader GPU controls failed')
    (artifact / raw.name).write_bytes(raw.read_bytes())
    validation = {'driver_sha256': library_hash, 'probe_sha256': digest(HERE / 'probe-cull-passes.mm'),
                  'helper_sha256': helpers, 'results_sha256': digest(raw),
                  'input_sha256': {str(p.relative_to(args.inputs)): digest(p)
                                   for p in sorted(args.inputs.rglob('*')) if p.is_file()},
                  'visual_water_fix_verified': False}
    (artifact / 'cull-pass-validation.json').write_text(json.dumps(validation, indent=2) + '\n')
    print('Exact candidate/source/control fingerprints recorded:', artifact)


if __name__ == '__main__':
    main()
