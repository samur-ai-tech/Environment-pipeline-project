"""Structured graph identity/readback verification across fresh original-map processes."""
import datetime,hashlib,json,os
from pathlib import Path
import unreal,geocity_runtime_guard
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve();HERE=ROOT/'Staging/GroundPainting_2026-10-04';REV=HERE/'Revision_2026-10-05';LIB=unreal.MaterialEditingLibrary
assignment=json.loads((HERE/'ASSIGNMENT.json').read_text());world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();named_map=world.get_outermost().get_path_name();area=next(k for k,v in assignment['original_maps'].items() if v==named_map)
fields=dict(t.split('=',1) for t in [s for s in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1].split() if '=' in t)
assert fields['OWNER']=='CODEX_GROUND_PAINTING' and fields['assigned_editor_PID']==str(os.getpid()) and fields['map']==named_map and fields['operator_thread_id']==assignment['execution_thread_id']
geocity_runtime_guard.verify();assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
def path(o):return o.get_path_name() if o else None
def safe(o,k):
 try:return o.get_editor_property(k)
 except Exception:return None
def canonical(v):
 if v is None or isinstance(v,(str,int,float,bool)):return v
 for fields in [('r','g','b','a'),('x','y','z','w'),('x','y','z')]:
  if all(hasattr(v,k) for k in fields):return [float(getattr(v,k)) for k in fields]
 if isinstance(v,unreal.Object):return path(v)
 s=str(v);assert '0x' not in s, 'No transient addresses in graph identity';return s
master=unreal.load_asset(assignment['material_contract']['master']);base=unreal.load_asset(assignment['material_contract']['base_instance']);child=unreal.load_asset(assignment['material_contract']['area_instances'][area])
assert isinstance(master,unreal.Material) and isinstance(child,unreal.MaterialInstanceConstant) and child.get_editor_property('parent')==base and base.get_editor_property('parent')==master
nodes=LIB.get_material_expressions(master);graph={}
for e in nodes:
 inputs=LIB.get_inputs_for_material_expression(master,e)
 row={'class':e.get_class().get_name(),'input_names':list(LIB.get_material_expression_input_names(e)),'inputs':[path(x) for x in inputs],'output_names':list(LIB.get_material_expression_output_names(e)),
      'input_outputs':{path(x):str(LIB.get_input_node_output_name_for_material_expression(e,x)) for x in inputs if x},
      'properties':{k:canonical(safe(e,k)) for k in ('parameter_name','default_value','constant','value','r','g','b','a','const_a','const_b','const_alpha','const_exponent','const_min','const_max','min_default','max_default','sampler_type','sampler_source','texture','material_function','mapping_scale','mapping_rotation','mapping_pan_u','mapping_pan_v','mapping_type','custom_uv_type','transform_source_type','transform_type')}}
 if isinstance(e,unreal.MaterialExpressionLandscapeLayerBlend):row['layers']=[{'name':str(x.get_editor_property('layer_name')),'type':str(x.get_editor_property('blend_type'))} for x in e.get_editor_property('layers')]
 if isinstance(e,unreal.MaterialExpressionLandscapeGrassOutput):row['grass_types']=[{'name':str(x.get_editor_property('name')),'grass_type':path(x.get_editor_property('grass_type'))} for x in e.get_editor_property('grass_types')]
 graph[path(e)]=row
roots={n:path(LIB.get_material_property_input_node(master,v)) for n,v in [('color',unreal.MaterialProperty.MP_BASE_COLOR),('normal',unreal.MaterialProperty.MP_NORMAL),('roughness',unreal.MaterialProperty.MP_ROUGHNESS),('ao',unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)]}
assert all(roots.values()) and safe(master,'tangent_space_normal') is True
layers=[[x['name'] for x in graph[p]['layers']] for p in roots.values()];assert len(layers[0])==69 and len(set(layers[0]))==69 and all(x==layers[0] for x in layers)
assert len([e for e in nodes if isinstance(e,unreal.MaterialExpressionLandscapeGrassOutput)])==1
targets=('Sand_01','Sand_02','Dirt_Path','Sand_Path');parameters={str(k):float(LIB.get_material_instance_scalar_parameter_value(child,k)) for k in LIB.get_scalar_parameter_names(master)}
assert 0<=parameters['GeoCity_GrassCoverage']<=1
texture_params={str(k):path(LIB.get_material_instance_texture_parameter_value(child,k)) for k in LIB.get_texture_parameter_names(master)}
settings={}
for t in targets:
 mask=unreal.load_asset(texture_params[t+'_PackedMask']);assert mask.get_editor_property('srgb') is False and mask.get_editor_property('compression_settings')==unreal.TextureCompressionSettings.TC_MASKS
 settings[t]={'path':path(mask),'srgb':False,'compression':'TC_MASKS'}
assert texture_params['Sand_01_Normal'].startswith('/Game/Project/Shared/SurfacePainting/Appearance_20261003/Textures/T_Sand_01_Normal_GeoCity.')
assert texture_params['Sand_02_Normal'].startswith('/Game/Project/Shared/SurfacePainting/Appearance_20261003/Textures/T_Sand_02_Normal_GeoCity.')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors();landscapes=[x for x in actors if isinstance(x,unreal.LandscapeProxy)]
assert all(x.get_editor_property('landscape_material')==child for x in landscapes)
assert all(x.get_actor_scale3d().x==100 and x.get_actor_scale3d().y==100 for x in landscapes)
backup=json.loads((REV/'BACKUP_MANIFEST.json').read_text())
for rel,h in {**backup['preserved_files'],**backup['sealed_files']}.items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h,rel
for row in backup['files']:
 if any(n in row['file'] for n in ('LG_GeoCity_','MI_SurfaceBank_Natural','T_Sand_01_Normal_GeoCity','T_Sand_02_Normal_GeoCity')):assert hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest()==row['sha256'],row['file']
signature={'graph':graph,'roots':roots,'tangent_space_normal':True,'enable_tessellation':bool(safe(master,'enable_tessellation'))}
reference={}
if ARGS.get('reference_receipt'):
 refpath=Path(ARGS['reference_receipt']).resolve();assert REV in refpath.parents
 ref=json.loads(refpath.read_text());assert signature==ref['signature'],'Fresh graph differs from reviewed retained graph'
 reference={'path':str(refpath),'sha256':hashlib.sha256(refpath.read_bytes()).hexdigest(),'signature_sha256':ref['signature_sha256']}
assert signature['enable_tessellation'] is False
result={'pid':os.getpid(),'area':area,'world':named_map,'master':path(master),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'graph_preserved':bool(reference),'reference':reference,'graph_count':len(nodes),'signature_sha256':hashlib.sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest(),'signature':signature,'parameters':parameters,'texture_settings':settings,'effective_grass':parameters['GeoCity_GrassCoverage'],'preserved_source_vendor_base_grass_normals':True,'ordinary_generation_run':False}
out=REV/f'VERIFY_{area}_{ARGS["stage"]}_PID{os.getpid()}.json';assert not out.exists();out.write_text(json.dumps(result,indent=2),encoding='utf-8')
RESULT={k:v for k,v in result.items() if k not in ('signature','parameters')};RESULT['receipt']=str(out)
