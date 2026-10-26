#!/usr/bin/env python3
"""Build a standalone control .app/ZIP; existing apps and source runtimes are preserved."""
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


def stamp_runtime_override(resources, sidecar):
    path = resources / 'runtime/manifest.json'
    manifest = json.loads(path.read_text())
    manifest['localOverrides'] = {'moltenvk': sidecar}
    path.write_text(json.dumps(manifest, indent=2) + '\n')


def append_sbom(directory, sidecar):
    with (directory / 'SBOM.md').open('a') as stream:
        stream.write('\n## Rebuilt MoltenVK control\n\n'
                     'The bundled MoltenVK driver is the rebuilt control, SHA-256 `' +
                     sidecar['control_dylib_sha256'] + '`. The archive row above records the '
                     'Highball reference input. The control uses upstream commit `' +
                     sidecar['source_commit'] + '` with the three pinned Highball patches. '
                     'See the bundled moltenvk-control-build.json for exact build inputs and flags.\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, default=ROOT / 'vendor/rdr2-runtime-r27-portable-v3')
    parser.add_argument('--control', type=Path, default=ROOT / 'vendor/tree-research/artifacts/control')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/control-app/RDR2 MoltenVK Control.app')
    parser.add_argument('--archive', type=Path, default=ROOT / 'dist/RDR2-MoltenVK-Control-development.zip')
    args = parser.parse_args()
    app = args.output.absolute()
    archive = args.archive.absolute()
    if app.exists() or app.is_symlink() or app.suffix != '.app':
        parser.error('Choose a NEW .app output path; no existing app is replaced')
    if archive.exists() or archive.is_symlink() or archive.suffix != '.zip':
        parser.error('Choose a NEW --archive .zip path; existing archives are preserved')
    source = args.control.resolve() / 'libMoltenVK.dylib'
    metadata = json.loads((args.control / 'build.json').read_text())
    if (metadata.get('mode') != 'control' or metadata.get('pins') != PINS or
            metadata.get('architecture') != 'x86_64' or digest(source) != metadata.get('sha256')):
        parser.error('Control provenance/hash/architecture differs')
    original = args.runtime.resolve() / 'frameworks/libMoltenVK.dylib'
    if digest(original) != PINS['moltenvk']['reference_dylib_sha256']:
        parser.error('Source runtime is not the pinned reference; no build was started')
    run(['codesign', '--verify', '--strict', source])
    env = dict(os.environ, RDR2_BUILD_OUTPUT=str(app))
    run([ROOT / 'packaging/build-app.sh', '--runtime', args.runtime.resolve()], cwd=ROOT, env=env)
    resources = app / 'Contents/Resources'
    target = resources / 'runtime/frameworks/libMoltenVK.dylib'
    if not target.resolve().is_relative_to(app.resolve()) or target.is_symlink() or os.path.samefile(target, original):
        raise ValueError('Replacement destination is not a private regular file in the new app')
    shutil.copy2(source, target)
    info_path = app / 'Contents/Info.plist'
    info = plistlib.loads(info_path.read_bytes())
    info.update({'CFBundleIdentifier': 'org.rdr2launcher.moltenvk-control',
                 'CFBundleName': 'RDR2 MoltenVK Control', 'CFBundleDisplayName': 'RDR2 MoltenVK Control',
                 'CFBundleVersion': '2', 'RDR2LauncherEdition': 'moltenvk-control'})
    info_path.write_bytes(plistlib.dumps(info))
    shutil.copy2(args.control / 'build.json', resources / 'moltenvk-control-build.json')
    shutil.copy2(HERE / 'CONTROL-APP.md', resources / 'CONTROL-TEST.md')
    notices = resources / 'runtime/licenses/moltenvk-control'
    notices.mkdir(parents=True)
    for source_notice in (HERE / 'patches').iterdir():
        if source_notice.name.startswith('LICENSE-') or source_notice.name == 'NOTICE.md':
            shutil.copy2(source_notice, notices / source_notice.name)
    sidecar = {'edition': 'moltenvk-control', 'renderer': 'rebuilt Highball-patched MoltenVK 1.4.2 control',
               'default_data_directory': 'RDR2Launcher-MoltenVK-Control',
               'control_dylib_sha256': digest(source), 'source_commit': PINS['moltenvk']['commit'],
               'candidate_patch_included': False, 'gameplay_verified': False, 'tree_fix_verified': False}
    (resources / 'tree-control.json').write_text(json.dumps(sidecar, indent=2) + '\n')
    stamp_runtime_override(resources, sidecar)
    run([ROOT / 'packaging/sign-app.sh', app, '-'], cwd=ROOT)
    # Preserve the exact independently signed control bytes if generic nested signing
    # chose a different identifier; then regenerate hashes and sign the outer app.
    if digest(target) != metadata['sha256']:
        shutil.copy2(source, target)
        run(['python3', ROOT / 'packaging/runtime_tools.py', 'manifest', resources])
        run(['codesign', '--force', '--sign', '-', app])
    run(['codesign', '--verify', '--deep', '--strict', app])
    assert digest(target) == metadata['sha256']
    assert digest(original) == PINS['moltenvk']['reference_dylib_sha256']
    diagnostic = subprocess.check_output([str(app / 'Contents/MacOS/RDR2Launcher'), '--diagnose'], text=True)
    if ('Launcher edition: moltenvk-control' not in diagnostic or
            'Default data folder: RDR2Launcher-MoltenVK-Control' not in diagnostic):
        raise ValueError('Built app did not select its isolated control edition')
    print(diagnostic)
    with (app.parent / 'dependency-audit.json').open('w') as audit:
        run([ROOT / 'packaging/audit-deps.sh', app], stdout=audit)
    run(['python3', ROOT / 'packaging/report.py', app, app.parent])
    append_sbom(app.parent, sidecar)
    shutil.copy2(HERE / 'CONTROL-APP.md', app.parent / 'CONTROL-TEST.md')
    report = app.parent / 'TEST-REPORT.md'
    with report.open('a') as stream:
        stream.write('\n# Standalone MoltenVK control app\n\n' + diagnostic + '\n' +
                     'Exact bundled control SHA-256: ' + metadata['sha256'] + '\n\n' +
                     'Separate default data folder; no candidate patch, game or account state.\n' +
                     'Host startup, gameplay and tree behavior remain unverified.\n')
    archive.parent.mkdir(parents=True, exist_ok=True)
    run(['/usr/bin/ditto', '-c', '-k', '--keepParent', app, archive])
    (archive.parent / 'RDR2-MoltenVK-Control-SHA256SUMS').write_text(digest(archive) + '  ' + archive.name + '\n')
    print('Standalone control app: ' + str(app) + '\nCopy archive: ' + str(archive))


if __name__ == '__main__':
    main()
