"""Bank-owned atomic prepared intake. Does not activate catalog rows or save Unreal."""
import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
import bank_contracts as C

def additive_preservation(before, after):
    old = {r['asset_id']: r for r in before['rows']}
    new = {r['asset_id']: r for r in after['rows']}
    assert len(old)==len(before['rows']) and len(new)==len(after['rows'])
    assert set(old) <= set(new)
    assert {k:v for k,v in before.items() if k!='rows'} == {k:v for k,v in after.items() if k!='rows'}
    for aid, original in old.items():
        result = new[aid]
        for key, value in original.items():
            if key=='native_supply_intakes':
                assert all(result[key].get(k)==v for k,v in value.items())
            else:
                assert result[key]==value, ('existing_prepared_field_changed',aid,key)
        assert set(result)-set(original) <= {'native_supply_intakes','native_measurement'}
    return len(old),len(new)

def configuration_evidence(prepared, canonical):
    """Expose revision-bound nested evidence without overwriting original fields."""
    source = {r['asset_id']:r for r in canonical['rows']}
    result = []
    for row in prepared['rows']:
        record = source.get(row['asset_id'])
        if not record:
            continue
        rt = record['runtime']
        evidence = dict(row.get('native_supply_intakes',{}))
        if row.get('native_supply_provenance'):
            evidence.setdefault('direct_supplier_row',row)
        for packet_id, entry in evidence.items():
            path=entry.get('object_path');revision=entry.get('current_package_sha256','').lower()
            bound=bool(path==rt['ObjectPath'] and revision and revision==rt['AssetRevision'].lower()
                       and not entry.get('canonical_revision_binding_pending')
                       and C.package_file(path).is_file() and C.sha(C.package_file(path)).lower()==revision)
            held=C.yes(rt['ExplicitHold']) or bool(rt['HoldReasons']) or bool(record.get('hold_reasons'))
            result.append({'asset_id':row['asset_id'],'packet_id':packet_id,'native_revision_bound':bound,
                           'held':held,'available_for_category_qualification':bound and not held,
                           'automatic_selection_allowed':False,
                           'native_measurement':copy.deepcopy(entry.get('native_measurement')),
                           'placement_contract_candidate':copy.deepcopy(entry.get('placement_contract_candidate')),
                           'source_prepared_fields_preserved':True})
    return result

def commit(request_path, expected_request_sha256):
    import unreal
    import native_bank_ops as N
    import bank_batch_loader as L
    request_path=Path(request_path).resolve(strict=True)
    assert C.sha(request_path)==expected_request_sha256
    request=C.read(request_path)
    for path,digest in request['file_pins'].items():assert C.sha(path)==digest,('commit_input_changed',path)
    for module in (C,N,L):
        path=str(Path(module.__file__).resolve());assert path in request['file_pins'];L.verify_module(module,path)
    activation=C.read(request['activation_path'])
    assert activation['approved'] is True and activation['scope']=='COMMIT_SUPPLIER_PREPARED_ONLY'
    assert activation['request_sha256']==expected_request_sha256 and activation['script_sha256']==C.sha(__file__)
    before_native=N.preflight()
    assert before_native['pid']==activation['pid']==os.getpid() and before_native['world']==activation['world']
    assert before_native['dirty']=={'content':[],'maps':[]},'clean_native_boundary_required'
    assert activation['manager_thread_id']==C.read(C.HERE/'ASSIGNMENT.json')['system_owner']
    assert activation['operator_thread_id']==C.read(C.HERE/'ASSIGNMENT.json')['thread']
    target=C.PREP/'PREPARED_BANK.json'
    before_bytes=target.read_bytes();before=json.loads(before_bytes)
    manifest_path=Path(request['supplier_manifest_path']);assert C.sha(manifest_path)==request['supplier_manifest_sha256']
    manifest=C.read(manifest_path)
    runner=Path(request['supplier_runner_path']).resolve(strict=True)
    assert str(runner) in manifest['files'] and C.sha(runner)==manifest['files'][str(runner)]
    name='bank_supplier_sealed_runner'
    if name in sys.modules:
        module=sys.modules[name];assert module.LOADED_SOURCE_SHA256==C.sha(runner);L.verify_module(module,runner)
    else:
        spec=importlib.util.spec_from_file_location(name,runner);module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module
        exec(compile(runner.read_bytes(),str(runner),'exec',dont_inherit=True),module.__dict__)
        L.verify_module(module,runner)
    table=unreal.load_asset('/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4')
    native_rows=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
    callback=module.run(str(manifest_path),'apply_prepared',{'transaction_path':request['transaction_path'],
                        'native_rows':native_rows,'prepared_document':before})
    assert not callback['shared_writes_performed'] and not callback['newly_enabled'] and not callback['newly_qualified']
    after=callback['prepared_document'];counts=additive_preservation(before,after)
    after_path=Path(callback['after_file_path']);assert C.sha(after_path)==callback['after_file_sha256'] and C.read(after_path)==after
    prepared_candidates=configuration_evidence(after,C.read(C.SOURCE))
    receipt_dir=C.HERE/'SupplierIntake'/callback['transaction_sha256'];receipt_dir.mkdir(parents=True,exist_ok=True)
    receipt=receipt_dir/'APPLIED.json';assert not receipt.exists(),'immutable_intake_already_applied'
    backup=receipt_dir/'PREPARED_BEFORE.json'
    if backup.exists():assert backup.read_bytes()==before_bytes
    else:backup.write_bytes(before_bytes)
    temporary=target.with_name('PREPARED_BANK.bank_intake_'+callback['transaction_sha256'][:16]+'.tmp')
    assert not temporary.exists(),'retained_pending_intake_requires_reconciliation'
    after_bytes=after_path.read_bytes()
    with temporary.open('xb') as handle:
        handle.write(after_bytes);handle.flush();os.fsync(handle.fileno())
    assert N.preflight()['dirty']==before_native['dirty']
    # Last checks before the single atomic replacement; no external calls between CAS and replace.
    assert C.sha(C.SOURCE)==callback['expected_source_sha256']
    assert C.sha(C.CSV)==callback['expected_csv_sha256']
    assert C.sha(target)==callback['expected_prepared_sha256']
    os.replace(temporary,target)
    assert C.sha(target)==callback['after_file_sha256'] and C.read(target)==after
    C.write(receipt_dir/'CONFIGURATION_EVIDENCE.json',prepared_candidates)
    result={'schema':'environmentpipeline.bank_prepared_intake_applied.v1','pid':os.getpid(),
            'request_sha256':expected_request_sha256,'transaction_sha256':callback['transaction_sha256'],
            'target':str(target),'before_sha256':callback['expected_prepared_sha256'],'after_sha256':C.sha(target),
            'before_rows':counts[0],'after_rows':counts[1],'backup':str(backup),
            'configuration_evidence':str(receipt_dir/'CONFIGURATION_EVIDENCE.json'),
            'actual_native_table_digest':C.digest(native_rows),'prior_fields_preserved':True,
            'native_content_or_maps_saved':False,'catalog_eligibility_changed':False}
    C.write(receipt,result)
    return result
