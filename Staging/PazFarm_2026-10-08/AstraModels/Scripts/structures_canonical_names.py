"""Use exact unsuffixed handoff names for the white default components."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,json
import paz_common as C
root=C.ROOT.resolve()
report=json.loads((root/'Reports/structures.json').read_text())
qa=json.loads((root/'Reports/structures_qa.json').read_text())
mapping={f'SM_PazFarm_NetHouse_{part}_White':f'SM_PazFarm_NetHouse_{part}' for part in ('Bay_8x4','Side_4','Door')}
bpy.ops.wm.open_mainfile(filepath=str(root/'Blend/NetHouse.blend'))
bpy.context.preferences.filepaths.save_version=0
for old,new in mapping.items():
    idx=next(i for i,r in enumerate(report['assets']) if r['name']==old)
    rec=report['assets'][idx]; ob=bpy.data.objects[old]
    coll=[bpy.data.objects[n] for n in rec['collision_objects']]
    renamed,fresh=C.asset(new,[ob],coll,pivot=rec['pivot']['position_metres'],notes=rec['notes'],budget=rec['triangle_budget'],nominal=rec['nominal_size_metres'])
    fresh['blend']='Blend/NetHouse.blend';report['assets'][idx]=fresh
    source=(root/rec['preview']).resolve();dest=(root/fresh['preview']).resolve()
    assert source.is_relative_to(root) and dest.is_relative_to(root) and source.is_file() and not dest.exists()
    source.rename(dest)
    obsolete=(root/rec['fbx']).resolve();replacement=(root/fresh['fbx']).resolve()
    assert obsolete.is_relative_to(root) and replacement.is_relative_to(root) and obsolete.is_file() and replacement.stat().st_size>10000
    obsolete.unlink()
for ob in bpy.context.scene.objects:
    ob.hide_set(ob.name!='SM_PazFarm_NetHouse_Bay_8x4');ob.hide_render=(ob.name!='SM_PazFarm_NetHouse_Bay_8x4')
bpy.context.scene['PazFarm_assets']=json.dumps([r['name'] for r in report['assets'] if '_NetHouse_' in r['name']])
bpy.ops.wm.save_as_mainfile(filepath=str(root/'Blend/NetHouse.blend'))
serialized=json.dumps(qa)
for old,new in mapping.items():serialized=serialized.replace(old,new)
qa=json.loads(serialized)
report['extra'].pop('canonical_white_mapping',None)
report['extra']['default_net_material']='White; canonical handoff names have no variant suffix. Black alternatives use _Black.'
qa['canonical_name_verification']={'status':'PASS','default_white_names':list(mapping.values()),'superseded_white_fbx_removed':list(mapping)}
(root/'Reports/structures.json').write_text(json.dumps(report,indent=2))
(root/'Reports/structures_qa.json').write_text(json.dumps(qa,indent=2))
print('CANONICAL_DEFAULT_NAMES_DONE',list(mapping.values()))
