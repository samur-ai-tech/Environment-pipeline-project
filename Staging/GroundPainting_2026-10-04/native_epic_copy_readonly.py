"""Exact read-only owned-copy/source property comparison after a preserved stop."""
import datetime, hashlib, json, os, types
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
HERE=ROOT/'Staging/GroundPainting_2026-10-04'; REV=HERE/'Revision_2026-10-05'
FILE=HERE/'native_ground_epic_resident_recovery.py'
assert hashlib.sha256(FILE.read_bytes()).hexdigest()=='e97858becfa1df6a405297779e32d224c49d1c32034d0d5dcb66f7d7b690d4bf'
r=types.ModuleType('epic_copy_readonly_definitions');r.__file__=str(FILE)
exec(compile(FILE.read_bytes(),str(FILE),'exec'),r.__dict__);assert 'ARGS' not in r.__dict__
h,p,s,_,_=r.load_definitions();p.sole_editor();assert os.getpid()==ARGS['expected_pid']
assignment=json.loads((HERE/'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
sources,actors=h.guard(assignment,world,require_authoring=False)
reference=json.loads((REV/'EPIC_GROUND_verify_GazaShujaiya_r027_fresh_reopen_PID26820.json').read_text())
master=unreal.load_asset(h.MASTER)
assert {h.path(e):h.describe(master,e) for e in h.LIB.get_material_expressions(master)}==reference['nodes']
assert {k:h.material_state(master,unreal.load_asset(k)) for k in reference['instances']}==reference['instances']
assert h.scene_state(actors)==reference['scene']
epic=json.loads((REV/'EPIC_STARTER_GROUND_NATIVE_READONLY_PID32464.json').read_text())
assert all(h.sha(h.package_file(k))==v for k,v in epic['original_file_sha256'].items())
dirty=lambda:{'maps':sorted(h.path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),'content':sorted(h.path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
before=dirty();rows={}
for source,destination in r.COPIES.items():
    original=p.texture_details(h,unreal.load_asset(source))
    assert original['properties']==epic['textures'][source]['properties']
    exists=unreal.EditorAssetLibrary.does_asset_exist(destination)
    copied=p.texture_details(h,unreal.load_asset(destination)) if exists else None
    rows[destination]={'source':source,'original':original,'copied':copied,'disk':h.disk_state(h.package_file(destination)),
        'property_differences':{k:{'original':v,'copied':copied['properties'][k]} for k,v in original['properties'].items() if copied and v!=copied['properties'][k]}}
assert dirty()==before
out=REV/('EPIC_COPY_READ_ONLY_'+ARGS['label']+'_PID'+str(os.getpid())+'.json');assert not out.exists()
result={'status':'EPIC_COPY_PROPERTIES_READ_ONLY','pid':os.getpid(),'world':world,'native_mutation':False,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'copies':rows,'dirty':before,'sources':sources,'originals_preserved':True,'graph_instances_scene_preserved':True}
out.write_text(json.dumps(result,indent=2),encoding='utf-8')
RESULT={'receipt':str(out),'sha256':h.sha(out),'differences':{k:v['property_differences'] for k,v in rows.items()},'dirty':before}
