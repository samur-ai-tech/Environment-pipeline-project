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
sys.path.insert(0, str(HERE)) if str(HERE) not in sys.path else None
import intake as I
ROOT = I.ROOT
BANK = I.BANK
CATALOG = I.CATALOG
CSV = CATALOG.with_name('catalog_v4_full.csv')
TABLE = '/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4'

def bank_modules():
    # Use the installed bank contract, without executing any module's CLI main.
    if str(BANK) not in sys.path: sys.path.insert(0,str(BANK))
    prior_bytecode=sys.dont_write_bytecode
    sys.dont_write_bytecode=True
    try:
        import bank_contracts as C
        import native_bank_ops as N
    finally:
        sys.dont_write_bytecode=prior_bytecode
    assert Path(C.__file__).resolve()==BANK/'bank_contracts.py'
    assert Path(N.__file__).resolve()==BANK/'native_bank_ops.py'
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

def inspect(job_ids):
    """Explicit bounded IDs; read-only Content, no material copying or saving."""
    import unreal
    C,N=bank_modules()
    before=N.preflight()
    queue=I.read(HERE/'READY_JOBS.json')
    selected={j['job_id']:j for j in queue['jobs']}
    assert job_ids and len(job_ids)==len(set(job_ids))
    out=[]
    for jid in job_ids:
        job=selected[jid]
        assert job['operation']=='reference_existing','external_source_not_loaded_or_migrated'
        path=job['native_object_path']
        assert path.startswith('/Game/')
        assert I.sha(C.package_file(path))==job['source_sha256'],'stale_source_package'
        receipt={'job_id':jid,'asset_id':job['asset_id'],'native_object_path':path,
                 'source_sha256':job['source_sha256'],'pid':os.getpid(),'world':before['world'],
                 'queue_sha256':I.sha(HERE/'READY_JOBS.json'),'status':'inspection_started'}
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
            assert I.sha(C.package_file(path))==job['source_sha256'],'native_original_changed'
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
        I.write(destination,receipt)
        out.append({'job_id':jid,'status':receipt['status']})
    I.write('NATIVE_BATCH_RESULT.json',{'pid':os.getpid(),'results':out,'dirty_unchanged':N.dirty()==before['dirty']})
    return out

def _contracts():
    # Offline use of pure bank type/digest functions.
    if str(BANK) not in sys.path: sys.path.insert(0,str(BANK))
    prior_bytecode=sys.dont_write_bytecode
    sys.dont_write_bytecode=True
    try:
        import bank_contracts as C
    finally:
        sys.dont_write_bytecode=prior_bytecode
    assert Path(C.__file__).resolve()==BANK/'bank_contracts.py'
    return C

def build_registration(job_ids):
    """Prepare an additive held-only CAS bundle; does not write the canonical bank."""
    C=_contracts()
    before=I.read(CATALOG)
    with CSV.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;csv_rows=list(reader)
    assert C.typed_rows(csv_rows)==C.typed_rows([r['runtime'] for r in before['rows']])
    source=copy.deepcopy(before)
    queue={j['job_id']:j for j in I.read(HERE/'READY_JOBS.json')['jobs']}
    paths={r['runtime']['ObjectPath']:r for r in source['rows'] if r['runtime']['ObjectPath']}
    ids={r['asset_id'] for r in source['rows']}
    names={r['catalog_row_name'] for r in source['rows']}
    added=[];reused=[]
    for jid in job_ids:
        j=queue[jid]
        path=j['native_object_path']
        assert path and path.startswith('/Game/')
        if path in paths:
            reused.append(paths[path]['asset_id']);continue
        byte_matches=[r for r in source['rows'] if j['source_sha256'].lower() in {
            str(r.get('asset_revision_sha256','')).lower(),str(r['runtime'].get('AssetRevision','')).lower()}]
        assert not byte_matches,'fresh_catalog_byte_identity_match_requires_reconciliation'
        assert not j['canonical_existing'],'canonical_identity_exists_with_different_native_binding'
        receipt_path=HERE/'Receipts'/(jid+'.json')
        r=I.read(receipt_path)
        assert r['status']=='native_measured' and r['resolved_object_path']==path
        assert r['source_sha256']==j['source_sha256']==I.sha(C.package_file(path))
        assert not r['dependencies']['missing'] and r['materials_present']
        assert all(x['state']=='files_hashed' for x in r['dependency_files']),'unresolved_plugin_or_dependency_file'
        assert r['native_class']=='StaticMesh','surface_materials_require_existing_surface_schema_owner_review'
        aid=j['asset_id'];name=j['catalog_row_name']
        assert aid not in ids and name not in names
        # No inherited rights, style, family budgets or placement permission.
        rt={k:'' for k in fields}
        for k in fields:
            if k in C.INTS: rt[k]='3' if k=='SchemaVersion' else 'false'
            elif k.endswith('Cm') or k in ('SelectionWeight','PreviewWeight'):rt[k]='0.0'
        rt.update(Name=name,AssetId=aid,ObjectPath=path,VariantId=path.rsplit('.',1)[-1],
            AssetRevision=j['source_sha256'],BoundsValid='true',FamilyId='native_'+j['source_id'].lower()+'_'+j['requested_role_candidate'],
            StyleSet=j['source_style'],PlacementScope='none',ExplicitHold='true',
            HoldReasons='native_supply_qualification_pending',DecisionId='NativeUnrealAssetSupply_20261004_registration_only')
        bounds=r['measurement']['bounds_cm']
        for axis,lo,hi in zip('XYZ',bounds['min'],bounds['max']):
            rt['BoundsMin'+axis+'Cm']=str(lo);rt['BoundsMax'+axis+'Cm']=str(hi)
        record={'asset_id':aid,'catalog_row_name':name,'object_path':path,'asset_revision_sha256':j['source_sha256'],
            'source_package':j['source_id'],'source_revision':j['source_sha256'],'source_catalog':str(HERE/'READY_JOBS.json'),
            'source_catalog_sha256':I.sha(HERE/'READY_JOBS.json'),'recorded_category':'NativeSupply/PendingQualification',
            'recorded_functional_role_inferred':j['requested_role_candidate'],'recorded_native_class':r['native_class'],
            'recorded_dependency_state':'native_hard_soft_closure_no_missing','recorded_material_state':'native_slots_present_appearance_unreviewed',
            'recorded_rights_state':j['rights_state'],'recorded_visual_state':'not_run','review_hold':'native_supply_qualification_pending',
            'canonical_run_eligible':False,'canonical_qualified':False,'general_generation_released':False,
            'request_role':'','placement_rule':'','technical_preview_eligible':False,'explicit_hold':True,'preview_weight':0.0,
            'min_spacing_cm':0.0,'preview_allowed_placement_ids':'','hold_reasons':['native_supply_qualification_pending'],
            'environment_style_set':j['source_style'],'style_evidence':'source_family_preserved_not_area_acceptance',
            'allowed_contexts':[],'allowed_area_policy':'none_pending_individual_review','runtime':rt,
            'native_supply':{'job_id':jid,'measurement_receipt':str(receipt_path),'receipt_sha256':I.sha(receipt_path),
                'source_original_preserved':True,'copied_native_asset':False,'registered_held_only':True}}
        source['rows'].append(record);paths[path]=record;ids.add(aid);names.add(name);added.append(aid)
    assert source['rows'][:len(before['rows'])]==before['rows'],'preexisting_rows_changed'
    rows=[r['runtime'] for r in source['rows']]
    digest=C.digest(rows)
    source['catalog_sha256']=source['normal_use_catalog_digest']=digest
    source['native_supply_registration_receipt']=str(HERE/'REGISTRATION_TRANSACTION.json')
    I.write('ApplyBundle/catalog_v4_source.json',source)
    with (HERE/'ApplyBundle/catalog_v4_full.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    transaction={'schema':'environmentpipeline.native_supply_registration.v1','added_ids':added,'reused_ids':reused,
        'before_rows':len(before['rows']),'after_rows':len(rows),'catalog_source_before_sha256':I.sha(CATALOG),
        'catalog_csv_before_sha256':I.sha(CSV),'before_digest':C.digest(csv_rows),'after_digest':digest,
        'bundle_source_sha256':I.sha(HERE/'ApplyBundle/catalog_v4_source.json'),
        'bundle_csv_sha256':I.sha(HERE/'ApplyBundle/catalog_v4_full.csv'),
        'existing_rows_exactly_preserved':True,'newly_selection_eligible':[],
        'required_manager_dependency':'Existing bank apply build() fixes row count at 1223; manager must sequence/review its generalization and matching profile digest before append.',
        'native_applied':False}
    I.write('REGISTRATION_TRANSACTION.json',transaction)
    I.write('PROFILE_PATCH_REQUEST.json',{'owner':'01a106bc-2fde-7f23-9aa7-8ba413dc6245',
        'before_digest':transaction['before_digest'],'after_digest':digest,'expected_rows':len(rows),
        'instruction':'Root must integrate catalog digest and row count in every affected ordinary profile after native apply; this worker changes no profiles.'})
    return transaction

def apply_registration():
    """Only designated writer calls after root writes exact activation in this scope."""
    import unreal
    C,N=bank_modules()
    state=N.preflight()
    activation=I.read(HERE/'REGISTRATION_ACTIVATION.json')
    tx=I.read(HERE/'REGISTRATION_TRANSACTION.json')
    assert activation['manager_thread_id']=='01a106bc-2fde-7f23-9aa7-8ba413dc6245'
    assert activation['operator_thread_id']=='01a1067c-5012-7550-b449-015b53c9d726'
    assert activation['pid']==os.getpid() and activation['action']=='apply_held_native_supply_registration'
    assert activation['transaction_sha256']==I.sha(HERE/'REGISTRATION_TRANSACTION.json')
    assert activation['row_count_consumers_reviewed'] is True
    assert activation['ordinary_generation_authorized'] is False
    assert tx['added_ids'],'no_new_rows_to_apply'
    source_bundle=HERE/'ApplyBundle/catalog_v4_source.json';csv_bundle=HERE/'ApplyBundle/catalog_v4_full.csv'
    assert I.sha(source_bundle)==tx['bundle_source_sha256'] and I.sha(csv_bundle)==tx['bundle_csv_sha256']
    expected=I.read(source_bundle)
    table=unreal.load_asset(TABLE);assert table
    actual=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
    if I.sha(CATALOG)==tx['bundle_source_sha256'] and I.sha(CSV)==tx['bundle_csv_sha256'] and C.digest(actual)==tx['after_digest']:
        return {'status':'already_applied','rows':len(actual)}
    assert I.sha(CATALOG)==tx['catalog_source_before_sha256'] and I.sha(CSV)==tx['catalog_csv_before_sha256']
    assert C.digest(actual)==tx['before_digest'],'native_table_changed'
    for row in expected['rows']:
        if row['asset_id'] in tx['added_ids']:
            assert I.sha(C.package_file(row['object_path']))==row['asset_revision_sha256']
            native_receipt=I.read(row['native_supply']['measurement_receipt'])
            assert I.sha(row['native_supply']['measurement_receipt'])==row['native_supply']['receipt_sha256']
            for dependency in native_receipt['dependency_files']:
                assert dependency['state']=='files_hashed'
                for f in dependency['files']:
                    assert I.sha(f['file'])==f['sha256'],'dependency_changed_after_measurement'
    # Named backups in this scope, no overwrites of historical backups.
    backup=HERE/'Before'/tx['before_digest']
    backup.mkdir(parents=True,exist_ok=True)
    for p in [CATALOG,CSV]:
        dest=backup/p.name
        if not dest.exists():dest.write_bytes(p.read_bytes())
    I.write(str((backup/'NATIVE_TABLE.json').relative_to(HERE)),actual)
    I.write('REGISTRATION_APPLY_STARTED.json',{'pid':os.getpid(),'transaction':tx,'state':state})
    assert unreal.DataTableFunctionLibrary.fill_data_table_from_csv_file(table,str(csv_bundle))
    after=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
    assert C.typed_rows(after)==C.typed_rows([r['runtime'] for r in expected['rows']])
    assert unreal.EditorAssetLibrary.save_asset(TABLE,only_if_is_dirty=True)
    # No source/profile migration; designated catalog writer owns these two exact files.
    CATALOG.write_bytes(source_bundle.read_bytes());CSV.write_bytes(csv_bundle.read_bytes())
    assert N.dirty()==state['dirty'],'unexpected_dirty_state_after_named_table_save'
    receipt={'pid':os.getpid(),'table':TABLE,'saved':True,'rows':len(after),'digest':C.digest(after),
        'registered_held_ids':tx['added_ids'],'newly_eligible':[],'reopened':False,'regenerated':False,
        'profile_patch_owner':'root_manager','ordinary_generation_authorized':False}
    I.write('REGISTRATION_APPLIED.json',receipt)
    return receipt
