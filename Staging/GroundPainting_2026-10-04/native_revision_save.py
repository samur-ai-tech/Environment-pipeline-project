"""Compile/readback or named save only of the reviewed ground dependency set."""
import datetime,json,os,struct,sys
from pathlib import Path
import unreal,geocity_runtime_guard
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve();HERE=ROOT/'Staging/GroundPainting_2026-10-04';REV=HERE/'Revision_2026-10-05';LIB=unreal.MaterialEditingLibrary
a=json.loads((HERE/'ASSIGNMENT.json').read_text());world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();named_map=world.get_outermost().get_path_name();area=next(k for k,v in a['original_maps'].items() if v==named_map)
fields=dict(t.split('=',1) for t in [s for s in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1].split() if '=' in t)
assert fields['OWNER']=='CODEX_GROUND_PAINTING' and fields['activation']=='GROUND_AUTHORING' and fields['assigned_editor_PID']==str(os.getpid()) and fields['map']==named_map and fields['operator_thread_id']==a['execution_thread_id']
geocity_runtime_guard.verify();assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert not any(getattr(r,k,None) is not None for n in ('geocity_bank_workflow','geocity_roadbld_workflow') for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle','_pending_correction'))
assert not unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable')
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 if isinstance(actor,unreal.HoudiniAssetActor):
  wrapper=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,actor);assert not wrapper.is_auto_cooking_enabled() and not wrapper.is_auto_bake_enabled()
master=unreal.load_asset(a['material_contract']['master']);child=unreal.load_asset(a['material_contract']['area_instances'][area]);shared='/Game/Project/Shared/SurfacePainting/Appearance_20261003'
paths=[a['material_contract']['master'].split('.')[0]]+[shared+'/Textures/T_'+n+'_Mask_GeoCity' for n in ('Sand_01','Sand_02','Dirt_Path_01','Sand_Path_01')]+[a['material_contract']['area_instances'][area].split('.')[0]]
out=REV/f'{ARGS["action"].upper()}_{area}_{ARGS["stage"]}_PID{os.getpid()}.json';assert not out.exists(), 'Preserve prior operation receipt'
def path(o):return o.get_path_name() if o else None
def dirty():return {'content':[path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],'maps':[path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]}
before=dirty();assert set(before['content'])<=set(paths) and set(before['maps'])<={named_map}
assert all(x.get_editor_property('landscape_material')==child for x in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(x,unreal.LandscapeProxy))
for p in paths:
 assert unreal.load_asset(p) is not None,p
if ARGS['action']=='compile':
 LIB.recompile_material(master);LIB.update_material_instance(child)
 result={'action':'compile_requested','pid':os.getpid(),'area':area,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before':before,'after':dirty(),'stats_api':[n for n in dir(LIB) if 'stat' in n.lower() or 'compil' in n.lower()],'visual_validation_pending':True}
elif ARGS['action']=='save':
 assert ARGS.get('reviewed_visual_stage') and ARGS.get('graph_review_receipt') and ARGS.get('visual_review_receipt'), 'Save requires concrete graph and actual visual review receipts'
 review_path=Path(ARGS['graph_review_receipt']).resolve();assert REV in review_path.parents and review_path.is_file()
 receipt=json.loads(review_path.read_text());assert receipt['pid']==os.getpid() and receipt.get('graph_preserved') is True and receipt['area']==area and receipt['world']==named_map and receipt['master']==master.get_path_name()
 visual_path=Path(ARGS['visual_review_receipt']).resolve();assert REV in visual_path.parents and visual_path.is_file()
 visual=json.loads(visual_path.read_text());assert visual['pid']==os.getpid() and visual['area']==area and visual['world']==named_map and visual['stage']==ARGS['reviewed_visual_stage'] and visual['save_approved_within_scope'] is True
 assert len(visual['images'])==3
 for shot in ('close','middle','wide'):
  image_path=(HERE/'Images'/f'{area}_{visual["stage"]}_{shot}.png').resolve();assert str(image_path) in visual['images'] and image_path.is_file()
  capture=json.loads((HERE/f'CAPTURE_{area}_{visual["stage"]}_{shot}.json').read_text());assert capture['pid']==os.getpid() and capture['area']==area and Path(capture['path']).resolve()==image_path
  assert capture.get('viewmode_readback')=='<ViewModeIndex.VMI_LIT: 3>' and capture.get('active_viewport_key'), 'Named save requires measured Lit evidence'
  header=image_path.read_bytes()[:24];assert header[:8]==b'\x89PNG\r\n\x1a\n';width,height=struct.unpack('>II',header[16:24]);assert width>=1280 and height>=720
 packages=[unreal.load_asset(p).get_outermost() for p in paths if p in before['content']]
 if named_map in before['maps']:packages.append(world.get_outermost())
 assert packages,'No dirty reviewed ground packages'
 assert unreal.EditorLoadingAndSavingUtils.save_packages(packages,False)
 result={'action':'named_save','pid':os.getpid(),'area':area,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before':before,'after':dirty(),'named_packages':[path(p) for p in packages],'ordinary_generation_run':False,'visual_review_stage':ARGS['reviewed_visual_stage']}
 assert not result['after']['content'] and not result['after']['maps']
else:raise AssertionError('Unknown action')
assert set(result['after']['content'])<=set(paths) and set(result['after']['maps'])<={named_map}
out.write_text(json.dumps(result,indent=2),encoding='utf-8');RESULT=result
