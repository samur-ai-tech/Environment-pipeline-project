"""Read-only requested Road63 native geometry plus projected terrain samples."""
import datetime
import hashlib
import json
import math
import os
import time
import traceback
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_junctions as junctions
import geocity_roadbld_clip as clip

HERE=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ManagedAstra_2026-10-03')
ROOT=HERE.parent.parent
request_snapshot=json.loads((HERE/'TASK2_ROAD63_REQUEST_SNAPSHOT.json').read_text())
request=request_snapshot['request']
assert hashlib.sha256(json.dumps(request,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==request_snapshot['request_sha256']
p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
p.guard();r.guard()
assert os.getpid()==32752 and r.state['phase']=='failed_clipping'
assert all(x.watch_tick is None and x.save_tick is None for x in bank.ACTIVE)
assert all(x.tick_handle is None for x in native.ACTIVE) and not r._tick_running
assert p.api.is_asset_cooking_paused()
assert p.autosave_before is True and not p.autosave_settings.get_editor_property('bAutoSaveEnable')
sampler=r.landscape_sampler
assert sampler.path==request['landscape_path']
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
assert all(a==sampler.landscape or a in sampler.ignored for a in actors)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
receipt=ROOT/'Staging/AppearanceRepair_2026-10-03'/('TASK2_ROAD63_PROJECTED_GEOMETRY_'+stamp+'.json')
status_path=HERE/'TASK2_ROAD63_COLLECTION_STATUS.json'
handle=None

def status(phase,**values):
    status_path.write_text(json.dumps(dict(phase=phase,receipt=str(receipt),**values),indent=2)+'\n')

def collect(dt):
    global handle
    unreal.unregister_slate_post_tick_callback(handle);handle=None
    start=time.monotonic()
    data={'utc':stamp,'request_sha256':request_snapshot['request_sha256'],'request':request,'surfaces':[]}
    def bounded():
        p.guard();r.guard()
        assert time.monotonic()-start<120
        assert p.watch_tick is None and p.save_tick is None and r.tick_handle is None
    def bindings():
        return sorted([{'component':c.get_path_name(),'mesh':native._path(c.static_mesh),
            'transform':clip._transform(c.get_world_transform()),'materials':clip._materials(c)}
            for a in r.native_geos() for c in a.get_components_by_class(unreal.StaticMeshComponent)],key=lambda row:row['component'])
    try:
        status('collecting_read_only_road63')
        before=junctions._owned_state(r);bound=bindings()
        checkpoint=junctions._sha(r.state['junction_repair_report'])
        road=next(a for a in r.roads if a.get_name()=='DynamicRoad_63')
        row=dict(r.plan['roads'][r.roads.index(road)],road_actor_path=road.get_path_name())
        assert row['piece_id']==request['additional_source_required']['piece_id']=='41254723:0'
        points=[[v[0]*100,v[2]*100,v[1]*100] for v in row['points_m']]
        projected_samples={}
        def project(point):
            choices=[]
            for index,(a,b) in enumerate(zip(points,points[1:])):
                dx,dy=b[0]-a[0],b[1]-a[1];length2=dx*dx+dy*dy
                if length2<=1e-12:continue
                fraction=max(0.,min(1.,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/length2))
                xy=[a[0]+fraction*dx,a[1]+fraction*dy]
                choices.append(((point[0]-xy[0])**2+(point[1]-xy[1])**2,index,fraction,xy,a[2]+fraction*(b[2]-a[2])))
            distance2,index,fraction,xy,grade=min(choices,key=lambda item:(item[0],item[1]))
            key=tuple(round(v,6) for v in xy)
            if key not in projected_samples:
                bounded()
                projected_samples[key]={'query_index':len(projected_samples),'xy_cm':list(key),
                    'first_exact_unrounded_projection_xy_cm':xy,'roles':['nearest_source_projection_of_actual_refined_vertex'],
                    'actual_Landscape_z_cm':sampler(*key)}
            return {'query_index':projected_samples[key]['query_index'],'exact_projection_xy_cm':xy,
                'segment_index':index,'fraction':fraction,'distance_xy_cm':math.sqrt(distance2),'source_grade_z_cm':grade}
        def geometry(copied,transform,with_projections=False):
            vertices,triangles=clip._read_geometry(copied,transform)
            copied,ids,present=unreal.GeometryScript_Materials.get_all_triangle_material_i_ds(copied)
            ids=[int(v) for v in unreal.GeometryScript_List.convert_index_list_to_array(ids)]
            assert present and len(ids)==len(triangles)
            normals=[]
            for index in range(len(triangles)):
                if index%512==0:bounded()
                normal,valid=unreal.GeometryScript_MeshQueries.get_triangle_face_normal(copied,index)
                assert valid
                normals.append([float(normal.x),float(normal.y),float(normal.z)])
            result={'world_vertices_cm':vertices,'triangles':triangles,'material_ids':ids,
                'native_face_normals_local':normals,'upward_asphalt_mask':[m==0 and n[2]>.25 for m,n in zip(ids,normals)],
                'attributes':clip._mesh_attributes(copied)}
            if with_projections:result['source_projections_by_vertex']=[project(v) for v in vertices]
            return result
        geos=[a for a in r.native_geos() if [native._path(v) for v in native._get(a,'SourceRoads')]==[road.get_path_name()]]
        assert geos
        for actor in geos:
            bounded()
            for c in actor.get_components_by_class(unreal.StaticMeshComponent):
                mesh=c.static_mesh
                if mesh is None:
                    data['surfaces'].append({'component':c.get_path_name(),'mesh':None});continue
                copied=clip._copy_static(mesh);transform=c.get_world_transform()
                item={'geometry_actor':actor.get_path_name(),'component':c.get_path_name(),
                    'original_bound_mesh':mesh.get_path_name(),'native_source_refs':[road.get_path_name()],
                    'transform':clip._transform(transform),'material_slots':clip._materials(c),
                    'collision':clip._collision(c,mesh),'original':geometry(copied,transform)}
                copied=unreal.GeometryScript_MeshSubdivide.apply_uniform_tessellation(copied,1)
                item['transient_uniform_tessellation_1']=geometry(copied,transform,True)
                data['surfaces'].append(item)
        dataset_path=ROOT/'Staging/AppearanceRepair_2026-10-03/TASK2_ALL_SOURCE_LANDSCAPE_PROFILES_20261003T185815153909Z.json'
        dataset_bytes=dataset_path.read_bytes()
        assert hashlib.sha256(dataset_bytes).hexdigest()=='4b0e3c3b49f1bc64bf0e51ff6dd4e3b38f1a8d29b86ef1ca96d4c3138f0ac023'
        previous=next(v for v in json.loads(dataset_bytes)['roads'] if v['piece_id']==row['piece_id'])
        assert previous['source_actor']==road.get_path_name() and previous['source_profile_points_cm']==points
        bounded()
        assert junctions._sha(junctions._owned_state(r))==junctions._sha(before)
        assert checkpoint==junctions._sha(r.state['junction_repair_report']) and bound==bindings()
        data.update(status='READ_ONLY_ROAD63_GEOMETRY_HEIGHTS_COMPLETE',source_row=row,
            native_control_readback=junctions._snapshot(road),landscape_path=sampler.path,
            projected_height_samples=sorted(projected_samples.values(),key=lambda v:v['query_index']),
            projection_policy='Nearest sourceXY segment; equal distance uses original source segment order. Query at unique rounded6-decimal projectedXY; exact per-vertex projection retained alongside query index.',
            reused_original_control_and_dense_station_data=previous,reused_dataset=str(dataset_path),
            participant_snapshot=before,checkpoint_sha256=checkpoint,bound_component_ledger=bound,
            participant_checkpoint_bindings_unchanged=True,no_helper_reload=True,no_bound_geometry_mutation=True,
            no_source_edit_cook_rebuild_save=True,callbacks=0,autosave_current=False,original_autosave=True,
            elapsed_seconds=time.monotonic()-start)
        payload=json.dumps(data,separators=(',',':'),allow_nan=False).encode('utf-8')
        receipt.write_bytes(payload)
        status('complete',sha256=hashlib.sha256(payload).hexdigest(),bytes=len(payload),
            surface_count=len(data['surfaces']),projected_height_count=len(projected_samples),elapsed_seconds=data['elapsed_seconds'])
    except Exception as exc:
        data.update(status='FAILED_READ_ONLY_ROAD63_COLLECTION',error=repr(exc),traceback=traceback.format_exc())
        receipt.write_text(json.dumps(data,indent=2)+'\n')
        status('failed',error=repr(exc))

assert not receipt.exists()
status('scheduled')
handle=unreal.register_slate_post_tick_callback(collect)
print(json.dumps({'scheduled':True,'status_path':str(status_path),'receipt':str(receipt)}))
