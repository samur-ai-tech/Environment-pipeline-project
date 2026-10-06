"""Read-only graph, texture and lighting diagnosis for rejected ground appearance."""
import datetime,json,os
from pathlib import Path
import unreal
import geocity_runtime_guard
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
HERE=ROOT/'Staging/GroundPainting_2026-10-04'
lease=[s for s in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1]
assert 'OWNER=CODEX_GROUND_PAINTING' in lease and f'assigned_editor_PID={os.getpid()} ' in lease
geocity_runtime_guard.verify()
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() and not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
LIB=unreal.MaterialEditingLibrary
def path(o):return o.get_path_name() if o else None
def safe(o,k):
 try:return o.get_editor_property(k)
 except Exception:return None
def describe(o):
 return {'path':path(o),'class':o.get_class().get_name(),**{k:str(safe(o,k)) for k in ('parameter_name','default_value','constant','sampler_type','desc')},'texture':path(safe(o,'texture')),'function':path(safe(o,'material_function'))}
master=unreal.load_asset('/Game/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural')
nodes=LIB.get_material_expressions(master)
graph=[]
for e in nodes:
 row=describe(e);row['input_names']=list(LIB.get_material_expression_input_names(e));row['inputs']=[path(i) for i in LIB.get_inputs_for_material_expression(master,e)]
 if isinstance(e,unreal.MaterialExpressionLandscapeLayerBlend):row['layers']=[{'name':str(l.get_editor_property('layer_name')),'blend_type':str(l.get_editor_property('blend_type'))} for l in e.get_editor_property('layers')]
 graph.append(row)
roots={n:path(LIB.get_material_property_input_node(master,v)) for n,v in [('color',unreal.MaterialProperty.MP_BASE_COLOR),('normal',unreal.MaterialProperty.MP_NORMAL),('roughness',unreal.MaterialProperty.MP_ROUGHNESS),('specular',unreal.MaterialProperty.MP_SPECULAR),('ao',unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)]}
textures={}
for e in nodes:
 t=safe(e,'texture')
 if t and path(t) not in textures:textures[path(t)]={k:str(safe(t,k)) for k in ('srgb','compression_settings','lod_group','mip_gen_settings','never_stream','virtual_texture_streaming','size_x','size_y')}
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
lights=[]
for a in actors:
 for c in a.get_components_by_class(unreal.LightComponentBase):
  lights.append({'actor':path(a),'class':a.get_class().get_name(),'component':path(c),'actor_hidden_editor':a.is_hidden_ed(),'rotation':str(a.get_actor_rotation()),**{k:str(safe(c,k)) for k in ('intensity','light_color','visible','affects_world','cast_shadows','indirect_lighting_intensity','volumetric_scattering_intensity','mobility','source_type','source_cubemap','real_time_capture')}})
postprocess=[]
for a in actors:
 if isinstance(a,unreal.PostProcessVolume):
  settings=safe(a,'settings');postprocess.append({'actor':path(a),'enabled':str(safe(a,'enabled')),'unbound':str(safe(a,'unbound')),'settings':str(settings)})
functions={}
for fname in ('WorldAlignedNormal','WorldAlignedTexture'):
 f=unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions01/Texturing/'+fname)
 expressions=safe(f,'function_expressions')
 functions[fname]={'path':path(f),'expressions_property_available':expressions is not None,'expressions':[describe(e) for e in expressions] if expressions else [],'functions_api':[n for n in dir(LIB) if 'function' in n.lower()]}
result={'pid':os.getpid(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'world':world.get_outermost().get_path_name(),'master_properties':{k:str(safe(master,k)) for k in ('tangent_space_normal','two_sided','blend_mode','shading_model','enable_tessellation','displacement_scaling')},'roots':roots,'graph':graph,'texture_settings':textures,'lighting':lights,'postprocess':postprocess,'engine_functions':functions,'dirty_maps_after':[path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],'dirty_content_after':[path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
assert not result['dirty_maps_after'] and not result['dirty_content_after']
out=HERE/'Revision_2026-10-05'/f'NATIVE_DIAGNOSIS_PID{os.getpid()}.json';out.write_text(json.dumps(result,indent=2),encoding='utf-8')
RESULT={'receipt':str(out),'master_properties':result['master_properties'],'roots':roots,'graph_count':len(graph),'lighting':lights,'postprocess_count':len(postprocess),'function_expression_counts':{k:len(v['expressions']) for k,v in functions.items()}}
