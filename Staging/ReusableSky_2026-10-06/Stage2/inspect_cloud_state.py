import json
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors();out={}
for a in actors:
 if a.get_name() not in ['BP_EnvironmentSky_C_0','VolumetricCloud_0','ExponentialHeightFog_0']:continue
 for c in a.get_components_by_class(unreal.SceneComponent):
  if isinstance(c,(unreal.VolumetricCloudComponent,unreal.SkyAtmosphereComponent,unreal.ExponentialHeightFogComponent)):
   d={'class':c.get_class().get_name(),'transform':str(c.get_world_transform())}
   for k in ['layer_bottom_altitude','layer_height','tracing_start_max_distance','tracing_max_distance','planet_radius','fog_density','mie_scattering','mie_scattering_scale','rayleigh_scattering_scale','visible','ground_albedo','use_per_sample_atmospheric_light_transmittance','stop_tracing_transmittance_threshold']:
    try:d[k]=str(c.get_editor_property(k))
    except:pass
   out[c.get_path_name()]=d
RESULT=out
(root/'CLOUD_STATE.json').write_text(json.dumps(out,indent=2))
