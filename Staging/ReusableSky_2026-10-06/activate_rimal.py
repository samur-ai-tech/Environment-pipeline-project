import json
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors={a.get_name():a for a in sub.get_all_level_actors()}
targets={'DirectionalLight_0':unreal.DirectionalLightComponent,'SkyLight_0':unreal.SkyLightComponent,'SkyAtmosphere_0':unreal.SkyAtmosphereComponent,'StaticMeshActor_0':unreal.StaticMeshComponent}
receipt=[]
for name,cls in targets.items():
 a=actors[name];cs=a.get_components_by_class(cls);assert len(cs)==1
 c=cs[0];assert c.is_visible()
 if name=='StaticMeshActor_0':assert a.get_actor_label()=='SM_SkySphere'
 receipt.append({'actor':a.get_path_name(),'label':a.get_actor_label(),'component':c.get_path_name(),'previous_visible':True,'new_visible':False})
(root/'LIGHTING_RESTORATION.json').write_text(json.dumps(receipt,indent=2))
for name,cls in targets.items():
 c=actors[name].get_components_by_class(cls)[0];c.modify();c.set_editor_property('visible',False)
a=actors['BP_EnvironmentSky_C_0'];a.set_editor_property('RigEnabled',True)
# Read ordinary property-edit results first; no explicit UpdateSky invocation.
RESULT={'status':a.get_editor_property('Status'),'conflicts':a.get_editor_property('ConflictActors'),'rig_enabled':a.get_editor_property('RigEnabled'),'clock':a.get_editor_property('ClockDisplay'),'sun':str(a.get_component_by_class(unreal.DirectionalLightComponent).get_world_rotation()),'lights':{c.get_name():c.is_visible() for c in a.get_components_by_class(unreal.SceneComponent)}}
(root/'ACTIVATED.json').write_text(json.dumps(RESULT,indent=2))
