import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3';base='/Game/Project/Shared/Atmosphere/ReusableSky/'
bp=unreal.load_asset(base+'BP_EnvironmentSky');sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
 d=unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h);c=unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(d,bp)
 if c.get_name().startswith('CelestialDome'):
  c.set_editor_property('relative_scale3d',unreal.Vector(2500,2500,2500));c.set_editor_property('visible_in_ray_tracing',False)
BP.compile_blueprint(bp,True)
RESULT={'dome_radius_km':102.4,'raytracing_visible':False,'setter_doc':unreal.Object.set_editor_property.__doc__,'notify':str(unreal.PropertyAccessChangeNotifyMode.__doc__)}
(r/'DOME_REFINEMENT.json').write_text(json.dumps(RESULT,indent=2))
