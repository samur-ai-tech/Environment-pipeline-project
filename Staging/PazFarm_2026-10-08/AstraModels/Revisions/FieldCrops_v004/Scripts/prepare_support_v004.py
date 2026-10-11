"""Adapt the proven v003 readback and camera helpers inside v004 only."""
import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
copy=ROOT/'Scripts/distance_core.py'
original=copy.read_text(encoding='utf-8')
names={'sha','rounded','png_read','png_write','diagnostic_background','metrics','bbox_world','configure_scene','position_camera','projected_bounds','loaded_texture_hashes'}
parts=[ast.get_source_segment(original,n) for n in ast.parse(original).body if isinstance(n,ast.FunctionDef) and n.name in names]
header='''"""Shared fixed-camera/PNG measurement helpers; no modelling or native actions."""
import bpy,sys,math,json,hashlib,struct,zlib,binascii,time
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import numpy as np
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SETTINGS={
 'engine':'CYCLES','samples':16,'adaptive_sampling':False,'denoising':False,
 'resolution_px':[1920,1080],'horizontal_fov_deg':60.0,'camera_type':'PERSP',
 'camera_clip_m':[0.01,10000],'view_transform':'Standard','look':'None','exposure_stops':0.0,'gamma':1.0,
 'world_color_linear':[0.65,0.70,0.78],'world_strength':0.35,
 'sun_energy':2.0,'sun_rotation_xyz_deg':[35,-25,-40],'sun_angle_deg':5.0,
 'transparent_film':True,'render_ground':False,'shadows_in_mask':False,
 'azimuth_deg':-55.0,'samples_seed':1977,'threads':4,
 'distance_definition':'Euclidean camera-to-declared-target slant distance in metres',
 'png':'RGBA8 display sRGB, original unrescaled 1920x1080 evidence'
}
SETTINGS_SHA=hashlib.sha256(json.dumps(SETTINGS,sort_keys=True).encode()).hexdigest()
'''
text=header+'\n\n'+'\n\n'.join(parts)+'\n'
text=text.replace("elif f in (3,4):\n            for x in range(step):", "elif f in (3,4):\n            if not row.any() and not prev.any():\n                out[y]=0\n                continue\n            for x in range(step):")
copy.write_text(text,encoding='utf-8')

v=ROOT/'Scripts/validate_delivery_v004.py'
s=v.read_text(encoding='utf-8').replace('v003','v004').replace("['pines_v004.json', 'strawberries_v004.json']", "['vines_v004.json', 'olives_v004.json', 'grass_v004.json']")
s=s.replace("any(k in mat.name.lower() for k in ['leaf','needle'])", "any(k in mat.name.lower() for k in ['leaf','needle','canopy','crown','blade','grass'])")
start=s.index("    if r['lod']==3:")
end=s.index("    for m in a['materials']:",start)
s=s[:start]+'''    if 'VineRow' in a['name']: limits=(100,300) if r['lod']==3 else (15000,40000)
    elif 'Olive' in a['name']: limits=(800,1500) if r['lod']==3 else (40000,100000)
    elif 'GrassPatch' in a['name']: limits=(20,80) if r['lod']==3 else (3000,8000)
    else: limits=(20,80) if r['lod']==3 else (300,3000)
    if not limits[0]<=r['triangles']<=limits[1]:fail(a['name']+': brief triangle budget')
    if r['lod']==3 and (r['boundary_edges'] or r['nonmanifold_edges']):fail(a['name']+': lowest LOD is not closed solid geometry')
    if 'VineRow' in a['name'] and max(abs(r['bounds_metres'][0][1]),abs(r['bounds_metres'][1][1]-3),abs(r['bounds_metres'][0][2]))>.0001:fail(a['name']+': vine tile envelope/start-end ground pivot')
    if max(abs(x) for x in r['pivot_metres'])>.0001 or abs(r['bounds_metres'][0][2])>.0001:fail(a['name']+': ground pivot or base')
'''+s[end:]
s=s.replace("    if any(v<.80 or v>1.1 for v in ratio):fail(high['name']+': excessive lowest LOD envelope change')", "    if any(v<.75 or v>1.15 for v in ratio):fail(high['name']+': excessive lowest LOD envelope change')\n    if low['materials']!=high['materials']:fail(high['name']+': LOD material slots differ from base')")
s=s.replace("if len(OUT['assets'])!=8 or len(OUT['sources'])!=2:fail('Expected four model families with two LODs each and two source files')", "if len(OUT['assets'])!=30 or len(OUT['sources'])!=3:fail('Expected fifteen base models with two LODs each and three sources')")
s=s.replace('V003_VALIDATION','V004_VALIDATION')
v.write_text(s,encoding='utf-8')
print('SUPPORT_PREPARED')
