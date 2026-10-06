"""Assemble the working copy of geocity_runtime_guard.py = sealed source + imports + guard_additions.py."""
from pathlib import Path
here = Path(__file__).resolve().parent
src = here.joinpath('geocity_runtime_guard.py').read_text(encoding='utf-8')
if 'PARALLEL_EDITOR_SCHEMA' in src:
    raise SystemExit('already assembled')
assert 'import hashlib\nimport importlib\n' in src and 'import os\nimport sys\nimport types\n' in src
src = src.replace('import hashlib\nimport importlib\n', 'import datetime\nimport hashlib\nimport importlib\n', 1)
src = src.replace('import os\nimport sys\nimport types\n', 'import os\nimport re\nimport subprocess\nimport sys\nimport types\n', 1)
src = src.rstrip('\n') + '\n' + here.joinpath('guard_additions.py').read_text(encoding='utf-8')
here.joinpath('geocity_runtime_guard.py').write_text(src, encoding='utf-8', newline='\n')
print('assembled', len(src.splitlines()), 'lines')
