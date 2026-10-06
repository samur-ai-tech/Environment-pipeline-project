"""Minimal persistent-module bootstrap. No graph or geometry evaluation.

PREPARED NOT LAUNCHED. Only an explicitly reviewed replacement process may
activate it. Every Unreal API call is preceded by an fsynced filesystem step.
The bootstrap never takes the editor lease; root must acquire the new PID.
"""
import datetime,json,os,sys,time,traceback
from pathlib import Path
ROOT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE=ROOT/'Staging/ManagedAstra_2026-10-03'
MAP='/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration'
HDA='/Game/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank.GeoCity_city_v015_PermanentBank'
STATE={'started':False,'handle':None,'api':None,'wrapper':None,'last_poll':0}
def journal(event,**values):
    row={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'event':event,**values}
    with STATE['journal'].open('a',encoding='utf-8') as f:
        f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
def call(label,fn):
    journal('BEFORE_NATIVE',operation=label)
    value=fn()
    journal('AFTER_NATIVE',operation=label)
    return value
def path(obj,label):return call(label+'.get_path_name',obj.get_path_name) if obj else None
def save_report():
    with STATE['receipt'].open('w',encoding='utf-8') as f:
        json.dump(STATE['report'],f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def stop():
    if STATE['handle'] is not None:
        handle=STATE['handle']
        call('unregister_bootstrap_tick',lambda:STATE['unreal'].unregister_slate_post_tick_callback(handle))
        STATE['handle']=None
def callbacks():
    result={}
    for name in ['geocity_bank_workflow','geocity_roadbld_workflow']:
        module=sys.modules.get(name)
        result[name]={'loaded':module is not None,'active_count':len(getattr(module,'ACTIVE',[])),
            'callback_count':sum(int(getattr(x,k,None) is not None) for x in getattr(module,'ACTIVE',[]) for k in ['watch_tick','save_tick','tick_handle'])}
    return result
def inspect_tick(delta):
    if time.monotonic()-STATE['last_poll']<1:return
    STATE['last_poll']=time.monotonic()
    try:
        assert time.monotonic()-STATE['began']<180,'Startup named world did not become ready'
        u=STATE['unreal'];report=STATE['report']
        subsystem=call('get_UnrealEditorSubsystem',lambda:u.get_editor_subsystem(u.UnrealEditorSubsystem))
        world=call('get_editor_world',subsystem.get_editor_world)
        if world is None:return
        outer=call('world.get_outermost',world.get_outermost)
        worldpackage=path(outer,'world_package')
        if worldpackage in ['/Temp/Untitled','/Engine/Maps/Entry'] or worldpackage.startswith('/Temp/Untitled'):return
        assert worldpackage==MAP,'Unexpected world: '+str(worldpackage)
        report['world']=path(world,'world');report['map']=worldpackage
        maps=call('get_dirty_map_packages_before',u.EditorLoadingAndSavingUtils.get_dirty_map_packages)
        content=call('get_dirty_content_packages_before',u.EditorLoadingAndSavingUtils.get_dirty_content_packages)
        report['dirty_before']={'maps':[path(x,'dirty_map_before') for x in maps],'content':[path(x,'dirty_content_before') for x in content]}
        hd=call('get_HoudiniAssetActor_in_named_world',lambda:u.GameplayStatics.get_all_actors_of_class(world,u.HoudiniAssetActor))
        assert len(hd)==1,'Expected exactly one saved named-world HDA; no actor creation or repair'
        actor=hd[0];report['hda_actor']=path(actor,'named_hda_actor')
        wrapper=call('create_read_wrapper_for_existing_hda',lambda:u.HoudiniPublicAPIAssetWrapper.create_wrapper(None,actor));assert wrapper
        STATE['wrapper']=wrapper
        info=call('get_houdini_asset_info',wrapper.get_houdini_asset_info)
        asset=call('read_info_houdini_asset',lambda:info.get_editor_property('houdini_asset'))
        report['hda_asset']=path(asset,'hda_asset');assert report['hda_asset']==HDA
        report['hda_auto_cooking_before']=call('is_auto_cooking_enabled_before',wrapper.is_auto_cooking_enabled)
        if report['hda_auto_cooking_before']:
            call('disable_named_hda_auto_cooking',lambda:wrapper.set_auto_cooking_enabled(False))
        report['hda_auto_cooking_after']=call('is_auto_cooking_enabled_after',wrapper.is_auto_cooking_enabled)
        assert not report['hda_auto_cooking_after']
        report['hda_auto_bake_enabled']=call('is_auto_bake_enabled_read_only',wrapper.is_auto_bake_enabled)
        assert not report['hda_auto_bake_enabled'],'Named HDA auto-bake unexpectedly enabled; Engine remains paused, report to root'
        landscapes=call('get_named_world_Landscapes',lambda:u.GameplayStatics.get_all_actors_of_class(world,u.Landscape))
        report['live_landscapes']=[path(x,'saved_landscape') for x in landscapes]
        if hasattr(u,'DynamicRoadNetwork'):
            networks=call('get_named_world_DynamicRoadNetworks',lambda:u.GameplayStatics.get_all_actors_of_class(world,u.DynamicRoadNetwork))
            report['live_native_networks']=[path(x,'saved_network') for x in networks]
        settings=call('read_autosave_settings_object',lambda:u.load_object(None,'/Script/UnrealEd.Default__EditorLoadingSavingSettings'))
        observed=call('read_autosave_flag_at_world_ready',lambda:settings.get_editor_property('bAutoSaveEnable'))
        report['autosave_at_world_ready_before_safety_check']=observed
        if observed:
            call('disable_autosave_at_world_ready_without_config_save',lambda:settings.set_editor_property('bAutoSaveEnable',False,notify_mode=u.PropertyAccessChangeNotifyMode.NEVER))
        report['autosave_runtime']=call('verify_autosave_false_at_world_ready',lambda:settings.get_editor_property('bAutoSaveEnable'))
        assert not report['autosave_runtime']
        report['startup_autosave_protection']='EditorPerProjectUserSettings scalar command-line override bAutoSaveEnable=False plus runtime check; NoAutoSave is supplementary only'
        report['Engine_paused']=call('Engine_is_asset_cooking_paused',STATE['api'].is_asset_cooking_paused)
        report['Engine_session_valid']=call('Engine_is_session_valid',STATE['api'].is_session_valid)
        assert report['Engine_paused']
        report['workflow_modules']=callbacks();assert all(v['callback_count']==0 and v['active_count']==0 for v in report['workflow_modules'].values())
        report['service_readiness']={'official_API_available':True,'official_session_valid':report['Engine_session_valid'],
            'RoadBLD_classes_exposed':hasattr(u,'DynamicRoadNetwork'),'Copilot_modules_loaded':any(k.startswith('unreal_copilot') for k in sys.modules),
            'MCP_transport_not_probed':True,'RoadBLD_signin_license_not_checked_or_changed':True}
        maps=call('get_dirty_map_packages_after',u.EditorLoadingAndSavingUtils.get_dirty_map_packages)
        content=call('get_dirty_content_packages_after',u.EditorLoadingAndSavingUtils.get_dirty_content_packages)
        report['dirty_after']={'maps':[path(x,'dirty_map_after') for x in maps],'content':[path(x,'dirty_content_after') for x in content]}
        stop();report['bootstrap_callbacks']=0;report['status']='READY_FOR_MANAGER_NEW_PID_LEASE'
        report['elapsed_seconds']=time.monotonic()-STATE['began'];save_report();journal('BOOTSTRAP_COMPLETE')
    except Exception:
        STATE['report'].update(status='BOOTSTRAP_STOPPED',error=traceback.format_exc())
        stop();save_report();journal('BOOTSTRAP_STOPPED',error=STATE['report']['error'])
def start():
    assert os.environ.get('GEOCITY_RECOVERY_STARTUP_TOKEN')=='ROOT_ACTIVATED_REPLACEMENT_EDITOR_STARTUP'
    assert not STATE['started'];STATE['started']=True;STATE['began']=time.monotonic()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    STATE['journal']=HERE/('RECOVERY_STARTUP_'+stamp+'.jsonl');STATE['receipt']=HERE/('RECOVERY_STARTUP_'+stamp+'.json')
    STATE['report']={'status':'STARTING','pid':os.getpid(),'expected_map':MAP,'old_pid':32752,'lease_acquired':False,
      'new_operation_required':True,'old_p_r_not_reconstructed':True,'journal':str(STATE['journal']),
      'no_Cook_rebuild_generation_save_asset_profile_edit_recovery_pack_or_autosave_restore':True,
      'autosave_original_user_policy':True,'autosave_restoration_policy':'Keep runtime disabled through manager-owned recovery/generation; root restores originalTrue only after named completion/reopen/clean checks. No config save frombootstrap.',
      'recovery_policy':'Prelaunch RestoreEnabled=False manifest; original flag andallfourautosavefiles preserved. No package import/delete/automatic flag restoration.'}
    save_report();journal('BEFORE_IMPORT_UNREAL')
    try:
        import unreal
        STATE['unreal']=unreal;journal('AFTER_IMPORT_UNREAL')
        assert os.getpid()!=32752,'This bootstrap is only for a replacement process'
        settings=call('get_autosave_settings_early',lambda:unreal.load_object(None,'/Script/UnrealEd.Default__EditorLoadingSavingSettings'))
        STATE['report']['autosave_runtime_observed_on_bootstrap_entry']=call('read_autosave_early',lambda:settings.get_editor_property('bAutoSaveEnable'))
        if STATE['report']['autosave_runtime_observed_on_bootstrap_entry']:
            call('disable_autosave_early_without_config_save',lambda:settings.set_editor_property('bAutoSaveEnable',False,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER))
        assert not call('verify_autosave_early_disabled',lambda:settings.get_editor_property('bAutoSaveEnable'))
        runtime=call('get_HoudiniRuntimeSettings_CDO',lambda:unreal.load_object(None,'/Script/HoudiniEngineRuntime.Default__HoudiniRuntimeSettings'))
        STATE['report']['Houdini_bPauseCookingOnStart']=call('read_bPauseCookingOnStart',lambda:runtime.get_editor_property('bPauseCookingOnStart'))
        assert STATE['report']['Houdini_bPauseCookingOnStart']
        api=call('get_official_Houdini_API',unreal.HoudiniPublicAPIBlueprintLib.get_api);assert api
        STATE['api']=api
        paused=call('Engine_is_paused_before',api.is_asset_cooking_paused)
        STATE['report']['Engine_paused_before']=paused
        if not paused:call('pause_official_Houdini_Engine',api.pause_asset_cooking)
        assert call('verify_Engine_paused_early',api.is_asset_cooking_paused)
        assert paused,'Plugin was not already paused on startup; safety-paused now, root must inspect before proceeding'
        STATE['handle']=call('register_minimal_startup_tick',lambda:unreal.register_slate_post_tick_callback(inspect_tick))
        STATE['report']['status']='WAITING_FOR_ORIGINAL_NAMED_WORLD';save_report()
    except Exception:
        STATE['report'].update(status='BOOTSTRAP_STOPPED',error=traceback.format_exc());save_report();journal('BOOTSTRAP_STOPPED',error=STATE['report']['error'])
