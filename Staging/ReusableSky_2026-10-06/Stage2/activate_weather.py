import json
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
old=next(a for a in actors if a.get_name()=='VolumetricCloud_0');c=old.get_component_by_class(unreal.VolumetricCloudComponent)
receipt={'actor':old.get_path_name(),'component':c.get_path_name(),'visible_before':c.is_visible(),'material':str(c.get_editor_property('material'))}
assert c.is_visible();(root/'CLOUD_RESTORATION.json').write_text(json.dumps(receipt,indent=2))
c.modify();c.set_editor_property('visible',False);c.set_visibility(False)
a=next(a for a in actors if a.get_name()=='BP_EnvironmentSky_C_0')
a.call_method('PresetPartlyCloudy')
mid=a.get_editor_property('CloudMID');cloud=a.get_component_by_class(unreal.VolumetricCloudComponent)
RESULT={'status':a.get_editor_property('Status'),'conflicts':a.get_editor_property('ConflictActors'),'preset':a.get_editor_property('WeatherPreset'),'amount':a.get_editor_property('CloudAmount'),'cloud_visible':cloud.is_visible(),'mid_path':mid.get_path_name() if mid else None,'mid_outer':mid.get_outer().get_path_name() if mid else None,'material':str(cloud.get_editor_property('material')),'mid_methods':[x for x in dir(mid) if 'parameter' in x] if mid else [],'dirty_content':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
(root/'ACTIVATION.json').write_text(json.dumps(RESULT,indent=2))
