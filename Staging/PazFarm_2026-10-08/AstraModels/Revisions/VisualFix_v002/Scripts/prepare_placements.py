"""Retained offline gate correction; preserve every plant and all other placement data."""
import json,math,hashlib,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FARM=ROOT.parents[2]
old=json.loads((FARM/'Georef/PLACEMENTS.json').read_text())
new=copy.deepcopy(old)
g=old['gate'];theta=math.radians(g['dir_deg']);axis=(math.cos(theta),math.sin(theta))
def project(p):return p['e']*axis[0]+p['n']*axis[1]
near=[p for p in old['fence_segments'] if math.hypot(p['e']-g['e'],p['n']-g['n'])<18 and abs(math.sin(math.radians(p['dir_deg']-g['dir_deg'])))<.005]
near.sort(key=project)
gap=None
for low,high in zip(near,near[1:]):
 difference=project(high)-project(low)
 if 8.9<difference<9.1:
  a={'e':high['e']+3*math.cos(math.radians(high['dir_deg'])),'n':high['n']+3*math.sin(math.radians(high['dir_deg']))}
  b={'e':low['e'],'n':low['n']}
  gap=(a,b);break
assert gap,'Expected two omitted 3m panels near the gate'
a,b=gap
centre=((a['e']+b['e'])/2,(a['n']+b['n'])/2)
angle=math.degrees(math.atan2(a['n']-b['n'],a['e']-b['e']))
new['gate']['e']=round(centre[0],6);new['gate']['n']=round(centre[1],6);new['gate']['dir_deg']=round(angle,6)
length=math.hypot(a['e']-b['e'],a['n']-b['n'])
assert abs(length-6)<.01
assert old['items']==new['items'] and old['barn']==new['barn'] and old['fence_segments']==new['fence_segments'] and old['corner_posts']==new['corner_posts']
end_errors=[]
for sign,target in [(1,a),(-1,b)]:
 q=(centre[0]+sign*3*math.cos(math.radians(angle)),centre[1]+sign*3*math.sin(math.radians(angle)))
 end_errors.append(math.hypot(q[0]-target['e'],q[1]-target['n']))
(ROOT/'Georef/PLACEMENTS.json').write_text(json.dumps(new,indent=1))
patch={'source':str((FARM/'Georef/PLACEMENTS.json').resolve()),'source_sha256':hashlib.sha256((FARM/'Georef/PLACEMENTS.json').read_bytes()).hexdigest(),'units':old['units'],'replace_only_gate':{'before':old['gate'],'after':new['gate']},'reason':'SM_PazFarm_Gate_Double_6m pivots at ground centre, not at a short end. Align its 6m envelope to actual omitted-panel interval.','preserved':{'all_items':len(new['items']),'fence_segments':len(new['fence_segments']),'corner_posts':len(new['corner_posts']),'barn':True},'native_actions_performed':False}
(ROOT/'Georef/PLACEMENT_PATCH.json').write_text(json.dumps(patch,indent=2))
qa={'passed':True,'source_only_delta_keys':['gate.e','gate.n','gate.dir_deg'],'gap_endpoints_metres':[a,b],'gap_length_metres':length,'gate_end_mismatch_metres':end_errors,'all_plant_placements_identical':True,'barn_and_fence_identical':True,'new_gate':new['gate']}
(ROOT/'Reports/placement_qa.json').write_text(json.dumps(qa,indent=2))
options={'default':'Keep every current tree scale and count until native distant visibility is fixed.','avocado_canopy_xy_factor_after_visibility_review':{'default':1.0,'suggested_review_value':.8,'preserve_height':True,'scope':'247 tree_avocado instances only; not current default.'},'unknown_east_crop':'Preserve current placeholder identities/locations; no guessed crop replacement until visibility is verified and species is identified.','boundary_vegetation':'Add native scrub only under receiving operator ownership after road/gate clearance check; no unverified mesh binding included.'}
(ROOT/'Georef/DEFERRED_VISUAL_OPTIONS.json').write_text(json.dumps(options,indent=2))
print('GATE_CORRECTED',json.dumps(qa))
