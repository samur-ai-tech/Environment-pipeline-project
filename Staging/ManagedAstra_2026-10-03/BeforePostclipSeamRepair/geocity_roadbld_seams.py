"""Close measured <=10cm native asphalt seams in owner-supplied transient meshes.

Import is inert. Existing vertices, triangles, actors, splines and assets stay
unchanged. A tiny material0 boundary fan is appended only for an uncovered
dense original geographic point and exact actual native source membership.
The owner binds scoped copies, clips, verifies and saves through its lifecycle.
"""
import hashlib
import json
import math
import time

SCHEMA = 'environmentpipeline.roadbld_native_seams.v1'


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def _xy_key(point):
    return round(point[0], 6), round(point[1], 6)


def _edge_projection(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    norm = dx*dx + dy*dy
    if norm <= 1e-12:
        return None
    fraction = max(0.0, min(1.0, ((point[0]-a[0])*dx + (point[1]-a[1])*dy)/norm))
    closest = [a[0]+fraction*dx, a[1]+fraction*dy]
    return math.dist(point[:2], closest), closest, fraction


def _boundary_edges(surface, field):
    """Count geometric upward-asphalt edges, including UV-split duplicates."""
    counts, records = {}, {}
    for number in field.faces:
        indices = surface['triangles'][number]
        for first, second in zip(indices, indices[1:] + indices[:1]):
            a, b = surface['points_cm'][first], surface['points_cm'][second]
            key = tuple(sorted((_xy_key(a), _xy_key(b))))
            if key[0] == key[1]:
                continue
            counts[key] = counts.get(key, 0) + 1
            records[key] = (number, first, second)
    return [records[key] for key in sorted(counts) if counts[key] == 1]


def plan_boundary_fan(path, point, surfaces, fields, landscape_z, clearance_cm=5.0,
                      cap_cm=10.0, extension_cm=0.1):
    """Pure narrow repair proposal; no existing geometric coordinate changes."""
    assert 0 < cap_cm <= 10 and 0 < extension_cm <= 0.1
    import geocity_roadbld_grounding as grounding
    candidates = []
    for surface in surfaces:
        # Expanded parent provenance cannot create a seam on another source.
        if path not in surface['native_source_road_paths']:
            continue
        field = fields[surface['component_path']]
        for number, first, second in _boundary_edges(surface, field):
            projection = _edge_projection(point, surface['points_cm'][first], surface['points_cm'][second])
            if projection is None:
                continue
            distance, closest, fraction = projection
            if 1e-7 < distance and distance + extension_cm <= cap_cm:
                candidates.append((distance, surface['component_path'], number, first, second, closest, fraction, surface))
    assert candidates, 'Uncovered source point has no genuine same-source asphalt boundary within10cm: ' + json.dumps({'source_road_actor_path': path, 'point_world_cm': point}, allow_nan=False)
    distance, component, number, first, second, closest, fraction, surface = min(candidates, key=lambda row: row[:5])
    dx, dy = (point[0]-closest[0])/distance, (point[1]-closest[1])/distance
    support = [point[0]+extension_cm*dx, point[1]+extension_cm*dy, 0.0]
    support[2] = float(landscape_z(support[0], support[1])) + clearance_cm
    assert all(math.isfinite(value) for value in support)
    a, b = surface['points_cm'][first], surface['points_cm'][second]
    cross = (b[0]-a[0])*(support[1]-a[1]) - (b[1]-a[1])*(support[0]-a[0])
    assert abs(cross) > 1e-8, 'Degenerate source seam fan'
    # Native UE face normals/front collision use clockwise XY winding.
    if cross > 0:
        first, second, a, b = second, first, b, a
    weights = grounding._barycentric(point, a, b, support)
    assert weights is not None and min(weights) >= -1e-9, 'Proposed fan does not cover exact source point'
    # Reuse a boundary edge only when the complete native topology permits it.
    # Curbs frequently share that edge; identical-position duplicate endpoints
    # then create an isolated fan without nonmanifold changes to the original.
    pair = {first, second}
    incidence = sum(pair.issubset(set(triangle)) for triangle in surface['triangles'])
    assert incidence >= 1
    return {'source_road_actor_path': path, 'source_point_world_cm': list(point),
        'component_path': component, 'geometry_actor_path': surface['geometry_actor_path'],
        'native_source_road_paths': list(surface['native_source_road_paths']),
        'parent_asphalt_triangle_index': number, 'boundary_edge_vertex_indices': [first, second],
        'boundary_edge_world_cm': [list(a), list(b)], 'boundary_asphalt_incidence': 1,
        'native_whole_mesh_edge_incidence': incidence, 'duplicate_boundary_vertices': incidence != 1,
        'nearest_boundary_distance_cm': distance, 'boundary_projection_xy_cm': closest,
        'support_vertex_world_cm': support, 'support_extension_beyond_source_cm': extension_cm,
        'boundary_extension_cm': distance+extension_cm, 'xy_extension_cap_cm': cap_cm,
        'patch_projected_area_cm2': abs(cross)*0.5,
        'native_clockwise_upward_winding': True,
        'original_coordinates_changed': 0, 'material_id': 0, 'saved': False}


def _unit_normal(points):
    a, b, c = points
    u, v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
    n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
    length = math.sqrt(sum(value*value for value in n))
    assert length > 1e-8
    return [value/length for value in n]


def _append_fan(surface, proposal, bounded):
    """Owner-run edits of an existing transient DynamicMesh only."""
    import geocity_roadbld_workflow as base
    import geocity_roadbld_clip as clip
    import geocity_roadbld_grounding as grounding
    unreal = base.unreal
    mesh = surface['dynamic_mesh']
    original_mesh = mesh
    before_points = [list(point) for point in surface['points_cm']]
    before_triangles = [list(row) for row in surface['triangles']]
    before_materials = list(surface['material_ids'])
    before_attributes = clip._mesh_attributes(mesh)
    first, second = proposal['boundary_edge_vertex_indices']
    new_world = proposal['boundary_edge_world_cm'] + [proposal['support_vertex_world_cm']]
    local = [unreal.MathLibrary.inverse_transform_location(surface['transform'], unreal.Vector(*point)) for point in new_world]
    parent_triangle = [before_points[index] for index in before_triangles[proposal['parent_asphalt_triangle_index']]]
    uv_values = []
    for uv_set in range(before_attributes['uv_sets']):
        row = []
        for point in new_world:
            weights = grounding._barycentric(point, *parent_triangle)
            assert weights is not None
            mesh, valid, uv = unreal.GeometryScript_MeshQueries.get_interpolated_triangle_uv(mesh, uv_set,
                proposal['parent_asphalt_triangle_index'], unreal.Vector(*weights))
            assert valid, 'Native seam parent triangle lacks required UV overlay'
            row.append(uv)
        uv_values.append(row)
    indices = [first, second]
    if proposal['duplicate_boundary_vertices']:
        indices = []
        for point in local[:2]:
            mesh, index = unreal.GeometryScript_MeshEdits.add_vertex_to_mesh(mesh, point, False)
            assert index >= len(before_points)
            indices.append(int(index))
    mesh, support_index = unreal.GeometryScript_MeshEdits.add_vertex_to_mesh(mesh, local[2], False)
    assert support_index >= len(before_points)
    indices.append(int(support_index))
    mesh, triangle_index = unreal.GeometryScript_MeshEdits.add_triangle_to_mesh(mesh, unreal.IntVector(*indices), 0, False)
    assert triangle_index == len(before_triangles), 'Native seam triangle append failed or triangle IDs are not compact'
    mesh, valid = unreal.GeometryScript_Materials.set_triangle_material_id(mesh, triangle_index, 0, False)
    assert valid
    for uv_set, values in enumerate(uv_values):
        uv_triangle = unreal.GeometryScriptUVTriangle()
        uv_triangle.uv0, uv_triangle.uv1, uv_triangle.uv2 = values
        mesh, valid = unreal.GeometryScript_UVs.set_mesh_triangle_u_vs(mesh, uv_set, triangle_index, uv_triangle, False)
        assert valid, 'Native seam UV assignment failed'
    normal, valid = unreal.GeometryScript_MeshQueries.get_triangle_face_normal(mesh, triangle_index)
    assert valid and normal.z > .25, 'Native seam must render and collide as an upward face'
    normals = unreal.GeometryScriptTriangle()
    normals.vector0 = normals.vector1 = normals.vector2 = normal
    mesh, valid = unreal.GeometryScript_Normals.set_mesh_triangle_normals(mesh, triangle_index, normals, False)
    assert valid
    mesh = unreal.GeometryScript_Normals.recompute_normals(mesh, unreal.GeometryScriptCalculateNormalsOptions(), False)
    assert mesh == original_mesh, 'Native seam changed transient mesh identity; prepared binding would become stale'
    points, triangles = clip._read_geometry(mesh, surface['transform'])
    assert points[:len(before_points)] == before_points and triangles[:len(before_triangles)] == before_triangles, 'Native seam changed existing geometry'
    assert len(triangles) == len(before_triangles)+1 and triangles[-1] == indices
    mesh, material_list, valid = unreal.GeometryScript_Materials.get_all_triangle_material_i_ds(mesh)
    materials = [int(value) for value in unreal.GeometryScript_List.convert_index_list_to_array(material_list)]
    assert valid and materials == before_materials+[0]
    attributes = clip._mesh_attributes(mesh)
    assert attributes['uv_sets'] == before_attributes['uv_sets'] and attributes['material_ids'] == before_attributes['material_ids'] and attributes['has_triangle_normals']
    surface['points_cm'], surface['triangles'], surface['material_ids'] = points, triangles, materials
    surface['upward'] = list(surface['upward']) + [True]
    surface['dynamic_mesh'], surface['attributes'] = mesh, attributes
    proposal.update(new_triangle_index=int(triangle_index), new_triangle_vertex_indices=indices,
        new_vertex_count=len(points)-len(before_points), added_triangle_count=1,
        native_uv_sets_interpolated=before_attributes['uv_sets'], native_normal_assignment_verified=True,
        before_geometry_sha256=_sha({'vertices_cm': before_points, 'triangles': before_triangles}),
        after_geometry_sha256=_sha({'vertices_cm': points, 'triangles': triangles}),
        assets_bound=False, passed=True)
    surface.setdefault('native_seam_extensions', []).append(proposal)
    bounded()


def repair_source_seams(run, surfaces, landscape_z, empty_geos=(), max_repairs=1,
                        cap_cm=10.0, extension_cm=0.1, max_seconds=180.0):
    """Return JSON proof; modify only supplied fitted transient surfaces in place.

    All existing native geometry remains bit-for-bit unchanged. A missing
    source point outside the10cm genuine asphalt boundary fails closed. Final
    full-source actual-triangle coverage/height proof is mandatory. The owner
    repeats it after named asset binding and exact geographic clipping.
    """
    import geocity_roadbld_workflow as base
    import geocity_roadbld_grounding as grounding
    assert callable(landscape_z) and 1 <= max_repairs <= 8 and 0 < max_seconds <= 600
    assert 0 < cap_cm <= 10.0 and 0 < extension_cm <= 0.1
    began = time.monotonic()
    def bounded():
        run.guard()
        assert time.monotonic()-began <= max_seconds, 'Bounded transient native seam repair timed out'
    bounded()
    surfaces = list(surfaces)
    assert surfaces and len({surface['component_path'] for surface in surfaces}) == len(surfaces)
    rows = [dict(row, road_actor_path=base._path(road)) for road, row in zip(run.roads, run.plan['roads'])]
    assert len(rows) == len(run.roads) == run.plan['source_piece_count']
    owned = {base._path(road) for road in run.roads+list(getattr(run, 'derived_junction_roads', []))}
    assert all(set(surface['native_source_road_paths']).issubset(owned) for surface in surfaces)
    fields = {surface['component_path']: grounding.AsphaltField(surface['points_cm'], surface['triangles'],
        surface['material_ids'], surface['upward']) for surface in surfaces}
    patches = []
    clearance = float(run.plan['settings']['surface_clearance_cm'])
    for row in rows:
        path = row['road_actor_path']
        candidates = [surface for surface in surfaces if path in surface['source_road_paths']]
        assert candidates, 'Source road has no owned native geometry'
        for number, (point, segment, fraction) in enumerate(grounding._samples(row, clearance, 100.0)):
            if number % 128 == 0:
                bounded()
            if any(grounding._source_eligibility(surface, path, point) is not None and fields[surface['component_path']].covered(point)
                   for surface in candidates):
                continue
            assert len(patches) < max_repairs, 'Additional native source seams exceed the bounded repair count'
            proposal = plan_boundary_fan(path, point, surfaces, fields, landscape_z, clearance, cap_cm, extension_cm)
            proposal.update(source_osm_id=str(row['source_osm_id']), piece_id=row['piece_id'],
                            source_segment_index=segment, source_segment_fraction=fraction)
            surface = next(surface for surface in surfaces if surface['component_path']==proposal['component_path'])
            _append_fan(surface, proposal, bounded)
            fields[surface['component_path']] = grounding.AsphaltField(surface['points_cm'], surface['triangles'], surface['material_ids'], surface['upward'])
            assert fields[surface['component_path']].covered(point), 'Appended native seam still misses the exact source point'
            patches.append(proposal)
    coverage = grounding.verify_source_coverage(run.plan, rows, surfaces, landscape_z, empty_geos, guard=bounded)
    return {'schema': SCHEMA, 'phase': 'transient_native_seams_physically_verified_pending_bind',
        'source_sha256': run.plan['source_sha256'], 'centreline_sha256': run.plan['centreline_sha256'],
        'repairs': patches, 'repair_count': len(patches), 'xy_extension_cap_cm': cap_cm,
        'existing_coordinate_changes': 0, 'source_coverage': coverage,
        'native_uv_material_and_normals_preserved': True, 'assets_bound': False, 'saved': False,
        'elapsed_seconds': time.monotonic()-began, 'passed': True}
