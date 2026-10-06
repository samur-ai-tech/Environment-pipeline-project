"""Retain and fit the installed RoadBLD prop ISMs in its ordinary transaction.

No actor, asset, catalog, session or generation is created on import. Native
props keep their original mesh/materials, XY, rotation and scale. Only their
ground contact and unsuitable generated instances are conditioned.
"""
import math
import time
import unreal


def allowed_meshes(run):
    import geocity_roadbld_workflow as base
    result = set()
    for preset in run.presets.values():
        for spawner in base._get(preset, 'PropSpawners'):
            # Current RoadBLD stores the settings struct directly in this array;
            # older presets wrap the same settings in a spawner object.
            settings = spawner if isinstance(spawner, unreal.PropSpawnerSettings) else base._get(spawner, 'Settings')
            for mesh in base._get(settings, 'MeshesToUse'):
                path = base._path(mesh)
                assert path and path.startswith(('/RoadBLD/', '/WorldBLD/')), 'Native prop preset contains content outside the installed permitted road kit: ' + str(path)
                result.add(path)
    return result


def checked_component(run, component):
    import geocity_roadbld_workflow as base
    if not isinstance(component, unreal.InstancedStaticMeshComponent):
        return False
    assert component.get_class().get_name() in ('InstancedStaticMeshComponent', 'HierarchicalInstancedStaticMeshComponent'), 'Unsupported native prop instancer subclass'
    assert component.get_owner() in run.native_geos(), 'Native prop component is outside this generation'
    mesh = component.static_mesh
    assert (mesh is None and component.get_instance_count() == 0) or base._path(mesh) in allowed_meshes(run), 'Native prop mesh lacks its installed preset provenance: ' + str(base._path(mesh))
    if component.get_instance_count():
        assert all(component.get_material(i) for i in range(component.get_num_materials())) and component.get_num_materials() > 0
    return True


def components(run):
    result = []
    for actor in run.native_geos():
        for component in actor.get_components_by_class(unreal.MeshComponent):
            if checked_component(run, component):
                result.append(component)
    return result


def _support_fields(run, bounded):
    import geocity_roadbld_workflow as base
    import geocity_roadbld_clip as clip
    from geocity_roadbld_grounding import AsphaltField
    materials = {base._path(unreal.load_asset(run.plan['settings'][name])) for name in ('road_material', 'sidewalk_material')}
    fields = []
    for actor in run.native_geos():
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            bounded()
            if isinstance(component, unreal.InstancedStaticMeshComponent) or component.static_mesh is None:
                continue
            mesh = clip._copy_static(component.static_mesh)
            points, triangles = clip._read_geometry(mesh, component.get_world_transform())
            mesh, ids, present = unreal.GeometryScript_Materials.get_all_triangle_material_i_ds(mesh)
            assert present
            ids = list(unreal.GeometryScript_List.convert_index_list_to_array(ids))
            selected = {i for i in range(component.get_num_materials()) if base._path(component.get_material(i)) in materials}
            mask = [int(value) in selected for value in ids]
            if not any(mask):
                continue
            upward = [bool(mask[i]) and unreal.GeometryScript_MeshQueries.get_triangle_face_normal(mesh, i)[0].z > .25 for i in range(len(triangles))]
            if any(upward):
                fields.append(AsphaltField(points, triangles, [0] * len(triangles), upward))
    assert fields, 'Native prop support requires the actual retained asphalt/sidewalk geometry'
    return fields


def _bottom(points):
    lowest = min(point[2] for point in points)
    contact = [point for point in points if point[2] <= lowest + .1]
    return [sum(point[i] for point in contact) / len(contact) for i in range(2)] + [lowest]


def _height(run, fields, contact):
    heights = [float(run.landscape_sampler(contact[0], contact[1]))]
    for field in fields:
        hit = field.covered(contact)
        if hit:
            heights.append(hit[0])
    value = max(heights)
    assert math.isfinite(value)
    return value + .2


def condition(run, max_seconds=180):
    """Fit new native instances; omit only exact generated geographic conflicts."""
    import geocity_roadbld_workflow as base
    import geocity_roadbld_clip as clip
    started = time.monotonic()

    def bounded():
        run.guard()
        assert time.monotonic() - started < max_seconds, 'Native prop fit exceeded its bounded transaction time'

    props = components(run)
    protections = clip.prepare_protections(run.plan)
    fields = _support_fields(run, bounded) if any(p.get_instance_count() for p in props) else []
    records = []
    total_before = total_after = 0
    for component in props:
        bounded()
        count = component.get_instance_count()
        total_before += count
        omitted = []
        corrected = []
        if count:
            copied = clip._copy_static(component.static_mesh)
            for index in range(count):
                bounded()
                original = component.get_instance_transform(index, world_space=True)
                assert original is not None
                points, triangles = clip._read_geometry(copied, original)
                proof = clip.measure_conflicts(points, triangles, protections, run.plan['settings']['area_boundary_tolerance_cm'], 0.0, bounded)
                if not proof['passed']:
                    omitted.append({'original_index': index, 'original_transform': clip._transform(original), 'reason': 'native_generated_prop_outside_area_or_protected_building', 'proof': proof})
                    continue
                contact = _bottom(points)
                target = _height(run, fields, contact)
                delta = target - contact[2]
                location = original.translation
                fitted = original.copy()
                fitted.translation = unreal.Vector(location.x, location.y, location.z + delta)
                assert component.update_instance_transform(index, fitted, world_space=True, mark_render_state_dirty=True, teleport=True), 'Native prop contact update failed'
                actual = component.get_instance_transform(index, world_space=True)
                actual_points, unused = clip._read_geometry(copied, actual)
                assert abs(_bottom(actual_points)[2] - target) <= .1, 'Native prop contact readback differs'
                corrected.append({'original_index': index, 'vertical_delta_cm': delta, 'target_support_z_cm': target})
            # Descending removals preserve unprocessed indices even with swap
            # removal. Read back the final multiset, never assume index order.
            for item in reversed(omitted):
                assert component.remove_instance(item['original_index']), 'Exact unsuitable generated prop omission failed'
        total_after += component.get_instance_count()
        records.append({'component': base._path(component), 'mesh': base._path(component.static_mesh), 'source_instance_count': count, 'retained_instance_count': component.get_instance_count(), 'omitted': omitted, 'ground_contact': corrected})
    receipt = {'schema': 'environmentpipeline.roadbld_native_props.v1', 'provider': 'installed_native_PropSpawner', 'configured_meshes': sorted(allowed_meshes(run)), 'source_instance_count': total_before, 'retained_instance_count': total_after, 'omitted_instance_count': total_before - total_after, 'components': records, 'native_originals_modified': False, 'distribution': 'native road endpoints/preset policy; traffic signs are procedural, not surveyed sign locations'}
    assert not total_before or total_after, 'All configured native street props failed geographic fit; prior output is preserved'
    run.state['native_props'] = receipt
    run.state['native_props_validation'] = verify(run, max_seconds=max_seconds)
    return receipt


def verify(run, max_seconds=180):
    """Read final instance geometry/contact on current or saved Landscape."""
    import geocity_roadbld_workflow as base
    import geocity_roadbld_clip as clip
    started = time.monotonic()

    def bounded():
        run.guard()
        assert time.monotonic() - started < max_seconds, 'Native prop readback exceeded its bounded time'

    props = components(run)
    fields = _support_fields(run, bounded) if any(p.get_instance_count() for p in props) else []
    protections = clip.prepare_protections(run.plan)
    snapshots = []
    for component in props:
        bounded()
        count = component.get_instance_count()
        copied = clip._copy_static(component.static_mesh) if count else None
        transforms = []
        for index in range(count):
            bounded()
            transform = component.get_instance_transform(index, world_space=True)
            points, triangles = clip._read_geometry(copied, transform)
            assert clip.measure_conflicts(points, triangles, protections, run.plan['settings']['area_boundary_tolerance_cm'], 0.0, bounded)['passed'], 'Native prop geometric fit is incomplete'
            contact = _bottom(points)
            assert abs(contact[2] - _height(run, fields, contact)) <= 2., 'Native prop ground contact is incomplete'
            transforms.append(clip._transform(transform))
        snapshots.append({'component': base._path(component), 'mesh': base._path(component.static_mesh), 'instance_count': count, 'world_transforms': transforms, 'world_transforms_sha256': clip._sha(sorted(transforms, key=clip._sha)), 'materials': clip._materials(component) if component.static_mesh else []})
    prior = run.state.get('native_props', {})
    assert sum(s['instance_count'] for s in snapshots) == prior.get('retained_instance_count', 0), 'Native prop instance count changed'
    assert {s['component'] for s in snapshots} == {r['component'] for r in prior.get('components', [])}, 'Native prop component identity changed'
    return {'passed': True, 'instance_count': sum(s['instance_count'] for s in snapshots), 'components': snapshots, 'current_authoritative_landscape': run.landscape_sampler.path}
