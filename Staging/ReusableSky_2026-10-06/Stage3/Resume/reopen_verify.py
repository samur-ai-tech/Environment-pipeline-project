import json,os,collections,hashlib
from pathlib import Path
r=Path(unreal.Paths.project_dir()).resolve();stage=r/'Staging/ReusableSky_2026-10-06/Stage3';base='/Game/Project/Shared/Atmosphere/ReusableSky/'
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
dc=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()];dm=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()];assert not dc and not dm
saved=json.loads((stage/'Resume/SAVE_RECEIPT.json').read_text())
for p,h in saved['hashes'].items():assert hashlib.sha256((r/p).read_bytes()).hexdigest()==h,(p,h)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors();a=next(a for a in actors if a.get_name()=='BP_EnvironmentSky_C_0')
expected={'TimeOfDay':12.,'ManualSun':False,'CloudAmount':.55,'CloudSpeed':1.,'CloudDirection':45.,'HighQuality':False,'MoonEnabled':True,'MoonBrightness':.006,'MoonDiskBrightness':.04,'MoonPhase':.5,'StarsEnabled':True,'StarBrightness':.02,'NightSkyFill':.12,'AnimateTime':False,'TimePaused':False,'DayLengthMinutes':20.,'OverrideExposure':False}
got={k:a.get_editor_property(k) for k in expected}
for k,v in expected.items():assert got[k]==v or (isinstance(v,float) and abs(got[k]-v)<1e-6),(k,got[k],v)
assert a.get_editor_property('CloudMID') and a.get_editor_property('CelestialMID') and not a.is_actor_tick_enabled() and not a.get_editor_property('ConflictActors')
assert a.get_editor_property('CelestialDome').get_material(0)==a.get_editor_property('CelestialMID')
assert a.get_editor_property('MoonLight').get_editor_property('atmosphere_sun_light_index')==1
assert len(a.get_components_by_class(unreal.ActorComponent))==13 and len(actors)==122
m=unreal.load_asset(base+'M_EnvironmentCelestial');stats=unreal.MaterialEditingLibrary.get_statistics(m);assert stats.num_pixel_shader_instructions>0
RESULT={'pid':os.getpid(),'fresh_process':True,'world':unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(),'saved_hashes_match':True,'controls':got,'cloud_mid_reconstructed':a.get_editor_property('CloudMID').get_path_name(),'celestial_mid_reconstructed':a.get_editor_property('CelestialMID').get_path_name(),'material_stats':str(stats),'owned_components':13,'actor_count':122,'dirty_content':dc,'dirty_maps':dm,'static_tick_disabled':True,'mutations_before_readback':False}
(stage/'Resume/REOPEN_VERIFIED.json').write_text(json.dumps(RESULT,indent=2))
