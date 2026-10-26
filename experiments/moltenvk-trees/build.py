#!/usr/bin/env python3
"""Build pinned controls; candidate builds require recorded host control acceptance."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PINS = json.loads((HERE / 'pins.json').read_text())


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def run(args, **kwargs):
    return subprocess.run(list(map(str, args)), check=True, **kwargs)


def fetch(url, path, expected):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if digest(path) != expected:
            raise ValueError('Existing download checksum differs: ' + str(path))
        return
    temporary = path.with_suffix(path.suffix + '.partial')
    try:
        with urllib.request.urlopen(url, timeout=45) as source, temporary.open('wb') as dest:
            shutil.copyfileobj(source, dest)
        if digest(temporary) != expected:
            raise ValueError('Downloaded checksum differs: ' + url)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def prepare_source(work, mode):
    source = work / (mode + '-source')
    if not source.exists():
        source.mkdir(parents=True)
        run(['git', 'init', '-q', source])
        run(['git', '-C', source, 'remote', 'add', 'origin', PINS['moltenvk']['repository']])
        run(['git', '-C', source, 'fetch', '--depth=1', 'origin', PINS['moltenvk']['commit']])
        run(['git', '-C', source, 'checkout', '--detach', 'FETCH_HEAD'])
    head = subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD'], text=True).strip()
    if head != PINS['moltenvk']['commit']:
        raise ValueError('Refusing to change a source tree at another commit')
    patches = PINS['moltenvk']['patches'][:]
    if mode.startswith('candidate'):
        patches.append(PINS['candidate'])
        patches.extend(PINS['candidate'].get('variants', {}).get(mode, {}).get('patches', []))
    for item in patches:
        if digest(HERE / 'patches' / item['file']) != item['sha256']:
            raise ValueError('Patch checksum differs: ' + item['file'])
    changed = subprocess.check_output(['git', '-C', source, 'diff', '--name-only'], text=True).splitlines()
    if not changed:
        for item in patches:
            patch = HERE / 'patches' / item['file']
            run(['git', '-C', source, 'apply', '--check', patch])
            run(['git', '-C', source, 'apply', patch])
    expected = dict(PINS['moltenvk']['control_files'])
    if mode.startswith('candidate'):
        expected.update(PINS['candidate']['files'])
        expected.update(PINS['candidate'].get('variants', {}).get(mode, {}).get('files', {}))
    added = PINS['candidate'].get('variants', {}).get(mode, {}).get('added_files', {})
    changed = subprocess.check_output(['git', '-C', source, 'diff', '--name-only'], text=True).splitlines()
    untracked = subprocess.check_output(['git', '-C', source, 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
    if (set(changed) != set(expected) or set(untracked) != set(added) or
            any(digest(source / p) != h for p, h in {**expected, **added}.items())):
        raise ValueError('Source changes differ from the pinned patch set; no reset was attempted')
    for name, revision in PINS['dependencies'].items():
        if (source / 'ExternalRevisions' / (name + '_repo_revision')).read_text().strip() != revision:
            raise ValueError('Dependency revision differs: ' + name)
    return source


def prepare_tools(work):
    item = PINS['cmake']
    archive = work / 'downloads' / ('cmake-' + item['version'] + '-verified.tar.gz')
    fetch(item['url'], archive, item['sha256'])
    tools = work / 'tools'
    binary = tools / item['directory'] / 'CMake.app/Contents/bin/cmake'
    if not binary.exists():
        # Reuse the repository's traversal/link-safe extractor, into a NEW directory.
        sys.path.insert(0, str(ROOT / 'packaging'))
        spec = importlib.util.spec_from_file_location('verified_extract', ROOT / 'packaging/extract-verified.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tools.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='unpack-', dir=work) as tmp:
            module.extract(archive, Path(tmp))
            shutil.move(str(Path(tmp) / item['directory']), tools / item['directory'])
    member = item['directory'] + '/CMake.app/Contents/bin/cmake'
    with tarfile.open(archive) as tar:
        expected = hashlib.sha256(tar.extractfile(member).read()).hexdigest()
    if digest(binary) != expected:
        raise ValueError('Extracted CMake executable differs from its verified archive')
    cpm = PINS['cpm']
    fetch(cpm['url'], work / 'cpm/cpm' / ('CPM_' + cpm['version'] + '.cmake'), cpm['sha256'])
    return binary


def require_control(evidence, work):
    if evidence is None:
        raise ValueError('Candidate deferred: supply --control-evidence after the control launches RDR2 on the physical host')
    report = json.loads(evidence.read_text())
    # A host user can report a successful control run without having recorded
    # video. Preserve that weaker evidence explicitly instead of inventing a
    # capture or claiming a historical loaded-library mapping.
    if report.get('evidence_basis') == 'user-reported-signed-control-app':
        app = Path(report.get('control_app', ''))
        if not app.is_absolute() or app.suffix != '.app':
            raise ValueError('User-reported control requires an absolute control app path')
        resources = app / 'Contents/Resources'
        control = resources / 'runtime/frameworks/libMoltenVK.dylib'
        metadata = json.loads((resources / 'moltenvk-control-build.json').read_text())
        profile = json.loads((resources / 'tree-control.json').read_text())
        control_pins = {k: v for k, v in PINS.items() if k != 'candidate'}
        recorded_control_pins = {k: v for k, v in metadata.get('pins', {}).items() if k != 'candidate'}
        if (report.get('engine_id') != PINS['engine_id'] or recorded_control_pins != control_pins or
                metadata.get('mode') != 'control' or profile.get('candidate_patch_included') is not False or
                metadata.get('sha256') != digest(control) or
                report.get('control_dylib_sha256') != digest(control) or
                report.get('story_mode_controllable') is not True or
                report.get('baseline_tree_disappearance_reproduced') is not True):
            raise ValueError('Reported host control does not match the signed baseline or required observations')
        observation = Path(report.get('user_observation', ''))
        if not observation.is_absolute() or not observation.is_file() or observation.stat().st_size == 0:
            raise ValueError('Missing recorded user observation')
        run(['codesign', '--verify', '--deep', '--strict', app])
        print('Control accepted from the user report and signed app provenance. '
              'No video or historical RDR2 loaded-library proof is claimed.', flush=True)
        return
    control = work / 'artifacts/control/libMoltenVK.dylib'
    if (not control.is_file() or report.get('engine_id') != PINS['engine_id'] or
            report.get('control_dylib_sha256') != digest(control) or
            report.get('loaded_dylib_sha256') != digest(control) or
            report.get('story_mode_controllable') is not True or
            report.get('baseline_tree_disappearance_reproduced') is not True):
        raise ValueError('Host control evidence does not match this control binary or the required baseline')
    for key in ['baseline_capture', 'control_capture', 'loaded_library_report']:
        path = Path(report.get(key, ''))
        if not path.is_absolute() or not path.is_file() or path.stat().st_size == 0:
            raise ValueError('Missing host evidence file: ' + key)
    mapping = json.loads(Path(report['loaded_library_report']).read_text())
    if (mapping.get('loaded_dylib_sha256') != digest(control) or
            'diagnostic' in mapping.get('process_kind', '').lower()):
        raise ValueError('Loaded-library report differs or describes a diagnostic instead of RDR2')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=ROOT / 'vendor/tree-research')
    parser.add_argument('--mode', choices=['control', 'candidate', 'candidate-argument-buffer-off',
                                         'candidate-query-results', 'candidate-tree-occlusion'], default='control')
    parser.add_argument('--control-evidence', type=Path)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    if args.mode.startswith('candidate'):
        require_control(args.control_evidence, work)
    source = prepare_source(work, args.mode)
    if args.prepare_only:
        print('Verified pinned source:', source)
        return
    cmake = prepare_tools(work)
    build = work / (args.mode + '-build')
    command = [cmake, '-S', source, '-B', build, '-G', 'Unix Makefiles',
               '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_OSX_ARCHITECTURES=x86_64',
               '-DCMAKE_OSX_DEPLOYMENT_TARGET=14.0', '-DMVK_USE_METAL_PRIVATE_API=OFF',
               '-DMVK_BUILD_SHADER_CONVERTER_TOOL=OFF', '-DMVK_EXCLUDE_CEREAL=OFF',
               '-DMVK_EXCLUDE_SPIRV_TOOLS=OFF', '-DSPIRV_SKIP_TESTS=ON',
               '-DSPIRV_SKIP_EXECUTABLES=ON', '-DJUST_INSTALL_CEREAL=ON',
               '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
    if args.mode == 'candidate-argument-buffer-off':
        command.extend(['-DCMAKE_CXX_FLAGS=-DMVK_CONFIG_USE_METAL_ARGUMENT_BUFFERS=0',
                        '-DCMAKE_OBJCXX_FLAGS=-DMVK_CONFIG_USE_METAL_ARGUMENT_BUFFERS=0'])
    env = {'PATH': str(cmake.parent) + ':/usr/bin:/bin:/usr/sbin:/sbin',
           'HOME': str(Path.home()), 'TMPDIR': tempfile.gettempdir(),
           'CPM_SOURCE_CACHE': str(work / 'cpm'),
           'CLANG_MODULE_CACHE_PATH': str(work / 'clang-modules')}
    if os.environ.get('DEVELOPER_DIR'):
        env['DEVELOPER_DIR'] = os.environ['DEVELOPER_DIR']
    run(command, env=env)
    # CMake's recipes pin commits; reject local changes in reused dependency caches.
    for name in ['SPIRV-Cross', 'SPIRV-Headers', 'SPIRV-Tools', 'Vulkan-Headers', 'cereal']:
        matches = list((work / 'cpm' / name.lower()).glob('*/' + name))
        if len(matches) != 1:
            raise ValueError('Unexpected dependency cache: ' + name)
        head = subprocess.check_output(['git', '-C', str(matches[0]), 'rev-parse', 'HEAD'], text=True).strip()
        if head != PINS['dependencies'][name]:
            raise ValueError('Dependency cache revision differs: ' + name)
        run(['git', '-C', matches[0], 'diff', '--exit-code', 'HEAD', '--'], stdout=subprocess.DEVNULL)
    run([cmake, '--build', build, '--target', 'MoltenVK', '--parallel', args.jobs], env=env)
    output = work / 'artifacts' / args.mode
    output.mkdir(parents=True, exist_ok=True)
    # Preserve an earlier artifact before replacing it, including its build metadata.
    library = output / 'libMoltenVK.dylib'
    if library.exists():
        previous = output / ('previous-' + digest(library))
        previous.mkdir(exist_ok=True)
        for name in ['libMoltenVK.dylib', 'build.json']:
            if (output / name).exists() and not (previous / name).exists():
                shutil.copy2(output / name, previous / name)
    shutil.copy2(build / 'MoltenVK/libMoltenVK.1.4.2.dylib', library)
    run(['install_name_tool', '-id', '@rpath/libMoltenVK.dylib', library])
    run(['codesign', '--force', '--sign', '-', library])
    run(['codesign', '--verify', '--strict', library])
    if subprocess.check_output(['lipo', '-archs', str(library)], text=True).split() != ['x86_64']:
        raise ValueError('Built dylib is not x86_64')
    strings = subprocess.check_output(['strings', '-a', str(library)], text=True)
    for item in ['shadow-import', 'linear-fallback', 'shadow-readback']:
        if 'HIGHBALL ' + item not in strings:
            raise ValueError('Missing compiled Highball patch marker: ' + item)
    headers = list((work / 'cpm/vulkan-headers').glob('*/Vulkan-Headers/include'))
    if len(headers) != 1:
        raise ValueError('Expected exactly the pinned Vulkan-Headers cache')
    probe = work / 'probe-config'
    run(['clang', '-arch', 'x86_64', '-mmacosx-version-min=14.0',
         '-I', source / 'MoltenVK/include', '-I', source / 'MoltenVK/MoltenVK/API',
         '-I', headers[0], HERE / 'probe-config.c', '-o', probe])
    probe_env = {'PATH': '/usr/bin:/bin', 'MVK_CONFIG_USE_METAL_PRIVATE_API': '1'}
    configuration = subprocess.check_output([str(probe), str(library)], env=probe_env, text=True)
    argument_buffers = 0 if args.mode == 'candidate-argument-buffer-off' else 1
    for line in ['useMTLHeap: 1', 'useMetalArgumentBuffers: ' + str(argument_buffers), 'useMetalPrivateAPI: 0']:
        if line not in configuration.splitlines():
            raise ValueError('Control configuration differs: ' + line)
    dependencies = subprocess.check_output(['otool', '-L', str(library)], text=True)
    for line in dependencies.splitlines()[2:]:
        if not line.strip().startswith(('/System/Library/', '/usr/lib/')):
            raise ValueError('Outside dependency in control dylib: ' + line)
    metadata = {'mode': args.mode, 'engine_id': PINS['engine_id'], 'source_commit': PINS['moltenvk']['commit'],
                'highball_commit': PINS['highball_commit'], 'sha256': digest(library),
                'configure_arguments': list(map(str, command)), 'architecture': 'x86_64',
                'clang': subprocess.check_output(['clang', '--version'], text=True),
                'sdk': subprocess.check_output(['xcrun', '--show-sdk-path'], text=True).strip(),
                'configuration_probe': configuration, 'dependencies': dependencies,
                'pins': PINS, 'game_launch_verified': False, 'visual_fix_verified': False,
                'backend': 'upstream CMake; differs from Highball release Xcode packaging'}
    if args.mode.startswith('candidate'):
        metadata['control_evidence'] = json.loads(args.control_evidence.read_text())
    (output / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(configuration + 'Artifact: ' + str(library) + '\nSHA256: ' + metadata['sha256'])
    print('Build/loading only. RDR2 launch and visual acceptance require the physical host.')


if __name__ == '__main__':
    try:
        main()
    except ValueError as error:
        sys.exit(str(error))
