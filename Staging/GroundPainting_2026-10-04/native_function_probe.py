"""Read-only installed function and native packed-texture contract inspection."""
import datetime,json,os
from pathlib import Path
import unreal,geocity_runtime_guard
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
HERE=ROOT/'Staging/GroundPainting_2026-10-04';LIB=unreal.MaterialEditingLibrary
lease=[s for s in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1]
assert 'OWNER=CODEX_GROUND_PAINTING' in lease and f'assigned_editor_PID={os.getpid()} ' in lease
geocity_runtime_guard.verify()
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() and not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
def path(o):return o.get_path_name() if o else None
def safe(o,k):
 try:return o.get_editor_property(k)
 except Exception:return None
def describe(e,asset,is_function):
 inputs=(LIB.get_inputs_for_material_function_expression(asset,e) if is_function else LIB.get_inputs_for_material_expression(asset,e))
 row={'path':path(e),'class':e.get_class().get_name(),'input_names':list(LIB.get_material_expression_input_names(e)),
      'inputs':[path(x) for x in inputs],
      'input_outputs':{path(x):str(LIB.get_input_node_output_name_for_material_expression(e,x)) for x in inputs if x},
      'properties':{k:str(safe(e,k)) for k in ('parameter_name','input_name','output_name','input_type','use_preview_value_as_default','preview_value','sort_priority','desc','default_value','constant','r','g','b','a','sampler_type','transform_source_type','transform_type','code','output_type')},
      'texture':path(safe(e,'texture')),'function':path(safe(e,'material_function'))}
 return row
function_paths=['/Engine/Functions/Engine_MaterialFunctions01/Texturing/'+n for n in ('WorldAlignedNormal','WorldAlignedTexture')]
function_paths+=['/Game/Iceland_Environment/Materials/MaterialFunctions/'+n for n in ('MF_TextureCellBomb','MF_DistanceTextureBlend','MF_DistanceCellBlend','MF_TriplanarProjection_Normal','MF_TriplanarProjection','MF_NormalIntensity','MF_MatLayerBlend_Standard_Normal')]
function_paths+=['/Game/MOUT_Arabian/Materials/Landscape/Material_Function/MF_Layer_Base']
function_paths+=['/Game/Iceland_Environment/Materials/SubMaterials/MF_A']
functions={}
for p in function_paths:
 f=unreal.load_asset(p)
 if not isinstance(f,unreal.MaterialFunction):
  functions[p]={'path':path(f),'class':f.get_class().get_name() if f else None,'unavailable':True,'nodes':[]};continue
 functions[p]={'path':path(f),'class':f.get_class().get_name(),'nodes':[describe(e,f,True) for e in LIB.get_material_function_expressions(f)]}
materials={}
for p in ARGS.get('materials',['/Game/Iceland_Environment/Materials/M_AutoLandscape']):
 m=unreal.load_asset(p)
 if not isinstance(m,unreal.Material):
  materials[p]={'path':path(m),'class':m.get_class().get_name() if m else None,'unavailable':True,'nodes':[]};continue
 materials[p]={'path':path(m),'tangent_space_normal':str(safe(m,'tangent_space_normal')),'nodes':[describe(e,m,False) for e in LIB.get_material_expressions(m)]}
result={'pid':os.getpid(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'functions':functions,'materials':materials,'input_api':[n for n in dir(LIB) if 'input' in n.lower() or 'output' in n.lower()]}
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() and not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
out=HERE/'Revision_2026-10-05'/f'INSTALLED_FUNCTIONS_PID{os.getpid()}.json';out.write_text(json.dumps(result,indent=2),encoding='utf-8')
RESULT={'receipt':str(out),'function_counts':{k:len(v['nodes']) for k,v in functions.items()},'material_counts':{k:len(v['nodes']) for k,v in materials.items()}}
