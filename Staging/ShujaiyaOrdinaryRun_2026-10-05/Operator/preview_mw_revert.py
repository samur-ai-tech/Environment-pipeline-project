import os,json,unreal
from pathlib import Path
from datetime import datetime,timezone
assert os.getpid()==16824
OUT=Path(r'C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/MWPreview_20261006')
rec=json.loads((OUT/'PREVIEW_ASSIGN.json').read_text(encoding='utf-8'))
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
land=[a for a in eas.get_all_level_actors() if isinstance(a,unreal.Landscape)][0]
orig=unreal.load_asset(rec['original_material'])
land.set_editor_property('landscape_material',orig)
now=land.get_editor_property('landscape_material').get_path_name()
dirty=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]+[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
(OUT/'PREVIEW_REVERT.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'restored_material':now,'matches_original':now==rec['original_material'],'dirty_after_revert_unsaved':dirty,'note':'preview reverted in memory; nothing saved; editor to be closed without saving before any authoring'},indent=2),encoding='utf-8')
print(json.dumps({'ok':True,'restored':now==rec['original_material'],'dirty':dirty}))
