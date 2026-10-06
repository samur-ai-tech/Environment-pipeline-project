import json
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3'
m=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/M_EnvironmentCelestial')
s=unreal.MaterialEditingLibrary.get_statistics(m)
RESULT={'stats':str(s),'dirty_content':[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],'dirty_maps':[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]}
(r/'SHADER_STATS.json').write_text(json.dumps(RESULT,indent=2))
