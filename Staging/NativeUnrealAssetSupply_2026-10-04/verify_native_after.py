"""Persisted native-table evidence tests. Unreal and every shared write are mocked."""
import copy
import hashlib
import json
import os
import sys
import types
from pathlib import Path
from unittest.mock import patch
from . import intake as I
from . import authority as A
from . import integrity as V
from . import native_supplier as N
from . import qualification_intake as Q


def rejects(fn):
    try:fn()
    except (AssertionError,KeyError):return
    raise AssertionError('expected_persisted_native_rejection')


def verify():
    protected={str(p):I.sha(p) for p in (I.CATALOG,N.CSV,I.PREP)}
    tx=I.read(I.HERE/'REGISTRATION_TRANSACTION.json');txpath=Path(tx['transaction_path'])
    t,before,expected=N.validate_transaction(txpath);C=N._contracts(t['command_manifest_path'])
    expected_rows=C.typed_rows([r['runtime'] for r in expected['rows']]);before_rows=C.typed_rows([r['runtime'] for r in before['rows']])
    checks=[];original_sha=I.sha;original_read=I.read;original_exists=Path.exists
    data={};hashes={str(I.CATALOG):t['catalog_source_before_sha256'],str(N.CSV):t['catalog_csv_before_sha256'],str(C.package_file(N.TABLE)):'d'*64}
    writes=[];calls=[];current_rows=copy.deepcopy(before_rows);corrupt_after_save=False
    fake=types.ModuleType('unreal');fake.load_asset=lambda path:object()
    def export(table):
        calls.append('export')
        rows=copy.deepcopy(current_rows)
        if corrupt_after_save and 'save' in calls:rows[0]['VariantId']='unexpected_after_save'
        return json.dumps(rows)
    def fill(table,path):
        nonlocal current_rows
        calls.append('fill');current_rows=copy.deepcopy(expected_rows);return True
    def save(path,only_if_is_dirty=True):calls.append('save');return True
    fake.DataTableFunctionLibrary=types.SimpleNamespace(export_data_table_to_json_string=export,fill_data_table_from_csv_file=fill)
    fake.EditorAssetLibrary=types.SimpleNamespace(save_asset=save)
    bank=types.SimpleNamespace(preflight=lambda:{'dirty':{'content':[],'maps':[]}},dirty=lambda:{'content':[],'maps':[]})
    activation={'transaction_sha256':I.sha(txpath),'decision_sha256':t['decision_sha256'],'row_count_consumers_reviewed':True}
    activationpath=I.HERE/'offline_native_after_fixture_activation.json'
    def read(path):
        key=str(Path(path).resolve())
        if key==str(activationpath):return activation
        return copy.deepcopy(data[key]) if key in data else original_read(path)
    def sha(path):
        key=str(Path(path).resolve())
        if key in hashes:return hashes[key]
        if key in data:return hashlib.sha256(json.dumps(data[key],sort_keys=True).encode()).hexdigest()
        return original_sha(path)
    def immutable(path,document):
        key=str(Path(path).resolve())
        assert key not in data or data[key]==document
        data[key]=copy.deepcopy(document)
    def write_bytes(path,payload):
        key=str(path.resolve());assert key in (str(I.CATALOG),str(N.CSV)),'unapproved_mock_write'
        writes.append(key);hashes[key]=hashlib.sha256(payload).hexdigest();return len(payload)
    def exists(path):return str(path.resolve()) in data or original_exists(path)
    with patch.dict(sys.modules,{'unreal':fake}),patch.object(N,'validate_transaction',return_value=(t,before,expected)),patch.object(N,'bank_modules',return_value=(C,bank)),patch.object(N,'_contracts',return_value=C),patch.object(A,'lease',return_value=({},t['command_manifest_path'],{'OWNER':'CODEX_BANK_INTEGRATION'})),patch.object(A,'immutable_json',side_effect=immutable),patch.object(I,'read',side_effect=read),patch.object(I,'sha',side_effect=sha),patch.object(I,'write',side_effect=lambda name,d:immutable(I.HERE/name,d)),patch.object(Path,'write_bytes',write_bytes),patch.object(Path,'exists',exists):
        result=N.apply_registration(txpath,activationpath)
        savedpath=txpath.parent/'NATIVE_TABLE_AFTER.json';saved=read(savedpath)
        assert calls==['export','fill','export','save','export']
        assert writes==[str(I.CATALOG),str(N.CSV)] and saved['typed_rows']==expected_rows
        assert result['native_table_after_sha256']==sha(savedpath)
        checks.append('first_apply_reexports_all_rows_after_named_save_and_hash_binds_full_receipt')
        originalwrites=list(writes);calls.clear()
        assert N.apply_registration(txpath,activationpath)==result and writes==originalwrites and calls==['export']
        checks.append('idempotent_apply_verifies_persisted_snapshot_without_save_or_shared_write')
        baseline_saved=copy.deepcopy(data[str(savedpath)]);baseline_applied=copy.deepcopy(data[str(txpath.parent/'APPLIED.json')])
        for field,value in [('transaction_sha256','bad'),('decision_sha256','bad'),('pid',0),('table','wrong'),('saved',False),('readback_after_named_save',False),('rows',0),('digest','bad'),('source_sha256','bad'),('csv_sha256','bad'),('native_table_package_sha256','bad')]:
            changed=copy.deepcopy(baseline_saved);changed[field]=value;data[str(savedpath)]=changed
            # Even an attacker updating the APPLIED hash cannot hide bad contents.
            data[str(txpath.parent/'APPLIED.json')]['native_table_after_sha256']=sha(savedpath)
            rejects(lambda:N.validate_applied_native(txpath,expected_rows));checks.append('reject_native_after_'+field)
            data[str(savedpath)]=copy.deepcopy(baseline_saved);data[str(txpath.parent/'APPLIED.json')]=copy.deepcopy(baseline_applied)
        changed=copy.deepcopy(baseline_saved);changed['typed_rows'][0]['VariantId']='changed'
        data[str(savedpath)]=changed;data[str(txpath.parent/'APPLIED.json')]['native_table_after_sha256']=sha(savedpath)
        rejects(lambda:N.validate_applied_native(txpath,expected_rows));checks.append('reject_full_row_change_even_with_rebound_receipt_hash')
        data[str(savedpath)]=copy.deepcopy(baseline_saved);data[str(txpath.parent/'APPLIED.json')]=copy.deepcopy(baseline_applied)
        for key in (str(I.CATALOG),str(N.CSV),str(C.package_file(N.TABLE))):
            oldhash=hashes[key];hashes[key]='x'*64
            rejects(lambda:N.validate_applied_native(txpath,expected_rows));checks.append('reject_current_binary_change_'+Path(key).name)
            hashes[key]=oldhash
        wrong_rows=copy.deepcopy(expected_rows);wrong_rows[-1]['VariantId']='changed'
        rejects(lambda:N.validate_applied_native(txpath,wrong_rows));checks.append('reject_current_native_export_row_change')
        data[str(txpath.parent/'APPLIED.json')]['native_table_after_sha256']='0'*64
        rejects(lambda:N.apply_registration(txpath,activationpath));checks.append('idempotent_retry_rejects_stale_receipt_hash')
        data[str(txpath.parent/'APPLIED.json')]=copy.deepcopy(baseline_applied)
        legacy=copy.deepcopy(baseline_applied)
        for key in ('native_table_after_path','native_table_after_sha256','native_table_package_sha256'):legacy.pop(key)
        data[str(txpath.parent/'APPLIED.json')]=legacy
        rejects(lambda:N.validate_applied_native(txpath,expected_rows));checks.append('reject_legacy_metadata_only_APPLIED')
        data[str(txpath.parent/'APPLIED.json')]=copy.deepcopy(baseline_applied)
        # Real prepared callback invokes the persisted after-table validator.
        pointer=original_read(I.HERE/'QUALIFICATION_INTAKE.json');qt,packet,prepared_after=Q.validate(pointer['path'])
        hashes[str(I.PREP)]=packet['prepared_before_sha256']
        data[str(I.CATALOG)]=expected
        with patch.object(Q,'validate',return_value=(qt,packet,prepared_after)),patch.object(Q,'project',side_effect=lambda *a:next(r for r in packet['rows'] if r['asset_id']==a[0]['asset_id'])):
            # Native validation succeeds before projection; no shared writes.
            prepared=Q.apply_prepared(pointer['path'],expected_rows,original_read(I.PREP))
            assert prepared['shared_writes_performed'] is False and writes==originalwrites
            assert prepared['expected_native_table_package_sha256']=='d'*64
            assert prepared['verified_saved_native_after']=={'path':str(savedpath),'sha256':sha(savedpath)}
            checks.append('prepared_callback_consumes_verified_saved_native_snapshot')
            hashes[str(C.package_file(N.TABLE))]='x'*64
            rejects(lambda:Q.apply_prepared(pointer['path'],expected_rows,original_read(I.PREP)))
            checks.append('prepared_callback_rejects_changed_DT_binary')
            hashes[str(C.package_file(N.TABLE))]='d'*64
        # Fresh synthetic attempt: mismatch after save must stop before source/CSV writes.
        data.clear();hashes[str(I.CATALOG)]=t['catalog_source_before_sha256'];hashes[str(N.CSV)]=t['catalog_csv_before_sha256']
        writes.clear();calls.clear();current_rows=copy.deepcopy(before_rows);corrupt_after_save=True
        rejects(lambda:N.apply_registration(txpath,activationpath))
        assert writes==[] and str(txpath.parent/'APPLIED.json') not in data and str(savedpath) not in data
        checks.append('post_save_row_mismatch_stops_before_source_csv_commit_and_APPLIED')
    assert protected=={str(p):I.sha(p) for p in (I.CATALOG,N.CSV,I.PREP)}
    report={'status':'passed','checks':checks,'count':len(checks),'native_execution_performed':False,'shared_writes_performed':False,
        'native_apply_and_prepared_callback_exercised_with_mocks_only':True,'protected_files_unchanged':protected,
        'command_manifest_sha256':I.sha(A.manifest()[1]),'verification_source_sha256':I.sha(__file__)}
    I.write('NATIVE_AFTER_VERIFICATION.json',report);print(json.dumps(report));return report
