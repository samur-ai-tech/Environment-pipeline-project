"""Read-only grounding-timeout state capture; no geometry processing or retry."""
import datetime,json,os,traceback
import fresh_delivery_21780 as d
STATE={'handle':None}
def schedule():
    assert STATE['handle'] is None and os.getpid()==21780
    import unreal as u
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    s={'journal':d.HERE/('GROUNDING_TIMEOUT_STOP_'+stamp+'.jsonl'),'receipt':d.HERE/('GROUNDING_TIMEOUT_STOP_'+stamp+'.json'),'report':{'status':'scheduled','pid':21780}}
    def tick(dt):
        d.call(s,'unregister_read_only_capture',lambda:u.unregister_slate_post_tick_callback(STATE['handle']));STATE['handle']=None
        try:
            a=d.read(d.HERE/'ASSIGNMENTS.json');assert a['one_editor_pid']==21780 and (a['tasks']['task2_delivery'].get('read_only_editor_calls_authorized') or a['tasks']['task2_delivery'].get('editor_calls_authorized'))
            import geocity_bank_workflow as bank
            import geocity_roadbld_workflow as native
            import geocity_roadbld_junctions as junctions
            import geocity_roadbld_clip as clip
            import continue_explicit_callbacks_21780 as continuation
            p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
            d.call(s,'parent_guard',p.guard);d.call(s,'native_guard',r.guard);d.call(s,'sole_editor_guard',p.guard_processes)
            assert r.revision=='20261003T203730573110' and r.state['phase']=='failed_clipping'
            assert r.state['error']=="AssertionError('Native grounding exceeded bounded time; no asset bindings changed')"
            actual=d.call(s,'full_participant_checkpoint',lambda:junctions._owned_state(r))
            geos=d.call(s,'current_native_geos',r.native_geos);bindings=[]
            for geo in geos:
                for component in d.call(s,'native_components',lambda geo=geo:geo.get_components_by_class(u.StaticMeshComponent)):
                    bindings.append(d.call(s,'component_binding_only',lambda component=component:dict(component=component.get_path_name(),mesh=native._path(component.static_mesh),materials=clip._materials(component),transform=clip._transform(component.get_world_transform()),collision=clip._collision(component,component.static_mesh))))
            api=d.call(s,'official_API',u.HoudiniPublicAPIBlueprintLib.get_api)
            s['report'].update(status='passed',revision=r.revision,token=r.transaction_token,parent_state=p.state,native_state=r.state,
                actual_participants=actual,bindings=bindings,source_roads=len(r.roads),derived_roads=len(r.derived_junction_roads),native_geos=len(geos),
                rebuild_pass=r.rebuild_pass,completed_corners=r.junction_repair['completed_corner_count'],
                grounding_report_exists=bool(getattr(r,'grounding_report',None)),clipping_report_exists=bool(r.clipping_report),
                callbacks={'parent_watch':p.watch_tick is not None,'parent_save':p.save_tick is not None,'native':r.tick_handle is not None},
                Engine_valid=d.call(s,'Engine_valid',api.is_session_valid),Engine_paused=d.call(s,'Engine_paused',api.is_asset_cooking_paused),
                autosave=d.call(s,'autosave',lambda:p.autosave_settings.get_editor_property('bAutoSaveEnable')),dirty=d.dirty(s),
                HDA_autoCook=d.call(s,'HDA_autoCook',p.wrapper.is_auto_cooking_enabled),HDA_autoBake=d.call(s,'HDA_autoBake',p.wrapper.is_auto_bake_enabled),
                observation_hooks_restored=continuation.ACTIVE[-1]['report'].get('observation_hooks_restored'),
                source_class_current=type(r) is native.RoadBLDRun,no_native_edit_geometry_processing_cook_save_or_retry=True)
        except Exception:s['report'].update(status='stopped',capture_error=traceback.format_exc())
        d.write(s['receipt'],s['report'])
    d.write(s['receipt'],s['report']);STATE['handle']=d.call(s,'register_read_only_capture',lambda:u.register_slate_post_tick_callback(tick));return str(s['receipt'])
