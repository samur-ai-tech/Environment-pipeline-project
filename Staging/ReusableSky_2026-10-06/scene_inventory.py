import json,os
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
rows=[]
for a in actors:
 if any(x in a.get_actor_label().lower() for x in ['sky','light','fog','cloud','postprocess']):
  comps=[]
  for c in a.get_components_by_class(unreal.SceneComponent):
   d={'path':c.get_path_name(),'class':c.get_class().get_name(),'visible':c.is_visible(),'rotation':str(c.get_world_rotation())}
   for p in ['intensity','static_mesh','real_time_capture','settings']:
    try:d[p]=str(c.get_editor_property(p))[:300]
    except:pass
   if isinstance(c,unreal.StaticMeshComponent):d['materials']=[str(m.get_path_name()) if m else None for m in c.get_materials()]
   comps.append(d)
  rows.append({'path':a.get_path_name(),'label':a.get_actor_label(),'class':a.get_class().get_name(),'components':comps})
RESULT={'pid':os.getpid(),'count':len(actors),'actors':rows,'capture_methods':[x for x in dir(unreal.EditorAppToolset) if 'capture' in x],'dirty_content':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],'dirty_maps':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]}
(root/'SCENE_BEFORE.json').write_text(json.dumps(RESULT,indent=2))
