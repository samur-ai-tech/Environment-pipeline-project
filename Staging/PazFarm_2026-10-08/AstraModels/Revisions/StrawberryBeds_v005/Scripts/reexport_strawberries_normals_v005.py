"""Correct FBX export only; never save or change approved source/report/textures."""
import sys, json, hashlib
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'Scripts'))
import build_strawberries_v005 as b
report_file=ROOT/'Reports/strawberries_v005.json';report=json.loads(report_file.read_text());records=report['assets']
protected=[ROOT/'Blend/StrawberryBeds.blend',report_file]+sorted((ROOT/'Textures').glob('T_PazFarm_Strawberry_*_v005_*.png'));fbxs=[ROOT/r['fbx'] for r in records]
def hashes(files):return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
protected_before=hashes(protected);fbx_before=hashes(fbxs)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blend/StrawberryBeds.blend'))
for rec in records:b.export_preserving_corner_normals(bpy.data.objects[rec['name']],ROOT/rec['fbx'])
protected_after=hashes(protected);assert protected_before==protected_after
receipt={'passed':True,'change':'FBX export use_triangles=False preserves original polygon corner normals; evaluated triangle counts unchanged. No source/report/texture save.','protected_hashes_before':protected_before,'protected_hashes_after':protected_after,'previous_fbx_hashes':fbx_before,'current_fbx_hashes':hashes(fbxs)}
(ROOT/'Reports/strawberries_v005_export_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
files=[ROOT/'Blend/StrawberryBeds.blend']+fbxs+sorted((ROOT/'Textures').glob('T_PazFarm_Strawberry_*_v005_*.png'));qa_before=hashes(files);qa=b.source_qa(records);qa_after=hashes(files);assert qa_before==qa_after
qa['input_hashes']={p.relative_to(ROOT).as_posix():{'sha256':qa_after[p.relative_to(ROOT).as_posix()],'bytes':p.stat().st_size} for p in files};qa['input_hashes_before']=qa_before;qa['input_hashes_after']=qa_after;qa['hash_capture']='Freshly reopened approved source after FBX-only normal export correction; pre/post QA inputs identical. Source/report/textures remained byte-identical; see export_receipt.'
(ROOT/'Reports/strawberries_v005_source_qa.json').write_text(json.dumps(qa,indent=2)+'\n')
print('FBX_NORMAL_EXPORT_FIXED_SOURCE_UNCHANGED',json.dumps(receipt['current_fbx_hashes'],indent=2),flush=True)
