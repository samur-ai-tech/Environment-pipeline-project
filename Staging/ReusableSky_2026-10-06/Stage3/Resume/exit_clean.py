import json,os
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3/Resume'
assert not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor()
dc=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()];dm=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()];assert not dc and not dm,(dc,dm)
p=r/'EDITOR_PREFERENCES_BEFORE.json'
if p.exists():
 s=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
 for k,v in json.loads(p.read_text()).items():s.set_editor_property(k,v)
RESULT={'pid':os.getpid(),'dirty_content':dc,'dirty_maps':dm,'requested_clean_exit':True,'shutdown_saves':0,'temporary_preferences_restored':True}
(r/('EXIT_REQUEST_'+str(os.getpid())+'.json')).write_text(json.dumps(RESULT,indent=2))
unreal.SystemLibrary.quit_editor()
