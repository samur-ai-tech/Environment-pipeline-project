"""One root-authorized fresh bounded post-rebuild pass after observer fix."""
import copy,datetime,hashlib,json,os,time,traceback
import fresh_delivery_21780 as d
import continue_explicit_callbacks_21780 as c
STOP=d.HERE/'GROUNDING_TIMEOUT_STOP_20261003T211925662803Z.json'
STOP_SHA='96bed34749da573c64be90bc638c5b78c68b02f04cd725029e5b9b415442768c'
ACTIVE=[]
def run(s):
    import unreal as u
    import geocity_bank_workflow as bank
    import geocity_roadbld_workflow as native
    import geocity_roadbld_junctions as junctions
    import geocity_roadbld_clip as clip
    a=d.read(d.HERE/'ASSIGNMENTS.json');assert a['one_editor_pid']==21780 and a['tasks']['task2_delivery']['editor_calls_authorized']
    assert os.getpid()==21780 and len(bank.ACTIVE)==len(native.ACTIVE)==1
    assert hashlib.sha256(STOP.read_bytes()).hexdigest()==STOP_SHA
    for name,expected in c.FROZEN.items():assert hashlib.sha256((d.ROOT/'Content/Python'/name).read_bytes()).hexdigest()==expected
    assert hashlib.sha256((d.HERE/'continue_explicit_callbacks_21780.py').read_bytes()).hexdigest()=='ef063beaca5a466c4d7fbd2dd8328a20d83337ebb30c84c8e8fc9997a08bafc6'
    p=bank.ACTIVE[0];r=native.ACTIVE[0];s.update(parent=p,native=r)
    assert p.native_road_run is r and type(r) is native.RoadBLDRun
    d.call(s,'parent_guard',p.guard);d.call(s,'native_guard',r.guard);d.call(s,'sole_editor_guard',p.guard_processes)
    stop=d.read(STOP)
    assert r.revision==stop['revision']=='20261003T203730573110' and r.transaction_token==stop['token']
    assert r.state['phase']=='failed_clipping' and r.state['error']==stop['native_state']['error']
    assert p.state['phase']=='failed_native_road_transaction' and p.native_road_phase=='authoring'
    assert r.rebuild_pass==3 and r.job_id==stop['native_state']['rebuild_job_id']
    assert len(r.roads)==40 and len(r.derived_junction_roads)==4 and r.junction_repair['completed_corner_count']==4
    assert r.clipping_report is None and not getattr(r,'grounding_report',None) and not r._tick_running
    assert all(getattr(x,k,None) is None for x in [p,r] for k in ['watch_tick','save_tick','tick_handle'])
    api=d.idle(s);assert d.call(s,'Engine_valid',api.is_session_valid)
    actual=d.call(s,'actual_participants',lambda:junctions._owned_state(r));assert actual==stop['actual_participants']
    current_dirty=d.dirty(s);assert {k:sorted(v) for k,v in current_dirty.items()}=={k:sorted(v) for k,v in stop['dirty'].items()}
    bindings=[]
    for geo in d.call(s,'actual_native_geos',r.native_geos):
        for component in d.call(s,'actual_components',lambda geo=geo:geo.get_components_by_class(u.StaticMeshComponent)):
            bindings.append(d.call(s,'actual_binding_material_collision',lambda component=component:dict(component=component.get_path_name(),mesh=native._path(component.static_mesh),materials=clip._materials(component),transform=clip._transform(component.get_world_transform()),collision=clip._collision(component,component.static_mesh))))
    assert len(bindings)==87 and bindings==stop['bindings']
    assert all('/ClippedGeometry/' not in row['mesh'] and ':PersistentLevel.RoadGeo_' in row['mesh'] for row in bindings)
    # Verify the live observer calls the provided original function every time,
    # while its repeat logging is coalesced. Pure Python; no authoring SDK call.
    assert '_GUARD_JOURNAL' in d.call.__code__.co_names and 'monotonic' in d.call.__code__.co_names
    s['report'].update(pre_parent_state=copy.deepcopy(p.state),pre_native_state=copy.deepcopy(r.state),actual_participants=actual,bindings=bindings,dirty=current_dirty,timeout_stop_receipt=str(STOP),all_bindings_still_original_native_subobjects=True,source_freeze=c.FROZEN,new_grounding_pass_limit_seconds=600,no_deadline_extension=True)
    d.write(s['receipt'],s['report'])
    s['transition_started']=True;c.install(s,p,r,native)
    d.call(s,'register_parent_post_cook',lambda:p.wrapper.on_post_cook_delegate.add_callable(p.after_cook))
    d.call(s,'register_parent_post_processing',lambda:p.wrapper.on_post_processing_delegate.add_callable(p.after_processing))
    d.call(s,'suspend_autosave',p.suspend_transaction_autosave)
    p.started_epoch=time.time();p.state['phase']='native_road_authoring';p.state.pop('error',None);p.state.pop('api_error',None)
    p.state['grounding_observer_restart_evidence']=str(s['receipt'])
    r.state['phase']='clipping';r.state.pop('error',None);r.state['grounding_observer_restart_evidence']=str(s['receipt'])
    d.call(s,'persist_native_pass_start',r.write);d.call(s,'persist_parent_pass_start',p.write)
    p.watch_tick=d.call(s,'register_parent_watch',lambda:u.register_slate_post_tick_callback(p.watch))
    s['report']['status']='post_rebuild_grounding_clipping_running';d.write(s['receipt'],s['report'])
    r._tick_running=True
    try:
        d.call(s,'fresh_600s_grounding_then_clipping',r.clip_final_geometry)
        r.state['phase']='validating';r.write()
        d.call(s,'ordinary_final_native_validation',r.validate)
        d.call(s,'ordinary_native_finish',r.finish)
        d.call(s,'ordinary_parent_native_completion',lambda:r.on_complete(r,True))
        s['report']['status']='native_complete_parent_lifecycle_resumed'
    finally:r._tick_running=False
def schedule(manager_activation):
    assert manager_activation=='ROOT_AUTHORIZED_GROUNDING_ONLY_AFTER_OBSERVER_FIX' and not ACTIVE
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    s={'handle':None,'receipt':d.HERE/('GROUNDING_ONLY_RESUME_'+stamp+'.json'),'journal':d.HERE/('GROUNDING_ONLY_RESUME_'+stamp+'.jsonl'),'report':{'status':'scheduled','pid':os.getpid()}}
    import unreal as u
    def tick(dt):
        d.call(s,'unregister_one_shot',lambda:u.unregister_slate_post_tick_callback(s['handle']));s['handle']=None
        try:run(s)
        except Exception as exc:
            s['report'].update(status='stopped',error=traceback.format_exc())
            if s.get('transition_started'):
                try:d.call(s,'ordinary_native_failure_cleanup',lambda:s['native'].fail(exc))
                except Exception:s['report']['cleanup_error']=traceback.format_exc()
        d.write(s['receipt'],s['report'])
    d.write(s['receipt'],s['report']);ACTIVE.append(s)
    s['handle']=d.call(s,'register_one_shot_GameThread',lambda:u.register_slate_post_tick_callback(tick));return str(s['receipt'])
