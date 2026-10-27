#!/usr/bin/env python3
"""Export each confirmed camera pose using one owned GPU replay session."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time
import uuid

from build import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pair', type=Path,
                        default=ROOT / 'vendor/tree-research/host-private/captures/camera-pair-active.json',
                        help='camera-pair manifest; select a separate manifest to preserve earlier tree evidence')
    parser.add_argument('--state', choices=['visible', 'missing'], required=True)
    parser.add_argument('--keep-session', action='store_true')
    args = parser.parse_args()
    pair_path = args.pair.resolve()
    pair = json.loads(pair_path.read_text())
    evidence = Path(pair[args.state + '_capture'])
    capture = json.loads((evidence / 'capture.json').read_text())
    if not capture['capture_completed'] or capture['renderer_sha256'] != pair['renderer_sha256'] or capture['pid'] != pair['game_pid']:
        raise ValueError('Camera-pair capture identity differs')
    rows = subprocess.check_output(['/bin/ps', '-axo', 'comm='], text=True).splitlines()
    if any(s.strip().replace('\\', '/').rsplit('/', 1)[-1].lower() == 'rdr2.exe' for s in rows):
        raise RuntimeError('Close RDR2 before loading the large replay')
    trace = evidence / 'rdr2.gputrace'
    output = evidence / ('analysis-pair-' + uuid.uuid4().hex)
    output.mkdir(mode=0o700)
    prior = pair.setdefault('analysis_paths', {}).get(args.state)
    if prior:
        pair.setdefault('analysis_history', {}).setdefault(args.state, []).append(prior)
    pair['analysis_paths'][args.state] = str(output)
    pair_path.write_text(json.dumps(pair, indent=2) + '\n')
    session = None
    count = 0

    def call(commands, opening=False, timeout=55):
        nonlocal count, session
        command = ['/usr/bin/gpudebug'] + (['-t', str(trace), '--timeout', '600'] if opening else ['-s', str(session)]) + ['--json']
        for text in commands:
            command.extend(['-c', text])
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        count += 1
        (output / ('request-%03d.log' % count)).write_text(result.stdout + result.stderr)
        if opening:
            found = re.search(r'^Session (\d+) created\.$', result.stdout, re.M)
            if not found:
                raise RuntimeError('No owned replay session was created')
            session = int(found.group(1))
            (output / 'owned-session.json').write_text(json.dumps({'session_id': session, 'trace': str(trace)}, indent=2) + '\n')
        if result.returncode or re.search(r'(?im)^\s*error:', result.stdout + '\n' + result.stderr):
            raise RuntimeError('GPU inspection request failed; see ' + str(output))
        data = [json.loads(line) for line in result.stdout.splitlines() if line.startswith(('{', '['))]
        if any(isinstance(row, dict) and 'error' in row for row in data):
            raise RuntimeError('GPU inspection returned an error object')
        return data

    try:
        status = call(['status'], opening=True)
        if not any(row.get('trace') == str(trace) for row in status if isinstance(row, dict)):
            raise RuntimeError('Replay opened another trace')
        print(args.state + ': owned replay session ' + str(session), flush=True)
        buffers = call(['go /commands', 'list --all'])[-1]
        (output / 'command-buffers.json').write_text(json.dumps(buffers, indent=2) + '\n')
        encoders = {}
        final = None
        for cb in reversed(buffers['children']):
            # The CLI's go command emits a misleading info error for an empty
            # command buffer. Its already-listed encoder count lets us skip it.
            if any(isinstance(value, dict) and value.get('value') == '0 encoders' for value in cb.get('values', [])):
                continue
            cb_path = '/commands/' + cb['name']
            listing = call(['go ' + cb_path, 'list --all'])[-1]
            encoders[cb['name']] = listing
            for encoder in reversed(listing.get('children', [])):
                if not re.fullmatch(r're\d+', encoder['name']):
                    continue
                path = cb_path + '/' + encoder['name']
                children = call(['go ' + path, 'list --all'])[-1]
                if any(c['name'] == 'color0' and 'CAMetalLayer Drawable' in json.dumps(c) for c in children.get('children', [])):
                    final = path
                    (output / 'final-encoder.json').write_text(json.dumps(children, indent=2) + '\n')
                    break
            if final:
                break
        if not final:
            raise RuntimeError('No captured presentation render target found')
        (output / 'encoders-inspected.json').write_text(json.dumps(encoders, indent=2) + '\n')
        api = call(['go /api_calls', 'list --all'])[-1]
        (output / 'api-calls.json').write_text(json.dumps(api, indent=2) + '\n')
        deadline = time.monotonic() + 120
        while True:
            status = call(['status'])[-1]
            (output / 'replay-status.json').write_text(json.dumps(status, indent=2) + '\n')
            if status.get('replayer', {}).get('state') == 'ready':
                break
            if time.monotonic() > deadline:
                raise RuntimeError('Replay did not become ready within the bounded wait')
            time.sleep(2)
        image = output / (args.state + '.png')
        fetched = call(['go ' + final, 'fetch color0 --out ' + str(image)])
        if not image.is_file() or image.stat().st_size == 0:
            raise RuntimeError('No exported scene image')
        result = {'state': args.state, 'pair_id': pair['pair_id'], 'session_id': session,
                  'trace': str(trace), 'final_encoder': final, 'image': str(image),
                  'image_bytes': image.stat().st_size, 'capture_pid': capture['pid'],
                  'renderer_sha256': capture['renderer_sha256'], 'visual_failure_reproduced': 'not yet assessed'}
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print('Scene exported: ' + str(image), flush=True)
    finally:
        if session is not None and not args.keep_session:
            closed = subprocess.run(['/usr/bin/gpudebug', '--terminate', str(session)], capture_output=True, text=True, timeout=20)
            (output / 'session-close.log').write_text(closed.stdout + closed.stderr)
            print('Released owned replay session ' + str(session), flush=True)


if __name__ == '__main__':
    main()
