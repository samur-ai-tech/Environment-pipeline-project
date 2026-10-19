"""Offline, plain Python. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the El Wahat switch_profile_v002.py
(itself a fork of the Karmei Yosef one). Points this area's profile at the new generator revision hda_edits.UNREAL_HDA
(area_constants.py HDA_VERSION) from the one it names now (UNREAL_HDA_PREVIOUS, HDA_PREVIOUS_VERSION). Changes only 'hda'
by replacing that one value in the file bytes, so every other byte, the key order and the CRLF layout stay as they are (a
json.dumps rewrite would reformat the file). Backs up the original once (AREA_PROFILE_before_<version>.json, exact bytes),
asserts every other key unchanged and that exactly one Staging/ModelBank/*/AREA_PROFILE.json names this map, and records
both hashes in ../receipts/PROFILE_SWITCH_<VERSION>.json.
No route_surface_materials key: the module default decides the track material (sealed workflow passes '{}').
The run computes profile_sha256 at its start, so this must happen before the menu run (after hda_revision_prepare.py
import, remove_actor and clear_for_instantiate), never during it. It writes AREA_PROFILE.json, so only an agent Aviv assigns
to this task may run it (GOVERNANCE_RECORD.md RC-12). The operator id is ASSIGNMENT.json operator_session_id.
    python -B Tools/switch_profile_hda.py --authority "<Aviv's words>"
"""
import argparse, datetime, hashlib, importlib.util, json, sys
from pathlib import Path
TOOLS = Path(__file__).resolve().parent
TASK = TOOLS.parent
ROOT = TASK.parents[1]
_spec = importlib.util.spec_from_file_location('hda_edits', TASK / 'hda_edits.py')
E = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(E)  # generator constants (loads area_constants.py)
ap = argparse.ArgumentParser(); ap.add_argument('--authority', required=True); AUTHORITY = ap.parse_args().authority
assert AUTHORITY.strip(), '--authority (Aviv\'s words) is required'
OPERATOR = json.loads((TASK / 'ASSIGNMENT.json').read_text(encoding='utf-8-sig')).get('operator_session_id')
assert OPERATOR, 'ASSIGNMENT.json operator_session_id is required'
assert E.UNREAL_HDA_PREVIOUS, 'area_constants.py HDA_PREVIOUS_VERSION is None: nothing to switch from'
VERSION = E.VERSION
P = ROOT / 'Staging/ModelBank' / E.AREA / 'AREA_PROFILE.json'
BK = P.with_name('AREA_PROFILE_before_%s.json' % VERSION)
MAP = E.A.MAIN_MAP
V1, V2 = E.UNREAL_HDA_PREVIOUS, E.UNREAL_HDA
OUT = TASK / 'receipts' / ('PROFILE_SWITCH_%s.json' % VERSION.upper())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert TASK.name == E.A.TASK_FOLDER and (ROOT / 'Staging/ModelBank').is_dir(), (TASK, ROOT)
V2_FILE = ROOT / ('Content' + V2[5:] + '.uasset')
assert V2_FILE.exists(), 'import the new revision first (hda_revision_prepare.py step import): ' + str(V2_FILE)
MAPFILE = ROOT / ('Content' + MAP[5:] + '.umap')                         # run order: switch only after remove_actor + clear (review fix)
CLR = TASK / 'receipts' / ('CLEAR_BEFORE_%s.json' % VERSION.upper())
clr = json.loads(CLR.read_text(encoding='utf-8')) if CLR.is_file() else {}
assert clr.get('status') == 'CLEARED_SAVED' and clr.get('map_sha256_after') == sha(MAPFILE) and clr.get('dirty_after') == [[], []], \
    ('switch only after hda_revision_prepare remove_actor + clear_for_instantiate on the current map', clr.get('status'))
lease = [l for l in (ROOT / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig', errors='replace').splitlines() if l.strip()][-1]
assert 'OWNER=NONE' in lease or MAP not in lease, ('a menu run holds this map; never switch the profile during a run', lease)
same = [f for f in sorted((ROOT / 'Staging/ModelBank').glob('*/AREA_PROFILE.json'))
        if json.loads(f.read_text(encoding='utf-8-sig')).get('map') == MAP]
assert [f.resolve() for f in same] == [P.resolve()], ('exactly one area profile must name this map', [str(f) for f in same])
raw = P.read_bytes()
p = json.loads(raw.decode('utf-8-sig'))
assert p['map'] == MAP, p['map']
assert p['hda'] == V1, ('profile hda is not the previous revision (already switched?)', p['hda'])
assert 'route_surface_materials' not in p, 'route_surface_materials must stay absent (module default decides)'
assert raw.count(b'"hda"') == 1, raw.count(b'"hda"')
old_item, new_item = ('"hda": ' + json.dumps(V1)).encode(), ('"hda": ' + json.dumps(V2)).encode()
assert raw.count(old_item) == 1, ('hda item not found exactly once', raw.count(old_item))
new = raw.replace(old_item, new_item)
q = json.loads(new.decode('utf-8-sig'))
others_same = {k: v for k, v in p.items() if k != 'hda'} == {k: v for k, v in q.items() if k != 'hda'}
assert q['hda'] == V2 and others_same and list(q) == list(p), 'other keys or key order changed'
assert new.count(b'\n') == new.count(b'\r\n') == raw.count(b'\r\n') and b'\r\r\n' not in new, 'CRLF layout changed'
assert len(new) - len(raw) == len(new_item) - len(old_item), 'byte change is not limited to the hda value'
before = sha(P)
if BK.exists():
    assert BK.read_bytes() == raw, BK.name + ' exists and differs from the current profile'
else:
    with open(BK, 'xb') as stream:
        stream.write(raw)
P.write_bytes(new)
assert P.read_bytes() == new
bk = json.loads(BK.read_bytes().decode('utf-8-sig'))
rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'operator': OPERATOR,
       'authority': AUTHORITY, 'profile': str(P), 'backup': str(BK),
       'backup_sha256': sha(BK), 'hda_before': V1, 'hda_after': V2, 'new_uasset': str(V2_FILE), 'new_uasset_sha256': sha(V2_FILE),
       'sha256_before': before, 'sha256_after': sha(P), 'prepared_map_sha256': clr['map_sha256_after'],
       'other_keys_unchanged': {k: v for k, v in bk.items() if k != 'hda'} == {k: v for k, v in q.items() if k != 'hda'},
       'key_order_unchanged': list(bk) == list(q), 'only_hda_value_bytes_changed': True, 'crlf_kept': True,
       'route_surface_materials_key_present': False, 'profiles_naming_this_map': [str(f) for f in same], 'lease_tail': lease}
assert rec['other_keys_unchanged'] and rec['key_order_unchanged']
OUT.write_text(json.dumps(rec, indent=2), encoding='utf-8')
print(json.dumps(rec, indent=1))
