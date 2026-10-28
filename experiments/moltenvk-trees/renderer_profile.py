"""Validate the renderer and data-folder identity of research and current apps."""
import hashlib
import json
from pathlib import Path


def app_profile(app, data):
    if data.name not in {'RDR2Launcher', 'RDR2Launcher-MoltenVK-Candidate'}:
        raise ValueError('Choose the explicit permanent or isolated RDR2 data folder')
    resources = app / 'Contents/Resources'
    current = resources / 'accepted-renderer.json'
    if current.exists():
        recorded = json.loads(current.read_text())
        profile = {'default_data_directory': recorded['data_directory'],
                   'candidate_dylib_sha256': recorded['sha256'],
                   'allocation_option_enabled': True}
    else:
        profile = json.loads((resources / 'tree-candidate.json').read_text())
        if profile.get('candidate_patch_included') is not True:
            raise ValueError('Legacy app is not the recorded candidate')
    library = (resources / 'runtime/frameworks/libMoltenVK.dylib').resolve()
    if (profile.get('default_data_directory') != data.name or
            not library.is_relative_to(app.resolve()) or
            hashlib.sha256(library.read_bytes()).hexdigest() != profile.get('candidate_dylib_sha256')):
        raise ValueError('App renderer bytes or data-folder profile differ')
    return profile
