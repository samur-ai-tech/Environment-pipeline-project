"""Focused offline integrity checks; no Unreal import, fixture project or Content write."""
import ast
import copy
import itertools
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch
from . import intake as I
from . import integrity as V
from . import authority as A
from . import native_supplier as N
from . import sealed_run


def must_fail(fn,label):
    try:fn()
    except (AssertionError,KeyError):return label
    raise AssertionError('negative_check_accepted:'+label)


def verify():
    checks=[];m,mp=A.manifest();baseline=I.read(I.CATALOG)
    ids=['NU_03d5b98d84743f46a66b','NU_eb007c34606172659e7e']
    tx=N.build_registration(ids);transaction_path=Path(tx['transaction_path']);transaction_hash=I.sha(transaction_path)
    assert N.build_registration(ids)==tx and I.sha(transaction_path)==transaction_hash
    N.validate_transaction(transaction_path);checks+=['deterministic_immutable_transaction','full_before_bundle_decision_hash_validation']
    for kind in ('asset_id','row_name','casefold_path'):
        rows=copy.deepcopy(baseline['rows']);r=rows[1];a=rows[0]
        if kind=='asset_id':r['asset_id']=a['asset_id'];r['runtime']['AssetId']=a['asset_id']
        elif kind=='row_name':r['catalog_row_name']=a['catalog_row_name'].lower();r['runtime']['Name']=r['catalog_row_name']
        else:r['object_path']=a['object_path'].swapcase();r['runtime']['ObjectPath']=r['object_path']
        checks.append(must_fail(lambda:V.validate_records(rows),'duplicate_'+kind))
    real_read=I.read;q=I.read(I.HERE/'READY_JOBS.json')
    ambiguous=copy.deepcopy(q);next(j for j in ambiguous['jobs'] if j['job_id']==ids[0])['status']='blocked_identity_ambiguity'
    def ambiguous_read(path):return ambiguous if Path(path).resolve()==(I.HERE/'READY_JOBS.json').resolve() else real_read(path)
    with patch.object(I,'read',side_effect=ambiguous_read):
        checks.append(must_fail(lambda:N.build_registration(ids),'ambiguous_hash_identity_rejected'))
    reused=next(j for j in q['jobs'] if j['canonical_existing'] and j['native_object_path'])
    for field,value in [('asset_id','different_identity'),('source_sha256','0'*64),('queued_canonical_record_sha256','0'*64)]:
        changed=copy.deepcopy(q);next(j for j in changed['jobs'] if j['job_id']==reused['job_id'])[field]=value
        def fake_read(path):return changed if Path(path).resolve()==(I.HERE/'READY_JOBS.json').resolve() else real_read(path)
        with patch.object(I,'read',side_effect=fake_read):
            checks.append(must_fail(lambda:N.build_registration([reused['job_id']]),'reused_path_stale_'+field))
    actual_sha=I.sha;dep=I.read(I.HERE/'Receipts'/(ids[0]+'.json'))['dependency_files'][0]['files'][0]['file']
    def stale_dependency(path):return '0'*64 if Path(path).resolve()==Path(dep).resolve() else actual_sha(path)
    with patch.object(I,'sha',side_effect=stale_dependency):
        checks.append(must_fail(lambda:N.build_registration(ids),'stale_dependency_rejected'))
    for label,path in [('before_source',tx['before_source_path']),('bundle_source',tx['bundle_source_path']),('decision',tx['decision_path'])]:
        def stale(patharg):return '0'*64 if Path(patharg).resolve()==Path(path).resolve() else actual_sha(patharg)
        with patch.object(I,'sha',side_effect=stale):checks.append(must_fail(lambda:N.validate_transaction(transaction_path),'stale_'+label))
    for bits in itertools.product((0,1),repeat=3):
        before=(tx['catalog_source_before_sha256'],tx['catalog_csv_before_sha256'],tx['before_digest'])
        after=(tx['bundle_source_sha256'],tx['bundle_csv_sha256'],tx['after_digest'])
        state=tuple((after if bit else before)[i] for i,bit in enumerate(bits))
        if bits in ((0,0,0),(1,1,1)):assert V.baseline_state(*state,tx) in ('before','applied')
        else:must_fail(lambda:V.baseline_state(*state,tx),'partial_apply')
    checks+=['all_six_partial_apply_combinations_rejected']
    for i in range(3):
        state=[tx['catalog_source_before_sha256'],tx['catalog_csv_before_sha256'],tx['before_digest']];state[i]='stale'
        checks.append(must_fail(lambda:V.baseline_state(*state,tx),'stale_baseline_'+str(i)))
    assignment=real_read(I.HERE/'ASSIGNMENT.json');old=copy.deepcopy(assignment);old['manager_thread_id']=old['previous_manager_thread_id']
    def old_manager(path):return old if Path(path).resolve()==(I.HERE/'ASSIGNMENT.json').resolve() else real_read(path)
    with patch.object(I,'read',side_effect=old_manager):checks.append(must_fail(A.authority,'outgoing_manager_rejected'))
    C=N._contracts(mp)
    old_path=C.__file__;C.__file__='wrong.py'
    try:checks.append(must_fail(lambda:N._contracts(mp),'cached_module_path_rejected'))
    finally:C.__file__=old_path
    old_sha=C.__supplier_source_sha256__;C.__supplier_source_sha256__='stale'
    try:checks.append(must_fail(lambda:N._contracts(mp),'cached_module_hash_rejected'))
    finally:C.__supplier_source_sha256__=old_sha
    original_sha=C.sha;C.sha=lambda p:'changed'
    try:checks.append(must_fail(lambda:N._contracts(mp),'cached_bank_module_code_rejected'))
    finally:C.sha=original_sha
    call=lambda:sealed_run.run(str(mp),'validate_transaction',{'transaction_path':str(transaction_path)})
    original_module_hash=I.__supplier_source_sha256__;I.__supplier_source_sha256__='stale'
    try:checks.append(must_fail(call,'stale_loaded_supplier_hash_requires_fresh_process'))
    finally:I.__supplier_source_sha256__=original_module_hash
    original_module_sha_fn=I.sha;I.sha=lambda p:'changed'
    try:checks.append(must_fail(call,'changed_loaded_supplier_code_requires_fresh_process'))
    finally:I.sha=original_module_sha_fn
    legacy_name='legacy_native_supplier_integrity_check'
    assert legacy_name not in sys.modules
    legacy=types.ModuleType(legacy_name);legacy.__file__=I.__file__;legacy.__supplier_source_sha256__='old'
    sys.modules[legacy_name]=legacy
    try:checks.append(must_fail(call,'legacy_same_source_module_cannot_bypass_restart'))
    finally:sys.modules.pop(legacy_name)
    generic={name:sys.modules.get(name) for name in ['intake','integrity','authority','bank_contracts']}
    sentinels={name:types.ModuleType(name) for name in generic}
    try:
        sys.modules.update(sentinels);call()
        assert all(sys.modules[name] is marker for name,marker in sentinels.items())
    finally:
        for name,prior in generic.items():
            if prior is None:sys.modules.pop(name,None)
            else:sys.modules[name]=prior
    checks+=['unrelated_generic_module_names_untouched','successor_assignment_and_succession_match']
    receipt={'transaction_sha256':transaction_hash,'decision_sha256':tx['decision_sha256'],'table':N.TABLE,
        'rows':tx['after_rows'],'digest':tx['after_digest'],'registered_held_ids':tx['added_ids'],'saved':True,
        'newly_eligible':[],'ordinary_generation_authorized':False,'pid':32508}
    assert V.applied_receipt(receipt,tx,transaction_hash,N.TABLE)
    for key,bad in [('transaction_sha256','wrong'),('decision_sha256','wrong'),('table','wrong'),('rows',0),('digest','wrong'),('registered_held_ids',[]),('saved',False)]:
        changed=dict(receipt);changed[key]=bad
        checks.append(must_fail(lambda:V.applied_receipt(changed,tx,transaction_hash,N.TABLE),'invalid_APPLIED_'+key))
    before=I.read(tx['before_source_path']);after=I.read(tx['bundle_source_path']);d=I.read(tx['decision_path'])
    V.preserved(before,after,d['new_records']);tamper=copy.deepcopy(after);tamper['rows'][0]['runtime']['RunEligible']='true'
    checks.append(must_fail(lambda:V.preserved(before,tamper,d['new_records']),'existing_row_mutation_rejected'))
    for p in I.HERE.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
    assert I.sha(I.CATALOG)==tx['catalog_source_before_sha256'] and I.sha(N.CSV)==tx['catalog_csv_before_sha256']
    assert I.sha(transaction_path)==transaction_hash
    report={'status':'passed','checks':checks,'count':len(checks),'native_tests_run':False,'new_editors_launched':0,
        'canonical_source_and_csv_unchanged':True,'immutable_transaction_unchanged':True,'transaction_path':str(transaction_path),
        'transaction_sha256':transaction_hash,'queue_sha256':I.sha(I.HERE/'READY_JOBS.json'),'command_manifest_path':str(mp),'command_manifest_sha256':I.sha(mp),
        'verification_source_sha256':I.sha(Path(__file__))}
    I.write('VERIFICATION_V2.json',report);print(json.dumps(report))
    return report

if __name__=='__main__':verify()
