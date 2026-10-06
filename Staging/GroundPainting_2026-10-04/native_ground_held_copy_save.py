"""Save only the reviewed unused partial copy as a held checkpoint."""
import hashlib,json,os,types
from pathlib import Path
import unreal
root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
here=root/'Staging/GroundPainting_2026-10-04';rev=here/'Revision_2026-10-05'
f=here/'native_ground_texture_policy.py'
assert hashlib.sha256(f.read_bytes()).hexdigest()=='bdba22a3bcf801663788166649e3fd593704507f133995a1085ed0b37c2404b4'
p=types.ModuleType('held_save_definitions');p.__file__=str(f);exec(compile(f.read_bytes(),str(f),'exec'),p.__dict__)
h=p.load_helper();p.sole_editor();assert os.getpid()==ARGS['expected_pid']==32464
ready_file=rev/'GROUND_TEXTURE_PARTIAL_READY_PID32464.json'
assert h.sha(ready_file)=='3a0b0a4e958a44a2820d0a9f55b4a0bffd22df501c601edd6d48a6684ee1a3b3'
ready=json.loads(ready_file.read_text());review_file=Path(ARGS['review_receipt']).resolve(strict=True)
assert review_file.parent==rev and h.sha(review_file)==ARGS['review_receipt_sha256']
review=json.loads(review_file.read_text());assert review['status']=='APPROVED_NAMED_HELD_COPY_SAVE'
assignment=json.loads((here/'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
target='/Game/Project/Shared/SurfacePainting/Appearance_20261003/Textures/Resident4K/T_Sand_01_Albedo_GeoCityResident4K'
assert review['named_packages']==[target] and review['pid']==32464 and review['working_ground_use_authorized'] is False
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
assert world==ready['world'];master=unreal.load_asset(h.MASTER);copy=unreal.load_asset(target)
def snapshot():
 sources,actors=h.guard(assignment,world,True)
 return {'sources':sources,'scene':h.scene_state(actors),'nodes':{h.path(e):h.describe(master,e) for e in h.LIB.get_material_expressions(master)},'instances':{k:h.material_state(master,unreal.load_asset(k)) for k in ready['state']['instances']},'disk':{k:h.sha(k) for k in ready['state']['disk']},'cvars':{k:unreal.SystemLibrary.get_console_variable_string_value(k) for k in p.CVARS},'copy':p.texture_details(h,copy),'dirty':{'maps':sorted(h.path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),'content':sorted(h.path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}}
before=snapshot();assert before=={k:ready['state'][k] for k in before}
assert before['dirty']=={'maps':[],'content':[target]}
assert not h.package_file(target).exists()
copy_object=h.path(copy)
assert all(copy_object!=t for i in before['instances'].values() for t in i['textures'].values())
assert all(copy_object!=r['properties'].get('texture') for r in before['nodes'].values())
once=rev/'HELD_COPY_SAVE_ONCE_PID32464.json';assert not once.exists()
once.write_text(json.dumps({'package':target,'helper_sha256':h.sha(here/'native_ground_held_copy_save.py'),'review_sha256':h.sha(review_file)}))
assert unreal.EditorAssetLibrary.save_loaded_asset(copy,only_if_is_dirty=True)
after=snapshot();assert after['dirty']=={'maps':[],'content':[]}
assert all(before[k]==after[k] for k in before if k!='dirty')
assert h.package_file(target).exists()
out=rev/'HELD_UNUSED_MOUT_COPY_SAVED_PID32464.json'
out.write_text(json.dumps({'status':'SAVED_HELD_UNUSED_NOT_SELECTED','package':target,'pid':os.getpid(),'world':world,'file_sha256':h.sha(h.package_file(target)),'before':before,'after':after,'review_receipt_sha256':h.sha(review_file),'only_saved_package':target,'not_bound_or_catalogued':True,'latest_choice':'Use Epic StarterContent for ground; this prior partial copy is retained only as a held checkpoint.'},indent=2))
RESULT={'receipt':str(out),'sha256':h.sha(out),'dirty':after['dirty'],'saved_package':target,'file_sha256':h.sha(h.package_file(target))}
