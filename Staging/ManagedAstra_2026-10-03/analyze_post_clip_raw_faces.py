"""Offline raw-face diagnostic from immutable actual geometry evidence."""
import datetime, hashlib, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('ground_pure',ROOT/'Content/Python/geocity_roadbld_grounding.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
source=ROOT/'Staging/AppearanceRepair_2026-10-03/TASK2_ALL40_POST_CLIP_GAPS_20261003T192521158589Z.json'
d=json.loads(source.read_text());samples=[]
for item in d['missing_samples']:
    point=item['point_cm'];found=[]
    for s in d['affected_actual_bound_surfaces']:
        eligibility=g._source_eligibility(s,item['road_actor_path'],point)
        if not eligibility:continue
        for i,(tri,material) in enumerate(zip(s['triangles'],s['material_ids'])):
            if material!=0:continue
            verts=[s['points_cm'][j] for j in tri]
            weights=g._barycentric(point,*verts)
            if weights is None:continue
            distance,xy=g._closest_xy(point,verts)
            if distance>0.01:continue
            normal=s['face_normals_local'][i]
            found.append({'component':s['component_path'],'triangle':i,'material_id':material,'native_face_normal_local':normal,
              'passes_normal_z_threshold':normal[2]>.25,'distance_cm':distance,'world_triangle_cm':verts,'weights':weights})
    samples.append({'road_actor_path':item['road_actor_path'],'point_cm':point,'segment':item['segment'],'fraction':item['fraction'],
      'raw_material0_covering_faces':found,'inside_pad_ids':[p['source_osm_id'] for p in item['containing_protected_pads']]})
out={'status':'OFFLINE_RAW_FACE_DIAGNOSTIC_COMPLETE','source_receipt':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
  'samples':samples,'missing_sample_count':len(samples),'samples_with_any_raw_asphalt_cover':sum(bool(x['raw_material0_covering_faces']) for x in samples),
  'normal_threshold_unchanged':.25,'xy_tolerance_unchanged_cm':.01,'no_editor_calls':True}
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
target=source.parent/('TASK2_POST_CLIP_RAW_FACE_DIAGNOSTIC_'+stamp+'.json')
target.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'receipt':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'samples_with_any_raw_asphalt_cover':out['samples_with_any_raw_asphalt_cover']}))
