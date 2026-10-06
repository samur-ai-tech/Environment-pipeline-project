"""One bounded read-only continuous interval/height/raw-face dataset, all40."""
import datetime,hashlib,json,math,os,time,traceback
import fresh_delivery_21780 as d
STATE={'handle':None}
def complement(values):
    cursor=0.;result=[]
    for lo,hi in values:
        if lo>cursor:result.append([cursor,lo])
        cursor=max(cursor,hi)
    if cursor<1.:result.append([cursor,1.])
    return result
def point_at(a,b,t):return [a[i]+t*(b[i]-a[i]) for i in range(len(a))]
def collect(s):
    import unreal as u
    import geocity_bank_workflow as bank
    import geocity_roadbld_workflow as native
    import geocity_roadbld_grounding as g
    import geocity_roadbld_clip as clip
    import geocity_roadbld_junctions as junctions
    a=d.read(d.HERE/'ASSIGNMENTS.json');assert a['one_editor_pid']==21780 and (a['tasks']['task2_delivery'].get('editor_calls_authorized') or a['tasks']['task2_delivery'].get('read_only_editor_calls_authorized'))
    p=bank.ACTIVE[-1];r=native.ACTIVE[-1];began=time.monotonic()
    d.call(s,'parent_guard',p.guard);d.call(s,'native_guard',r.guard);d.call(s,'sole_editor_guard',p.guard_processes)
    assert r.revision=='20261003T203730573110' and r.state['phase']=='failed_validating'
    api=d.idle(s);checkpoint=d.call(s,'participant_checkpoint_before',lambda:junctions._owned_state(r));dirty=d.dirty(s)
    clip_sha=g._sha(r.clipping_report);ground_sha=g._sha(r.grounding_report);junction_sha=g._sha(r.junction_repair)
    def bounded():
        assert time.monotonic()-began<300,'Read-only all40 collection limit exceeded'
        r.guard();assert p.watch_tick is None and p.save_tick is None and r.tick_handle is None
    def status(phase,**values):
        d.write(s['status'],dict(phase=phase,receipt=str(s['receipt']),elapsed_seconds=time.monotonic()-began,**values))
    status('read_actual_87_bound_surfaces')
    rows,surfaces,empty=d.call(s,'read_copy_all_bound_native_geometry',lambda:g._read_native(r,None,bounded))
    assert len(rows)==40 and len(surfaces)==87
    ledger=d.call(s,'exact_immutable_clip_ledger',lambda:g._verify_partition_ledger(r.plan,rows,surfaces,r.clipping_report,r.grounding_report))
    fields=[(surface,g.AsphaltField(surface['points_cm'],surface['triangles'],surface['material_ids'],surface['upward'])) for surface in surfaces]
    partition=d.call(s,'exact_protected_source_partition',lambda:g.analyze_protected_source_intervals(r.plan,rows,bounded))
    by_piece={row['piece_id']:row for row in partition['source_roads']}
    rings=[(str(pad['source_osm_id']),[[float(v[0])*100,float(v[1])*100] for v in pad['ring_xz_m']]) for pad in r.plan['protected_building_footprints_xz_m']]
    clearance=r.plan['settings']['surface_clearance_cm'];gaps=[];road_records=[];affected=set();height_issues=[]
    def nearest_pads(point):
        results=[]
        for sid,ring in rings:
            best=float('inf')
            for aa,bb in zip(ring,ring[1:]+ring[:1]):
                dv=[bb[k]-aa[k] for k in range(2)];den=sum(x*x for x in dv)
                t=max(0,min(1,sum((point[k]-aa[k])*dv[k] for k in range(2))/den)) if den else 0
                best=min(best,math.dist(point[:2],[aa[k]+t*dv[k] for k in range(2)]))
            results.append(dict(pad_source_osm_id=sid,location=g._ring_location(point,ring),edge_distance_cm=best))
        return sorted(results,key=lambda value:value['edge_distance_cm'])[:3]
    def probe(row,candidates,point,segment,fraction,kind):
        value=dict(point_cm=point,segment=segment,fraction=fraction,kind=kind)
        try:
            pads=[sid for sid,ring in rings if g._ring_location(point,ring)=='interior'];value['protected_interior_pads']=pads
            value['Landscape_z_cm']=r.landscape_sampler(*point[:2]);expected=value['Landscape_z_cm']+clearance
            hits=[]
            for surface,field in candidates:
                provenance=g._source_eligibility(surface,row['road_actor_path'],point)
                if provenance is None:continue
                hit=field.covered(point)
                if hit is not None:hits.append(dict(component=surface['component_path'],asphalt_z_cm=hit[0],triangle=hit[1],height_error_cm=abs(hit[0]-expected),provenance=provenance))
            value['eligible_actual_hits']=hits
            if not pads and (not hits or min(x['height_error_cm'] for x in hits)>10):height_issues.append(dict(piece_id=row['piece_id'],**value))
        except Exception:value['measurement_error']=traceback.format_exc()
        return value
    for row in rows:
        bounded();path=row['road_actor_path'];candidates=[(surf,field) for surf,field in fields if path in surf['source_road_paths']]
        record=dict(piece_id=row['piece_id'],source_osm_id=row['source_osm_id'],road_actor_path=path,continuous_segments=[],station_samples=[],boundary_and_gap_probes=[],errors=[])
        points=[[v[0]*100,v[2]*100,v[1]*100+clearance] for v in row['points_m']]
        exclusions={x['segment_index']:x for x in by_piece[row['piece_id']]['segments']}
        for index,(start,end) in enumerate(zip(points,points[1:])):
            if index%64==0:bounded()
            try:
                actual=g._physical_segment_intervals(start,end,path,candidates);excluded=exclusions.get(index,{}).get('excluded_union',[])
                combined=g._interval_union(actual+excluded);missing=complement(combined)
                record['continuous_segments'].append(dict(segment=index,source_endpoints_cm=[start,end],length_cm=math.dist(start[:2],end[:2]),actual_asphalt_intervals=actual,excluded_intervals=excluded,combined_intervals=combined,unaccounted_intervals=missing))
                probes=set()
                for lo,hi in excluded:probes.update([lo,hi])
                for lo,hi in missing:
                    middle=(lo+hi)*.5;midpoint=point_at(start,end,middle)
                    entry=dict(road_actor_path=path,piece_id=row['piece_id'],source_osm_id=row['source_osm_id'],segment=index,interval=[lo,hi],world_endpoints_cm=[point_at(start,end,lo),point_at(start,end,hi)],length_cm=(hi-lo)*math.dist(start[:2],end[:2]),nearest_protected_pads=nearest_pads(midpoint),same_source_components=[surf['component_path'] for surf,field in candidates])
                    gaps.append(entry);affected.update(entry['same_source_components']);probes.update([lo,middle,hi])
                for fraction in sorted(probes):record['boundary_and_gap_probes'].append(probe(row,candidates,point_at(start,end,fraction),index,fraction,'analytic_boundary_or_gap'))
            except Exception:record['errors'].append(dict(segment=index,error=traceback.format_exc()))
        for number,(point,segment,fraction) in enumerate(g._samples(row,clearance,100.0)):
            if number%128==0:bounded()
            record['station_samples'].append(probe(row,candidates,point,segment,fraction,'original_station'))
        road_records.append(record);status('scanning_all40',roads_complete=len(road_records),gaps=len(gaps),height_issues=len(height_issues))
    serial=lambda surf:{key:value for key,value in surf.items() if key not in ['component','dynamic_mesh','transform']}
    actual_surfaces=[];original_surfaces=[];raw_fields={}
    for surface in surfaces:
        bounded();saved=serial(surface)
        # All materials and orientations, rather than only asphalt/upward faces.
        normals=[]
        for number in range(len(surface['triangles'])):
            if number%1024==0:bounded()
            normal,valid=u.GeometryScript_MeshQueries.get_triangle_face_normal(surface['dynamic_mesh'],number)
            normals.append(dict(valid=bool(valid),xyz=[float(normal.x),float(normal.y),float(normal.z)]))
        saved['actual_face_normals_local_all_materials']=normals
        saved['geometry_sha256']=g._sha({'vertices_cm':surface['points_cm'],'triangles':surface['triangles']})
        saved['material_ids_sha256']=g._sha(surface['material_ids']);saved['normal_sha256']=g._sha(normals)
        saved['collision']=d.call(s,'component_collision_readback',lambda surface=surface:clip._collision(surface['component'],surface['component'].static_mesh))
        actual_surfaces.append(saved)
        if surface['component_path'] not in affected:continue
        raw_fields[surface['component_path']]=dict(asphalt_any_orientation=g.AsphaltField(surface['points_cm'],surface['triangles'],surface['material_ids'],[True]*len(surface['triangles'])),all_materials_any_orientation=g.AsphaltField(surface['points_cm'],surface['triangles'],[0]*len(surface['triangles']),[True]*len(surface['triangles'])))
        binding=next(v for v in r.clipping_report['bindings'] if v['component']==surface['component_path'])
        original=d.call(s,'load_retained_native_source_mesh',lambda binding=binding:u.load_object(None,binding['source_native_mesh']))
        entry=dict(component_path=surface['component_path'],source_native_mesh=binding['source_native_mesh'],available=original is not None)
        if original:
            copied=d.call(s,'copy_retained_native_mesh',lambda:clip._copy_static(original));pts,tris=clip._read_geometry(copied,surface['transform'])
            copied,ids,present=u.GeometryScript_Materials.get_all_triangle_material_i_ds(copied);assert present
            entry.update(points_cm=pts,triangles=tris,material_ids=[int(v) for v in u.GeometryScript_List.convert_index_list_to_array(ids)],face_normals_local_all_materials=[])
            for number in range(len(tris)):
                if number%1024==0:bounded()
                normal,valid=u.GeometryScript_MeshQueries.get_triangle_face_normal(copied,number);entry['face_normals_local_all_materials'].append(dict(valid=bool(valid),xyz=[float(normal.x),float(normal.y),float(normal.z)]))
        original_surfaces.append(entry)
    by_component={surf['component_path']:surf for surf in surfaces};by_road={r['road_actor_path']:r for r in rows}
    for gap in gaps:
        bounded();row=by_road[gap['road_actor_path']];points=[[v[0]*100,v[2]*100,v[1]*100+clearance] for v in row['points_m']];start,end=points[gap['segment']:gap['segment']+2]
        gap['raw_diagnostic_intervals']={kind:g._physical_segment_intervals(start,end,gap['road_actor_path'],[(by_component[key],raw_fields[key][kind]) for key in gap['same_source_components']]) for kind in ['asphalt_any_orientation','all_materials_any_orientation']}
    diagnostic=getattr(r,'_grounding_transient_diagnostic',{})
    preclip=[serial(surf) for surf in diagnostic.get('surfaces',[]) if surf['component_path'] in affected]
    assert d.call(s,'participant_checkpoint_after',lambda:junctions._owned_state(r))==checkpoint and d.dirty(s)==dirty
    assert g._sha(r.clipping_report)==clip_sha and g._sha(r.grounding_report)==ground_sha and g._sha(r.junction_repair)==junction_sha
    s['report'].update(status='READ_ONLY_ALL40_CONTINUOUS_DATASET_COMPLETE',revision=r.revision,token=r.transaction_token,source_rows=rows,road_records=road_records,gaps=gaps,height_issues=height_issues,
        actual_bound_surfaces=actual_surfaces,affected_original_native_surfaces=original_surfaces,affected_retained_preclip_grounded_arrays=preclip,
        plan=r.plan,protected_source_partition=partition,immutable_clipping_ledger_proof=ledger,clipping_report=r.clipping_report,grounding_report=r.grounding_report,
        bound_participant_checkpoint=checkpoint,junction_repair=r.junction_repair,empty_geometry=empty,
        interpretation='Diagnostic enumeration only; same source/normal/material/provenance and .01cm XY/.1cm provenance/10cm height acceptance gates unchanged. Raw variants explicitly disable filters for diagnosis, not acceptance.',
        callbacks={'parent_watch':p.watch_tick is not None,'parent_save':p.save_tick is not None,'native':r.tick_handle is not None},Engine_valid=api.is_session_valid(),Engine_paused=api.is_asset_cooking_paused(),autosave=p.autosave_settings.get_editor_property('bAutoSaveEnable'),dirty=dirty,
        source_piece_count=len(rows),bound_component_count=len(surfaces),all_station_samples=sum(len(x['station_samples']) for x in road_records),continuous_segment_count=sum(len(x['continuous_segments']) for x in road_records),
        collection_errors=sum(len(x['errors']) for x in road_records),participants_reports_dirty_unchanged=True,no_geometry_mutation_source_reload_Cook_rebuild_or_save=True,elapsed_seconds=time.monotonic()-began)
    status('complete_before_receipt_write',roads_complete=len(rows),gaps=len(gaps),height_issues=len(height_issues))
def schedule():
    assert STATE['handle'] is None and os.getpid()==21780
    import unreal as u
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    s={'journal':d.HERE/('ALL40_INTERVALS_'+stamp+'.jsonl'),'receipt':d.HERE/('ALL40_INTERVALS_'+stamp+'.json'),'status':d.HERE/'ALL40_INTERVALS_CURRENT_STATUS.json','report':{'status':'scheduled','pid':21780}}
    def tick(dt):
        d.call(s,'unregister_read_only_capture',lambda:u.unregister_slate_post_tick_callback(STATE['handle']));STATE['handle']=None
        try:collect(s)
        except Exception:s['report'].update(status='READ_ONLY_COLLECTION_FAILED',collection_error=traceback.format_exc())
        d.write(s['receipt'],s['report']);d.write(s['status'],dict(status=s['report']['status'],receipt=str(s['receipt']),bytes=s['receipt'].stat().st_size,error=s['report'].get('collection_error')))
    d.write(s['receipt'],s['report']);STATE['handle']=d.call(s,'register_read_only_callback',lambda:u.register_slate_post_tick_callback(tick));return str(s['receipt'])
