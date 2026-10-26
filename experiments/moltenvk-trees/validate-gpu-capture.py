#!/usr/bin/env python3
"""Validate Apple capture/replay on a separate x86-64 Vulkan probe, never a game."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import uuid

from build import ROOT, HERE, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=ROOT / 'vendor/tree-research')
    parser.add_argument('--method', choices=['external', 'programmatic'], default='programmatic')
    args = parser.parse_args()
    work = args.work.resolve()
    library = work / 'artifacts/control/libMoltenVK.dylib'
    metadata = json.loads(library.with_name('build.json').read_text())
    if digest(library) != metadata['sha256']:
        raise ValueError('Control library differs from recorded build')
    headers = list((work / 'cpm/vulkan-headers').glob('*/Vulkan-Headers/include'))
    if len(headers) != 1:
        raise ValueError('Expected pinned Vulkan headers')
    evidence = work / 'host-private' / ('capture-validation-' + uuid.uuid4().hex)
    evidence.mkdir(parents=True, mode=0o700)
    binary = evidence / 'probe'
    subprocess.run(['clang', '-arch', 'x86_64', '-mmacosx-version-min=14.0',
                    '-I', str(headers[0]), str(HERE / 'probe-gpu.c'), '-o', str(binary)], check=True)
    env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'HOME': str(Path.home()),
           'TMPDIR': tempfile.gettempdir(), 'MTL_CAPTURE_ENABLED': '1', 'MVK_CONFIG_LOG_LEVEL': '2'}
    trace = evidence / 'probe.gputrace'
    if args.method == 'external':
        env['MTLCAPTURE_WAIT_FOR_SIGNAL'] = '1'
    else:
        env.update(MVK_CONFIG_AUTO_GPU_CAPTURE_SCOPE='1',
                   MVK_CONFIG_AUTO_GPU_CAPTURE_OUTPUT_FILE=str(trace))
    report = {'probe_source_sha256': digest(HERE / 'probe-gpu.c'),
              'probe_binary_sha256': digest(binary), 'dylib_sha256': digest(library),
              'evidence_directory': str(evidence), 'game_process_touched': False,
              'method': args.method}
    with (evidence / 'probe.log').open('w') as log:
        child = subprocess.Popen([str(binary), str(library)], env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            report['probe_pid'] = child.pid
            if args.method == 'external':
                deadline = time.monotonic() + 35
                target_line = None
                while time.monotonic() < deadline:
                    listing = subprocess.run(['/usr/bin/gpucapture', 'list'], capture_output=True,
                                             text=True, timeout=25, check=True)
                    # Discard unrelated application identities; retain only our own child.
                    target_line = next((s for s in listing.stdout.splitlines()
                                        if re.search(r'(?<!\d)' + str(child.pid) + r'(?!\d)', s)), None)
                    if target_line:
                        break
                    if child.poll() is not None:
                        raise RuntimeError('Probe exited before it registered for capture')
                    time.sleep(0.25)
                report['capturable'] = target_line is not None
                if not target_line:
                    raise RuntimeError('Independent x86-64 probe did not become capturable')
                print('Independent x86-64 Vulkan probe is capturable.', flush=True)
                boundaries = subprocess.run(['/usr/bin/gpucapture', 'boundaries', '--pid', str(child.pid)],
                                            capture_output=True, text=True, check=True, timeout=15)
                (evidence / 'boundaries.log').write_text(boundaries.stdout + boundaries.stderr)
                capture = subprocess.run(['/usr/bin/gpucapture', 'start', '--pid', str(child.pid),
                                          '--until-exit', '--output', str(trace)],
                                         capture_output=True, text=True, timeout=55)
                (evidence / 'capture.log').write_text(capture.stdout + capture.stderr)
                report['capture_exit'] = capture.returncode
                if capture.returncode:
                    raise RuntimeError('Probe capture command failed; see ' + str(evidence))
            report['probe_exit'] = child.wait(timeout=40)
            if report['probe_exit'] or not trace.exists():
                raise RuntimeError('Probe capture failed; see ' + str(evidence))
            print('Independent Vulkan workload captured; GPU copy passed.', flush=True)
            replay = subprocess.run(['/usr/bin/gpudebug', '-t', str(trace), '--oneshot', '--json',
                                     '-c', 'list', '-c', 'go commands', '-c', 'list'],
                                    capture_output=True, text=True, timeout=55)
            (evidence / 'replay.log').write_text(replay.stdout + replay.stderr)
            report['replay_exit'] = replay.returncode
            if replay.returncode or 'error:' in (replay.stdout + replay.stderr).lower():
                raise RuntimeError('GPU replay failed; see ' + str(evidence))
            trees = [json.loads(line) for line in replay.stdout.splitlines() if line.startswith('{')]
            if len(trees) < 2 or not any(c.get('name') == 'commands' for c in trees[0].get('children', [])) or trees[-1].get('totalCount', 0) < 1:
                raise RuntimeError('Replay did not expose the captured GPU command buffers')
            report['capture_and_replay_passed'] = True
            print('GPU trace replay/command inspection passed.', flush=True)
        except BaseException as error:
            report['error'] = str(error)
            raise
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=3)
            (evidence / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
            (work / 'host-private/capture-validation-result.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
