"""Reject false control acceptance while allowing explicitly labelled user observations."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('tree_build', ROOT / 'experiments/moltenvk-trees/build.py')
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class ControlEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.app = self.root / 'Control.app'
        self.resources = self.app / 'Contents/Resources'
        library = self.resources / 'runtime/frameworks/libMoltenVK.dylib'
        library.parent.mkdir(parents=True)
        library.write_bytes(b'fixture-control-library')
        self.sha = hashlib.sha256(library.read_bytes()).hexdigest()
        self.metadata = {'mode': 'control', 'pins': copy.deepcopy(BUILD.PINS), 'sha256': self.sha}
        (self.resources / 'moltenvk-control-build.json').write_text(json.dumps(self.metadata))
        (self.resources / 'tree-control.json').write_text(json.dumps({'candidate_patch_included': False}))
        observation = self.root / 'observation.md'
        observation.write_text('User reported the baseline tree issue in the control app. No video was captured.')
        self.report = {'evidence_basis': 'user-reported-signed-control-app', 'control_app': str(self.app),
                       'engine_id': BUILD.PINS['engine_id'], 'control_dylib_sha256': self.sha,
                       'story_mode_controllable': True, 'baseline_tree_disappearance_reproduced': True,
                       'user_observation': str(observation)}
        self.evidence = self.root / 'control-evidence.json'

    def tearDown(self):
        self.temporary.cleanup()

    def check(self):
        self.evidence.write_text(json.dumps(self.report))
        with patch.object(BUILD, 'run') as signature:
            BUILD.require_control(self.evidence, self.root)
            signature.assert_called_once_with(['codesign', '--verify', '--deep', '--strict', self.app])

    def test_reported_control_does_not_claim_video_or_a_loaded_mapping(self):
        self.check()
        self.assertNotIn('loaded_dylib_sha256', self.report)
        self.assertNotIn('control_capture', self.report)

    def test_candidate_cannot_be_accepted_as_the_baseline(self):
        self.metadata['mode'] = 'candidate'
        (self.resources / 'moltenvk-control-build.json').write_text(json.dumps(self.metadata))
        with self.assertRaises(ValueError): self.check()

    def test_a_changed_driver_cannot_use_an_older_user_report(self):
        (self.resources / 'runtime/frameworks/libMoltenVK.dylib').write_bytes(b'changed-driver')
        with self.assertRaises(ValueError): self.check()

    def test_changed_control_sources_are_rejected(self):
        self.metadata['pins']['moltenvk']['commit'] = 'another-commit'
        (self.resources / 'moltenvk-control-build.json').write_text(json.dumps(self.metadata))
        with self.assertRaises(ValueError): self.check()

    def test_missing_human_observation_is_not_control_acceptance(self):
        self.report['story_mode_controllable'] = False
        with self.assertRaises(ValueError): self.check()


if __name__ == '__main__':
    unittest.main()
