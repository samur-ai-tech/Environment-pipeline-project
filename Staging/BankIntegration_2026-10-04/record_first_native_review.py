"""Record individual observations made in the actual native Lit mesh editors."""
import datetime
import bank_contracts as C
jobs=C.read(C.HERE/'NATIVE_CONFIGURATIONS.json')['rows'][:6]
measurements=C.read(C.HERE/'NATIVE_CONTACT_READBACK.json')
validation=C.read(C.HERE/'NATIVE_VALIDATION.json')
observations=[
    'Single tied rubbish bag, textured dark surface, upright ground-supported form; no directional entrance or attachment requirement.',
    'Single tied black trash bag with visible folds and material, stable broad base; arbitrary ground yaw is appropriate.',
    'Closed cylindrical metal rubbish bin with lid, textured vertical sides and circular base; roadside ground placement and arbitrary yaw.',
    'Open cylindrical metal rubbish bin, textured vertical sides and circular base; roadside ground placement and arbitrary yaw.',
    'Open cylindrical metal bin containing a rubbish bag; complete ground-supported asset, arbitrary roadside yaw.',
    'Ribbed open metal bin containing a rubbish bag; complete ground-supported asset, arbitrary roadside yaw.'
]
rows=[]
for job,observation in zip(jobs,observations):
    aid=job['asset_id'];m=measurements[aid]
    assert m['pid']==32508 and not m['dependencies']['missing']
    assert m['source_sha256']==job['package_sha256']==C.sha(C.package_file(job['object_path']))
    assert m['bottom_support']['vertex_count']>=3
    assert m['bottom_support']['xy_min'][0]<0<m['bottom_support']['xy_max'][0]
    assert m['bottom_support']['xy_min'][1]<0<m['bottom_support']['xy_max'][1]
    assert abs(job['anchor_z_cm']-m['bounds_cm']['min'][2])<0.001
    validation[aid].update(ready=True,contact_reviewed=True,facing_reviewed=True,material_reviewed=True,
        pending=None,review_receipt=str(C.HERE/'NATIVE_VISUAL_REVIEW_FIRST6.json'),
        readiness_scope='Individual native ground-prop configuration; ordinary-area generation and final art acceptance remain pending')
    rows.append({'asset_id':aid,'native_path':job['object_path'],'pid':32508,'inspection':'Actual Unreal Static Mesh Editor Lit viewport; observed in Computer Use tool images',
        'observation':observation,'contact':'Source mesh bottom support spans local origin in XY; anchor equals measured minimum Z',
        'facing':'No required architectural front; local +X convention retained for arbitrary yaw',
        'materials':'Actual native material visible, complete dependencies, saved instancing-compatible derivative or prior compatible override',
        'role':job['role'],'context':job['allowed_zones'],'area_generated':False,'fresh_reopen':False,'user_art_acceptance':False})
C.write(C.HERE/'NATIVE_VISUAL_REVIEW_FIRST6.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':rows})
C.write(C.HERE/'NATIVE_VALIDATION.json',validation)
print('Six individually reviewed native prop configurations are ready for scoped catalog activation.')
