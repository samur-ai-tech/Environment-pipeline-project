"""Tune the saved project material copies; native source assets remain intact."""
import datetime, json, os, shutil
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native

PROJECT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE=PROJECT/'Staging/AppearanceRepair_2026-10-03'
lease=(PROJECT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
assert 'OWNER=CODEX_APPEARANCE_MANAGER' in lease and f'assigned_editor_PID={os.getpid()}' in lease
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert all(not r.tick_handle for r in native.ACTIVE)
assert all(not r.watch_tick and not r.save_tick for r in bank.ACTIVE)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
before=HERE/'BeforeTone'/stamp
before.mkdir(parents=True,exist_ok=False)
palettes={
 'chalk_plaster':((.50,.49,.45),.72),
 'stone_gray_plaster':((.12,.13,.14),.78),
 'warm_sand_plaster':((.31,.22,.12),.68),
 'weathered_brick':((.30,.095,.045),.58),
}
ground={'Sand_01':(.70,.66,.56),'Sand_02':(.64,.62,.57),
        'Dirt_Path':(.50,.45,.36),'Sand_Path':(.61,.53,.40)}
root='/Game/Project/Shared/ModelBank/Materials/Appearance_20261003'
surface='/Game/Project/Shared/SurfacePainting/Appearance_20261003/MI_SurfaceBank_Natural'
paths=[root+'/MI_Facade_'+key for key in palettes]+[surface]
for path in paths:
 file=PROJECT/'Content'/Path(path.removeprefix('/Game/')+'.uasset')
 assert file.is_file() and file.resolve().is_relative_to((PROJECT/'Content/Project/Shared').resolve())
 target=before/'Content'/file.relative_to(PROJECT/'Content');target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(file,target)
evidence={'schema':'environmentpipeline.retained_tone.v1','utc':stamp,
          'basis':'Actual native graph Lerp tint reachability and visibly pale repeated beige; project copies only',
          'palettes':{},'ground':{},'saved_paths':paths,'landscape_masks_changed':False,'lighting_changed':False}
lib=unreal.MaterialEditingLibrary
receipt_path=HERE/'FACADE_MATERIALS.json'
receipt=json.loads(receipt_path.read_text())
shutil.copy2(receipt_path,before/receipt_path.name)
for key,(rgb,alpha) in palettes.items():
 m=unreal.load_asset(root+'/MI_Facade_'+key);assert isinstance(m,unreal.MaterialInstanceConstant)
 old=lib.get_material_instance_vector_parameter_value(m,'Tint_Albedo')
 old_alpha=lib.get_material_instance_scalar_parameter_value(m,'Intencity_Tint_Albedo')
 lib.set_material_instance_vector_parameter_value(m,'Tint_Albedo',unreal.LinearColor(*rgb,1))
 lib.set_material_instance_scalar_parameter_value(m,'Intencity_Tint_Albedo',alpha)
 lib.update_material_instance(m)
 actual=lib.get_material_instance_vector_parameter_value(m,'Tint_Albedo')
 actual_alpha=lib.get_material_instance_scalar_parameter_value(m,'Intencity_Tint_Albedo')
 assert max(abs(a-b) for a,b in zip((actual.r,actual.g,actual.b),rgb))<1e-6 and abs(actual_alpha-alpha)<1e-6
 evidence['palettes'][key]={'before_rgb':[old.r,old.g,old.b],'before_alpha':old_alpha,'after_rgb':list(rgb),'after_alpha':actual_alpha}
 receipt['variants'][key].update(Tint_Albedo=list(rgb)+[1],Intencity_Tint_Albedo=actual_alpha,visual_check='retained_tone_live_review_pending')
m=unreal.load_asset(surface);assert isinstance(m,unreal.MaterialInstanceConstant)
for key,rgb in ground.items():
 old=lib.get_material_instance_vector_parameter_value(m,key+'_Tint')
 lib.set_material_instance_vector_parameter_value(m,key+'_Tint',unreal.LinearColor(*rgb,1))
 actual=lib.get_material_instance_vector_parameter_value(m,key+'_Tint')
 assert max(abs(a-b) for a,b in zip((actual.r,actual.g,actual.b),rgb))<1e-6
 evidence['ground'][key]={'before_rgb':[old.r,old.g,old.b],'after_rgb':list(rgb)}
lib.update_material_instance(m)
for path in paths:
 assert unreal.EditorAssetLibrary.save_asset(path,only_if_is_dirty=True),path
receipt_path.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
configs=[HERE/'STYLE_CONTRACT_PROPOSAL.json',
 PROJECT/'Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json',
 PROJECT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json']
for i,path in enumerate(configs):
 shutil.copy2(path,before/(str(i)+'_'+path.name))
 data=json.loads(path.read_text(encoding='utf-8-sig'))
 styles=data.get('building_style_variants') or data['building_assembly_contract']['building_style_variants']
 for row in styles['palettes']:
  rgb,alpha=palettes[row['id']]
  row['actual_native_values']=receipt['variants'][row['id']]
  row['proposed_vector_overrides_linear']['Tint_Albedo']=list(rgb)+[1]
  row['proposed_scalar_overrides']['Intencity_Tint_Albedo']=alpha
 path.write_text(json.dumps(data,indent=2),encoding='utf-8')
unreal.EditorLevelLibrary.editor_invalidate_viewports()
(HERE/('TONE_'+stamp+'.json')).write_text(json.dumps(evidence,indent=2),encoding='utf-8')
(HERE/'TONE_CURRENT.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
print(json.dumps(evidence))
