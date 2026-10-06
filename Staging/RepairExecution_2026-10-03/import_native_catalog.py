"""Import the reviewed one-row scoped repair into the existing native table."""
import unreal
import json
import os
import csv
from pathlib import Path
import importlib.util

PROJECT = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE = PROJECT / 'Staging/RepairExecution_2026-10-03'
lease = (PROJECT / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
assert 'OWNER=CODEX_REPAIR_MANAGER' in lease and f'assigned_editor_PID={os.getpid()}' in lease
api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
assert api.is_asset_cooking_paused()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
assert world == '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration'
dirty = [p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
from geocity_editor_action import acknowledged_cook_leftovers
assert set(dirty).issubset(acknowledged_cook_leftovers(PROJECT, dirty))
spec = importlib.util.spec_from_file_location('pole_configuration', str(HERE / 'configure_pole5.py'))
configuration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(configuration)
table_path = '/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4'
table = unreal.load_asset(table_path)
assert isinstance(table, unreal.DataTable)
prior = json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
assert configuration.digest(prior) == configuration.BEFORE_DIGEST
(HERE / 'NATIVE_TABLE_BEFORE.json').write_text(json.dumps(prior, indent=2), encoding='utf-8')
assert unreal.DataTableFunctionLibrary.fill_data_table_from_csv_file(table, str(configuration.CSV))
actual = json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
report = json.loads(configuration.RECEIPT.read_text())
with configuration.CSV.open(encoding='utf-8-sig', newline='') as stream:
    expected = list(csv.DictReader(stream))
assert configuration.typed_rows(actual) == configuration.typed_rows(expected), 'Native table fields differ from reviewed CSV'
assert configuration.digest(actual) == report['after_typed_catalog_sha256']
assert unreal.EditorAssetLibrary.save_asset(table_path, only_if_is_dirty=True)
(HERE / 'NATIVE_TABLE_READBACK.json').write_text(json.dumps(configuration.typed_rows(actual), indent=2), encoding='utf-8')
(HERE / 'NATIVE_TABLE_IMPORT.json').write_text(json.dumps({'table': table_path, 'saved': True, 'row_count': len(actual), 'catalog_sha256': configuration.digest(actual), 'changed_row': configuration.ROW_NAME}, indent=2), encoding='utf-8')
print(json.dumps({'native_table_saved': table_path, 'rows': len(actual), 'digest': configuration.digest(actual)}))
