import json
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3/Resume'
names=['r.EyeAdaptationQuality','r.EyeAdaptation.PreExposureOverride','r.UsePreExposure','r.DefaultFeature.AutoExposure','r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange','r.EyeAdaptation.LensAttenuation','r.SkyLight.RealTimeReflectionCapture','r.VolumetricRenderTarget.Mode']
RESULT={'cvars':{n:unreal.SystemLibrary.get_console_variable_float_value(n) for n in names},'camera':str(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_level_viewport_camera_info())}
(r/'EXPOSURE_INSPECTION.json').write_text(json.dumps(RESULT,indent=2))
