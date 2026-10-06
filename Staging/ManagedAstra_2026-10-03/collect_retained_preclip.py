"""Read-only retained preclip arrays and actual transient normal evidence."""
import datetime,hashlib,json,time,traceback
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_grounding as g
import geocity_roadbld_clip as clip
import geocity_roadbld_junctions as junctions
ROOT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline');HERE=ROOT/'Staging/ManagedAstra_2026-10-03'
p=bank.ACTIVE[-1];r=native.ACTIVE[-1];p.guard();r.guard()
assert r.state['phase']=='failed_validating' and r.tick_handle is None and not r._tick_running and p.watch_tick is None and p.save_tick is None
source=ROOT/'Staging/AppearanceRepair_2026-10-03/TASK2_ALL40_POST_CLIP_GAPS_20261003T192521158589Z.json'
d=json.loads(source.read_text());affected={s['component_path'] for s in d['affected_actual_bound_surfaces']}
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');receipt=source.parent/('TASK2_RETAINED_PRECLIP_'+stamp+'.json')
handle=None
def collect(dt):
    global handle
    unreal.unregister_slate_post_tick_callback(handle);handle=None
    began=time.monotonic();owned=junctions._owned_state(r);captured=[]
    before=[(s['component'].get_path_name(),native._path(s['component'].static_mesh)) for s in r._grounding_transient_diagnostic['surfaces']]
    for s in r._grounding_transient_diagnostic['surfaces']:
        p.guard();r.guard();assert time.monotonic()-began<120
        if s['component_path'] not in affected:continue
        v={k:x for k,x in s.items() if k not in ('component','dynamic_mesh','transform')}
        points,tris=clip._read_geometry(s['dynamic_mesh'],s['transform'])
        v['current_transient_matches_retained_preclip_arrays']=points==s['points_cm'] and tris==s['triangles']
        if v['current_transient_matches_retained_preclip_arrays']:
            v['actual_preclip_face_normals_local']=[[float(n.x),float(n.y),float(n.z)] for n,valid in [unreal.GeometryScript_MeshQueries.get_triangle_face_normal(s['dynamic_mesh'],i) for i in range(len(tris))]]
        field=g.AsphaltField(s['points_cm'],s['triangles'],s['material_ids'],s['upward'])
        v['missing_postclip_station_preclip_hits']=[]
        for item in d['missing_samples']:
            if not g._source_eligibility(s,item['road_actor_path'],item['point_cm']):continue
            hit=field.covered(item['point_cm'])
            if hit:v['missing_postclip_station_preclip_hits'].append({'point_cm':item['point_cm'],'triangle':hit[1],'z_cm':hit[0],'old_upward_mask':s['upward'][hit[1]],'actual_preclip_normal':v.get('actual_preclip_face_normals_local',[None]*len(s['triangles']))[hit[1]]})
        captured.append(v)
    assert owned==junctions._owned_state(r)
    assert before==[(s['component'].get_path_name(),native._path(s['component'].static_mesh)) for s in r._grounding_transient_diagnostic['surfaces']]
    out={'status':'READ_ONLY_RETAINED_PRECLIP_COMPLETE','source_receipt':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'correction_to_all40_receipt':'Retained _grounding_transient_diagnostic is available; this supplement contains it. Earlier availability statement was based on workflow local prepared variable and is superseded.',
      'surfaces':captured,'callbacks':0,'bound_meshes_and_participants_unchanged':True,'no_cook_save_rebuild_or_helper_reload':True,'elapsed_seconds':time.monotonic()-began}
    receipt.write_text(json.dumps(out,indent=2)+'\n')
    (HERE/'TASK2_RETAINED_PRECLIP_STATUS.json').write_text(json.dumps({'status':out['status'],'receipt':str(receipt),'sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),'elapsed_seconds':out['elapsed_seconds'],'transient_matches':[s['current_transient_matches_retained_preclip_arrays'] for s in captured],'preclip_hits':[len(s['missing_postclip_station_preclip_hits']) for s in captured]},indent=2)+'\n')
handle=unreal.register_slate_post_tick_callback(collect)
print(json.dumps({'scheduled':True,'receipt':str(receipt)}))
