import json,os
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
dm=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
dc=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
assert dm==[] and set(dc).issubset({'/SunPosition/SunSky'}),(dm,dc)
RESULT={'pid':os.getpid(),'dirty_maps':dm,'discarded_unsaved_vendor_inspection_buffer':dc,'shutdown_saves':0,'other_editors_touched':False}
(root/('EXIT_'+str(os.getpid())+'.json')).write_text(json.dumps(RESULT,indent=2))
unreal.SystemLibrary.quit_editor()
