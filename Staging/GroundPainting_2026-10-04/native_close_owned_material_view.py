"""Close only the exact material editor opened by this ground task; never save."""
import datetime,json,os,sys
from pathlib import Path
import unreal,geocity_runtime_guard
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
HERE=ROOT/'Staging/GroundPainting_2026-10-04'
REV=HERE/'Revision_2026-10-05'
assert os.getpid()==int(ARGS['expected_pid'])
assignment=json.loads((HERE/'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
lease=[x for x in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1]
fields=dict(t.split('=',1) for t in lease.split() if '=' in t)
assert fields['OWNER']=='CODEX_GROUND_PAINTING' and fields['assigned_editor_PID']==str(os.getpid())
assert fields['operator_thread_id']==assignment['execution_thread_id'] and fields['map']==ARGS['world']
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name()==ARGS['world']
sources=geocity_runtime_guard.verify()
api=unreal.HoudiniPublicAPIBlueprintLib.get_api();assert api.is_asset_cooking_paused()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
hd=[a for a in actors if a.get_class().get_name()=='HoudiniAssetActor'];assert len(hd)==1
w=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,hd[0])
assert not w.is_auto_cooking_enabled() and not w.is_auto_bake_enabled()
assert not unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable')
assert not any(sum(getattr(r,k,None) is not None for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle','_pending_correction')) for n in ('geocity_bank_workflow','geocity_roadbld_workflow'))
def dirty():
 return {'maps':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()], 'content':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
before=dirty();assert not before['maps'] and not before['content']
area=next(k for k,v in assignment['original_maps'].items() if v==ARGS['world'])
target=assignment['material_contract']['area_instances'][area]
opened=json.loads((REV/f'OPEN_MATERIAL_VIEW_PID{os.getpid()}.json').read_text(encoding='utf-8-sig'))
open_request=json.loads((HERE/'tool_query_args.json').read_text(encoding='utf-8-sig'))
assert open_request['arguments']['tool_name']=='OpenEditorForAsset' and open_request['arguments']['arguments']['assetPath']==target
assert 'returnValue' in json.dumps(opened) and not opened['result'].get('isError'), 'Successful exact asset-open receipt required'
material=unreal.load_asset(target);assert material
sub=unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
assert hasattr(sub,'close_all_editors_for_asset')
closed=sub.close_all_editors_for_asset(material)
after=dirty();assert after==before and api.is_asset_cooking_paused()
out=REV/f'CLOSE_OWNED_MATERIAL_VIEW_PID{os.getpid()}.json';assert not out.exists()
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'world':ARGS['world'],'asset':target,'closed_count':closed,'dirty_before':before,'dirty_after':after,'saved':False,'sources':sources}
out.write_text(json.dumps(result,indent=2),encoding='utf-8')
RESULT={'receipt':str(out),'closed_count':closed,'dirty':after,'saved':False}
