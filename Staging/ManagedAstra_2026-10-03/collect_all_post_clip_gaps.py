"""One bounded read-only all-source post-clip coverage scan; no workflow restart."""
import datetime, hashlib, json, math, os, time, traceback
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_grounding as ground
import geocity_roadbld_clip as clip
import geocity_roadbld_junctions as junctions
ROOT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE=ROOT/'Staging/ManagedAstra_2026-10-03'
p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
p.guard();r.guard()
assert os.getpid()==32752 and r.state['phase']=='failed_validating'
assert all(x.watch_tick is None and x.save_tick is None for x in bank.ACTIVE)
assert all(x.tick_handle is None for x in native.ACTIVE) and not r._tick_running
assert p.api.is_asset_cooking_paused() and not p.autosave_settings.get_editor_property('bAutoSaveEnable')
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
receipt=ROOT/'Staging/AppearanceRepair_2026-10-03'/('TASK2_ALL40_POST_CLIP_GAPS_'+stamp+'.json')
status_path=HERE/'TASK2_ALL40_POST_CLIP_GAPS_STATUS.json'
handle=None
def status(phase,**more):
    status_path.write_text(json.dumps(dict(status=phase,receipt=str(receipt),**more),indent=2)+'\n')
def ledger():
    return [{'component':c.get_path_name(),'mesh':native._path(c.static_mesh),'transform':clip._transform(c.get_world_transform()),'materials':clip._materials(c)}
        for a in r.native_geos() for c in a.get_components_by_class(unreal.StaticMeshComponent)]
def edge_distance(point,a,b):
    dx=b[0]-a[0];dy=b[1]-a[1];d=dx*dx+dy*dy
    t=max(0,min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/d)) if d else 0
    xy=[a[0]+t*dx,a[1]+t*dy]
    return math.dist(point,xy),xy
def inside(point,ring):
    hit=False;x,y=point
    for a,b in zip(ring,ring[1:]+ring[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit
def collect(dt):
    global handle
    unreal.unregister_slate_post_tick_callback(handle);handle=None
    began=time.monotonic();before=ledger();owned=junctions._owned_state(r)
    checkpoint=ground._sha(r.junction_repair)
    data={'utc':stamp,'stop_receipt':'TASK2_POST_CLIP_COVERAGE_STOP_20261003T192250614726Z.json','phase':r.state['phase'],
        'plan':r.plan,'grounding_report':r.grounding_report,'clipping_report':r.clipping_report,'bound_ledger':before,
        'owned_snapshot':owned,'junction_repair':r.junction_repair,'revision':r.revision,'rebuild_pass':r.rebuild_pass,
        'no_geometry_mutation_cook_rebuild_save_or_helper_reload':True}
    def bounded():
        p.guard();r.guard();assert time.monotonic()-began<300
        assert p.watch_tick is None and p.save_tick is None and r.tick_handle is None
    try:
        status('reading_actual_bound_geometry')
        rows,surfaces,empty=ground._read_native(r,None,bounded)
        fields=[(s,ground.AsphaltField(s['points_cm'],s['triangles'],s['material_ids'],s['upward'])) for s in surfaces]
        area,pads,grid=clip.prepare_protections(r.plan)
        missing=[];road_results=[];affected=set()
        for row in rows:
            bounded();path=row['road_actor_path'];count=0;roadmissing=[]
            candidates=[(s,f) for s,f in fields if path in s['source_road_paths']]
            for point,segment,fraction in ground._samples(row,r.plan['settings']['surface_clearance_cm'],100):
                count+=1;bounded()
                eligible=[(s,f) for s,f in candidates if ground._source_eligibility(s,path,point)]
                if any(f.covered(point) for s,f in eligible):continue
                nearest=[]
                for s,f in eligible:
                    dist,xy,n=min((*ground._closest_xy(point,t),i) for i,t in f.faces.items())
                    nearest.append({'component':s['component_path'],'distance_cm':dist,'xy_cm':xy,'triangle':n,
                      'triangle_world_cm':f.faces[n],'material_id':s['material_ids'][n],'upward':s['upward'][n],
                      'native_source_refs':s['native_source_road_paths'],'eligibility':ground._source_eligibility(s,path,point)})
                    affected.add(s['component_path'])
                point_m=[point[0]/100,point[1]/100];padinfo=[]
                for sid,box,tris,ring in pads:
                    is_inside=inside(point_m,ring)
                    dist,xy,edge=min((*edge_distance(point_m,a,b),i) for i,(a,b) in enumerate(zip(ring,ring[1:]+ring[:1])))
                    padinfo.append({'source_osm_id':sid,'inside':is_inside,'edge_distance_cm':dist*100,'closest_edge':edge,'edge_xy_cm':[v*100 for v in xy]})
                contained=[q for q in padinfo if q['inside']]
                item={'road_actor_path':path,'piece_id':row['piece_id'],'source_osm_id':row['source_osm_id'],'point_cm':point,
                  'segment':segment,'fraction':fraction,'nearest_eligible_asphalt':sorted(nearest,key=lambda q:q['distance_cm']),
                  'containing_protected_pads':contained,'nearest_protected_pads':sorted(padinfo,key=lambda q:q['edge_distance_cm'])[:3],
                  'area_inside':area[0]<=point_m[0]<=area[2] and area[1]<=point_m[1]<=area[3],
                  'area_edge_signed_distances_cm':[(point_m[0]-area[0])*100,(point_m[1]-area[1])*100,(area[2]-point_m[0])*100,(area[3]-point_m[1])*100]}
                missing.append(item);roadmissing.append(len(missing)-1)
            road_results.append({'road_actor_path':path,'piece_id':row['piece_id'],'sample_count':count,'missing_count':len(roadmissing),'missing_indices':roadmissing})
            status('scanning_all40',roads_complete=len(road_results),missing_samples=len(missing))
        data.update(source_rows=rows,road_results=road_results,missing_samples=missing,empty_geometry=empty,
          geometry_hashes=[{'component':s['component_path'],'mesh':s['original_mesh_path'],'geometry_sha256':ground._sha({'points_cm':s['points_cm'],'triangles':s['triangles']}),
            'material_ids_sha256':ground._sha(s['material_ids']),'upward_sha256':ground._sha(s['upward'])} for s in surfaces])
        captured=[];originals=[]
        for s in surfaces:
            bounded()
            if s['component_path'] not in affected:continue
            saved={k:v for k,v in s.items() if k not in ('component','dynamic_mesh','transform')}
            saved['face_normals_local']=[[float(n.x),float(n.y),float(n.z)] for n,valid in [unreal.GeometryScript_MeshQueries.get_triangle_face_normal(s['dynamic_mesh'],i) for i in range(len(s['triangles']))]]
            captured.append(saved)
            binding=next((b for b in r.clipping_report['bindings'] if b['component']==s['component_path']),None)
            if binding:
                original=unreal.load_object(None,binding['source_native_mesh'])
                entry={'component':s['component_path'],'binding':binding,'original_available':original is not None}
                if original:
                    copied=clip._copy_static(original);pts,tris=clip._read_geometry(copied,s['transform'])
                    copied,ids,present=unreal.GeometryScript_Materials.get_all_triangle_material_i_ds(copied)
                    entry.update(points_cm=pts,triangles=tris,material_ids=[int(v) for v in unreal.GeometryScript_List.convert_index_list_to_array(ids)],
                        face_normals_local=[[float(n.x),float(n.y),float(n.z)] for n,valid in [unreal.GeometryScript_MeshQueries.get_triangle_face_normal(copied,i) for i in range(len(tris))]])
                originals.append(entry)
        data['affected_actual_bound_surfaces']=captured;data['affected_original_native_surfaces']=originals
        data['retained_preclip_transient_members']=[k for k in vars(r) if any(t in k for t in ('prepar','ground','clip'))]
        data['preclip_transient_availability']='Workflow uses local prepared list; no retained prepared surface field. Passed preclip report and original native meshes preserved; no re-grounding performed.'
        assert ledger()==before and junctions._owned_state(r)==owned and ground._sha(r.junction_repair)==checkpoint
        data.update(status='READ_ONLY_ALL40_POST_CLIP_EVIDENCE_COMPLETE',participant_checkpoint_bindings_unchanged=True,callbacks=0,
          source_road_count=len(rows),missing_sample_count=len(missing),affected_road_count=sum(q['missing_count']>0 for q in road_results))
    except Exception:
        data.update(status='READ_ONLY_COLLECTION_FAILED',collection_error=traceback.format_exc())
    data['elapsed_seconds']=time.monotonic()-began
    receipt.write_text(json.dumps(data,indent=2)+'\n')
    status(data['status'],sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),bytes=receipt.stat().st_size,
        missing_samples=data.get('missing_sample_count'),affected_roads=data.get('affected_road_count'),elapsed_seconds=data['elapsed_seconds'],error=data.get('collection_error'))
handle=unreal.register_slate_post_tick_callback(collect)
status('scheduled_read_only')
print(json.dumps({'scheduled':True,'receipt':str(receipt)}))
