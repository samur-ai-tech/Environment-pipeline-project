"""Baseline all earlier farm files before modelling; never alters inputs."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FARM=ROOT.parents[2]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
out=ROOT/'Reports/ORIGINAL_INPUTS_SHA256.json'
assert not out.exists(),'Do not replace the pre-work baseline'
files=sorted(p for p in FARM.rglob('*') if p.is_file() and not p.is_relative_to(ROOT))
records=[{'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]
out.write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
(ROOT/'ASSIGNMENT.json').write_text(json.dumps({'revision':'StrawberryBeds_v005','date':'2026-10-11','brief':str(FARM/'HANDOFF_ASTRA_StrawberryBeds_v005.md'),'write_root':str(ROOT),'scope':'Offline Blender only: three young strawberry bed tiles, authored lowest LODs, retained real photo references and distance evidence','native_actions_authorized':False,'modelling_requires_reference_review':True},indent=2)+'\n',encoding='utf-8')
print('ORIGINAL_FILES_BASELINED',len(records),sum(r['bytes'] for r in records),'bytes')
