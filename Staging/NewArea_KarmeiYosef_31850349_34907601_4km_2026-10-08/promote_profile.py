"""Register only the new area's profile (Lebanon promote_area_profile.py method). Fills the native creation receipt
hash, checks the saved native packages and bank digest, and writes Staging/ModelBank/<area>/AREA_PROFILE.json once."""
import hashlib, json
from pathlib import Path
TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
AREA = 'KarmeiYosef_31850349_34907601_4km'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
p = json.loads((TASK / 'PROFILE_CANDIDATE.json').read_text(encoding='utf-8'))
creation = json.loads((TASK / 'NATIVE_AREA_CREATION.json').read_text(encoding='utf-8'))
assert creation['status'] == 'AREA_MAP_SKY_GROUND_AND_HDA_SAVED_GENERATION_PENDING'
native = lambda pkg, ext='.uasset': ROOT / ('Content/' + pkg.split('.')[0][6:] + ext)
assert sha(native(p['map'], '.umap')) == creation['files']['map_sha256']
assert sha(native(p['hda'])) == creation['files']['hda_sha256']
assert sha(native(p['landscape_material'])) == creation['files']['ground_mi_sha256']
assert sha(TASK / 'AREA_DECISION.json') == p['release']['decision_sha256']
lebanon = json.loads((ROOT / 'Staging/ModelBank/Lebanon_33390778_35506639_4km/AREA_PROFILE.json').read_text(encoding='utf-8-sig'))
assert lebanon['catalog_sha256'] == p['catalog_sha256'] == p['release']['catalog_sha256'], 'Bank digest moved'
p['native_ground_receipt'] = str(TASK / 'NATIVE_AREA_CREATION.json')
p['native_ground_receipt_sha256'] = sha(TASK / 'NATIVE_AREA_CREATION.json')
target = ROOT / 'Staging/ModelBank' / AREA / 'AREA_PROFILE.json'
assert not target.exists()
matching = [str(f) for f in (ROOT / 'Staging/ModelBank').glob('*/AREA_PROFILE.json')
            if json.loads(f.read_text(encoding='utf-8-sig')).get('map') == p['map']]
assert not matching, matching
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(p, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
record = {'path': str(target), 'sha256': sha(target), 'existing_profiles_changed': False,
          'shared_native_hda_changed': False, 'native_bank_changed': False, 'map_sha256': creation['files']['map_sha256']}
(TASK / 'AREA_PROFILE_PROMOTION.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
