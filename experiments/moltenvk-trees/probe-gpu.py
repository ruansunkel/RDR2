#!/usr/bin/env python3
"""Compare real GPU allocations and bind results to exact tested artifact bytes."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid

from build import ROOT, HERE, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=ROOT / 'vendor/tree-research')
    parser.add_argument('--candidate-artifact', type=Path)
    args = parser.parse_args()
    work = args.work.resolve()
    candidate_artifact = args.candidate_artifact.resolve() if args.candidate_artifact else work / 'artifacts/candidate'
    candidate_metadata = json.loads((candidate_artifact / 'build.json').read_text())
    expected_arguments = 'useMetalArgumentBuffers: 1' in candidate_metadata['configuration_probe'].splitlines()
    headers = list((work / 'cpm/vulkan-headers').glob('*/Vulkan-Headers/include'))
    if len(headers) != 1: parser.error('Prepare exactly the pinned Vulkan-Headers dependency first')
    source = HERE / 'probe-gpu.c'
    binary = work / 'probe-gpu'
    subprocess.run(['clang', '-arch', 'x86_64', '-mmacosx-version-min=14.0', '-Wall', '-Wextra',
                    '-I', str(headers[0]), str(source), '-o', str(binary)], check=True)
    evidence = work / 'host-private' / ('gpu-probe-' + uuid.uuid4().hex)
    evidence.mkdir(parents=True, mode=0o700)
    results = []
    cases = [('control', 'control', False, None, None),
             ('candidate-off', 'candidate', False, '0', None),
             ('candidate-on', 'candidate', True, '1', None),
             ('candidate-bundle-on', 'candidate', True, None, True),
             ('candidate-bundle-off', 'candidate', False, None, False),
             ('candidate-symlink-policy-on', 'candidate', True, None, True),
             ('candidate-env-overrides-bundle', 'candidate', False, '0', True)]
    for label, mode, enabled, environment_flag, bundle_flag in cases:
        source_library = (work / 'artifacts/control' if mode == 'control' else candidate_artifact) / 'libMoltenVK.dylib'
        before = digest(source_library)
        run_directory = evidence / label
        run_directory.mkdir()
        library = run_directory / 'libMoltenVK.dylib'
        shutil.copy2(source_library, library)
        if bundle_flag is not None:
            (run_directory / 'rdr2-tree-policy.conf').write_text('RDR2_TREE_POLICY_V1\nenabled=' + ('1' if bundle_flag else '0') + '\n')
        marker = evidence / (label + '.events')
        env = {'PATH': '/usr/bin:/bin', 'HOME': str(Path.home()), 'MVK_CONFIG_LOG_LEVEL': '2',
               'RDR2_MVK_ALLOCATION_MARKER_FILE': str(marker)}
        if environment_flag is not None: env['RDR2_MVK_DEDICATED_BUFFER_NO_HEAP'] = environment_flag
        load_path = library
        if label == 'candidate-symlink-policy-on':
            alias = run_directory / 'engine/lib/libMoltenVK.dylib'
            alias.parent.mkdir(parents=True)
            alias.symlink_to(os.path.relpath(library, alias.parent))
            load_path = alias
        p = subprocess.run([str(binary), str(load_path)], env=env, capture_output=True, text=True, timeout=40)
        (evidence / (label + '.log')).write_text(p.stdout + p.stderr)
        native_pid = re.search(r'native probe PID: (\d+)', p.stdout)
        events = marker.read_text().splitlines() if marker.exists() else []
        prefix = 'pid=' + native_pid.group(1) + ' ' if native_pid else '(no-native-pid) '
        marked = prefix + 'dedicated-buffer-no-heap' in events
        policy_seen = prefix + ('policy-on' if enabled else 'policy-off') in events
        arguments_match = prefix + ('argument-buffers-on' if expected_arguments else 'argument-buffers-off') in events
        row = {'run': label, 'exit': p.returncode, 'marker_present': marked,
               'policy_marker_seen': policy_seen, 'expected_enabled': enabled,
               'argument_buffer_configuration_matches': arguments_match,
               'dylib_sha256': before, 'probe_source_sha256': digest(source), 'evidence_directory': str(evidence)}
        results.append(row)
        print(label + ': exit ' + str(p.returncode) + ', marker ' + str(marked), flush=True)
        if (p.returncode or marked != enabled or digest(library) != before or digest(source_library) != before or
                (mode == 'candidate' and (not policy_seen or not arguments_match)) or any(not line.startswith(prefix) for line in events)):
            raise RuntimeError('GPU comparison failed; inspect ' + str(evidence))
    (work / 'host-private/gpu-probe-results.json').write_text(json.dumps(results, indent=2) + '\n')
    print('All real-GPU allocation comparisons passed; artifact hashes recorded.', flush=True)


if __name__ == '__main__':
    main()
