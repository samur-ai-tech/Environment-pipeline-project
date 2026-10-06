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
    'contracts_module_name':binding['module_name'],'importer_module_name':B.IMPORTER_MODULE_NAME}
B.write('ADAPTER_CHECKS.json',checks)
print(checks)
