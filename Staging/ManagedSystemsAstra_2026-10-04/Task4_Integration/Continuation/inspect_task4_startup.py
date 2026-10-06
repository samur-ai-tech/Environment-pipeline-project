"""Prepared native READ-ONLY startup inspection. Do not run before manager activation.

Only staging receipts/official-object text exports are written. No source reload,
workflow start, session start, cooking, Bake, Content/map saves or actor deletion.
"""
import datetime
import json
import os
import runpy
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent

def inspect():
    # Local helper has no Unreal imports or execution when loaded this way.
    helpers=runpy.run_path(str(HERE/'continuation_manifest.py'))
    read,sha=helpers['read'],helpers['sha'];root=helpers['ROOT']
    approval=read(HERE/'STARTUP_ACTIVATION.json')
    assert approval['startup_inspection_authorized'] is True
    assert approval['ordinary_generation_authorized'] is False
    assert approval['manager_thread_id']==helpers['MANAGER']
    assert approval['operator_thread_id']==helpers['OPERATOR']
    assert approval['continuation_manifest_sha256']==sha(HERE/'CONTINUATION_MANIFEST.json')
    bound=helpers['verify']()
    assert approval['native_table_selection_sha256']==bound['native_table_selection_sha256']
    process_pids_before=helpers['editor_pids']()
    helpers['require_sole_editor'](process_pids_before,os.getpid())
    _,ownership=helpers['checked_receipt'](approval['landscape_ownership_receipt'],approval['landscape_ownership_sha256'])
    _,release=helpers['checked_receipt'](approval['bank_clean_handoff_receipt'],approval['bank_clean_handoff_sha256'])
    # Require normal startup to have loaded every runtime module already.
    names=read(helpers['SEAL'])['modules']
    assert all(name in sys.modules for name in names), 'Missing sealed startup module'
    guard=sys.modules['geocity_runtime_guard'];workflow=sys.modules['geocity_bank_workflow']
    action=sys.modules['geocity_editor_action'];roads=sys.modules['geocity_roadbld_workflow']
    sources=guard.verify();assert len(sources)==12
    lease=(root/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').strip().splitlines()[-1]
    fields=action.lease_fields(lease)
    assert fields['OWNER']=='CODEX_MANAGED_SYSTEMS_STARTUP'
    assert fields['activation']=='AWAITING_MANAGER_ACTUAL_PID' and fields['task']=='task4'
    assert fields['assigned_editor_PID']==str(os.getpid())
    assert fields['manager_thread_id']==approval['manager_thread_id']
    assert fields['operator_thread_id']==approval['operator_thread_id']
    # The startup lease must immediately follow the exact reviewed release.
    lease_lines=(root/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').strip().splitlines()
    lease_lines=[line for line in lease_lines if line.strip()]
    assert len(lease_lines)>=2 and lease_lines[-1]==lease
    helpers['validate_release_data'](release,approval,bound,lease_lines[-2])
    import unreal
    assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()==root
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    named_map=world.get_outermost().get_path_name()
    assert named_map==fields['map']==approval['map']
    area=next(a for a in bound['areas'] if a['map']==named_map);profile=read(area['profile'])
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    hdas=[a for a in actors.get_all_level_actors() if a.get_class().get_name()=='HoudiniAssetActor']
    assert len(hdas)==1
    wrapper=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,hdas[0])
    api=unreal.HoudiniPublicAPIBlueprintLib.get_api()
    def snapshot():
        live_world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        return {'pid':os.getpid(),'map':live_world.get_outermost().get_path_name(),'cooking_paused':api.is_asset_cooking_paused(),
            'auto_cook':wrapper.is_auto_cooking_enabled(),'auto_bake':wrapper.is_auto_bake_enabled(),
            'session_valid':api.is_session_valid(),
            'autosave':unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable'),
            'dirty_maps':sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
            'dirty_content':sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
            'active_callback_handles':{name:sum(getattr(run,key,None) is not None for run in getattr(sys.modules[name],'ACTIVE',[])
                for key in ('watch_tick','save_tick','tick_handle','_pending_correction')) for name in ('geocity_bank_workflow','geocity_roadbld_workflow')},
            'actors':sorted(a.get_path_name() for a in actors.get_all_level_actors())}
    before=snapshot()
    assert before['map']==named_map
    result={'schema':'environmentpipeline.task4.successor_startup.v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'lease':lease,'before':before,'sources':sources,'manifest_sha256':bound['manifest_sha256'],
        'os_editor_pids_before':process_pids_before,'landscape_ownership_sha256':approval['landscape_ownership_sha256'],
        'bank_clean_handoff_sha256':approval['bank_clean_handoff_sha256'],
        'continuation_manifest_sha256':sha(HERE/'CONTINUATION_MANIFEST.json'),'generation_started':False,'content_saved':False}
    try:
        assert before['cooking_paused'] and not before['auto_cook'] and not before['auto_bake'] and not before['autosave']
        assert not before['dirty_maps'] and not before['dirty_content']
        assert not any(before['active_callback_handles'].values())
        result['road_landscape_authority']=roads.inspect_geographic_landscape_authority()
        assert result['road_landscape_authority']['passed']
        result['roadbld_licensed']=unreal.get_editor_subsystem(unreal.WorldBLDAuthSubsystem).has_license_for_tool('RoadBLD')
        assert result['roadbld_licensed'], 'RoadBLD licensed session required'
        table=unreal.load_asset(profile['table']);assert table is not None
        rows=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
        result['native_catalog_digest']=helpers['digest'](rows);result['native_catalog_rows']=len(rows)
        assert result['native_catalog_digest']==area['catalog_sha256']==bound['catalog']['typed_source_digest']
        assert len(rows)==profile['row_count']==bound['catalog']['rows']
        run=workflow.GeoCityRun.__new__(workflow.GeoCityRun)
        run.project=root;run.p=profile;run.api=api;run.state={}
        run.state_path=HERE/('STARTUP_INSPECTION_PID'+str(os.getpid())+'.json')
        resolved=run.official_landscapes(wrapper)
        prior=read(area['last_success_receipt'])
        landscapes={a.get_path_name() for a in actors.get_all_level_actors() if isinstance(a,unreal.Landscape)}
        known=set(prior['baked_actor_paths'])|set(resolved)
        result.update(all_landscapes=sorted(landscapes),resolved_official_landscapes=sorted(resolved),
            unaccounted_landscapes=sorted(landscapes-known),official_identity_reads=run.state.get('official_landscape_identity_reads',[]))
        helpers['validate_landscapes'](ownership,area,landscapes,resolved,prior['baked_actor_paths'],hdas[0].get_path_name())
        # Two accounted saved Landscapes are allowed before replacement. Never
        # call saved=True sampler here; successful final delivery requires one.
        helpers['verify']()
        assert sha(approval['landscape_ownership_receipt'])==approval['landscape_ownership_sha256']
        assert sha(approval['bank_clean_handoff_receipt'])==approval['bank_clean_handoff_sha256']
        result['os_editor_pids_after']=helpers['editor_pids']()
        helpers['require_sole_editor'](result['os_editor_pids_after'],os.getpid())
        assert lease==(root/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').strip().splitlines()[-1]
        result['passed']=True
    except Exception as exc:
        result.update(passed=False,error=repr(exc))
    finally:
        result['after']=snapshot();result['state_unchanged']=result['after']==before
        result['passed']=bool(result.get('passed') and result['state_unchanged'])
        (HERE/('STARTUP_INSPECTION_PID'+str(os.getpid())+'.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return {key:result.get(key) for key in ('passed','error','state_unchanged','roadbld_licensed','native_catalog_digest','all_landscapes','unaccounted_landscapes')}

if __name__=='__main__':
    print(inspect())
