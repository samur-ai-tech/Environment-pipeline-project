"""Read the owned r018 saved area; do not cook, bake, save, or change the editor."""
import datetime
import hashlib
import json
import math
import os
import re
from collections import Counter
from pathlib import Path

import unreal

PROJECT = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE = PROJECT / 'Staging/AppearanceRepair_2026-10-03'
REVISION = 'r018_retained_appearance'
PROFILE_PATHS = [PROJECT / 'Staging/ModelBank' / directory / 'AREA_PROFILE.json'
    for directory in ('PermanentIntegration_2026-10-02', 'GazaShujaiyaIntegration_2026-10-02')]


def _path(value):
    return value.get_path_name() if value is not None else None


def _new_receipt_path(name):
    target = HERE / name
    if target.exists():
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        target = target.with_name(target.stem + '_' + stamp + target.suffix)
    assert not target.exists(), 'Existing inspection receipt must remain preserved'
    return target


def _surface_normal_override_metadata(profile):
    """Allow only the owner's saved, provenance-checked two sand normal copies."""
    overrides = profile.get('surface_normal_overrides', {})
    assert isinstance(overrides, dict), 'surface_normal_overrides must be an explicit mapping'
    allowed = {
        name: (
            '/Game/MOUT_Arabian/Textures/Landscape/' + layer + '/T_' + layer + '_Normal.T_' + layer + '_Normal',
            '/Game/Project/Shared/SurfacePainting/Appearance_20261003/Textures/T_' + layer + '_Normal_GeoCity.T_' + layer + '_Normal_GeoCity')
        for name, layer in (('Sand_01_Normal', 'Sand_01'), ('Sand_02_Normal', 'Sand_02'))
    }
    assert not overrides or set(overrides) == set(allowed), 'Only the two paired sand normal overrides are allowed'
    if not overrides:
        return {}
    catalog = json.loads((PROJECT / 'Staging/ModelBank/SurfacePainting/surface_bank_v2.json').read_text(encoding='utf-8'))
    assert catalog.get('schema') == 'environmentpipeline.surface_bank.v2'
    canonical = {option['option_id']: option['native_textures']['normal'] for option in catalog['texture_options']}
    proofs = {}
    for name, entry in overrides.items():
        assert isinstance(entry, dict), 'Normal override requires explicit provenance: ' + name
        original, copy = allowed[name]
        assert entry.get('canonical_original') == original and entry.get('copy') == copy, 'Unexpected normal source/copy: ' + name
        assert canonical['mout.' + name.removesuffix('_Normal')] == original, 'Canonical surface catalog changed: ' + name
        original_sha = entry.get('original_sha256', '')
        receipt_sha = entry.get('receipt_sha256', '')
        assert re.fullmatch(r'[0-9a-f]{64}', original_sha) and re.fullmatch(r'[0-9a-f]{64}', receipt_sha), 'Normal provenance requires exact SHA256 values'
        proof_path = Path(entry.get('receipt_path', '')).resolve()
        assert proof_path.parent == HERE.resolve(), 'Normal provenance receipt must belong to this retained repair'
        assert proof_path.name.startswith('GROUND_SHADER_REPAIR_') and proof_path.suffix == '.json', 'Unexpected normal provenance receipt'
        proof_bytes = proof_path.read_bytes()
        assert hashlib.sha256(proof_bytes).hexdigest() == receipt_sha, 'Normal provenance receipt bytes changed'
        proof = json.loads(proof_bytes.decode('utf-8-sig'))
        assert proof.get('schema') == 'environmentpipeline.retained_ground_shader_repair.v1'
        assert proof.get('status') == 'named_assets_saved_graph_verified', 'Normal copy is not a completed named save'
        assert proof.get('instance') == profile['landscape_material'], 'Normal receipt belongs to another Landscape material'
        assert set(proof.get('normal_copies', {})) == set(allowed), 'Normal receipt must contain exactly the two approved copies'
        assert proof['normal_copies'][name] == copy, 'Normal receipt/copy mismatch'
        package = original.split('.')[0]
        assert proof.get('source_hashes_before', {}).get(package) == original_sha
        assert proof.get('source_hashes_after', {}).get(package) == original_sha, 'Original normal preservation was not proved'
        original_file = PROJECT / 'Content' / (package.removeprefix('/Game/') + '.uasset')
        assert hashlib.sha256(original_file.read_bytes()).hexdigest() == original_sha, 'Original native normal bytes changed'
        assert copy.split('.')[0] in proof.get('saved_paths', []), 'Normal copy was not named-saved'
        settings = proof.get('normal_settings_after', {}).get(name, {})
        assert settings.get('path') == copy and settings.get('srgb') is False
        assert 'TC_NORMALMAP' in settings.get('compression', ''), 'Saved normal copy compression is unproved'
        proofs[name] = dict(entry, canonical_catalog_preserved=True, original_bytes_unchanged=True,
                            saved_normal_settings_verified=True)
    return proofs


lease = (PROJECT / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]
assert 'OWNER=CODEX_APPEARANCE_MANAGER' in lease and f'assigned_editor_PID={os.getpid()}' in lease
api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
assert api.is_asset_cooking_paused(), 'Inspection requires paused official Engine cooking'
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world_path = world.get_outermost().get_path_name()
profiles = [(path, json.loads(path.read_text(encoding='utf-8'))) for path in PROFILE_PATHS]
profiles = [(path, profile) for path, profile in profiles if profile['map'] == world_path]
assert len(profiles) == 1, 'Current world must be one of the two assigned retained areas'
profile_path, profile = profiles[0]
area = json.loads(Path(profile['source']).read_text(encoding='utf-8'))['area_id']
assert area in ('GazaRimal', 'GazaShujaiya')
state = json.loads(Path(profile['workflow_receipt']).read_text(encoding='utf-8'))
receipt = json.loads(Path(profile['catalog_receipt']).read_text(encoding='utf-8'))
assert state['phase'] == 'baked_saved_verified' and state['generator_revision'] == REVISION
assert receipt['generator_revision'] == REVISION
records = receipt['nonbuilding_instances']
expected = Counter(record['path'] for record in records)
native_default_slots = {}


def _expected_slots(record):
    path = record['path']
    slots = record.get('material_slots') or profile.get('instance_materials', {}).get(path)
    if slots is None:
        if path not in native_default_slots:
            mesh = unreal.load_asset(path)
            assert isinstance(mesh, unreal.StaticMesh), 'Missing expected native mesh: ' + path
            native_default_slots[path] = [_path(slot.material_interface)
                for slot in mesh.get_editor_property('static_materials')]
        slots = native_default_slots[path]
    return tuple(slots)


expected_material_groups = Counter((record['path'], _expected_slots(record)) for record in records)
actual = Counter()
actual_material_groups = Counter()
native_positions = {}
components = []
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
for actor in actors:
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.static_mesh
        if not mesh or mesh.get_path_name() not in expected:
            continue
        path = mesh.get_path_name()
        instanced = isinstance(component, unreal.InstancedStaticMeshComponent)
        count = component.get_instance_count() if instanced else 1
        slots = tuple(_path(component.get_material(index)) for index in range(component.get_num_materials()))
        group = (path, slots)
        actual[path] += count
        actual_material_groups[group] += count
        positions = native_positions.setdefault(group, [])
        transforms = [component.get_instance_transform(index, world_space=True) for index in range(count)] if instanced else [component.get_world_transform()]
        for transform in transforms:
            point = transform.translation
            positions.append((point.x, point.y, point.z))
        components.append({'actor': actor.get_path_name(), 'mesh': path,
            'instances': count, 'materials': list(slots)})
assert actual == expected, {'missing': dict(expected - actual), 'extra': dict(actual - expected)}
assert actual_material_groups == expected_material_groups, 'Exact native mesh/full-material partitions do not match the recipe'
assert sum(actual.values()) == state['instance_count']

# Match every transferred anchor inside its exact mesh/material partition.
# This also detects a correct palette count applied to the wrong source building.
buckets = {}
for group, positions in native_positions.items():
    table = {}
    for position in positions:
        table.setdefault(tuple(math.floor(value) for value in position), []).append(position)
    buckets[group] = table
maximum_error = 0.0
for record in records:
    point = (record['P'][0] * 100, record['P'][2] * 100, record['P'][1] * 100)
    cell = tuple(math.floor(value) for value in point)
    group = (record['path'], _expected_slots(record))
    matches = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                key = (cell[0] + dx, cell[1] + dy, cell[2] + dz)
                matches.extend((math.dist(point, candidate), key, index)
                    for index, candidate in enumerate(buckets[group].get(key, [])))
    assert matches, 'Missing native anchor/material group: ' + record['placement_id']
    error, key, index = min(matches)
    assert error <= 0.1, (record['placement_id'], error)
    maximum_error = max(maximum_error, error)
    buckets[group][key].pop(index)
assert not any(positions for table in buckets.values() for positions in table.values())
actor_paths = {actor.get_path_name() for actor in actors}
assert set(state['baked_actor_paths']).issubset(actor_paths)
hdas = [actor for actor in actors if actor.get_class().get_name() == 'HoudiniAssetActor']
assert len(hdas) == 1 and not hdas[0].get_components_by_class(unreal.MeshComponent)
wrapper = unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None, hdas[0])
assert not wrapper.is_auto_cooking_enabled()
dirty_maps = [_path(package) for package in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
assert not dirty_maps
styles = receipt.get('building_style_variants', {})
surface_geometry = receipt.get('surface_geometry', {})
assert styles.get('family_building_counts') and styles.get('palette_building_counts'), 'Missing r018 actual style summary'
assert surface_geometry.get('source_coverage_preserved') is True, 'Missing r018 source surface coverage ledger'
result = {'world': world_path, 'pid': os.getpid(), 'generator_revision': REVISION,
    'profile': str(profile_path), 'native_count': sum(actual.values()),
    'native_mesh_counts': dict(actual), 'all_native_anchor_locations_match_recipe_within_1mm': True,
    'anchor_material_partition_verified': True, 'maximum_anchor_transfer_error_cm': maximum_error,
    'native_material_slots_verified': True,
    'native_mesh_material_counts': [{'mesh': group[0], 'material_slots': list(group[1]), 'instances': count}
        for group, count in sorted(actual_material_groups.items(), key=lambda item: str(item[0]))],
    'components': components, 'building_assembly': receipt.get('building_assembly'),
    'building_style_variants': styles, 'surface_geometry': surface_geometry,
    'terrain_support': receipt.get('terrain_support'), 'proxy_outputs': receipt.get('proxy_outputs'),
    'all_saved_baked_actors_present': True, 'saved_baked_actor_count': len(state['baked_actor_paths']),
    'cooked_mesh_components': 0, 'hda_actor_count': 1, 'auto_cooking_enabled': False,
    'dirty_maps': dirty_maps, 'landscape_count': sum(isinstance(actor, unreal.Landscape) for actor in actors),
    'landscape_readback': [], 'appearance_accepted': False}
assert result['landscape_count'] == 1
selected_layers = {'Dirt_Path', 'Sand_01', 'Sand_02', 'Sand_Path'}
native_layer_directories = {'Dirt_Path': 'Dirt_Path_01', 'Sand_01': 'Sand_01',
    'Sand_02': 'Sand_02', 'Sand_Path': 'Sand_Path_01'}
normal_override_metadata = _surface_normal_override_metadata(profile)
for landscape in [actor for actor in actors if isinstance(actor, unreal.Landscape)]:
    material = landscape.get_editor_property('landscape_material')
    assert _path(material) == profile['landscape_material']
    infos = []
    for name, settings in landscape.get_editor_property('target_layers').items():
        info = settings.get_editor_property('layer_info_obj')
        if info:
            infos.append({'target': str(name), 'layer': str(info.get_editor_property('layer_name')), 'info': _path(info)})
    assert {item['layer'] for item in infos} == selected_layers and len(infos) == 4
    assert {item['target'] for item in infos} == selected_layers
    assert all(item['info'].startswith(profile['root'] + '/') for item in infos), 'LayerInfo must belong to the retained area'
    target_names = [str(name) for name in landscape.get_target_layer_names()]
    assert set(target_names) == selected_layers
    resolved = {}
    for layer in sorted(selected_layers):
        directory = native_layer_directories[layer]
        for suffix in ('Albedo', 'Normal'):
            name = layer + '_' + suffix
            texture = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(material, name)
            assert texture is not None, 'Missing selected Landscape texture: ' + name
            texture_name = 'T_' + directory + '_' + suffix
            expected_texture = '/Game/MOUT_Arabian/Textures/Landscape/' + directory + '/' + texture_name + '.' + texture_name
            if name in normal_override_metadata:
                entry = normal_override_metadata[name]
                assert entry['canonical_original'] == expected_texture
                expected_texture = entry['copy']
                assert texture.get_editor_property('srgb') is False, 'Corrected normal must use linear sampling: ' + name
                assert texture.get_editor_property('compression_settings') == unreal.TextureCompressionSettings.TC_NORMALMAP, 'Corrected normal must use normal-map compression: ' + name
            assert _path(texture) == expected_texture, (name, _path(texture), expected_texture)
            resolved[name] = _path(texture)
    result['landscape_readback'].append({'material': _path(material),
        'valid_target_layer_names': target_names, 'assigned_layer_infos': infos,
        'resolved_selected_layer_texture_parameters': resolved,
        'eight_native_selected_layer_textures_verified': True,
        'surface_normal_overrides': normal_override_metadata,
        'canonical_surface_texture_catalog_preserved': True,
        'texture_query_scope': 'Shared base MI; no Landscape component static-weight permutation. Empty used-textures here is inconclusive.',
        'used_texture_paths': sorted(_path(texture) for texture in unreal.MaterialEditingLibrary.get_material_used_textures(material))})
assert api.is_asset_cooking_paused()
prefix = globals().get('READBACK_PREFIX', 'ACTUAL_')
target = _new_receipt_path(prefix + area + '.json')
target.write_text(json.dumps(result, indent=2), encoding='utf-8')
READBACK_RESULT = result
READBACK_TARGET_PATH = str(target)
print(json.dumps({'area': area, 'native_count': result['native_count'],
    'material_group_count': len(actual_material_groups),
    'building_style_variants': {'family_building_counts': styles['family_building_counts'],
        'palette_building_counts': styles['palette_building_counts']},
    'surface_geometry': {'road_provider': {key:(surface_geometry.get('road_provider') or {}).get(key)
        for key in ('provider','source_road_count','generated_road_count','vehicle_surfaces_suppressed')},
        'source_coverage_preserved': surface_geometry['source_coverage_preserved']}, 'receipt': str(target)}))
