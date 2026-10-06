"""Read-only collision samples and pure replay of the failed source grade."""
import datetime
import hashlib
import json
import marshal
import math
import os
import time
import traceback
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_grounding as grounding
import geocity_roadbld_clip as clip
import geocity_roadbld_junctions as junctions

HERE=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ManagedAstra_2026-10-03')
ROOT=HERE.parent.parent
p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
p.guard();r.guard()
stopped_path=ROOT/'Staging/AppearanceRepair_2026-10-03/TASK2_HEIGHT_GATE_STOP_20261003T185123265485Z.json'
stopped=json.loads(stopped_path.read_text())
assert r.state['phase']=='failed_clipping' and r.state['error']==stopped['error']
assert all(x.watch_tick is None and x.save_tick is None for x in bank.ACTIVE)
assert all(x.tick_handle is None for x in native.ACTIVE) and not r._tick_running
assert p.autosave_before is True and not p.autosave_settings.get_editor_property('bAutoSaveEnable')
assert p.api.is_asset_cooking_paused()
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
receipt=ROOT/'Staging/AppearanceRepair_2026-10-03'/('TASK2_HEIGHT_GATE_DETAIL_'+stamp+'.json')
status_path=HERE/'TASK2_HEIGHT_DETAIL_STATUS.json'
handle=None

def status(phase,**items):
    status_path.write_text(json.dumps(dict(phase=phase,receipt=str(receipt),**items),indent=2)+'\n')

def collect(dt):
    global handle
    unreal.unregister_slate_post_tick_callback(handle);handle=None
    began=time.monotonic()
    data={'utc':stamp,'stop_receipt':str(stopped_path),'source_state_preserved':True,
        'no_bound_geometry_mutation':True,'no_workflow_continuation':True,'no_helper_reload':True}
    def bounded():
        p.guard();r.guard()
        assert time.monotonic()-began<120
        assert r.tick_handle is None and p.watch_tick is None and p.save_tick is None
    try:
        status('collecting_read_only_height_detail')
        before=junctions._owned_state(r)
        checkpoint_hash=junctions._sha(r.state['junction_repair_report'])
        row=stopped['source_row']
        point=stopped['failure_point_cm']
        road=next(a for a in r.roads if a.get_path_name()==row['road_actor_path'])
        geo=next(a for a in r.native_geos() if a.get_name()=='RoadGeo_96')
        refs=[native._path(v) for v in native._get(geo,'SourceRoads')]
        assert refs==[road.get_path_name()]
        source_grade=[[v[0]*100,v[2]*100,v[1]*100] for v in row['points_m']]
        sampler=grounding.SourceGradeSampler(source_grade)
        clearance=r.plan['settings']['surface_clearance_cm']
        native_surface=stopped['native_meshes_before_grounding'][0]
        assert native_surface['component'].endswith('RoadGeo_96.RoadBLD Mesh')
        vertices=native_surface['world_vertices_cm']
        triangles=native_surface['triangles']
        ids=native_surface['material_ids']
        upward=[m==0 and n[2]>.25 for m,n in zip(ids,native_surface['native_face_normals_local'])]
        grounded,proof=grounding.ground_geometry(vertices,triangles,ids,sampler,clearance,300.0,upward,bounded)
        field=grounding.AsphaltField(grounded,triangles,ids,upward)
        z,number,weights=field.covered(point)
        assert abs(z-stopped['actual_grounded_z_cm'])<0.001,'Pure replay no longer matches actual failure'
        match=min((math.dist(sample,point),segment,fraction,sample) for sample,segment,fraction in grounding._samples(row,clearance,100))
        assert match[0]<0.001
        _,segment,fraction,sample=match
        terrain_cache={}
        def sample_height(xy):
            bounded()
            key=tuple(xy)
            if key not in terrain_cache:
                terrain_cache[key]=r.landscape_sampler(*xy)
            return terrain_cache[key]
        tri_ids=triangles[number]
        tri_before=[vertices[index] for index in tri_ids]
        tri_grounded=[grounded[index] for index in tri_ids]
        triangle_terrain=[{'vertex_index':index,'xy_cm':grounded[index][:2],
            'source_grade_z_cm':sampler(*grounded[index][:2]),
            'actual_landscape_z_cm':sample_height(grounded[index][:2]),
            'native_before_grounding_z_cm':vertices[index][2],'reconstructed_grounded_z_cm':grounded[index][2]}
            for index in tri_ids]
        profile=[]
        for index,xyz in enumerate(source_grade):
            profile.append({'source_point_index':index,'xy_cm':xyz[:2],'export_source_grade_z_cm':xyz[2],
                'actual_landscape_z_cm':sample_height(xyz[:2]),
                'is_original_source_vertex':index in row['original_point_indices'],
                'is_boundary_vertex':index in row['boundary_point_indices']})
        local=[]
        for sample,seg,frac in grounding._samples(row,clearance,25):
            if abs(seg-segment)>2:continue
            cover=field.covered(sample)
            local.append({'source_segment':seg,'fraction':frac,'sample_cm':sample,
                'source_grade_z_cm':sampler(*sample[:2]),'actual_landscape_z_cm':sample_height(sample[:2]),
                'grounded_native_asphalt_z_cm':cover[0] if cover else None,'triangle':cover[1] if cover else None})
        original_components=[]
        for component in geo.get_components_by_class(unreal.StaticMeshComponent):
            mesh=component.static_mesh
            copied=clip._copy_static(mesh)
            points,indices=clip._read_geometry(copied,component.get_world_transform())
            original_components.append({'component':component.get_path_name(),'bound_mesh':mesh.get_path_name(),
                'world_vertices_cm':points,'triangles':indices,'transform':clip._transform(component.get_world_transform()),
                'material_slots':clip._materials(component),'collision':clip._collision(component,mesh)})
        bounded()
        assert junctions._sha(junctions._owned_state(r))==junctions._sha(before)
        assert junctions._sha(r.state['junction_repair_report'])==checkpoint_hash
        data.update(status='READ_ONLY_HEIGHT_DETAIL_COMPLETE',elapsed_seconds=time.monotonic()-began,
            participant_and_checkpoint_unchanged=True,source_row=row,native_source_refs=refs,
            actual_road_controls=junctions._snapshot(road),
            sampler_mode='verified_source_longitudinal_native_lane_grade; sole native source is an original geographic road',
            sampler_code_sha256=hashlib.sha256(marshal.dumps(grounding.SourceGradeSampler.__call__.__code__)).hexdigest(),
            original_native_components=original_components,refined_geometry_stop_receipt=str(stopped_path),
            reconstruction='Original local grounding outputs were not retained on r when the function raised. Pure numerical replay uses the exact captured native refined geometry, loaded unchanged SourceGradeSampler and original source row. No reconstructed geometry is bound.',
            reconstructed_grounded_vertices_cm=grounded,reconstructed_grounding_proof=proof,
            failed_sample={'point_cm':point,'source_segment':segment,'fraction':fraction,
                'triangle':number,'triangle_indices':tri_ids,'barycentric_weights':weights,
                'original_refined_triangle_cm':tri_before,'reconstructed_grounded_triangle_cm':tri_grounded,
                'original_barycentric_z_cm':sum(w*v[2] for w,v in zip(weights,tri_before)),
                'grounded_barycentric_z_cm':z,'actual_reported_grounded_z_cm':stopped['actual_grounded_z_cm'],
                'actual_landscape_z_cm':sample_height(point[:2]),'clearance_cm':clearance,
                'expected_height_cm':sample_height(point[:2])+clearance,'error_cm':abs(z-sample_height(point[:2])-clearance)},
            failed_triangle_vertex_terrain_samples=triangle_terrain,
            all_exported_source_vertex_terrain_profile=profile,near_failure_25cm_source_samples=local,
            actual_landscape_path=r.landscape_sampler.path,callbacks=0,autosave_current=False,original_autosave=True,
            no_save_cook_rebuild=True)
        receipt.write_text(json.dumps(data,indent=2)+'\n')
        status('complete',source_profile_samples=len(profile),local_samples=len(local),elapsed_seconds=data['elapsed_seconds'])
    except Exception as exc:
        data.update(status='FAILED_READ_ONLY_HEIGHT_DETAIL',error=repr(exc),traceback=traceback.format_exc())
        receipt.write_text(json.dumps(data,indent=2)+'\n')
        status('failed',error=repr(exc))

assert not receipt.exists()
status('scheduled')
handle=unreal.register_slate_post_tick_callback(collect)
print(json.dumps({'scheduled':True,'status_path':str(status_path),'receipt':str(receipt)}))
