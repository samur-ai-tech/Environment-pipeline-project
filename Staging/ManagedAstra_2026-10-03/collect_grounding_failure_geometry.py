"""Bounded read-copy evidence only; no bound geometry edit or workflow resume."""
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
import geocity_roadbld_grounding as grounding
import geocity_roadbld_clip as clip
import geocity_roadbld_junctions as junctions

HERE=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ManagedAstra_2026-10-03')
ROOT=HERE.parent.parent
p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
p.guard();r.guard()
assert os.getpid()==32752 and r.state['phase']=='failed_clipping'
assert r.revision=='20261003T172549017159' and r.rebuild_pass==3
assert all(x.watch_tick is None and x.save_tick is None for x in bank.ACTIVE)
assert all(x.tick_handle is None for x in native.ACTIVE) and not r._tick_running
assert p.autosave_before is True and not p.autosave_settings.get_editor_property('bAutoSaveEnable')
assert p.api.is_asset_cooking_paused()
failed_point=[-12966.939453125,11392.55078125,4948.57421875]
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
destination=ROOT/'Staging/AppearanceRepair_2026-10-03'/('TASK2_GROUNDING_GEOMETRY_'+stamp+'.json')
status_path=HERE/'TASK2_GEOMETRY_COLLECTION_STATUS.json'
handle=None

def status(phase,**values):
    status_path.write_text(json.dumps(dict(phase=phase,receipt=str(destination),**values),indent=2)+'\n')

def collect(dt):
    global handle
    unreal.unregister_slate_post_tick_callback(handle);handle=None
    started=time.monotonic()
    data={'utc':stamp,'pid':os.getpid(),'failed_point_world_cm':failed_point,'native_revision':r.revision,
        'no_retained_asset_created':True,'no_sdk_edit':True,'no_cook_rebuild_save':True,
        'loaded_helpers_reused_without_reload':True,'surfaces':[]}
    def bounded():
        p.guard();r.guard()
        assert time.monotonic()-started<=180,'Bounded evidence collection timed out'
        assert r.tick_handle is None and p.watch_tick is None and p.save_tick is None
    def bindings(geos):
        return [{'geo':a.get_path_name(),'component':c.get_path_name(),'mesh':native._path(c.static_mesh),
            'transform':clip._transform(c.get_world_transform()),'materials':clip._materials(c)}
            for a in geos for c in a.get_components_by_class(unreal.StaticMeshComponent)]
    try:
        bounded()
        status('collecting_read_only_native_geometry')
        before=junctions._owned_state(r)
        checkpoint_sha=junctions._sha(r.state['junction_repair_report'])
        geos=r.native_geos()
        bound_before=bindings(geos)
        failure=next(a for a in geos if a.get_name()=='RoadGeo_174')
        exact_sources=[native._path(v) for v in native._get(failure,'SourceRoads')]
        assert len(exact_sources)==1 and exact_sources[0].endswith(':PersistentLevel.DynamicRoad_88')
        record=next(v for v in r.junction_repair['derived_junction_roads'] if v['road_actor_path']==exact_sources[0])
        parent_paths=record['parent_road_actor_paths']
        related=set(exact_sources+parent_paths)
        selected=[a for a in geos if related.intersection(native._path(v) for v in native._get(a,'SourceRoads'))]
        rows=[dict(row,road_actor_path=road.get_path_name()) for road,row in zip(r.roads,r.plan['roads']) if road.get_path_name() in parent_paths]
        data.update(failure_geo=failure.get_path_name(),exact_native_source_roads=exact_sources,
            derived_record=record,parent_source_rows=rows,plan_settings=r.plan['settings'],
            parent_preset_specs={row['preset_key']:r.plan['presets'][row['preset_key']] for row in rows},
            participant_snapshot_before=before,junction_checkpoint_sha256=checkpoint_sha,
            bound_component_snapshot_before=bound_before,
            selected_geos=[a.get_path_name() for a in selected],
            related_parent_geometry_is_not_automatically_eligible=True)
        presets=[]
        for path in exact_sources+parent_paths:
            road=unreal.load_object(None,path)
            preset=native._get(road,'SourceDrawPreset')
            item={'road':path,'preset':native._path(preset),'preset_class':preset.get_class().get_path_name(),
                'policy':{f:native._plain(native._get(road,f)) for f in junctions._POLICY_FIELDS},'sidewalks':{}}
            for side in ('LeftSidewalkPresetClass','RightSidewalkPresetClass'):
                cls=native._get(preset,side)
                if not cls:
                    item['sidewalks'][side]=None;continue
                cdo=unreal.get_default_object(cls)
                item['sidewalks'][side]={'class':cls.get_path_name(),'settings':{f:native._plain(native._get(cdo,f))
                    for f in ('Width','ZOffset','Material','CornerMaterial','CurbClass','CurbCutLowerAmount')}}
            presets.append(item)
        data['native_presets']=presets
        def geometry(copied,transform):
            points,triangles=clip._read_geometry(copied,transform)
            copied,ids,present=unreal.GeometryScript_Materials.get_all_triangle_material_i_ds(copied)
            ids=[int(x) for x in unreal.GeometryScript_List.convert_index_list_to_array(ids)]
            assert present and len(ids)==len(triangles)
            normals=[];nearest=[];nearby=[]
            for index,tri in enumerate(triangles):
                if index%512==0:bounded()
                normal,valid=unreal.GeometryScript_MeshQueries.get_triangle_face_normal(copied,index)
                assert valid
                normals.append([float(normal.x),float(normal.y),float(normal.z)])
                triangle=[points[v] for v in tri]
                distance,projected=grounding._closest_xy(failed_point,triangle)
                if distance<=1200:nearby.append(index)
                if ids[index]==0 and normal.z>.25:
                    nearest.append((distance,index,projected))
            nearest.sort()
            return {'world_vertices_cm':points,'triangles':triangles,'material_ids':ids,
                'native_GeometryScript_face_normals_local':normals,
                'upward_asphalt_mask':[m==0 and n[2]>.25 for m,n in zip(ids,normals)],
                'triangles_within_1200cm_xy':nearby,
                'nearest_upward_asphalt':[{'distance_xy_cm':d,'triangle':i,'closest_xy_cm':xy,
                    'world_triangle_cm':[points[v] for v in triangles[i]]} for d,i,xy in nearest[:12]],
                'nearest_vertex_to_failed_point':min((math.dist(point,failed_point),i) for i,point in enumerate(points)),
                'attributes':clip._mesh_attributes(copied)}
        for actor in selected:
            bounded()
            refs=[native._path(v) for v in native._get(actor,'SourceRoads')]
            for component in actor.get_components_by_class(unreal.StaticMeshComponent):
                mesh=component.static_mesh
                if mesh is None:
                    data['surfaces'].append({'geometry_actor':actor.get_path_name(),'component':component.get_path_name(),
                        'native_source_refs':refs,'mesh':None});continue
                copied=clip._copy_static(mesh)
                transform=component.get_world_transform()
                item={'geometry_actor':actor.get_path_name(),'component':component.get_path_name(),
                    'native_source_refs':refs,'actual_same_native_source_as_failure':bool(set(refs).intersection(exact_sources)),
                    'original_bound_mesh':mesh.get_path_name(),'transform':clip._transform(transform),
                    'material_slots':clip._materials(component),'collision':clip._collision(component,mesh),
                    'original':geometry(copied,transform)}
                if actor==failure:
                    refined=unreal.GeometryScript_MeshSubdivide.apply_uniform_tessellation(copied,1)
                    item['transient_uniform_tessellation_1']=geometry(refined,transform)
                data['surfaces'].append(item)
        bounded()
        after=junctions._owned_state(r)
        bound_after=bindings(geos)
        assert junctions._sha(after)==junctions._sha(before)
        assert bound_after==bound_before
        assert junctions._sha(r.state['junction_repair_report'])==checkpoint_sha
        mesh_bindings=[row['mesh'] for row in bound_after if row['mesh']]
        data.update(status='READ_ONLY_EVIDENCE_COMPLETE',elapsed_seconds=time.monotonic()-started,
            participant_snapshot_unchanged=True,all_owned_bindings_unchanged_during_collection=True,
            checkpoint_unchanged=True,grounding_report_committed=bool(getattr(r,'grounding_report',None)),
            clipping_report_bound=bool(r.clipping_report),
            all_bound_meshes_are_native_geo_subobjects=all(':PersistentLevel.RoadGeo_' in path and path.endswith('.RoadGeoSurfaceMesh') for path in mesh_bindings),
            failure_stage='Transient grounding; ground_native_geos raised before returning prepared outputs, so clip_native_outputs was never entered for this attempt.',
            actual_geometry_not_modified=True)
        destination.write_text(json.dumps(data,indent=2)+'\n')
        status('complete',surface_count=len(data['surfaces']),elapsed_seconds=data['elapsed_seconds'])
    except Exception as exc:
        data.update(status='FAILED_READ_ONLY_COLLECTION',error=repr(exc),traceback=traceback.format_exc())
        destination.write_text(json.dumps(data,indent=2)+'\n')
        status('failed',error=repr(exc))

assert not destination.exists()
status('scheduled')
handle=unreal.register_slate_post_tick_callback(collect)
print(json.dumps({'scheduled':True,'status_path':str(status_path),'receipt':str(destination)}))
