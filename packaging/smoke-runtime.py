#!/usr/bin/env python3
"""Build-only engine checks; private HOME and new prefix, never existing game data."""
import argparse
import json
from pathlib import Path
import subprocess


def environment(runtime, prefix):
    home = prefix.parent / (prefix.name + '-home')
    home.mkdir(exist_ok=True)
    env = {'HOME': str(home), 'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
           'TMPDIR': str(prefix.parent) + '/', 'WINEPREFIX': str(prefix), 'WINEDEBUG': '-all',
           'WINEMSYNC': '0', 'WINEESYNC': '0', 'WINEDLLOVERRIDES': 'winemenubuilder.exe=d',
           'WINEDLLPATH_PREPEND': str(runtime / 'renderers/dxmt/wine')}
    upstream = json.loads((runtime / 'manifest.json').read_text())
    env.update({k: v.replace('${frameworks}', str(runtime / 'frameworks'))
                for k, v in upstream['baseEnv'].items() if k != 'WINEDEBUG'})
    env['GST_PLUGIN_SYSTEM_PATH_1_0'] = ''
    env['GST_PLUGIN_SCANNER'] = str(runtime / 'frameworks/GStreamer.framework/Versions/1.0/libexec/gstreamer-1.0/gst-plugin-scanner')
    env['GST_REGISTRY_1_0'] = str(home / 'gstreamer-registry.bin')
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app', type=Path, help='app bundle, or staged runtime with --staged-runtime')
    parser.add_argument('prefix', type=Path, help='new private Wine prefix')
    parser.add_argument('--staged-runtime', action='store_true')
    args = parser.parse_args()
    prefix = args.prefix.resolve()
    if prefix.exists():
        parser.error('Refusing to reuse an existing smoke-test prefix')
    prefix.parent.mkdir(parents=True, exist_ok=True)
    runtime = args.app.resolve() if args.staged_runtime else args.app.resolve() / 'Contents/Resources/runtime'
    subprocess.run(['/usr/bin/arch', '-x86_64', '/usr/bin/true'], check=True)
    env = environment(runtime, prefix)
    wine = runtime / 'engine/bin/wine'
    try:
        for command in [['--version'], ['wineboot', '--init'], ['cmd', '/c', 'ver'], ['regsvr32', '/s', 'winegstreamer.dll']]:
            print('Testing ' + ' '.join(command), flush=True)
            subprocess.run([str(wine), *command], cwd=prefix.parent, env=env, check=True, timeout=180)
        gst = runtime / 'frameworks/GStreamer.framework/Versions/1.0/bin/gst-inspect-1.0'
        for name in ['--version', 'libav']:
            subprocess.run([str(gst), name], env=env, check=True, timeout=60)
        source = Path(__file__).with_name('probe-libraries.c')
        probe = prefix.parent / (prefix.name + '-dlopen-probe')
        subprocess.run(['/usr/bin/xcrun', 'clang', '-arch', 'x86_64', '-mmacosx-version-min=14.0',
                        str(source), '-o', str(probe)], check=True)
        subprocess.run([str(probe), str(runtime / 'frameworks/ffmpeg/libavformat.63.dylib'),
                        str(runtime / 'frameworks/GStreamer.framework/Versions/1.0/lib/libgstreamer-1.0.0.dylib')],
                       env=env, check=True, timeout=30)
        print('Wine, fresh prefix, media plugins and dynamic library loading passed. Gameplay remains unverified.')
    finally:
        # This script refuses existing prefixes. Stop ONLY its own disposable services.
        subprocess.run([str(runtime / 'engine/bin/wineserver'), '-k'], env=env, check=False, timeout=30)


if __name__ == '__main__':
    main()
