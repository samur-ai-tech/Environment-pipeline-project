"""Retained complete whole-building batch; offline preparation is the default.

Only the bank integrator may call execute_native, inside its current sole editor
lease. This adapter never edits the catalog, profiles, system sources or maps.
Run offline: python category_batch.py --build
Run after new native receipts: python category_batch.py --build --verify
"""
import argparse
import collections
import copy
import csv
import importlib.util
import hashlib
import inspect
import json
import math
import os
import re
import shutil
import sys
import types
from pathlib import Path

SOURCE_IDENTITY_ATTRIBUTE = '_whole_buildings_loaded_source_identity'
CONTRACTS_MODULE_NAME = 'environmentpipeline_whole_buildings_category_contracts'
IMPORTER_MODULE_NAME = 'environmentpipeline_whole_buildings_retained_import_adapter'

def _code_signature(code):
    return (code.co_code,tuple(_code_signature(v) if isinstance(v,types.CodeType) else v for v in code.co_consts),
        code.co_names,code.co_varnames,code.co_freevars,code.co_cellvars,code.co_argcount,
        code.co_posonlyargcount,code.co_kwonlyargcount,code.co_flags,getattr(code,'co_exceptiontable',b''))

def _code_fingerprint(code):
    return hashlib.sha256(repr(_code_signature(code)).encode('utf-8')).hexdigest()

def _verify_registered_source(module,path,expected_sha256):
    """Check registry object, captured source identity and actual live function code."""
    path=Path(path).resolve(strict=True)
    assert sys.modules.get(module.__name__) is module,('module_not_registered_exact_object',module.__name__)
    assert Path(module.__file__).resolve(strict=True)==path,('loaded_module_path_differs',module.__name__)
    source=path.read_bytes();actual_sha=hashlib.sha256(source).hexdigest()
    assert actual_sha==expected_sha256,('reviewed_module_source_changed',module.__name__)
    compiled=compile(source,str(path),'exec',dont_inherit=True)
    expected={}
    def walk(code):
        expected[getattr(code,'co_qualname',code.co_name)]=code
        for item in code.co_consts:
            if isinstance(item,types.CodeType):walk(item)
    walk(compiled)
    binding=getattr(module,SOURCE_IDENTITY_ATTRIBUTE,None)
    assert binding and binding['module_name']==module.__name__ and binding['path']==str(path),('unattested_cached_module_restart_required',module.__name__)
    assert binding['source_sha256']==expected_sha256 and binding['code_fingerprint']==_code_fingerprint(compiled),('stale_cached_module_restart_required',module.__name__)
    if path.name=='category_contracts.py':
        expected_here=path.parent
        assert module.HERE.resolve()==expected_here and module.ROOT.resolve()==expected_here.parents[3],('category_contract_paths_changed',module.__name__)
        assert module.PREP.resolve()==(expected_here.parents[3]/'Staging/BankPreparation_2026-10-04').resolve(),('category_preparation_path_changed',module.__name__)
    # Every direct source def must remain present; replacing it with an imported
    # function must not evade the same-module function scan.
    direct=[v for v in compiled.co_consts if isinstance(v,types.CodeType) and not v.co_name.startswith('<')]
    for wanted in direct:
        fn=vars(module).get(wanted.co_name)
        assert inspect.isfunction(fn) and fn.__module__==module.__name__,('source_function_replaced',module.__name__,wanted.co_name)
    functions=[v for v in vars(module).values() if inspect.isfunction(v) and v.__module__==module.__name__]
    for fn in functions:
        assert fn.__globals__ is module.__dict__,('foreign_function_globals',module.__name__,fn.__qualname__)
        assert Path(fn.__code__.co_filename).resolve(strict=True)==path,('live_function_path_changed',module.__name__,fn.__qualname__)
        wanted=expected.get(fn.__qualname__) or expected.get(fn.__name__)
        assert wanted is not None and _code_signature(fn.__code__)==_code_signature(wanted),('stale_live_function_restart_required',module.__name__,fn.__qualname__)
    return {**binding,'module_identity':id(module),'verified_functions':len(functions)}

def _load_registered_source(name,path,expected_sha256=None):
    """Execute exactly the reviewed bytes once; stale cached modules are rejected."""
    path=Path(path).resolve(strict=True)
    source=path.read_bytes();source_sha=hashlib.sha256(source).hexdigest()
    expected_sha256=expected_sha256 or source_sha
    assert source_sha==expected_sha256,('unreviewed_module_source',str(path))
    if name in sys.modules:
        module=sys.modules[name]
        _verify_registered_source(module,path,expected_sha256)
        return module
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    compiled=compile(source,str(path),'exec',dont_inherit=True)
    sys.modules[name]=module
    try:
        exec(compiled,module.__dict__)
        setattr(module,SOURCE_IDENTITY_ATTRIBUTE,{'module_name':name,'path':str(path),
            'source_sha256':source_sha,'code_fingerprint':_code_fingerprint(compiled)})
        _verify_registered_source(module,path,expected_sha256)
    except Exception:
        if sys.modules.get(name) is module:del sys.modules[name]
        raise
    return module

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
INTEGRATION = HERE.parents[1]
PREPARATION = ROOT / 'Staging/BankPreparation_2026-10-04'
CATALOG = ROOT / 'Staging/ModelBank/PermanentIntegration_2026-10-02/catalog_v4_source.json'
CATALOG_CSV = CATALOG.with_name('catalog_v4_full.csv')
CATEGORY_ASSIGNMENT = HERE.parent/'ASSIGNMENT.json'
TRANSFER_STATE = ROOT/'Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/STATE.json'
BANK_ACTIVATION = ROOT/'Staging/ManagedSystemsAstra_2026-10-04/BANK_ACTIVATION.json'
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
C = _load_registered_source(CONTRACTS_MODULE_NAME,HERE/'category_contracts.py')

AREAS = ['GazaRimal', 'GazaShujaiya']
ZONES = 'building_yes|building_residential|building_house|building_apartments|building_commercial'
COHERENT_SOURCE_GROUPS = {'external.H0017', 'external.H0018', 'external.H0019', 'external.H0020', 'external.H0021'}
NAMED_HOLDS = ['H0013', 'H0907', 'H0051', 'H0958', 'H0094']
SOURCE_MODULE = Path('C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank/geocity_city_module.py')
OPERATIVE_CONFIGURATION_FIELDS = (
    'asset_id','row_name','object_path','package_sha256','role','placement_rule',
    'contact_kind','anchor_z_cm','bounds_cm','forward_axis','native_scale',
    'allowed_areas','allowed_zones','style_context','source_style_preserved',
    'family_id','min_spacing_cm','material_slots','rights_state_preserved')
PRESERVED_CONFIGURATION_EVIDENCE = ('anchor_basis','review_note','style_policy')

def verify_configuration_merge(configs,shared,material_state,material_file_pins):
    """Check operative values and saved slot bindings without rewriting evidence."""
    assert len({j['asset_id'] for j in configs})==len(configs),'duplicate_category_configuration_identity'
    verified=[]
    for job in configs:
        aid=job['asset_id'];existing=shared.get(aid)
        assert existing is not None,('missing_shared_configuration',aid)
        mismatch={key:{'shared':existing.get(key),'category':job.get(key)}
                  for key in OPERATIVE_CONFIGURATION_FIELDS
                  if key not in existing or key not in job or existing[key]!=job[key]}
        assert not mismatch,('operative_configuration_differs',aid,mismatch)
        assert existing.get('automatic_ground_activation_allowed',True)==job.get('automatic_ground_activation_allowed',True),('activation_consumer_constraint_differs',aid)
        # Extra policy explanation remains bank-owned; its actual style decisions
        # must still match the reviewed category values.
        for key in ['source_style_preserved','configured_runtime_style','gaza_profile_style','matches_current_gaza_style']:
            if key in job.get('style_policy',{}):
                assert existing.get('style_policy',{}).get(key)==job['style_policy'][key],('operative_style_policy_differs',aid,key)
        slots=material_state.get('mesh_slots',{}).get(job['object_path'])
        assert slots and len(slots)==len(job['material_slots']),('verified_material_slot_count_differs',aid)
        assert slots==job['existing_instance_materials'],('category_material_bindings_not_verified',aid)
        assert existing.get('existing_instance_materials')==slots,('integrator_material_binding_merge_required',aid)
        identities={}
        for slot in slots:
            path=C.package_file(slot).resolve();key=str(path)
            assert path.is_file() and key in material_file_pins,('material_package_not_hash_bound',aid,slot)
            assert C.sha(path)==material_file_pins[key],('verified_material_package_changed',aid,slot)
            identities[key]=material_file_pins[key]
        verified.append({'asset_id':aid,'operative_fields_equal':True,'verified_instance_material_slots':slots,
            'material_file_identities':identities,'preserved_evidence_fields':list(PRESERVED_CONFIGURATION_EVIDENCE),
            'normal_correction_required_or_called':False})
    return verified

def read(path, fallback=None):
    return C.read(path) if Path(path).is_file() else copy.deepcopy(fallback)

def evidence(path, key=None):
    p = Path(path)
    return {'path': str(p.resolve()), 'sha256': C.sha(p), 'record_key': key} if p.is_file() else None

def write(name, value):
    C.write(HERE / name, value)

def current_ownership():
    assignment=read(CATEGORY_ASSIGNMENT)
    bank_assignment=read(INTEGRATION/'ASSIGNMENT.json')
    assert assignment['bank_integrator_thread']==bank_assignment['thread'],'bank_operator_assignments_differ'
    assert assignment['system_manager_thread']==bank_assignment['system_owner'],'manager_assignments_differ'
    own=(ROOT/assignment['categories']['WholeBuildings']['owned_directory']).resolve()
    assert own==HERE,'wrong_category_owned_directory'
    transfer=read(TRANSFER_STATE,{})
    if transfer.get('status')=='TRANSFERRED_TO_SUCCESSOR':
        assert assignment['system_manager_thread']==transfer['successor_manager_thread_id'],'stale_manager_assignment'
    return {'bank_integrator_thread':assignment['bank_integrator_thread'],
        'system_manager_thread':assignment['system_manager_thread'],
        'category_thread':assignment['categories']['WholeBuildings'].get('thread_id'),
        'assignment':evidence(CATEGORY_ASSIGNMENT),'management_transfer':evidence(TRANSFER_STATE)}

def validate_canonical_rows(catalog,csv_rows,fields):
    """Pure integrity gate, including every current field and hold value."""
    rows=catalog['rows']
    assert rows and csv_rows and 'AssetId' in fields and 'Name' in fields,'missing_canonical_schema'
    assert len(rows)==len(csv_rows),'canonical_source_csv_count_mismatch'
    identities={r['asset_id']:r for r in rows};names={r['catalog_row_name']:r for r in rows}
    assert len(identities)==len(names)==len(rows),'duplicate_canonical_identity_or_row_name'
    csv_by_name={r['Name']:r for r in csv_rows}
    assert len(csv_by_name)==len(csv_rows) and set(csv_by_name)==set(names),'csv_row_identity_mismatch'
    for record in rows:
        rt=record['runtime'];aid=record['asset_id'];name=record['catalog_row_name']
        assert aid==rt['AssetId'] and name==rt['Name'],('canonical_runtime_identity_mismatch',aid)
        assert set(rt)==set(fields),('canonical_csv_schema_mismatch',aid)
        assert rt==csv_by_name[name],('canonical_source_csv_exact_row_mismatch',aid)
    return identities

def canonical_catalog(source_path=CATALOG,csv_path=CATALOG_CSV,preserve_baseline=True):
    """Exact full current rows, identities and holds; additive identities allowed."""
    start={str(Path(p).resolve()):C.sha(p) for p in [source_path,csv_path]}
    catalog=read(source_path)
    with Path(csv_path).open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream);fields=list(reader.fieldnames or []);csv_rows=list(reader)
    rows=catalog['rows']
    identities=validate_canonical_rows(catalog,csv_rows,fields)
    baseline_path=HERE/'CANONICAL_IDENTITY_BASELINE.json'
    if preserve_baseline:
        baseline=read(baseline_path)
        identity_names={r['asset_id']:r['catalog_row_name'] for r in rows}
        if baseline is None:
            write(baseline_path.name,{'schema':'environmentpipeline.canonical_identity_guard.v1',
                'first_observed_count':len(rows),'source_sha256':start[str(Path(source_path).resolve())],
                'identities':identity_names,'policy':'Preserve every original canonical ID and row name; permit additions without changing the baseline.'})
        else:
            assert set(baseline['identities'])<=set(identity_names),'existing_canonical_identity_removed'
            assert all(identity_names[a]==n for a,n in baseline['identities'].items()),'existing_canonical_row_name_changed'
    assert all(C.sha(p)==expected for p,expected in start.items()),'catalog_changed_during_read_retry_from_fresh_snapshot'
    guard={'source_sha256':start[str(Path(source_path).resolve())], 'csv_sha256':start[str(Path(csv_path).resolve())],
        'source_count':len(rows),'csv_count':len(csv_rows),'source_csv_exact_rows_equal':True,
        'identity_keyset_sha256':hashlib.sha256(json.dumps(sorted((a,r['catalog_row_name']) for a,r in identities.items()),separators=(',',':')).encode()).hexdigest(),
        'holds_rights_style_sha256':hashlib.sha256(json.dumps(sorted((r['asset_id'],r['runtime']['ExplicitHold'],r['runtime']['HoldReasons'],r['recorded_rights_state'],r['canonical_qualified'],r['environment_style_set'],r['runtime']['StyleSet']) for r in rows),separators=(',',':')).encode()).hexdigest(),
        'additive_identities_allowed':True,'current_canonical_rows_written':False}
    return catalog,guard

def native_activation_guard():
    """File-only guard before importing any Unreal helper; inspection is insufficient."""
    ownership=current_ownership();activation=read(BANK_ACTIVATION)
    lines=(ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()
    lease=next(line for line in reversed(lines) if line.strip())
    fields=dict(re.findall(r'(\w+)=([^\s]+)',lease))
    assert activation.get('native_authorized_now') is True,'native_authoring_paused_by_manager'
    assert str(activation['assigned_editor_PID'])==str(os.getpid())==fields.get('assigned_editor_PID'),'wrong_actual_native_pid'
    assert activation['manager_thread_id']==ownership['system_manager_thread']==fields.get('manager_thread_id'),'native_activation_manager_mismatch'
    assert activation['bank_thread_id']==ownership['bank_integrator_thread']==fields.get('operator_thread_id'),'native_activation_operator_mismatch'
    assert fields.get('OWNER')=='CODEX_BANK_INTEGRATION' and fields.get('activation')=='MANAGER_ACTIVATED','native_lease_is_not_authoring_activation'
    assert fields.get('native_authorized_now','true').lower()!='false','native_lease_explicitly_paused'
    return ownership

def held(record, prepared):
    return (str(record['runtime']['ExplicitHold']).lower() in ('true','1')
            or bool(record['hold_reasons']) or bool(prepared['named_holds_preserved'])
            or bool(prepared['palm_hold_not_released']))

def material_bindings(record, measurement, shared_materials, catalog):
    path = record['runtime']['ObjectPath']
    return copy.deepcopy(shared_materials.get('mesh_slots', {}).get(path)
                         or catalog.get('instance_materials', {}).get(path)
                         or [s['path'] for s in measurement.get('material_slots', [])])

def native_file_identities(paths):
    return {str(C.package_file(path).resolve()):C.sha(C.package_file(path))
            for path in paths if path and path.startswith('/Game/') and C.package_file(path).is_file()}

def import_material_contract(payload, recipe):
    result=[]
    for material in recipe['materials']:
        refs={r['channel']:r for r in payload['textures'] if r['material']==material['source_material']}
        config={'recipe':material,'textures':refs,'native_normal_green_flipped':True,'native_mask_clip':0.333}
        digest=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
        path='/Game/Project/Shared/ModelBank/Prepared/Dependencies/Materials/M_'+digest[:16]
        result.append({'recipe_slot':material['slot'],'source_material':material['source_material'],
            'native_material_path_proposed':path+'.'+path.rsplit('/',1)[1],
            'recipe_sha256':digest,'source_channels':refs})
    return result

def consumer_contract():
    return {
        'route': 'Existing shared catalog -> geographic whole_building requests -> retained Houdini selector -> official Houdini Engine unreal_instance -> native Unreal',
        'request_role': 'whole_building', 'placement_rule': 'building_footprint',
        'source': evidence(SOURCE_MODULE),
        'functions': ['cook_nonbuilding_requests', '_permanent_rectangle', '_permanent_candidate_rejection', '_permanent_building_height_preference', '_terrain_r015_support_samples'],
        'native_scale': [1,1,1], 'native_units': 'centimetres, Z up',
        'houdini_units': 'metres, Y up; official Engine performs native coordinate conversion',
        'anchor': 'Retained selector compensates the native horizontal AABB centre and AnchorZCm through its yaw quaternion; full authored envelope remains authoritative.',
        'facing': 'ForwardAxis corrects the geographic longest footprint edge yaw. This is geometric alignment, not a facade/entrance survey.',
        'height_provenance': {'accepted': ['osm_height_m','osm_levels_x_3.2m','seeded_rule_not_measured'],
            'source_height_fit': '0.5 * source height <= native envelope height <= 1.5 * source height',
            'seeded_height': 'Preference max(0.05, (min(desired,native)/max(desired,native))**2); never fabricates measured height or floors'},
        'footprint': 'Complete rotated rectangle must fit the source polygon and its area must cover at least 0.45 of source-pad area.',
        'terrain': 'All retained whole-footprint/intersected-grid-cell support samples must be within 0.03 m of the final support datum.',
        'style': 'Both bank_style_set and environment_style_set gates require exact existing StyleSet. No source style conversion.',
        'spacing': 'Retain configured native spacing and full geometry; existing rectangle overlap checks remain in force.',
        'replacement': 'Existing official lifecycle and owned generation ledgers; original maps, scoped Replace Previous Bake and named saves only.',
        'unsupported': ['Blueprint/family rows are not a single StaticMesh', 'module showrooms are not whole buildings', 'no guessed floor counts or surveyed facade/entrance directions'],
        'ordinary_output_state': 'Not established for new additions by category preparation.'}

def classification_exception(aid, p, imported):
    if p['native_class_recorded']=='ObjectRedirector':
        return {'code':'native_redirector_not_selectable','missing':'Recorded ObjectRedirector is an alias, not another whole-building mesh. Preserve its canonical ID and hold; resolve its target in integrator native readback and select the existing measured SM_Warehouse_Building identity only once.'}
    if p['record_kind'] == 'family_candidate':
        return {'code': 'family_record_not_single_asset', 'missing': 'Existing canonical family has no individual measured native StaticMesh path; supplier/integrator must resolve exact existing member IDs and supported representation, preserving the family ID.'}
    s = p.get('prepared_source')
    if s and s['primary_render_object_count'] > 1 and aid not in COHERENT_SOURCE_GROUPS:
        if aid in {'external.H0693','external.H0694','external.H0695'}:
            return {'code': 'modular_showroom_excluded', 'missing': 'Prepared receipt lists separate hangar walls/roof/corners/support pieces with showroom transforms. Assembly authoring is explicitly outside WholeBuildings scope; never combine the full showroom into one whole building.'}
        if aid == 'external.H0896':
            return {'code': 'multi_building_scene_requires_existing_member_groups', 'missing': '109 render objects span a 137.23 x 111.09 m source scene, containing several building groups and hosted tanks/dishes. Exact group membership, original canonical child identity and support envelopes are absent; no scene-wide combined mesh.'}
        return {'code': 'source_composition_requires_correction', 'missing': 'Existing H0022 geometry preview visibly has open/back surfaces and irregular duplicated massing; no intact complete-building grouping is established. Preserve all seven source objects; do not combine or invent closure.'}
    return None

def proposed_configuration(aid, record, p, measurements, configured, materials, catalog):
    rt = record['runtime']
    m = measurements
    if aid in configured:
        job = copy.deepcopy(configured[aid])
    else:
        bounds = copy.deepcopy(m.get('vertex_bounds_cm', m.get('bounds_cm', p.get('bounds_native_cm_recorded'))))
        if not bounds:
            return None
        active = str(rt['RunEligible']).lower() in ('true','1')
        forward = rt['ForwardAxis'] if rt['ForwardAxis'] in ['+X','-X','+Y','-Y'] else '+X'
        spacing = float(rt['MinSpacingCm']) if active else math.ceil(math.hypot(bounds['max'][0]-bounds['min'][0], bounds['max'][1]-bounds['min'][1]) + 100)
        job = {'asset_id': aid, 'row_name': record['catalog_row_name'], 'object_path': rt['ObjectPath'],
            'package_sha256': C.sha(C.package_file(rt['ObjectPath'])), 'role':'whole_building','placement_rule':'building_footprint',
            'contact_kind':'authored_complete_building_support', 'anchor_z_cm':float(rt['AnchorZCm']) if active else bounds['min'][2],
            'anchor_basis':'Existing enabled row retained' if active else 'Measured native minimum is a candidate; support plane review remains required.',
            'bounds_cm':bounds,'forward_axis':forward,'forward_basis':'Existing retained alignment' if active else 'Geographic envelope alignment proposal, facade direction unverified',
            'native_scale':[1,1,1],'allowed_areas':AREAS,'allowed_zones':ZONES,'style_context':rt['StyleSet'],
            'source_style_preserved':record['environment_style_set'],'family_id':rt['FamilyId'],'min_spacing_cm':spacing,
            'material_slots':copy.deepcopy(m.get('material_slots',[])),'historical_native_images':p['native_preview_sources'],
            'rights_state_preserved':record['recorded_rights_state'],'state':'retain_existing_enabled_contract' if active else 'measured_configuration_review_pending',
            'automatic_ground_activation_allowed':not held(record,p)}
    job['existing_instance_materials'] = material_bindings(record,m,materials,catalog)
    job['style_context'] = rt['StyleSet']
    job['style_policy'] = {'source_style_preserved':record['environment_style_set'],
        'configured_runtime_style':rt['StyleSet'],'gaza_profile_style':'mediterranean_urban',
        'matches_current_gaza_style':rt['StyleSet']=='mediterranean_urban'}
    if 'SM_H0902_' in aid:
        job.update(anchor_z_cm=0.0, anchor_basis='SOURCE_CONTACT_READBACK: ten authored building-base vertices at Z=0. Ladder minimum -2.2491 cm is not the building support plane.',
                   review_note='Latest delegated native graph readback: neutral Constant3Vector normal already present. Preserve native graph; do not call apply_building_normal_corrections.')
    if 'SM_H0016_' in aid:
        job.update(anchor_z_cm=0.0, anchor_basis='SOURCE_CONTACT_READBACK: authored support Z=0. Keep full 18.4218 x 52.6892 x 21.7008 m envelope; decorative minimum -0.2597 cm is not a platform.',
                   review_note='Latest delegated native graph readback: current native materials have correct building normals. Preserve native graphs; do not call apply_building_normal_corrections.')
    return job

def build():
    ownership=current_ownership()
    catalog,canonical_guard = canonical_catalog()
    records = {r['asset_id']:r for r in catalog['rows']}
    prepared = {r['asset_id']:r for r in read(PREPARATION/'PREPARED_BANK.json')['rows']}
    configured = {r['asset_id']:r for r in read(INTEGRATION/'NATIVE_CONFIGURATIONS.json')['rows']}
    validation = read(INTEGRATION/'NATIVE_VALIDATION.json',{})
    contact = read(INTEGRATION/'NATIVE_CONTACT_READBACK.json',{})
    materials = read(INTEGRATION/'NATIVE_INSTANCE_MATERIALS.json',{})
    manifest = {r['asset_id']:r for r in read(PREPARATION/'EXTERNAL_IMPORT_MANIFEST.json')}
    shared_queue = {r['asset_id']:r for r in read(INTEGRATION/'EXTERNAL_IMPORT_QUEUE.json')}
    local_recipes={r['asset_id']:r for r in read(HERE/'EXTERNAL_MATERIAL_RECIPES.json',[])}
    ids = sorted(a for a,p in prepared.items() if p['category']=='Buildings/Whole' or p['request_role']=='whole_building')
    canonical_ids = {r['asset_id'] for r in records.values() if r['recorded_category']=='Buildings/Whole' or r['runtime']['RequestRole']=='whole_building'}
    assert canonical_ids <= set(ids), ('uncovered_canonical_whole_assets', sorted(canonical_ids-set(ids)))
    assert len(set(records)) == len(catalog['rows']) == canonical_guard['csv_count']
    jobs=[];native_payload=[];new_imports=[];row_patches=[];validation_preserved={};bind={};family_members=collections.defaultdict(list)
    for aid in ids:
        p=prepared[aid];record=records[aid];rt=record['runtime'];isheld=held(record,p)
        enabled=str(rt['RunEligible']).lower() in ('true','1')
        source=p.get('prepared_source')
        shared_receipt=INTEGRATION/('IMPORTED_'+aid.replace('.','_')+'.json')
        local_receipt=HERE/('IMPORTED_'+aid.replace('.','_')+'.json')
        imp=read(local_receipt) or read(shared_receipt)
        m=contact.get(aid) or (imp or {}).get('measurement') or p.get('native_measurement') or {}
        path=rt['ObjectPath'] or (imp or {}).get('native_path','')
        native_sha=C.sha(C.package_file(path)) if path and C.package_file(path).is_file() else None
        if imp and imp.get('saved'):
            assert native_sha==imp['native_sha256'], ('saved_import_changed',aid)
        elif native_sha:
            expected_measurement_sha=(m.get('source_sha256') or m.get('package_sha256_at_queue')
                                      or p.get('current_package_sha256') or rt['AssetRevision'])
            assert expected_measurement_sha==native_sha,('native_measurements_no_longer_match_package',aid)
        if validation.get(aid,{}).get('ready'):
            assert validation[aid]['source_sha256']==native_sha,('stale_ready_validation',aid)
        exceptional=classification_exception(aid,p,imp)
        job={'asset_id':aid,'row_name':record['catalog_row_name'],'category':'WholeBuildings','object_path':path,
            'native_sha256':native_sha,'canonical_object_path_at_build':rt['ObjectPath'],
            'source_fbx':source.get('source_fbx') if source else p['source_path'],
            'source_sha256':source.get('source_fbx_sha256') if source else native_sha,
            'prepared_blend':source.get('blend') if source else None,
            'prepared_blend_sha256':C.sha(source['blend']) if source else None,
            'role':'whole_building','placement_rule':'building_footprint','native_scale':[1,1,1],
            'family_id':rt['FamilyId'],'style_context_preserved':rt['StyleSet'],
            'source_style_preserved':record['environment_style_set'],
            'gaza_style_matches':rt['StyleSet']=='mediterranean_urban',
            'holds':{'ExplicitHold':rt['ExplicitHold'],'HoldReasons':rt['HoldReasons'],'canonical_reasons':record['hold_reasons'],
                     'named_holds':p['named_holds_preserved'],'palm_hold_preserved':p['palm_hold_not_released']},
            'rights_state_preserved':record['recorded_rights_state'],'canonical_qualification_preserved':record['canonical_qualified'],
            'bounds_native_cm':copy.deepcopy(m.get('vertex_bounds_cm',m.get('bounds_cm'))),
            'bounds_source_m':source.get('bounds_m') if source else None,
            'native_dependency_evidence':copy.deepcopy(m.get('dependencies')),
            'native_material_slots':copy.deepcopy(m.get('material_slots',[])),
            'instance_material_slots':material_bindings({**record,'runtime':{**rt,'ObjectPath':path}},m,materials,catalog),
            'existing_readiness':copy.deepcopy(validation.get(aid)),
            'source_object_count':source.get('primary_render_object_count') if source else None,
            'composition_exception':exceptional,
            'evidence':[e for e in [evidence(CATALOG,aid),evidence(PREPARATION/'PREPARED_BANK.json',aid),
                evidence(INTEGRATION/'NATIVE_CONTACT_READBACK.json',aid) if aid in contact else evidence(PREPARATION/'NATIVE_MEASUREMENTS.json',aid),
                evidence(local_receipt if local_receipt.exists() else shared_receipt),
                evidence(Path(source['receipt'])) if source else None] if e],
            'lifecycle':{'native_saved':bool(path and native_sha),'catalog_connected':bool(rt['ObjectPath']),
                'runtime_enabled':enabled,'new_ordinary_generation':False,'new_saved_area_reopen':False,'final_visual_acceptance':False}}
        config = None
        if not aid.startswith('external.') and path and m:
            config=proposed_configuration(aid,record,p,m,configured,materials,catalog)
            job['configuration_payload']=config
            if config:
                job['contact_contract']={k:config[k] for k in ['contact_kind','anchor_z_cm','anchor_basis','forward_axis','forward_basis','bounds_cm','allowed_areas','allowed_zones','min_spacing_cm']}
            if not isheld and not enabled and config:
                native_payload.append(config)
                validation_preserved[aid]=copy.deepcopy(validation.get(aid,{'source_sha256':native_sha,'ready':False,
                    'contact_reviewed':False,'facing_reviewed':False,'material_reviewed':False,
                    'pending':'Exact native contact, facing and instance-material evidence remains missing; no readiness fabricated.'}))
        elif imp and imp.get('saved'):
            job['contact_contract']={'contact_kind':'building_foundation_unreviewed','anchor_z_cm_candidate':m['bounds_cm']['min'][2],
                'anchor_basis':'Native measured minimum is a candidate only; individual functional support plane not established.',
                'forward_axis_candidate':None,'native_scale':[1,1,1],'allowed_areas_proposed':AREAS,
                'allowed_zones_proposed':ZONES,'source_axes_not_copied_to_native':True}
        elif source:
            job['contact_contract']={'contact_kind':'authored_building_support_unreviewed',
                'source_support_candidate_z_m':source['bounds_m']['min'][2],
                'native_anchor_z_cm':None,'forward_axis':None,'allowed_areas_proposed':AREAS,'allowed_zones_proposed':ZONES,
                'native_import_readback_required':True,'source_axes_not_copied_to_native':True,
                'footprint_policy':'Retain every component transform, pavement/platform and authored envelope; no shrink/stretch to manufacture fit.'}
        if aid in manifest:
            payload=copy.deepcopy(shared_queue.get(aid,manifest[aid]))
            payload.update(original_explicit_hold=rt['ExplicitHold'],hold_reasons_preserved=record['hold_reasons'],native_activation=False,
                activation_policy='Import and binding preserve current ExplicitHold and exact reasons; no normal-use release.',
                source_bounds_m=source['bounds_m'],source_dimensions_m=source['dimensions_m'],original_source_receipt=source['receipt'],
                category='Buildings/Whole',required_consumer_context='whole_building_footprint_height_terrain_fit',
                primary_render_object_count=source['primary_render_object_count'])
            if aid in COHERENT_SOURCE_GROUPS:
                payload.update(category_combine_meshes=True,
                    category_composition_review='Existing prepared receipt plus actual existing geometry preview show components of one authored complete building; merge only these named components in their original transforms. Native geometry/material/readback and readiness remain unrun.',
                    category_object_members=copy.deepcopy(read(Path(source['receipt']))['objects']))
                job['source_composition_preview']=evidence(source['preview'])
            job['import_payload']=payload
            job['texture_file_identities']={str(Path(t['path']).resolve()):C.sha(t['path']) for t in payload['textures'] if Path(t['path']).is_file()}
            if aid in local_recipes:
                job['material_import_contract']=import_material_contract(payload,local_recipes[aid])
                job['native_material_behavior_exceptions']=local_recipes[aid].get('native_material_behavior_exceptions',[])
            if not imp and aid in COHERENT_SOURCE_GROUPS:
                new_imports.append(payload)
        missing=[]
        if isheld:
            missing.append({'code':'existing_explicit_hold_preserved','reasons':record['hold_reasons'],'action':'Integrator/manager must resolve the exact recorded hold with authorized evidence before enabling. This batch never clears it.'})
        if rt['StyleSet']!='mediterranean_urban':
            missing.append({'code':'exact_style_gate','recorded_style':rt['StyleSet'],'required_current_area_style':'mediterranean_urban','action':'Preserve recorded style; exact Gaza selector cannot use this row under current profiles.'})
        if exceptional:missing.append(exceptional)
        missing.extend(job.get('native_material_behavior_exceptions',[]))
        if not enabled:
            v=validation.get(aid,{})
            for field in ['contact_reviewed','facing_reviewed','material_reviewed']:
                if not v.get(field):missing.append({'code':field+'_missing','action':'Batch existing native/source evidence review and record an explicit exact-SHA validation; never an inventory replay or proof map.'})
        deps=m.get('dependencies',{})
        unresolved=deps.get('missing',deps.get('unresolved_registry_packages',[]))
        if unresolved:missing.append({'code':'unresolved_native_dependencies','paths':unresolved})
        job['exceptional_blockers']=missing
        if enabled:job['action']='retain_enabled_contract'
        elif exceptional:job['action']='preserve_composition_exception'
        elif aid in COHERENT_SOURCE_GROUPS and not imp:job['action']='import_authored_whole_group_preserve_hold'
        elif imp:job['action']='reuse_saved_import_connect_if_needed_preserve_hold'
        elif isheld:job['action']='retain_native_binding_preserve_hold'
        else:job['action']='complete_native_configuration_without_style_or_hold_change'
        delta={}
        if imp and imp.get('saved'):
            proposed={'ObjectPath':imp['native_path'],'AssetRevision':imp['native_sha256'],'BoundsValid':'true'}
            for axis,lo,hi in zip('XYZ',m['bounds_cm']['min'],m['bounds_cm']['max']):
                proposed['BoundsMin'+axis+'Cm']=str(lo);proposed['BoundsMax'+axis+'Cm']=str(hi)
            delta={k:{'before':rt[k],'after':v} for k,v in proposed.items() if rt[k]!=v}
        job['row_delta_ready']=delta
        job['row_delta_from_completed_import']={'requires':'Exact saved native import receipt, package SHA and full dependency/slot readback. Integrator shared apply_bank_configuration consumes IMPORTED_external_*.json.',
            'fields_from_receipt':['ObjectPath=native_path','AssetRevision=native_sha256','BoundsValid=true',
                                   'BoundsMin/MaxXYZCm=measurement.bounds_cm'],
            'preserve_fields':['ExplicitHold','HoldReasons','StyleSet','RunEligible','canonical rights/qualification'],
            'no_blender_bounds_to_native_columns':True} if source and not imp and not exceptional else None
        job['row_delta_after_exact_validation']=None
        if config and not isheld and not enabled:
            proposed={'Role':'whole_building','RequestRole':'whole_building','PlacementRule':'building_footprint',
                'RunEligible':'true','BoundsValid':'true','AnchorValid':'true','AnchorZCm':str(config['anchor_z_cm']),
                'OrientationValid':'true','ForwardAxis':config['forward_axis'],'StyleSet':rt['StyleSet'],
                'PlacementScope':'area_zone','AllowedAreas':'|'.join(AREAS),'AllowedZones':ZONES,'AllowedPlacementIds':'',
                'ReleaseId':catalog['normal_use_release_id'],'DecisionId':'Aviv_BankIntegration_2026-10-04_Nonmodular_v001',
                'MinSpacingCm':str(config['min_spacing_cm'])}
            for axis,lo,hi in zip('XYZ',config['bounds_cm']['min'],config['bounds_cm']['max']):
                proposed['BoundsMin'+axis+'Cm']=str(lo);proposed['BoundsMax'+axis+'Cm']=str(hi)
            job['row_delta_after_exact_validation']={'requires':['ready=true','matching mesh SHA','contact_reviewed=true','facing_reviewed=true','material_reviewed=true','all instance material slots saved','no hold','same recorded style'],
                'delta':{k:{'before':rt[k],'after':v} for k,v in proposed.items() if rt[k]!=v},
                'SelectionWeight':'Recompute aggregate 1.0/N over actually eligible family members after all eligibility gates; do not preallocate to held variants.'}
        if delta:row_patches.append({'asset_id':aid,'row_name':record['catalog_row_name'],'delta':delta,'requires_saved_import_sha256':native_sha,'hold_release':False})
        if path:bind[path]=job['instance_material_slots']
        original_material_paths=[s.get('path') for s in m.get('material_slots',[])]
        job['native_material_file_identities']=native_file_identities(job['instance_material_slots']+original_material_paths)
        family_members[(rt['FamilyId'],rt['StyleSet'])].append(aid)
        jobs.append(job)
    budgets=[]
    for (family,style),members in sorted(family_members.items()):
        active=[a for a in members if str(records[a]['runtime']['RunEligible']).lower() in ('true','1')]
        budgets.append({'role':'whole_building','family_id':family,'style':style,'areas':AREAS,'context':'building_footprint',
            'aggregate_budget':1.0,'all_canonical_members':members,'currently_enabled_members':active,
            'current_member_weight':1.0/len(active) if active else None,'weight_application':'Only integrator after actual eligibility filtering; preserve held/style-excluded identities.'})
    status=collections.Counter(j['action'] for j in jobs)
    adapter_source=INTEGRATION/'import_prepared.py'
    text=adapter_source.read_text(encoding='utf-8-sig')
    assert text.count('import bank_contracts as C')==1
    text=text.replace('import bank_contracts as C',
        'from category_batch import C\nassert __import__("sys").modules.get(C.__name__) is C, "unregistered_category_contracts"')
    assert text.count('def import_one(asset_id):\n    before=N.preflight()')==1
    text=text.replace('def import_one(asset_id):\n    before=N.preflight()',
        'def import_one(asset_id):\n    from category_batch import native_activation_guard\n    native_activation_guard()\n    before=N.preflight()')
    assert text.count("'combine_meshes':False")==1
    text=text.replace("'combine_meshes':False", "'combine_meshes':bool(job.get('category_combine_meshes', False))")
    # Authored component objects may reference the same material. Preserve each
    # native slot and require coverage of every used source material identity.
    text=text.replace("assert len(set(mapped_indices))==len(mapped_indices) and set(slot_usage['used_slots']).issubset(mapped_indices),'native_material_slots_lost_used_source_faces'",
                      "assert set(slot_usage['used_slots']).issubset(mapped_indices),'native_material_slots_lost_used_source_faces'")
    (HERE/'retained_import_adapter.py').write_text('# Category-owned derivative of '+str(adapter_source)+'; source SHA256 '+C.sha(adapter_source)+'\n'+text,encoding='utf-8')
    write('EXTERNAL_IMPORT_QUEUE.json',new_imports)
    existing_recipes=read(HERE/'EXTERNAL_MATERIAL_RECIPES.json',[])
    write('EXTERNAL_MATERIAL_RECIPES.json',existing_recipes)
    write('NATIVE_CONFIGURATIONS.json',{'schema':'environmentpipeline.bank_native_configuration.v2','decision_id':'Aviv_BankIntegration_2026-10-04_Nonmodular_v001','rows':native_payload,'native_activation_completed':False})
    write('NATIVE_VALIDATION_PRESERVE.json',validation_preserved)
    write('ROW_PATCHES.json',{'canonical_source_sha256':C.sha(CATALOG),'rows':row_patches,'shared_apply_owner':'bank_integrator','profile_merge_owner':'system_manager'})
    write('FAMILY_BUDGETS.json',budgets)
    write('CONSUMER_CONTRACT.json',consumer_contract())
    write('CANONICAL_GUARD.json',canonical_guard)
    write('INTEGRATOR_MERGE.json',{'native_configurations':{'operation':'merge_verified_existing_instance_materials_only_for_existing_rows',
        'destination':str(INTEGRATION/'NATIVE_CONFIGURATIONS.json'),'requires_same_source_sha256':True,
        'required_operative_fields':list(OPERATIVE_CONFIGURATION_FIELDS),
        'preserve_evidence_fields':list(PRESERVED_CONFIGURATION_EVIDENCE),
        'payload':[{'asset_id':j['asset_id'],'require_operative_values':{k:j[k] for k in OPERATIVE_CONFIGURATION_FIELDS},
                    'set':{'existing_instance_materials':j['existing_instance_materials']},'preserve_every_other_field':True} for j in native_payload],
        'normal_policy':'Preserve current native material graphs; no blanket building normal correction.'},
        'native_validation':{'operation':'preserve_existing_current_validation_never_overwrite_newer_review','payload':validation_preserved,
        'destination':str(INTEGRATION/'NATIVE_VALIDATION.json')},
        'materials':{'operation':'reuse_existing_saved_slot_order','mesh_slots':bind},
        'imports':{'operation':'copy_completed_exact_sha_receipts_only','sources':str(HERE/'IMPORTED_external_*.json'),
        'destination':str(INTEGRATION),'shared_apply_helper':str(INTEGRATION/'apply_bank_configuration.py')},
        'catalog_and_profiles':'Integrator builds/applies current shared transaction; system manager owns exact profile patch merge. Category never writes either.'})
    interface_jobs=[]
    for j in jobs:
        if j['action']=='complete_native_configuration_without_style_or_hold_change' and not j['gaza_style_matches']:
            interface_jobs.append({'asset_id':j['asset_id'],'source_sha256':j['native_sha256'],'object_path':j['object_path'],
                'bounds_cm':j['bounds_native_cm'],'instance_material_slots':j['instance_material_slots'],
                'owner':'system_manager','current_blocker':'Retained exact style gate excludes '+j['style_context_preserved']+' from current mediterranean_urban profiles.',
                'implementation_scope':'For the measured industrial warehouse only, manager may assign a bounded source-tag/zone and style-compatibility consumer contract after reviewing genuine local industrial geography. Stylized outbuildings retain stylized_town and require a matching future ordinary area style; no Mediterranean relabeling.',
                'input_contract':['source_area_id','source_osm_id','building_class from original geographic tag','source footprint polygon','height provenance','final terrain support','allowed recorded style for this exact request context'],
                'candidate_zone_contract':['building_industrial','building_warehouse'] if j['style_context_preserved']=='industrial_urban' else ['building_shed','building_hut','building_outbuilding'],
                'native_scale':[1,1,1],'authorization':'Category supplies exact contract only; no shared selector/profile edit or gate relaxation authorized here.'})
    write('CONSUMER_INTERFACE_JOBS.json',interface_jobs)
    data={'schema':'environmentpipeline.category_batch.v1','category':'WholeBuildings','exclusive_directory':str(HERE),
        'bank_integrator_thread':ownership['bank_integrator_thread'],'system_manager_thread':ownership['system_manager_thread'],
        'current_assignment':ownership,'canonical_guard':canonical_guard,
        'canonical_catalog_sha256':C.sha(CATALOG),'canonical_identity_count':len(records),'ordinary_generation_authorized_by_category':False,
        'scope_count':len(jobs),'native_count':sum(not j['asset_id'].startswith('external.') for j in jobs),
        'external_count':sum(j['asset_id'].startswith('external.') for j in jobs),'action_counts':dict(status),
        'native_configuration_payload':str(HERE/'NATIVE_CONFIGURATIONS.json'),'validation_preserve_payload':str(HERE/'NATIVE_VALIDATION_PRESERVE.json'),
        'import_payload':str(HERE/'EXTERNAL_IMPORT_QUEUE.json'),'row_patches':str(HERE/'ROW_PATCHES.json'),
        'consumer_contract':str(HERE/'CONSUMER_CONTRACT.json'),'family_budgets':budgets,'jobs':jobs,
        'normal_corrections_policy':'Do not execute old apply_building_normal_corrections; current H0902 and H0016 native graphs are already correct per delegated current native readback.',
        'native_execute_state':'NOT_RUN_BY_CATEGORY','saved_area_output_state':'NOT_RUN_BY_CATEGORY'}
    write('READY_JOBS.json',data)
    verify()
    pin_paths=[Path(__file__),HERE/'category_contracts.py',HERE/'collect_material_recipes.py',HERE/'retained_import_adapter.py',HERE/'READY_JOBS.json',HERE/'EXTERNAL_IMPORT_QUEUE.json',HERE/'EXTERNAL_MATERIAL_RECIPES.json',HERE/'NATIVE_CONFIGURATIONS.json',HERE/'CONSUMER_CONTRACT.json',
               HERE/'CANONICAL_GUARD.json',HERE/'CANONICAL_IDENTITY_BASELINE.json',HERE/'NATIVE_VALIDATION_PRESERVE.json',HERE/'INTEGRATOR_MERGE.json',HERE/'CONSUMER_INTERFACE_JOBS.json',HERE/'ROW_PATCHES.json',HERE/'FAMILY_BUDGETS.json',HERE/'VERIFICATION.json',
               INTEGRATION/'native_bank_ops.py',INTEGRATION/'bank_contracts.py',INTEGRATION/'bank_batch_loader.py']
    for name in ['verify_adapter.py','ADAPTER_CHECKS.json','CONFIGURATION_MERGE_READBACK.json']:
        if (HERE/name).is_file():pin_paths.append(HERE/name)
    if (HERE/'SOURCE_IMPORT_SLOT_USAGE.json').is_file():pin_paths.append(HERE/'SOURCE_IMPORT_SLOT_USAGE.json')
    pins={str(p.resolve()):C.sha(p) for p in pin_paths}
    batch_digest=hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    review_dir=HERE/'Reviews'/batch_digest
    reviewed_receipt=review_dir/'REVIEWED_BATCH.json'
    write('HANDOFF.json',{'schema':'environmentpipeline.category_handoff.v1','category':'WholeBuildings','status':'EXECUTABLE_BATCH_READY_NATIVE_INTEGRATOR_REQUIRED',
        'scope_count':len(jobs),'action_counts':dict(status),'files':pins,'current_assignment':ownership,
        'canonical_guard':canonical_guard,'batch_digest':batch_digest,'immutable_reviewed_receipt':str(reviewed_receipt),
        'native_activation_snapshot':{'receipt':evidence(BANK_ACTIVATION),
            'status':read(BANK_ACTIVATION)['status'],'native_authorized_now':read(BANK_ACTIVATION)['native_authorized_now'],
            'execution_guard':'Fresh exact actual-PID MANAGER_ACTIVATED bank lease and native_authorized_now=true are required; an inspection-only lease never permits this adapter.'},
        'loaded_command_identity':{'contracts_module_name':CONTRACTS_MODULE_NAME,'importer_module_name':IMPORTER_MODULE_NAME,
            'load':'Compile/execute exact reviewed source bytes, register stable unique names in sys.modules before execution.',
            'verify':'Captured resolved path/source SHA/module-code fingerprint plus live function source path and compiled code fingerprint before every import_one; unchanged actual C module object required.',
            'stale_cache':'Reject without hot reload or replacing a cached module.',
            'bank_loader':str(INTEGRATION/'bank_batch_loader.py'),'combined_command_module_name':'category_batch'},
        'additive_integrator_dependency':{'owner':ownership['bank_integrator_thread'],
            'helper':str(INTEGRATION/'apply_bank_configuration.py'),
            'current_helper_evidence':evidence(INTEGRATION/'apply_bank_configuration.py'),
            'required_contract':'Integrator preserves exact current canonical identities, rows and holds, typed source/CSV/native equivalence and transaction before hashes for additive supplier table application. Category already validates dynamic counts and original identity preservation; shared helper remains integrator-owned.'},
        'native_integrator_steps':['Load exact reviewed category module path/hash; existing sole lease and runtime seal preflight remain mandatory.',
            'Offline collect_material_recipes.py in Blender for only the five unimported coherent whole groups; original/prepared files are opened read-only and no new render is needed.',
            'Match required operative NATIVE_CONFIGURATIONS fields by asset_id. Merge verified existing_instance_materials only; preserve richer shared anchor_basis/review_note/style_policy and existing native validation.',
            'Only after successor actual-PID authoring reactivation: execute_native(reviewed_manifest, native_configs_merged=True) checks BANK_ACTIVATION and MANAGER_ACTIVATED lease, then reuses saved material slots and imports five complete authored groups; holds stay true.',
            'Rebuild category files; copy completed category IMPORTED_external_*.json into integrator receipts only after exact package/material/dependency readback. Existing apply_bank_configuration build/apply consumes them.',
            'Actual exact-SHA contact/facing/material validation is still required for seven non-held candidates. Preserve current native normal graphs.',
            'Integrator applies native DataTable/named saves; manager merges catalog digest and instance-material profile fields, then separately coordinates ordinary original-area replacement/save/reopen.'],
        'protected':['shared catalogs/CSV/DataTable/profiles/system/HDA/original sources/maps not written by category', 'all named and existing holds/rights/source styles', '87 unvalidated roads'],
        'native_execution':False,'ordinary_generation':False,'new_area_save_reopen':False,'source_compound_exceptions':[j['asset_id'] for j in jobs if j['composition_exception']]})
    review_dir.mkdir(parents=True,exist_ok=True)
    snapshots={}
    for path,expected in {**pins,str(HERE/'HANDOFF.json'):C.sha(HERE/'HANDOFF.json')}.items():
        origin=Path(path)
        if not origin.is_relative_to(HERE):continue
        target=review_dir/origin.name
        if target.is_file():assert C.sha(target)==expected,('immutable_review_snapshot_collision',str(target))
        else:shutil.copy2(origin,target)
        snapshots[str(target)]=expected
    review={'schema':'environmentpipeline.immutable_category_batch_review.v1','batch_digest':batch_digest,
        'current_assignment':ownership,'canonical_guard':canonical_guard,'runtime_original_path_hash_manifest':pins,
        'immutable_snapshots':snapshots,'snapshot_only_do_not_execute_from_review_directory':True,
        'preparation_complete':True,'native_execution':False,'ordinary_area_output_save_reopen':False}
    if reviewed_receipt.is_file():assert read(reviewed_receipt)==review,'immutable_review_receipt_collision'
    else:C.write(reviewed_receipt,review)
    print(json.dumps({'category':'WholeBuildings','scope':len(jobs),'actions':dict(status),'native_run':False}))
    return data

def verify():
    data=read(HERE/'READY_JOBS.json');jobs=data['jobs']
    assert len({j['asset_id'] for j in jobs})==len(jobs)
    assert len({j['row_name'] for j in jobs})==len(jobs)
    paths=[j['object_path'] for j in jobs if j['object_path']]
    assert len(set(paths))==len(paths),'duplicate_native_identity'
    assert C.sha(CATALOG)==data['canonical_catalog_sha256'],'catalog_changed_rebuild_batch_before_apply'
    catalog,current_guard=canonical_catalog()
    assert current_guard==data['canonical_guard'],'canonical_csv_or_guard_changed_rebuild_batch'
    records={r['asset_id']:r for r in catalog['rows']}
    failures=[]
    for j in jobs:
        record=records[j['asset_id']];rt=record['runtime']
        assert j['row_name']==record['catalog_row_name'] and j['holds']['ExplicitHold']==rt['ExplicitHold'] and j['holds']['HoldReasons']==rt['HoldReasons']
        assert j['holds']['canonical_reasons']==record['hold_reasons'] and j['rights_state_preserved']==record['recorded_rights_state']
        assert j['source_style_preserved']==record['environment_style_set'] and j['style_context_preserved']==rt['StyleSet']
        if j['native_sha256'] and C.sha(C.package_file(j['object_path']))!=j['native_sha256']:failures.append([j['asset_id'],'native_sha'])
        if j['prepared_blend'] and C.sha(j['prepared_blend'])!=j['prepared_blend_sha256']:failures.append([j['asset_id'],'prepared_sha'])
        if j['asset_id'].startswith('external.') and j['prepared_blend'] and C.sha(j['source_fbx'])!=j['source_sha256']:failures.append([j['asset_id'],'fbx_sha'])
        for mapping in [j.get('texture_file_identities',{}),j.get('native_material_file_identities',{})]:
            for path,expected in mapping.items():
                if C.sha(path)!=expected:failures.append([j['asset_id'],path])
        if str(j['holds']['ExplicitHold']).lower() in ('true','1'):
            assert j['row_delta_after_exact_validation'] is None and not j['lifecycle']['runtime_enabled'],j['asset_id']
        if any(h in j['asset_id'] for h in NAMED_HOLDS):
            assert str(j['holds']['ExplicitHold']).lower() in ('true','1'),j['asset_id']
        assert all(k not in j['row_delta_ready'] for k in ['ExplicitHold','HoldReasons','StyleSet','RunEligible'])
    assert not failures,failures
    recipes={r['asset_id']:r for r in read(HERE/'EXTERNAL_MATERIAL_RECIPES.json',[])}
    checked_materials=0
    for job in read(HERE/'EXTERNAL_IMPORT_QUEUE.json',[]):
        assert job['asset_id'] in COHERENT_SOURCE_GROUPS and job['category_combine_meshes']
        assert len(job['category_object_members'])==job['primary_render_object_count']
        if job['asset_id'] not in recipes:continue
        rec=recipes[job['asset_id']]
        assert C.sha(job['prepared_blend'])==rec['prepared_blend_sha256']
        for material in rec['materials']:
            p=material['principled_inputs'];refs={r['channel']:r for r in job['textures'] if r['material']==material['source_material']}
            assert 'BaseColor' in refs or not p['Base Color']['links'],('unresolved_base_color_link',job['asset_id'],material['source_material'])
            assert not p['Alpha']['links'] or p['Alpha']['links'][0]['output']=='Alpha',('unsupported_alpha_graph',job['asset_id'],material['source_material'])
            if 'ORM_R_AO_G_Roughness_B_Metallic' not in refs:
                assert not p['Roughness']['links'] and not p['Metallic']['links'],('unsupported_scalar_graph',job['asset_id'],material['source_material'])
            checked_materials+=1
    write('VERIFICATION.json',{'status':'PASS','scope_count':len(jobs),'identity_and_native_reference_deduplication':True,
        'source_and_native_file_hashes_match':True,'all_holds_rights_source_styles_preserved':True,
        'ready_row_deltas_do_not_enable_held_rows':True,'new_import_material_contracts_checked':checked_materials,
        'native_operation_or_area_generation':False})
    return True

def execute_native(reviewed_manifest, native_configs_merged=False):
    """Integrator-only native import/material batch. No catalog/profile/map writes."""
    contracts_path=str((HERE/'category_contracts.py').resolve())
    assert contracts_path in reviewed_manifest,('unbound_category_contracts',contracts_path)
    _verify_registered_source(C,contracts_path,reviewed_manifest[contracts_path])
    for path,expected in reviewed_manifest.items():
        assert C.sha(path)==expected,('reviewed_category_file_changed',path)
    for path in [Path(__file__),HERE/'category_contracts.py',HERE/'retained_import_adapter.py']:
        assert str(path.resolve()) in reviewed_manifest,('unbound_category_module',str(path))
    native_activation_guard()
    sys.path.insert(0,str(INTEGRATION))
    import native_bank_ops as N
    import bank_contracts as bank
    import bank_batch_loader as loader
    assert Path(N.__file__).resolve()==(INTEGRATION/'native_bank_ops.py').resolve()
    assert Path(bank.__file__).resolve()==(INTEGRATION/'bank_contracts.py').resolve()
    # Every loaded helper is bound to the exact path/hash manifest as well.
    for module in [N,bank,loader]:
        path=str(Path(module.__file__).resolve())
        assert path in reviewed_manifest and C.sha(path)==reviewed_manifest[path],('unbound_bank_helper',path)
        loader.verify_module(module,path)
    before=N.preflight();verify()
    import_jobs=read(HERE/'EXTERNAL_IMPORT_QUEUE.json')
    recipes={r['asset_id']:r for r in read(HERE/'EXTERNAL_MATERIAL_RECIPES.json',[])}
    slot_usage=read(HERE/'SOURCE_IMPORT_SLOT_USAGE.json',{})
    for job in import_jobs:
        assert job['asset_id'] in recipes and job['asset_id'] in slot_usage,('category_recipe_not_collected',job['asset_id'])
        assert recipes[job['asset_id']]['prepared_blend_sha256']==slot_usage[job['asset_id']]['sha256']==C.sha(job['prepared_blend'])
    configs=read(HERE/'NATIVE_CONFIGURATIONS.json')['rows']
    shared={j['asset_id']:j for j in bank.read(bank.HERE/'NATIVE_CONFIGURATIONS.json')['rows']}
    assert native_configs_merged,'integrator_must_approve_operative_and_material_configuration_merge_first'
    material_state=bank.read(bank.HERE/'NATIVE_INSTANCE_MATERIALS.json')
    material_pins={path:sha for job in read(HERE/'READY_JOBS.json')['jobs']
                   for path,sha in job.get('native_material_file_identities',{}).items()}
    configuration_readback=verify_configuration_merge(configs,shared,material_state,material_pins)
    source_path=HERE/'retained_import_adapter.py'
    importer=_load_registered_source(IMPORTER_MODULE_NAME,source_path,reviewed_manifest[str(source_path.resolve())])
    assert importer.C is C,'importer_uses_different_category_contracts'
    loader.verify_module(importer,source_path)
    results=[]
    for j in import_jobs:
        assert j['asset_id'] in recipes,('category_recipe_not_collected',j['asset_id'])
        assert j['category_combine_meshes'] and j['asset_id'] in COHERENT_SOURCE_GROUPS
        _verify_registered_source(C,contracts_path,reviewed_manifest[contracts_path])
        _verify_registered_source(importer,source_path,reviewed_manifest[str(source_path.resolve())])
        assert importer.C is C,'importer_category_contracts_identity_changed'
        loader.verify_module(importer,source_path)
        results.append(importer.import_one(j['asset_id']))
    contracts_identity=_verify_registered_source(C,contracts_path,reviewed_manifest[contracts_path])
    importer_identity=_verify_registered_source(importer,source_path,reviewed_manifest[str(source_path.resolve())])
    after=N.preflight()
    assert after['world']==before['world'] and after['dirty']['maps']==before['dirty']['maps']
    write('NATIVE_EXECUTION.json',{'pid':before['pid'],'imported_ids':[r['asset_id'] for r in results],
        'material_configuration_ids':[],'verified_configuration_readback':configuration_readback,
        'holds_preserved':True,'catalog_written':False,'profiles_written':False,'maps_saved':False,
        'loaded_modules':[contracts_identity,importer_identity]})
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--build',action='store_true');parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    if args.build:build()
    elif args.verify:verify()
    else:parser.print_help()
