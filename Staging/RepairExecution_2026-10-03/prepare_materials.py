"""Retained instancing materials for supported native assembly/pole dependencies."""
import unreal, json, hashlib, os
from pathlib import Path

PROJECT = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE = PROJECT / 'Staging/RepairExecution_2026-10-03'
lease = (PROJECT / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
assert 'OWNER=CODEX_REPAIR_MANAGER' in lease and f'assigned_editor_PID={os.getpid()}' in lease
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
MESHES = [
    '/Game/ModularCourtyard/Meshes/SM_wall_windows_4x4_01',
    '/Game/ModularCourtyard/Meshes/SM_wall_4x4_01',
    '/Game/ModularCourtyard/Meshes/SM_wall_4x2_01',
    '/Game/ModularCourtyard/Meshes/SM_Wall_4x1_01',
    '/Game/ModularCourtyard/Meshes/SM_Steeldoor',
    '/Game/AssetsvilleTown/Meshes/StreetProps/SM_utility_pole_5',
]
ROOT = '/Game/Project/Shared/ModelBank/Materials/Instancing/Repair_20261003'
created, copies = {}, {}

def compatible_copy(source):
    if source.get_path_name() in copies:
        return copies[source.get_path_name()]
    is_material = isinstance(source, unreal.Material)
    assert is_material or isinstance(source, unreal.MaterialInstanceConstant), source
    target = ROOT + '/' + ('M_' if is_material else 'MI_') + hashlib.sha256(source.get_path_name().encode()).hexdigest()[:12]
    copy = unreal.load_asset(target) if unreal.EditorAssetLibrary.does_asset_exist(target) else unreal.EditorAssetLibrary.duplicate_asset(source.get_path_name(), target)
    assert copy and copy.get_path_name().startswith(ROOT + '/')
    copies[source.get_path_name()] = copy
    if is_material:
        copy.set_editor_property('used_with_instanced_static_meshes', True)
        copy.set_editor_property('automatically_set_usage_in_editor', False)
        unreal.MaterialEditingLibrary.recompile_material(copy)
    else:
        copy.set_editor_property('parent', compatible_copy(source.get_editor_property('parent')))
        unreal.MaterialEditingLibrary.update_material_instance(copy)
    created[target] = copy
    return copy

slots, measurements = {}, []
for mesh_path in MESHES:
    mesh = unreal.load_asset(mesh_path)
    assert isinstance(mesh, unreal.StaticMesh), mesh_path
    materials = [s.material_interface for s in mesh.get_editor_property('static_materials')]
    assert all(materials), mesh_path
    slots[mesh.get_path_name()] = [compatible_copy(m).get_path_name() for m in materials]
    bounds = mesh.get_bounds()
    measurements.append({'path': mesh.get_path_name(), 'min_cm': [bounds.origin.x-bounds.box_extent.x, bounds.origin.y-bounds.box_extent.y, bounds.origin.z-bounds.box_extent.z],
                         'max_cm': [bounds.origin.x+bounds.box_extent.x, bounds.origin.y+bounds.box_extent.y, bounds.origin.z+bounds.box_extent.z],
                         'original_materials': [m.get_path_name() for m in materials], 'instance_materials': slots[mesh.get_path_name()]})
assert created
for path in sorted(created):
    assert unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=True), path
result = {'schema': 'environmentpipeline.retained_assembly_materials.v1', 'mesh_slots': slots, 'measurements': measurements,
          'copies': {p: obj.get_path_name() for p, obj in copies.items()}, 'saved_paths': sorted(created),
          'scope': 'Two named areas; source-only route classifications retained; named/dependency holds excluded; original native meshes and materials untouched'}
(HERE/'INSTANCE_MATERIALS.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'saved_materials': len(created), 'meshes': len(slots), 'receipt': str(HERE/'INSTANCE_MATERIALS.json')}))
