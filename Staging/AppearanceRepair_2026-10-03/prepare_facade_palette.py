"""Named native plaster/brick instances; preserve original materials."""
import unreal,json,os
from pathlib import Path
PROJECT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE=PROJECT/'Staging/AppearanceRepair_2026-10-03'
lease=(PROJECT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
assert 'OWNER=CODEX_APPEARANCE_MANAGER' in lease and f'assigned_editor_PID={os.getpid()}' in lease
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
root='/Game/Project/Shared/ModelBank/Materials/Appearance_20261003'
source=unreal.load_asset('/Game/Project/Shared/ModelBank/Materials/Instancing/Repair_20261003/MI_e4aa3c9e1bea')
assert isinstance(source,unreal.MaterialInstanceConstant)
values={
 'chalk_plaster':((.58,.55,.49),.18),
 'warm_sand_plaster':((.34,.28,.19),.28),
 'stone_gray_plaster':((.29,.30,.28),.24),
 'weathered_brick':((.30,.18,.10),.30),
}
result={'schema':'environmentpipeline.native_facade_palette.v1','variants':{},'saved_paths':[]}
for key,(rgb,intensity) in values.items():
    path=root+'/MI_Facade_'+key
    m=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else unreal.EditorAssetLibrary.duplicate_asset(source.get_path_name(),path)
    assert m
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(m,'Tint_Albedo',unreal.LinearColor(*rgb,1))
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(m,'Intencity_Tint_Albedo',intensity)
    if key=='weathered_brick':
        t=unreal.load_asset('/Game/ModularCourtyard/Textures/Wall/brick_plaster/T_BrickPlaster_BaseColor')
        assert isinstance(t,unreal.Texture2D)
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(m,'Albedo_01',t)
    unreal.MaterialEditingLibrary.update_material_instance(m)
    tint=unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(m,'Tint_Albedo')
    actual=unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(m,'Intencity_Tint_Albedo')
    assert max(abs(a-b) for a,b in zip((tint.r,tint.g,tint.b),rgb))<1e-6 and abs(actual-intensity)<1e-6
    assert unreal.EditorAssetLibrary.save_asset(path,only_if_is_dirty=True)
    result['variants'][key]={'material_path':m.get_path_name(),'Tint_Albedo':list(rgb)+[1],'Intencity_Tint_Albedo':actual,'Albedo_01':unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(m,'Albedo_01').get_path_name(),'native_parent':m.get_editor_property('parent').get_path_name(),'native_masks_and_normals_preserved':True,'visual_check':'pending_retained_area_inspection'}
    result['saved_paths'].append(path)
(HERE/'FACADE_MATERIALS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
