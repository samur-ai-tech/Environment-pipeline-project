"""Preserve earlier farm staging/deliveries before FieldCrops v004 authoring."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FARM=ROOT.parents[2]
files=sorted(p for p in FARM.rglob('*') if p.is_file() and not p.is_relative_to(ROOT))
records=[{'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
target=ROOT/'Reports/ORIGINAL_INPUTS_SHA256.json'
assert not target.exists(),'Preserve original baseline'
target.write_text(json.dumps(records,indent=2),encoding='utf-8')
(ROOT/'ASSIGNMENT.json').write_text(json.dumps({'revision':'FieldCrops_v004','date':'2026-10-11','brief':str(FARM/'HANDOFF_ASTRA_FieldCrops_v004.md'),'write_root':str(ROOT),'scope':'Offline Blender: 3 grapevine tiles, 4 olives, 6 grass clumps, 2 grass patches, all with authored lowest LODs and distance evidence','native_actions_authorized':False,'references_sufficient':True},indent=2),encoding='utf-8')
print('ORIGINAL_FILES_BASELINED',len(records))
