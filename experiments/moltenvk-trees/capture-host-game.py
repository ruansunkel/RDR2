#!/usr/bin/env python3
"""Inspect an isolated RDR2 capture target; capture at most four frames on request.

The default is read-only. This never launches a game, attaches a debugger,
changes security settings, or stops any process. A timed-out capture is stopped
only through gpucapture's explicit --pid option after target revalidation.
"""
import argparse
import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

from build import ROOT, HERE, digest


GPUCAPTURE = '/usr/bin/gpucapture'
ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')


def clean(text):
    return ANSI.sub('', text)


def processes():
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,comm='], capture_output=True,
                            text=True, check=True, timeout=10)
    rows = {}
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 1)
        if len(fields) == 2 and fields[0].isdigit():
            rows[int(fields[0])] = fields[1]
    return rows


def game_identity(data):
    matches = [(pid, comm) for pid, comm in processes().items()
               if comm.replace('\\', '/').rsplit('/', 1)[-1].lower() == 'rdr2.exe'
               and data.name in comm]
    if len(matches) != 1:
        raise RuntimeError('Expected exactly one RDR2.exe in the isolated candidate environment; found ' + str(len(matches)))
    return matches[0]


def verify_target(pid, comm, library, expected):
    if processes().get(pid) != comm:
        raise RuntimeError('The verified RDR2 process identity changed; no capture action was requested')
    result = subprocess.run(['/usr/sbin/lsof', '-a', '-p', str(pid), '-Fn'],
                            capture_output=True, text=True, timeout=10)
    paths = [Path(line[1:]) for line in result.stdout.splitlines()
             if line.startswith('n') and 'MoltenVK' in line and line.endswith('.dylib')]
    if result.returncode or not paths or any(path.resolve() != library for path in paths):
        raise RuntimeError('RDR2 does not map only the exact expected app MoltenVK library')
    if digest(library) != expected:
        raise RuntimeError('Mapped driver bytes differ from the candidate profile')
    if processes().get(pid) != comm:
        raise RuntimeError('RDR2 exited or changed identity during renderer verification')


def gpu_command(arguments, timeout):
    result = subprocess.run([GPUCAPTURE, *arguments], capture_output=True,
                            text=True, timeout=timeout)
    output = clean(result.stdout + '\n' + result.stderr)
    # The CLI can return zero after a sandbox/service connection error.
    if result.returncode or re.search(r'(?im)(?:\berror\s*:|cannot connect|unable to connect)', output):
        raise RuntimeError('The scoped GPU tool request failed or could not connect to its service')
    return output


def target_is_capturable(output, pid):
    # PID is a distinct numeric table field, never a substring of a name/PID.
    # Do not retain or print any unrelated capturable application identities.
    matches = [line for line in clean(output).splitlines()
               if re.match(r'^\s*' + str(pid) + r'\s+\d+\s+', line)]
    if len(matches) != 1:
        return False
    # Device zero is this host. Never let a coincident remote PID select a
    # remote process when the locally verified game is not capturable.
    if not re.match(r'^\s*' + str(pid) + r'\s+0\s+', matches[0]):
        return False
    return not re.search(r'\[(?:suspended|non-debuggable)\]', matches[0], re.IGNORECASE)


def boundaries_for(output, pid):
    text = clean(output)
    headers = re.findall(r'(?im)^\s*boundaries for\s+(\d+)\b', text)
    if headers != [str(pid)]:
        raise RuntimeError('GPU boundary output did not identify exactly the verified game PID')
    boundaries = []
    for line in text.splitlines():
        match = re.match(r'^\s*(\d+)\s+(Layer|Scope|Device|Queue)\b(.*)$', line)
        if match:
            boundaries.append({'id': int(match[1]), 'type': match[2], 'details': match[3].strip()})
    if not boundaries or len({row['id'] for row in boundaries}) != len(boundaries):
        raise RuntimeError('No unique capturable boundary table was found for this game')
    return boundaries


def process_events(data, pid):
    marker = data / 'state/tree-allocation-events.log'
    if not marker.exists():
        return []
    prefix = 'pid=' + str(pid) + ' '
    # Accept only the fixed diagnostic vocabulary, not arbitrary client output.
    return sorted({line[len(prefix):] for line in marker.read_text().splitlines()
                   if line.startswith(prefix) and re.fullmatch(r'[a-z0-9-]{1,96}', line[len(prefix):])})


def trace_size(trace):
    if trace.is_symlink() or not trace.exists():
        return {'exists': False, 'files': 0, 'bytes': 0}
    files = [trace] if trace.is_file() else [p for p in trace.rglob('*') if p.is_file() and not p.is_symlink()]
    return {'exists': True, 'files': len(files), 'bytes': sum(p.stat().st_size for p in files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, default=ROOT / 'dist/tree-query-results/RDR2 Trees Query Results.app')
    parser.add_argument('--data-root', type=Path, default=Path.home() / 'Library/Application Support/RDR2Launcher-MoltenVK-Candidate')
    parser.add_argument('--capture', action='store_true', help='capture the verified game; default only inspects')
    parser.add_argument('--frames', type=int, default=2, help='boundary iterations, 1–4; default 2 Layer frames')
    parser.add_argument('--boundary', type=int, help='explicit numeric boundary ID; otherwise requires exactly one Layer')
    args = parser.parse_args()
    if not 1 <= args.frames <= 4:
        parser.error('--frames must be between 1 and 4')
    if args.boundary is not None and args.boundary < 0:
        parser.error('--boundary must be a nonnegative numeric ID')
    app, data = args.app.resolve(), args.data_root.resolve()
    if data.name != 'RDR2Launcher-MoltenVK-Candidate':
        parser.error('Only the isolated candidate data root is supported')
    resources = app / 'Contents/Resources'
    profile = json.loads((resources / 'tree-candidate.json').read_text())
    if profile.get('default_data_directory') != data.name or profile.get('candidate_patch_included') is not True:
        parser.error('App profile does not identify the isolated candidate environment')
    library = (resources / 'runtime/frameworks/libMoltenVK.dylib').resolve()
    if not library.is_relative_to(app):
        parser.error('The expected renderer must be private to this app')
    expected = profile['candidate_dylib_sha256']
    pid, comm = game_identity(data)
    verify_target(pid, comm, library, expected)
    listing = gpu_command(['list'], 15)
    capturable = target_is_capturable(listing, pid)
    del listing
    if not capturable:
        raise RuntimeError('The verified RDR2 PID is not uniquely listed as capturable; no capture was requested')
    boundaries = boundaries_for(gpu_command(['boundaries', '--pid', str(pid), '--device', '0'], 15), pid)
    print('Verified candidate RDR2 PID:', pid)
    print('Exact renderer mapping/hash verified; game is listed as capturable.')
    print('Boundaries for this game only:')
    for row in boundaries:
        print('  {id}  {type}  {details}'.format(**row))
    if not args.capture:
        print('Read-only inspection complete; no capture started.')
        return
    if args.boundary is None:
        layers = [row for row in boundaries if row['type'] == 'Layer']
        if len(layers) != 1:
            raise RuntimeError('Automatic frame selection requires exactly one Layer; specify its numeric --boundary after inspection')
        boundary = layers[0]
    else:
        selected = [row for row in boundaries if row['id'] == args.boundary]
        if len(selected) != 1:
            raise RuntimeError('Requested boundary does not belong to the verified game')
        boundary = selected[0]
    # Specify the proven Layer ID explicitly rather than permit fallback to Device.
    verify_target(pid, comm, library, expected)
    private = ROOT / 'vendor/tree-research/host-private/captures'
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    evidence = private / ('game-' + uuid.uuid4().hex)
    evidence.mkdir(mode=0o700)
    trace = evidence / 'rdr2.gputrace'
    command = [GPUCAPTURE, 'start', '--pid', str(pid), '--device', '0', '--boundary', str(boundary['id']),
               '--count', str(args.frames), '--output', str(trace),
               '--disable-unused-recording', '--disable-backtrace-recording']
    report = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'app': str(app), 'data_root': str(data), 'pid': pid, 'process_kind': 'RDR2.exe',
              'renderer_path': str(library), 'renderer_sha256': expected,
              'script_sha256': digest(HERE / 'capture-host-game.py'),
              'capture_arguments': command, 'boundary': boundary, 'boundary_count': args.frames,
              'native_events_before': process_events(data, pid),
              'debugger_attached': False, 'security_settings_changed': False,
              'visual_fix_claimed': False, 'capture_completed': False}
    print('Capturing', args.frames, boundary['type'], 'iterations from only PID', pid, flush=True)
    try:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=55)
            (evidence / 'capture.log').write_text(clean(result.stdout + '\n' + result.stderr))
            report['capture_exit'] = result.returncode
            if result.returncode or re.search(r'(?im)\berror\s*:', clean(result.stdout + '\n' + result.stderr)):
                raise RuntimeError('Scoped capture failed; its output and any partial trace are preserved')
            report['capture_completed'] = trace.exists()
            if not report['capture_completed']:
                raise RuntimeError('Capture command produced no trace; evidence is preserved')
        except subprocess.TimeoutExpired as error:
            report['capture_timeout'] = True
            partial = ''.join(part.decode(errors='replace') if isinstance(part, bytes) else (part or '')
                              for part in [error.stdout, error.stderr])
            (evidence / 'capture.log').write_text(clean(partial))
            # Stop only our exact live target. Never use --all, signals, or a
            # process group. If identity verification fails, do not send a stop.
            try:
                verify_target(pid, comm, library, expected)
                stopped = gpu_command(['stop', '--pid', str(pid), '--device', '0'], 15)
                (evidence / 'stop.log').write_text(stopped)
                report['scoped_stop_requested_after_timeout'] = True
            except (RuntimeError, subprocess.SubprocessError) as stop_error:
                report['scoped_stop_requested_after_timeout'] = False
                report['stop_error'] = str(stop_error)
            raise RuntimeError('Capture timed out; only the verified PID was eligible for a scoped stop. Partial evidence is preserved') from error
    except BaseException as error:
        report['error'] = str(error)
        raise
    finally:
        report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        report['native_events_after'] = process_events(data, pid)
        report['trace'] = trace_size(trace)
        (evidence / 'capture.json').write_text(json.dumps(report, indent=2) + '\n')
        print('Capture evidence:', evidence, flush=True)
    print('Capture complete:', trace)
    print('Trace bytes:', report['trace']['bytes'], '; no visual-fix claim is made.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
