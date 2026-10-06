"""Measure source contact for selected existing Bank_ME models without editing geometry."""
import bpy
import itertools
import json
import hashlib
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ARCHIVE=Path('C:/Users/USER/Documents/Unreal Projects/GIS_WorldBLD/SourceData/ModelBanks_Archive/Unreal_Model_Library_2026-09-24/Sources/Hergel')
jobs=json.loads((HERE/'NATIVE_CONFIGURATIONS.json').read_text())['rows']
results=[]
for job in jobs:
    if 'Bank_ME_v3' not in job['asset_id']:continue
    import re
    num=re.search(r'SM_H(\d{4})_',job['asset_id']).group(1)
    report=json.loads((ARCHIVE/'Reports'/(num+'.json')).read_text());path=ARCHIVE/report['blend']
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
    all_v=[];objects=[];scale=bpy.context.scene.unit_settings.scale_length
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        if re.match(r'^(UCX|UBX|UCP|USP)_',ob.name,re.I) or re.search(r'(?:_|\b)LOD[_-]?[1-9]',ob.name,re.I):continue
        co=np.empty(len(ob.data.vertices)*3,dtype=np.float64);ob.data.vertices.foreach_get('co',co);co=co.reshape(-1,3)
        mat=np.asarray(ob.matrix_world);world=(co@mat[:3,:3].T+mat[:3,3])*scale*100
        all_v.append(world);objects.append({'name':ob.name,'vertices':len(world),'bounds_source_cm':{'min':world.min(axis=0).tolist(),'max':world.max(axis=0).tolist()}})
    v=np.concatenate(all_v);low=v.min(axis=0);high=v.max(axis=0)
    native=job['bounds_cm'];nlow=np.asarray(native['min']);nhigh=np.asarray(native['max'])
    # Infer only a rigid signed axis permutation from matching both full bounds.
    # No scale fitting or guessed unit compensation is allowed.
    transforms=[]
    for perm in itertools.permutations(range(3)):
        for sign in itertools.product((-1,1),repeat=3):
            s=np.asarray(sign);a=low[list(perm)]*s;b=high[list(perm)]*s
            lo=np.minimum(a,b);hi=np.maximum(a,b)
            error=max(np.max(np.abs(lo-nlow)),np.max(np.abs(hi-nhigh)))
            if error<0.06:transforms.append({'native_axis_from_source':list(perm),'sign':list(sign),'bounds_error_cm':float(error)})
    z=float(low[2]);bottom=v[v[:,2]<=z+1.0]
    near=v[v[:,2]<=z+12.0]
    levels=[]
    for level in sorted(set(np.round(near[:,2],1))):
        group=near[np.abs(np.round(near[:,2],1)-level)<0.01]
        levels.append({'z_cm_rounded':float(level),'vertices':len(group),'xy_min':group[:,:2].min(axis=0).tolist(),'xy_max':group[:,:2].max(axis=0).tolist()})
    results.append({'asset_id':job['asset_id'],'source_blend':str(path),'source_sha256':before,
        'source_bounds_cm':{'min':low.tolist(),'max':high.tolist()},'objects':objects,'source_bottom_1cm':{
            'vertices':len(bottom),'xy_min':bottom[:,:2].min(axis=0).tolist(),'xy_max':bottom[:,:2].max(axis=0).tolist()},
        'matching_rigid_native_axis_transforms':transforms,'lowest_12cm_levels':levels,'geometry_changed':False,
        'note':'Bounds agreement constrains source/native axes; symmetric ambiguity stays explicit. Individual facing is reviewed separately.'})
    assert before==hashlib.sha256(path.read_bytes()).hexdigest()
    (HERE/'SOURCE_CONTACT_READBACK.json').write_text(json.dumps(results,indent=2)+'\n')
    print('SOURCE_CONTACT',job['asset_id'],len(transforms),flush=True)
