"""Bounded read-only current Road49 exterior-interval geometry evidence."""
import datetime,json,os,time,traceback
import fresh_delivery_21780 as d
STATE={'handle':None}
def collect(s):
    import unreal as u
    import geocity_bank_workflow as bank
    import geocity_roadbld_workflow as native
    import geocity_roadbld_grounding as grounding
    import geocity_roadbld_clip as clip
    import geocity_roadbld_junctions as junctions
    a=d.read(d.HERE/'ASSIGNMENTS.json');assert a['one_editor_pid']==21780 and (a['tasks']['task2_delivery'].get('editor_calls_authorized') or a['tasks']['task2_delivery'].get('read_only_editor_calls_authorized'))
    p=bank.ACTIVE[-1];r=native.ACTIVE[-1];started=time.monotonic()
    d.call(s,'parent_guard',p.guard);d.call(s,'native_guard',r.guard);d.call(s,'sole_editor_guard',p.guard_processes)
    assert r.revision=='20261003T203730573110' and r.state['phase']=='failed_validating' and 'DynamicRoad_49 segment=4' in r.state['error']
    api=d.idle(s);before=d.call(s,'participant_checkpoint_before',lambda:junctions._owned_state(r));dirty_before=d.dirty(s)
    def bound():
        assert time.monotonic()-started<120
        r.guard()
    def ledger():
        rows=[]
        for actor in r.native_geos():
            for component in actor.get_components_by_class(u.StaticMeshComponent):
                rows.append(dict(geo=actor.get_path_name(),source_refs=sorted(native._path(x) for x in native._get(actor,'SourceRoads')),component=component.get_path_name(),mesh=native._path(component.static_mesh),transform=clip._transform(component.get_world_transform()),materials=clip._materials(component),collision=clip._collision(component,component.static_mesh)))
        return rows
    bindings=d.call(s,'full_bound_mesh_material_transform_collision_ledger',ledger)
    target=next(road for road in r.roads if road.get_name()=='DynamicRoad_49');target_path=target.get_path_name()
    eligible={target_path}
    eligible.update(row['road_actor_path'] for row in r.junction_repair['derived_junction_roads'] if target_path in row['parent_road_actor_paths'])
    selected=d.call(s,'select_same_source_geos',lambda:[geo for geo in r.native_geos() if eligible.intersection(native._path(x) for x in native._get(geo,'SourceRoads'))])
    rows,surfaces,empty=d.call(s,'read_copy_actual_same_source_geometry_normals_materials',lambda:grounding._read_native(r,selected,bound))
    row=next(row for row in rows if row['road_actor_path']==target_path)
    clearance=r.plan['settings']['surface_clearance_cm']
    points=[[v[0]*100,v[2]*100,v[1]*100+clearance] for v in row['points_m']]
    start,end=points[4:6]
    candidates=[(surface,grounding.AsphaltField(surface['points_cm'],surface['triangles'],surface['material_ids'],surface['upward'])) for surface in surfaces if target_path in surface['source_road_paths']]
    intervals=grounding._physical_segment_intervals(start,end,target_path,candidates)
    heights=[]
    for fraction in [.4612367876575603,(.4612367876575603+.4614122522707323)/2,.4614122522707323]:
        point=[start[i]+fraction*(end[i]-start[i]) for i in range(3)]
        heights.append(dict(fraction=fraction,source_point_cm=point,actual_Landscape_z_cm=d.call(s,'exact_gap_Landscape_height',lambda point=point:r.landscape_sampler(*point[:2]))))
    serial=lambda surface:{key:value for key,value in surface.items() if key not in ['component','dynamic_mesh','transform']}
    diagnostic=getattr(r,'_grounding_transient_diagnostic',{})
    preclip=[serial(surface) for surface in diagnostic.get('surfaces',[]) if target_path in surface['source_road_paths']]
    assert d.call(s,'participant_checkpoint_after',lambda:junctions._owned_state(r))==before
    assert d.call(s,'full_binding_ledger_after',ledger)==bindings and d.dirty(s)==dirty_before
    s['report'].update(status='passed',revision=r.revision,token=r.transaction_token,error=r.state['error'],parent_phase=p.state['phase'],native_phase=r.state['phase'],
        failed_source_row=row,source_segment_cm=[start,end],actual_asphalt_intervals=intervals,exact_gap_Landscape_samples=heights,
        actual_same_source_surfaces=[serial(surface) for surface in surfaces],retained_preclip_grounded_arrays=preclip,
        preclip_array_caveat='Retained read-copy diagnostic arrays from completed preclip grounding; not current bound geometry.',
        plan=r.plan,grounding_report=r.grounding_report,clipping_report=r.clipping_report,full_bound_ledger=bindings,owned_participants=before,junction_repair=r.junction_repair,
        callbacks={'parent_watch':p.watch_tick is not None,'parent_save':p.save_tick is not None,'native':r.tick_handle is not None},
        Engine_valid=d.call(s,'Engine_valid',api.is_session_valid),Engine_paused=d.call(s,'Engine_paused',api.is_asset_cooking_paused),
        autosave=d.call(s,'autosave',lambda:p.autosave_settings.get_editor_property('bAutoSaveEnable')),dirty=dirty_before,
        participants_bindings_dirty_unchanged=True,no_bound_geometry_material_edit_source_reload_Cook_rebuild_or_save=True,elapsed_seconds=time.monotonic()-started)
def schedule():
    assert STATE['handle'] is None and os.getpid()==21780
    import unreal as u
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    s={'journal':d.HERE/('EXTERIOR_INTERVAL_EVIDENCE_'+stamp+'.jsonl'),'receipt':d.HERE/('EXTERIOR_INTERVAL_EVIDENCE_'+stamp+'.json'),'report':{'status':'scheduled','pid':21780}}
    def tick(dt):
        d.call(s,'unregister_capture',lambda:u.unregister_slate_post_tick_callback(STATE['handle']));STATE['handle']=None
        try:collect(s)
        except Exception:s['report'].update(status='stopped',capture_error=traceback.format_exc())
        d.write(s['receipt'],s['report'])
    d.write(s['receipt'],s['report']);STATE['handle']=d.call(s,'register_read_only_capture',lambda:u.register_slate_post_tick_callback(tick));return str(s['receipt'])
