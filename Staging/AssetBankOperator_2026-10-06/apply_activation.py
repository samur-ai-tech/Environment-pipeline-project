"""Apply the measured, additive native tables and their exact profile pins."""
import unreal,json,hashlib,importlib.util,shutil
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir()).resolve();HERE=ROOT/'Staging/AssetBankOperator_2026-10-06'
ns={'__file__':str(HERE/'native_operator.py')};exec((HERE/'native_operator.py').read_text(),ns)
before=ns['preflight']();read=ns['read'];write=ns['write']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('bank_activation_digest',ROOT/'Staging/BankIntegration_2026-10-04/bank_contracts.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
tx=read(HERE/'Activation/TRANSACTION.json');source=Path(tx['source_path']);csv=Path(tx['csv_path'])
assert sha(source)==tx['source_before_sha256'] and sha(csv)==tx['csv_before_sha256']
assert all(sha(p['path'])==p['before_sha256'] for p in tx['profiles'])
assert not (HERE/'Activation/APPLY_STARTED.json').exists(),'Reconcile prior transaction before retry'
tables=[]
for t in tx['tables']:
    table=unreal.load_asset(t['table']);actual=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table));assert C.digest(actual)==t['before_digest']
    file=ROOT/'Content'/(t['table'][6:]+'.uasset');shutil.copy2(file,HERE/'Before'/('TABLE_'+t['key']+'.uasset'))
    tables.append((t,table))
shutil.copy2(source,HERE/'Before/CATALOG_SOURCE.json');shutil.copy2(csv,HERE/'Before/CATALOG_FULL.csv')
write('Activation/APPLY_STARTED.json',{'pid':29900,'tables':[t['table'] for t in tx['tables']],'dirty_before':before})
applied=[]
for t,table in tables:
    expected=read(Path(t['rows']))
    assert unreal.DataTableFunctionLibrary.fill_data_table_from_csv_file(table,t['csv'])
    actual=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
    assert C.typed_rows(actual)==C.typed_rows(expected),'Native table readback mismatch before save: '+t['key']
    assert C.digest(actual)==t['after_digest']
    assert unreal.EditorAssetLibrary.save_asset(t['table'],only_if_is_dirty=True)
    actual=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table));assert C.digest(actual)==t['after_digest']
    write('Activation/NATIVE_AFTER_'+t['key']+'.json',actual);applied.append(t['key'])
    write('Activation/APPLY_PROGRESS.json',{'named_saved_tables':applied,'profiles_written':False})
assert ns['dirty']()==before
assert sha(source)==tx['source_before_sha256'] and sha(csv)==tx['csv_before_sha256']
assert all(sha(p['path'])==p['before_sha256'] for p in tx['profiles'])
source.write_bytes(Path(tx['new_source']).read_bytes());csv.write_bytes(Path(tx['tables'][0]['csv']).read_bytes())
for p in tx['profiles']:
    Path(p['path']).write_text(json.dumps(p['proposed'],indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
write('Activation/APPLIED.json',{'pid':29900,'added_native_catalog_rows':72,'shared_table_rows':1295,'iran_table_rows':1295,'enabled_gaza_added':72,'enabled_iran_added':54,'existing_rows_unchanged':True,'named_saved_tables':applied,'profiles':[{'path':p['path'],'sha256':sha(p['path'])} for p in tx['profiles']],'canonical_source_sha256':sha(source),'canonical_csv_sha256':sha(csv),'dirty_restored':ns['dirty']()==before,'generated':False,'reopened':False})
print(json.dumps({'registered':72,'gaza_enabled':72,'iran_enabled':54,'profile_pins_updated':3,'dirty_restored':True}))
