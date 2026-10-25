#!/usr/bin/env python3
"""Build-time runtime integrity, relocation and dependency checks (stdlib only)."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

MACHO = {b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xcf',
         b'\xfe\xed\xfa\xce', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca', b'\xca\xfe\xba\xbf'}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def within(path, root):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, RuntimeError):
        return False


def system_path(path):
    path = os.path.normpath(path)
    return path.startswith(('/usr/lib/', '/System/Library/'))


def macho(path):
    with path.open('rb') as stream:
        return stream.read(4) in MACHO


def inventory(resources):
    records = []
    runtime = resources / 'runtime'
    if not runtime.is_dir():
        raise ValueError('No runtime staged; launcher-only previews cannot be packaged as releases')
    for path in sorted(runtime.rglob('*')):
        if path.is_symlink():
            if os.path.isabs(os.readlink(path)) or not within(path, runtime) or not path.exists():
                raise ValueError(f'Escaping, absolute or broken runtime link: {path}')
            records.append({'path': str(path.relative_to(resources)), 'symlink': os.readlink(path)})
        elif path.is_file():
            records.append({'path': str(path.relative_to(resources)), 'sha256': sha256(path)})
    return records


def write_manifest(resources):
    upstream = json.loads((resources / 'engine-upstream.json').read_text())
    required = ['engine/bin/wine', 'frameworks/libMoltenVK.dylib',
                'renderers/dxmt/wine/x86_64-windows/d3d11.dll']
    for item in required:
        if not (resources / 'runtime' / item).is_file():
            raise ValueError(f'Required runtime file missing: {item}')
    manifest = {'engineID': upstream['id'], 'wine': 'runtime/engine/bin/wine',
                'baseEnv': upstream['baseEnv'], 'files': inventory(resources)}
    (resources / 'runtime-manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')


def resolve_reference(ref, binary, executable, rpaths, root):
    def expand(value):
        return value.replace('@loader_path', str(binary.parent)).replace('@executable_path', str(executable.parent))
    if ref.startswith('@rpath/'):
        candidates = [expand(r) + ref[len('@rpath'):] for r in rpaths]
    else:
        candidates = [expand(ref)]
    for candidate in candidates:
        if system_path(os.path.normpath(candidate)):
            return True
        path = Path(os.path.normpath(candidate))
        if path.is_absolute() and path.exists() and within(path, root):
            return True
    return False


def audit(app):
    root = app.resolve()
    failures, binaries = [], []
    for path in sorted(root.rglob('*')):
        rel = str(path.relative_to(root))
        if any(part.lower() in {'d3dmetal.framework', 'd3dmetal', 'd3dmetal-tsshim', 'steamapps',
                               'loginusers.vdf', 'userdata', 'system.reg', 'user.reg'} for part in path.parts):
            failures.append(f'Forbidden redistributable/account state: {rel}')
        if path.is_symlink():
            if os.path.isabs(os.readlink(path)) or not within(path, root) or not path.exists():
                failures.append(f'Escaping, absolute or broken symlink: {rel}')
            continue
        if path.is_file() and macho(path):
            binaries.append(path)
    for binary in binaries:
        deps = subprocess.check_output(['/usr/bin/otool', '-L', str(binary)], text=True)
        ids = subprocess.check_output(['/usr/bin/otool', '-D', str(binary)], text=True).splitlines()[1:]
        loads = subprocess.check_output(['/usr/bin/otool', '-l', str(binary)], text=True).splitlines()
        rpaths = []
        for index, line in enumerate(loads):
            if line.strip() == 'cmd LC_RPATH':
                for following in loads[index + 1:index + 5]:
                    if following.strip().startswith('path '):
                        rpaths.append(following.strip()[5:].rsplit(' (offset ', 1)[0])
        executable = root / 'Contents/MacOS/RDR2Launcher'
        if os.access(binary, os.X_OK) and 'bin' in binary.parts:
            executable = binary
        for rpath in rpaths:
            if rpath.startswith('/') and not system_path(rpath + '/'):
                failures.append(f'Absolute non-system RPATH: {binary.relative_to(root)} -> {rpath}')
        for line in deps.splitlines():
            if ' (compatibility version ' not in line:
                continue
            ref = line.strip().split(' (compatibility version ', 1)[0]
            # otool -L includes a dylib's own LC_ID_DYLIB; inspect via otool -D to exclude it.
            if ref in [s.strip() for s in ids]:
                if ref.startswith('/') and not system_path(ref):
                    failures.append(f'Non-relocatable dylib ID: {ref}')
                continue
            if not resolve_reference(ref, binary, executable, rpaths, root):
                failures.append(f'Unresolved/outside dependency: {binary.relative_to(root)} -> {ref}')
    print(json.dumps({'macho_files': len(binaries), 'failures': failures,
                      'note': 'Static audit only; dynamic loads and gameplay require relocation/host tests.'}, indent=2))
    return not failures


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in {'manifest', 'audit', 'prune-launcher-rpaths'}:
        raise ValueError('Usage: runtime_tools.py manifest RESOURCES | audit APP | prune-launcher-rpaths APP')
    path = Path(sys.argv[2]).resolve(strict=True)
    if sys.argv[1] == 'manifest':
        write_manifest(path)
    elif sys.argv[1] == 'prune-launcher-rpaths':
        # Only our newly compiled native launcher: never rewrite vendor runtime binaries.
        binary = path / 'Contents/MacOS/RDR2Launcher'
        lines = subprocess.check_output(['/usr/bin/otool', '-l', str(binary)], text=True).splitlines()
        for i, line in enumerate(lines):
            if line.strip() == 'cmd LC_RPATH':
                for following in lines[i + 1:i + 5]:
                    if following.strip().startswith('path '):
                        value = following.strip()[5:].rsplit(' (offset ', 1)[0]
                        if value.startswith('/') and not system_path(value):
                            subprocess.run(['/usr/bin/install_name_tool', '-delete_rpath', value, str(binary)], check=True)
    elif not audit(path):
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
