#!/usr/bin/env python3
"""Inspect only the candidate game's renderer mapping and fixed allocation event."""
import argparse
import json
from pathlib import Path
import re
import subprocess

from build import ROOT, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, default=ROOT / 'dist/tree-candidate/RDR2 Trees Candidate.app')
    parser.add_argument('--data-root', type=Path, default=Path.home() / 'Library/Application Support/RDR2Launcher-MoltenVK-Candidate')
    args = parser.parse_args()
    app, data = args.app.resolve(), args.data_root.resolve()
    library = app / 'Contents/Resources/runtime/frameworks/libMoltenVK.dylib'
    expected = json.loads((app / 'Contents/Resources/tree-candidate.json').read_text())['candidate_dylib_sha256']
    rows = subprocess.check_output(['/bin/ps', '-axo', 'pid=,comm='], text=True).splitlines()
    pids = []
    for line in rows:
        fields = line.strip().split(None, 1)
        if len(fields) == 2 and fields[1].endswith('\\RDR2.exe') and data.name in fields[1]:
            pids.append(int(fields[0]))
    if not pids:
        print('The candidate RDR2 process is not running yet.')
        return
    markers = data / 'state/tree-allocation-events.log'
    events = markers.read_text().splitlines() if markers.exists() else []
    for pid in pids:
        listing = subprocess.check_output(['/usr/sbin/lsof', '-a', '-p', str(pid), '-Fn'], text=True)
        paths = [Path(line[1:]) for line in listing.splitlines()
                 if line.startswith('n') and 'MoltenVK' in line and line.endswith('.dylib')]
        if not paths:
            print('RDR2 PID:', pid, 'has started but has not loaded MoltenVK yet.')
            continue
        if not any(path.resolve() == library for path in paths):
            raise ValueError('Candidate RDR2 does not map the expected isolated library')
        actual = digest(library)
        if actual != expected: raise ValueError('Mapped library bytes differ from the candidate profile')
        # Discard the complete process/environment response immediately after
        # extracting the single public experiment switch; never print or save it.
        process_environment = subprocess.check_output(['/bin/ps', 'eww', '-p', str(pid), '-o', 'command='], text=True)
        flag = re.search(r'(?:^|\s)RDR2_MVK_DEDICATED_BUFFER_NO_HEAP=([01])(?:\s|$)', process_environment)
        requested = flag.group(1) if flag else None
        del process_environment
        exercised = f'pid={pid} dedicated-buffer-no-heap' in events
        process_events = [line[len(f'pid={pid} '):] for line in events if line.startswith(f'pid={pid} ')]
        argument_buffers = False if 'argument-buffers-off' in process_events else (True if 'argument-buffers-on' in process_events else None)
        report = {'process_kind': 'RDR2.exe', 'pid': pid, 'loaded_dylib': str(library),
                  'loaded_dylib_sha256': actual, 'allocation_path_exercised': exercised,
                  'requested_allocation_policy': requested,
                  'native_allocation_events': process_events,
                  'native_argument_buffers_enabled': argument_buffers,
                  'marker_file': str(markers), 'visual_result': 'requires user observation'}
        destination = ROOT / 'vendor/tree-research/host-private/candidate-loaded-in-rdr2.json'
        destination.write_text(json.dumps(report, indent=2) + '\n')
        print('RDR2 PID:', pid)
        print('Patched renderer mapping and hash: verified')
        print('RDR2 allocation experiment switch:', requested)
        print('Native allocation events:', ', '.join(process_events) or '(none observed)')
        print('RDR2 exercised the changed allocation path:', exercised)


if __name__ == '__main__':
    main()
