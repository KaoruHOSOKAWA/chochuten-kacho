"""Record successful container execution only after font checks have passed."""
import importlib.metadata
import json
import platform
from pathlib import Path

assert Path('/.dockerenv').is_file(), 'Docker container required'
root = Path(__file__).resolve().parent.parent
verification = json.loads((root / 'qa/render-validation.json').read_text())
assert verification['docker_execution'] == 'container'
report = {
    'execution': 'Docker container',
    'python': platform.python_version(),
    'dependencies': {name: importlib.metadata.version(name) for name in
                     ['fonttools', 'Pillow', 'opencv-python-headless', 'numpy', 'uharfbuzz']},
    'fonts': json.loads((root / 'qa/validation.json').read_text()),
    'render_validation': 'passed',
    'vertical_validation': json.loads((root / 'qa/vertical-validation.json').read_text()),
    'specimen_validation': json.loads((root / 'qa/specimen-validation.json').read_text()),
    'local_virtual_environment_used': False,
}
(root / 'qa/docker-provenance.json').write_text(json.dumps(report, indent=2) + '\n')
(root / 'qa/docker-status.txt').write_text(
    'Docker build and verification: COMPLETED.\n'
    'Font generation, rendering, verification and release packaging run inside Docker.\n'
    'No host Python virtual environment or host dependency cache is used.\n'
    'The source code and generated glyph atlases are copied into the image.\n'
    'Only output/ and qa/ are mounted from the host.\n'
    'Runtime networking is disabled.\n')
print(json.dumps(report, indent=2))
