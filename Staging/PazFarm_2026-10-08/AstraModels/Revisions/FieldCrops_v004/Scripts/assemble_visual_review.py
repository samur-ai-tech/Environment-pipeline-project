"""Record the final, independently reviewed offline appearance decision."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
qa=read('Reports/VALIDATION.json');dist=read('Reports/distance_validation.json')
assert qa['passed'] and dist['status']=='COMPLETE_OFFLINE_EVIDENCE' and dist['all_frame_source_bindings_current']
reviews={}
for family in ('VINE','OLIVE','GRASS'):
    path='Reports/INDEPENDENT_'+family+'_REVIEW.json';doc=read(path)
    assert any(doc.get(k) is True for k in ('ready','delivery_ready','ready_for_offline_delivery')),path
    assert not doc.get('blocking_issues'),path
    bindings={}
    def collect(node):
        if isinstance(node,dict):
            if 'path' in node and 'sha256' in node:bindings[node['path']]=node['sha256']
            for k,v in node.items():
                if ('/' in k or '\\' in k) and isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v):bindings[k]=v
                elif ('/' in k or '\\' in k) and isinstance(v,dict) and 'sha256' in v:bindings[k]=v['sha256']
                collect(v)
        elif isinstance(node,list):
            for x in node:collect(x)
    collect(doc)
    stale=[p for p,h in bindings.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    assert not stale,(family,stale)
    reviews[family.lower()]={'file':path,'sha256':sha(ROOT/path),'reviewed_input_hashes_rechecked':len(bindings),'stale_inputs':stale,'ready':True}
byid={r['id']:r for r in dist['frames']}
flags=[]
for p in dist['lod_comparisons']:
    if not p['review_flags']:continue
    k=p['key']
    assert k[0]=='grass',p
    if k[1].startswith('Patch_2m_'):
        assert p['review_flags']==['silhouette IoU below 0.55'],p
        assert .75<=p['LOD3_over_LOD0_opaque_area_ratio']<=1.25 and abs(p['LOD3_minus_LOD0_luma_code_value'])<10,p
        reason='The 80-triangle closed low tuft volumes replace individual blades. Coverage and dry/mixed colour remain comparable, but individual blade positions do not. Coarse low mounds are visible at 15–50 m; use the detailed mesh near the viewer and verify the native transition.'
    else:
        assert k==['grass','Clump_C','single','perspective',150] and p['review_flags']==['area ratio outside 0.65..1.45'],p
        assert .64<=p['LOD3_over_LOD0_opaque_area_ratio']<.65 and p['alpha_weighted_silhouette_iou']>.60 and abs(p['LOD3_minus_LOD0_luma_code_value'])<3,p
        reason='At 150 m the 80-triangle clump retains 64.83% of detailed alpha coverage, 0.17 percentage points below the 65% diagnostic band. Its shape and colour remain legible as a small tuft, and the mixed scatter retains 75.48% coverage. The raw flag is retained; this slight threshold miss is not treated as a broken model or hidden by changing the band.'
    flags.append({'comparison':p['key'],'flags':p['review_flags'],'decision':'ACCEPTED_OFFLINE_SIMPLIFICATION','reason':reason,'coverage_ratio':p['LOD3_over_LOD0_opaque_area_ratio'],'alpha_iou':p['alpha_weighted_silhouette_iou'],'luma_delta':p['LOD3_minus_LOD0_luma_code_value']})
assert all(p['both_visible'] for p in dist['lod_comparisons'])
def select(family,variant,arrangement,distance):return next(p for p in dist['lod_comparisons'] if p['key']==[family,variant,arrangement,'perspective',distance])
scatter=select('grass','mixed','scatter_10x10m',150)
patches={v:select('grass',v,'single',150) for v in ('Patch_2m_A','Patch_2m_B')}
report={'status':'READY_FOR_OFFLINE_HANDOFF_WITH_DOCUMENTED_LOD_SIMPLIFICATION','delivery_ready':True,'native_verified':False,
 'reviewed_utc':datetime.now(timezone.utc).isoformat(),'method':'Parent reviewed representative close and far PNGs and geometry reports; independent cross-family reviewers inspected all families and current distance bindings. Quantitative flags were retained, not suppressed.',
 'independent_reviews':reviews,'model_validation_sha256':sha(ROOT/'Reports/VALIDATION.json'),'distance_validation_sha256':sha(ROOT/'Reports/distance_validation.json'),
 'frames':154,'lod_pairs':76,'blocking_issues':[],'flagged_pairs_reviewed':flags,
 'vine_findings':'Three compatible modules retain continuous green bands, correct start posts and two grounded trunks. All 18 within-LOD variant joins pass, with no positive-volume tile overlap. The mixed block retains five uninterrupted rows at 500 m.',
 'olive_findings':'Silvery, narrow geometric foliage and open branching distinguish the olives from the earlier citrus and avocado at 100 m. Mature crown/trunk silhouettes persist at 1 km. The young tree remains present but is only a few pixels there, so individual species recognition is not claimed.',
 'grass_findings':'Detailed dry clumps and greener E/F retain fine blades, seeds and weeds. All low meshes are 80-triangle closed tufts, with low-only width expansion and darker calibrated BaseColors. Central patch coverage was repaired. Final coverage and colours are reviewed on singles and the fixed 104-instance scatter.',
 'grass_scatter_150m':scatter,'grass_patches_150m':patches,
 'calibration_history':'Reports/CalibrationGrassInitial preserves the rejected initial pixels and metrics. That patch proxy retained only about 16–17% area. Final figures above use the revised sources and current pre-render hashes.',
 'native_limits':['Explicitly install each separate authored lowest LOD and preserve material slots.','No Unreal import, Nanite or HLOD execution, native lighting, streaming or save/reopen was performed.','Coarse grass and crown volumes are distant proxies, not close-up replacements.','Tiny items remain limited by screen resolution, FOV, anti-aliasing and native material settings.'],
 'reviewed_scene_sha256':{s['file']:s['sha256'] for s in qa['sources']}}
(ROOT/'Reports/VISUAL_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('VISUAL_REVIEW_READY',len(flags),'documented grass simplification flags')
