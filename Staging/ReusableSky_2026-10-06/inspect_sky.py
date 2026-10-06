import json, os
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
def dirty():
 return {'content':[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],'maps':[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]}
before=dirty()
sky=unreal.load_asset('/SunPosition/SunSky')
graphs={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(sky)} if sky else {}
(root/'SUNSKY_REFERENCE_GRAPHS.json').write_text(json.dumps(graphs,indent=2))
lights=[]
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 if any(a.get_components_by_class(c) for c in [unreal.DirectionalLightComponent,unreal.SkyLightComponent,unreal.SkyAtmosphereComponent,unreal.PostProcessComponent,unreal.ExponentialHeightFogComponent,unreal.VolumetricCloudComponent]) or isinstance(a,unreal.PostProcessVolume):
  lights.append({'label':a.get_actor_label(),'path':a.get_path_name(),'class':a.get_class().get_name()})
RESULT={'pid':os.getpid(),'map':unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(),'dirty_before':before,'dirty_after':dirty(),'cooking_paused':unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused(),'sun_loaded':bool(sky),'solar_api':hasattr(unreal,'SunPositionFunctionLibrary'),'graphs':list(graphs),'lights':lights,'bp_editor_methods':[x for x in dir(unreal.BlueprintEditorLibrary) if 'variable' in x or 'metadata' in x],'blueprint_class':str(type(sky))}
(root/'PREFLIGHT_SKY_EDITOR.json').write_text(json.dumps(RESULT,indent=2))
