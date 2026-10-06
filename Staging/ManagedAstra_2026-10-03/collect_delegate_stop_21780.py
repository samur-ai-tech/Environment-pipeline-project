"""Read-only observation of failed delegate registration; no authoring."""
import datetime,json,os,traceback
import fresh_delivery_21780 as d
STATE={'handle':None}
def schedule():
    assert STATE['handle'] is None and os.getpid()==21780
    import unreal as u
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    s={'journal':d.HERE/('DELEGATE_STOP_'+stamp+'.jsonl'),'receipt':d.HERE/('DELEGATE_STOP_'+stamp+'.json'),'report':{'status':'scheduled'}}
    def tick(dt):
        d.call(s,'unregister_capture',lambda:u.unregister_slate_post_tick_callback(STATE['handle']));STATE['handle']=None
        try:
            a=d.read(d.HERE/'ASSIGNMENTS.json');assert a['one_editor_pid']==21780 and (a['tasks']['task2_delivery'].get('read_only_editor_calls_authorized') or a['tasks']['task2_delivery'].get('editor_calls_authorized'))
            import geocity_bank_workflow as bank
            import geocity_roadbld_workflow as native
            import geocity_roadbld_junctions as junctions
            import continue_fresh_license_operation_21780 as continuation
            p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
            d.call(s,'parent_guard',p.guard);d.call(s,'native_guard',r.guard);d.call(s,'sole_editor_guard',p.guard_processes)
            actual=d.call(s,'actual_participants',lambda:junctions._owned_state(r))
            archive=d.read(continuation.ARCHIVE);op=r.state['junction_repair_report']['operation']
            api=d.call(s,'official_API',u.HoudiniPublicAPIBlueprintLib.get_api)
            s['report'].update(status='passed',pid=os.getpid(),revision=r.revision,token=r.transaction_token,parent_state=p.state,native_state=r.state,
                actual_participants=actual,actual_participants_unchanged_from_original_failed_call=junctions._sha(actual)==junctions._sha(archive['operation']['before']),
                new_operation_attempts=op['attempts'],new_operation_calls=op['calls'],new_operation_deadline=op['deadline_monotonic'],
                callbacks={'parent_watch':p.watch_tick is not None,'parent_save':p.save_tick is not None,'native':r.tick_handle is not None},
                Engine_valid=d.call(s,'session_valid',api.is_session_valid),Engine_paused=d.call(s,'cooking_paused',api.is_asset_cooking_paused),
                autosave=d.call(s,'autosave',lambda:p.autosave_settings.get_editor_property('bAutoSaveEnable')),dirty=d.dirty(s),
                observation_hooks_restored=continuation.ACTIVE[-1]['report'].get('observation_hooks_restored'),
                live_ACTIVE_preserved=native.ACTIVE[0] is r and bank.ACTIVE[0] is p and p.native_road_run is r)
            assert op['attempts']==0 and op['calls']==[]
        except Exception:s['report'].update(status='stopped',capture_error=traceback.format_exc())
        d.write(s['receipt'],s['report'])
    d.write(s['receipt'],s['report']);STATE['handle']=d.call(s,'register_read_only_capture',lambda:u.register_slate_post_tick_callback(tick));return str(s['receipt'])
