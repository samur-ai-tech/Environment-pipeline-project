"""Read-only source renderer for fitted, deliberately non-distance previews."""
import sys, json, hashlib
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'Scripts'))
import build_strawberries_v005 as builder
report=json.loads((ROOT/'Reports/strawberries_v005.json').read_text())
files=[ROOT/'Blend/StrawberryBeds.blend']+sorted((ROOT/'Textures').glob('T_PazFarm_Strawberry_*_v005_*.png'))
def hashes():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blend/StrawberryBeds.blend'));rendered=[]
for rec in report['assets']:
 if '--caps-only' in sys.argv and rec['variant']!='End':continue
 ob=bpy.data.objects[rec['name']];builder.fitted_preview(ob,rec);rendered.append(rec['preview'])
 if rec['variant']=='A' and rec['lod_index']==0:
  builder.fitted_preview(ob,rec,close=True);builder.fitted_preview(ob,rec,side=True)
  rendered.extend(['Previews/'+rec['name']+'_PlantHoleClose.png','Previews/'+rec['name']+'_Side.png'])
after=hashes();receipt={'source_unchanged_during_render':before==after,'input_hashes_before':before,'input_hashes_after':after,'fitted_previews_not_actual_distance_tests':True,'images':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in rendered}}
suffix='cap_heroes' if '--caps-only' in sys.argv else 'heroes'
(ROOT/('Reports/strawberries_v005_'+suffix+'_receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print('FITTED_HERO_RENDER_COMPLETE',len(rendered),before==after,flush=True)
