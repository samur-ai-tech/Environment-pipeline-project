"""Point the 4 km area profile at generator v002 (Aviv 2026-10-11, full generator route for road 44). Backs up the profile once
(AREA_PROFILE_before_v002.json), changes only 'hda', keeps the file's JSON layout, and records both hashes.
The run computes profile_sha256 at its start, so this must happen before the menu run, never during it."""
import datetime, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
P = ROOT / 'Staging/ModelBank/KarmeiYosef_31850349_34907601_4km/AREA_PROFILE.json'
BK = P.with_name('AREA_PROFILE_before_v002.json')
V2 = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/BankIntegration_v015/HDA/GeoCity_city_v015_CurrentBank_4km_KY_v002'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
raw = P.read_text(encoding='utf-8-sig')
p = json.loads(raw)
assert (ROOT / ('Content' + V2[5:] + '.uasset')).exists(), 'import v002 first'
if not BK.exists():
    BK.write_text(raw, encoding='utf-8')
before = sha(P)
old = p['hda']
p['hda'] = V2
indent = 2 if '\n  "' in raw[:200] else (1 if '\n "' in raw[:200] else None)
P.write_text(json.dumps(p, indent=indent), encoding='utf-8')
rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'profile': str(P), 'backup': str(BK), 'hda_before': old, 'hda_after': V2,
       'sha256_before': before, 'sha256_after': sha(P), 'other_keys_unchanged': {k: v for k, v in json.loads(BK.read_text(encoding='utf-8')).items() if k != 'hda'} == {k: v for k, v in p.items() if k != 'hda'}}
assert rec['other_keys_unchanged']
(Path(__file__).resolve().parent / 'receipts' / 'PROFILE_SWITCH_V002.json').write_text(json.dumps(rec, indent=2), encoding='utf-8')
print(json.dumps(rec, indent=1))
