"""Bounded texture-loading diagnostic; no package, geometry or CVar edits."""
import datetime,json,os,sys,time
from pathlib import Path
import unreal
import geocity_runtime_guard
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
HERE=ROOT/'Staging/GroundPainting_2026-10-04'
assert os.getpid()==int(ARGS['expected_pid'])
lease=[x for x in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1]
assert f'assigned_editor_PID={os.getpid()} ' in lease and 'OWNER=CODEX_GROUND_PAINTING' in lease
assignment=json.loads((HERE/'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
fields=dict(t.split('=',1) for t in lease.split() if '=' in t)
assert fields['operator_thread_id']==assignment['execution_thread_id'] and fields['map']==ARGS['world']
geocity_runtime_guard.verify()
api=unreal.HoudiniPublicAPIBlueprintLib.get_api()
assert api.is_asset_cooking_paused()
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name()==ARGS['world']
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
hd=[a for a in actors if a.get_class().get_name()=='HoudiniAssetActor'];assert len(hd)==1
wrappers=[unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,a) for a in hd]
assert all(not w.is_auto_cooking_enabled() and not w.is_auto_bake_enabled() for w in wrappers)
assert not unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable')
assert not any(sum(getattr(r,k,None) is not None for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle','_pending_correction')) for n in ('geocity_bank_workflow','geocity_roadbld_workflow'))
def dirty():
 return {'maps':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
         'content':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
def prop(o,k):
 try:return str(o.get_editor_property(k))
 except Exception:return None
def camera(level,key):
 p,r=level.get_level_viewport_camera_info(key)
 return {'eye':[float(p.x),float(p.y),float(p.z)],'rotation':[float(r.pitch),float(r.yaw),float(r.roll)]}
def snapshot():
 master=unreal.load_asset('/Game/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural')
 textures={}
 for node in unreal.MaterialEditingLibrary.get_material_expressions(master):
  try:t=node.get_editor_property('texture')
  except Exception:continue
  if t:textures[t.get_path_name()]={'persistent':{k:prop(t,k) for k in ('lod_bias','lod_group','max_texture_size','never_stream','global_force_mip_levels_to_be_resident','num_cinematic_mip_levels','virtual_texture_streaming')},'transient_deadline':prop(t,'force_mip_levels_to_be_resident_timestamp')}
 cvars={k:unreal.SystemLibrary.get_console_variable_string_value(k) for k in ('r.TextureStreaming','r.Streaming.PoolSize','r.Streaming.MipBias','r.Streaming.UsePerTextureBias','r.Streaming.Boost','r.Streaming.MaxEffectiveScreenSize','r.Streaming.HiddenPrimitiveScale','r.Streaming.FullyLoadUsedTextures','r.Streaming.UseAllMips','r.ScreenPercentage','sg.TextureQuality')}
 return {'dirty':dirty(),'textures':textures,'cvars':cvars,'cooking_paused':api.is_asset_cooking_paused()}
mode=ARGS['mode'];assert mode in ('inspect','finish_loading','investigate','viewport_realtime','targeted_residency')
out=HERE/'Revision_2026-10-05'/f'STREAMING_{ARGS["label"]}_PID{os.getpid()}.json'
assert not out.exists(),'Preserve previous diagnostic receipt'
before=snapshot();assert not before['dirty']['maps'] and not before['dirty']['content']
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'world':world.get_outermost().get_path_name(),'mode':mode,'before':before,'finish_api_available':hasattr(unreal.AutomationLibrary,'finish_loading_before_screenshot'),'status':'STARTED'}
out.write_text(json.dumps(result,indent=2),encoding='utf-8')
started=time.monotonic()
try:
 if mode=='finish_loading':
  assert result['finish_api_available']
  unreal.AutomationLibrary.finish_loading_before_screenshot()
 elif mode=='investigate':
  result['readonly_commands']=['DumpTextureStreamingStats']+['InvestigateTexture '+n for n in ('T_Sand_01_Albedo','T_Sand_01_Normal_GeoCity','T_Sand_01_Mask_GeoCity','T_Dirt_Path_01_Albedo')]
  for command in result['readonly_commands']:unreal.SystemLibrary.execute_console_command(world,command)
 elif mode=='viewport_realtime':
  level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);key=level.get_active_viewport_config_key()
  result['active_key']=str(key);result['camera_before']=camera(level,key)
  result['prior_realtime']='UNKNOWN_NO_REFLECTED_GETTER';result['requested_realtime']=True
  level.editor_set_viewport_realtime(True,key)
  level.editor_invalidate_viewports()
  result['camera_after']=camera(level,key);assert result['camera_after']==result['camera_before']
 elif mode=='targeted_residency':
  area=next(k for k,v in assignment['original_maps'].items() if v==ARGS['world'])
  material=unreal.load_asset(assignment['material_contract']['area_instances'][area])
  names=[layer+'_'+channel for layer in ('Sand_01','Sand_02','Dirt_Path','Sand_Path') for channel in ('Albedo','Normal','PackedMask')]
  selected=[unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(material,n) for n in names]
  assert all(isinstance(t,unreal.Texture2D) and hasattr(t,'set_force_mip_levels_to_be_resident') for t in selected)
  assert len({t.get_path_name() for t in selected})==12
  result['diagnostic_only']=True;result['residency_seconds']=30.0
  result['selected_textures']={n:t.get_path_name() for n,t in zip(names,selected)}
  for texture in selected:texture.set_force_mip_levels_to_be_resident(30.0,0)
 result['after']=snapshot()
 assert result['after']['cooking_paused']
 assert result['after']['dirty']==before['dirty']
 assert result['after']['cvars']==before['cvars']
 assert {k:v['persistent'] for k,v in result['after']['textures'].items()}=={k:v['persistent'] for k,v in before['textures'].items()},'Unexpected persistent texture-property change'
 result['status']='COMPLETED_NO_PERSISTENT_CHANGES'
except Exception as e:
 result['status']='FAILED';result['error']=repr(e)
 raise
finally:
 result['elapsed_seconds']=time.monotonic()-started
 out.write_text(json.dumps(result,indent=2),encoding='utf-8')
RESULT={'receipt':str(out),'mode':mode,'elapsed_seconds':result['elapsed_seconds'],'finish_api_available':result['finish_api_available'],'texture_count':len(before['textures']),'persistent_properties_preserved':True}
