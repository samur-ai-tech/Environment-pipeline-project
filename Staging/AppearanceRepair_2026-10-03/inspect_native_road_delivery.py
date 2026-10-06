"""Owner-run, read-only saved/reopened native RoadBLD delivery inspection.

Import has no editor effects. Call inspect_delivery(profile_path, context=...)
after the owner has saved, or actually reopened, the named map. This helper
never loads a map, rebuilds roads, cooks Houdini, changes a binding, or saves an
Unreal package. A newly named JSON inspection receipt is its sole file output.
"""
import datetime
import hashlib
import json
import math
import os
import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace

try:
    import unreal
except ImportError:
    unreal = None

PROJECT = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE = PROJECT / 'Staging/AppearanceRepair_2026-10-03'
SCHEMA = 'environmentpipeline.roadbld_saved_inspection.v1'
PROFILES = tuple(PROJECT / 'Staging/ModelBank' / name / 'AREA_PROFILE.json'
    for name in ('PermanentIntegration_2026-10-02', 'GazaShujaiyaIntegration_2026-10-02'))


def _read(value):
    return json.loads(Path(value).read_text(encoding='utf-8-sig')) if isinstance(value, (str, Path)) else value


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode('utf-8')).hexdigest()


def _path(value):
    return value.get_path_name() if value is not None else None


def _field(value, name):
    """The installed AICallable discovery tools return AsyncValue JSON."""
    if isinstance(value, dict):
        normal = lambda item: re.sub('_', '', item).lower()
        names = {normal(name), normal(name[1:])} if name.startswith('b') and name[1:2].isupper() else {normal(name)}
        matches = [item for key, item in value.items() if normal(key) in names]
        assert len(matches) == 1, 'Missing/ambiguous discovery field: ' + name
        return matches[0]
    import geocity_roadbld_workflow as native
    return native._get(value, name)


def _unwrap(value):
    if hasattr(value, 'get_value_as_json_string'):
        assert value.is_complete and not value.error, 'Read-only native discovery is incomplete: ' + str(value.error)
        return json.loads(value.get_value_as_json_string())
    return value


def _discover(name, *args):
    import geocity_roadbld_workflow as native
    return _unwrap(native._tool('RoadBLDDiscoveryToolset', name, *args))


def _xyz(value):
    if isinstance(value, (list, tuple)):
        result = list(map(float, value))
    elif isinstance(value, dict):
        result = [float(_field(value, axis)) for axis in ('X', 'Y', 'Z')]
    else:
        result = [float(value.x), float(value.y), float(value.z)]
    assert len(result) == 3 and all(math.isfinite(item) for item in result), 'Invalid native vector'
    return result


def _unique_paths(rows, label):
    values = list(rows)
    assert values and len(values) == len(set(values)), 'Missing/duplicated ' + label
    assert all(isinstance(value, str) for value in values), 'Non-path ' + label
    return set(values)


def _source_ledger(contract, plan):
    ledger = contract.get('source_piece_ledger')
    delivery = contract['source_delivery']
    if ledger is None:
        ledger = []
        for row in delivery:
            assert len(row['piece_ids']) == len(row['road_actor_paths'])
            ledger.extend({'source_osm_id': str(row['source_osm_id']), 'piece_id': piece,
                'road_actor_path': path} for piece, path in zip(row['piece_ids'], row['road_actor_paths']))
    expected = {row['piece_id']: str(row['source_osm_id']) for row in plan['roads']}
    assert len(ledger) == len(expected) and len({row['piece_id'] for row in ledger}) == len(expected)
    assert {row['piece_id']: str(row['source_osm_id']) for row in ledger} == expected, 'Original geographic piece/source coverage differs'
    full_plan = {row['piece_id']: row for row in plan['roads']}
    for row in ledger:
        assert all(row.get(key) == value for key, value in full_plan[row['piece_id']].items()), 'Retained source-piece fields differ from the unchanged geographic export'
    assert len({row['road_actor_path'] for row in ledger}) == len(ledger)
    assert {row['road_actor_path'] for row in ledger} == _unique_paths(contract['road_actor_paths'], 'original road actors')
    rebuilt = []
    for source_id in plan['drivable_source_ids']:
        rows = sorted((row for row in ledger if str(row['source_osm_id']) == str(source_id)), key=lambda row: row['piece_id'])
        rebuilt.append({'source_osm_id': str(source_id), 'piece_ids': [row['piece_id'] for row in rows],
            'road_actor_paths': [row['road_actor_path'] for row in rows]})
    normalized = [{**row, 'source_osm_id': str(row['source_osm_id'])} for row in delivery]
    assert sorted(normalized, key=lambda row: row['source_osm_id']) == sorted(rebuilt, key=lambda row: row['source_osm_id']), 'Completed source-delivery ledger differs'
    return ledger


def _assert_transform(actual, expected):
    assert set(actual) == set(expected), 'Incomplete native transform snapshot'
    for key in ('translation_cm', 'scale3d', 'rotation_xyzw'):
        assert len(actual[key]) == len(expected[key]) and all(abs(float(a) - float(b)) <= 1e-6
            for a, b in zip(actual[key], expected[key])), 'Native component transform differs: ' + key


def _component_snapshot(component, actor, clip):
    assert component.get_class().get_name() == 'StaticMeshComponent', 'Exact retained binding inspection requires measured StaticMeshComponent'
    mesh = component.static_mesh
    assert isinstance(mesh, unreal.StaticMesh), 'Missing native retained mesh'
    dynamic = clip._copy_static(mesh)
    points, triangles = clip._read_geometry(dynamic, component.get_world_transform())
    return {'actor': _path(actor), 'component': _path(component), 'mesh': _path(mesh),
        'material_slots': clip._materials(component), 'component_world_transform': clip._transform(component.get_world_transform()),
        'collision': clip._collision(component, mesh), 'attributes': clip._mesh_attributes(dynamic),
        'asset_material_slots': [_path(slot.material_interface) for slot in mesh.get_editor_property('static_materials')],
        'asset_material_slot_names': [str(slot.material_slot_name) for slot in mesh.get_editor_property('static_materials')],
        'world_triangle_geometry_sha256': clip._sha({'vertices_cm': points, 'triangles': triangles}),
        'triangle_count': len(triangles)}


def _check_binding(expected, actual, clipped=False):
    assert expected['actor'] == actual['actor'] and expected['component'] == actual['component'], 'Native component ownership differs'
    wanted_mesh = expected.get('clipped_mesh') or expected.get('mesh') or expected.get('static_mesh')
    assert wanted_mesh == actual['mesh'], 'Native PostLoad/rebuild changed the retained mesh binding: ' + actual['component']
    assert expected['material_slots'] == actual['material_slots'], 'Full ordered native material slots differ'
    _assert_transform(actual['component_world_transform'], expected['component_world_transform'])
    assert expected['collision'] == actual['collision'], 'Exact native collision policy differs'
    wanted_hash = expected.get('clipped_world_triangle_geometry_sha256') or expected.get('world_triangle_geometry_sha256')
    assert wanted_hash and wanted_hash == actual['world_triangle_geometry_sha256'], 'Actual retained native triangle hash differs'
    attributes = expected.get('attributes_after') if clipped else expected.get('attributes')
    if attributes is not None:
        assert attributes == actual['attributes'], 'Native UV/normal/material-ID attributes differ'
    if clipped:
        assert expected['source_asset_material_slots'] == actual['asset_material_slots'], 'Clipped asset material slots differ from native source'
        assert expected['source_asset_material_slot_names'] == actual['asset_material_slot_names'], 'Clipped native slot names differ'


def _measure_all(actors, geometry_paths, plan, clip, bounded, accepted_empty_geometry=()):
    """Independently read actual components, not the clipping input/receipt."""
    import geocity_roadbld_workflow as native
    protections = clip.prepare_protections(plan)
    options = unreal.GeometryScriptCopyMeshFromComponentOptions()
    native._set(options, 'bWantNormals', False)
    native._set(options, 'bWantTangents', False)
    totals = {'component_count': 0, 'instance_geometry_count': 0, 'triangle_count': 0,
        'summed_projected_triangle_area_m2': 0.0, 'max_area_escape_cm': 0.0}
    overlaps, by_actor, components = {}, {}, {}
    empty_by_actor = {row['geometry_actor_path']: row for row in accepted_empty_geometry}
    assert len(empty_by_actor) == len(accepted_empty_geometry) and set(empty_by_actor).issubset(geometry_paths)
    allowed_null, seen_null = {}, set()
    for path, row in empty_by_actor.items():
        assert row['passed'] and row['automatic_empty_placeholder'] and row['replacement_proof']
        null_paths = row['null_component_paths']
        assert null_paths and len(null_paths) == len(set(null_paths))
        for component_path in null_paths:
            assert component_path.startswith(path + '.') and component_path not in allowed_null
            allowed_null[component_path] = path
    for actor in actors:
        bounded()
        patch_type = getattr(unreal, 'LandscapePatchComponent', None)
        if patch_type:
            assert all(not item.is_enabled() for item in actor.get_components_by_class(patch_type)), 'Native Landscape patch can change authoritative terrain'
        for component in actor.get_components_by_class(unreal.MeshComponent):
            bounded()
            key = _path(component)
            assert key not in components, 'Repeated actual native component'
            if component.get_class().get_name() == 'StaticMeshComponent' and component.static_mesh is None:
                assert allowed_null.get(key) == _path(actor), 'Unproven or changed null native component: ' + key
                seen_null.add(key)
                continue
            instanced = isinstance(component, unreal.InstancedStaticMeshComponent)
            transforms = [component.get_instance_transform(index, world_space=True) for index in range(component.get_instance_count())] if instanced else [unreal.Transform()]
            if not transforms:
                continue
            dynamic, unused, outcome = unreal.GeometryScript_SceneUtils.copy_mesh_from_component(
                component, unreal.DynamicMesh(), options, not instanced)
            clip._success(outcome)
            if not dynamic.get_triangle_count():
                continue
            assert component.get_num_materials() and all(component.get_material(index)
                for index in range(component.get_num_materials())), 'Missing actual native material'
            totals['component_count'] += 1
            components[key] = (actor, component)
            for transform in transforms:
                bounded()
                assert transform is not None, 'Missing native instance transform'
                points, triangles = clip._read_geometry(dynamic, transform)
                fit = clip.measure_conflicts(points, triangles, protections,
                    float(plan['settings']['area_boundary_tolerance_cm']), 0.0, bounded)
                totals['instance_geometry_count'] += 1
                totals['triangle_count'] += len(triangles)
                totals['summed_projected_triangle_area_m2'] += fit['summed_projected_triangle_area_m2']
                totals['max_area_escape_cm'] = max(totals['max_area_escape_cm'], fit['max_area_escape_cm'])
                by_actor[_path(actor)] = by_actor.get(_path(actor), 0) + len(triangles)
                for source_id, value in fit['overlap_m2_by_pad'].items():
                    overlaps[source_id] = overlaps.get(source_id, 0.0) + value
    failed = {key: value for key, value in overlaps.items() if value > float(plan['settings']['building_overlap_tolerance_m2'])}
    totals.update(schema='environmentpipeline.roadbld_native_mesh_fit.v1',
        basis='all actual native component triangles copied in world space; every ISM world transform; summed projected pad intersections',
        protected_footprints_sha256=plan['protected_footprint_proof']['footprints_sha256'],
        protected_pad_count=plan['protected_footprint_proof']['source_pad_count'], overlap_pad_count=len(failed),
        summed_triangle_intersection_m2_by_pad=failed, all_positive_intersections_m2_by_pad=overlaps,
        passed=not failed and totals['max_area_escape_cm'] <= float(plan['settings']['area_boundary_tolerance_cm'])
            and totals['triangle_count'] > 0 and totals['summed_projected_triangle_area_m2'] > 0)
    assert seen_null == set(allowed_null), 'Exact proven native null component ledger differs'
    assert all(by_actor.get(path, 0) > 0 or path in empty_by_actor for path in geometry_paths), 'Retained RoadGeo actor has no actual native triangles or complete merged replacement proof'
    assert all(by_actor.get(path, 0) == 0 for path in empty_by_actor), 'A proven automatic empty RoadGeo gained unexpected geometry'
    totals['automatic_empty_geometry_actor_paths'] = sorted(empty_by_actor)
    totals['null_component_paths'] = sorted(seen_null)
    assert totals['passed'], 'Aggregate actual native boundary/protected-pad fit failed: ' + json.dumps(totals)
    return totals, components


def _inspect_grounding(contract, plan, ledger, derived, actual, geo_paths, network, world, bounded):
    """Fresh saved Landscape and bound mesh proof; no cached cook sampler."""
    expected = contract.get('native_grounding_validation')
    preparation = contract.get('grounding_report')
    if expected is None and preparation is None:
        return None
    import geocity_roadbld_grounding as grounding
    from geocity_roadbld_landscape import LandscapeSampler
    assert isinstance(expected, dict) and isinstance(preparation, dict), 'Saved grounding requires preparation and final physical validation'
    assert expected['schema'] == preparation['schema'] == grounding.SCHEMA
    assert expected['passed'] and preparation['passed']
    for key in ('source_sha256', 'centreline_sha256'):
        assert expected[key] == preparation[key] == plan[key], 'Saved grounding provenance differs: ' + key
    repair = contract.get('junction_repair') or contract.get('junction_repair_report')
    repair = json.loads(json.dumps(_read(repair))) if repair else None
    def read_guard():
        bounded()
        return world
    clipping = contract.get('clipping_report')
    assert isinstance(clipping, dict), 'Saved grounding requires the retained immutable clipping report'
    proxy = SimpleNamespace(plan=plan, guard=read_guard, network=network,
        state={'junction_repair': repair, 'clipping_report': clipping, 'grounding_report': preparation},
        junction_repair=repair, clipping_report=clipping, grounding_report=preparation,
        roads=[actual[row['road_actor_path']] for row in ledger],
        derived_junction_roads=[actual[row['road_actor_path']] for row in derived])
    sampler = LandscapeSampler(proxy, saved=True)
    proof = grounding.verify_native_delivery(proxy, sampler,
        actors=[actual[path] for path in sorted(geo_paths)], landscape_actor_path=sampler.path)
    # Elapsed time is diagnostic only. All physical sample/geometry/material
    # hashes, source/connector provenance, exact nulls and the Landscape actor
    # must match the final validation retained by commit before its named save.
    for key in ('schema', 'basis', 'source_sha256', 'centreline_sha256', 'source_road_count', 'source_piece_count',
                'source_roads', 'automatic_empty_geometry', 'max_surface_height_error_cm',
                'landscape_actor_path', 'component_geometry', 'passed'):
        assert key in expected and proof[key] == expected[key], 'Saved native grounding readback differs: ' + key
    # New final contracts retain exact complementary source partition and
    # exclusion/continuity accounting. Compare every such recorded field;
    # historical zero-exclusion Rimal keeps the unchanged core checks above.
    for key in ('source_partition', 'clipping_fit_proof', 'physical_surface_continuous',
                'source_coverage_accounted', 'protected_excluded_sample_count',
                'excluded_length_cm', 'analytic_exterior_triangle_coverage_verified',
                'outside_uncovered_length_cm', 'physical_sample_count', 'unresolved_source_conflicts'):
        if key in expected:
            assert key in proof and proof[key] == expected[key], 'Saved source partition readback differs: ' + key
    assert {row['component_path'] for row in preparation['components']} == {
        row['component_path'] for row in proof['component_geometry']}, 'Saved grounding component coverage differs'
    return proof


def inspect_delivery(profile_path=None, context='saved_readback', receipt_path=None, max_seconds=180.0):
    """Root-only call. context names an already completed save/reopen action.

    A reopen_readback result proves exact bindings in the currently reopened
    world; it does not assert a process restart, another regeneration, or visual
    acceptance. No editor mutations or native authoring functions are invoked.
    """
    assert unreal is not None, 'Owner must run this inspection inside the retained editor'
    assert context in ('saved_readback', 'reopen_readback') and 0 < max_seconds <= 300
    began = time.monotonic()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    lease_path = PROJECT / 'Staging/ModelBank/EDITOR_OWNER.txt'
    lease = lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]
    assert 'OWNER=CODEX_APPEARANCE_MANAGER' in lease and ('assigned_editor_PID=' + str(os.getpid())) in lease
    api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
    assert api.is_asset_cooking_paused(), 'Saved inspection requires paused official Engine cooking'
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    world_path = _path(world.get_outermost())
    if profile_path is None:
        matches = [(path, _read(path)) for path in PROFILES if _read(path)['map'] == world_path]
        assert len(matches) == 1, 'Current world is not exactly one assigned retained area'
        profile_path, profile = matches[0]
    else:
        profile_path = Path(profile_path).resolve()
        assert profile_path in tuple(path.resolve() for path in PROFILES), 'Out-of-scope profile'
        profile = _read(profile_path)
    assert profile['map'] == world_path, 'Inspector does not open or switch maps'
    source = _read(profile['source'])
    area = source['area_id']
    assert area in ('GazaRimal', 'GazaShujaiya')
    destination = Path(receipt_path or HERE / ('ROADBLD_INSPECT_' + area + '_' + context + '_' + stamp + '.json')).resolve()
    assert destination.is_relative_to(HERE.resolve()) and not destination.exists(), 'Inspection receipts are named and immutable'
    report = {'schema': SCHEMA, 'utc': stamp, 'context': context, 'area_id': area,
        'named_map': world_path, 'pid': os.getpid(), 'profile': str(profile_path), 'status': 'checking',
        'editor_mutations': 0, 'native_rebuild_performed': False, 'houdini_cook_performed': False,
        'map_save_performed': False, 'map_load_performed': False, 'process_restart_verified': False,
        'visual_acceptance': False, 'receipt': str(destination)}

    def bounded():
        assert time.monotonic() - began <= max_seconds, 'Bounded native delivery inspection timed out'
        assert lease_path.read_text(encoding='utf-8-sig').splitlines()[-1] == lease, 'Editor ownership changed during inspection'
        assert api.is_asset_cooking_paused() and _path(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost()) == world_path

    try:
        if str(PROJECT / 'Content/Python') not in sys.path:
            sys.path.insert(0, str(PROJECT / 'Content/Python'))
        import geocity_roadbld_workflow as native
        import geocity_roadbld_clip as clip
        contract = _read(profile['road_provider_contract'])
        assert profile.get('road_provider') == 'RoadBLD' and contract['provider'] == 'RoadBLD'
        assert contract['schema'] == native.DELIVERY_SCHEMA and contract['coordinate_frame'] == native.FRAME
        assert contract['saved'] is True and contract['phase'] == 'native_generated_saved_verified', 'Delivery is not saved'
        assert contract['area_id'] == area and contract['named_map'] == world_path and contract['hda_vehicle_surfaces_suppressed'] is True
        settings = contract.get('adapter_settings') or profile.get('roadbld_workflow', {}).get('adapter_settings')
        assert settings, 'Saved delivery must retain the exact adapter settings'
        plan = native.plan(profile, settings=settings)
        for key in ('area_id', 'named_map', 'source_sha256', 'centreline_sha256', 'source_road_count', 'source_piece_count'):
            assert contract[key] == plan[key], 'Current source/delivery differs: ' + key
        assert sorted(contract['drivable_source_ids']) == sorted(plan['drivable_source_ids'])
        assert sorted(contract['generated_piece_ids']) == sorted(plan['drivable_piece_ids'])
        assert contract['generated_road_count'] == plan['source_piece_count'], 'Derived junction roads cannot replace/count as geographic roads'
        assert contract['protected_footprint_proof'] == plan['protected_footprint_proof'], 'Actual source pads or assembly footprint proof changed'
        report.update(delivery_sha256=_sha(contract), source_sha256=plan['source_sha256'], centreline_sha256=plan['centreline_sha256'],
            protected_footprints_sha256=plan['protected_footprint_proof']['footprints_sha256'])
        catalog = _read(profile['catalog_receipt'])
        hda_provider = catalog['surface_geometry']['road_provider']
        assert hda_provider['provider'] == 'RoadBLD' and hda_provider['vehicle_surfaces_suppressed'] is True
        for key in ('area_id', 'source_sha256', 'centreline_sha256', 'drivable_source_ids', 'source_road_count', 'generated_road_count', 'generated_piece_ids'):
            assert hda_provider[key] == contract[key], 'Saved HDA/native provider disagreement: ' + key
        ledger = _source_ledger(contract, plan)
        by_piece = {row['piece_id']: row for row in ledger}
        plan_by_piece = {row['piece_id']: row for row in plan['roads']}
        report['actual_original_source_fields_sha256'] = _sha([{key: row[key] for key in plan_by_piece[row['piece_id']]}
            for row in sorted(ledger, key=lambda row: row['piece_id'])])
        originals = {row['road_actor_path'] for row in ledger}
        derived = contract.get('derived_junction_roads', [])
        derived_paths = {row['road_actor_path'] for row in derived}
        assert len(derived_paths) == len(derived) and not originals.intersection(derived_paths)
        assert len({row['derived_id'] for row in derived}) == len(derived)
        if derived:
            assert contract.get('derived_road_count', contract.get('derived_junction_road_count')) == len(derived)
            assert contract.get('total_native_road_count', contract.get('actual_native_road_actor_count')) == len(originals) + len(derived)
        road_paths = originals | derived_paths
        geo_paths = _unique_paths(contract['geometry_actor_paths'], 'generated geometry actors')
        owned_paths = _unique_paths(contract['owned_actor_paths'], 'owned actors')
        network_path = contract['network_actor_path']
        assert {network_path}.union(road_paths, geo_paths).issubset(owned_paths)
        assert all(path.startswith(world_path + '.') for path in owned_paths), 'Native ownership crosses named map'
        all_actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
        actual = {_path(actor): actor for actor in all_actors}
        assert owned_paths.issubset(actual), 'Saved native actor paths are missing'
        tags = {path: {str(value) for value in actor.get_editor_property('tags')} for path, actor in actual.items()}
        owned_tags = {native.OWNER, 'GeoCityArea_' + area, 'GeoCityRevision_' + contract['revision']}
        assert all(owned_tags.issubset(tags[path]) for path in owned_paths), 'Retained actor ownership/revision tags differ'
        tagged = {path for path in actual if native.OWNER in tags[path] and 'GeoCityArea_' + area in tags[path]}
        assert tagged == owned_paths, 'Previous or unreceipted native generation remains'
        assert {_path(actor) for actor in all_actors if isinstance(actor, unreal.DynamicRoadNetwork)} == {network_path}, 'Extra/stale native network remains in named area'
        assert {_path(actor) for actor in all_actors if isinstance(actor, unreal.DynamicRoad)} == road_paths, 'Extra/missing native road actor'
        assert {_path(actor) for actor in all_actors if isinstance(actor, unreal.RoadGeo)} == geo_paths, 'Extra/missing native RoadGeo actor'
        network = actual[network_path]
        assert not network.is_road_network_stale(), 'Retained native network is stale'
        infos = list(_discover('DescribeNetwork', network, len(road_paths) + 1))
        assert len(infos) == 1
        info = infos[0]
        assert _field(_field(info, 'Actor'), 'RefPath') == network_path
        assert not _field(info, 'bStale') and not _field(info, 'bRebuildInProgress')
        assert int(_field(info, 'RoadCount')) == len(road_paths)
        assert {_field(_field(row, 'Actor'), 'RefPath') for row in _field(info, 'Roads')} == road_paths
        junction_report = contract.get('junction_repair_report') or contract.get('junction_repair')
        junction_proxy = None
        if junction_report:
            import geocity_roadbld_junctions as junctions
            junction_report = json.loads(json.dumps(_read(junction_report)))
            assert junction_report['schema'] == 'environmentpipeline.roadbld_junction_repair.v1'
            assert junction_report['global_cdo_limit_restored'] is True
            assert set(junction_report['sourcecontrols_trimproof']) == originals
            assert set(junction_report['original_source_actor_paths']) == originals
            assert junction_report['source_piece_count'] == len(originals)
            assert junction_report['derived_junction_roads'] == derived
            junction_proxy = SimpleNamespace(plan=plan, guard=bounded, network=network,
                state={}, roads=[actual[row['road_actor_path']] for row in ledger],
                derived_junction_roads=[actual[row['road_actor_path']] for row in derived])
        assert not derived or junction_proxy is not None, 'Native junction connectors need the explicit complete source-trim proof'
        control_records, max_error = [], 0.0
        for row in ledger:
            bounded()
            path, piece = row['road_actor_path'], row['piece_id']
            assert {'GeoCitySource_' + str(row['source_osm_id']), 'GeoCityPiece_' + piece}.issubset(tags[path])
            road = actual[path]
            data = _discover('DescribeRoad', road)
            assert _field(_field(data, 'Actor'), 'RefPath') == path and _field(_field(data, 'Network'), 'RefPath') == network_path
            points = [_xyz(_field(point, 'Location')) for point in _field(data, 'ControlPoints')]
            expected = [[point[0] * 100, point[2] * 100, point[1] * 100 + plan['settings']['surface_clearance_cm']] for point in plan_by_piece[piece]['points_m']]
            original_expected = expected
            trim_proof = None
            if junction_proxy is not None:
                trim_proof = junction_report['sourcecontrols_trimproof'][path]
                source_row = plan_by_piece[piece]
                assert trim_proof['original_source_vertex_export_indices'] == source_row['original_point_indices']
                assert trim_proof['boundary_export_indices'] == source_row['boundary_point_indices']
                assert trim_proof['protected_indices'] == sorted(set(source_row['original_point_indices'] + source_row['boundary_point_indices']))
                for trim in trim_proof['end_trims']:
                    assert math.isfinite(float(trim['pullback_cm'])) and 0 < float(trim['pullback_cm']) <= 200.0
                    radius = float(trim['turn_radius_cm'])
                    assert math.isfinite(radius) and 50.0 <= radius <= 100.0 and trim['partner_actor_path'] in originals
                    assert trim['source_endpoint_world_cm'] == original_expected[0 if trim['start'] else -1]
                # Both installed verifier functions were read: they only read
                # native controls/properties/samples. Report metric writes stay
                # inside the private JSON copy, never the saved contract.
                junctions.verify_source_road(junction_proxy, road, source_row, junction_report)
                expected = trim_proof['expected_control_points_world_cm']
            assert len(points) == len(expected), 'Native original geographic vertex count differs'
            error = max(math.dist(a, b) for a, b in zip(points, expected))
            assert error <= plan['settings']['control_point_tolerance_cm'], 'Original source control moved: ' + piece
            max_error = max(max_error, error)
            width = plan_by_piece[piece]['width_m'] * 100
            lanes = list(_field(data, 'LeftLanes')) + list(_field(data, 'RightLanes'))
            assert all(abs(sum(float(_field(lane, field)) for lane in lanes) - width) <= 0.1 for field in ('WidthAtStart', 'WidthAtEnd'))
            assert all(not native._get(road, field) for field in ('bEnableLandscapeSplineMirroring', 'bConformToLandscape', 'bEnableLandscapePaint'))
            control_records.append({**row, 'original_export_control_points_world_cm': original_expected,
                'explicit_native_trim_proof': trim_proof, 'actual_control_points_world_cm': points,
                'actual_control_points_sha256': _sha(points), 'max_error_cm': error})
        for row in derived:
            bounded()
            assert len(row['parent_piece_ids']) == 2 and set(row['parent_piece_ids']).issubset(by_piece)
            assert set(row['parent_source_osm_ids']) == {str(by_piece[piece]['source_osm_id']) for piece in row['parent_piece_ids']}
            assert set(row['parent_road_actor_paths']) == {by_piece[piece]['road_actor_path'] for piece in row['parent_piece_ids']}
            assert row['derived_id'].startswith('junction:'), 'Unrecognized derived road provenance'
            assert {'GeoCityDerivedJunction', 'GeoCityDerived_' + row['derived_id']}.issubset(tags[row['road_actor_path']])
            radius = float(row['turn_radius_cm'])
            assert math.isfinite(radius) and 50.0 <= radius <= 100.0, 'Derived connector radius exceeds the authorized native range'
            assert len(row['native_endpoint_trims']) == len(row['parent_road_actor_paths']) == 2
            for parent_path, trim in zip(row['parent_road_actor_paths'], row['native_endpoint_trims']):
                assert trim in junction_report['sourcecontrols_trimproof'][parent_path]['end_trims'], 'Derived connector endpoint trim differs from its source proof'
                assert float(trim['turn_radius_cm']) == radius, 'Source trim/connector selected radius differs'
                assert trim['partner_actor_path'] in set(row['parent_road_actor_paths']) - {parent_path}
            data = _discover('DescribeRoad', actual[row['road_actor_path']])
            assert _field(_field(data, 'Network'), 'RefPath') == network_path
            native_controls = list(_field(data, 'ControlPoints'))
            points = [_xyz(_field(point, 'Location')) for point in native_controls]
            actual_radii = [float(_field(point, 'TurnRadius')) for point in native_controls]
            expected_radii = [float(value) for value in row['point_turn_radii_cm']]
            assert len(expected_radii) == len(actual_radii) == len(points)
            assert all(math.isfinite(value) and abs(value - radius) <= 0.1 for value in expected_radii), 'Recorded connector point radii differ from the selected radius'
            assert all(abs(actual_radius - expected_radius) <= 0.1 for actual_radius, expected_radius in zip(actual_radii, expected_radii)), 'Actual connector point radii differ from the exact retained record'
            assert _sha(row['control_points_world_cm']) == row['control_points_sha256'], 'Derived control receipt corrupt'
            assert _sha(points) == row['control_points_sha256'], 'Saved derived native controls differ'
            lanes = list(_field(data, 'LeftLanes')) + list(_field(data, 'RightLanes'))
            assert abs(sum(float(_field(lane, 'WidthAtStart')) for lane in lanes) - row.get('width_start_cm', row['full_width_cm'])) <= 0.1
            assert abs(sum(float(_field(lane, 'WidthAtEnd')) for lane in lanes) - row.get('width_end_cm', row['full_width_cm'])) <= 0.1
        if junction_proxy is not None:
            junctions.verify_derived_roads(junction_proxy, junction_report)
            report['junction_trim_proof_verified'] = True
            report['junction_repair_readback'] = junction_report
        covered = set()
        for path in geo_paths:
            references = {_path(road) for road in native._get(actual[path], 'SourceRoads')}
            assert references and references.issubset(road_paths), 'RoadGeo crosses network/source ownership'
            covered.update(references)
            assert native._get(actual[path], 'bDisableIntersectionLandscapeAlignment')
        assert covered == road_paths, 'Some original/derived native roads lack generated geometry'
        raw_junction_issues = list(_discover('FindJunctionIssues', network))
        if raw_junction_issues:
            assert junction_proxy is not None, 'Native multiway junctions lack their explicit geographic proof'
            import geocity_roadbld_topology as topology
            unresolved, topology_proofs = topology.classify_native_junction_issues(junction_proxy, raw_junction_issues)
            assert not unresolved, 'Saved native junction defects remain'
            assert topology_proofs == junction_report.get('automatic_native_junctions', []), 'Saved native multiway topology/geometry proof differs'
            report['native_multiway_junction_readback'] = topology_proofs
        else:
            assert not (junction_report or {}).get('automatic_native_junctions'), 'Saved native multiway issue ledger differs'
        assert not _discover('FindGeometryIssues', network, plan['settings']['max_geometry_issues']), 'Saved native generated geometry defects remain'
        clipping = _read(contract['clipping_report'])
        assert clipping['schema'] == clip.SCHEMA and clipping['area_id'] == area and clipping['named_map'] == world_path
        for key in ('source_sha256', 'centreline_sha256'):
            assert clipping[key] == contract[key]
        assert clipping['protected_footprints_sha256'] == plan['protected_footprint_proof']['footprints_sha256']
        assert not clipping['unsupported_conflicts'] and clipping['native_material_slots_and_transforms_verified'] and clipping['native_collision_policy_verified']
        grounding_proof = _inspect_grounding(contract, plan, ledger, derived, actual, geo_paths, network, world, bounded)
        accepted_empty = grounding_proof['automatic_empty_geometry'] if grounding_proof else []
        if grounding_proof:
            report['native_grounding_readback'] = grounding_proof
        fit, components = _measure_all([actual[path] for path in sorted(owned_paths)], geo_paths, plan, clip, bounded, accepted_empty)
        report['native_mesh_footprint_validation'] = fit
        expected_bindings = contract.get('native_component_bindings') or contract.get('full_component_bindings')
        assert expected_bindings is not None, 'Saved delivery requires every actual native component binding/hash'
        assert len(expected_bindings) == len(components) and {row['component'] for row in expected_bindings} == set(components), 'Full native component ledger coverage differs'
        snapshots = {}
        for row in expected_bindings:
            bounded()
            actor, component = components[row['component']]
            snapshot = _component_snapshot(component, actor, clip)
            _check_binding(row, snapshot)
            snapshots[row['component']] = snapshot
        clipped_bindings = clipping['bindings']
        assert len({row['component'] for row in clipped_bindings}) == len(clipped_bindings)
        assert {row['clipped_mesh'] for row in clipped_bindings} == set(clipping['created_asset_paths'])
        for row in clipped_bindings:
            assert row['component'] in snapshots and row['binding_applied'] and row['actual_rebound_triangles_verified']
            _check_binding(row, snapshots[row['component']], clipped=True)
        dirty_maps = {_path(package) for package in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()}
        dirty_content = {_path(package) for package in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}
        assert world_path not in dirty_maps, 'Named retained map is dirty'
        dependencies = contract['named_generated_dependency_paths']
        assert not dirty_content.intersection(dependencies), 'Named native generated dependencies are dirty'
        for path in dependencies:
            assert path.startswith('/Game/Project/Areas/' + area + '/'), 'Unscoped named native dependency'
            assert path == world_path or unreal.EditorAssetLibrary.does_asset_exist(path), 'Named retained dependency missing: ' + path
        report.update(status='passed', original_source_road_count=plan['source_road_count'], original_source_piece_count=len(ledger),
            derived_road_count=len(derived), total_native_road_count=len(road_paths), geometry_actor_count=len(geo_paths), owned_actor_count=len(owned_paths),
            source_piece_ledger=ledger, original_control_readback=control_records, max_control_point_error_cm=max_error,
            derived_junction_roads=derived, component_bindings=list(snapshots.values()), clipped_component_count=len(clipped_bindings),
            automatic_empty_geometry=accepted_empty,
            exact_null_component_paths=fit['null_component_paths'],
            actual_saved_grounding_verified=grounding_proof is not None,
            native_network_stale=False, exact_actor_paths_and_tags_verified=True, source_hashes_verified=True,
            exact_materials_transforms_collision_and_geometry_hashes_verified=True, saved_named_packages_clean=True,
            reopened_binding_readback_verified=context == 'reopen_readback')
        bounded()
    except Exception as exc:
        report.update(status='failed', error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        report['elapsed_seconds'] = time.monotonic() - began
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(report, indent=2, allow_nan=False))
    return report
