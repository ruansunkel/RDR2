"""Keep capture relaunches scoped to the selected Wine prefix."""
import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / 'experiments/moltenvk-trees/switch-host-app.py'
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location('tree_session', SCRIPT)
SESSION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SESSION)


class CandidateSessionTests(unittest.TestCase):
    data = Path('/test/candidate')
    server = {42: '/test/runtime/bin/wineserver'}

    def test_closed_session_does_not_start_wine(self):
        with patch.object(SESSION, 'processes', return_value={}), patch.object(SESSION.subprocess, 'run') as run:
            self.assertFalse(SESSION.candidate_session_running(self.data))
            run.assert_not_called()

    def test_only_exact_prefix_directory_matches(self):
        for directory, expected in [('/test/candidate/prefixes/default', True),
                                    ('/test/other/prefixes/default', False),
                                    ('/test/candidate/prefixes/default-copy', False)]:
            with self.subTest(directory=directory), patch.object(SESSION, 'processes', return_value=self.server), \
                    patch.object(SESSION.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'n' + directory + '\n')):
                self.assertEqual(SESSION.candidate_session_running(self.data), expected)

    def test_uninspectable_live_server_refuses_launch(self):
        with patch.object(SESSION, 'processes', return_value=self.server), \
                patch.object(SESSION.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '')):
            with self.assertRaisesRegex(RuntimeError, 'Cannot verify'):
                SESSION.candidate_session_running(self.data)

    def test_server_exiting_during_inspection_is_handled(self):
        with patch.object(SESSION, 'processes', side_effect=[self.server, {}]), \
                patch.object(SESSION.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '')):
            self.assertFalse(SESSION.candidate_session_running(self.data))

    def test_capture_switch_environment_uses_selected_app(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ['Old.app', 'New Candidate.app']:
                app = root / name
                resources = app / 'Contents/Resources'
                resources.mkdir(parents=True)
                (resources / 'runtime-manifest.json').write_text(json.dumps({
                    'baseEnv': {'VK_ICD_FILENAMES': '${frameworks}/MoltenVK_icd.json',
                                'WINEDEBUG': '+all'}}))
            with patch.dict(SESSION.os.environ, {'MTL_CAPTURE_ENABLED': '1'}):
                env = SESSION.wine_environment(root / 'New Candidate.app', self.data,
                                               {'usePrivateHome': True})
            self.assertEqual(env['VK_ICD_FILENAMES'],
                             str(root / 'New Candidate.app/Contents/Resources/runtime/frameworks/MoltenVK_icd.json'))
            self.assertEqual(env['WINEDLLPATH_PREPEND'],
                             str(root / 'New Candidate.app/Contents/Resources/runtime/renderers/dxmt/wine'))
            self.assertEqual(env['WINEPREFIX'], '/test/candidate/prefixes/default')
            self.assertEqual(env['HOME'], '/test/candidate/build-test-home')
            self.assertEqual(env['WINEDEBUG'], '-all')
            self.assertNotIn('MTL_CAPTURE_ENABLED', env)

    def test_current_comparison_profile_requires_exact_renderer_and_data_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / 'Graphics Check.app'
            resources = app / 'Contents/Resources'
            library = resources / 'runtime/frameworks/libMoltenVK.dylib'
            library.parent.mkdir(parents=True)
            library.write_bytes(b'original comparison renderer')
            (resources / 'accepted-renderer.json').write_text(json.dumps({
                'data_directory': 'RDR2Launcher',
                'sha256': hashlib.sha256(library.read_bytes()).hexdigest(),
                'occlusion_fixes_included': False}))
            data = Path('/test/RDR2Launcher')
            self.assertTrue(SESSION.app_profile(app, data)['allocation_option_enabled'])
            for other in ['RDR2Launcher-MoltenVK-Candidate', 'Unrelated']:
                with self.assertRaises(ValueError):
                    SESSION.app_profile(app, data.with_name(other))
            library.write_bytes(b'a different renderer')
            with self.assertRaises(ValueError):
                SESSION.app_profile(app, data)


if __name__ == '__main__':
    unittest.main()
