#!/usr/bin/env python3
"""Package a candidate in a new app with its own host-data selection."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess

from build import ROOT, HERE, PINS, digest


def run(args, **kwargs):
    return subprocess.run(list(map(str, args)), check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, default=ROOT / 'vendor/tree-research/artifacts/candidate')
    parser.add_argument('--runtime', type=Path, default=ROOT / 'vendor/rdr2-runtime-r27-portable-v3')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/tree-candidate/RDR2 Trees Candidate.app')
    parser.add_argument('--fix-disabled', action='store_true', help='same binary with the allocation option absent')
    args = parser.parse_args()
    app = args.output.absolute()
    if app.exists() or app.is_symlink() or app.suffix != '.app':
        parser.error('Choose a NEW app destination; existing builds are preserved')
    artifact = args.artifact.resolve()
    source = artifact / 'libMoltenVK.dylib'
    metadata = json.loads((artifact / 'build.json').read_text())
    if (metadata.get('mode') not in ['candidate', 'candidate-argument-buffer-off', 'candidate-query-results', 'candidate-tree-occlusion'] or metadata.get('pins') != PINS or
            metadata.get('architecture') != 'x86_64' or digest(source) != metadata.get('sha256')):
        parser.error('Candidate artifact provenance/hash/architecture differs')
    if args.fix_disabled and metadata['mode'] in ['candidate-query-results', 'candidate-tree-occlusion']:
        parser.error('--fix-disabled controls only the dedicated-buffer option; use the actual control artifact for a query-fix comparison')
    if metadata['mode'] == 'candidate-tree-occlusion':
        cull = json.loads((ROOT / 'vendor/tree-research/host-private/captured-cull-workaround-results.json').read_text())
        header = 'MoltenVK/MoltenVK/GPUObjects/MVKRDR2TreeOcclusion.h'
        if (not cull.get('six_gpu_controls_passed') or not cull.get('guard_negative_controls_passed') or
                cull.get('game_hiz_data_reproduced') is not False or
                cull.get('helper_sha256') != digest(HERE / 'tree-cull-hiz-workaround.h') or
                cull.get('helper_sha256') != PINS['candidate']['variants']['candidate-tree-occlusion']['added_files'][header] or
                cull.get('probe_sha256') != digest(HERE / 'probe-captured-cull.mm')):
            parser.error('Captured-culling GPU controls do not match this diagnostic workaround')
    original = args.runtime.resolve() / 'frameworks/libMoltenVK.dylib'
    if digest(original) != PINS['moltenvk']['reference_dylib_sha256']:
        parser.error('Source runtime is not the pinned reference')
    results = json.loads((ROOT / 'vendor/tree-research/host-private/gpu-probe-results.json').read_text())
    expected = {'control': False, 'candidate-off': False, 'candidate-on': True,
                'candidate-bundle-on': True, 'candidate-bundle-off': False,
                'candidate-symlink-policy-on': True,
                'candidate-env-overrides-bundle': False}
    if ({r.get('run') for r in results} != set(expected) or
            any(r.get('exit') != 0 or r.get('marker_present') != expected[r['run']] for r in results) or
            any(not r.get('policy_marker_seen') or not r.get('argument_buffer_configuration_matches') for r in results if r['run'] != 'control')):
        parser.error('Required real-GPU allocation comparison has not passed')
    for row in results:
        tested = (ROOT / 'vendor/tree-research/artifacts/control' if row['run'] == 'control' else artifact) / 'libMoltenVK.dylib'
        if row.get('dylib_sha256') != digest(tested) or row.get('probe_source_sha256') != digest(HERE / 'probe-gpu.c'):
            parser.error('GPU evidence does not match the current artifact and probe bytes')
    if metadata['mode'] in ['candidate-query-results', 'candidate-tree-occlusion']:
        query_results = json.loads((ROOT / 'vendor/tree-research/host-private/query-probe-results.json').read_text())
        if len(query_results) != 2 or {r.get('run') for r in query_results} != {'control', 'candidate'}:
            parser.error('Query regression requires the real control and candidate GPU comparison')
        for row in query_results:
            control = row['run'] == 'control'
            tested = (ROOT / 'vendor/tree-research/artifacts/control' if control else artifact) / 'libMoltenVK.dylib'
            if (row.get('dylib_sha256') != digest(tested) or
                    row.get('probe_source_sha256') != digest(HERE / 'probe-queries.c') or
                    row.get('exit') != (3 if control else 0) or
                    row.get('baseline_bug_reproduced') is not control or
                    row.get('regression_passed') is control):
                parser.error('Query regression evidence does not prove the exact control failure and candidate fix')
        events = next(r['native_events'] for r in query_results if r['run'] == 'candidate')
        if not {'query-range-nonzero-first', 'query-availability-offset-applied',
                'query-availability-status-differs'}.issubset(events):
            parser.error('Query GPU regression did not exercise the corrected nonzero range/offset')
    run(['codesign', '--verify', '--strict', source])
    cache = ROOT / '.cache/physical-host'
    env = dict(os.environ, RDR2_BUILD_OUTPUT=str(app), RDR2_BUILD_CACHE_ROOT=str(cache),
               RDR2_BUILD_SCRATCH=str(cache / 'build'))
    run([ROOT / 'packaging/build-app.sh', '--runtime', args.runtime.resolve()], cwd=ROOT, env=env)
    resources = app / 'Contents/Resources'
    target = resources / 'runtime/frameworks/libMoltenVK.dylib'
    if target.is_symlink() or not target.resolve().is_relative_to(app.resolve()) or os.path.samefile(target, original):
        raise ValueError('Candidate library destination is not private to the new app')
    shutil.copy2(source, target)
    # This signed/inventoried fallback survives launchers that discard native
    # environment variables. The original and control libraries never read it.
    (target.parent / 'rdr2-tree-policy.conf').write_text(
        'RDR2_TREE_POLICY_V1\nenabled=' + ('0' if args.fix_disabled else '1') +
        '\ndata_directory=RDR2Launcher-MoltenVK-Candidate\n')
    info_path = app / 'Contents/Info.plist'
    info = plistlib.loads(info_path.read_bytes())
    variant_names = {'candidate': ('RDR2 Trees Candidate', ''),
                     'candidate-argument-buffer-off': ('RDR2 Trees Argument Buffers Off', '.argument-buffers-off'),
                     'candidate-query-results': ('RDR2 Trees Query Results', '.query-results'),
                     'candidate-tree-occlusion': ('RDR2 Trees Occlusion Diagnostic', '.tree-occlusion')}
    name, identifier_suffix = variant_names[metadata['mode']]
    info.update({'CFBundleIdentifier': 'org.rdr2launcher.moltenvk-candidate' + identifier_suffix + ('.off' if args.fix_disabled else ''),
                 'CFBundleName': name + (' Off' if args.fix_disabled else ''),
                 'CFBundleDisplayName': name + (' Off' if args.fix_disabled else ''),
                 'CFBundleVersion': '3', 'RDR2LauncherEdition': 'moltenvk-candidate',
                 'RDR2RendererVariant': metadata['mode'],
                 'RDR2TreeFixEnabled': not args.fix_disabled})
    info_path.write_bytes(plistlib.dumps(info))
    sidecar = {'edition': 'moltenvk-candidate', 'default_data_directory': 'RDR2Launcher-MoltenVK-Candidate',
               'experiment_mode': metadata['mode'],
               'source_commit': PINS['moltenvk']['commit'], 'candidate_patch_included': True,
               'allocation_option_enabled': not args.fix_disabled, 'candidate_dylib_sha256': metadata['sha256'],
               'gpu_allocation_probes_passed': True,
               'query_result_gpu_regression_passed': metadata['mode'] in ['candidate-query-results', 'candidate-tree-occlusion'],
               'captured_tree_hiz_bypass': metadata['mode'] == 'candidate-tree-occlusion',
               'gameplay_verified': False, 'tree_fix_verified': False}
    (resources / 'tree-candidate.json').write_text(json.dumps(sidecar, indent=2) + '\n')
    shutil.copy2(artifact / 'build.json', resources / 'moltenvk-candidate-build.json')
    notices = resources / 'runtime/licenses/moltenvk-tree-experiment'
    notices.mkdir(parents=True)
    for item in (HERE / 'patches').iterdir():
        if item.is_file(): shutil.copy2(item, notices / item.name)
    runtime_manifest = resources / 'runtime/manifest.json'
    manifest = json.loads(runtime_manifest.read_text())
    manifest['localOverrides'] = {'moltenvk': sidecar}
    runtime_manifest.write_text(json.dumps(manifest, indent=2) + '\n')
    variant_description = {
        'candidate': 'It changes eligible dedicated-buffer allocation only; image heaps and argument buffers remain enabled.',
        'candidate-argument-buffer-off': 'Metal argument buffers are disabled. Image heaps remain enabled; the dedicated-buffer allocation experiment is also included.',
        'candidate-query-results': 'It backports upstream PR2794 query-result range and availability-offset fixes. Heaps and Metal argument buffers remain enabled; the earlier dedicated-buffer experiment is also included.',
        'candidate-tree-occlusion': 'It bypasses only the HiZ depth rejection in the exact captured tree-culling shader, guarded by SHA256 of its complete generated MSL body. This is a diagnostic workaround, not a proven driver fix, and may draw extra objects. Earlier query/allocation changes remain included.'
    }[metadata['mode']]
    (resources / 'CANDIDATE-TEST.md').write_text(
        '# Experimental RDR2 tree renderer build\n\n'
        'This candidate has no verified tree fix. ' + variant_description + ' The fixed PID events in '
        'state/tree-allocation-events.log record which process exercised the diagnostic paths.\n\n'
        'Use the copied candidate environment and the same save, camera pan and graphics settings '
        'as the control. Compare nearby/distant trees, water, shadows, terrain and performance. '
        'The original and control apps are preserved. Quit test clients normally before switching apps. '
        'No game or account data is included in this bundle.\n')
    run([ROOT / 'packaging/sign-app.sh', app, '-'], cwd=ROOT)
    if digest(target) != metadata['sha256']:
        shutil.copy2(source, target)
        run(['python3', ROOT / 'packaging/runtime_tools.py', 'manifest', resources])
        run(['codesign', '--force', '--sign', '-', app])
    run(['codesign', '--verify', '--deep', '--strict', app])
    assert digest(target) == metadata['sha256']
    assert digest(original) == PINS['moltenvk']['reference_dylib_sha256']
    output = subprocess.check_output([str(app / 'Contents/MacOS/RDR2Launcher'), '--diagnose'], text=True)
    if ('Launcher edition: moltenvk-candidate' not in output or
            'Default data folder: RDR2Launcher-MoltenVK-Candidate' not in output):
        raise ValueError('Candidate edition/data isolation diagnostic failed')
    (app.parent / ('candidate-off-diagnostic.txt' if args.fix_disabled else 'candidate-on-diagnostic.txt')).write_text(output)
    print(output)
    print('Built separate candidate app:', app)


if __name__ == '__main__':
    main()
