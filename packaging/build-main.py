#!/usr/bin/env python3
"""Rebuild the main launcher with the exact locally tested renderer artifact."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
import game_mode

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def validate_artifact(artifact, accepted, pins):
    metadata = json.loads((artifact / 'build.json').read_text())
    recorded = metadata.get('pins', {})
    # New experimental variants do not invalidate earlier accepted binaries.
    # Require every common pin and the complete selected patch/source record.
    def selected_pins(value):
        candidate = dict(value.get('candidate', {}))
        variant = candidate.get('variants', {}).get(accepted['mode'])
        if not variant:
            raise ValueError('Missing selected renderer source pins')
        candidate['variants'] = {accepted['mode']: variant}
        return dict(value, candidate=candidate)
    recorded, pins = selected_pins(recorded), selected_pins(pins)
    if (metadata.get('mode') != accepted['mode'] or
            metadata.get('architecture') != 'x86_64' or
            recorded != pins or
            metadata.get('sha256') != accepted['sha256'] or
            digest(artifact / 'libMoltenVK.dylib') != accepted['sha256']):
        raise ValueError('Renderer differs from the accepted build; rebuild/validate it through experiments/moltenvk-trees first')
    return metadata


def validate_pass_controls(artifact, accepted, pins):
    report = json.loads((artifact / 'cull-pass-validation.json').read_text())
    raw = artifact / 'cull-pass-results.json'
    results = json.loads(raw.read_text())
    here = ROOT / 'experiments/moltenvk-trees'
    helpers = {str(path.relative_to(here)): digest(path)
               for path in here.glob('*-cull-pass-safe-hiz-workaround.h')}
    variant = pins['candidate']['variants'][accepted['mode']]
    labels = {'tree': 'Tree', 'foliage': 'Foliage', 'rock': 'Rock'}
    if (len(helpers) != 3 or report.get('driver_sha256') != accepted['sha256'] or
            report.get('probe_sha256') != digest(here / 'probe-cull-passes.mm') or
            report.get('helper_sha256') != helpers or
            report.get('results_sha256') != digest(raw) or
            results.get('cases') != 216 or results.get('legacy_inverse_failures') != 18 or
            any(results.get(key) is not True for key in
                ['pass_controls_passed', 'guard_controls_passed', 'original_instances_retained', 'synthetic_depth']) or
            any(helpers[kind + '-cull-pass-safe-hiz-workaround.h'] !=
                variant['added_files']['MoltenVK/MoltenVK/GPUObjects/MVKRDR2' + label + 'Occlusion.h']
                for kind, label in labels.items())):
        raise ValueError('Pass-preserving renderer requires matching captured-shader GPU controls')
    allocations = json.loads((artifact / 'gpu-probe-results.json').read_text())
    expected = {'control': False, 'candidate-off': False, 'candidate-on': True,
                'candidate-bundle-on': True, 'candidate-bundle-off': False,
                'candidate-symlink-policy-on': True, 'candidate-env-overrides-bundle': False}
    if (len(allocations) != 7 or {r.get('run') for r in allocations} != set(expected) or
            any(r.get('exit') != 0 or r.get('marker_present') is not expected[r['run']] or
                r.get('probe_source_sha256') != digest(here / 'probe-gpu.c') or
                (r['run'] != 'control' and (r.get('dylib_sha256') != accepted['sha256'] or
                 r.get('policy_marker_seen') is not True or r.get('argument_buffer_configuration_matches') is not True))
                for r in allocations)):
        raise ValueError('Water candidate allocation/policy controls differ')
    queries = json.loads((artifact / 'query-probe-results.json').read_text())
    if (len(queries) != 2 or {r.get('run') for r in queries} != {'control', 'candidate'} or
            any(r.get('probe_source_sha256') != digest(here / 'probe-queries.c') or
                (r['run'] == 'candidate' and (r.get('dylib_sha256') != accepted['sha256'] or
                 r.get('exit') != 0 or r.get('regression_passed') is not True)) or
                (r['run'] == 'control' and (r.get('exit') != 3 or r.get('baseline_bug_reproduced') is not True))
                for r in queries)):
        raise ValueError('Water candidate query regression controls differ')


def run(*args, **kwargs):
    return subprocess.run(list(map(str, args)), check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='App destination; defaults to a separate app for graphics checks')
    profile = parser.add_mutually_exclusive_group()
    profile.add_argument('--without-occlusion-fixes', action='store_true',
                        help='Omit the tree, foliage/grass and rock HiZ workarounds; reuse the existing environment')
    profile.add_argument('--water-reflection-candidate', action='store_true',
                         help='Build the separately pinned pass-preserving occlusion candidate for water checks')
    args = parser.parse_args()
    occlusion = not args.without_occlusion_fixes
    water = args.water_reflection_candidate
    default_name = 'RDR2WaterCheck.app' if water else 'RDR2Launcher.app' if occlusion else 'RDR2GraphicsCheck.app'
    output = (args.output or ROOT / 'dist' / default_name).absolute()
    if output.suffix != '.app' or output.is_symlink() or (output.exists() and not output.is_dir()):
        parser.error('Output must be an app directory, not a symlink')
    accepted = json.loads((ROOT / 'config/accepted-renderer.json').read_text())
    comparison = accepted.pop('without_occlusion_fixes')
    if not occlusion:
        accepted.update(comparison)
    if water:
        accepted.update(json.loads((ROOT / 'config/water-reflection-candidate.json').read_text()))
    accepted['occlusion_fixes_included'] = occlusion
    pins = json.loads((ROOT / 'experiments/moltenvk-trees/pins.json').read_text())
    artifact = ROOT / accepted['artifact']
    runtime = ROOT / accepted['runtime']
    metadata = validate_artifact(artifact, accepted, pins)
    if water:
        validate_pass_controls(artifact, accepted, pins)
    compiled_strings = subprocess.check_output(['/usr/bin/strings', '-a', str(artifact / 'libMoltenVK.dylib')], text=True)
    for name in ['TREE', 'FOLIAGE', 'ROCK']:
        if ('RDR2_MVK_' + name + '_HIZ_BYPASS' in compiled_strings) != occlusion:
            raise ValueError('Compiled occlusion helpers do not match the requested build')
    if digest(runtime / 'frameworks/libMoltenVK.dylib') != pins['moltenvk']['reference_dylib_sha256']:
        raise ValueError('Runtime is not the pinned baseline')
    run('/usr/bin/codesign', '--verify', '--strict', artifact / 'libMoltenVK.dylib')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Stage and verify everything before replacing the previous main app.
    with tempfile.TemporaryDirectory(prefix='.main-build-', dir=output.parent) as staging:
        staging = Path(staging)
        app = staging / 'RDR2Launcher.app'
        env = dict(os.environ, RDR2_BUILD_OUTPUT=str(app))
        # Separate native caches from historical caches copied from another Mac.
        env.setdefault('RDR2_BUILD_CACHE_ROOT', str(ROOT / '.cache/main'))
        env.setdefault('RDR2_BUILD_SCRATCH', str(ROOT / '.build/main'))
        run(ROOT / 'packaging/build-app.sh', '--runtime', runtime, env=env, cwd=ROOT)
        resources = app / 'Contents/Resources'
        target = resources / 'runtime/frameworks/libMoltenVK.dylib'
        if target.is_symlink() or not target.resolve().is_relative_to(app.resolve()):
            raise ValueError('Renderer destination escapes staged app')
        shutil.copy2(artifact / 'libMoltenVK.dylib', target)
        (target.parent / 'rdr2-tree-policy.conf').write_text(
            'RDR2_TREE_POLICY_V1\nenabled=1\ndata_directory=' + accepted['data_directory'] + '\n')
        info_path = app / 'Contents/Info.plist'
        info = plistlib.loads(info_path.read_bytes())
        info.update({
            'CFBundleDisplayName': 'RDR2 Water Check' if water else 'RDR2 Launcher' if occlusion else 'RDR2 Graphics Check',
            'CFBundleName': 'RDR2WaterCheck' if water else 'RDR2Launcher' if occlusion else 'RDR2GraphicsCheck',
            'CFBundleIdentifier': 'org.rdr2launcher.water-check' if water else 'org.rdr2launcher.app' if occlusion else 'org.rdr2launcher.graphics-check',
            'CFBundleVersion': '7',
            'RDR2LauncherEdition': 'patched',
            'RDR2LauncherSubtitle': 'Steam edition · Story Mode · Vulkan / patched MoltenVK\n' +
                ('Water reflection test · pass-preserving occlusion candidate.' if water else
                 'Tree, foliage and rock workarounds ' + ('included.' if occlusion else 'omitted for graphics checks.')),
            'RDR2OcclusionFixesIncluded': occlusion,
            'RDR2RendererVariant': accepted['mode'], 'RDR2TreeFixEnabled': True})
        info_path.write_bytes(plistlib.dumps(info))
        shutil.copy2(artifact / 'build.json', resources / 'moltenvk-candidate-build.json')
        (resources / 'accepted-renderer.json').write_text(json.dumps(accepted, indent=2) + '\n')
        if water:
            evidence = resources / 'water-check-validation'
            evidence.mkdir()
            for name in ['cull-pass-results.json', 'cull-pass-validation.json',
                         'gpu-probe-results.json', 'query-probe-results.json']:
                shutil.copy2(artifact / name, evidence / name)
        notices = resources / 'runtime/licenses/moltenvk-local-patches'
        notices.mkdir(parents=True, exist_ok=True)
        patches = pins['moltenvk']['patches'] + [pins['candidate']]
        patches += pins['candidate']['variants'][accepted['mode']]['patches']
        for item in patches:
            patch = ROOT / 'experiments/moltenvk-trees/patches' / item['file']
            shutil.copy2(patch, notices / patch.name)
        if occlusion:
            for header in (ROOT / 'experiments/moltenvk-trees').glob('*-hiz-workaround.h'):
                shutil.copy2(header, notices / header.name)
        shutil.copy2(ROOT / 'experiments/moltenvk-trees/pins.json', notices / 'pins.json')
        manifest_path = resources / 'runtime/manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['localOverrides'] = {'moltenvk': accepted}
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        game_mode.sign(resources / 'runtime')
        run('python3', ROOT / 'packaging/runtime_tools.py', 'manifest', resources)
        run(ROOT / 'packaging/audit-deps.sh', app, stdout=subprocess.DEVNULL)
        # Nested runtime binaries already carry valid signatures. Preserve the
        # tested renderer bytes instead of re-signing it with a new identifier.
        run('/usr/bin/codesign', '--force', '--sign', '-', app)
        run('/usr/bin/codesign', '--verify', '--deep', '--strict', app)
        if digest(target) != metadata['sha256']:
            raise ValueError('Packaged renderer bytes changed')
        result = run(app / 'Contents/MacOS/RDR2Launcher', '--diagnose',
                     stdout=subprocess.PIPE, text=True).stdout
        if ('Launcher edition: patched' not in result or
                'Default data folder: ' + accepted['data_directory'] not in result or
                'Occlusion workarounds: ' + ('included' if occlusion else 'not included') not in result):
            raise ValueError('App selected the wrong environment or renderer profile')
        previous = staging / 'previous.app'
        if output.exists():
            output.rename(previous)
        try:
            app.rename(output)
        except BaseException:
            if previous.exists():
                previous.rename(output)
            raise
    print(result)
    print('Built app:', output)
    print('Renderer SHA256:', metadata['sha256'])


if __name__ == '__main__':
    main()
