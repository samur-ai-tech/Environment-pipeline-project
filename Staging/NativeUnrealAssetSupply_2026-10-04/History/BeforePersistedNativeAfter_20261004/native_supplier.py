"""Designated bank writer entrypoints; importing this file does not run Unreal.

inspect(): read-only native measurements; retained receipt per job.
build_registration(): offline, held catalog transaction in supplier staging only.
apply_registration(): bank-writer-only named table save after exact manager activation.
No entrypoint cooks, changes worlds, launches an editor, or enables selection.
"""
import copy
import csv
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
from . import intake as I
from . import authority as A
from . import integrity as V
ROOT = I.ROOT
BANK = I.BANK
CATALOG = I.CATALOG
CSV = CATALOG.with_name('catalog_v4_full.csv')
TABLE = '/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4'

def bank_modules(manifest_path=None):
    m,_=A.manifest(manifest_path)
    C=A.pinned_module('bank_contracts',BANK/'bank_contracts.py',m)
    # Lexical import binding, no replacement of another chat's sys.modules entry.
    N=A.pinned_module('native_bank_ops',BANK/'native_bank_ops.py',m,imports={'bank_contracts':C})
    assert Path(C.__file__).resolve()==BANK/'bank_contracts.py'
    assert Path(N.__file__).resolve()==BANK/'native_bank_ops.py'
    assert N.C is C,'cached_native_contract_binding_mismatch'
    return C,N

def dependency_files(closure):
    import unreal
    result=[]
    for package in closure['packages']:
        if package.startswith('/Game/'):
            p=ROOT/'Content'/(package[6:]+'.uasset')
        elif package.startswith('/Engine/'):
            p=Path(unreal.Paths.engine_content_dir()).resolve()/(package[8:]+'.uasset')
        else:
            result.append({'package':package,'state':'plugin_mount_file_requires_resolved_owner_evidence'})
            continue
        files=[]
        for suffix in ['.uasset','.uexp','.ubulk','.uptnl']:
            f=p.with_suffix(suffix)
            if f.is_file(): files.append({'file':str(f),'sha256':I.sha(f),'bytes':f.stat().st_size})
        result.append({'package':package,'files':files,'state':'files_hashed' if files else 'missing_package_file'})
    return result

def inspect(job_ids,activation_path=None,queue_path=None,measurement_request_path=None):
    """Explicit bounded IDs; read-only Content, no material copying or saving."""
    import unreal
    activation=I.read(activation_path or HERE/'INSPECTION_ACTIVATION.json')
    m,mp,_=A.lease('inspect_native_supply_batch',activation)
    assert sorted(job_ids)==sorted(activation['job_ids'])
    from . import post_remap as P
    queue,qp=P.load_queue(queue_path)
    assert activation['queue_sha256']==I.sha(qp),'inspection_queue_not_activated'
    if queue_path is None and measurement_request_path is None:assert activation['batch_sha256']==I.sha(HERE/'WRITER_BATCH.json')
    if measurement_request_path:
        from . import targeted_measurement as T
        T.validate_request(measurement_request_path,job_ids,activation)
    C,N=bank_modules(mp)
    before=N.preflight()
    assert not before['dirty']['content'] and not before['dirty']['maps'],'inspection_requires_clean_native_boundary'
    selected={j['job_id']:j for j in queue['jobs']}
    assert job_ids and len(job_ids)==len(set(job_ids))
    out=[]
    for jid in job_ids:
        job=selected[jid]
        assert job['operation'] in ('reference_existing','inspect_remapped_target'),'external_source_not_loaded_or_migrated'
        assert I.sha(job['source_file'])==job['source_sha256'],'source_original_changed'
        native_sha=job.get('native_sha256',job['source_sha256'])
        path=job['native_object_path']
        assert path.startswith('/Game/')
        assert I.sha(C.package_file(path))==native_sha,'stale_native_package'
        receipt={'job_id':jid,'asset_id':job['asset_id'],'native_object_path':path,
                 'source_sha256':job['source_sha256'],'native_sha256':native_sha,'pid':os.getpid(),'world':before['world'],
                 'queue_path':str(qp),'queue_sha256':I.sha(qp),'status':'inspection_started'}
        destination='Receipts/'+jid+'.json'
        I.write(destination,receipt)
        try:
            a=unreal.load_asset(path)
            assert a is not None,'native_load_failed'
            receipt['resolved_object_path']=a.get_path_name()
            assert a.get_path_name()==path,'redirector_requires_identity_reconciliation'
            receipt['native_class']=a.get_class().get_name()
            closure=N.dependency_closure(path.split('.')[0])
            receipt['dependencies']=closure
            receipt['dependency_files']=dependency_files(closure)
            if isinstance(a,unreal.StaticMesh):
                receipt['measurement']=N.measure(a)
                receipt['instancing_material_usage']=[{'path':s.material_interface.get_path_name() if s.material_interface else None,
                    'compatible':bool(s.material_interface and unreal.MaterialEditingLibrary.has_material_usage(s.material_interface,unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES))} for s in a.static_materials]
                receipt['materials_present']=bool(a.static_materials) and all(s.material_interface for s in a.static_materials) and not closure['missing']
            elif isinstance(a,(unreal.Material,unreal.MaterialInstanceConstant)):
                receipt['used_textures']=[t.get_path_name() for t in unreal.MaterialEditingLibrary.get_used_textures(a)]
                receipt['materials_present']=not closure['missing']
            else:
                raise AssertionError('unsupported_native_class:'+receipt['native_class'])
            if measurement_request_path:
                receipt['targeted_measurement']=T.capture(a)
                receipt['measurement_request_path']=str(Path(measurement_request_path).resolve())
                receipt['measurement_request_sha256']=I.sha(measurement_request_path)
            assert I.sha(C.package_file(path))==native_sha,'native_original_changed'
            assert N.dirty()==before['dirty'],'unexpected_dirty_state_stop_for_owner'
            receipt.update(status='native_measured',dirty_unchanged=True,contact_reviewed=False,
                facing_reviewed=False,visual_reviewed=False,materials_appearance_verified=False,
                source_scale=[1,1,1],native_up_axis='Z',pivot_local_cm=[0,0,0],
                pivot_contact_offset='requires_functional_support_review_not_AABB_minimum',
                selection_eligible=False,area_generated=False,named_save_performed=False)
        except Exception as exc:
            receipt.update(status='native_inspection_blocked',error=repr(exc),dirty_after=N.dirty())
            I.write(destination,receipt)
            if N.dirty()!=before['dirty']: raise
        frozen=HERE/'MeasurementEvidence'/V.digest(receipt)/'RECEIPT.json'
        A.immutable_json(frozen,receipt)
        I.write(destination,receipt)
        I.write('ReceiptPointers/'+jid+'.json',{'path':str(frozen),'sha256':I.sha(frozen)})
        out.append({'job_id':jid,'status':receipt['status']})
    I.write('NATIVE_BATCH_RESULT.json',{'pid':os.getpid(),'results':out,'dirty_unchanged':N.dirty()==before['dirty']})
    return out

def _contracts(manifest_path=None):
    # Offline use of pure bank type/digest functions.
    m,_=A.manifest(manifest_path)
    C=A.pinned_module('bank_contracts',BANK/'bank_contracts.py',m)
    assert Path(C.__file__).resolve()==BANK/'bank_contracts.py'
    return C

def build_registration(job_ids,queue_path=None):
    """Prepare an additive held-only CAS bundle; does not write the canonical bank."""
    m,mp=A.manifest();C=_contracts(mp)
    assert job_ids and len(job_ids)==len(set(job_ids)),'duplicate_or_empty_job_ids'
    before_bytes=CATALOG.read_bytes();csv_bytes=CSV.read_bytes()
    import hashlib
    before_hash=hashlib.sha256(before_bytes).hexdigest();csv_hash=hashlib.sha256(csv_bytes).hexdigest()
    before=json.loads(before_bytes.decode('utf-8-sig'))
    V.validate_records(before['rows'])
    with CSV.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;csv_rows=list(reader)
    assert C.typed_rows(csv_rows)==C.typed_rows([r['runtime'] for r in before['rows']])
    assert len(csv_rows)==len({r['Name'].casefold() for r in csv_rows})
    assert I.sha(CATALOG)==before_hash and I.sha(CSV)==csv_hash,'baseline_changed_during_read'
    source=copy.deepcopy(before)
    from . import post_remap as P
    q,qp=P.load_queue(queue_path)
    queue={j['job_id']:j for j in q['jobs']}
    paths={r['runtime']['ObjectPath']:r for r in source['rows'] if r['runtime']['ObjectPath']}
    ids={r['asset_id'] for r in source['rows']}
    names={r['catalog_row_name'] for r in source['rows']}
    added=[];reused=[]
    for jid in job_ids:
        j=queue[jid]
        native_sha=j.get('native_sha256',j['source_sha256'])
        assert I.sha(j['source_file'])==j['source_sha256'],'source_original_changed'
        assert j['status']!='blocked_identity_ambiguity'
        path=j['native_object_path']
        assert path and path.startswith('/Game/')
        if path in paths:
            existing=paths[path]
            assert j['canonical_existing'] and j['asset_id']==existing['asset_id'] and j['catalog_row_name']==existing['catalog_row_name'],'queued_canonical_identity_changed'
            assert j['queued_canonical_record_sha256']==V.digest(existing),'queued_canonical_record_changed'
            assert native_sha.lower()==existing['runtime']['AssetRevision'].lower()==I.sha(C.package_file(path)),'reused_native_revision_changed'
            reused.append(existing['asset_id']);continue
        byte_matches=[r for r in source['rows'] if {native_sha.lower(),j['source_sha256'].lower()} & {
            str(r.get('asset_revision_sha256','')).lower(),str(r.get('source_revision','')).lower(),str(r['runtime'].get('AssetRevision','')).lower()}]
        assert not byte_matches,'fresh_catalog_byte_identity_match_requires_reconciliation'
        assert not j['canonical_existing'],'canonical_identity_exists_with_different_native_binding'
        receipt_path=HERE/'Receipts'/(jid+'.json')
        r=I.read(receipt_path)
        frozen=HERE/'MeasurementEvidence'/V.digest(r)/'RECEIPT.json'
        A.immutable_json(frozen,r);receipt_path=frozen
        assert r['status']=='native_measured' and r['resolved_object_path']==path
        assert r['source_sha256']==j['source_sha256']
        assert r.get('native_sha256',r['source_sha256'])==native_sha==I.sha(C.package_file(path))
        if queue_path is not None:assert r['queue_sha256']==I.sha(qp)
        assert not r['dependencies']['missing'] and r['materials_present']
        assert all(x['state']=='files_hashed' for x in r['dependency_files']),'unresolved_plugin_or_dependency_file'
        for dep in r['dependency_files']:
            for f in dep['files']:assert I.sha(f['file'])==f['sha256'],'stale_dependency_before_registration'
        from . import qualification_intake as Q
        Q.check_measurement(j,r)
        assert j['requested_role_candidate'] in Q.ROLES,'unsupported_role_requires_owner_contract'
        aid=j['asset_id'];name=j['catalog_row_name']
        assert aid not in ids and name not in names
        # No inherited rights, style, family budgets or placement permission.
        rt={k:'' for k in fields}
        for k in fields:
            if k in C.INTS: rt[k]='3' if k=='SchemaVersion' else 'false'
            elif k.endswith('Cm') or k in ('SelectionWeight','PreviewWeight'):rt[k]='0.0'
        rt.update(Name=name,AssetId=aid,ObjectPath=path,VariantId=path.rsplit('.',1)[-1],
            AssetRevision=native_sha,BoundsValid='true' if r['native_class']=='StaticMesh' else 'false',FamilyId='native_'+j['source_id'].lower()+'_'+j['requested_role_candidate'],
            StyleSet=j['source_style'],PlacementScope='none',ExplicitHold='true',
            HoldReasons='native_supply_qualification_pending',DecisionId='NativeUnrealAssetSupply_20261004_registration_only')
        if r['native_class']=='StaticMesh':
            bounds=r['measurement']['bounds_cm']
            for axis,lo,hi in zip('XYZ',bounds['min'],bounds['max']):
                rt['BoundsMin'+axis+'Cm']=str(lo);rt['BoundsMax'+axis+'Cm']=str(hi)
        category=Q.ROLES[j['requested_role_candidate']][0]
        record={'asset_id':aid,'catalog_row_name':name,'object_path':path,'asset_revision_sha256':native_sha,
            'source_package':path.split('/')[2],'source_revision':j['source_sha256'],'source_catalog':str(qp),
            'source_catalog_sha256':I.sha(qp),'recorded_category':category,
            'recorded_functional_role_inferred':j['requested_role_candidate'],'recorded_native_class':r['native_class'],
            'recorded_dependency_state':'native_hard_soft_closure_no_missing','recorded_material_state':'native_slots_present_appearance_unreviewed',
            'recorded_rights_state':j['rights_state'],'recorded_visual_state':'not_run','review_hold':'native_supply_qualification_pending',
            'canonical_run_eligible':False,'canonical_qualified':False,'general_generation_released':False,
            'request_role':'','placement_rule':'','technical_preview_eligible':False,'explicit_hold':True,'preview_weight':0.0,
            'min_spacing_cm':0.0,'preview_allowed_placement_ids':'','hold_reasons':['native_supply_qualification_pending'],
            'environment_style_set':j['source_style'],'style_evidence':'source_family_preserved_not_area_acceptance',
            'allowed_contexts':[],'allowed_area_policy':'none_pending_individual_review','runtime':rt,
            'native_supply':{'job_id':jid,'measurement_receipt':str(receipt_path),'receipt_sha256':I.sha(receipt_path),
                'source_original_preserved':True,'copied_native_asset':j['operation']=='inspect_remapped_target','registered_held_only':True}}
        source['rows'].append(record);paths[path]=record;ids.add(aid);names.add(name);added.append(aid)
    assert I.sha(CATALOG)==before_hash and I.sha(CSV)==csv_hash,'baseline_changed_during_build'
    new_records=source['rows'][len(before['rows']):]
    decision={'schema':'environmentpipeline.native_supply_decision.v2','authority':m['authority'],
        'command_manifest_path':str(mp),'command_manifest_sha256':I.sha(mp),'job_ids':job_ids,
        'queue_path':str(qp),'queue_sha256':I.sha(qp),'before_source_sha256':before_hash,'before_csv_sha256':csv_hash,
        'before_records_sha256':V.digest(before['rows']),'new_records':new_records,'reused_ids':reused,
        'registration_only':True,'selection_release_authorized':False}
    decision_id=V.digest(decision);folder=HERE/'Transactions'/decision_id
    folder.mkdir(parents=True,exist_ok=True)
    for filename,data in [('before_source.json',before_bytes),('before_catalog.csv',csv_bytes)]:
        p=folder/filename
        if p.exists():assert p.read_bytes()==data,'immutable_baseline_conflict'
        else:
            with p.open('xb') as f:f.write(data)
    A.immutable_json(folder/'DECISION.json',decision)
    rows=[r['runtime'] for r in source['rows']]
    digest=C.digest(rows)
    source['catalog_sha256']=source['normal_use_catalog_digest']=digest
    source['native_supply_registration_receipt']=str(folder/'TRANSACTION.json')
    V.preserved(before,source,new_records)
    A.immutable_json(folder/'catalog_v4_source.json',source)
    import io
    output=io.StringIO(newline='');w=csv.DictWriter(output,fieldnames=fields);w.writeheader();w.writerows(rows)
    p=folder/'catalog_v4_full.csv';payload=output.getvalue().encode('utf-8')
    if p.exists():assert p.read_bytes()==payload
    else:
        with p.open('xb') as f:f.write(payload)
    transaction={'schema':'environmentpipeline.native_supply_registration.v2','added_ids':added,'reused_ids':reused,
        'transaction_path':str(folder/'TRANSACTION.json'),'decision_path':str(folder/'DECISION.json'),'decision_sha256':I.sha(folder/'DECISION.json'),
        'command_manifest_path':str(mp),'command_manifest_sha256':I.sha(mp),'authority':m['authority'],
        'before_source_path':str(folder/'before_source.json'),'before_csv_path':str(folder/'before_catalog.csv'),
        'bundle_source_path':str(folder/'catalog_v4_source.json'),'bundle_csv_path':str(folder/'catalog_v4_full.csv'),
        'before_records_sha256':V.digest(before['rows']),'after_records_sha256':V.digest(rows),
        'before_rows':len(before['rows']),'after_rows':len(rows),'catalog_source_before_sha256':before_hash,
        'catalog_csv_before_sha256':csv_hash,'before_digest':C.digest(csv_rows),'after_digest':digest,
        'bundle_source_sha256':I.sha(folder/'catalog_v4_source.json'),
        'bundle_csv_sha256':I.sha(folder/'catalog_v4_full.csv'),
        'existing_rows_exactly_preserved':True,'newly_selection_eligible':[],
        'required_manager_dependency':'Bank owner reviews dynamic row-count support; root merges exact row_count and digests after native apply.',
        'native_applied':False}
    A.immutable_json(folder/'TRANSACTION.json',transaction)
    I.write('REGISTRATION_TRANSACTION.json',transaction)
    # Mutable convenience copies are never trusted by apply_registration.
    I.write('ApplyBundle/catalog_v4_source.json',source)
    (HERE/'ApplyBundle/catalog_v4_full.csv').write_bytes(payload)
    I.write('PROFILE_PATCH_REQUEST.json',{'owner':m['authority']['manager_thread_id'],
        'before_digest':transaction['before_digest'],'after_digest':digest,'expected_rows':len(rows),
        'instruction':'Root must integrate catalog digest and row count in every affected ordinary profile after native apply; this worker changes no profiles.'})
    return transaction

def validate_transaction(transaction_path):
    """Offline validation repeats preservation checks; never trust booleans in a receipt."""
    p=Path(transaction_path).resolve();assert p.is_relative_to(HERE/'Transactions')
    tx=I.read(p);assert Path(tx['transaction_path']).resolve()==p
    C=_contracts(tx['command_manifest_path'])
    assert I.sha(tx['command_manifest_path'])==tx['command_manifest_sha256']
    assert tx['authority']==A.authority()
    for pathkey,hashkey in [('before_source_path','catalog_source_before_sha256'),('before_csv_path','catalog_csv_before_sha256'),
                          ('bundle_source_path','bundle_source_sha256'),('bundle_csv_path','bundle_csv_sha256'),('decision_path','decision_sha256')]:
        path=Path(tx[pathkey]).resolve();assert path.parent==p.parent
        assert I.sha(path)==tx[hashkey],'transaction_file_changed:'+pathkey
    before=I.read(tx['before_source_path']);after=I.read(tx['bundle_source_path']);decision=I.read(tx['decision_path'])
    assert decision['authority']==tx['authority'] and decision['command_manifest_sha256']==tx['command_manifest_sha256']
    assert decision['before_source_sha256']==tx['catalog_source_before_sha256'] and decision['before_csv_sha256']==tx['catalog_csv_before_sha256']
    from . import post_remap as P
    _,qp=P.load_queue(decision.get('queue_path'))
    assert decision['queue_sha256']==I.sha(qp)
    assert decision['registration_only'] is True and decision['selection_release_authorized'] is False
    assert V.digest(before['rows'])==tx['before_records_sha256']==decision['before_records_sha256']
    V.preserved(before,after,decision['new_records'])
    assert [r['asset_id'] for r in decision['new_records']]==tx['added_ids']
    assert len(before['rows'])==tx['before_rows'] and len(after['rows'])==tx['after_rows']
    for key,document,digest_key in [('before_csv_path',before,'before_digest'),('bundle_csv_path',after,'after_digest')]:
        with Path(tx[key]).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        assert len(rows)==len({r['Name'].casefold() for r in rows})
        assert C.typed_rows(rows)==C.typed_rows([r['runtime'] for r in document['rows']])
        assert C.digest(rows)==tx[digest_key]
    assert V.digest([r['runtime'] for r in after['rows']])==tx['after_records_sha256']
    assert after['catalog_sha256']==after['normal_use_catalog_digest']==tx['after_digest']
    for row in decision['new_records']:
        receipt_path=row['native_supply']['measurement_receipt']
        assert I.sha(receipt_path)==row['native_supply']['receipt_sha256'],'measurement_receipt_changed'
        r=I.read(receipt_path)
        assert r['status']=='native_measured' and r['resolved_object_path']==row['object_path']
        assert I.sha(C.package_file(row['object_path']))==row['asset_revision_sha256']==r.get('native_sha256',r['source_sha256'])
        for dependency in r['dependency_files']:
            assert dependency['state']=='files_hashed'
            for f in dependency['files']:assert I.sha(f['file'])==f['sha256'],'dependency_changed_after_measurement'
    return tx,before,after


def apply_registration(transaction_path=None,activation_path=None):
    """Designated writer only; exact immutable decision and current successor activation."""
    import unreal
    tx_path=Path(transaction_path or I.read(HERE/'REGISTRATION_TRANSACTION.json')['transaction_path'])
    tx,before,expected=validate_transaction(tx_path)
    activation=I.read(activation_path or HERE/'REGISTRATION_ACTIVATION.json')
    _,mp,fields=A.lease('apply_held_native_supply_registration',activation,tx['command_manifest_path'])
    assert fields['OWNER']=='CODEX_BANK_INTEGRATION'
    assert activation['transaction_sha256']==I.sha(tx_path) and activation['decision_sha256']==tx['decision_sha256']
    assert activation['row_count_consumers_reviewed'] is True
    assert tx['added_ids'],'no_new_rows_to_apply'
    C,N=bank_modules(mp);state=N.preflight()
    assert not state['dirty']['content'] and not state['dirty']['maps'],'registration_requires_clean_native_boundary'
    table=unreal.load_asset(TABLE);assert table
    actual=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
    phase=V.baseline_state(I.sha(CATALOG),I.sha(CSV),C.digest(actual),tx)
    receipt_path=tx_path.parent/'APPLIED.json';started=tx_path.parent/'APPLY_STARTED.json'
    if phase=='applied':
        assert receipt_path.exists(),'applied_state_without_final_receipt_requires_reconciliation'
        result=I.read(receipt_path)
        V.applied_receipt(result,tx,I.sha(tx_path),TABLE)
        assert C.typed_rows(actual)==C.typed_rows([r['runtime'] for r in expected['rows']])
        return result
    assert C.typed_rows(actual)==C.typed_rows([r['runtime'] for r in before['rows']]),'native_baseline_rows_differ'
    assert not started.exists(),'incomplete_previous_attempt_requires_manager_reconciliation'
    # All checks above precede the first DataTable mutation.
    A.immutable_json(tx_path.parent/'NATIVE_TABLE_BEFORE.json',actual)
    A.immutable_json(started,{'pid':os.getpid(),'transaction_sha256':I.sha(tx_path),'state':state})
    assert unreal.DataTableFunctionLibrary.fill_data_table_from_csv_file(table,tx['bundle_csv_path'])
    after=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
    assert C.typed_rows(after)==C.typed_rows([r['runtime'] for r in expected['rows']])
    assert C.digest(after)==tx['after_digest']
    assert I.sha(CATALOG)==tx['catalog_source_before_sha256'] and I.sha(CSV)==tx['catalog_csv_before_sha256'],'canonical_changed_during_native_apply'
    assert unreal.EditorAssetLibrary.save_asset(TABLE,only_if_is_dirty=True)
    CATALOG.write_bytes(Path(tx['bundle_source_path']).read_bytes())
    CSV.write_bytes(Path(tx['bundle_csv_path']).read_bytes())
    assert N.dirty()==state['dirty'],'unexpected_dirty_state_after_named_save'
    assert V.baseline_state(I.sha(CATALOG),I.sha(CSV),C.digest(after),tx)=='applied'
    receipt={'pid':os.getpid(),'table':TABLE,'saved':True,'rows':len(after),'digest':C.digest(after),
        'transaction_sha256':I.sha(tx_path),'decision_sha256':tx['decision_sha256'],
        'registered_held_ids':tx['added_ids'],'newly_eligible':[],'reopened':False,'regenerated':False,
        'profile_patch_owner':tx['authority']['manager_thread_id'],'ordinary_generation_authorized':False}
    A.immutable_json(receipt_path,receipt)
    I.write('REGISTRATION_APPLIED.json',receipt)
    return receipt
