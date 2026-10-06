import json,hashlib,os,time
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
r=Path(unreal.Paths.project_dir()).resolve();stage=r/'Staging/ReusableSky_2026-10-06/Stage3';base='/Game/Project/Shared/Atmosphere/ReusableSky/'
assignment=json.loads((stage/'ASSIGNMENT.json').read_text(encoding='utf-8-sig'));assert assignment['assigned_editor_PID']==os.getpid()
mapfile=r/'Content/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration.umap'
assert hashlib.sha256(mapfile.read_bytes()).hexdigest()==assignment['map_baseline_sha256'],'Map changed on disk; refuse stale overwrite'
assert not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors();a=next(a for a in actors if a.get_name()=='BP_EnvironmentSky_C_0')
a.call_method('SetTimeProgression',(False,False,20.));a.call_method('SetSkyTime',(12.,));a.call_method('PresetPartlyCloudy')
for k,v in {'CloudSpeed':1.,'MoonEnabled':True,'MoonBrightness':.006,'MoonDiskBrightness':.04,'MoonPhase':.5,'StarsEnabled':True,'StarBrightness':.02,'NightSkyFill':.12,'HighQuality':False}.items():a.set_editor_property(k,v)
assert not a.is_actor_tick_enabled() and not a.get_editor_property('OverrideExposure') and not a.get_editor_property('ConflictActors')
bp=unreal.load_asset(base+'BP_EnvironmentSky');BP.compile_blueprint(bp,True)
dc=[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()];dm=[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
assert set(dc)<=set([base+'BP_EnvironmentSky']) and set(dm)<=set([assignment['map']]),(dc,dm)
reg=unreal.AssetRegistryHelpers.get_asset_registry();opts=unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=False,include_soft_management_references=False,include_hard_management_references=False)
deps={p:[str(x) for x in reg.get_dependencies(p,opts)] for p in [base+'BP_EnvironmentSky',base+'M_EnvironmentCelestial',base+'MI_EnvironmentCloudDefaults']}
assert not any('/Areas/' in d or '/Temp/' in d for ds in deps.values() for d in ds),deps
assert unreal.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();assert unreal.EditorLoadingAndSavingUtils.save_map(world,assignment['map'])
dc_after=[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()];dm_after=[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()];assert not dc_after and not dm_after
files=[r/'Content/Project/Shared/Atmosphere/ReusableSky'/n for n in ['BP_EnvironmentSky.uasset','M_EnvironmentCelestial.uasset','MI_EnvironmentCloudDefaults.uasset']]+[mapfile]
RESULT={'pid':os.getpid(),'named_saves':[base+'BP_EnvironmentSky',assignment['map']],'material_already_saved_by_commandlet':True,'hashes':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'dirty_after':{'content':dc_after,'maps':dm_after},'dependencies':deps,'clock':a.get_editor_property('ClockDisplay'),'preset':a.get_editor_property('WeatherPreset'),'static_tick_disabled':not a.is_actor_tick_enabled(),'exposure_override':a.get_editor_property('OverrideExposure'),'actor_count':len(actors)}
(stage/'Resume/SAVE_RECEIPT.json').write_text(json.dumps(RESULT,indent=2))
