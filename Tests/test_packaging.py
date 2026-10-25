import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'packaging'))
import runtime_tools as rt


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'packaging' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load('prepare-runtime')
gate = load('release-gate')
extractor = load('extract-verified')


class PackagingTests(unittest.TestCase):
    def test_verified_source_extractor_rejects_traversal_and_escaping_links(self):
        for name, link in [('source/../../escape', None), ('source/link', '../../../escape')]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                stage = root / 'stage'
                stage.mkdir()
                archive = self.archive(root, name, link)
                with self.assertRaises(ValueError):
                    extractor.extract(archive, stage)
                self.assertFalse((root / 'escape').exists())

    def test_verified_source_extractor_will_not_follow_existing_destination_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / 'stage'
            stage.mkdir()
            outside = root / 'outside'
            outside.mkdir()
            (stage / 'source').symlink_to(outside)
            archive = self.archive(root, 'source/file')
            with self.assertRaises(ValueError):
                extractor.extract(archive, stage)
            self.assertFalse((outside / 'file').exists())

    def test_escaping_inventory_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'runtime').mkdir()
            (root / 'runtime/leak').symlink_to('/usr/bin/true')
            with self.assertRaises(ValueError):
                rt.inventory(root)

    def test_inventory_preserves_internal_links_and_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'runtime').mkdir()
            (root / 'runtime/file').write_bytes(b'contents')
            (root / 'runtime/link').symlink_to('file')
            records = rt.inventory(root)
            self.assertEqual(records[0]['sha256'], rt.sha256(root / 'runtime/file'))
            self.assertEqual(records[1]['symlink'], 'file')

    def test_missing_dependency_and_homebrew_are_not_system(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / 'Contents/MacOS/main'
            self.assertFalse(rt.resolve_reference('/opt/homebrew/lib/libfoo.dylib', binary, binary, [], root))
            self.assertFalse(rt.resolve_reference('@rpath/missing.dylib', binary, binary, [], root))
            self.assertTrue(rt.resolve_reference('/usr/lib/libSystem.B.dylib', binary, binary, [], root))
            lib = root / 'Contents/Frameworks/libfoo.dylib'
            lib.parent.mkdir(parents=True)
            lib.touch()
            self.assertTrue(rt.resolve_reference('@rpath/libfoo.dylib', binary, binary,
                                                ['@executable_path/../Frameworks'], root))

    def archive(self, root, name, link=None):
        archive = root / 'test.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            member = tarfile.TarInfo(name)
            if link:
                member.type = tarfile.SYMTYPE
                member.linkname = link
                tar.addfile(member)
            else:
                member.size = 4
                tar.addfile(member, io.BytesIO(b'test'))
        return archive

    def test_archive_traversal_and_symlink_escape_rejected(self):
        component = {'extract': {'subpath': 'engine', 'into': 'engine'}}
        for name, link in [('engine/../../escape', None), ('engine/link', '../../../escape')]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                stage = root / 'stage'
                stage.mkdir()
                archive = self.archive(root, name, link)
                with self.assertRaises(ValueError):
                    prepare.extract_component(archive, component, stage)

    def test_d3dmetal_is_excluded_during_staging(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / 'stage'
            stage.mkdir()
            archive = root / 'test.tar'
            with tarfile.open(archive, 'w') as tar:
                for name in ['fw/renderer/d3dmetal/wine/d3d12.dll', 'fw/libsafe.dylib']:
                    member = tarfile.TarInfo(name)
                    member.size = 4
                    tar.addfile(member, io.BytesIO(b'test'))
            prepare.extract_component(archive, {'extract': {'subpath': 'fw', 'into': 'frameworks'}}, stage)
            self.assertTrue((stage / 'frameworks/libsafe.dylib').exists())
            self.assertFalse((stage / 'frameworks/renderer/d3dmetal').exists())

    def test_release_requires_actual_report_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            with self.assertRaises(ValueError):
                gate.validate({}, directory)
            fake = {key: {'passed': True, 'observed_at': '2026-10-25', 'report': 'absent.md'} for key in gate.REQUIRED}
            with self.assertRaises(ValueError):
                gate.validate(fake, directory)
            (directory / 'observed.md').write_text('Fixture observation')
            for record in fake.values():
                record['report'] = 'observed.md'
            gate.validate(fake, directory)


if __name__ == '__main__':
    unittest.main()
