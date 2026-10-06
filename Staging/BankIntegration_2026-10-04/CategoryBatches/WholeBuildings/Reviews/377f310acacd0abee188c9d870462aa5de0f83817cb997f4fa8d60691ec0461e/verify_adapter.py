"""Offline transaction checks; no Unreal import, asset mutation or scene proof."""
import ast
import copy
import csv
import sys
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
checks={'schema':'environmentpipeline.category_adapter_checks.v1','status':'PASS',
    'current_source_csv_equivalence':True,'current_rows':len(rows),'in_memory_additive_rows_accepted':len(add_rows),
    'changed_hold_rejected':True,'dropped_row_rejected':True,'duplicate_identity_rejected':True,
    'changed_runtime_identity_rejected':True,'dropped_hold_field_rejected':True,
    'source_csv_or_native_assets_written':False,'activation_guard_precedes_unreal_helper_import':True,
    'old_blanket_normal_correction_not_called':True,'all_category_python_parses':True}
B.write('ADAPTER_CHECKS.json',checks)
print(checks)
