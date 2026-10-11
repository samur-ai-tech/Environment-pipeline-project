"""Read-only baseline of original farm delivery and referenced distance captures."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FARM=ROOT.parents[2]
PROJECT=FARM.parents[1]
CAPTURES=PROJECT/'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/receipts/Captures'
names=['nv_pre_b_forest_oblique.png','nv_final_b_forest_oblique.png','lod_f_SM_green-tree01_400m.png','sb_b_straw_150m.png','sb_nn_b_straw_150m.png','sb_b_straw_60m.png']
files=[p for p in FARM.rglob('*') if p.is_file() and not p.is_relative_to(ROOT)]
files.extend(CAPTURES/n for n in names)
records=[{'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(set(files))]
target=ROOT/'Reports/ORIGINAL_INPUTS_SHA256.json'
if target.exists(): raise RuntimeError('Baseline exists; do not replace')
target.write_text(json.dumps(records,indent=2),encoding='utf-8')
(ROOT/'ASSIGNMENT.json').write_text(json.dumps({'revision':'VisualFix_v003','date':'2026-10-10','brief':str(FARM/'HANDOFF_ASTRA_VisualFix_v003.md'),'scope':'Offline Blender only: 3 Aleppo pine variants plus strawberry v003 with authored lowest LODs and distance previews','write_root':str(ROOT),'no_native_actions':True,'originals_preserved':True,'references_sufficient':True},indent=2),encoding='utf-8')
print('BASELINE_FILES',len(records))
