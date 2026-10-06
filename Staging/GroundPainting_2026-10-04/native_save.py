"""Save only reviewed area ground instance and exact original map package."""
import datetime,json,os
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve();HERE=ROOT/'Staging/GroundPainting_2026-10-04'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();named_map=world.get_outermost().get_path_name()
assignment=json.loads((HERE/'ASSIGNMENT.json').read_text());area=next(k for k,v in assignment['original_maps'].items() if v==named_map)
lease=[x for x in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1];fields=dict(t.split('=',1) for t in lease.split() if '=' in t)
assert fields['OWNER']=='CODEX_GROUND_PAINTING' and fields['activation']=='GROUND_AUTHORING' and fields['assigned_editor_PID']==str(os.getpid()) and fields['map']==named_map
child=unreal.load_asset(assignment['material_contract']['area_instances'][area]);packages=[child.get_outermost(),world.get_outermost()]
before={'content':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],'maps':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]}
assert set(before['content']).issubset({child.get_outermost().get_path_name()}) and set(before['maps']).issubset({named_map})
landscapes=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(a,unreal.Landscape)]
assert all(a.get_editor_property('landscape_material')==child for a in landscapes)
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
saved=unreal.EditorLoadingAndSavingUtils.save_packages(packages,False);assert saved
after={'content':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],'maps':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]}
assert not after['content'] and not after['maps']
result={'pid':os.getpid(),'area':area,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before':before,'after':after,'named_packages':[p.get_path_name() for p in packages],
 'landscape_packages':[{'actor':a.get_path_name(),'outermost':a.get_outermost().get_path_name()} for a in landscapes], 'external_dirty_landscape_packages':[], 'saved':saved,'ordinary_generation_run':False}
out=HERE/f'SAVE_{area}_PID{os.getpid()}.json';out.write_text(json.dumps(result,indent=2),encoding='utf-8');RESULT=result
