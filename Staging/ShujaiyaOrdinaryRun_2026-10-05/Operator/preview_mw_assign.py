import os,json,time,unreal
from pathlib import Path
from datetime import datetime,timezone
assert os.getpid()==16824,'unexpected PID'
ROOT=Path(r'C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
OUT=ROOT/'Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/MWPreview_20261006'; OUT.mkdir(exist_ok=True)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
lands=[a for a in eas.get_all_level_actors() if isinstance(a,unreal.Landscape)]
assert len(lands)==1,('expected one Landscape',[a.get_path_name() for a in lands])
land=lands[0]
orig=land.get_editor_property('landscape_material')
orig_path=orig.get_path_name() if orig else None
mw_path='/Game/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_DesertExample.MTL_MWAM_Landscape_DesertExample'
mw=unreal.load_asset(mw_path)
assert mw is not None,'MW desert instance not found'
dirty_before=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]+[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
land.set_editor_property('landscape_material',mw)
now=land.get_editor_property('landscape_material')
rec={'pid':os.getpid(),'utc':datetime.now(timezone.utc).isoformat(),'world':world.get_outermost().get_path_name(),'landscape':land.get_path_name(),
     'original_material':orig_path,'preview_material':now.get_path_name() if now else None,'dirty_before':dirty_before,
     'note':'UNSAVED PREVIEW for Aviv decision (Unreal auto-landscape material on our terrain). Must be reverted and the editor closed WITHOUT saving.'}
(OUT/'PREVIEW_ASSIGN.json').write_text(json.dumps(rec,indent=2),encoding='utf-8')
print(json.dumps({'ok':True,'original':orig_path,'now':rec['preview_material'],'dirty_before':len(dirty_before)}))
