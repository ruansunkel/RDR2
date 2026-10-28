"""Wine child launches and integrity must retain the game bundle after relocation."""
import json
from pathlib import Path
import plistlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'packaging'))
import game_mode
import runtime_tools


class GameModePackagingTests(unittest.TestCase):
    def fixture(self, root):
        resources = root.resolve() / 'Launcher.app/Contents/Resources'
        runtime = resources / 'runtime'
        for name in ['engine/bin/wine', str(game_mode.LOADER_DIR / 'wine'),
                     str(game_mode.LOADER_DIR / 'ntdll.so'), 'frameworks/libMoltenVK.dylib',
                     'renderers/dxmt/wine/x86_64-windows/d3d11.dll']:
            path = runtime / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(name.encode())
        (resources / 'engine-upstream.json').write_text(json.dumps({'id': 'fixture', 'baseEnv': {}}))
        icon = root / 'icon.icns'
        icon.write_bytes(b'icon fixture')
        return resources, runtime, icon

    @patch('game_mode.subprocess.run')
    def test_child_loader_identity_and_manifest_survive_app_relocation(self, signing):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            resources, runtime, icon = self.fixture(root)
            old = (runtime / game_mode.LOADER_DIR / 'wine').read_bytes()
            game_mode.stage(runtime, icon)
            # The engine's ntdll-derived child path resolves to the actual bundle
            # executable, which in turn still finds the original ntdll beside it.
            self.assertEqual((runtime / game_mode.LOADER_DIR / 'wine').resolve(), runtime / game_mode.EXECUTABLE)
            self.assertEqual((runtime / game_mode.EXECUTABLE).read_bytes(), old)
            self.assertEqual((runtime / game_mode.EXECUTABLE).with_name('ntdll.so').resolve(),
                             (runtime / game_mode.LOADER_DIR / 'ntdll.so').resolve())
            info = plistlib.loads((runtime / game_mode.HELPER / 'Contents/Info.plist').read_bytes())
            self.assertTrue(info['LSSupportsGameMode'])
            self.assertEqual(info['LSApplicationCategoryType'], 'public.app-category.games')
            runtime_tools.write_manifest(resources)
            manifest = json.loads((resources / 'runtime-manifest.json').read_text())
            self.assertEqual(manifest['wine'], 'runtime/' + str(game_mode.EXECUTABLE))
            self.assertTrue(any(r['path'].endswith('RDR2WineGame.app/Contents/Info.plist') for r in manifest['files']))
            moved = root / 'Relocated app.app'
            resources.parents[1].rename(moved)
            resources = moved / 'Contents/Resources'
            self.assertEqual(runtime_tools.inventory(resources), manifest['files'])
            self.assertTrue((resources / manifest['wine']).is_file())
            with self.assertRaises(ValueError):
                game_mode.stage(resources / 'runtime', icon)

    def test_manifest_rejects_a_game_loader_outside_the_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            resources, runtime, icon = self.fixture(Path(temporary))
            (runtime / 'game-mode.json').write_text(json.dumps({'wine': '../engine-upstream.json'}))
            with self.assertRaises(ValueError):
                runtime_tools.write_manifest(resources)
