from pathlib import Path
from datetime import datetime,timezone
import unreal,json,os,sys,hashlib,subprocess
import geocity_runtime_guard,geocity_editor_action,geocity_roadbld_workflow
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
auth=read(HERE/'RUN_AUTHORIZATION.json')
assert auth['status']=='STARTUP_AUTHORIZED' and auth['ordinary_generation_authorized']
launch=read(ROOT/'Staging/SystemCompletion_2026-10-04/LAUNCH_STATE.json')
assert os.getpid()==launch['pid']
ids=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command','ConvertTo-Json -Compress -InputObject @((Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue).Id)'],creationflags=subprocess.CREATE_NO_WINDOW,text=True))
assert ids==[os.getpid()]
assert len(geocity_runtime_guard.verify())==12
assert sha(ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json')==auth['manifest_sha256']
assert sha(Path(auth['profile']))==auth['profile_sha256']
assert sha(ROOT/'Content'/(auth['map'][6:]+'.umap'))==auth['map_sha256']
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name()==auth['map']
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
assert not any(getattr(r,k,None) is not None for n in ('geocity_bank_workflow','geocity_roadbld_workflow') for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle'))
api=unreal.HoudiniPublicAPIBlueprintLib.get_api();assert api.is_asset_cooking_paused()
actors={a.get_path_name():a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
hd=[a for a in actors.values() if a.get_class().get_name()=='HoudiniAssetActor'];assert len(hd)==1
wrapper=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,hd[0])
assert not wrapper.is_auto_cooking_enabled() and not wrapper.is_auto_bake_enabled()
assert not unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable')
authority=geocity_roadbld_workflow.inspect_geographic_landscape_authority();assert authority['passed']
assert unreal.get_editor_subsystem(unreal.WorldBLDAuthSubsystem).has_license_for_tool('RoadBLD'),'RoadBLD sign-in required'
ledger=read(Path(auth['profile']).parent/'ROADBLD_WORKFLOW_STATE.json')
paths=ledger['staged_actor_paths'];required={'GeoCity_RoadBLD','GeoCityArea_GazaShujaiya','GeoCityRevision_'+ledger['revision']}
assert len(paths)==132 and all(p in actors and required.issubset({str(t) for t in actors[p].tags}) for p in paths)
profile=read(Path(auth['profile']));assert 'source_family_registry_ref' not in profile['building_assembly_contract']
lease=ROOT/'Staging/ModelBank/EDITOR_OWNER.txt'
fields=geocity_editor_action.lease_fields(lease.read_text().splitlines()[-1])
assert fields['OWNER']=='CODEX_MANAGED_SYSTEMS_STARTUP' and fields['assigned_editor_PID']==str(os.getpid())
assert fields['operator_thread_id']==auth['operator_thread_id']
state={'pid':os.getpid(),'world':auth['map'],'dirty_content':[],'dirty_maps':[],'sealed_modules':12,
       'landscape_authority':authority,'saved_failed_roads_accounted':132,'actor_count':len(actors),
       'landscape_paths':[p for p,a in actors.items() if a.get_class().get_name()=='Landscape'],
       'ordinary_configuration_unchanged':True,'new_modular_families_connected':False,'passed':True}
write(HERE/'STARTUP.json',state)
utc=datetime.now(timezone.utc).isoformat()
with lease.open('a',encoding='utf-8') as f:
    f.write('\n'+utc+' OWNER=CODEX_MANAGED_SYSTEMS_TASK4 manager_thread_id='+auth['manager_thread_id']+' operator_thread_id='+auth['operator_thread_id']+' assigned_editor_PID='+str(os.getpid())+' map='+auth['map']+' activation=MANAGER_ACTIVATED scope=existing_configuration_GazaShujaiya_run_only ordinary_generation_authorized=true\n')
assert geocity_editor_action.managed_operation_lease(ROOT,lease.read_text().splitlines()[-1],auth['map'])
auth.update(status='GENERATION_STARTED',pid=os.getpid(),started_utc=utc)
write(HERE/'RUN_AUTHORIZATION.json',auth)
result=geocity_editor_action.generate_current_area()
write(HERE/'DISPATCH.json',{'pid':os.getpid(),'utc':utc,'live_run_returned':result is not None,'result_type':str(type(result))})
print(json.dumps({'dispatched':result is not None,'pid':os.getpid()}))
