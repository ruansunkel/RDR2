#!/usr/bin/env python3
"""Prove the nonzero Vulkan query-copy regression against exact driver bytes."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import uuid

from build import ROOT, HERE, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=ROOT / 'vendor/tree-research')
    parser.add_argument('--control-artifact', type=Path)
    parser.add_argument('--candidate-artifact', type=Path, required=True)
    parser.add_argument('--control-only', action='store_true', help='Diagnose baseline while the candidate builds')
    args = parser.parse_args()
    work = args.work.resolve()
    control_artifact = args.control_artifact.resolve() if args.control_artifact else work / 'artifacts/control'
    candidate_artifact = args.candidate_artifact.resolve()
    headers = list((work / 'cpm/vulkan-headers').glob('*/Vulkan-Headers/include'))
    if len(headers) != 1: parser.error('Prepare exactly the pinned Vulkan-Headers dependency first')
    source = HERE / 'probe-queries.c'
    binary = work / 'probe-queries'
    subprocess.run(['clang', '-arch', 'x86_64', '-mmacosx-version-min=14.0', '-Wall', '-Wextra',
                    '-I', str(headers[0]), str(source), '-o', str(binary)], check=True)
    evidence = work / 'host-private' / ('query-probe-' + uuid.uuid4().hex)
    evidence.mkdir(parents=True, mode=0o700)
    rows = []
    cases = [('control', control_artifact, False)]
    if not args.control_only: cases.append(('candidate', candidate_artifact, True))
    for label, artifact, expected_pass in cases:
        source_library = artifact / 'libMoltenVK.dylib'
        before = digest(source_library)
        metadata = json.loads((artifact / 'build.json').read_text())
        if metadata['sha256'] != before: raise ValueError('Artifact hash differs from its build metadata')
        run_directory = evidence / label
        run_directory.mkdir()
        library = run_directory / 'libMoltenVK.dylib'
        shutil.copy2(source_library, library)
        marker = run_directory / 'events.log'
        env = {'PATH': '/usr/bin:/bin', 'HOME': str(Path.home()), 'MVK_CONFIG_LOG_LEVEL': '2',
               'RDR2_MVK_ALLOCATION_MARKER_FILE': str(marker), 'RDR2_MVK_DEDICATED_BUFFER_NO_HEAP': '0'}
        process = subprocess.run([str(binary), str(library)], env=env, capture_output=True, text=True, timeout=40)
        (run_directory / 'probe.log').write_text(process.stdout + process.stderr)
        reports = [json.loads(line[len('QUERY_RESULT_JSON '):]) for line in process.stdout.splitlines()
                   if line.startswith('QUERY_RESULT_JSON ')]
        if len(reports) != 1: raise RuntimeError('No unique query probe result; inspect ' + str(run_directory))
        report = reports[0]
        # The baseline must fail for this exact known offset bug, while its
        # independent firstQuery=0 case succeeds. A crash is not a regression proof.
        baseline_failed_as_expected = (process.returncode == 3 and report['passed'] is False and
                                      report['host_available'] == 1 and report['zero64_available'] == 1 and
                                      report['nonzero64_available'] == 0 and report['nonzero32_available'] == 0)
        candidate_passed = process.returncode == 0 and report['passed'] is True
        events = marker.read_text().splitlines() if marker.exists() else []
        prefix = 'pid=' + str(report['pid']) + ' '
        if any(not line.startswith(prefix) for line in events): raise RuntimeError('Unexpected diagnostic event format')
        row = {'run': label, 'exit': process.returncode, 'expected_pass': expected_pass,
               'baseline_regression_reproduced': baseline_failed_as_expected,
               'baseline_bug_reproduced': baseline_failed_as_expected,
               'regression_passed': candidate_passed,
               'result': report, 'native_events': [line[len(prefix):] for line in events],
               'dylib_sha256': before, 'probe_source_sha256': digest(source),
               'probe_binary_sha256': digest(binary), 'evidence_directory': str(run_directory)}
        rows.append(row)
        print(label + ': ' + ('passed' if candidate_passed else 'known regression reproduced' if baseline_failed_as_expected else 'unexpected failure'), flush=True)
        if digest(library) != before or digest(source_library) != before: raise RuntimeError('Driver changed during test')
        if (expected_pass and not candidate_passed) or (not expected_pass and not baseline_failed_as_expected):
            raise RuntimeError('Query comparison failed; inspect ' + str(run_directory))
    destination = work / ('host-private/query-probe-control-results.json' if args.control_only else 'host-private/query-probe-results.json')
    destination.write_text(json.dumps(rows, indent=2) + '\n')
    print('Query GPU results and exact hashes recorded at ' + str(destination), flush=True)


if __name__ == '__main__':
    main()
