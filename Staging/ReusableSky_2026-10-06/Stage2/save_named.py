import json,os,hashlib,collections
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
base='/Game/Project/Shared/Atmosphere/ReusableSky/'
bp=unreal.load_asset(base+'BP_EnvironmentSky');mi=unreal.load_asset(base+'MI_EnvironmentCloudDefaults')
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);actors=sub.get_all_level_actors();a=next(a for a in actors if a.get_name()=='BP_EnvironmentSky_C_0')
assert len(actors)==122
for k,v in json.loads((root/'PREFLIGHT.json').read_text())['public_controls'].items():
 if k not in ['ClockDisplay','RigEnabled']:a.set_editor_property(k,v)
a.call_method('PresetPartlyCloudy')
for k,v in {'CloudSpeed':1.0,'CloudDirection':45.0,'HighQuality':False}.items():a.set_editor_property(k,v)
assert a.get_editor_property('ClockDisplay')=='12:00' and a.get_editor_property('ConflictActors')==''
assert a.get_editor_property('Status')=='Active - Time and Location'
assert not a.get_editor_property('OverrideExposure')
assert not unreal.get_default_object(bp.generated_class()).get_editor_property('RigEnabled')
BP.compile_blueprint(bp,True)
# Preserve all preexisting lighting actors, their original intensities and fog settings.
for row in json.loads((root.parent/'SCENE_BEFORE.json').read_text())['actors']:
 old=unreal.find_object(None,row['path']);assert old
 for c in row['components']:
  obj=unreal.find_object(None,c['path']);assert obj
  if 'intensity' in c:assert str(obj.get_editor_property('intensity'))==c['intensity']
fog=next(x for x in actors if x.get_name()=='ExponentialHeightFog_0').get_component_by_class(unreal.ExponentialHeightFogComponent)
fog_before=json.loads((root/'CLOUD_STATE.json').read_text())[fog.get_path_name()]
assert str(fog.get_editor_property('fog_density'))==fog_before['fog_density']
assert str(fog.get_editor_property('visible'))==fog_before['visible']
cloud_original=unreal.find_object(None,json.loads((root/'CLOUD_RESTORATION.json').read_text())['component']);assert not cloud_original.is_visible()
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();map_path=world.get_outermost().get_path_name()
dc=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()];dm=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
assert set(dc).issubset({base+'BP_EnvironmentSky',base+'MI_EnvironmentCloudDefaults'}),dc
assert set(dm).issubset({map_path}),dm
assert unreal.EditorAssetLibrary.save_loaded_asset(mi,False)
assert unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
assert unreal.EditorLoadingAndSavingUtils.save_map(world,map_path)
dc=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()];dm=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
assert dc==[] and dm==[],(dc,dm)
registry=unreal.AssetRegistryHelpers.get_asset_registry()
deps={p:[str(x) for x in (registry.get_dependencies(p,unreal.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True)) or [])] for p in [base+'BP_EnvironmentSky',base+'MI_EnvironmentCloudDefaults']}
RESULT={'pid':os.getpid(),'saved':[base+'MI_EnvironmentCloudDefaults',base+'BP_EnvironmentSky',map_path],'dirty_content':dc,'dirty_maps':dm,'actor_count':len(actors),'clock':a.get_editor_property('ClockDisplay'),'weather_preset':a.get_editor_property('WeatherPreset'),'mid':a.get_editor_property('CloudMID').get_path_name(),'fog_unchanged':True,'previous_lighting_retained':True,'no_bank_saves':True,'dependencies':deps}
(root/'NAMED_SAVE.json').write_text(json.dumps(RESULT,indent=2))
sub.set_selected_level_actors([a])
