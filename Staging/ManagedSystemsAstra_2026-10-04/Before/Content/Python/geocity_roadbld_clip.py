"""Clip measured conflicts in actual native RoadBLD output, after its rebuild.

This module does nothing on import. The editor owner calls clip_native_outputs
with the already verified native plan and owned actors. Original road controls,
actors, vendor assets and geographic protections remain untouched. Created
meshes are named area-owned derivatives of the actual RoadBLD target geometry.
Saved-map persistence is a separate mandatory readback, not inferred here.
"""
import datetime
import hashlib
import json
import math
import re
import time
from pathlib import Path

try:
    import unreal
except ImportError:
    unreal = None

SCHEMA = 'environmentpipeline.roadbld_native_clipping.v1'
FRAME = 'houdini_local_m_x_yup_z_to_unreal_cm_x_z_y'
OWNER = 'GeoCity_RoadBLD'


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode('utf-8')).hexdigest()


def _path(value):
    return value.get_path_name() if value is not None else None


def _success(value):
    expected = getattr(getattr(unreal, 'GeometryScriptOutcomePins', None), 'SUCCESS', None)
    assert (expected is not None and value == expected) or re.search(
        r'(?:\.|\b)SUCCESS(?:\s*[:>]|$)', str(value).upper()), 'GeometryScript failed: ' + str(value)


def _xyz(vector):
    return [float(vector.x), float(vector.y), float(vector.z)]


def _transform(transform):
    rotation = transform.rotation
    return {'translation_cm': _xyz(transform.translation), 'scale3d': _xyz(transform.scale3d),
        'rotation_xyzw': [float(rotation.x), float(rotation.y), float(rotation.z), float(rotation.w)]}


def _materials(component):
    return [_path(component.get_material(index)) for index in range(component.get_num_materials())]


def _collision(component, mesh):
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    simple = unreal.GeometryScript_Collision.get_simple_collision_from_static_mesh(mesh)
    channels = ['WORLD_STATIC', 'WORLD_DYNAMIC', 'PAWN', 'VISIBILITY', 'CAMERA',
        'PHYSICS_BODY', 'VEHICLE', 'DESTRUCTIBLE']
    channels += ['ENGINE_TRACE_CHANNEL' + str(index) for index in range(1, 7)]
    channels += ['GAME_TRACE_CHANNEL' + str(index) for index in range(1, 19)]
    responses = {}
    for name in channels:
        channel = getattr(unreal.CollisionChannel, name, None)
        if channel is None:
            channel = getattr(unreal.CollisionChannel, 'ECC_' + name, None)
        if channel is not None:
            responses[name] = str(component.get_collision_response_to_channel(channel))
    assert len(responses) >= 8, 'Cannot snapshot native component collision responses'
    return {'enabled': str(component.get_collision_enabled()),
        'profile': str(component.get_collision_profile_name()),
        'object_type': str(component.get_collision_object_type()),
        'generate_overlap_events': bool(component.get_editor_property('generate_overlap_events')),
        'responses': responses, 'complexity': str(subsystem.get_collision_complexity(mesh)),
        'simple_shape_count': int(unreal.GeometryScript_Collision.get_simple_collision_shape_count(simple))}


def _read_geometry(mesh, transform):
    mesh, triangles, unused = unreal.GeometryScript_MeshQueries.get_all_triangle_indices(mesh, True)
    mesh, vertices, unused = unreal.GeometryScript_MeshQueries.get_all_vertex_positions(mesh, False)
    triangles = list(unreal.GeometryScript_List.convert_triangle_list_to_array(triangles))
    vertices = list(unreal.GeometryScript_List.convert_vector_list_to_array(vertices))
    assert len(triangles) == mesh.get_triangle_count(), 'Native triangle coverage differs'
    points = [_xyz(transform.transform_location(vertex)) for vertex in vertices]
    assert all(all(math.isfinite(value) for value in point) for point in points)
    indices = [[int(row.x), int(row.y), int(row.z)] for row in triangles]
    assert all(all(0 <= index < len(points) for index in row) for row in indices)
    return points, indices


def prepare_protections(plan):
    """Pure geographic validation and spatial index; no editor operations."""
    import geocity_roadbld_workflow as native
    assert plan['schema'] == 'environmentpipeline.roadbld_plan.v1'
    assert plan['coordinate_frame'] == FRAME and plan['area_id'] in ('GazaRimal', 'GazaShujaiya')
    root = '/Game/Project/Areas/' + plan['area_id']
    assert plan['named_map'].startswith(root + '/') and plan['asset_root'] == root + '/RoadBLD'
    area = [float(value) for value in plan['area_box_xz_m']]
    assert len(area) == 4 and all(math.isfinite(value) for value in area)
    assert area[0] < area[2] and area[1] < area[3]
    pads = plan['protected_building_footprints_xz_m']
    proof = plan['protected_footprint_proof']
    assert len(pads) == proof['source_pad_count'] and _sha(pads) == proof['footprints_sha256']
    assert len({str(row['source_osm_id']) for row in pads}) == len(pads)
    prepared, grid = [], {}
    for index, row in enumerate(pads):
        ring = native._clean_ring(row['ring_xz_m'])
        bounds = native._bounds(ring)
        prepared.append((str(row['source_osm_id']), bounds, native._triangulate_ring(ring), ring))
        for cell in native._grid_cells(bounds):
            grid.setdefault(cell, []).append(index)
    return area, prepared, grid


def measure_conflicts(points_cm, triangles, protections, boundary_tolerance_cm=0.0,
        overlap_tolerance_m2=0.0, bounded=None):
    """Pure full-triangle fit, using the adapter's exact protected-pad arithmetic."""
    import geocity_roadbld_workflow as native
    area, pads, grid = protections
    maximum_escape_cm, overlap, projected = 0.0, {}, 0.0
    points = [(point[0] / 100.0, point[1] / 100.0) for point in points_cm]
    for number, indices in enumerate(triangles):
        if bounded and number % 512 == 0:
            bounded()
        triangle = tuple(points[index] for index in indices)
        bounds = native._bounds(triangle)
        maximum_escape_cm = max(maximum_escape_cm, 100.0 * max(area[0] - bounds[0],
            area[1] - bounds[1], bounds[2] - area[2], bounds[3] - area[3], 0.0))
        flat_area = abs(native._cross(*triangle)) * 0.5
        projected += flat_area
        if flat_area <= 1e-12:
            continue
        candidates = {index for cell in native._grid_cells(bounds) for index in grid.get(cell, ())}
        for index in candidates:
            source_id, pad_bounds, pad_triangles, unused = pads[index]
            if bounds[2] <= pad_bounds[0] or pad_bounds[2] <= bounds[0] or bounds[3] <= pad_bounds[1] or pad_bounds[3] <= bounds[1]:
                continue
            intersection = sum(native._triangle_intersection_area(triangle, pad) for pad in pad_triangles)
            if intersection > 1e-12:
                overlap[source_id] = overlap.get(source_id, 0.0) + intersection
    failed_pads = {source_id: value for source_id, value in overlap.items() if value > overlap_tolerance_m2}
    return {'triangle_count': len(triangles), 'summed_projected_triangle_area_m2': projected,
        'max_area_escape_cm': maximum_escape_cm, 'overlap_m2_by_pad': failed_pads,
        'conflicting_pad_ids': sorted(failed_pads),
        'passed': maximum_escape_cm <= boundary_tolerance_cm and not failed_pads}


def _mesh_attributes(mesh):
    mesh, materials, present = unreal.GeometryScript_Materials.get_all_triangle_material_i_ds(mesh)
    values = list(unreal.GeometryScript_List.convert_index_list_to_array(materials)) if present else []
    return {'material_ids': sorted({int(value) for value in values if int(value) >= 0}),
        'has_material_ids': bool(present), 'uv_sets': int(unreal.GeometryScript_MeshQueries.get_num_uv_sets(mesh)),
        'has_triangle_normals': bool(unreal.GeometryScript_MeshQueries.get_has_triangle_normals(mesh))}


def _copy_static(mesh):
    target = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    lod = unreal.GeometryScriptMeshReadLOD()
    # False uses native asset material-slot IDs, rather than section-order IDs.
    target, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(mesh, target, options, lod, False)
    _success(outcome)
    return target


def _trim(target, transform, ring, z_low, z_high, operation):
    tool = unreal.DynamicMesh()
    primitive = unreal.GeometryScriptPrimitiveOptions()
    frame = unreal.Transform(location=unreal.Vector(0.0, 0.0, z_low))
    tool = unreal.GeometryScript_Primitives.append_simple_extrude_polygon(tool, primitive, frame,
        [unreal.Vector2D(float(point[0]) * 100.0, float(point[1]) * 100.0) for point in ring],
        z_high - z_low, 0, True, unreal.GeometryScriptPrimitiveOriginMode.BASE)
    assert tool.get_triangle_count() > 0, 'Empty native clipping tool'
    options = unreal.GeometryScriptMeshBooleanOptions()
    options.set_editor_property('fill_holes', False)
    options.set_editor_property('simplify_output', False)
    options.set_editor_property('allow_empty_result', True)
    options.set_editor_property('output_transform_space', unreal.GeometryScriptBooleanOutputSpace.TARGET_TRANSFORM_SPACE)
    return unreal.GeometryScript_MeshBooleans.apply_mesh_boolean(target, transform, tool,
        unreal.Transform(), operation, options)


def _verify_candidate_coverage(plan, candidates, bounded, converted):
    import geocity_roadbld_seams as seams
    contexts = [c['prepared'].get('source_coverage_context') for c in candidates if c['prepared']]
    if not any(contexts):
        return None
    assert len(contexts) == len(candidates) and all(c is contexts[0] for c in contexts)
    surfaces = []
    for candidate in candidates:
        surface = dict(candidate['prepared']['coverage_surface'])
        surface['dynamic_mesh'] = candidate['output_mesh'] if converted else candidate['mesh']
        seams.refresh_surface(surface)
        surfaces.append(surface)
    return seams.verify_before_bind(contexts[0], surfaces, bounded)


def _restore_candidate_asset(candidate):
    """Restore exact pre-transaction geometry/materials of an owned candidate."""
    slots = candidate['rollback_slots']
    options = unreal.GeometryScriptCopyMeshToAssetOptions()
    options.set_editor_property('emit_transaction', False)
    options.set_editor_property('replace_materials', True)
    options.set_editor_property('new_materials', [s.material_interface for s in slots])
    options.set_editor_property('new_material_slot_names', [s.material_slot_name for s in slots])
    unused, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(
        candidate['rollback_mesh'], candidate['source'], options, unreal.GeometryScriptMeshWriteLOD(), False)
    _success(outcome)
    candidate['source'].set_editor_property('static_materials', slots)
    assert list(candidate['source'].get_editor_property('static_materials')) == slots
    metadata = candidate['rollback_metadata']
    current = _candidate_metadata(candidate['source'])
    for key in current.keys() - metadata.keys():
        unreal.EditorAssetLibrary.remove_metadata_tag(candidate['source'],key)
    for key,value in metadata.items():
        unreal.EditorAssetLibrary.set_metadata_tag(candidate['source'],key,value)
    assert _candidate_metadata(candidate['source']) == metadata, 'Candidate metadata presence/value rollback differs'
    if candidate['component'].static_mesh != candidate['source']:
        assert candidate['component'].set_static_mesh(candidate['source'])
    assert _materials(candidate['component']) == candidate['materials']
    assert _collision(candidate['component'], candidate['source']) == candidate['collision']
    assert _transform(candidate['component'].get_world_transform()) == _transform(candidate['transform'])
    before = _read_geometry(candidate['rollback_mesh'], candidate['transform'])
    after = _read_geometry(_copy_static(candidate['source']), candidate['transform'])
    assert _sha(before) == _sha(after), 'Candidate geometry rollback did not reproduce original triangles'
    assert _mesh_payload_sha(candidate['rollback_mesh'],candidate['transform']) == _mesh_payload_sha(
        _copy_static(candidate['source']),candidate['transform']), 'Candidate rollback changed UVs/normals/material IDs'
    actual_slots = list(candidate['source'].get_editor_property('static_materials'))
    assert [(_path(s.material_interface),str(s.material_slot_name)) for s in actual_slots] == [
        (_path(s.material_interface),str(s.material_slot_name)) for s in slots]


def _mesh_payload_sha(mesh, transform):
    import geocity_roadbld_seams as seams
    points,triangles = _read_geometry(mesh,transform)
    mesh,ids,valid = unreal.GeometryScript_Materials.get_all_triangle_material_i_ds(mesh)
    assert valid
    surface = {'dynamic_mesh':mesh,'points_cm':points,'triangles':triangles,
               'material_ids':[int(v) for v in unreal.GeometryScript_List.convert_index_list_to_array(ids)],
               'attributes':_mesh_attributes(mesh)}
    return _sha(dict(seams._outside_faces(surface,None,lambda:None)))


def _candidate_metadata(mesh):
    # The complete map preserves both absence and empty values, including
    # original-source lineage and collision-related package metadata.
    return {str(k):str(v) for k,v in unreal.EditorAssetLibrary.get_metadata_tag_values(mesh).items()}


def clip_native_outputs(plan, actors, guard, receipt_path=None, generation_id=None, max_seconds=180.0, prepared_native_meshes=None, replacement_bindings=None, deferred_native_prop_components=()):
    """Owner-run clipping. Returns named asset/binding ledger; never saves maps.

    Supply native plan(), owned_actors(), and the active operation's guard().
    Only conflicting exact StaticMeshComponents with one rendered LOD and no
    active simple collision are eligible. ISM, spline, dynamic and skeletal
    conflicts fail before any asset or binding mutation. Every candidate is
    independently checked before all-or-nothing rebinding; failures restore
    changed bindings and leave named new assets for explicit root review.
    """
    assert unreal is not None and callable(guard), 'Active owned editor guard is required'
    began = time.monotonic()
    assert 0 < max_seconds <= 600
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    token = generation_id or stamp
    assert re.fullmatch(r'[A-Za-z0-9_]{1,80}', token)
    project = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    target_receipt = Path(receipt_path or project / 'Staging/AppearanceRepair_2026-10-03' /
        ('ROADBLD_CLIP_' + plan['area_id'] + '_' + stamp + '.json')).resolve()
    assert target_receipt.is_relative_to(project / 'Staging/AppearanceRepair_2026-10-03')
    assert not target_receipt.exists(), 'Clipping receipts are immutable'
    report = {'schema': SCHEMA, 'utc': stamp, 'area_id': plan['area_id'],
        'named_map': plan['named_map'], 'source_sha256': plan['source_sha256'],
        'centreline_sha256': plan['centreline_sha256'], 'generation_id': token,
        'protected_footprints_sha256': plan['protected_footprint_proof']['footprints_sha256'],
        'status': 'measuring', 'created_asset_paths': [], 'bindings': [], 'unsupported_conflicts': [],
        'native_actor_and_control_edits': 0, 'vendor_asset_edits': 0,
        'map_save_performed': False, 'saved_reopen_verified': False,
        'independent_native_fit_validation_required': True,
        'persistence_requirement': 'After named asset/map saves, reopen and compare this exact component/mesh/material/transform ledger; native PostLoad may restore its own generated binding.',
        'ordinary_regeneration_requirement': 'Reapply after final native RoadBLD rebuild, before independent fit validation and named saves.'}
    rebound, candidates, overwritten = [], [], []
    replacement_bindings = replacement_bindings or {}
    report['updated_asset_paths'] = []
    report['in_place_owned_candidate_correction'] = bool(replacement_bindings)
    report['conversion_proof_timing'] = ('after in-place writes to already-bound unsaved candidates; rollback required on any failure'
                                         if replacement_bindings else 'new unbound assets before component rebinding')
    prepared_native_meshes = prepared_native_meshes or {}
    deferred_props = set(deferred_native_prop_components)
    assert len(deferred_props) == len(deferred_native_prop_components), 'Ambiguous deferred native prop component ledger'
    report['deferred_native_prop_components'] = sorted(deferred_props)
    if replacement_bindings:
        assert prepared_native_meshes and all(v.get('source_coverage_context') for v in prepared_native_meshes.values()), 'Replacement requires complete physical prebinding context'
        assert len({v['clipped_mesh'] for v in replacement_bindings.values()}) == len(replacement_bindings), 'Shared candidate assets require a separate transaction'
        report['previous_candidate_bindings_sha256'] = _sha(replacement_bindings)
    report['nonrendering_null_components'] = []

    def bounded():
        guard()
        assert time.monotonic() - began <= max_seconds, 'Bounded native clipping time exceeded'

    def write_report():
        report['elapsed_seconds'] = time.monotonic() - began
        report['receipt'] = str(target_receipt)
        target_receipt.parent.mkdir(parents=True, exist_ok=True)
        with target_receipt.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(report, indent=2, allow_nan=False))

    try:
        bounded()
        protections = prepare_protections(plan)
        area, pads, unused = protections
        tolerance = float(plan['settings']['area_boundary_tolerance_cm'])
        pad_tolerance = float(plan['settings']['building_overlap_tolerance_m2'])
        assert 0 <= tolerance <= 2.0 and 0 <= pad_tolerance <= 0.0001
        read_options = unreal.GeometryScriptCopyMeshFromComponentOptions()
        seen = set()
        for actor in actors:
            bounded()
            tags = {str(value) for value in actor.get_editor_property('tags')}
            assert {OWNER, 'GeoCityArea_' + plan['area_id']}.issubset(tags), 'Foreign native actor'
            assert _path(actor).startswith(plan['named_map'] + '.'), 'Native actor belongs to another map'
            for component in actor.get_components_by_class(unreal.MeshComponent):
                bounded()
                if _path(component) in seen:
                    continue
                seen.add(_path(component))
                if _path(component) in deferred_props:
                    assert isinstance(component, unreal.InstancedStaticMeshComponent), 'Only checked native prop ISMs can defer surface clipping'
                    continue  # Caller must fit and validate exact rigid instances.
                if component.get_class().get_name() == 'StaticMeshComponent' and component.static_mesh is None:
                    report['nonrendering_null_components'].append(_path(component))
                    continue  # Final physical same-source coverage remains mandatory.
                instanced = isinstance(component, unreal.InstancedStaticMeshComponent)
                transforms = [component.get_instance_transform(index, world_space=True)
                    for index in range(component.get_instance_count())] if instanced else [component.get_world_transform()]
                if not transforms:
                    continue
                prepared = prepared_native_meshes.get(_path(component))
                if prepared:
                    assert not instanced and prepared['component'] == component
                    expected = replacement_bindings[_path(component)]['source_native_mesh'] if replacement_bindings else _path(component.static_mesh)
                    assert prepared['original_mesh_path'] == expected
                    copied = prepared['dynamic_mesh']
                else:
                    copied, unused, outcome = unreal.GeometryScript_SceneUtils.copy_mesh_from_component(
                        component, unreal.DynamicMesh(), read_options, False)
                    _success(outcome)
                conflicts = []
                for index, transform in enumerate(transforms):
                    points, triangles = _read_geometry(copied, transform)
                    # Detect any positive pad intersection, so many individually
                    # tiny conflicts cannot evade the adapter's aggregate gate.
                    proof = measure_conflicts(points, triangles, protections, tolerance, 0.0, bounded)
                    if not proof['passed']:
                        conflicts.append({'instance_index': index if instanced else None, 'proof': proof})
                if not conflicts and not prepared:
                    continue
                # Strictly reject subclasses with deformation or shared base geometry.
                if component.get_class().get_name() != 'StaticMeshComponent':
                    report['unsupported_conflicts'].append({'actor': _path(actor), 'component': _path(component),
                        'class': component.get_class().get_name(), 'conflicts': conflicts,
                        'reason': 'Conflicting component requires measured type-specific clipping; shared or deformed base must not be rewritten.'})
                    continue
                source = component.static_mesh
                assert source is not None and all(_materials(component)), 'Native output lacks mesh/materials'
                rendered_lods = int(unreal.GeometryScript_AssetUtils.get_num_static_mesh_lods_of_type(source, unreal.GeometryScriptLODType.RENDER_DATA))
                assert rendered_lods == 1, 'Conflicting native mesh has unhandled additional render LODs'
                collision = _collision(component, source)
                assert collision['simple_shape_count'] == 0, 'Conflicting native simple collision needs measured shape clipping'
                candidates.append({'actor': actor, 'component': component, 'source': source,
                    'transform': transforms[0], 'materials': _materials(component),
                    'collision': collision, 'before': conflicts[0]['proof'] if conflicts else proof,
                    'prepared': prepared})
        assert set(prepared_native_meshes).issubset(seen), 'Prepared native grounding binding is absent'
        assert deferred_props.issubset(seen), 'Deferred native prop binding is absent'
        assert not report['unsupported_conflicts'], 'Unsupported native component conflicts remain; no native clipping applied'
        report['measured_component_count'] = len(seen)
        report['conflicting_static_component_count'] = len(candidates)
        # Prepare all named copies before changing any native component binding.
        for candidate in candidates:
            bounded()
            source, component, transform = candidate['source'], candidate['component'], candidate['transform']
            mesh = candidate['prepared']['dynamic_mesh'] if candidate['prepared'] else _copy_static(source)
            before_attributes = _mesh_attributes(mesh)
            source_slots = list(source.get_editor_property('static_materials'))
            assert before_attributes['has_material_ids'] and before_attributes['material_ids']
            assert max(before_attributes['material_ids']) < len(source_slots), 'Native material-slot IDs are invalid'
            points, indices = _read_geometry(mesh, transform)
            before = measure_conflicts(points, indices, protections, tolerance, 0.0, bounded)
            assert not before['passed'] or candidate['prepared'], 'Actual native source/component conflict correspondence differs'
            z_low = min(point[2] for point in points) - 1000.0
            z_high = max(point[2] for point in points) + 1000.0
            if before['max_area_escape_cm'] > tolerance:
                ring = [(area[0], area[1]), (area[2], area[1]), (area[2], area[3]), (area[0], area[3])]
                mesh = _trim(mesh, transform, ring, z_low, z_high, unreal.GeometryScriptBooleanOperation.TRIM_OUTSIDE)
            for source_id, unused, unused, ring in pads:
                if source_id in before['conflicting_pad_ids']:
                    bounded()
                    mesh = _trim(mesh, transform, ring, z_low, z_high, unreal.GeometryScriptBooleanOperation.TRIM_INSIDE)
            assert mesh.get_triangle_count() > 0, 'Clipping removed an entire native component; explicit source resolution is required'
            after_attributes = _mesh_attributes(mesh)
            assert after_attributes['has_material_ids'] and after_attributes['material_ids']
            assert set(after_attributes['material_ids']).issubset(before_attributes['material_ids']), 'Clipping introduced tool material IDs'
            assert after_attributes['uv_sets'] == before_attributes['uv_sets']
            assert after_attributes['has_triangle_normals'] == before_attributes['has_triangle_normals']
            points, indices = _read_geometry(mesh, transform)
            after = measure_conflicts(points, indices, protections, tolerance, pad_tolerance, bounded)
            assert after['passed'], 'Supported native trim did not satisfy exact authoritative protections'
            candidate.update(mesh=mesh, before_attributes=before_attributes, after_attributes=after_attributes,
                             source_slots=source_slots, before_fit=before, after_fit=after)
        report['transient_prebinding_coverage'] = _verify_candidate_coverage(plan, candidates, bounded, converted=False)
        if replacement_bindings:
            assert set(replacement_bindings) == {_path(c['component']) for c in candidates}
            for candidate in candidates:
                component = candidate['component']; previous = replacement_bindings[_path(component)]
                assert previous['clipped_mesh'] == _path(component.static_mesh)
                assert previous['component_world_transform'] == _transform(component.get_world_transform())
                assert previous['material_slots'] == _materials(component)
                assert previous['collision'] == _collision(component, component.static_mesh)
                saved = _copy_static(component.static_mesh)
                points, triangles = _read_geometry(saved, component.get_world_transform())
                assert _sha({'vertices_cm':points,'triangles':triangles}) == previous['clipped_world_triangle_geometry_sha256']
                candidate['rollback_mesh'] = saved
                candidate['rollback_slots'] = list(component.static_mesh.get_editor_property('static_materials'))
                candidate['rollback_metadata'] = _candidate_metadata(component.static_mesh)
        for candidate in candidates:
            bounded()
            source, component, transform, mesh = candidate['source'], candidate['component'], candidate['transform'], candidate['mesh']
            source_slots = candidate['source_slots']
            before, after = candidate['before_fit'], candidate['after_fit']
            before_attributes, after_attributes = candidate['before_attributes'], candidate['after_attributes']
            if replacement_bindings:
                output = component.static_mesh
                assert _path(output).startswith(plan['asset_root']+'/ClippedGeometry/')
                assert unreal.EditorAssetLibrary.get_metadata_tag(output, 'GeoCityOwner') == OWNER
                assert unreal.EditorAssetLibrary.get_metadata_tag(output, 'GeoCityArea') == plan['area_id']
                overwritten.append(candidate)
                candidate['output'] = output
                report['updated_asset_paths'].append(_path(output))
            else:
                identity = _sha({'component': _path(component), 'source_mesh': _path(source)})[:16]
                asset_path = plan['asset_root'] + '/ClippedGeometry/' + token + '/SM_Clipped_' + identity
                assert not unreal.EditorAssetLibrary.does_asset_exist(asset_path), 'Clipped mesh destination already exists'
                creation = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
                creation.set_editor_property('enable_collision', True)
                creation.set_editor_property('collision_mode', unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).get_collision_complexity(source))
                output, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(mesh, asset_path, creation)
                _success(outcome)
                assert isinstance(output, unreal.StaticMesh) and _path(output).startswith(plan['asset_root'] + '/ClippedGeometry/')
                report['created_asset_paths'].append(_path(output))
            copy_options = unreal.GeometryScriptCopyMeshToAssetOptions()
            copy_options.set_editor_property('emit_transaction', False)
            copy_options.set_editor_property('replace_materials', True)
            copy_options.set_editor_property('new_materials', [slot.material_interface for slot in source_slots])
            copy_options.set_editor_property('new_material_slot_names', [slot.material_slot_name for slot in source_slots])
            mesh, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(mesh, output,
                copy_options, unreal.GeometryScriptMeshWriteLOD(), False)
            _success(outcome)
            assert [_path(slot.material_interface) for slot in output.get_editor_property('static_materials')] == [_path(slot.material_interface) for slot in source_slots]
            assert _collision(component, output) == candidate['collision'], 'Clipped asset changed native collision policy'
            output_mesh = _copy_static(output)
            output_points, output_indices = _read_geometry(output_mesh, transform)
            assert measure_conflicts(output_points, output_indices, protections, tolerance, pad_tolerance, bounded)['passed'], 'New asset geometry differs from validated clipped native target'
            unreal.EditorAssetLibrary.set_metadata_tag(output, 'GeoCityOwner', OWNER)
            unreal.EditorAssetLibrary.set_metadata_tag(output, 'GeoCityArea', plan['area_id'])
            unreal.EditorAssetLibrary.set_metadata_tag(output, 'GeoCityNativeSourceMesh', candidate['prepared']['original_mesh_path'] if candidate['prepared'] else _path(source))
            unreal.EditorAssetLibrary.set_metadata_tag(output, 'GeoCityNativeSourceComponent', _path(component))
            unreal.EditorAssetLibrary.set_metadata_tag(output, 'GeoCityProtectedFootprints', report['protected_footprints_sha256'])
            candidate.update(output=output, mesh=mesh, output_mesh=output_mesh)
            report['bindings'].append({'actor': _path(candidate['actor']), 'component': _path(component),
                'source_native_mesh': candidate['prepared']['original_mesh_path'] if candidate['prepared'] else _path(source), 'clipped_mesh': _path(output),
                'material_slots': candidate['materials'], 'source_asset_material_slots': [_path(slot.material_interface) for slot in source_slots],
                'source_asset_material_slot_names': [str(slot.material_slot_name) for slot in source_slots],
                'component_world_transform': _transform(transform), 'collision': candidate['collision'],
                'before': before, 'after': after, 'attributes_before': before_attributes,
                'attributes_after': after_attributes,
                'height_projection_proof': candidate['prepared']['proof'] if candidate['prepared'] else None,
                'clipped_world_triangle_geometry_sha256': _sha({'vertices_cm': output_points, 'triangles': output_indices}),
                'source_native_geometry_preserved_as_input': True, 'binding_applied': False})
        report['converted_prebinding_coverage'] = _verify_candidate_coverage(plan, candidates, bounded, converted=True)
        for candidate, binding in zip(candidates, report['bindings']):
            bounded()
            component = candidate['component']
            rebound.append(candidate)
            if component.static_mesh != candidate['output']:
                assert component.set_static_mesh(candidate['output'])
            assert _materials(component) == candidate['materials'], 'Native material overrides changed during binding'
            assert _transform(component.get_world_transform()) == _transform(candidate['transform']), 'Native component transform changed'
            assert _collision(component, candidate['output']) == candidate['collision'], 'Native collision state changed'
            actual_mesh, unused, outcome = unreal.GeometryScript_SceneUtils.copy_mesh_from_component(
                component, unreal.DynamicMesh(), read_options, False)
            _success(outcome)
            actual_points, actual_indices = _read_geometry(actual_mesh, component.get_world_transform())
            assert measure_conflicts(actual_points, actual_indices, protections, tolerance, pad_tolerance, bounded)['passed'], 'Rebound native component differs from validated mesh asset'
            binding['binding_applied'] = True
            binding['actual_rebound_triangles_verified'] = True
        report['status'] = 'native_conflicts_clipped_pending_independent_fit_saves_and_reopen' if candidates else 'no_measured_conflicts_no_mutation'
        report['native_material_slots_and_transforms_verified'] = True
        report['native_collision_policy_verified'] = True
        write_report()
        return report
    except Exception as exception:
        report['status'] = 'failed_closed'
        report['error'] = repr(exception)
        report['rollback_errors'] = []
        for candidate in reversed(rebound):
            try:
                if candidate['component'].static_mesh != candidate['source']:
                    assert candidate['component'].set_static_mesh(candidate['source'])
                assert _materials(candidate['component']) == candidate['materials']
                for binding in report['bindings']:
                    if binding['component'] == _path(candidate['component']):
                        binding['binding_applied'] = False
                        binding['restored_original_binding_after_failure'] = True
            except Exception as rollback:
                report['rollback_errors'].append({'component': _path(candidate['component']), 'error': repr(rollback)})
        for candidate in reversed(overwritten):
            try:
                _restore_candidate_asset(candidate)
            except Exception as rollback:
                report['rollback_errors'].append({'asset': _path(candidate['source']), 'error': repr(rollback)})
        report['restored_original_component_bindings'] = not report['rollback_errors']
        write_report()
        raise RuntimeError('Native clipping failed closed; review ' + str(target_receipt)) from exception
