"""Filesystem-only camera proposals from original geographic coordinates."""
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def closest(point, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    t = max(0, min(1, ((point[0]-a[0])*dx+(point[1]-a[1])*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
    q = (a[0]+t*dx, a[1]+t*dy)
    return math.dist(point, q), q

def inside(point, ring):
    result = False
    x, y = point
    for a, b in zip(ring, ring[1:]+ring[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            result = not result
    return result

def main():
    profile = read(ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json')
    source = Path(profile['source'])
    package = read(source)
    osm_entry = next(x for x in package['files'] if x['role']=='osm_xml')
    osm_path = source.parent/osm_entry['path']
    assert hashlib.sha256(osm_path.read_bytes()).hexdigest()==osm_entry['sha256']
    osm = ET.parse(osm_path).getroot()
    frame = dict(package['origin'], **package['local_frame'])
    nodes = {n.attrib['id']: ((float(n.attrib['lon'])-frame['lon0'])*frame['Mlon_m_per_deg']*100,
        -(float(n.attrib['lat'])-frame['lat0'])*frame['Mlat_m_per_deg']*100) for n in osm.findall('node')}
    pads = []
    for way in osm.findall('way'):
        tags = {v.attrib['k']:v.attrib['v'] for v in way.findall('tag')}
        if 'building' not in tags or tags['building']=='no':
            continue
        refs = [n.attrib['ref'] for n in way.findall('nd')]
        if len(refs)>3 and refs[0]==refs[-1] and all(n in nodes for n in refs):
            pads.append((way.attrib['id'], [nodes[n] for n in refs[:-1]]))
    state_path = ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/ROADBLD_WORKFLOW_STATE.json'
    state = read(state_path)
    proofs = list(state['junction_repair_report']['sourcecontrols_trimproof'].values())
    segments = []
    for proof in proofs:
        points = proof['original_control_points_world_cm']
        for a,b in zip(points,points[1:]):
            if math.dist(a[:2],b[:2])>1:
                segments.append((a,b,max(proof['width_start_cm'],proof['width_end_cm'])/2,proof['piece_id']))
    def pad_clearance(pt):
        if any(inside(pt,ring) for _,ring in pads):
            return -1
        return min(closest(pt,a,b)[0] for _,ring in pads for a,b in zip(ring,ring[1:]+ring[:1]))
    candidates=[]
    for a,b,halfwidth,piece in segments[::10]:
        length=math.dist(a[:2],b[:2])
        if length<80:
            continue
        mid=[(a[i]+b[i])/2 for i in range(2)]
        tangent=[(b[i]-a[i])/length for i in range(2)]
        for side in (-1,1):
            normal=[-tangent[1]*side,tangent[0]*side]
            target=[mid[i]+normal[i]*(halfwidth+450) for i in range(2)]
            eye=[target[i]-tangent[i]*400 for i in range(2)]
            if min(pad_clearance(target),pad_clearance(eye))<200:
                continue
            road_clearance=min(closest(target,x[:2],y[:2])[0]-width for x,y,width,_ in segments)
            if road_clearance<200:
                continue
            candidates.append(dict(piece=piece,target=target,eye=eye,normal=normal,tangent=tangent,
                midpoint=mid,halfwidth=halfwidth,road_clearance_cm=road_clearance,
                pad_clearance_cm=pad_clearance(target)))
    assert candidates,'No unoccluded source-ground camera proposal found'
    candidates.sort(key=lambda v: math.hypot(*v['target']))
    chosen=candidates[0]
    other=next((c for c in candidates if math.dist(c['target'],chosen['target'])>5000),candidates[-1])
    shots=[]
    def shot(name,eye,target,height,target_height,purpose,basis):
        shots.append(dict(name=name,eye_xy_cm=eye,target_xy_cm=target,eye_above_saved_landscape_cm=height,
            target_above_saved_landscape_cm=target_height,purpose=purpose,coordinate_basis=basis))
    for name,c in [('ground_close',chosen),('ground_second_location',other)]:
        shot(name,c['eye'],c['target'],170,0,'Judge texture scale, beige uniformity, normal detail and apparent roughness under current lighting.',c)
    shot('ground_grazing',[chosen['target'][i]+chosen['normal'][i]*450 for i in range(2)],chosen['target'],110,0,
        'Second angle on the same soil patch; distinguish view/lighting effects from persistent texture appearance.',{'piece':chosen['piece']})
    curb=[chosen['midpoint'][i]+chosen['normal'][i]*chosen['halfwidth'] for i in range(2)]
    shot('curb_street_close',[curb[i]-chosen['tangent'][i]*700 for i in range(2)],curb,170,8,
        'Read native curb contact, street material and sidewalk continuity at pedestrian scale.',{'piece':chosen['piece']})
    corners=[p for p in proofs if p['end_trims']]
    corner=min(corners,key=lambda p:math.hypot(*p['end_trims'][0]['source_endpoint_world_cm'][:2]))
    target=corner['end_trims'][0]['source_endpoint_world_cm'][:2]
    points=corner['original_control_points_world_cm']
    eye=min(points,key=lambda p:abs(math.dist(p[:2],target)-1000))[:2]
    shot('junction_close',eye,target,230,8,'Inspect the actual repaired corner and joined sidewalk/curb surfaces.',
        {'piece':corner['piece_id'],'trim':corner['end_trims'][0]})
    nearest=min(((closest(chosen['target'],a,b)[0],osm_id,closest(chosen['target'],a,b)[1])
        for osm_id,ring in pads for a,b in zip(ring,ring[1:]+ring[:1])),key=lambda x:x[0])
    _,osm_id,edge=nearest
    length=math.dist(chosen['target'],edge)
    direction=[(chosen['target'][i]-edge[i])/length for i in range(2)]
    target=[edge[i]+direction[i]*80 for i in range(2)]
    eye=[edge[i]+direction[i]*min(450,length) for i in range(2)]
    assert pad_clearance(eye)>0 and pad_clearance(target)>0
    shot('pad_margin_close',eye,target,170,0,'Inspect ground-to-building support, pad transition and soil variation.',{'building_osm_id':osm_id,'source_edge_xy_cm':edge})
    all_points=[p for row in proofs for p in row['original_control_points_world_cm']]
    center=[(min(p[i] for p in all_points)+max(p[i] for p in all_points))/2 for i in range(2)]
    span=max(max(p[i] for p in all_points)-min(p[i] for p in all_points) for i in range(2))
    shot('area_overview',[center[0]-span*.55,center[1]-span*.55],center,span*.8,0,
        'Context only; close images govern local ground and junction assessment.',{'source_road_extent_cm':span})
    plan=dict(schema='environmentpipeline.task2.saved_close_view_plan.v1',status='PREPARED_NOT_CAPTURED',area='GazaShujaiya',
        named_map=profile['map'],source_package=str(source),source_osm_sha256=osm_entry['sha256'],
        road_proof_revision=state['revision'],road_proof_path=str(state_path),
        camera_api='EditorLevelLibrary.set_level_viewport_camera_info; RoadBLDFeedbackToolset.CaptureViewport View=Current',
        height_policy='Resolve target/eye heights from the sole saved Landscape after saved/reopen inspection; no height guessed from old revision.',
        readiness='Explicit manager reactivation AND successful saved/reopen receipts for current delivery revision; no active bank/native callbacks.',
        no_material_changes=True,no_rebuild=True,shots=shots,
        limitations='Source-derived proposed views; framing/occlusion and actual Lit rendering still need pixel review. Current-lighting images do not independently quantify roughness or normal correctness.')
    destination=HERE/'TASK2_CAPTURE_PLAN.json'
    destination.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'plan':str(destination),'shots':len(shots),'source_building_rings':len(pads)}))

if __name__=='__main__':
    main()
