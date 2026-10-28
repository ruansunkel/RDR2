"""Preserve provenance when selecting a renderer built before later variants."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'packaging/build-main.py'
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location('main_build', SCRIPT)
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class RendererSelectionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.artifact = Path(self.directory.name)
        library = self.artifact / 'libMoltenVK.dylib'
        library.write_bytes(b'comparison renderer fixture')
        self.accepted = {'mode': 'candidate-query-results',
                         'sha256': hashlib.sha256(library.read_bytes()).hexdigest()}
        self.pins = {'moltenvk': {'commit': 'base'},
                     'candidate': {'sha256': 'allocation-patch', 'variants': {
                         'candidate-query-results': {'files': {'queries.mm': 'corrected-query-source'}},
                         'candidate-rock-occlusion': {'files': {'shader.mm': 'later-source'}}}}}
        self.metadata = {'mode': self.accepted['mode'], 'architecture': 'x86_64',
                         'sha256': self.accepted['sha256'], 'pins': copy.deepcopy(self.pins)}
        del self.metadata['pins']['candidate']['variants']['candidate-rock-occlusion']

    def validate(self):
        (self.artifact / 'build.json').write_text(json.dumps(self.metadata))
        return BUILD.validate_artifact(self.artifact, self.accepted, self.pins)

    def test_later_unrelated_variants_do_not_invalidate_the_comparison(self):
        self.assertEqual(self.validate()['sha256'], self.accepted['sha256'])

    def test_selected_and_common_source_changes_cannot_use_the_old_artifact(self):
        original = copy.deepcopy(self.metadata)
        for changed in ['selected-source', 'allocation-patch', 'base-commit']:
            with self.subTest(changed=changed):
                self.metadata = copy.deepcopy(original)
                recorded = self.metadata['pins']
                if changed == 'selected-source':
                    recorded['candidate']['variants']['candidate-query-results']['files']['queries.mm'] = 'different'
                elif changed == 'allocation-patch':
                    recorded['candidate']['sha256'] = 'different'
                else:
                    recorded['moltenvk']['commit'] = 'different'
                with self.assertRaises(ValueError):
                    self.validate()

    def test_accepted_rock_renderer_survives_an_unrelated_water_variant(self):
        self.accepted['mode'] = self.metadata['mode'] = 'candidate-rock-occlusion'
        self.metadata['pins'] = copy.deepcopy(self.pins)
        self.pins['candidate']['variants']['candidate-pass-safe-occlusion'] = {
            'files': {'shader.mm': 'experimental-source'}}
        self.assertEqual(self.validate()['sha256'], self.accepted['sha256'])
        self.pins['candidate']['variants']['candidate-rock-occlusion']['files']['shader.mm'] = 'changed'
        with self.assertRaises(ValueError):
            self.validate()

    def test_missing_selected_variant_is_rejected(self):
        del self.metadata['pins']['candidate']['variants']['candidate-query-results']
        del self.pins['candidate']['variants']['candidate-query-results']
        with self.assertRaises(ValueError):
            self.validate()
