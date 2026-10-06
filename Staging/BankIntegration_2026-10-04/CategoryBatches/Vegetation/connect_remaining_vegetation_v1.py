"""Retained bank-writer action: import the ready hedge and connect saved content.

No Unreal imports or shared writes occur on module import. The category worker
does not execute this. The sole activated bank writer runs execute_connection()
through the existing exact-source bank_batch_loader.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BANK = HERE.parents[1]
ASSET_ID = 'external.T1144'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def merge_list(path, incoming, key='asset_id'):
    before = read(path)
    records = {row[key]: row for row in before}
    assert len(records) == len(before), ('duplicate_input_identity', str(path))
    for row in incoming:
        existing = records.get(row[key])
        assert existing is None or existing == row, ('conflicting_existing_job', row[key], str(path))
        records[row[key]] = row
    after = list(records.values())
    return before, after


def execute_connection():
    """One content transaction, no diagnostics or city generation; holds stay exact."""
    import bank_contracts as C
    import native_bank_ops as N
    import import_prepared as I
    import apply_bank_configuration as A
    context = N.preflight()
    before_dirty = N.dirty()
    queue = [r for r in read(HERE / 'EXTERNAL_IMPORT_QUEUE.payload.json') if r['asset_id'] == ASSET_ID]
    recipes = [r for r in read(HERE / 'ADDITIONAL_MATERIAL_RECIPES.json') if r['asset_id'] == ASSET_ID]
    assert len(queue) == len(recipes) == 1
    assert queue[0]['required_consumer_context'] == 'linear_boundary_alignment'
    overrides = read(HERE / 'IMPORT_SOURCE_OVERRIDES.payload.json')
    slot_usage = read(HERE / 'ADDITIONAL_SLOT_USAGE.json')
    changes = []
    for name, rows in [('EXTERNAL_IMPORT_QUEUE.json', queue), ('EXTERNAL_MATERIAL_RECIPES.json', recipes)]:
        path = BANK / name
        before, after = merge_list(path, rows)
        if before != after:
            before_hash = sha(path)
            C.write(path, after)
            changes.append({'path': str(path), 'before_sha256': before_hash, 'after_sha256': sha(path)})
    for name, additions in [('IMPORT_SOURCE_OVERRIDES.json', overrides), ('SOURCE_IMPORT_SLOT_USAGE.json', slot_usage)]:
        path = BANK / name
        before = read(path) if path.exists() else {}
        existing = before.get(ASSET_ID)
        assert existing is None or existing == additions[ASSET_ID], ('conflicting_existing_dependency', name)
        if existing is None:
            before_hash = sha(path) if path.exists() else None
            before[ASSET_ID] = additions[ASSET_ID]
            C.write(path, before)
            changes.append({'path': str(path), 'before_sha256': before_hash, 'after_sha256': sha(path)})
    receipt = I.import_one(ASSET_ID)
    assert receipt['saved'] and receipt['asset_id'] == ASSET_ID
    assert C.sha(C.package_file(receipt['native_path'])) == receipt['native_sha256']
    records = {r['asset_id']: r for r in C.read(C.SOURCE)['rows']}
    old = records[ASSET_ID]['runtime']
    if not old['ObjectPath']:
        A.build()
        A.apply()
    else:
        assert old['ObjectPath'] == receipt['native_path'] and old['AssetRevision'] == receipt['native_sha256']
    current = {r['asset_id']: r for r in C.read(C.SOURCE)['rows']}[ASSET_ID]
    assert current['runtime']['ObjectPath'] == receipt['native_path']
    assert current['runtime']['ExplicitHold'] == old['ExplicitHold']
    assert current['runtime']['HoldReasons'] == old['HoldReasons']
    assert not C.yes(current['runtime']['RunEligible']), 'hosted_hedge_must_not_become_random_ground_scatter'
    after_dirty = N.dirty()
    assert after_dirty == before_dirty, 'connection_dirty_state_requires_bank_review'
    result = {'schema': 'environmentpipeline.vegetation_remaining_connection.v1',
              'status': 'HEDGE_IMPORTED_NAMED_SAVED_AND_NATIVE_CATALOG_CONNECTED',
              'pid': context['pid'], 'world': context['world'], 'asset_id': ASSET_ID,
              'native_path': receipt['native_path'], 'native_sha256': receipt['native_sha256'],
              'helper_input_changes': changes, 'dirty_before': before_dirty, 'dirty_after': after_dirty,
              'native_import_receipt': str(BANK / 'IMPORTED_external_T1144.json'),
              'native_table_receipt': str(BANK / 'NATIVE_TABLE_APPLIED.json'),
              'manager_profile_patch': str(BANK / 'PROFILE_BANK_FIELD_PATCH.json'),
              'consumer': 'linear_boundary_alignment', 'holds_and_rights_preserved': True,
              'ordinary_generation_performed': False, 'profile_merge_owner': 'successor_manager',
              'additional_material_diagnostics_performed': False}
    C.write(HERE / 'REMAINING_CONNECTION_EXECUTED.json', result)
    return result
