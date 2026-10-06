"""Manager-only exact profile merge after an immutable native catalog readback."""
import argparse
import copy
import csv
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANAGER = '01a10789-2e6a-7321-ad85-0a2964f8a937'
PROFILES = {
    (ROOT/'Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json').resolve(),
    (ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json').resolve(),
}
ALLOWED = {'catalog_sha256', 'row_count', 'release.catalog_sha256',
           'release.decision_receipt', 'release.decision_sha256',
           'normal_asset_policy.bank_integration_receipt'}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def set_field(obj, key, value):
    parts = key.split('.')
    for part in parts[:-1]:
        obj = obj[part]
    obj[parts[-1]] = value

def apply(patch_path, patch_sha, native_path, native_sha):
    patch_path, native_path = Path(patch_path).resolve(), Path(native_path).resolve()
    assert sha(patch_path) == patch_sha and sha(native_path) == native_sha
    patch, native = read(patch_path), read(native_path)
    assert patch['system_owner'] == MANAGER
    assert patch['preserve_every_other_profile_field'] is True
    paths = [Path(p).resolve() for p in patch['profiles']]
    assert len(paths) == 2 and set(paths) == PROFILES
    assert set(patch['set']).issubset(ALLOWED)
    assert native['schema'] == 'environmentpipeline.actual_native_typed_table_readback.v1'
    assert native['native_source_csv_typed_equal'] and not native['native_table_dirty']
    helper = ROOT/'Staging/BankIntegration_2026-10-04/bank_contracts.py'
    ns = {'__file__': str(helper), '__name__': 'manager_read_only_catalog_contracts'}
    exec(compile(helper.read_bytes(), str(helper), 'exec'), ns)
    source = read(ns['SOURCE'])
    with Path(ns['CSV']).open(newline='', encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    source_rows = [r['runtime'] for r in source['rows']]
    assert ns['typed_rows'](rows) == ns['typed_rows'](source_rows) == native['typed_rows']
    digest = ns['digest'](source_rows)
    assert digest == native['digest'] == patch['set']['catalog_sha256']
    assert sha(ns['SOURCE']) == native['source_sha256']
    assert sha(ns['CSV']) == native['csv_sha256']
    assert sha(ns['package_file'](native['table'])) == native['native_table_package_sha256']
    assert len(source_rows) == native['row_count']
    decision = Path(patch['set']['release.decision_receipt'])
    assert sha(decision) == patch['set']['release.decision_sha256']
    receipt = ROOT/'Staging/ManagedSystemsAstra_2026-10-04'/('BANK_PROFILE_MERGE_'+digest[:16]+'.json')
    assert not receipt.exists(), 'immutable merge receipt already exists'
    backups, prepared, changes = {}, {}, []
    for path in paths:
        before_hash = patch['profile_before_sha256'][str(path)]
        assert sha(path) == before_hash
        before = read(path)
        assert before['catalog_sha256'] == patch['require_previous_catalog_digest']
        after = copy.deepcopy(before)
        for key, value in patch['set'].items():
            set_field(after, key, value)
        assert after['row_count'] == native['row_count']
        for mesh, slots in patch.get('merge_instance_materials', {}).items():
            assert mesh.startswith('/Game/') and all(s.startswith('/Game/') for s in slots)
            assert all(ns['package_file'](s).exists() for s in slots)
            after['instance_materials'][mesh] = slots
        unchanged = copy.deepcopy(after)
        for key in patch['set']:
            obj = before
            for part in key.split('.'):
                obj = obj[part]
            set_field(unchanged, key, obj)
        unchanged['instance_materials'] = before['instance_materials']
        assert unchanged == before, 'unscoped profile change'
        backup = receipt.parent/'ProfileMergeBefore'/digest[:16]/path.parent.name/'AREA_PROFILE.json'
        backup.parent.mkdir(parents=True, exist_ok=True)
        assert not backup.exists()
        backup.write_bytes(path.read_bytes())
        backups[path] = path.read_bytes()
        prepared[path] = (json.dumps(after, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()
        changes.append({'profile': str(path), 'before_sha256': before_hash, 'backup': str(backup)})
    assert sha(patch_path) == patch_sha and sha(native_path) == native_sha
    assert sha(ns['SOURCE']) == native['source_sha256'] and sha(ns['CSV']) == native['csv_sha256']
    for path in paths:
        assert path.read_bytes() == backups[path]
    try:
        for path in paths:
            temporary = path.with_name('AREA_PROFILE.manager_merge_pending')
            assert not temporary.exists()
            temporary.write_bytes(prepared[path])
            temporary.replace(path)
        for row in changes:
            row['after_sha256'] = sha(row['profile'])
        result = {'schema': 'environmentpipeline.manager_bank_profile_merge.v1',
                  'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'manager_thread_id': MANAGER, 'patch_sha256': patch_sha,
                  'native_readback': str(native_path), 'native_readback_sha256': native_sha,
                  'catalog_digest': digest, 'row_count': native['row_count'],
                  'decision_receipt': str(decision), 'decision_sha256': sha(decision),
                  'profiles': changes, 'instance_materials_merged': patch.get('merge_instance_materials', {}),
                  'other_profile_fields_preserved': True, 'ordinary_generation_authorized': False,
                  'native_content_or_map_operations': False, 'applied': True}
        receipt.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    except Exception:
        for path, original in backups.items():
            path.write_bytes(original)
        raise
    return {'receipt': str(receipt), 'receipt_sha256': sha(receipt), 'profiles': changes, 'catalog_digest': digest}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('patch'); parser.add_argument('patch_sha')
    parser.add_argument('native'); parser.add_argument('native_sha')
    args = parser.parse_args()
    print(json.dumps(apply(args.patch, args.patch_sha, args.native, args.native_sha)))
