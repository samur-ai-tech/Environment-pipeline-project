import json,hashlib,os
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve();stage=r/'Staging/ReusableSky_2026-10-06/Stage3';base='/Game/Project/Shared/Atmosphere/ReusableSky/'
saved=json.loads((stage/'Resume/SAVE_RECEIPT.json').read_text());assignment=json.loads((stage/'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
for p,h in saved['hashes'].items():assert hashlib.sha256((r/p).read_bytes()).hexdigest()==h,'Saved package changed outside this reopen session'
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='BP_EnvironmentSky_C_0')
a.call_method('SetSkyTime',(12.,));a.call_method('PresetPartlyCloudy');a.set_editor_property('CloudSpeed',1.)
assert not a.get_editor_property('OverrideExposure') and not a.is_actor_tick_enabled()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
assert unreal.EditorLoadingAndSavingUtils.save_map(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),assignment['map'])
reg=unreal.AssetRegistryHelpers.get_asset_registry();opts=unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=False,include_soft_management_references=False,include_hard_management_references=False)
deps={p:[str(x) for x in reg.get_dependencies(p,opts)] for p in [base+'BP_EnvironmentSky',base+'M_EnvironmentCelestial',base+'MI_EnvironmentCloudDefaults']}
assert not any('/Areas/' in d or '/Temp/' in d for ds in deps.values() for d in ds)
assert base+'M_EnvironmentCelestial' in deps[base+'BP_EnvironmentSky'],deps
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages() and not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
RESULT={'pid':os.getpid(),'named_save':assignment['map'],'reason':'Restore original noon/PartlyCloudy/wind1 after fresh-process night verification','dependencies_after_reload':deps,'hashes':{p:hashlib.sha256((r/p).read_bytes()).hexdigest() for p in saved['hashes']},'blueprint_and_material_unchanged_since_reopen':True,'dirty_after':[]}
(stage/'Resume/FINAL_SAVE_RECEIPT.json').write_text(json.dumps(RESULT,indent=2))
