import json
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3';actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors();a=next(x for x in actors if x.get_name()=='BP_EnvironmentSky_C_0');d=a.get_editor_property('CelestialDome');mat=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/M_EnvironmentCelestial')
pps=[]
for x in actors:
 if isinstance(x,unreal.PostProcessVolume):
  s=x.get_editor_property('settings');pps.append({'actor':x.get_path_name(),'enabled':x.get_editor_property('enabled'),'unbound':x.get_editor_property('unbound'),'min_ev':s.auto_exposure_min_brightness,'max_ev':s.auto_exposure_max_brightness,'override_min':s.override_auto_exposure_min_brightness,'override_max':s.override_auto_exposure_max_brightness})
RESULT={'dome_material':str(d.get_material(0)),'dome_bounds':str(d.get_local_bounds()),'dome_scale':str(d.get_world_scale()),'material_is_sky':mat.get_editor_property('is_sky'),'material_shading':str(mat.get_editor_property('shading_model')),'material_node_count':unreal.MaterialEditingLibrary.get_num_material_expressions(mat),'exposure_volumes':pps}
(r/'LOOK_INSPECTION.json').write_text(json.dumps(RESULT,indent=2))
