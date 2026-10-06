"""Prepared for manager-activated task4 ONLY, after fresh reviewed reseal/startup.

Task1 has not run this. No cook, Bake, map/content save, removal or reload.
"""
def inspect():
    import datetime
    import json
    import os
    import sys
    from pathlib import Path
    import unreal
    import geocity_runtime_guard
    import geocity_bank_workflow
    import geocity_editor_action

    project=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    sources=geocity_runtime_guard.verify()
    handoff=json.loads((Path(__file__).parent/'SOURCE_HANDOFF.json').read_text())
    assert sources['geocity_bank_workflow']['sha256']==handoff['source_sha256'],'Requires newly sealed fresh source'
    lease=(project/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
    fields=geocity_editor_action.lease_fields(lease)
    assert fields.get('assigned_editor_PID')==str(os.getpid())
    assert fields.get('OWNER')=='CODEX_MANAGED_SYSTEMS_STARTUP' and fields.get('activation')=='AWAITING_MANAGER_ACTUAL_PID'
    assignment=json.loads((project/'Staging/ManagedSystemsAstra_2026-10-04/ASSIGNMENTS.json').read_text())
    task4=next(row for row in assignment['tasks'] if row['id']=='task4')
    assert fields.get('manager_thread_id')==assignment['manager_thread_id'] and fields.get('operator_thread_id')==task4['thread_id']
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    named_map=world.get_outermost().get_path_name()
    assert named_map==fields['map'] and named_map in assignment['native_area_maps']
    profiles=[path for path in geocity_editor_action.persistent_profiles(project) if json.loads(path.read_text())['map']==named_map]
    assert len(profiles)==1
    profile=json.loads(profiles[0].read_text())
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    hd=[a for a in actors if a.get_class().get_name()=='HoudiniAssetActor']
    assert len(hd)==1
    wrapper=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,hd[0])
    api=unreal.HoudiniPublicAPIBlueprintLib.get_api()
    def snapshot():
        return {'pid':os.getpid(),'map':named_map,'cooking_paused':api.is_asset_cooking_paused(),
            'auto_cook':wrapper.is_auto_cooking_enabled(),'auto_bake':wrapper.is_auto_bake_enabled(),
            'session_valid':api.is_session_valid(),
            'dirty_maps':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
            'dirty_content':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],
            'active_callback_handles':{name:sum(getattr(run,key,None) is not None for run in getattr(sys.modules.get(name),'ACTIVE',[]) for key in ('watch_tick','save_tick','tick_handle','_pending_correction'))
                for name in ('geocity_bank_workflow','geocity_roadbld_workflow')},
            'actors':sorted(a.get_path_name() for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())}
    before=snapshot()
    assert before['cooking_paused'] and not before['auto_cook'] and not before['auto_bake']
    assert not before['dirty_maps'] and not before['dirty_content']
    assert not any(before['active_callback_handles'].values())
    # Deliberately avoid constructor/start/account methods that write workflow
    # history or its build-state alias. Call only the exact fresh helper.
    run=geocity_bank_workflow.GeoCityRun.__new__(geocity_bank_workflow.GeoCityRun)
    run.project=project;run.p=profile;run.api=api;run.state={}
    run.state_path=project/'Staging/ManagedSystemsAstra_2026-10-04/Task4_Integration/LANDSCAPE_CONSUMER_CONFIRMATION.json'
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'lease':lease,'before':before,
            'source_sha256':sources['geocity_bank_workflow']['sha256'],'generation_started':False,'content_save_performed':False}
    try:
        resolved=run.official_landscapes(wrapper)
        prior=json.loads(Path(profile['workflow_receipt']).with_name('LAST_SUCCESSFUL_WORKFLOW_STATE.json').read_text())
        assert Path(prior['profile']).resolve()==profiles[0].resolve()
        landscapes={a.get_path_name() for a in actors if isinstance(a,unreal.Landscape)}
        known=set(prior['baked_actor_paths'])|set(resolved)
        result.update(resolved_official_landscapes=sorted(resolved),unaccounted_landscapes=sorted(landscapes-known),
                      official_identity_reads=run.state['official_landscape_identity_reads'])
        assert not landscapes-known,'Unaccounted saved Landscape'
        result['passed']=True
    except Exception as exc:
        result.update(passed=False,error=repr(exc),official_identity_reads=run.state.get('official_landscape_identity_reads',[]))
    finally:
        result['after']=snapshot()
        result['state_unchanged']=result['after']==before
        result['passed']=bool(result.get('passed') and result['state_unchanged'])
        run.state_path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    print(inspect())
