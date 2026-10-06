"""Read original Epic ground graphs and current consumer; no setters/saves."""
import hashlib,json,os,types
from pathlib import Path
import unreal
root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
here=root/'Staging/GroundPainting_2026-10-04'
rev=here/'Revision_2026-10-05'
f=here/'native_ground_texture_policy.py'
assert hashlib.sha256(f.read_bytes()).hexdigest()=='bdba22a3bcf801663788166649e3fd593704507f133995a1085ed0b37c2404b4'
p=types.ModuleType('epic_ground_inspect_definitions');p.__file__=str(f)
exec(compile(f.read_bytes(),str(f),'exec'),p.__dict__)
h=p.load_helper();p.sole_editor();assert os.getpid()==ARGS['expected_pid']==32464
assignment=json.loads((here/'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
sources,actors=h.guard(assignment,world,False)
def dirty():
 return {'maps':sorted(h.path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),'content':sorted(h.path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
before={'dirty':dirty(),'sources':sources,'scene':h.scene_state(actors)}
materials={};textures={};files={}
for name in ('M_Ground_Gravel','M_Rock_Sandstone','M_Concrete_Poured','M_Ground_Grass','M_Ground_Moss'):
 path='/Game/StarterContent/Materials/'+name; files[path]=h.sha(h.package_file(path))
 mat=unreal.load_asset(path);assert isinstance(mat,unreal.Material)
 rows={h.path(e):h.describe(mat,e) for e in h.LIB.get_material_expressions(mat)}
 roots={k:h.path(h.LIB.get_material_property_input_node(mat,v)) for k,v in h.PROPERTIES.items()}
 materials[path]={'roots':roots,'nodes':rows,'settings':{k:h.plain(h.safe(mat,k)) for k in ('two_sided','use_material_attributes','blend_mode','shading_model','tangent_space_normal','material_domain')}}
 for e in h.LIB.get_material_expressions(mat):
  texture=h.safe(e,'texture')
  if isinstance(texture,unreal.Texture2D) and h.path(texture) not in textures:
   textures[h.path(texture)]=p.texture_details(h,texture);files[h.path(texture)]=h.sha(h.package_file(h.path(texture)))
master=unreal.load_asset(h.MASTER)
instances={v:h.material_state(master,unreal.load_asset(v)) for v in [h.BASE]+list(assignment['material_contract']['area_instances'].values())}
nodes={h.path(e):h.describe(master,e) for e in h.LIB.get_material_expressions(master)}
after_sources,after_actors=h.guard(assignment,world,False)
assert before=={'dirty':dirty(),'sources':after_sources,'scene':h.scene_state(after_actors)}
assert all(h.sha(h.package_file(k))==v for k,v in files.items())
out=rev/'EPIC_STARTER_GROUND_NATIVE_READONLY_PID32464.json';assert not out.exists()
result={'status':'EPIC_ORIGINAL_GRAPHS_READ_ONLY','pid':os.getpid(),'world':world,'materials':materials,'textures':textures,'original_file_sha256':files,'state':before,'natural_nodes':nodes,'instances':instances,'native_mutation':False}
out.write_text(json.dumps(result,indent=2))
RESULT={'receipt':str(out),'sha256':h.sha(out),'material_counts':{k:len(v['nodes']) for k,v in materials.items()},'roots':{k:v['roots'] for k,v in materials.items()},'dirty':dirty()}
