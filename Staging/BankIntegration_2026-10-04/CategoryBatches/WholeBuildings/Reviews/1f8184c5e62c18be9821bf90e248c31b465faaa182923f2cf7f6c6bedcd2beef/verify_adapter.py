"""Offline transaction checks; no Unreal import, asset mutation or scene proof."""
import ast
import copy
import csv
import sys
import types
from pathlib import Path

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import category_batch as B

catalog=B.read(B.CATALOG)
with B.CATALOG_CSV.open(encoding='utf-8-sig',newline='') as stream:
    reader=csv.DictReader(stream);fields=list(reader.fieldnames);rows=list(reader)
B.validate_canonical_rows(catalog,rows,fields)

def rejected(c,r,f=fields):
    try:B.validate_canonical_rows(c,r,f)
    except AssertionError:return True
    raise AssertionError('invalid_transaction_was_not_rejected')

# The additive fixture exists only in memory and carries a hold. It cannot be
# written to a shared catalog or selected/loaded as a model by this check.
added=copy.deepcopy(catalog['rows'][0])
added['asset_id']='OFFLINE_GUARD_FIXTURE_ADDITIVE_IDENTITY'
added['catalog_row_name']='OFFLINE_GUARD_FIXTURE_ADDITIVE_ROW'
added['runtime'].update(AssetId=added['asset_id'],Name=added['catalog_row_name'],RunEligible='false',ExplicitHold='true',HoldReasons='offline_guard_fixture_only')
add_catalog=copy.deepcopy(catalog);add_catalog['rows'].append(added)
add_rows=copy.deepcopy(rows);add_rows.append(copy.deepcopy(added['runtime']))
B.validate_canonical_rows(add_catalog,add_rows,fields)

changed=copy.deepcopy(rows);changed[0]['ExplicitHold']='false' if changed[0]['ExplicitHold']=='true' else 'true'
rejected(catalog,changed)
rejected(catalog,rows[:-1])
duplicate=copy.deepcopy(catalog);duplicate['rows'].append(copy.deepcopy(duplicate['rows'][0]))
rejected(duplicate,rows+[copy.deepcopy(rows[0])])
renamed=copy.deepcopy(rows);renamed[0]['AssetId']='OFFLINE_GUARD_FIXTURE_CHANGED_ID'
rejected(catalog,renamed)
missing_field=copy.deepcopy(rows);missing_field[0].pop('HoldReasons')
rejected(catalog,missing_field)

for path in HERE.glob('*.py'):ast.parse(path.read_text(encoding='utf-8-sig'))
tree=ast.parse((HERE/'category_batch.py').read_text())
native=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute_native')
gate=next(n.lineno for n in ast.walk(native) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='native_activation_guard')
first_native_import=min(n.lineno for n in ast.walk(native) if isinstance(n,ast.Import) and any(a.name=='native_bank_ops' for a in n.names))
assert gate<first_native_import,'native_helper_loaded_before_activation_guard'
assert 'apply_building_normal_corrections(' not in ast.get_source_segment((HERE/'category_batch.py').read_text(),native)
contracts_path=HERE/'category_contracts.py'
contracts_sha=B.C.sha(contracts_path)
binding=B._verify_registered_source(B.C,contracts_path,contracts_sha)
fixture_name='environmentpipeline_whole_buildings_identity_check_fixture'
assert fixture_name not in sys.modules,'identity_fixture_already_loaded'
fixture=B._load_registered_source(fixture_name,contracts_path,contracts_sha)
fixture_identity=id(fixture)
assert B._load_registered_source(fixture_name,contracts_path,contracts_sha) is fixture

def identity_rejected(fn):
    try:fn()
    except AssertionError:return
    raise AssertionError('changed_loaded_identity_was_not_rejected')

try:
    saved_binding=dict(getattr(fixture,B.SOURCE_IDENTITY_ATTRIBUTE))
    stale_binding={**saved_binding,'source_sha256':'0'*64}
    setattr(fixture,B.SOURCE_IDENTITY_ATTRIBUTE,stale_binding)
    identity_rejected(lambda:B._load_registered_source(fixture_name,contracts_path,contracts_sha))
    assert id(sys.modules[fixture_name])==fixture_identity,'stale_cache_was_reloaded'
    setattr(fixture,B.SOURCE_IDENTITY_ATTRIBUTE,saved_binding)
    original_sha=fixture.sha
    replacement={}
    exec(compile('def sha(path):\n    return "changed_live_code"\n',str(contracts_path.resolve()),'exec',dont_inherit=True),fixture.__dict__,replacement)
    fixture.sha=replacement['sha']
    identity_rejected(lambda:B._verify_registered_source(fixture,contracts_path,contracts_sha))
    fixture.sha=original_sha
    original_here=fixture.HERE;fixture.HERE=HERE/'wrong_category_scope'
    identity_rejected(lambda:B._verify_registered_source(fixture,contracts_path,contracts_sha))
    fixture.HERE=original_here
    sys.modules[fixture_name]=types.ModuleType(fixture_name)
    identity_rejected(lambda:B._verify_registered_source(fixture,contracts_path,contracts_sha))
    sys.modules[fixture_name]=fixture
    B._verify_registered_source(fixture,contracts_path,contracts_sha)
finally:
    # Only the disposable in-memory test module is removed. The actual category
    # contracts object and every native helper remain untouched.
    if sys.modules.get(fixture_name) is fixture:del sys.modules[fixture_name]

sys.path.insert(0,str(B.INTEGRATION))
import bank_batch_loader as bank_loader
bank_loader.verify_module(B.C,contracts_path)
bank_loader.verify_module(B,HERE/'category_batch.py')
# Check the actual retained importer source with inert in-memory API names.
# No Unreal library is loaded, import_one is never called, and no editor or
# asset operation can occur. The stubs exist only in this offline check process.
assert 'unreal' not in sys.modules and 'native_bank_ops' not in sys.modules
assert B.IMPORTER_MODULE_NAME not in sys.modules
unreal_stub=types.ModuleType('unreal')
unreal_stub.EditorAssetLibrary=object()
unreal_stub.MaterialEditingLibrary=object()
native_stub=types.ModuleType('native_bank_ops')
sys.modules['unreal']=unreal_stub;sys.modules['native_bank_ops']=native_stub
importer=None
try:
    importer_path=HERE/'retained_import_adapter.py';importer_sha=B.C.sha(importer_path)
    importer=B._load_registered_source(B.IMPORTER_MODULE_NAME,importer_path,importer_sha)
    assert sys.modules[B.IMPORTER_MODULE_NAME] is importer and importer.C is B.C
    assert B._load_registered_source(B.IMPORTER_MODULE_NAME,importer_path,importer_sha) is importer
    bank_loader.verify_module(importer,importer_path)
    original_import_one=importer.import_one
    replacement={}
    exec(compile('def import_one(asset_id):\n    return "changed_import_code"\n',str(importer_path.resolve()),'exec',dont_inherit=True),importer.__dict__,replacement)
    importer.import_one=replacement['import_one']
    identity_rejected(lambda:B._load_registered_source(B.IMPORTER_MODULE_NAME,importer_path,importer_sha))
    assert sys.modules[B.IMPORTER_MODULE_NAME] is importer,'changed_importer_was_reloaded'
    importer.import_one=original_import_one
    B._verify_registered_source(importer,importer_path,importer_sha)
finally:
    if importer is not None and sys.modules.get(B.IMPORTER_MODULE_NAME) is importer:del sys.modules[B.IMPORTER_MODULE_NAME]
    if sys.modules.get('unreal') is unreal_stub:del sys.modules['unreal']
    if sys.modules.get('native_bank_ops') is native_stub:del sys.modules['native_bank_ops']
configs=B.read(HERE/'NATIVE_CONFIGURATIONS.json')['rows']
existing={j['asset_id']:j for j in B.read(B.INTEGRATION/'NATIVE_CONFIGURATIONS.json')['rows']}
material_state=B.read(B.INTEGRATION/'NATIVE_INSTANCE_MATERIALS.json')
material_pins={path:sha for job in B.read(HERE/'READY_JOBS.json')['jobs'] for path,sha in job.get('native_material_file_identities',{}).items()}
merged=copy.deepcopy(existing)
for job in configs:
    merged[job['asset_id']]['existing_instance_materials']=copy.deepcopy(material_state['mesh_slots'][job['object_path']])
merged_before=copy.deepcopy(merged)
verified=B.verify_configuration_merge(configs,merged,material_state,material_pins)
assert merged==merged_before,'configuration_guard_modified_shared_evidence'
for job in configs:
    aid=job['asset_id']
    for key in B.PRESERVED_CONFIGURATION_EVIDENCE:
        assert merged[aid].get(key)==existing[aid].get(key)
    assert {k for k in merged[aid] if merged[aid].get(k)!=existing[aid].get(k)}<= {'existing_instance_materials'}
bad=copy.deepcopy(merged);bad[configs[0]['asset_id']]['anchor_z_cm']+=1.0
identity_rejected(lambda:B.verify_configuration_merge(configs,bad,material_state,material_pins))
bad=copy.deepcopy(merged);bad[configs[0]['asset_id']]['package_sha256']='0'*64
identity_rejected(lambda:B.verify_configuration_merge(configs,bad,material_state,material_pins))
bad=copy.deepcopy(merged);bad[configs[0]['asset_id']]['existing_instance_materials']=[]
identity_rejected(lambda:B.verify_configuration_merge(configs,bad,material_state,material_pins))
bad=copy.deepcopy(merged);bad[configs[0]['asset_id']]['style_policy']['configured_runtime_style']='wrong_style'
identity_rejected(lambda:B.verify_configuration_merge(configs,bad,material_state,material_pins))
bad_pins=dict(material_pins);first_slot=configs[0]['existing_instance_materials'][0]
bad_pins[str(B.C.package_file(first_slot).resolve())]='0'*64
identity_rejected(lambda:B.verify_configuration_merge(configs,merged,material_state,bad_pins))
checks={'schema':'environmentpipeline.category_adapter_checks.v1','status':'PASS',
    'current_source_csv_equivalence':True,'current_rows':len(rows),'in_memory_additive_rows_accepted':len(add_rows),
    'changed_hold_rejected':True,'dropped_row_rejected':True,'duplicate_identity_rejected':True,
    'changed_runtime_identity_rejected':True,'dropped_hold_field_rejected':True,
    'source_csv_or_native_assets_written':False,'activation_guard_precedes_unreal_helper_import':True,
    'old_blanket_normal_correction_not_called':True,'all_category_python_parses':True,
    'actual_contracts_registered_source_sha_and_live_code_verified':True,
    'cached_identity_reused_without_reload':True,'stale_cached_source_sha_rejected_without_reload':True,
    'changed_live_function_same_path_rejected':True,'changed_contract_scope_rejected':True,
    'registry_module_replacement_rejected':True,'current_bank_loader_verifies_category_and_actual_contracts':True,
    'actual_importer_exact_source_registered_and_bank_loader_verified_offline':True,
    'actual_importer_uses_same_contracts_object':True,'changed_cached_importer_rejected_without_reload':True,
    'native_api_stub_context':'Inert names in standalone offline process only; no Unreal library loaded and no import_one or editor operation called.',
    'operative_configuration_and_verified_material_merge_passes':len(verified),
    'richer_shared_anchor_review_and_style_evidence_preserved':True,
    'configuration_merge_guard_does_not_mutate_inputs':True,
    'changed_operative_anchor_or_source_sha_rejected':True,
    'unmerged_material_bindings_rejected':True,'changed_material_package_hash_rejected':True,
    'changed_operative_style_policy_rejected':True,
    'contracts_module_name':binding['module_name'],'importer_module_name':B.IMPORTER_MODULE_NAME}
B.write('ADAPTER_CHECKS.json',checks)
print(checks)
