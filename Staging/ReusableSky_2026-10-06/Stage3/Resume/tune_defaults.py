import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky');cdo=unreal.get_default_object(bp.generated_class())
defaults={'MoonBrightness':.006,'MoonDiskBrightness':.04,'StarBrightness':.02,'NightSkyFill':.12,'AnimateTime':False,'TimePaused':False,'DayLengthMinutes':20.}
for k,v in defaults.items():cdo.set_editor_property(k,v)
BP.compile_blueprint(bp,True)
RESULT={'defaults':defaults,'defaults_readback':{k:cdo.get_editor_property(k) for k in defaults}}
(r/'Resume/TUNED_DEFAULTS.json').write_text(json.dumps(RESULT,indent=2))
