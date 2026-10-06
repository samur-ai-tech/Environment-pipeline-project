"""Read-only actual-PID startup inspection; writes only its bank staging receipt."""
import datetime, hashlib, json, os, subprocess, sys
from pathlib import Path
import unreal
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def editor_pids():
    return json.loads(subprocess.check_output(['powershell','-NoProfile','-NonInteractive','-Command',
        'ConvertTo-Json -Compress -InputObject @((Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue).Id)'],
        creationflags=subprocess.CREATE_NO_WINDOW,text=True))
def inspect(activation_path,activation_sha):
    assert sha(activation_path)==activation_sha
    activation=read(activation_path)
    assert activation['status']=='MODULAR_STARTUP_AUTHORIZED' and activation['startup_authorized'] is True
    assert activation['native_authorized_now'] is False and activation['ordinary_generation_authorized'] is False
    assert editor_pids()==[os.getpid()],'not_the_sole_native_editor'
    assert sha(__file__)==activation['inspector_sha256']
    assert sha(activation['request_path'])==activation['request_sha256']
    request=read(activation['request_path'])
    assert all(sha(p)==s for p,s in request['python_sources'].items())
    assert sha(activation['resumption_path'])==activation['resumption_sha256']
    import geocity_runtime_guard as guard
    import geocity_editor_action as action
    import geocity_roadbld_workflow as roads
    sources=guard.verify();assert len(sources)==12
    assert sha(ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json')==activation['manifest_sha256']
    lease=[l for l in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().splitlines() if l.strip()][-1]
    fields=action.lease_fields(lease)
    assert fields['OWNER']=='CODEX_MANAGED_SYSTEMS_STARTUP'
    assert fields['activation']=='MODULAR_STARTUP_INSPECTION_ONLY'
    assert fields['native_authorized_now']=='false' and fields['ordinary_generation_authorized']=='false'
    assert fields['assigned_editor_PID']==str(os.getpid())
    assert fields['operator_thread_id']==activation['operator_thread_id']=='01a1067c-5012-7550-b449-015b53c9d726'
    assert fields['manager_thread_id']==activation['manager_thread_id']=='01a10789-2e6a-7321-ad85-0a2964f8a937'
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
    assert world==activation['world']==fields['map']
    api=unreal.HoudiniPublicAPIBlueprintLib.get_api()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    hd=[a for a in actors if a.get_class().get_name()=='HoudiniAssetActor'];assert len(hd)==1
    wrapper=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,hd[0])
    def snapshot():return {'pid':os.getpid(),'world':world,'cooking_paused':api.is_asset_cooking_paused(),
        'auto_cook':wrapper.is_auto_cooking_enabled(),'auto_bake':wrapper.is_auto_bake_enabled(),
        'autosave':unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable'),
        'dirty_content':sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
        'dirty_maps':sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
        'callback_count':sum(getattr(run,key,None) is not None for name in ('geocity_bank_workflow','geocity_roadbld_workflow') for run in getattr(sys.modules.get(name),'ACTIVE',[]) for key in ('watch_tick','save_tick','tick_handle','_pending_correction')),
        'actor_paths':sorted(a.get_path_name() for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())}
    assert sha(activation['preservation_path'])==activation['preservation_sha256']
    protected={p:s.lower() for p,s in read(activation['preservation_path'])['files'].items()}
    before=snapshot()
    result={'schema':'environmentpipeline.modular_startup_inspection.v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'before':before,'lease':lease,'source_modules':sources,'activation_sha256':activation_sha,'passed':False}
    try:
        assert before['cooking_paused'] and not before['auto_cook'] and not before['auto_bake'] and not before['autosave']
        assert not before['dirty_content'] and not before['dirty_maps'] and before['callback_count']==0
        assert sha(activation['profile_path'])==activation['profile_sha256']
        assert sha(activation['preservation_path'])==activation['preservation_sha256']
        result['preserved_files']={p:sha(p) for p in protected}
        assert result['preserved_files']==protected
        result['landscape_authority']=roads.inspect_geographic_landscape_authority()
        assert result['landscape_authority']['passed']
        result['api_available']={name:hasattr(unreal.StaticMeshDescription,name) for name in ('get_vertex_instance_count','get_vertex_instance_vertex','get_vertex_instance_uv')}
        assert all(result['api_available'].values()),result['api_available']
        assert hasattr(unreal.TextureCompressionSettings,'TC_VECTOR_DISPLACEMENTMAP')
        result['passed']=True
    except Exception as exc:result['error']=repr(exc)
    result['after']=snapshot();result['state_unchanged']=result['before']==result['after']
    try:
        result['preserved_files_after']={p:sha(p) for p in protected}
        result['preservation_unchanged']=result['preserved_files_after']==protected
        result['authority_unchanged']=sha(activation_path)==activation_sha and sha(activation['preservation_path'])==activation['preservation_sha256'] and [l for l in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().splitlines() if l.strip()][-1]==lease
        result['sole_editor_after']=editor_pids()==[os.getpid()]
        result['request_unchanged']=sha(activation['request_path'])==activation['request_sha256']
        result['source_pins_after']={p:sha(p) for p in request['python_sources']}
        result['source_pins_unchanged']=result['source_pins_after']==request['python_sources'] and sha(ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json')==activation['manifest_sha256'] and len(guard.verify())==12
    except Exception as exc:
        result.update(preservation_unchanged=False,authority_unchanged=False,sole_editor_after=False,request_unchanged=False,source_pins_unchanged=False,postcheck_error=repr(exc))
    result['passed']=result['passed'] and result['state_unchanged'] and result['preservation_unchanged'] and result['authority_unchanged'] and result['sole_editor_after'] and result['request_unchanged'] and result['source_pins_unchanged']
    path=HERE/('STARTUP_INSPECTION_PID'+str(os.getpid())+'.json')
    path.write_text(json.dumps(result,indent=2)+'\n')
    return {'passed':result['passed'],'pid':os.getpid(),'receipt':str(path),'sha256':sha(path),'error':result.get('error')}
