"""One bounded read-only all-source/current-Landscape profile dataset."""
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

HERE=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ManagedAstra_2026-10-03')
ROOT=HERE.parent.parent
p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
p.guard();r.guard()
assert os.getpid()==32752 and r.state['phase']=='failed_clipping'
assert r.revision=='20261003T172549017159' and r.rebuild_pass==3
assert len(r.roads)==40 and len(r.derived_junction_roads)==4
assert all(x.watch_tick is None and x.save_tick is None for x in bank.ACTIVE)
assert all(x.tick_handle is None for x in native.ACTIVE) and not r._tick_running
assert p.api.is_asset_cooking_paused()
assert p.autosave_before is True and not p.autosave_settings.get_editor_property('bAutoSaveEnable')
sampler=r.landscape_sampler
assert sampler.run is r
assert sampler.landscape.get_name().startswith('GeoCity_city_v015_PermanentBank_')
assert sampler.landscape.get_name().endswith('_GazaShujaiya_landscape')
assert sampler.path==sampler.landscape.get_path_name()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
assert all(a==sampler.landscape or a in sampler.ignored for a in actors)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
destination=ROOT/'Staging/AppearanceRepair_2026-10-03'/('TASK2_ALL_SOURCE_LANDSCAPE_PROFILES_'+stamp+'.json')
status_path=HERE/'TASK2_ALL_SOURCE_PROFILE_STATUS.json'
handle=None

def status(phase,**items):
    status_path.write_text(json.dumps(dict(phase=phase,receipt=str(destination),**items),indent=2)+'\n')

def collect(dt):
    global handle
    unreal.unregister_slate_post_tick_callback(handle);handle=None
    started=time.monotonic()
    data={'schema':'environmentpipeline.all_source_actual_landscape_profiles.v1','utc':stamp,
        'pid':os.getpid(),'revision':r.revision,'source_sha256':r.plan['source_sha256'],
        'centreline_sha256':r.plan['centreline_sha256'],'landscape_actor':sampler.path,
        'sampling':'Existing verified current-export Landscape-only collision sampler; all other actors ignored.',
        'station_max_interval_cm':50.0,'height_frame':'World cm; source_ground_z excludes the same5cm asphalt clearance as actual Landscape Z.',
        'surface_clearance_cm':r.plan['settings']['surface_clearance_cm'],
        'roads':[],'geometry_terrain_source_changes':False}
    def bounded():
        assert time.monotonic()-started<120,'All-source profile collection exceeded120seconds'
        p.guard();r.guard()
        assert p.watch_tick is None and p.save_tick is None and r.tick_handle is None
        assert p.api.is_asset_cooking_paused()
    try:
        status('collecting_read_only_profiles')
        before=junctions._owned_state(r)
        checkpoint_sha=junctions._sha(r.state['junction_repair_report'])
        extrema={'original_export_controls':None,'dense_stations':None,'genuine_geographic_controls':None}
        exceed20={'original_export_controls':[],'dense_stations':[]}
        count_controls=count_dense=count_original=0
        for road,row in zip(r.roads,r.plan['roads']):
            bounded()
            points=[[float(v[0])*100,float(v[2])*100,float(v[1])*100] for v in row['points_m']]
            controls=[];stations=[]
            identity={'source_actor':road.get_path_name(),'source_osm_id':str(row['source_osm_id']),'piece_id':row['piece_id']}
            def sample(point,segment,fraction,index=None,station=None):
                bounded()
                terrain=float(sampler(point[0],point[1]))
                delta=point[2]-terrain
                value={'xy_cm':point[:2],'source_ground_z_cm':point[2],'actual_Landscape_z_cm':terrain,
                    'signed_source_minus_Landscape_cm':delta,'absolute_delta_cm':abs(delta),
                    'segment_index':segment,'fraction':fraction,'export_control_index':index,
                    'station_distance_xy_cm':station}
                value['is_genuine_source_vertex']=index in row['original_point_indices'] if index is not None else False
                value['is_area_boundary_vertex']=index in row['boundary_point_indices'] if index is not None else False
                # Asphalt that is within10cm of both heights exists iff their
                # +/-10cm intervals overlap; this is not an acceptance waiver.
                low=max(point[2],terrain)+data['surface_clearance_cm']-10
                high=min(point[2],terrain)+data['surface_clearance_cm']+10
                value['two_10cm_intervals_overlap']=low<=high
                value['asphalt_interval_intersection_cm']=[low,high] if low<=high else None
                return value
            def consider(category,value):
                full=dict(identity,**value)
                if extrema[category] is None or value['absolute_delta_cm']>extrema[category]['absolute_delta_cm']:
                    extrema[category]=full
            cumulative=0.0
            for i,point in enumerate(points):
                if i:cumulative+=math.dist(points[i-1][:2],point[:2])
                v=sample(point,max(0,i-1),1.0 if i else 0.0,i,cumulative)
                controls.append(v);count_controls+=1
                consider('original_export_controls',v)
                if v['is_genuine_source_vertex']:
                    consider('genuine_geographic_controls',v);count_original+=1
                if v['absolute_delta_cm']>20:exceed20['original_export_controls'].append(dict(identity,**v))
            cumulative=0.0
            stations.append(controls[0]);count_dense+=1
            consider('dense_stations',controls[0])
            for segment,(a,b) in enumerate(zip(points,points[1:])):
                length=math.dist(a[:2],b[:2]);steps=max(1,math.ceil(length/50.0))
                assert length/steps<=50.0+1e-8
                for number in range(1,steps+1):
                    fraction=number/steps
                    point=[a[k]+fraction*(b[k]-a[k]) for k in range(3)]
                    index=segment+1 if number==steps else None
                    v=sample(point,segment,fraction,index,cumulative+fraction*length)
                    stations.append(v);count_dense+=1
                    consider('dense_stations',v)
                    if v['absolute_delta_cm']>20:exceed20['dense_stations'].append(dict(identity,**v))
                cumulative+=length
            data['roads'].append(dict(identity,source_profile_points_cm=points,original_export_controls=controls,
                dense_stations=stations,current_native_control_readback=junctions._snapshot(road)))
        bounded()
        assert junctions._sha(junctions._owned_state(r))==junctions._sha(before)
        assert junctions._sha(r.state['junction_repair_report'])==checkpoint_sha
        summary={'road_count':len(data['roads']),'export_control_count':count_controls,
            'genuine_geographic_control_count':count_original,'dense_station_count':count_dense,
            'maxima':extrema,'delta_over20cm_counts':{key:len(value) for key,value in exceed20.items()},
            'interpretation':'For original exported controls, abs(delta)<=20cm is a necessary pointwise condition for satisfying both10cm gates. Dense interpolated source-grade deltas diagnose the current interpolation; they are not a new requirement that every interpolated source height remain authoritative. Feasibility does not prove geometry fit or final acceptance.'}
        data.update(status='READ_ONLY_PROFILE_DATASET_COMPLETE',summary=summary,delta_over20cm=exceed20,
            participant_and_checkpoint_unchanged=True,elapsed_seconds=time.monotonic()-started,
            callbacks=0,autosave_current=False,original_autosave=True,no_save_cook_rebuild=True)
        payload=json.dumps(data,separators=(',',':'),allow_nan=False).encode('utf-8')
        destination.write_bytes(payload)
        status('complete',sha256=hashlib.sha256(payload).hexdigest(),bytes=len(payload),
            elapsed_seconds=data['elapsed_seconds'],summary=summary)
    except Exception as exc:
        data.update(status='FAILED_READ_ONLY_PROFILE_COLLECTION',error=repr(exc),traceback=traceback.format_exc())
        destination.write_text(json.dumps(data,indent=2)+'\n')
        status('failed',error=repr(exc))

assert not destination.exists()
status('scheduled')
handle=unreal.register_slate_post_tick_callback(collect)
print(json.dumps({'scheduled':True,'status_path':str(status_path),'receipt':str(destination)}))
