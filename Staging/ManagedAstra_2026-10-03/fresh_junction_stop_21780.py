"""Read-only fresh transaction checkpoint evidence; no continuation."""
import datetime,json,os,time,traceback
import fresh_delivery_21780 as d
READ_ONLY_RUNS=[]
def read_only_guard():
    assert os.getpid()==21780
    a=d.read(d.HERE/'ASSIGNMENTS.json');task=a['tasks']['task2_delivery']
    assert a['one_editor_pid']==21780 and a['editor_writer_thread_id']=='01a102e1-25e6-7f13-b593-4988290a283b'
    assert task['read_only_editor_calls_authorized'] is True
    assert task['editor_calls_authorized'] is False
    lease=(d.ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
    assert 'assigned_editor_PID=21780' in lease and 'worker_thread_id=01a102e1-25e6-7f13-b593-4988290a283b' in lease
def collect(s):
    import unreal as u
    import geocity_bank_workflow as bank
    import geocity_roadbld_workflow as native
    import geocity_roadbld_junctions as junctions
    api=d.idle(s);p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
    d.call(s,'parent_guard',p.guard);d.call(s,'native_guard',r.guard);d.call(s,'sole_editor_process_guard',p.guard_processes)
    assert r.revision=='20261003T203730573110' and r.state['phase']=='failed_rebuilding'
    report=r.state['junction_repair_report'];operation=report['operation']
    assert operation['step']=='connector_controls' and operation['attempts']==1 and report['completed_corner_count']==0
    before_parent=json.dumps(p.state,sort_keys=True);before_native=json.dumps(r.state,sort_keys=True)
    deadline_before=operation['deadline_monotonic']
    world=d.call(s,'current_world',lambda:u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world())
    world_path=d.path(s,world,'current_world')
    actual=d.call(s,'actual_full_participant_checkpoint',lambda:junctions._owned_state(r))
    before=operation['before']
    s['report'].update(revision=r.revision,world=world_path,current_parent_count=len(bank.ACTIVE),current_native_count=len(native.ACTIVE),parent_native_link_is_current=p.native_road_run is r,parent_phase=p.state['phase'],native_phase=r.state['phase'],error=r.state['error'],
        operation={k:operation.get(k) for k in ['step','task_index','attempts','calls','deadline_monotonic','retry_at_monotonic']},
        actual_owned_state=actual,actual_owned_state_sha256=junctions._sha(actual),operation_before_sha256=junctions._sha(before),
        actual_participants_unchanged_from_pre_call=junctions._sha(actual)==junctions._sha(before),
        actual_defaults=d.call(s,'actual_global_defaults',junctions._defaults),expected_global_defaults=report['global_defaults_before'],
        source_roads=len(r.roads),derived_roads=[d.path(s,x,'derived_road') for x in r.derived_junction_roads],
        owned_native_geos=len(d.call(s,'owned_native_geos',r.native_geos)),rebuild_pass=r.rebuild_pass,job_id=r.job_id,
        callbacks={'parent_watch':p.watch_tick is not None,'parent_save':p.save_tick is not None,'native_tick':r.tick_handle is not None},
        Engine_valid=d.call(s,'Engine_valid',api.is_session_valid),Engine_paused=d.call(s,'Engine_paused',api.is_asset_cooking_paused),
        autosave_current=d.call(s,'autosave_current',lambda:p.autosave_settings.get_editor_property('bAutoSaveEnable')),
        HDA_autoCook=d.call(s,'HDA_autoCook',p.wrapper.is_auto_cooking_enabled),HDA_autoBake=d.call(s,'HDA_autoBake',p.wrapper.is_auto_bake_enabled),
        dirty=d.dirty(s),source_freeze=d.FROZEN,no_mutation_or_resume=True)
    assert operation['deadline_monotonic']==deadline_before
    assert json.dumps(p.state,sort_keys=True)==before_parent and json.dumps(r.state,sort_keys=True)==before_native
    s['report'].update(operation_deadline_monotonic_preserved=deadline_before,current_monotonic=time.monotonic(),deadline_expired=time.monotonic()>deadline_before,
        parent_native_states_unchanged=True,source_disk_sha256={name:d.hashlib.sha256((d.ROOT/'Content/Python'/name).read_bytes()).hexdigest() for name in d.FROZEN},
        loaded_source_not_reloaded=True,read_only_permission_used=True)
def schedule():
    read_only_guard();assert not any(s['handle'] is not None for s in READ_ONLY_RUNS)
    import unreal as u
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    s={'handle':None,'journal':d.HERE/('FRESH_READONLY_STOP_'+stamp+'.jsonl'),'receipt':d.HERE/('FRESH_READONLY_STOP_'+stamp+'.json'),'report':{'status':'scheduled','pid':os.getpid()}}
    def tick(dt):
        d.call(s,'unregister_read_only_callback',lambda:u.unregister_slate_post_tick_callback(s['handle']));s['handle']=None
        try:read_only_guard();collect(s);s['report']['status']='passed'
        except Exception:s['report'].update(status='stopped',capture_error=traceback.format_exc())
        d.write(s['receipt'],s['report']);d.journal(s,'READ_ONLY_CAPTURE_END',status=s['report']['status'])
    d.write(s['receipt'],s['report']);READ_ONLY_RUNS.append(s)
    s['handle']=d.call(s,'register_read_only_callback',lambda:u.register_slate_post_tick_callback(tick))
    return str(s['receipt'])
