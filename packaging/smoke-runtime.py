#!/usr/bin/env python3
"""Build-only engine smoke test using the same environment as the native launcher."""
import json
import os
from pathlib import Path
import subprocess
import sys

app, prefix = map(Path, sys.argv[1:])
if prefix.exists():
    sys.exit('Refusing to reuse an existing smoke-test prefix')
subprocess.run(['/usr/bin/arch', '-x86_64', '/usr/bin/true'], check=True)
resources = app / 'Contents/Resources'
manifest = json.loads((resources / 'runtime-manifest.json').read_text())
fw = resources / 'runtime/frameworks'
env = {'HOME': os.environ['HOME'], 'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
       'TMPDIR': str(prefix.parent) + '/', 'WINEPREFIX': str(prefix), 'WINEDEBUG': '-all',
       'WINEMSYNC': '0', 'WINEESYNC': '0', 'WINEDLLOVERRIDES': 'winemenubuilder.exe=d',
       'WINEDLLPATH_PREPEND': str(resources / 'runtime/renderers/dxmt/wine')}
env.update({k: v.replace('${frameworks}', str(fw)) for k, v in manifest['baseEnv'].items() if k != 'WINEDEBUG'})
wine = str(resources / manifest['wine'])
for args in [['--version'], ['wineboot', '--init'], ['cmd', '/c', 'ver']]:
    subprocess.run([wine, *args], env=env, check=True, timeout=600)
print('Wine version, fresh wineboot and cmd passed. Gameplay remains unverified.')
