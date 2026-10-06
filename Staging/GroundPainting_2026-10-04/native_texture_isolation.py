"""One temporary Sand albedo override; inspect/start/restore. Root owns all calls and capture."""
import datetime,hashlib,json,os,sys,time
from pathlib import Path
import unreal,geocity_runtime_guard
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve();HERE=ROOT/'Staging/GroundPainting_2026-10-04';REV=HERE/'Revision_2026-10-05';LIB=unreal.MaterialEditingLibrary
assignment=json.loads((HERE/'ASSIGNMENT.json').read_text());world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();named_map=world.get_outermost().get_path_name();area=next(k for k,v in assignment['original_maps'].items() if v==named_map)
fields=dict(t.split('=',1) for t in [s for s in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1].split() if '=' in t)
assert fields['OWNER']=='CODEX_GROUND_PAINTING' and fields['activation']=='GROUND_AUTHORING' and fields['assigned_editor_PID']==str(os.getpid()) and fields['map']==named_map and fields['operator_thread_id']==assignment['execution_thread_id']
geocity_runtime_guard.verify();assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert not any(getattr(r,k,None) is not None for n in ('geocity_bank_workflow','geocity_roadbld_workflow') for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle','_pending_correction'))
assert not unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
assert sum(isinstance(a,unreal.HoudiniAssetActor) for a in actors)==1
for a in actors:
 if isinstance(a,unreal.HoudiniAssetActor):
  w=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,a);assert not w.is_auto_cooking_enabled() and not w.is_auto_bake_enabled()
baseline_path=Path(ARGS['baseline_receipt']).resolve(strict=True);assert HERE in baseline_path.parents
baseline=json.loads(baseline_path.read_text());assert baseline['pid']==os.getpid() and baseline['world']==named_map and not baseline['dirty_maps'] and not baseline['dirty_content']
def path(o):return o.get_path_name() if o else None
def transforms():return {path(a):{'translation':[getattr(a.get_actor_transform().translation,c) for c in ('x','y','z')],'rotation':[getattr(a.get_actor_transform().rotation,c) for c in ('x','y','z','w')],'scale':[getattr(a.get_actor_transform().scale3d,c) for c in ('x','y','z')]} for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
assert transforms()==baseline['actor_transforms']
child=unreal.load_asset(assignment['material_contract']['area_instances'][area]);base=unreal.load_asset(assignment['material_contract']['base_instance']);master=unreal.load_asset(assignment['material_contract']['master'])
assert isinstance(child,unreal.MaterialInstanceConstant) and child.get_editor_property('parent')==base and base.get_editor_property('parent')==master
landscapes=[a for a in actors if isinstance(a,unreal.LandscapeProxy)];assert sorted(path(a) for a in landscapes)==sorted(s['path'] for s in baseline['landscapes'])
assert all(a.get_editor_property('landscape_material')==child and a.get_actor_scale3d().x==100 and a.get_actor_scale3d().y==100 for a in landscapes)
shared='/Game/Project/Shared/SurfacePainting/Appearance_20261003';allowed={master.get_outermost().get_path_name(),child.get_outermost().get_path_name()}|{shared+'/Textures/T_'+n+'_Mask_GeoCity' for n in ('Sand_01','Sand_02','Dirt_Path_01','Sand_Path_01')}
def dirty():return {'maps':[path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],'content':[path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
before_dirty=dirty();assert set(before_dirty['content'])<=allowed and set(before_dirty['maps'])<={named_map}
PARAM='Sand_01_Albedo';WHITE='/Engine/EngineResources/WhiteSquareTexture.WhiteSquareTexture';white=unreal.load_asset(WHITE);original=LIB.get_material_instance_texture_parameter_value(child,PARAM);assert isinstance(original,unreal.Texture2D) and isinstance(white,unreal.Texture2D)
def texture(o):return {'path':path(o),'class':o.get_class().get_name(),'srgb':o.get_editor_property('srgb'),'compression':str(o.get_editor_property('compression_settings'))}
ASSOC=(unreal.MaterialParameterAssociation.GLOBAL_PARAMETER,unreal.MaterialParameterAssociation.LAYER_PARAMETER,unreal.MaterialParameterAssociation.BLEND_PARAMETER)
def overrides():return [{'name':str(v.get_editor_property('parameter_info').get_editor_property('name')),'association':ASSOC.index(v.get_editor_property('parameter_info').get_editor_property('association')),'index':v.get_editor_property('parameter_info').get_editor_property('index'),'texture':path(v.get_editor_property('parameter_value')),'guid':[v.get_editor_property('expression_guid').get_editor_property(c) for c in ('a','b','c','d')]} for v in child.get_editor_property('texture_parameter_values')]
def native_rows(rows):
 out=[]
 for v in rows:
  info=unreal.MaterialParameterInfo();guid=unreal.Guid();row=unreal.TextureParameterValue()
  for k,x in {'name':v['name'],'association':ASSOC[v['association']],'index':v['index']}.items():info.set_editor_property(k,x)
  for k,x in zip(('a','b','c','d'),v['guid']):guid.set_editor_property(k,x)
  row.set_editor_property('parameter_info',info);row.set_editor_property('parameter_value',unreal.load_asset(v['texture']) if v['texture'] else None);row.set_editor_property('expression_guid',guid);out.append(row)
 return out
grass=LIB.get_material_instance_scalar_parameter_value(child,'GeoCity_GrassCoverage');other={k:str(child.get_editor_property(k)) for k in ('scalar_parameter_values','vector_parameter_values')};snapshot=overrides();native_rows(snapshot)
out=REV/f'TEXTURE_ISOLATION_PID{os.getpid()}.json';mode=ARGS['mode'];assert mode in ('inspect','start','restore')
RESULT={'pid':os.getpid(),'world':named_map,'area':area,'original':texture(original),'white':texture(white),'original_overrides':snapshot,'explicit_save_called':False}
if mode!='inspect':
 assert white.get_editor_property('srgb') is True and white.get_editor_property('compression_settings')==unreal.TextureCompressionSettings.TC_DEFAULT
 if mode=='start':
  assert not out.exists();capture=Path(ARGS['capture_receipt']).resolve();assert HERE in capture.parents and not capture.exists()
  r=dict(RESULT,status='original_snapshotted_before_override',started_epoch=time.time(),capture_receipt=str(capture),grass=grass,other=other,dirty_before=before_dirty);out.write_text(json.dumps(r,indent=2),encoding='utf-8')
 else:
  r=json.loads(out.read_text());assert r['pid']==os.getpid() and r['world']==named_map and r['status']=='white_override_active' and path(original)==WHITE
  capture=Path(r['capture_receipt']).resolve(strict=True);assert ARGS['capture_finished'] is True;cap=json.loads(capture.read_text());image=Path(cap['path']).resolve(strict=True);pixels=image.read_bytes()
  assert cap['pid']==os.getpid() and cap['area']==area and cap['requested'] is True and cap['valid_task'] is True and HERE in image.parents and image.stat().st_mtime>=r['started_epoch'] and pixels.startswith(b'\x89PNG\r\n\x1a\n') and pixels.endswith(b'\x00\x00\x00\x00IEND\xaeB'+bytes([96,130]))
  assert grass==r['grass'] and other==r['other'];r['capture']={'receipt':str(capture),'image':str(image),'sha256':hashlib.sha256(pixels).hexdigest()}
 try:
  if mode=='start':assert LIB.set_material_instance_texture_parameter_value(child,PARAM,white)
  else:child.set_editor_property('texture_parameter_values',native_rows(r['original_overrides']))
  LIB.update_material_instance(child);assert path(LIB.get_material_instance_texture_parameter_value(child,PARAM))==(WHITE if mode=='start' else r['original']['path'])
  if mode=='start':assert [v for v in overrides() if (v['name'],v['association'],v['index'])!=(PARAM,0,-1)]==[v for v in snapshot if (v['name'],v['association'],v['index'])!=(PARAM,0,-1)]
  assert LIB.get_material_instance_scalar_parameter_value(child,'GeoCity_GrassCoverage')==grass and {k:str(child.get_editor_property(k)) for k in other}==other
  assert transforms()==baseline['actor_transforms'] and all(a.get_editor_property('landscape_material')==child for a in landscapes);after=dirty();assert set(after['content'])<=allowed and set(after['maps'])<={named_map}
  assert set(after['maps'])==set(before_dirty['maps']) and set(after['content'])==set(before_dirty['content'])|{child.get_outermost().get_path_name()}
  if mode=='restore':assert overrides()==r['original_overrides']
  r.update(status='white_override_active' if mode=='start' else 'original_override_state_restored',after=texture(LIB.get_material_instance_texture_parameter_value(child,PARAM)),dirty_after=after,explicit_save_called=False);RESULT=r
 except Exception as error:
  r.update(status='failed_requires_root_review',error=repr(error),dirty_after=dirty());out.write_text(json.dumps(r,indent=2),encoding='utf-8');raise
 out.write_text(json.dumps(r,indent=2),encoding='utf-8')

