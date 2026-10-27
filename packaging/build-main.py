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

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def validate_artifact(artifact, accepted, pins):
    metadata = json.loads((artifact / 'build.json').read_text())
    if (metadata.get('mode') != accepted['mode'] or
            metadata.get('architecture') != 'x86_64' or
            metadata.get('pins') != pins or
            metadata.get('sha256') != accepted['sha256'] or
            digest(artifact / 'libMoltenVK.dylib') != accepted['sha256']):
        raise ValueError('Renderer differs from the accepted build; rebuild/validate it through experiments/moltenvk-trees first')
    return metadata


def run(*args, **kwargs):
    return subprocess.run(list(map(str, args)), check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/RDR2Launcher.app')
    args = parser.parse_args()
    output = args.output.absolute()
    if output.suffix != '.app' or output.is_symlink() or (output.exists() and not output.is_dir()):
        parser.error('Output must be an app directory, not a symlink')
    accepted = json.loads((ROOT / 'config/accepted-renderer.json').read_text())
    pins = json.loads((ROOT / 'experiments/moltenvk-trees/pins.json').read_text())
    artifact = ROOT / accepted['artifact']
    runtime = ROOT / accepted['runtime']
    metadata = validate_artifact(artifact, accepted, pins)
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
            'CFBundleDisplayName': 'RDR2 Launcher', 'CFBundleVersion': '5',
            'RDR2LauncherEdition': 'patched',
            'RDR2LauncherSubtitle': 'Steam edition · Story Mode · Vulkan / patched MoltenVK\nTree, foliage and rock workarounds included.',
            'RDR2RendererVariant': accepted['mode'], 'RDR2TreeFixEnabled': True})
        info_path.write_bytes(plistlib.dumps(info))
        shutil.copy2(artifact / 'build.json', resources / 'moltenvk-candidate-build.json')
        (resources / 'accepted-renderer.json').write_text(json.dumps(accepted, indent=2) + '\n')
        notices = resources / 'runtime/licenses/moltenvk-local-patches'
        notices.mkdir(parents=True, exist_ok=True)
        for patch in (ROOT / 'experiments/moltenvk-trees/patches').glob('*.patch'):
            shutil.copy2(patch, notices / patch.name)
        for header in (ROOT / 'experiments/moltenvk-trees').glob('*-hiz-workaround.h'):
            shutil.copy2(header, notices / header.name)
        shutil.copy2(ROOT / 'experiments/moltenvk-trees/pins.json', notices / 'pins.json')
        manifest_path = resources / 'runtime/manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['localOverrides'] = {'moltenvk': accepted}
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
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
                'Default data folder: ' + accepted['data_directory'] not in result):
            raise ValueError('Main app selected the wrong default environment')
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
    print('Built main app:', output)
    print('Renderer SHA256:', metadata['sha256'])


if __name__ == '__main__':
    main()
