import os,json
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
dc=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()];dm=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
assert dc==[] and dm==[],(dc,dm)
prefs=root/'PERFORMANCE_EDITOR_SETTINGS_BEFORE.json'
if prefs.exists():
 obj=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
 data=json.loads(prefs.read_text())
 for k,v in data.items():
  if k.startswith('b'):obj.set_editor_property(k,v)
RESULT={'pid':os.getpid(),'dirty_content':dc,'dirty_maps':dm,'shutdown_saves':0,'other_editors_touched':False}
(root/('EXIT_'+str(os.getpid())+'.json')).write_text(json.dumps(RESULT,indent=2))
unreal.SystemLibrary.quit_editor()
