"""Read-only inspection for the reviewed bank startup; no content writes."""
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
import unreal

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def inspect():
    import geocity_runtime_guard as guard
    import geocity_bank_workflow as workflow
    import geocity_editor_action as action
    import geocity_roadbld_workflow as roads
    activation = read(ROOT/'Staging/ManagedSystemsAstra_2026-10-04/BANK_ACTIVATION.json')
    assignment = read(HERE/'ASSIGNMENT.json')
    lease = [x for x in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1]
    fields = action.lease_fields(lease)
    assert fields['OWNER'] == 'CODEX_MANAGED_SYSTEMS_STARTUP'
    assert fields['activation'] == 'AWAITING_MANAGER_ACTUAL_PID'
    assert fields['assigned_editor_PID'] == str(os.getpid())
    assert fields['task'] == 'bank'
    assert fields['operator_thread_id'] == activation['bank_thread_id'] == assignment['thread']
    assert fields['manager_thread_id'] == activation['manager_thread_id'] == assignment['system_owner']
    assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve() == ROOT
    sources = guard.verify()
    assert len(sources) == 12
    manifest = ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
    assert sha(manifest) == activation['expected_manifest_sha256']
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    assert named_map == fields['map'] == activation['map']
    profiles = [p for p in action.persistent_profiles(ROOT) if read(p)['map'] == named_map]
    assert len(profiles) == 1 and sha(profiles[0]) == activation['expected_profile_sha256']
    profile = read(profiles[0])
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = actor_sub.get_all_level_actors()
    hd = [a for a in actors if a.get_class().get_name() == 'HoudiniAssetActor']
    assert len(hd) == 1
    wrapper = unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None, hd[0])
    api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
    def snapshot():
        return {'pid':os.getpid(), 'world':named_map,
            'cooking_paused':api.is_asset_cooking_paused(), 'auto_cook':wrapper.is_auto_cooking_enabled(),
            'auto_bake':wrapper.is_auto_bake_enabled(), 'session_valid':api.is_session_valid(),
            'autosave':unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable'),
            'dirty_maps':sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
            'dirty_content':sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
            'active_callback_handles':{name:sum(getattr(run,key,None) is not None for run in getattr(sys.modules.get(name),'ACTIVE',[]) for key in ('watch_tick','save_tick','tick_handle','_pending_correction')) for name in ('geocity_bank_workflow','geocity_roadbld_workflow')},
            'actors':sorted(a.get_path_name() for a in actor_sub.get_all_level_actors())}
    before = snapshot()
    result = {'schema':'environmentpipeline.bank_startup_inspection.v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'lease':lease,'sources':sources,'manifest_sha256':sha(manifest),'before':before,'generation_started':False,'content_saved':False}
    try:
        assert before['cooking_paused'] and not before['auto_cook'] and not before['auto_bake'] and not before['autosave']
        assert not before['dirty_maps'] and not before['dirty_content']
        assert not any(before['active_callback_handles'].values())
        result['road_landscape_authority'] = roads.inspect_geographic_landscape_authority()
        assert result['road_landscape_authority']['passed']
        result['roadbld_licensed'] = unreal.get_editor_subsystem(unreal.WorldBLDAuthSubsystem).has_license_for_tool('RoadBLD')
        run = workflow.GeoCityRun.__new__(workflow.GeoCityRun)
        run.project=ROOT; run.p=profile; run.api=api; run.state={}; run.state_path=HERE/'STARTUP_INSPECTION.json'
        resolved = run.official_landscapes(wrapper)
        prior_path = Path(profile['workflow_receipt']).with_name('LAST_SUCCESSFUL_WORKFLOW_STATE.json')
        prior = read(prior_path)
        assert Path(prior['profile']).resolve() == profiles[0].resolve()
        landscapes = {a.get_path_name() for a in actors if isinstance(a,unreal.Landscape)}
        known = set(prior['baked_actor_paths']) | set(resolved)
        result.update(resolved_official_landscapes=sorted(resolved),all_landscapes=sorted(landscapes),unaccounted_landscapes=sorted(landscapes-known),official_identity_reads=run.state['official_landscape_identity_reads'],prior_receipt=str(prior_path),prior_receipt_sha256=sha(prior_path))
        assert not landscapes-known
        handoff = read(ROOT/'Staging/ManagedSystemsAstra_2026-10-04/Task4_Integration/BANK_TURN_HANDOFF.json')
        preserved=[]
        for row in handoff['preserved']['original_maps']:
            path=ROOT/('Content/'+row['map'][6:]+'.umap')
            current=sha(path); preserved.append({'path':str(path),'sha256':current,'unchanged':current==row['sha256']})
        for row in handoff['preserved']['legitimate_named_saved_packages']:
            path=ROOT/row['file']; current=sha(path)
            preserved.append({'path':str(path),'sha256':current,'unchanged':current==row['sha256']})
        result['preserved_named_files']=preserved
        assert all(r['unchanged'] for r in preserved)
        result['passed']=True
    except Exception as exc:
        result.update(passed=False,error=repr(exc))
    finally:
        result['after']=snapshot()
        result['state_unchanged']=result['after']==before
        result['passed']=bool(result.get('passed') and result['state_unchanged'])
        text=json.dumps(result,indent=2)+'\n'
        (HERE/'STARTUP_INSPECTION.json').write_text(text,encoding='utf-8')
        (HERE/('STARTUP_INSPECTION_PID'+str(os.getpid())+'.json')).write_text(text,encoding='utf-8')
    return {key:result.get(key) for key in ('passed','error','state_unchanged','roadbld_licensed','unaccounted_landscapes')} | {'pid':os.getpid(),'receipt':str(HERE/'STARTUP_INSPECTION.json')}

if __name__ == '__main__':
    print(inspect())
