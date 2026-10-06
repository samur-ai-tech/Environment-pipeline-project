"""Finish the retained native transaction, correcting one measured seam face."""
import copy
import datetime
import hashlib
import importlib
import json
import math
import time
import traceback
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_clip as clip
import geocity_roadbld_grounding as grounding
import geocity_roadbld_topology as topology

HERE = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03')
p, r = bank.ACTIVE[-1], native.ACTIVE[-1]
p.guard(); p.guard_processes(); r.guard()
assert r.area == 'GazaRimal' and not p.watch_tick and not p.save_tick and not r.tick_handle
assert not r.network.is_road_network_stale()
for module in (native, clip, grounding, topology):
    importlib.reload(module)
native.ACTIVE.append(r); r.__class__ = native.RoadBLDRun
r.on_complete = p.after_native_roads
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
status_path = HERE / ('NATIVE_BOUND_COMPLETION_' + stamp + '.json')

def record(phase, **values):
    status_path.write_text(json.dumps(dict(area=r.area, phase=phase, **values), indent=2)+'\n', encoding='utf-8')

def correct_seam():
    seam = r.grounding_report['native_seam_repair']['repairs'][0]
    component = next(c for a in r.owned_actors() for c in a.get_components_by_class(unreal.StaticMeshComponent)
        if native._path(c) == seam['component_path'])
    asset, transform = component.static_mesh, component.get_world_transform()
    assert native._path(asset).startswith(r.plan['asset_root']+'/ClippedGeometry/')
    mesh = clip._copy_static(asset)
    points, triangles = clip._read_geometry(mesh, transform)
    expected = seam['boundary_edge_world_cm']+[seam['support_vertex_world_cm']]
    matches=[]
    for i, indices in enumerate(triangles):
        values=[points[v] for v in indices]
        if all(min(math.dist(v, e) for v in values)<.02 for e in expected):
            matches.append(i)
    assert len(matches)==1, 'Exact seam triangle not uniquely present'
    index=matches[0]
    normal, valid=unreal.GeometryScript_MeshQueries.get_triangle_face_normal(mesh,index)
    assert valid
    if normal.z > .25:
        return dict(already_correct=True, native_face_normal_z=normal.z)
    assert normal.z < -.25
    before_sha=clip._sha({'vertices_cm':points,'triangles':triangles})
    uv_sets=clip._mesh_attributes(mesh)['uv_sets']
    uv_rows=[]
    for uv_set in range(uv_sets):
        row=[]
        for weights in ((1,0,0),(0,1,0),(0,0,1)):
            mesh, valid, uv=unreal.GeometryScript_MeshQueries.get_interpolated_triangle_uv(mesh,uv_set,index,unreal.Vector(*weights))
            assert valid
            row.append(uv)
        uv_rows.append(row)
    old_indices=triangles[index]
    local=[unreal.MathLibrary.inverse_transform_location(transform,unreal.Vector(*points[v])) for v in old_indices]
    collision=clip._collision(component,asset)
    materials=clip._materials(component)
    mesh,deleted=unreal.GeometryScript_MeshEdits.delete_triangle_from_mesh(mesh,index,False)
    assert deleted
    new_indices=[]
    # Three isolated seam endpoints may be removed by native deletion. Recreate
    # only the same positions and let the actual asset copy compact native IDs.
    for position in (local[0],local[2],local[1]):
        mesh, vertex=unreal.GeometryScript_MeshEdits.add_vertex_to_mesh(mesh,position,False)
        assert vertex>=0
        new_indices.append(int(vertex))
    mesh,new_index=unreal.GeometryScript_MeshEdits.add_triangle_to_mesh(mesh,unreal.IntVector(*new_indices),0,False)
    assert new_index>=0
    mesh,valid=unreal.GeometryScript_Materials.set_triangle_material_id(mesh,new_index,0,False)
    assert valid
    for uv_set,row in enumerate(uv_rows):
        uv=unreal.GeometryScriptUVTriangle();uv.uv0,uv.uv1,uv.uv2=row[0],row[2],row[1]
        mesh,valid=unreal.GeometryScript_UVs.set_mesh_triangle_u_vs(mesh,uv_set,new_index,uv,False)
        assert valid
    normal,valid=unreal.GeometryScript_MeshQueries.get_triangle_face_normal(mesh,new_index)
    assert valid and normal.z>.25, 'Actual native frontface remains downward'
    normals=unreal.GeometryScriptTriangle()
    normals.vector0=normals.vector1=normals.vector2=normal
    mesh,valid=unreal.GeometryScript_Normals.set_mesh_triangle_normals(mesh,new_index,normals,False)
    assert valid, 'Seam normal overlay assignment failed'
    mesh=unreal.GeometryScript_Normals.recompute_normals(mesh,unreal.GeometryScriptCalculateNormalsOptions(),False)
    options=unreal.GeometryScriptCopyMeshToAssetOptions()
    options.set_editor_property('emit_transaction',False)
    options.set_editor_property('replace_materials',False)
    mesh,outcome=unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(mesh,asset,options,unreal.GeometryScriptMeshWriteLOD(),False)
    clip._success(outcome)
    component.set_static_mesh(None)
    assert component.set_static_mesh(asset)
    assert clip._collision(component,asset)==collision and clip._materials(component)==materials
    actual=clip._copy_static(asset)
    new_points,new_triangles=clip._read_geometry(actual,transform)
    assert len(new_triangles)==len(triangles)
    def shape(points,triangles):
        return sorted(tuple(sorted(tuple(round(v,5) for v in points[i]) for i in t)) for t in triangles)
    assert shape(points,triangles)==shape(new_points,new_triangles), 'Orientation repair changed actual geometry positions'
    new_sha=clip._sha({'vertices_cm':new_points,'triangles':new_triangles})
    proof=dict(schema='environmentpipeline.native_seam_orientation.v1',component=seam['component_path'],asset=native._path(asset),
        previous_geometry_sha256=before_sha,actual_geometry_sha256=new_sha,actual_native_face_normal_z=normal.z,
        triangle_count=len(new_triangles),positions_and_triangle_shapes_unchanged=True,uv_sets_preserved=uv_sets,
        materials_and_collision_preserved=True,new_asset_copies=0,map_saved=False,passed=True)
    proof_path=HERE/('NATIVE_SEAM_ORIENTATION_'+stamp+'.json')
    proof_path.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    report=copy.deepcopy(r.clipping_report)
    report['previous_clipping_receipt']=report['receipt']
    report['native_seam_orientation_repair']=str(proof_path)
    binding=next(x for x in report['bindings'] if x['component']==seam['component_path'])
    assert binding['clipped_world_triangle_geometry_sha256']==before_sha
    binding['clipped_world_triangle_geometry_sha256']=new_sha
    path=HERE/('ROADBLD_CLIP_GazaRimal_ORIENTATION_'+stamp+'.json')
    report['receipt']=str(path)
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    r.clipping_report=report;r.state['clipping_report']=report
    r.grounding_report['native_seam_orientation_repair']=proof
    r.state['grounding_report']=r.grounding_report
    return proof

def finish(delta_time):
    unreal.unregister_slate_post_tick_callback(r._bound_completion_tick)
    r._bound_completion_tick=None
    p.suspend_transaction_autosave()
    try:
        r.guard();record('correcting_exact_bound_seam_orientation')
        proof=correct_seam()
        record('validating_actual_native_ground',orientation=proof)
        r.state.update(phase='validating');r.state.pop('error',None);r.write()
        r.validate();r.finish()
        p.native_road_phase='authoring';p.native_road_run=r;p.started_epoch=time.time()
        p.state.pop('error',None)
        p.wrapper.on_post_cook_delegate.add_callable(p.after_cook)
        p.wrapper.on_post_processing_delegate.add_callable(p.after_processing)
        p.watch_tick=unreal.register_slate_post_tick_callback(p.watch)
        p.after_native_roads(r,True)
        record('official_suppression_cook_started',native_validated=True,map_saved=False)
    except Exception as exc:
        r.fail(exc)
        record('failed_preserving_saved_map',error=repr(exc),traceback=traceback.format_exc(),map_saved=False)

record('scheduled',map_saved=False)
r._bound_completion_tick=unreal.register_slate_post_tick_callback(finish)
print(json.dumps({'scheduled':True,'status_path':str(status_path)}))
