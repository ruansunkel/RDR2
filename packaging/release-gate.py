#!/usr/bin/env python3
"""Evidence is manually recorded observation, never synthesized from build success."""
import json
from pathlib import Path
import sys

REQUIRED = ('build_story_mode_controlled', 'clean_host_story_mode_controlled', 'finder_gatekeeper',
            'no_external_runtime', 'relocation_with_spaces', 'app_replacement_preserves_data',
            'steam_install_resume', 'licenses_and_corresponding_source_reviewed')


def validate(evidence, directory):
    for key in REQUIRED:
        record = evidence.get(key, {})
        if record.get('passed') is not True or not record.get('observed_at'):
            raise ValueError(f'Acceptance evidence incomplete: {key}')
        path = (directory / record.get('report', '')).resolve()
        if not path.is_relative_to(directory.resolve()) or not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f'Missing local observation report: {key}')


if __name__ == '__main__':
    path = Path(sys.argv[1])
    validate(json.loads(path.read_text()), path.parent)
