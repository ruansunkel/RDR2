"""Give Wine 11 child processes a game bundle without rebuilding the engine."""
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess

from runtime_tools import sha256

LOADER_DIR = Path('engine/lib/wine/x86_64-unix')
HELPER = Path('RDR2WineGame.app')
EXECUTABLE = HELPER / 'Contents/MacOS/wine'


def stage(runtime, icon):
    """Only call on a new app's private runtime copy, before writing its manifest."""
    loader = runtime / LOADER_DIR / 'wine'
    helper = runtime / HELPER
    if helper.exists() or loader.is_symlink():
        raise ValueError('Game Mode staging requires an unmodified runtime copy')
    if not loader.is_file() or not (loader.parent / 'ntdll.so').is_file():
        raise ValueError('Expected the pinned Wine 11 child loader and ntdll.so')
    source_hash = sha256(loader)
    executable = runtime / EXECUTABLE
    executable.parent.mkdir(parents=True)
    resources = helper / 'Contents/Resources'
    resources.mkdir()
    # A signed bundle may not link out to its dependencies. Keep the complete
    # engine inside the helper and retain the original runtime paths as aliases.
    # Its internal relative links and ntdll-derived child path still work.
    for item in list(runtime.iterdir()):
        if item == helper:
            continue
        if item.name == '.DS_Store' or item.name.startswith('._'):
            item.unlink()
            continue
        destination = resources / item.name
        item.rename(destination)
        item.symlink_to(os.path.relpath(destination, item.parent))
    loader = resources / LOADER_DIR / 'wine'
    # Retain the original loader's Wine address-space reservations and code.
    # ntdll starts children at its adjacent "wine" path. Resolve that path to
    # this real bundle executable; a shell wrapper would lose the identity.
    loader.rename(executable)
    loader.symlink_to(os.path.relpath(executable, loader.parent))
    (executable.parent / 'ntdll.so').symlink_to(os.path.relpath(loader.parent / 'ntdll.so', executable.parent))
    shutil.copy2(icon, resources / 'RDR2Launcher.icns')
    info = {
        'CFBundleExecutable': 'wine', 'CFBundleIdentifier': 'org.rdr2launcher.wine-game',
        'CFBundleName': 'Red Dead Redemption 2', 'CFBundlePackageType': 'APPL',
        'CFBundleVersion': '1', 'CFBundleShortVersionString': '0.1.0',
        'CFBundleIconFile': 'RDR2Launcher.icns', 'LSMinimumSystemVersion': '14.0',
        'LSApplicationCategoryType': 'public.app-category.games', 'LSSupportsGameMode': True,
        'NSPrincipalClass': 'WineApplication', 'NSHighResolutionCapable': True,
        'CFBundleAllowMixedLocalizations': True, 'LSUIElement': True,
    }
    (helper / 'Contents/Info.plist').write_bytes(plistlib.dumps(info))
    sign(runtime)
    (runtime / 'game-mode.json').write_text(json.dumps({
        'helper': str(HELPER), 'wine': str(EXECUTABLE),
        'original_child_loader_sha256': source_hash,
        'bundled_child_loader_sha256': sha256(executable),
        'activation_requires_focused_fullscreen_game': True,
        'game_mode_activation_verified': False,
    }, indent=2) + '\n')


def sign(runtime):
    helper = runtime / HELPER
    subprocess.run(['/usr/bin/codesign', '--force', '--sign', '-', str(helper)], check=True)
    subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(helper)], check=True)
    record = runtime / 'game-mode.json'
    if record.exists():
        metadata = json.loads(record.read_text())
        metadata['bundled_child_loader_sha256'] = sha256(runtime / EXECUTABLE)
        record.write_text(json.dumps(metadata, indent=2) + '\n')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runtime', type=Path)
    parser.add_argument('icon', type=Path)
    args = parser.parse_args()
    stage(args.runtime.resolve(strict=True), args.icon.resolve(strict=True))
