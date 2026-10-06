import json
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3'
m=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/M_EnvironmentCelestial')
# A property notification refreshes only this material; do not run the broad streaming rebuild.
m.set_editor_property('two_sided',True,unreal.PropertyAccessChangeNotifyMode.ALWAYS)
RESULT={'stats':str(unreal.MaterialEditingLibrary.get_statistics(m))}
(r/'NARROW_COMPILE.json').write_text(json.dumps(RESULT,indent=2))
