import json,os
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3/Resume'
tag=json.loads((r/'PRESERVATION_REQUEST.json').read_text())['tag']
def transform(t):
 return {'location':[t.translation.x,t.translation.y,t.translation.z],'rotation':[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w],'scale':[t.scale3d.x,t.scale3d.y,t.scale3d.z]}
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors();data={}
for a in actors:
 if a.get_name()=='BP_EnvironmentSky_C_0':continue
 entry={'class':a.get_class().get_path_name(),'label':a.get_actor_label(),'transform':transform(a.get_actor_transform()),'hidden':a.is_hidden_ed()}
 cs=[]
 for c in a.get_components_by_class(unreal.SceneComponent):
  v={'name':c.get_name(),'visible':c.is_visible(),'relative_transform':transform(c.get_relative_transform())}
  if isinstance(c,unreal.LightComponentBase):v['intensity']=c.intensity
  if isinstance(c,unreal.ExponentialHeightFogComponent):
   for k in ['fog_density','fog_height_falloff','fog_max_opacity','fog_inscattering_luminance']:v[k]=str(c.get_editor_property(k)).split(' {')[-1]
  if isinstance(c,unreal.PostProcessComponent):v['settings']=str(c.settings);v['blend_weight']=c.blend_weight
  cs.append(v)
 entry['components']=cs;data[a.get_name()]=entry
if tag=='after':
 before=json.loads((r/'SCENE_BEFORE.json').read_text())['actors']
 assert data==before,'Unrelated actor state changed; inspect preservation receipt'
RESULT={'pid':os.getpid(),'actors':data,'actor_count':len(actors),'tag':tag,'matches_before':tag=='after'}
(r/('SCENE_'+tag.upper()+'.json')).write_text(json.dumps(RESULT,indent=2));RESULT={'actor_count':len(actors),'matches_before':tag=='after'}
