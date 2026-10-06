"""Offline captured-array replay. Never imports or calls an active Unreal editor."""
import gzip
import hashlib
import json
import math
import sys
import time
from types import SimpleNamespace
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT/'Content/Python'))
sys.dont_write_bytecode = True
import geocity_roadbld_grounding as g
import geocity_roadbld_seams as s

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load():
    review = json.loads((HERE/'ALL40_OFFLINE_REVIEW_20261003T213901084762Z.json').read_text())
    plan = json.loads((HERE/'EXTERIOR_INTERVAL_EVIDENCE_20261003T213208608026Z.json').read_text())['plan']
    package = review['review_geometry_packages']['retained_preclip']
    assert sha(package['path']) == package['sha256']
    with gzip.open(package['path'], 'rt') as stream:
        data = json.load(stream)
    surfaces = [{**ref, **data['geometry_blobs'][ref['geometry_blob_sha256']]} for ref in data['surface_references']]
    changes = []
    for surface in surfaces:
        assert surface['frame']['scale3d'] == [1.,1.,1.]
        assert surface['frame']['rotation_xyzw'] == [0.,0.,0.,1.]
        flags=[]
        for number,(triangle,material,old) in enumerate(zip(surface['triangles'],surface['material_ids'],surface['upward'])):
            points=[surface['points_cm'][i] for i in triangle]
            try:
                normal_z=-s._unit_normal(points)[2]
            except AssertionError:
                normal_z=0.
            flag=material==0 and normal_z>.25
            flags.append(flag)
            if flag != old:
                changes.append({'component':surface['component_path'],'triangle':number,'old':old,'new':flag,'actual_native_normal_z':normal_z})
        surface['upward']=flags
    rows=[row for row in review['source_rows'] if row['piece_id'] in review['affected_piece_ids']]
    return review,plan,surfaces,rows,changes

if __name__ == '__main__':
    began=time.monotonic()
    review,plan,surfaces,rows,changes=load()
    print('captured surfaces',len(surfaces),'affected rows',len(rows),'normal changes',len(changes),flush=True)
    gaps,proof=s.continuous_gaps(plan,rows,surfaces,lambda:None)
    print('refreshed preclip gaps',len(gaps),'max',max(v['length_cm'] for v in gaps),flush=True)
    result={'source_scope':'all40 captured audit; replay geometry restricted to its 16 affected source rows and 58 captured components',
            'captured_all40_gap_count':review['gap_count'],'replayed_source_rows':len(rows),
            'refreshed_eligibility_changes':changes,'initial_refreshed_preclip_gaps':gaps,'initial_proof':proof,
            'editor_calls':0,'elapsed_seconds':time.monotonic()-began}
    (HERE/'TASK1_REPLACEMENT_REPLAY_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    # The replay executes the production planner/iteration with explicit array
    # sinks. It proves XY coverage and ownership, not native Boolean/UV/collision
    # execution or physical Landscape heights, which require the owned editor.
    replay_patches=[]
    def append_array(surface,points,triangles):
        offset=len(surface['points_cm'])
        surface['points_cm']=surface['points_cm']+points
        surface['triangles']=surface['triangles']+[[offset+i for i in tri] for tri in triangles]
        surface['material_ids']=surface['material_ids']+[0]*len(triangles)
        surface['upward']=surface['upward']+[True]*len(triangles)
    def apron(run,proposal,surfaces,fields,landscape_z,bounded):
        carrier=next(v for v in surfaces if v['component_path']==proposal['component_path'])
        ring=proposal['ring_world_xy_cm']
        tri=fields[carrier['component_path']].faces[proposal['parent_asphalt_triangle_index']]
        points=[[x,y,g._plane_z(g._barycentric([x,y],*tri),tri)] for x,y in ring]
        append_array(carrier,points,[[0,1,2],[0,2,3]])
        replay_patches.append({'kind':'join_plan_xy_projection','component':carrier['component_path'],'ring':ring})
        print('join strip',proposal['gap']['piece_id'],round(proposal['longitudinal_length_cm'],3),flush=True)
    def fan(surface,proposal,bounded):
        points=proposal['boundary_edge_world_cm']+[proposal['support_vertex_world_cm']]
        append_array(surface,points,[[0,1,2]])
        replay_patches.append({'kind':'fan_actual_plane','component':surface['component_path'],'proposal':proposal})
        print('fan',proposal['gap']['piece_id'],proposal['gap']['length_cm'],flush=True)
    def nearest_native_plane(x,y):
        # A geometric replay fixture, deliberately not called Landscape proof.
        candidates=[]
        for v in surfaces:
            f=g.AsphaltField(v['points_cm'],v['triangles'],v['material_ids'],v['upward'])
            hit=f.covered([x,y])
            if hit:
                candidates.append((0.,hit[0]))
            else:
                for t in f.faces.values():
                    dist,p=g._closest_xy([x,y],t)
                    candidates.append((dist,g._plane_z(g._barycentric([x,y],*t),t)))
        return min(candidates,key=lambda v:v[0])[1]-plan['settings']['surface_clearance_cm']
    # Small-fan support Z must use its selected native parent plane; the
    # production check still calls the real Landscape and enforces <=10cm.
    last_support={}
    original_plan=s.plan_boundary_fan
    def boundary_plan(*args,**kwargs):
        args=list(args);args[4]=lambda x,y:0.
        proposal=original_plan(*args,**kwargs)
        surface=next(v for v in surfaces if v['component_path']==proposal['component_path'])
        tri=args[3][surface['component_path']].faces[proposal['parent_asphalt_triangle_index']]
        p=proposal['support_vertex_world_cm'];z=g._plane_z(g._barycentric(p,*tri),tri)
        last_support['z']=z-plan['settings']['surface_clearance_cm']
        return proposal
    s._append_connector_apron=apron
    s._append_fan=fan
    s.refresh_surface=lambda surface:None
    s._clear_fan_obstructions=lambda *args:None
    s.plan_boundary_fan=boundary_plan
    try:
        proof=s.repair_continuous(SimpleNamespace(plan=plan),rows,surfaces,lambda x,y:last_support['z'],lambda:None)
        result['xy_planner_replay']=proof
        result['status']='XY_PLANNER_REPLAY_PASSED_NATIVE_OPERATIONS_NOT_RUN'
    except Exception as exc:
        result['status']='REPLAY_FAILED'
        result['error']=repr(exc)
        raise
    finally:
        result['executed_array_sinks']=replay_patches
        result['not_run']=['Unreal Boolean trimming','native UV/normal/material/collision mutation and rollback','Landscape height validation','static mesh conversion','editor binding/save/reopen','unaffected24 geometry replay']
        result['elapsed_seconds']=time.monotonic()-began
        (HERE/'TASK1_REPLACEMENT_CAPTURED_REPLAY.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
