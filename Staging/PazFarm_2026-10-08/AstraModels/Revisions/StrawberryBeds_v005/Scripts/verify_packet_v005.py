"""Verify packaged bytes and local gallery targets without changing delivery assets."""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


class Targets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        self.targets.extend(value for key, value in attrs if key in ('href', 'src') and value)


manifest = json.loads((ROOT / 'MANIFEST.json').read_text(encoding='utf-8'))
errors = []
for entry in manifest['files']:
    path = ROOT / entry['path']
    if not path.is_file():
        errors.append('Missing: ' + entry['path'])
    elif path.stat().st_size != entry['bytes'] or sha(path) != entry['sha256']:
        errors.append('Changed after packaging: ' + entry['path'])

links_checked = 0
for page in (ROOT / 'INDEX.html', ROOT / 'Previews/Distance/INDEX.html'):
    parser = Targets()
    parser.feed(page.read_text(encoding='utf-8'))
    for target in parser.targets:
        parts = urlsplit(target)
        if parts.scheme or parts.netloc or not parts.path:
            continue
        resolved = (page.parent / unquote(parts.path)).resolve()
        if not resolved.is_relative_to(ROOT):
            errors.append('Gallery target escapes delivery: ' + target)
        elif not resolved.is_file():
            errors.append('Missing gallery target: ' + str(resolved.relative_to(ROOT)))
        links_checked += 1

expected = {asset['fbx'] for asset in manifest['assets']}
actual = {path.relative_to(ROOT).as_posix() for path in (ROOT / 'FBX').glob('*.fbx')}
if expected != actual or len(expected) != 8:
    errors.append('Production FBX set differs from the eight manifest assets')
for base in manifest['lod_pairings']:
    if base['pivot_m'] != [0.0, 0.0, 0.0]:
        errors.append('Unexpected pivot: ' + base['base_model'])
    if not 100 <= base['lowest_triangles'] <= 300:
        errors.append('Lowest budget exceeded: ' + base['base_model'])
    if base['base_model'].endswith(('_A', '_B', '_C')) and not 15000 <= base['detailed_triangles'] <= 40000:
        errors.append('Regular detailed budget exceeded: ' + base['base_model'])
result = {'passed': not errors, 'manifest_files_checked': len(manifest['files']),
          'local_gallery_targets_checked': links_checked, 'production_fbxs': len(actual),
          'manifest_sha256': sha(ROOT / 'MANIFEST.json'), 'errors': errors}
(ROOT / 'Temp/packet_verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
if errors:
    raise SystemExit(1)
