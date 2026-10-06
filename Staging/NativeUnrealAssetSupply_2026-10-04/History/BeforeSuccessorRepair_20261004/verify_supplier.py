"""Offline regression checks on real prepared transactions; never loads Unreal."""
import ast
import copy
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import intake as I
import native_supplier as N

def verify():
    queue_path=I.HERE/'READY_JOBS.json'
    original_queue=I.sha(queue_path)
    q=I.build()
    assert I.sha(queue_path)==original_queue,'non_idempotent_queue'
    assert all(j['native_object_path'].startswith('/Game/') for j in q['jobs'] if j['native_object_path'])
    assert all('/Prepared/NativeUnreal/' in j['target_object_path'] for j in q['jobs'] if j['operation'].startswith('native_migrate'))
    assert all(not j['states']['native_imported_by_supplier'] for j in q['jobs'])
    assert len({j['job_id'] for j in q['jobs']})==len(q['jobs'])
    ids=['NU_03d5b98d84743f46a66b','NU_eb007c34606172659e7e']
    tx=N.build_registration(ids)
    bundle_hash=I.sha(I.HERE/'ApplyBundle/catalog_v4_source.json')
    second=N.build_registration(ids)
    assert tx==second and I.sha(I.HERE/'ApplyBundle/catalog_v4_source.json')==bundle_hash
    before=I.read(I.CATALOG);after=I.read(I.HERE/'ApplyBundle/catalog_v4_source.json')
    assert after['rows'][:len(before['rows'])]==before['rows']
    assert len(after['rows'])==len(before['rows'])+2
    for r in after['rows'][len(before['rows']):]:
        assert r['runtime']['RunEligible']=='false' and r['runtime']['ExplicitHold']=='true'
        assert r['runtime']['PlacementScope']=='none' and r['runtime']['AllowedAreas']==''
        assert not r['canonical_qualified'] and not r['general_generation_released']
    real_sha=I.sha
    stale_path=next(j['source_file'] for j in q['jobs'] if j['job_id']==ids[0])
    def stale(p):
        return 'stale_source' if Path(p).resolve()==Path(stale_path).resolve() else real_sha(p)
    with patch.object(I,'sha',side_effect=stale):
        try:N.build_registration(ids)
        except AssertionError:pass
        else:raise AssertionError('stale_source_accepted')
    assert I.sha(I.HERE/'ApplyBundle/catalog_v4_source.json')==bundle_hash
    assert I.sha(I.CATALOG)==tx['catalog_source_before_sha256'],'canonical_source_changed_during_checks'
    for name in ['intake.py','native_supplier.py','source_migration.py','adopt_measured.py','verify_supplier.py']:
        ast.parse((I.HERE/name).read_text(encoding='utf-8'),filename=name)
    report={'status':'passed','checks':['deterministic_queue_rebuild','unique_job_ids','native_Game_contract','prepared_external_namespace',
        'deterministic_additive_registration','all_preexisting_rows_exactly_preserved','new_rows_held_and_unselected',
        'stale_mesh_rejected_before_bundle_write','canonical_source_unchanged','python_syntax'],
        'native_tests_run':False,'new_editors_launched':0,'queue_sha256':I.sha(queue_path),'transaction_sha256':I.sha(I.HERE/'REGISTRATION_TRANSACTION.json')}
    I.write('VERIFICATION.json',report)
    print(json.dumps(report))

if __name__=='__main__':verify()
