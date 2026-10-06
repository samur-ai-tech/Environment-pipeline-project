"""Ground actual native RoadBLD meshes on the authoritative Landscape.

Import is inert. The owner supplies a verified, single-Landscape collision
sampler. Only copied transient meshes are edited; retained asset creation,
binding, clipping, named saves and reopen are the owner's normal lifecycle.
XY, topology, UVs, materials and the native curb/underside offsets survive.
"""
import hashlib
import json
import math
import time

SCHEMA = 'environmentpipeline.roadbld_native_grounding.v1'


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode('utf-8')).hexdigest()


def _finite_point(point):
    return len(point) == 3 and all(math.isfinite(float(value)) for value in point)


def _cells(bounds, size):
    for x in range(math.floor(bounds[0] / size), math.floor(bounds[2] / size) + 1):
        for y in range(math.floor(bounds[1] / size), math.floor(bounds[3] / size) + 1):
            yield x, y


def _barycentric(point, a, b, c):
    ux, uy = b[0] - a[0], b[1] - a[1]
    vx, vy = c[0] - a[0], c[1] - a[1]
    determinant = ux * vy - uy * vx
    if abs(determinant) <= 1e-8:
        return None
    px, py = point[0] - a[0], point[1] - a[1]
    s = (px * vy - py * vx) / determinant
    t = (ux * py - uy * px) / determinant
    return 1.0 - s - t, s, t


def _plane_z(weights, triangle):
    return sum(weight * vertex[2] for weight, vertex in zip(weights, triangle))


def _closest_xy(point, triangle):
    weights = _barycentric(point, *triangle)
    if weights and min(weights) >= -1e-9:
        return 0.0, (point[0], point[1])
    candidates = []
    for a, b in zip(triangle, triangle[1:] + triangle[:1]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length2 = dx * dx + dy * dy
        fraction = max(0.0, min(1.0, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length2)) if length2 else 0.0
        closest = a[0] + fraction * dx, a[1] + fraction * dy
        candidates.append((math.hypot(point[0] - closest[0], point[1] - closest[1]), closest))
    return min(candidates)


class AsphaltField:
    """Pure world-XY index of explicitly selected upward native asphalt faces."""

    def __init__(self, points, triangles, material_ids, upward=None, cell_cm=200.0):
        assert len(triangles) == len(material_ids) and cell_cm > 0
        assert all(_finite_point(point) for point in points)
        if upward is not None:
            assert len(upward) == len(triangles)
        self.points, self.triangles = points, triangles
        self.cell_cm, self.faces, self.grid = float(cell_cm), {}, {}
        for number, indices in enumerate(triangles):
            assert len(indices) == 3 and all(0 <= index < len(points) for index in indices)
            if int(material_ids[number]) != 0:
                continue
            triangle = [points[index] for index in indices]
            a, b, c = triangle
            ux, uy, uz = (b[k] - a[k] for k in range(3))
            vx, vy, vz = (c[k] - a[k] for k in range(3))
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            norm = math.sqrt(nx * nx + ny * ny + nz * nz)
            selected = bool(upward[number]) if upward is not None else norm > 1e-8 and nz / norm > 0.25
            if not selected or abs(nz) <= 1e-8:
                continue
            self.faces[number] = triangle
            bounds = min(v[0] for v in triangle), min(v[1] for v in triangle), max(v[0] for v in triangle), max(v[1] for v in triangle)
            for cell in _cells(bounds, self.cell_cm):
                self.grid.setdefault(cell, []).append(number)
        assert self.faces, 'Native mesh has no explicitly upward material0 asphalt triangles'

    def covered(self, point):
        candidates = []
        # Native render positions are float32. At an exact geographic endpoint
        # the rounded mesh boundary can differ by a few thousandths of a cm.
        # Permit only 0.01 cm (0.1 mm) of XY quantization, measured in world XY.
        boundary_cm = 0.01
        indices = {number for cell in _cells((point[0]-boundary_cm, point[1]-boundary_cm,
                    point[0]+boundary_cm, point[1]+boundary_cm), self.cell_cm)
                   for number in self.grid.get(cell, ())}
        for number in indices:
            triangle = self.faces[number]
            weights = _barycentric(point, *triangle)
            if weights is not None and min(weights) >= -1e-9:
                candidates.append((_plane_z(weights, triangle), number, weights))
            elif weights is not None:
                distance, projected = _closest_xy(point, triangle)
                if distance <= boundary_cm:
                    weights = _barycentric(projected, *triangle)
                    candidates.append((_plane_z(weights, triangle), number, weights))
        return max(candidates, key=lambda row: (row[0], -row[1])) if candidates else None

    def reference(self, point, max_lateral_cm):
        covered = self.covered(point)
        if covered:
            return covered[0], covered[1], 0.0
        bounds = point[0] - max_lateral_cm, point[1] - max_lateral_cm, point[0] + max_lateral_cm, point[1] + max_lateral_cm
        indices = {number for cell in _cells(bounds, self.cell_cm) for number in self.grid.get(cell, ())}
        candidates = []
        for number in sorted(indices):
            triangle = self.faces[number]
            distance, unused = _closest_xy(point, triangle)
            if distance <= max_lateral_cm:
                # Evaluate the same asphalt plane at original XY, not the
                # projected point, preserving native lateral curb offsets.
                z = _plane_z(_barycentric(point, *triangle), triangle)
                candidates.append((distance, -z, number, z))
        if not candidates:
            nearest = min((_closest_xy(point, triangle)[0], number) for number, triangle in self.faces.items())
            raise AssertionError('Native vertex has no bounded adjacent asphalt reference: point=%r nearest_distance_cm=%r triangle=%r limit_cm=%r' % (point, nearest[0], nearest[1], max_lateral_cm))
        distance, unused, number, z = min(candidates)
        return z, number, distance


def ground_geometry(points, triangles, material_ids, landscape_z, clearance_cm=5.0,
                    max_lateral_cm=300.0, upward=None, guard=None, reference_field=None):
    """Pure geometry arithmetic; sampler is supplied by the editor owner."""
    assert callable(landscape_z) and 0 < max_lateral_cm <= 300.0
    assert math.isfinite(clearance_cm) and 0 <= clearance_cm <= 10.0
    field = AsphaltField(points, triangles, material_ids, upward)
    cache, changed, maximum_delta, maximum_lateral, fallback_samples = {}, [], 0.0, 0.0, []
    for index, point in enumerate(points):
        if guard and index % 256 == 0:
            guard()
        # Copied vertices sharing XY get the same offset, including split
        # vertices at UV/material seams and bottom/curb extrusion vertices.
        key = (round(point[0], 6), round(point[1], 6))
        if key not in cache:
            try:
                base_z, triangle, lateral = field.reference(point, max_lateral_cm)
            except AssertionError as exc:
                if not str(exc).startswith('Native vertex has no bounded adjacent asphalt reference') or reference_field is None:
                    raise
                base_z, triangle, lateral, provenance = reference_field.reference(point, max_lateral_cm)
                fallback_samples.append(dict(provenance, vertex_xy_cm=list(point[:2]),
                    reference_asphalt_z_cm=base_z, reference_triangle_index=triangle,
                    lateral_reference_cm=lateral))
            ground_z = float(landscape_z(float(point[0]), float(point[1])))
            assert math.isfinite(ground_z), 'Authoritative Landscape collision sample is missing'
            delta = ground_z + clearance_cm - base_z
            cache[key] = (delta, lateral)
        delta, lateral = cache[key]
        changed.append([point[0], point[1], point[2] + delta])
        maximum_delta = max(maximum_delta, abs(delta))
        maximum_lateral = max(maximum_lateral, lateral)
    assert all(before[:2] == after[:2] for before, after in zip(points, changed))
    # A material0 triangle that itself folds or becomes downward is invalid;
    # vertical displacement cannot change its signed XY projection.
    grounded_field = AsphaltField(changed, triangles, material_ids, upward)
    assert set(grounded_field.faces) == set(field.faces)
    proof = {'vertex_count': len(points), 'triangle_count': len(triangles),
             'asphalt_top_triangle_count': len(field.faces), 'sampled_xy_count': len(cache),
             'max_vertical_delta_cm': maximum_delta, 'max_lateral_reference_cm': maximum_lateral,
             'clearance_cm': clearance_cm, 'xy_unchanged': True, 'topology_unchanged': True,
             'same_xy_same_delta': True, 'original_geometry_sha256': _sha({'vertices_cm': points, 'triangles': triangles}),
             'grounded_geometry_sha256': _sha({'vertices_cm': changed, 'triangles': triangles}),
             'material_ids_sha256': _sha(material_ids),
             'same_source_union_fallback_sample_count': len(fallback_samples),
             'same_source_union_fallback_samples': fallback_samples}
    return changed, proof


def _samples(row, clearance_cm, interval_cm):
    points = [[float(p[0]) * 100.0, float(p[2]) * 100.0, float(p[1]) * 100.0 + clearance_cm] for p in row['points_m']]
    assert len(points) >= 2 and all(_finite_point(p) for p in points)
    yield points[0], 0, 0.0
    for index, (a, b) in enumerate(zip(points, points[1:])):
        count = max(1, math.ceil(math.dist(a[:2], b[:2]) / interval_cm))
        for sample in range(1, count + 1):
            fraction = sample / count
            yield [a[k] + fraction * (b[k] - a[k]) for k in range(3)], index, fraction


def _source_eligibility(surface, path, point):
    """Native membership, or one validated connector's exact parent trim zone."""
    native_paths = surface.get('native_source_road_paths', surface['source_road_paths'])
    if path in native_paths:
        return {'basis': 'native_source_membership'}
    eligible = []
    for proof in surface.get('derived_parent_provenance', []):
        if proof['parent_road_actor_path'] != path or proof['road_actor_path'] not in native_paths:
            continue
        trim = proof['native_endpoint_trim']
        endpoint = trim['source_endpoint_world_cm']
        distance = math.dist(point[:2], endpoint[:2])
        if distance <= float(trim['pullback_cm']) + 0.1:
            eligible.append(proof)
    if eligible:
        return {'basis': 'validated_derived_parent_inside_exact_endpoint_trim',
                'derived_parent_provenance': sorted(eligible, key=lambda row: row['derived_id'])}
    return None


def _parent_trim_cross_section_support(own, reference, path, point, reference_xy, max_lateral_cm):
    """Ground a lateral connector vertex from its proven parent's pavement.

    Query XY must lie longitudinally inside the exact removed parent trim.
    The nearest actual asphalt must be on that named parent's retained side
    of the join and inside its measured pavement width. The reference search
    still has the unchanged 300cm Euclidean cap. This predicate neither moves
    the trim boundary nor changes final source-centerline coverage eligibility.
    """
    assert 0 < max_lateral_cm <= 300.0
    if path not in reference['native_source_road_paths']:
        return None
    for proof in own.get('derived_parent_provenance', []):
        if (proof['parent_road_actor_path'] != path or
                proof['road_actor_path'] not in own['native_source_road_paths']):
            continue
        assert proof['native_controls_widths_policy_links_and_corridor_verified'] is True
        trim = proof['native_endpoint_trim']
        a, b = trim['source_endpoint_world_cm'], trim['native_endpoint_world_cm']
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        assert 0 < length <= 200.1 and abs(length - float(trim['pullback_cm'])) <= 0.1
        half_width = float(proof['parent_full_width_cm']) * 0.5
        assert math.isfinite(half_width) and half_width > 0
        projections = []
        for p in (point, reference_xy):
            along = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length
            across = abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / length
            projections.append((along, across))
        # Existing 0.1cm native readback tolerance, not a longer source trim.
        if not -0.1 <= projections[0][0] <= length + 0.1:
            continue
        if projections[0][1] > half_width + max_lateral_cm + 0.1:
            continue
        # Prove the reference against the actual verified retained native
        # endpoint segment, not an infinite extension of the removed trim.
        retained = proof['parent_retained_endpoint_segment_world_cm']
        assert len(retained) == 2 and all(_finite_point(p) for p in retained)
        assert math.dist(retained[0], b) <= 0.1
        rx, ry = retained[1][0] - retained[0][0], retained[1][1] - retained[0][1]
        retained_length = math.hypot(rx, ry)
        assert retained_length > 0
        reference_along = ((reference_xy[0] - retained[0][0]) * rx +
                           (reference_xy[1] - retained[0][1]) * ry) / retained_length
        reference_across = abs((reference_xy[0] - retained[0][0]) * ry -
                               (reference_xy[1] - retained[0][1]) * rx) / retained_length
        if not -0.1 <= reference_along <= retained_length + 0.1 or reference_across > half_width + 0.1:
            continue
        actual_distance = math.dist(point[:2], reference_xy)
        if not math.isfinite(actual_distance) or actual_distance > max_lateral_cm:
            continue
        return {'basis': 'validated_linked_parent_trim_cross_section',
                'source_road_actor_path': path, 'derived_parent_provenance': proof,
                'trim_longitudinal_length_cm': length, 'parent_pavement_half_width_cm': half_width,
                'query_longitudinal_cm': projections[0][0], 'query_lateral_cm': projections[0][1],
                'reference_longitudinal_cm': projections[1][0], 'reference_lateral_cm': projections[1][1],
                'reference_longitudinal_side': 'retained_named_parent_pavement',
                'reference_retained_segment_along_cm': reference_along,
                'reference_retained_segment_across_cm': reference_across,
                'retained_endpoint_segment_length_cm': retained_length,
                'nearest_actual_asphalt_xy_cm': list(reference_xy),
                'actual_asphalt_distance_cm': actual_distance,
                'unchanged_max_asphalt_distance_cm': max_lateral_cm}
    return None


class SameSourceAsphaltReference:
    """Bounded fallback across original owned native copies, never whole-world geometry."""

    def __init__(self, own, surfaces, fields, guard=None):
        self.own, self.surfaces, self.fields, self.guard = own, surfaces, fields, guard

    def reference(self, point, max_lateral_cm):
        assert 0 < max_lateral_cm <= 300.0
        own_native = set(self.own['native_source_road_paths'])
        candidates, eligible_fields = [], []
        for surface in self.surfaces:
            if surface['component_path'] == self.own['component_path']:
                continue
            actual_common = sorted(own_native.intersection(surface['native_source_road_paths']))
            effective_common = sorted(set(self.own['source_road_paths']).intersection(surface['source_road_paths']))
            if not actual_common and not effective_common:
                continue
            derived_support = []
            if not actual_common:
                for path in effective_common:
                    own_proof = _source_eligibility(self.own, path, point)
                    other_proof = _source_eligibility(surface, path, point)
                    if own_proof is not None and other_proof is not None:
                        derived_support.append({'source_road_actor_path': path,
                            'own_eligibility': own_proof, 'reference_eligibility': other_proof})
            field = self.fields[surface['component_path']]
            if actual_common or derived_support:
                eligible_fields.append((surface, field))
            if self.guard:
                self.guard()
            try:
                z, number, lateral = field.reference(point, max_lateral_cm)
            except AssertionError as exc:
                if not str(exc).startswith('Native vertex has no bounded adjacent asphalt reference'):
                    raise
                continue
            if not actual_common and not derived_support:
                # Centerline trim provenance is a longitudinal restriction.
                # A native curb vertex at its joining cross-section can be
                # outside the centreline's radial disk while its named parent
                # asphalt remains within the unchanged physical 300cm cap.
                # Keep the final centreline coverage predicate unchanged.
                unused, reference_xy = _closest_xy(point, field.faces[number])
                for path in effective_common:
                    support = _parent_trim_cross_section_support(
                        self.own, surface, path, point, reference_xy, max_lateral_cm)
                    if support is not None:
                        derived_support.append(support)
                if not derived_support:
                    continue
                eligible_fields.append((surface, field))
            provenance = {'basis': 'actual_owned_same_source_asphalt_union' if actual_common else 'validated_derived_parent_trim_asphalt_union',
                'own_component_path': self.own['component_path'],
                'reference_component_path': surface['component_path'],
                'reference_geometry_actor_path': surface['geometry_actor_path'],
                'own_native_source_road_paths': self.own['native_source_road_paths'],
                'reference_native_source_road_paths': surface['native_source_road_paths'],
                'shared_actual_native_source_road_paths': actual_common,
                'derived_trim_support': derived_support,
                'reference_triangle_world_cm': field.faces[number]}
            candidates.append((lateral, -z, surface['component_path'], number, z, provenance))
        if not candidates:
            # Diagnose actual nearest distances without expanding acceptance.
            distances = []
            own_field = self.fields[self.own['component_path']]
            for surface, field in [(self.own, own_field)] + eligible_fields:
                minimum = math.inf
                for index, triangle in enumerate(field.faces.values()):
                    if self.guard and index % 512 == 0:
                        self.guard()
                    minimum = min(minimum, _closest_xy(point, triangle)[0])
                distances.append({'component_path': surface['component_path'], 'nearest_asphalt_xy_cm': minimum})
            raise AssertionError('Same-source native asphalt union has no bounded reference: ' + json.dumps({
                'component_path': self.own['component_path'], 'point_world_cm': point,
                'lateral_cap_cm': max_lateral_cm, 'nearest_distances': distances}, allow_nan=False))
        lateral, unused, component, number, z, provenance = min(candidates, key=lambda row: row[:4])
        return z, number, lateral, provenance


def verify_source_coverage(plan, rows, surfaces, landscape_z=None, empty_geos=(),
                           interval_cm=100.0, tolerance_cm=10.0, guard=None):
    """Pure final physical proof using actual owned upward asphalt triangles.

    surfaces entries: component_path, geometry_actor_path, source_road_paths,
    points_cm, triangles, material_ids, optional upward mask. rows must include
    their exact road_actor_path. No authored-profile samples can replace mesh.
    """
    assert 0 < interval_cm <= 100.0 and 0 < tolerance_cm <= 10.0
    clearance = float(plan['settings']['surface_clearance_cm'])
    prepared = []
    for surface in surfaces:
        field = AsphaltField(surface['points_cm'], surface['triangles'], surface['material_ids'], surface.get('upward'))
        prepared.append((surface, field))
    assert prepared, 'No actual native asphalt geometry'
    assert len(rows) == plan['source_piece_count']
    proofs, by_path = [], {}
    for row in rows:
        path = row['road_actor_path']
        candidates = [(surface, field) for surface, field in prepared if path in surface['source_road_paths']]
        assert candidates, 'Source road has no actual same-source native geometry: ' + path
        maximum, source_ground_difference, checked, used, samples, derived_used = 0.0, 0.0, 0, set(), [], {}
        for point, segment, fraction in _samples(row, clearance, interval_cm):
            if guard and checked % 128 == 0:
                guard()
            covered = [(field.covered(point), surface, _source_eligibility(surface, path, point)) for surface, field in candidates]
            covered = [(value, surface, provenance) for value, surface, provenance in covered if value is not None and provenance is not None]
            assert covered, 'Source centerline is not covered by actual native top triangles: ' + path
            value, surface, provenance = max(covered, key=lambda pair: (pair[0][0], pair[1]['component_path']))
            z, triangle, weights = value
            expected = float(landscape_z(point[0], point[1])) + clearance if landscape_z else point[2]
            assert math.isfinite(expected)
            error = abs(z - expected)
            maximum = max(maximum, error)
            source_ground_difference = max(source_ground_difference, abs(expected - point[2]))
            assert error <= tolerance_cm, 'Actual native asphalt exceeds source-ground height tolerance: %s point_cm=%r actual_z=%r expected_z=%r error_cm=%r component=%s triangle=%r' % (path, point, z, expected, error, surface['component_path'], triangle)
            # Every original exported point remains an independent ground
            # constraint even when additional Landscape samples are provided.
            if fraction in (0.0, 1.0):
                assert abs(z - point[2]) <= tolerance_cm, 'Native asphalt differs from original exported ground height'
            used.add(surface['geometry_actor_path'])
            for proof in provenance.get('derived_parent_provenance', []):
                derived_used[(proof['road_actor_path'], proof['parent_road_actor_path'])] = proof
            samples.append([point[0], point[1], expected, z, surface['component_path'], triangle, provenance])
            checked += 1
        record = {'road_actor_path': path, 'source_osm_id': str(row['source_osm_id']), 'piece_id': row['piece_id'],
                  'sample_count': checked, 'max_sample_spacing_cm': interval_cm,
                  'max_surface_height_error_cm': maximum, 'max_landscape_vs_source_interpolation_cm': source_ground_difference,
                  'geometry_actor_paths': sorted(used), 'physical_sample_sha256': _sha(samples),
                  'derived_parent_coverage': [derived_used[key] for key in sorted(derived_used)], 'passed': True}
        proofs.append(record)
        by_path[path] = record
    empty_proofs = []
    for empty in empty_geos:
        paths = sorted(empty['source_road_paths'])
        assert paths, 'Empty native geometry has no source provenance'
        support = []
        for path in paths:
            assert path in by_path, 'Empty native geometry references a non-source road'
            alternatives = [(surface, field) for surface, field in prepared
                            if surface['geometry_actor_path'] != empty['geometry_actor_path']
                            and path in surface['source_road_paths']
                            and len(surface.get('native_source_road_paths', surface['source_road_paths'])) >= 2]
            assert alternatives, 'Empty native geometry has no owned same-source merged replacement'
            row = next(row for row in rows if row['road_actor_path'] == path)
            used, maximum = set(), 0.0
            for sample_number, (point, unused, fraction) in enumerate(_samples(row, clearance, interval_cm)):
                if guard and sample_number % 128 == 0:
                    guard()
                covering = [(field.covered(point), surface) for surface, field in alternatives
                            if _source_eligibility(surface, path, point) is not None]
                covering = [(value, surface) for value, surface in covering if value is not None]
                assert covering, 'Empty RoadGeo source is not entirely covered by another owned merged RoadGeo'
                value, surface = max(covering, key=lambda pair: pair[0][0])
                expected = float(landscape_z(point[0], point[1])) + clearance if landscape_z else point[2]
                error = abs(value[0] - expected)
                maximum = max(maximum, error)
                assert error <= tolerance_cm
                if fraction in (0.0, 1.0):
                    assert abs(value[0] - point[2]) <= tolerance_cm
                used.add(surface['geometry_actor_path'])
            support.append({'road_actor_path': path, 'replacement_geometry_actor_paths': sorted(used),
                            'max_surface_height_error_cm': maximum, 'full_source_covered': True})
        empty_proofs.append({'geometry_actor_path': empty['geometry_actor_path'], 'source_road_paths': paths,
                             'null_component_paths': empty.get('null_static_mesh_components', []),
                             'replacement_proof': support, 'automatic_empty_placeholder': True, 'passed': True})
    return {'schema': SCHEMA, 'basis': 'actual upward native asphalt triangles; exact source XY; authoritative ground',
            'xy_float32_boundary_tolerance_cm': 0.01,
            'source_sha256': plan['source_sha256'], 'centreline_sha256': plan['centreline_sha256'],
            'source_road_count': len(rows), 'source_piece_count': plan['source_piece_count'],
            'source_roads': proofs, 'automatic_empty_geometry': empty_proofs,
            'max_surface_height_error_cm': max(row['max_surface_height_error_cm'] for row in proofs), 'passed': True}


def _interval_union(values):
    result = []
    for lo, hi in sorted(values):
        lo, hi = max(0.0, lo), min(1.0, hi)
        if hi < lo:
            continue
        if result and lo <= result[-1][1] + 1e-13:
            result[-1][1] = max(result[-1][1], hi)
        else:
            result.append([lo, hi])
    return result


def _ring_location(point, ring):
    """Strict interior; numerical edge recognition does not enlarge a pad."""
    inside = False
    for a, b in zip(ring, ring[1:] + ring[:1]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length2 = dx * dx + dy * dy
        if length2:
            t = ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length2
            if 0 <= t <= 1 and math.hypot(point[0] - a[0] - t * dx,
                                          point[1] - a[1] - t * dy) <= 1e-8:
                return 'boundary'
        if (a[1] > point[1]) != (b[1] > point[1]):
            if point[0] < a[0] + (b[0] - a[0]) * (point[1] - a[1]) / (b[1] - a[1]):
                inside = not inside
    return 'interior' if inside else 'exterior'


def _ring_intervals(a, b, ring):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    cuts = [0.0, 1.0]
    for p, q in zip(ring, ring[1:] + ring[:1]):
        ex, ey = q[0] - p[0], q[1] - p[1]
        cross = dx * ey - dy * ex
        if abs(cross) > 1e-12:
            t = ((p[0] - a[0]) * ey - (p[1] - a[1]) * ex) / cross
            u = ((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / cross
            if 0 <= t <= 1 and 0 <= u <= 1:
                cuts.append(t)
        elif length2 and abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) <= 1e-8:
            for v in (p, q):
                t = ((v[0] - a[0]) * dx + (v[1] - a[1]) * dy) / length2
                if 0 <= t <= 1:
                    cuts.append(t)
    cuts = sorted(set(cuts))
    return [[lo, hi] for lo, hi in zip(cuts, cuts[1:]) if hi > lo and
            _ring_location([a[0] + (lo + hi) * .5 * dx,
                            a[1] + (lo + hi) * .5 * dy], ring) == 'interior']


def analyze_protected_source_intervals(plan, rows=None, guard=None):
    """Pure r018 visible-policy diagnostic, not a road/pad source modification."""
    rows = plan['roads'] if rows is None else rows
    pads = plan['protected_building_footprints_xz_m']
    assert _sha(pads) == plan['protected_footprint_proof']['footprints_sha256']
    assert len(pads) == plan['protected_footprint_proof']['source_pad_count']
    assert len({str(p['source_osm_id']) for p in pads}) == len(pads)
    assert len(rows) == plan['source_piece_count']
    assert {r['piece_id'] for r in rows} == set(plan['drivable_piece_ids'])
    assert len({r['piece_id'] for r in rows}) == len(rows)
    originals = {r['piece_id']: r for r in plan['roads']}
    for row in rows:
        for name in ('source_osm_id', 'points_m', 'width_m'):
            assert row[name] == originals[row['piece_id']][name], 'Partition row differs from geographic plan'
    prepared = []
    for pad in pads:
        ring = [[float(v[0]) * 100, float(v[1]) * 100] for v in pad['ring_xz_m']]
        assert len(ring) >= 3 and all(all(math.isfinite(x) for x in v) for v in ring)
        prepared.append((str(pad['source_osm_id']), ring,
                         (min(v[0] for v in ring), min(v[1] for v in ring),
                          max(v[0] for v in ring), max(v[1] for v in ring))))
    records = []
    for row in rows:
        if guard:
            guard()
        points = [[p[0] * 100.0, p[2] * 100.0] for p in row['points_m']]
        segments = []
        for number, (a, b) in enumerate(zip(points, points[1:])):
            length = math.dist(a, b)
            values = []
            for pad_id, ring, box in prepared:
                if (max(a[0], b[0]) < box[0] or min(a[0], b[0]) > box[2] or
                        max(a[1], b[1]) < box[1] or min(a[1], b[1]) > box[3]):
                    continue
                for lo, hi in _ring_intervals(a, b, ring):
                    values.append({'pad_source_osm_id': pad_id, 't0': lo, 't1': hi,
                        'length_cm': (hi - lo) * length,
                        'entry_xy_cm': [a[k] + lo * (b[k] - a[k]) for k in range(2)],
                        'exit_xy_cm': [a[k] + hi * (b[k] - a[k]) for k in range(2)]})
            if values:
                union = _interval_union((v['t0'], v['t1']) for v in values)
                segments.append({'segment_index': number, 'intervals': values,
                    'excluded_union': union, 'excluded_length_cm': sum((hi-lo)*length for lo, hi in union)})
        records.append({'source_osm_id': str(row['source_osm_id']), 'piece_id': row['piece_id'],
            'source_points_sha256': _sha(row['points_m']), 'segments': segments,
            'excluded_length_cm': sum(v['excluded_length_cm'] for v in segments)})
    conflicts = [v for v in records if v['segments']]
    return {'schema': 'environmentpipeline.roadbld_visible_source_partition.v1',
        'policy': 'r018_exact_protected_footprint_visible_surface_exclusion',
        'source_sha256': plan['source_sha256'], 'centreline_sha256': plan['centreline_sha256'],
        'protected_footprints_sha256': _sha(pads), 'source_piece_count': len(rows),
        'source_roads': records, 'source_conflicts': conflicts,
        'excluded_length_cm': sum(v['excluded_length_cm'] for v in records),
        'physical_surface_continuous': not conflicts,
        'diagnostic_only': True, 'source_or_geometry_changes': False}


def _linear_interval(values):
    """Intersection of affine inequalities v(t)>=0 with the unit segment."""
    lo, hi = 0.0, 1.0
    for start, end in values:
        delta = end - start
        if delta == 0:
            if start < 0:
                return None
        elif delta > 0:
            lo = max(lo, -start / delta)
        else:
            hi = min(hi, -start / delta)
    return [lo, hi] if lo <= hi else None


def _circle_interval(a, b, centre, radius):
    dx, dy = b[0] - a[0], b[1] - a[1]
    px, py = a[0] - centre[0], a[1] - centre[1]
    aa, bb, cc = dx*dx + dy*dy, 2*(px*dx + py*dy), px*px + py*py - radius*radius
    if aa == 0:
        return [0.0, 1.0] if cc <= 0 else None
    discriminant = bb*bb - 4*aa*cc
    if discriminant < 0:
        return None
    root = math.sqrt(discriminant)
    lo, hi = max(0.0, (-bb-root)/(2*aa)), min(1.0, (-bb+root)/(2*aa))
    return [lo, hi] if lo <= hi else None


def _triangle_intervals(a, b, triangle):
    """Actual XY triangle plus the existing 0.01cm Euclidean boundary tolerance."""
    values = []
    wa, wb = _barycentric(a, *triangle), _barycentric(b, *triangle)
    if wa is not None and wb is not None:
        hit = _linear_interval(list(zip(wa, wb)))
        if hit:
            values.append(hit)
    for p, q in zip(triangle, triangle[1:] + triangle[:1]):
        dx, dy = q[0] - p[0], q[1] - p[1]
        length = math.hypot(dx, dy)
        if length:
            along = [((v[0]-p[0])*dx + (v[1]-p[1])*dy)/length for v in (a, b)]
            across = [((v[0]-p[0])*dy - (v[1]-p[1])*dx)/length for v in (a, b)]
            hit = _linear_interval([(along[0], along[1]), (length-along[0], length-along[1]),
                (.01-across[0], .01-across[1]), (.01+across[0], .01+across[1])])
            if hit:
                values.append(hit)
        hit = _circle_interval(a, b, p, .01)
        if hit:
            values.append(hit)
    return _interval_union(values)


def _physical_segment_intervals(a, b, path, candidates):
    values = []
    for surface, field in candidates:
        native = surface.get('native_source_road_paths', surface['source_road_paths'])
        allowed = [[0.0, 1.0]] if path in native else []
        if not allowed:
            for proof in surface.get('derived_parent_provenance', []):
                if proof['parent_road_actor_path'] == path and proof['road_actor_path'] in native:
                    trim = proof['native_endpoint_trim']
                    hit = _circle_interval(a, b, trim['source_endpoint_world_cm'], float(trim['pullback_cm']) + .1)
                    if hit:
                        allowed.append(hit)
        if not allowed:
            continue
        bounds = (min(a[0], b[0])-.01, min(a[1], b[1])-.01,
                  max(a[0], b[0])+.01, max(a[1], b[1])+.01)
        numbers = {n for cell in _cells(bounds, field.cell_cm) for n in field.grid.get(cell, ())}
        for number in numbers:
            for lo, hi in _triangle_intervals(a, b, field.faces[number]):
                for start, end in allowed:
                    if max(lo, start) <= min(hi, end):
                        values.append([max(lo, start), min(hi, end)])
    return _interval_union(values)


def _verify_partition_ledger(plan, rows, surfaces, clipping, preclip):
    assert clipping and preclip and preclip.get('passed') is True
    for name in ('source_sha256', 'centreline_sha256'):
        assert clipping[name] == preclip[name] == plan[name], 'Source identity changed before partition proof'
    assert clipping['area_id'] == plan['area_id'] and clipping['named_map'] == plan['named_map']
    assert clipping['protected_footprints_sha256'] == _sha(plan['protected_building_footprints_xz_m'])
    assert clipping['status'] == 'native_conflicts_clipped_pending_independent_fit_saves_and_reopen'
    prior = preclip['source_coverage']
    assert prior['passed'] is True and prior['source_piece_count'] == len(rows)
    assert prior['source_sha256'] == plan['source_sha256'] and prior['centreline_sha256'] == plan['centreline_sha256']
    assert {p['piece_id'] for p in prior['source_roads']} == {p['piece_id'] for p in rows}
    assert all(p['passed'] for p in prior['source_roads'])
    prior_by_id = {v['piece_id']: v for v in prior['source_roads']}
    for row in rows:
        assert prior_by_id[row['piece_id']]['road_actor_path'] == row['road_actor_path']
        assert prior_by_id[row['piece_id']]['source_osm_id'] == str(row['source_osm_id'])
    bindings = {v['component']: v for v in clipping['bindings']}
    assert len(bindings) == len(clipping['bindings']) == len(surfaces) == preclip['native_component_count']
    assert set(bindings) == {s['component_path'] for s in surfaces}
    verified = []
    for surface in surfaces:
        binding = bindings[surface['component_path']]
        assert binding['binding_applied'] and binding['actual_rebound_triangles_verified']
        assert binding['actor'] == surface['geometry_actor_path']
        assert binding['clipped_mesh'] == surface['original_mesh_path']
        assert binding['component_world_transform'] == surface['frame']
        assert binding['material_slots'] == surface['material_slots']
        assert binding['attributes_after'] == surface['attributes']
        digest = _sha({'vertices_cm': surface['points_cm'], 'triangles': surface['triangles']})
        assert digest == binding['clipped_world_triangle_geometry_sha256'], 'Bound candidate geometry differs from immutable clipping proof'
        fit = binding['after']
        assert fit['passed'] and not fit['conflicting_pad_ids'] and not fit['overlap_m2_by_pad']
        assert fit['max_area_escape_cm'] <= 2.0
        verified.append({'component_path': surface['component_path'], 'geometry_sha256': digest})
    return {'immutable_clip_report_sha256': _sha(clipping), 'preclip_report_sha256': _sha(preclip),
        'current_bound_geometry_matches_measured_clip_fit': True, 'components': verified,
        'building_overlap_tolerance_m2': .0001, 'area_boundary_tolerance_cm': 2.0}


def verify_clipped_source_partition(plan, rows, surfaces, landscape_z, clipping_report,
                                    preclip_grounding_report, empty_geos=(), guard=None):
    """Full source accounting under the retained r018 visible-pad policy.

    Interior exclusions are NOT asphalt, height evidence, or driveable continuity.
    The unconditional preclip verify_source_coverage remains a separate proof.
    """
    ledger = _verify_partition_ledger(plan, rows, surfaces, clipping_report, preclip_grounding_report)
    analysis = analyze_protected_source_intervals(plan, rows, guard)
    prepared = [(s, AsphaltField(s['points_cm'], s['triangles'], s['material_ids'], s.get('upward'))) for s in surfaces]
    # Preserve the strict no-exclusion station/height proof and its report,
    # adding continuous actual triangle coverage rather than changing gates.
    if not analysis['source_conflicts']:
        result = verify_source_coverage(plan, rows, surfaces, landscape_z, empty_geos, guard=guard)
        for row in rows:
            candidates = [(s, f) for s, f in prepared if row['road_actor_path'] in s['source_road_paths']]
            points = [[p[0]*100.0, p[2]*100.0] for p in row['points_m']]
            for index, (a, b) in enumerate(zip(points, points[1:])):
                if guard and index % 64 == 0:
                    guard()
                intervals = _physical_segment_intervals(a, b, row['road_actor_path'], candidates)
                assert len(intervals) == 1 and intervals[0][0] <= 1e-13 and intervals[0][1] >= 1-1e-13, 'Uncovered native source interval: %s segment=%s' % (row['piece_id'], index)
        result.update(source_partition=analysis, clipping_fit_proof=ledger,
            physical_surface_continuous=True, source_coverage_accounted=True,
            protected_excluded_sample_count=0, excluded_length_cm=0.0,
            analytic_exterior_triangle_coverage_verified=True, outside_uncovered_length_cm=0.0,
            physical_sample_count=sum(v['sample_count'] for v in result['source_roads']))
        return result
    clearance = float(plan['settings']['surface_clearance_cm'])
    analysis_by_id = {v['piece_id']: v for v in analysis['source_roads']}
    rings = [(str(p['source_osm_id']), [[v[0]*100.0, v[1]*100.0] for v in p['ring_xz_m']])
             for p in plan['protected_building_footprints_xz_m']]
    def check_row(row, candidates):
        path = row['road_actor_path']
        assert candidates, 'Source has no actual same-source geometry: ' + path
        record = analysis_by_id[row['piece_id']]
        exclusions = {v['segment_index']: v for v in record['segments']}
        points = [[p[0]*100.0, p[2]*100.0, p[1]*100.0+clearance] for p in row['points_m']]
        samples, omitted, used, derived = [], [], set(), {}
        maximum, ground_difference = 0.0, 0.0
        def physical(point, segment, fraction, kind):
            nonlocal maximum, ground_difference
            hits = [(f.covered(point), s, _source_eligibility(s, path, point)) for s, f in candidates]
            hits = [(v, s, p) for v, s, p in hits if v is not None and p is not None]
            assert hits, 'Exterior/boundary source lacks actual asphalt: %s segment=%r fraction=%r point=%r' % (path, segment, fraction, point)
            value, surface, provenance = max(hits, key=lambda v: (v[0][0], v[1]['component_path']))
            expected = float(landscape_z(point[0], point[1])) + clearance
            assert math.isfinite(expected)
            error = abs(value[0] - expected)
            assert error <= 10.0, 'Exterior native asphalt exceeds unchanged terrain height tolerance'
            if fraction in (0.0, 1.0):
                assert abs(value[0] - point[2]) <= 10.0, 'Exterior exported control height differs'
            maximum = max(maximum, error)
            ground_difference = max(ground_difference, abs(expected-point[2]))
            used.add(surface['geometry_actor_path'])
            for proof in provenance.get('derived_parent_provenance', []):
                derived[(proof['road_actor_path'], proof['parent_road_actor_path'])] = proof
            samples.append([point, segment, fraction, kind, expected, value[0], surface['component_path'], value[1], provenance])
        for number, (point, segment, fraction) in enumerate(_samples(row, clearance, 100.0)):
            if guard and number % 128 == 0:
                guard()
            pads = sorted(pad for pad, ring in rings if _ring_location(point, ring) == 'interior')
            if pads:
                intervals = exclusions.get(segment, {}).get('intervals', [])
                assert all(any(v['pad_source_osm_id'] == pad and v['t0'] <= fraction <= v['t1'] for v in intervals) for pad in pads)
                omitted.append({'point_cm': point, 'segment': segment, 'fraction': fraction, 'protected_pad_ids': pads})
            else:
                physical(point, segment, fraction, 'original_station')
        original_physical = len(samples)
        analytic = []
        for index, (a, b) in enumerate(zip(points, points[1:])):
            if guard and index % 64 == 0:
                guard()
            excluded = exclusions.get(index, {}).get('excluded_union', [])
            actual = _physical_segment_intervals(a, b, path, candidates)
            combined = _interval_union(actual + excluded)
            assert len(combined) == 1 and combined[0][0] <= 1e-13 and combined[0][1] >= 1-1e-13, 'Unaccounted exterior interval: %s segment=%s intervals=%r' % (path, index, combined)
            analytic.append({'segment': index, 'actual_asphalt_intervals': actual, 'excluded_intervals': excluded})
            length = math.dist(a[:2], b[:2])
            probes = set()
            for lo, hi in excluded:
                for t in (lo, hi):
                    probes.add(t)
                    if length:
                        probes.add(max(0.0, t-.02/length))
                        probes.add(min(1.0, t+.02/length))
            for t in sorted(probes):
                point = [a[k]+t*(b[k]-a[k]) for k in range(3)]
                if not any(_ring_location(point, ring) == 'interior' for unused, ring in rings):
                    physical(point, index, t, 'analytic_boundary_or_exterior_0.02cm_probe')
        return {'road_actor_path': path, 'source_osm_id': str(row['source_osm_id']), 'piece_id': row['piece_id'],
            'sample_count': original_physical + len(omitted), 'physical_sample_count': original_physical,
            'protected_excluded_sample_count': len(omitted), 'excluded_samples': omitted,
            'boundary_probe_count': len(samples)-original_physical, 'max_sample_spacing_cm': 100.0,
            'max_surface_height_error_cm': maximum, 'max_landscape_vs_source_interpolation_cm': ground_difference,
            'geometry_actor_paths': sorted(used), 'physical_sample_sha256': _sha(samples),
            'derived_parent_coverage': [derived[k] for k in sorted(derived)],
            'analytic_segment_partition': analytic, 'excluded_length_cm': record['excluded_length_cm'],
            'physical_surface_continuous': not record['segments'], 'source_coverage_accounted': True,
            'outside_uncovered_length_cm': 0.0, 'passed': True}
    proofs = [check_row(row, [(s, f) for s, f in prepared if row['road_actor_path'] in s['source_road_paths']]) for row in rows]
    empty_proofs = []
    for empty in empty_geos:
        support = []
        for path in empty['source_road_paths']:
            row = next(v for v in rows if v['road_actor_path'] == path)
            alternatives = [(s, f) for s, f in prepared if s['geometry_actor_path'] != empty['geometry_actor_path']
                and path in s['source_road_paths'] and len(s.get('native_source_road_paths', s['source_road_paths'])) >= 2]
            verified = check_row(row, alternatives)
            support.append({'road_actor_path': path, 'replacement_geometry_actor_paths': verified['geometry_actor_paths'],
                'source_coverage_accounted': True, 'physical_surface_continuous': verified['physical_surface_continuous'],
                'excluded_length_cm': verified['excluded_length_cm'], 'max_surface_height_error_cm': verified['max_surface_height_error_cm']})
        assert support
        empty_proofs.append({'geometry_actor_path': empty['geometry_actor_path'], 'source_road_paths': empty['source_road_paths'],
            'null_component_paths': empty.get('null_static_mesh_components', []), 'replacement_proof': support,
            'automatic_empty_placeholder': True, 'passed': True})
    return {'schema': SCHEMA, 'basis': 'actual same-source upward asphalt outside exact protected source interiors; interiors explicitly excluded by retained r018 policy',
        'source_sha256': plan['source_sha256'], 'centreline_sha256': plan['centreline_sha256'],
        'source_road_count': len(rows), 'source_piece_count': plan['source_piece_count'], 'source_roads': proofs,
        'automatic_empty_geometry': empty_proofs, 'xy_float32_boundary_tolerance_cm': .01,
        'max_surface_height_error_cm': max(v['max_surface_height_error_cm'] for v in proofs),
        'physical_sample_count': sum(v['physical_sample_count'] for v in proofs),
        'protected_excluded_sample_count': sum(v['protected_excluded_sample_count'] for v in proofs),
        'source_partition': analysis, 'clipping_fit_proof': ledger,
        'physical_surface_continuous': False, 'source_coverage_accounted': True,
        'excluded_length_cm': analysis['excluded_length_cm'], 'outside_uncovered_length_cm': 0.0,
        'unresolved_source_conflicts': analysis['source_conflicts'], 'passed': True}


def _validated_derived_provenance(run, rows, bounded):
    """Read-only native verification; never trust an unvalidated JSON expansion."""
    import geocity_roadbld_workflow as base
    actors = list(getattr(run, 'derived_junction_roads', []))
    if not actors:
        return {}
    paths = {base._path(actor) for actor in actors}
    assert len(paths) == len(actors)
    report = getattr(run, 'junction_repair', None)
    state = getattr(run, 'state', {})
    report = report or state.get('junction_repair') or state.get('junction_repair_report')
    assert report and isinstance(report, dict), 'Derived grounding coverage needs the complete native junction proof'
    # The installed validators write only measured fields in this private JSON
    # copy; actor/control/preset/property access remains read-only.
    report = json.loads(json.dumps(report, allow_nan=False))
    assert report['schema'] == 'environmentpipeline.roadbld_junction_repair.v1'
    assert report['global_cdo_limit_restored'] is True
    records = report['derived_junction_roads']
    assert len(records) == len(paths) and {record['road_actor_path'] for record in records} == paths
    assert len({record['derived_id'] for record in records}) == len(records)
    source_rows = {row['road_actor_path']: row for row in rows}
    source_actors = {base._path(actor): actor for actor in run.roads}
    assert set(report['sourcecontrols_trimproof']) == set(source_rows)
    import geocity_roadbld_junctions as junctions
    for path, row in source_rows.items():
        bounded()
        junctions.verify_source_road(run, source_actors[path], row, report)
    junctions.verify_derived_roads(run, report)
    result = {}
    for record in sorted(records, key=lambda row: row['derived_id']):
        parents = record['parent_road_actor_paths']
        assert len(parents) == len(set(parents)) == 2 and set(parents).issubset(source_rows)
        assert len(record['native_endpoint_trims']) == len(record['parent_source_osm_ids']) == len(record['parent_piece_ids']) == 2
        assert _sha(record['control_points_world_cm']) == record['control_points_sha256']
        assert len(record['endpoint_link_proof']) == 2 and all(link['reciprocal'] for link in record['endpoint_link_proof'])
        provenance = []
        for index, (path, trim) in enumerate(zip(parents, record['native_endpoint_trims'])):
            row = source_rows[path]
            assert str(row['source_osm_id']) == str(record['parent_source_osm_ids'][index]) and row['piece_id'] == record['parent_piece_ids'][index]
            proof = report['sourcecontrols_trimproof'][path]
            assert trim in proof['end_trims'] and trim['partner_actor_path'] == parents[1 - index]
            assert math.isfinite(float(trim['pullback_cm'])) and 0 < float(trim['pullback_cm']) <= 200.0
            original = [[float(p[0]) * 100.0, float(p[2]) * 100.0,
                         float(p[1]) * 100.0 + run.plan['settings']['surface_clearance_cm']] for p in row['points_m']]
            assert trim['source_endpoint_world_cm'] == original[0 if trim['start'] else -1]
            retained = proof['expected_control_points_world_cm']
            endpoint_segment = retained[:2] if trim['start'] else [retained[-1], retained[-2]]
            assert math.dist(endpoint_segment[0], trim['native_endpoint_world_cm']) <= 0.1
            provenance.append({'road_actor_path': record['road_actor_path'], 'derived_id': record['derived_id'],
                'control_points_sha256': record['control_points_sha256'], 'parent_road_actor_path': path,
                'parent_source_osm_id': str(row['source_osm_id']), 'parent_piece_id': row['piece_id'],
                'parent_full_width_cm': float(row['width_m']) * 100.0,
                'parent_retained_endpoint_segment_world_cm': endpoint_segment,
                'parent_original_controls_sha256': _sha(original), 'native_endpoint_trim': trim,
                'native_controls_widths_policy_links_and_corridor_verified': True})
        result[record['road_actor_path']] = provenance
    return result


def _read_native(run, actors, bounded, source_meshes=None):
    """Read-copy only, using installed UE5.8 public signatures verified by owner."""
    import geocity_roadbld_workflow as base
    import geocity_roadbld_clip as clip
    unreal = base.unreal
    rows = [dict(row, road_actor_path=base._path(road)) for road, row in zip(run.roads, run.plan['roads'])]
    assert len(rows) == len(run.roads) == run.plan['source_piece_count']
    derived_proofs = _validated_derived_provenance(run, rows, bounded)
    owned = {base._path(road) for road in run.roads + list(getattr(run, 'derived_junction_roads', []))}
    surfaces, empty = [], []
    actors = sorted(list(actors if actors is not None else run.native_geos()), key=base._path)
    assert actors and len({base._path(actor) for actor in actors}) == len(actors)
    for actor in actors:
        bounded()
        assert isinstance(actor, unreal.RoadGeo) and base._path(actor).startswith(run.plan['named_map'] + '.')
        sources = sorted(base._path(road) for road in base._get(actor, 'SourceRoads'))
        assert sources and len(sources) == len(set(sources)) and set(sources).issubset(owned)
        parent_provenance = [proof for path in sources for proof in derived_proofs.get(path, [])]
        effective_sources = sorted(set(sources).union(proof['parent_road_actor_path'] for proof in parent_provenance))
        components = sorted(list(actor.get_components_by_class(unreal.MeshComponent)), key=base._path)
        assert components, 'Native RoadGeo has no component provenance'
        actual, missing = [], []
        for component in components:
            bounded()
            assert component.get_class().get_name() == 'StaticMeshComponent', 'Grounding requires exact native StaticMeshComponents'
            mesh = source_meshes[base._path(component)] if source_meshes and base._path(component) in source_meshes else component.static_mesh
            if mesh is None:
                missing.append(base._path(component))
                continue
            # Service pieces may have asphalt only; sidewalks and curbs are
            # present only where that native road preset actually requests them.
            assert component.get_num_materials() >= 1 and all(component.get_material(i) for i in range(component.get_num_materials()))
            assert 'road_worn' in base._path(component.get_material(0)).lower(), 'Material0 is not the verified native asphalt family'
            transform = component.get_world_transform()
            frame = clip._transform(transform)
            q = frame['rotation_xyzw']
            assert abs(q[0]) <= 1e-10 and abs(q[1]) <= 1e-10 and abs(sum(v*v for v in q) - 1) <= 1e-6, 'Pitched/rolled native component needs a separately verified world-Z edit'
            assert all(v > 0 for v in frame['scale3d']), 'Native mirrored/singular component is unsupported'
            copied = clip._copy_static(mesh)
            points, triangles = clip._read_geometry(copied, transform)
            assert triangles, 'Assigned native StaticMesh is empty; not an automatic null placeholder'
            copied, ids, present = unreal.GeometryScript_Materials.get_all_triangle_material_i_ds(copied)
            material_ids = [int(v) for v in unreal.GeometryScript_List.convert_index_list_to_array(ids)]
            assert present and len(material_ids) == len(triangles), 'Native material/triangle ID gaps need explicit support'
            upward = []
            for number, material in enumerate(material_ids):
                if number % 512 == 0:
                    bounded()
                if material != 0:
                    upward.append(False)
                    continue
                normal, valid = unreal.GeometryScript_MeshQueries.get_triangle_face_normal(copied, number)
                assert valid, 'Native triangle IDs are not compact'
                upward.append(float(normal.z) > 0.25)
            AsphaltField(points, triangles, material_ids, upward)
            surface = {'geometry_actor_path': base._path(actor), 'source_road_paths': effective_sources,
                       'native_source_road_paths': sources, 'derived_parent_provenance': parent_provenance,
                       'component_path': base._path(component), 'original_mesh_path': base._path(mesh),
                       'material_slots': clip._materials(component), 'frame': frame,
                       'points_cm': points, 'triangles': triangles, 'material_ids': material_ids,
                       'upward': upward, 'attributes': clip._mesh_attributes(copied),
                       'component': component, 'dynamic_mesh': copied, 'transform': transform}
            surfaces.append(surface)
            actual.append(base._path(component))
        if missing:
            assert not actual, 'Partially missing assigned RoadGeo components are not supported'
            empty.append({'geometry_actor_path': base._path(actor), 'source_road_paths': sources,
                          'null_static_mesh_components': missing})
    return rows, surfaces, empty


def _operation(run, max_seconds):
    assert callable(run.guard) and 0 < max_seconds <= 600
    start = time.monotonic()
    def bounded():
        run.guard()
        assert time.monotonic() - start <= max_seconds, 'Native grounding exceeded bounded time; no asset bindings changed'
    return start, bounded


class SourceGradeSampler:
    """A source-aligned longitudinal grade for one native road cross-section.

    A native lane is a graded cross-section. Sampling terrain separately at
    its left/right vertices bends that cross-section and can lift its centre
    above the measured source. The final gate still reads actual Landscape
    collision along every original source line at <=1m spacing. An optional
    Landscape sampler replaces coarse exported-Z interpolation only for a
    piece whose dense measured grade check requires it; source XY is retained.
    """
    def __init__(self, points_cm, landscape_z=None):
        self.points = points_cm
        assert len(points_cm) >= 2 and all(_finite_point(p) for p in points_cm)
        assert landscape_z is None or callable(landscape_z)
        self.landscape_z = landscape_z
        self.cache = {}
        self.projected_samples = {}

    def __call__(self, x, y):
        key = (round(x, 6), round(y, 6))
        if key not in self.cache:
            choices = []
            for a, b in zip(self.points, self.points[1:]):
                dx, dy = b[0]-a[0], b[1]-a[1]
                length2 = dx*dx+dy*dy
                if length2 <= 1e-12:
                    continue
                t = max(0., min(1., ((x-a[0])*dx+(y-a[1])*dy)/length2))
                distance2 = (x-a[0]-t*dx)**2+(y-a[1]-t*dy)**2
                choices.append((distance2, a[2]+t*(b[2]-a[2]), a[0]+t*dx, a[1]+t*dy))
            assert choices
            unused, source_z, projected_x, projected_y = min(choices, key=lambda v: v[0])
            if self.landscape_z is None:
                self.cache[key] = source_z
            else:
                # Sample only the nearest point ON the original source line.
                # Lateral road/curb vertices retain a common longitudinal grade;
                # sampling each vertex's terrain XY would bend that section.
                actual_z = float(self.landscape_z(projected_x, projected_y))
                assert math.isfinite(actual_z), 'Projected source Landscape height is missing'
                self.cache[key] = actual_z
                self.projected_samples[(round(projected_x, 6), round(projected_y, 6))] = [
                    projected_x, projected_y, source_z, actual_z]
        return self.cache[key]


def _measure_source_grade(row, landscape_z, clearance_cm, tolerance_cm, guard=None):
    """Select terrain projection only after this source's coarse grade fails."""
    assert 0 < tolerance_cm <= 10.0
    samples, failures = [], []
    maximum = 0.0
    for count, (point, segment, fraction) in enumerate(_samples(row, clearance_cm, 50.0)):
        if guard and count % 128 == 0:
            guard()
        actual = float(landscape_z(point[0], point[1])) + clearance_cm
        assert math.isfinite(actual), 'Source-grade Landscape sample is missing'
        error = abs(actual - point[2])
        maximum = max(maximum, error)
        samples.append([point[0], point[1], point[2], actual])
        if error > tolerance_cm:
            failures.append({'point_world_cm': point, 'landscape_plus_clearance_cm': actual,
                'error_cm': error, 'segment_export_index': segment, 'fraction': fraction})
    return {'basis': 'actual_current_Landscape_at_dense_original_source_XY',
            'sample_count': len(samples), 'max_sample_spacing_cm': 50.0,
            'source_piece_id': row['piece_id'], 'source_osm_id': str(row['source_osm_id']),
            'source_points_sha256': _sha(row['points_m']), 'samples_sha256': _sha(samples),
            'max_export_interpolation_error_cm': maximum,
            'unchanged_height_tolerance_cm': tolerance_cm,
            'terrain_projected_grade_required': bool(failures), 'failed_interpolation_samples': failures}


def ground_native_geos(run, landscape_z, actors=None, max_lateral_cm=300.0,
                       max_seconds=180.0, landscape_actor_path=None, source_meshes=None):
    """Return (JSON report, transient prepared outputs); no bindings or saves.

    The supplied sampler must read collision from the exact current official
    HDA Landscape, ignoring every other actor and road. Clip before this call
    when the Landscape cannot cover every original native output vertex.
    Runtime APIs below are verified UE5.8 Python public signatures. Normals
    recomputation preserves existing hard edges; UVs/material IDs are retained.
    """
    import geocity_roadbld_workflow as base
    import geocity_roadbld_clip as clip
    unreal = base.unreal
    assert callable(landscape_z) and landscape_actor_path and landscape_actor_path.startswith(run.plan['named_map'] + '.')
    start, bounded = _operation(run, max_seconds)
    rows, surfaces, empty = _read_native(run, actors, bounded, source_meshes)
    clearance = float(run.plan['settings']['surface_clearance_cm'])
    # Freeze every reference at the native pre-grounding geometry. Never use
    # a previously edited transient neighbor as another component's baseline.
    original_fields = {surface['component_path']: AsphaltField(surface['points_cm'], surface['triangles'],
        surface['material_ids'], surface['upward']) for surface in surfaces}
    row_by_path = {row['road_actor_path']: row for row in rows}
    derived_by_path = {row['road_actor_path']: row for row in (getattr(run, 'junction_repair', None) or {}).get('derived_junction_roads', [])}
    outputs, component_proofs, source_grade_checks = [], [], {}
    for surface in surfaces:
        bounded()
        copied = surface['dynamic_mesh']
        original_triangle_count = len(surface['triangles'])
        original_geometry_sha = _sha({'vertices_cm': surface['points_cm'], 'triangles': surface['triangles']})
        # One exact linear refinement halves native 2m longitudinal segments;
        # it preserves the native shape/UV/materials before height correction.
        copied = unreal.GeometryScript_MeshSubdivide.apply_uniform_tessellation(copied, 1)
        points, triangles = clip._read_geometry(copied, surface['transform'])
        copied, ids, present = unreal.GeometryScript_Materials.get_all_triangle_material_i_ds(copied)
        material_ids = [int(v) for v in unreal.GeometryScript_List.convert_index_list_to_array(ids)]
        assert present and len(material_ids) == len(triangles)
        upward = [unreal.GeometryScript_MeshQueries.get_triangle_face_normal(copied, number)[0].z > .25 if material == 0 else False
                  for number, material in enumerate(material_ids)]
        surface.update(dynamic_mesh=copied, points_cm=points, triangles=triangles, material_ids=material_ids,
                       upward=upward, attributes=clip._mesh_attributes(copied))
        sampler, strategy = landscape_z, 'actual_Landscape_junction_heightfield'
        grade_check = None
        if len(surface['native_source_road_paths']) == 1:
            path = surface['native_source_road_paths'][0]
            if path in row_by_path:
                grade = [[p[0]*100., p[2]*100., p[1]*100.] for p in row_by_path[path]['points_m']]
                if path not in source_grade_checks:
                    source_grade_checks[path] = _measure_source_grade(row_by_path[path], landscape_z,
                        clearance, run.plan['settings']['ground_profile_tolerance_cm'], bounded)
                grade_check = source_grade_checks[path]
            else:
                assert path in derived_by_path
                grade = [[p[0], p[1], p[2]-clearance] for p in derived_by_path[path]['control_points_world_cm']]
            sampler, strategy = SourceGradeSampler(grade), 'verified_source_longitudinal_native_lane_grade'
            if grade_check and grade_check['terrain_projected_grade_required']:
                sampler = SourceGradeSampler(grade, landscape_z)
                strategy = 'actual_Landscape_projected_source_longitudinal_grade'
        grounded, proof = ground_geometry(surface['points_cm'], surface['triangles'], surface['material_ids'],
            sampler, clearance, max_lateral_cm, surface['upward'], bounded,
            SameSourceAsphaltReference(surface, surfaces, original_fields, bounded))
        proof.update(height_strategy=strategy, original_native_geometry_sha256=original_geometry_sha,
                     original_native_triangle_count=original_triangle_count,
                     linear_tessellation_level=1, source_grade_checked_against_actual_Landscape_in_final_gate=True)
        if grade_check is not None:
            proof['source_grade_measurement'] = grade_check
            if sampler.projected_samples:
                samples = [sampler.projected_samples[key] for key in sorted(sampler.projected_samples)]
                proof['projected_source_grade_samples'] = {'count': len(samples), 'sha256': _sha(samples),
                    'max_actual_vs_export_interpolation_cm': max(abs(v[2]-v[3]) for v in samples),
                    'cross_section_grade_preserved': True, 'original_source_XY_unchanged': True}
        copied = surface['dynamic_mesh']
        copied, positions, gaps = unreal.GeometryScript_MeshQueries.get_all_vertex_positions(copied, False)
        positions = list(unreal.GeometryScript_List.convert_vector_list_to_array(positions))
        assert not gaps and len(positions) == len(grounded), 'Native vertex gaps require explicit support'
        # Native components may have yaw/positive scale. Changing only local Z
        # then preserves world XY exactly, including a clipped boundary vertex.
        scale_z = surface['frame']['scale3d'][2]
        changed = [unreal.Vector(float(v.x), float(v.y), float(v.z) + (p[2] - before[2]) / scale_z)
                   for v, p, before in zip(positions, grounded, surface['points_cm'])]
        position_list = unreal.GeometryScript_List.convert_array_to_vector_list(changed)
        copied = unreal.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(copied, position_list)
        copied = unreal.GeometryScript_Normals.recompute_normals(copied, unreal.GeometryScriptCalculateNormalsOptions(), False)
        actual, triangles = clip._read_geometry(copied, surface['transform'])
        assert triangles == surface['triangles'] and len(actual) == len(surface['points_cm'])
        assert all(a[:2] == b[:2] and abs(a[2] - b[2]) <= 0.001 for a, b in zip(actual, grounded)), 'Native position edit changed XY or missed requested world Z'
        copied, ids, present = unreal.GeometryScript_Materials.get_all_triangle_material_i_ds(copied)
        assert present and [int(v) for v in unreal.GeometryScript_List.convert_index_list_to_array(ids)] == surface['material_ids']
        assert clip._mesh_attributes(copied) == surface['attributes'], 'Native UV/material/normal attributes changed unexpectedly'
        surface['points_cm'], surface['dynamic_mesh'] = actual, copied
        # Eligibility must describe the corrected faces, not their old heights.
        flags = []
        for n, material in enumerate(surface['material_ids']):
            normal, valid = unreal.GeometryScript_MeshQueries.get_triangle_face_normal(copied, n)
            assert valid, 'Corrected native triangle has no valid face normal'
            flags.append(material == 0 and normal.z > .25)
        surface['upward'] = flags
        component_proofs.append(dict(proof, component_path=surface['component_path'], geometry_actor_path=surface['geometry_actor_path'],
            original_mesh_path=surface['original_mesh_path'], source_road_paths=surface['source_road_paths'],
            native_source_road_paths=surface['native_source_road_paths'], derived_parent_provenance=surface['derived_parent_provenance'],
            material_slots=surface['material_slots'], frame=surface['frame'], uv_sets=surface['attributes']['uv_sets'],
            normals_recomputed_preserving_hard_edges=True, assets_bound=False))
        outputs.append({'component': surface['component'], 'dynamic_mesh': copied, 'transform': surface['transform'],
                        'component_path': surface['component_path'], 'original_mesh_path': surface['original_mesh_path'],
                        'material_slots': surface['material_slots'], 'proof': component_proofs[-1]})
    run._grounding_transient_diagnostic = {'rows': rows, 'surfaces': surfaces, 'empty': empty,
        'outputs': outputs, 'component_proofs': component_proofs}
    import geocity_roadbld_seams as seams
    continuous = seams.repair_continuous(run, rows, surfaces, landscape_z, bounded)
    seam_report = seams.repair_source_seams(run, surfaces, landscape_z, empty_geos=empty)
    coverage = verify_source_coverage(run.plan, rows, surfaces, landscape_z, empty, guard=bounded)
    context = {'plan': run.plan, 'rows': rows, 'landscape_z': landscape_z, 'empty_geos': empty}
    # Boolean corrections can replace transient objects. Rebuild every output
    # reference from the final surface; never bind an earlier cached copy.
    outputs = [{'component': surface['component'], 'dynamic_mesh': surface['dynamic_mesh'],
                'transform': surface['transform'], 'component_path': surface['component_path'],
                'original_mesh_path': surface['original_mesh_path'], 'material_slots': surface['material_slots'],
                'proof': component_proofs[number], 'coverage_surface': surface,
                'source_coverage_context': context}
               for number, surface in enumerate(surfaces)]
    for surface, proof in zip(surfaces, component_proofs):
        proof['after_continuous_repair_geometry_sha256'] = _sha({'vertices_cm': surface['points_cm'], 'triangles': surface['triangles']})
        proof['actual_corrected_upward_face_count'] = sum(surface['upward'])
    run._grounding_transient_diagnostic = {'rows': rows, 'surfaces': surfaces, 'empty': empty,
        'outputs': outputs, 'component_proofs': component_proofs}
    bounded()
    return {'schema': SCHEMA, 'phase': 'transient_grounded_physically_verified', 'landscape_actor_path': landscape_actor_path,
            'source_sha256': run.plan['source_sha256'], 'centreline_sha256': run.plan['centreline_sha256'],
            'components': component_proofs, 'source_coverage': coverage,
            'native_seam_repair': seam_report,
            'continuous_source_conditioning': continuous,
            'automatic_empty_geometry': coverage['automatic_empty_geometry'],
            'native_component_count': len(outputs), 'assets_bound': False, 'saved': False,
            'elapsed_seconds': time.monotonic() - start, 'passed': True}, outputs


class _PendingCorrection:
    """Owner-held native handles; deliberately never placed in JSON state."""
    def __init__(self, run, snapshots, result_path):
        import copy
        assert getattr(run, '_pending_correction', None) is None
        self.run, self.snapshots, self.result_path = run, snapshots, result_path
        self.references = {name:getattr(run,name,None) for name in
            ('grounding_report','clipping_report','junction_repair','state',
             'landscape_sampler','_grounding_transient_diagnostic','geo_actors')}
        self.values = {name:copy.deepcopy(self.references[name]) for name in
                       ('grounding_report','clipping_report','junction_repair','state')}
        self.geo_actors = list(self.references['geo_actors'] or [])
        self.state_bytes = run.state_path.read_bytes()
        self.wrote_candidates = False
        self.links_verified = False
        self.validation_passes = 0
        self.staged_verified = False
        self.status = 'pending'
        self.result = None
        run._pending_correction = self
        run._correction_outcome = 'pending'

    def resolution(self, status, error=None, errors=()):
        import datetime
        path = self.result_path.with_name(self.result_path.stem+'_'+status+'_'+
            datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S%f')+'.json')
        value = {'schema':'environmentpipeline.roadbld_correction_resolution.v1',
                 'status':status,'correction_receipt':str(self.result_path),
                 'revision':self.run.revision,'transaction_token':self.run.transaction_token,
                 'links_verified':self.links_verified,'ordinary_validation_passes':self.validation_passes,
                 'staged_contract_verified':self.staged_verified,'error':repr(error) if error else None,
                 'rollback_errors':list(errors),'saved':False}
        with path.open('x',encoding='utf-8') as stream:
            json.dump(value,stream,indent=2,allow_nan=False)
        return str(path)

    def rollback(self, error):
        import geocity_roadbld_clip as clip
        errors = []
        if self.wrote_candidates:
            for index,snapshot in reversed(list(enumerate(self.snapshots))):
                try:
                    clip._restore_candidate_asset(snapshot)
                except Exception as exc:
                    errors.append({'candidate_index':index,'error':repr(exc)})
        for name,value in self.values.items():
            original = self.references[name]
            if isinstance(original,dict):
                original.clear(); original.update(value)
            setattr(self.run,name,original)
            assert getattr(self.run,name) is original and getattr(self.run,name) == value
        for name in ('landscape_sampler','_grounding_transient_diagnostic'):
            setattr(self.run,name,self.references[name])
        original_geos = self.references['geo_actors']
        if isinstance(original_geos,list):
            original_geos[:] = self.geo_actors
        self.run.geo_actors = original_geos
        try:
            # run.write adds a fresh UTC and cannot restore exact prior state.
            self.run.state_path.write_bytes(self.state_bytes)
            assert self.run.state_path.read_bytes() == self.state_bytes
        except Exception as exc:
            errors.append({'state_receipt':str(self.run.state_path),'error':repr(exc)})
        self.status = 'rollback_failed' if errors else 'rolled_back'
        try:
            self.resolution(self.status,error,errors)
        except Exception as exc:
            errors.append({'resolution_receipt':str(self.result_path),'error':repr(exc)})
        if errors:
            self.status = 'rollback_failed'
            self.run._correction_outcome = 'rollback_failed'
            # Retain every native handle for explicit owner recovery/retry.
            raise RuntimeError('Correction rollback incomplete; pending snapshots retained: '+json.dumps(errors)) from error
        self.run._pending_correction = None
        self.run._correction_outcome = 'rolled_back'
        self.snapshots.clear()


def rollback_correction(run, error):
    """Restore on any owner/callback/validation failure before suppression."""
    pending = getattr(run,'_pending_correction',None)
    if pending is not None:
        pending.rollback(error)


def commit_correction(run):
    """Parent calls after all ownership checks, immediately before Cook resume."""
    pending = getattr(run,'_pending_correction',None)
    if pending is None:
        return None  # Ordinary generation has no same-path correction.
    try:
        run.guard()
        assert pending.status == 'pending' and pending.result is not None
        assert pending.links_verified and pending.validation_passes >= 2 and pending.staged_verified
        assert run.state['phase'] == 'native_generated_verified' and run.tick_handle is None
        path = pending.resolution('committed_before_suppression')
    except Exception as exc:
        rollback_correction(run,exc)
        raise
    pending.status = 'committed'
    run._pending_correction = None
    run._correction_outcome = 'committed'
    pending.snapshots.clear()
    return path


def correction(run):
    """Owner-only correction of the same unsaved candidates; no rebuild/save.

    Fresh copies of preserved native inputs are conditioned. Existing owned
    candidate assets are updated in place only after complete transient proof.
    Actual converted proof follows those writes; any failure restores all old
    candidate geometry. Old evidence files are never rewritten.
    """
    import copy
    import datetime
    from pathlib import Path
    import geocity_roadbld_workflow as base
    import geocity_roadbld_clip as clip
    import geocity_roadbld_junctions as junctions
    from geocity_roadbld_landscape import LandscapeSampler
    run.guard()
    assert run.tick_handle is None and not getattr(run, '_tick_running', False)
    assert getattr(run, '_pending_correction', None) is None
    assert run.state['phase'] == 'failed_validating' and run.state['native_rebuild_completed']
    assert run.grounding_report and run.clipping_report and not run.state.get('saved')
    previous = {'grounding_report':copy.deepcopy(run.grounding_report),
                'clipping_report':copy.deepcopy(run.clipping_report)}
    old_clip_path = Path(previous['clipping_report']['receipt'])
    assert _sha(json.loads(old_clip_path.read_text(encoding='utf-8'))) == _sha(previous['clipping_report'])
    participant = junctions._owned_state(run)
    start,bounded = _operation(run,600.)
    rows,current,empty = _read_native(run,None,bounded)
    _verify_partition_ledger(run.plan,rows,current,previous['clipping_report'],previous['grounding_report'])
    bindings = {b['component']:b for b in previous['clipping_report']['bindings']}
    assert set(bindings) == {s['component_path'] for s in current}
    snapshots, originals, original_hashes = [], {}, {}
    for surface in current:
        bounded()
        component = surface['component']; mesh = component.static_mesh
        binding = bindings[surface['component_path']]
        assert base._path(mesh) == binding['clipped_mesh']
        assert base._path(mesh).startswith(run.plan['asset_root']+'/ClippedGeometry/')
        snapshots.append({'component':component,'source':mesh,'transform':surface['transform'],
            'materials':surface['material_slots'],'collision':clip._collision(component,mesh),
            'rollback_mesh':surface['dynamic_mesh'],
            'rollback_slots':list(mesh.get_editor_property('static_materials')),
            'rollback_metadata':clip._candidate_metadata(mesh)})
        original = base.unreal.load_object(None,binding['source_native_mesh'])
        assert original and original != mesh, 'Original native input is missing or aliases the candidate'
        originals[surface['component_path']] = original
        original_hashes[surface['component_path']] = _sha(clip._read_geometry(clip._copy_static(original),surface['transform']))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder = run.project/'Staging/AppearanceRepair_2026-10-03'
    result_path = folder/('ROADBLD_CONTINUITY_CORRECTION_'+run.area+'_'+stamp+'.json')
    grounding_path = folder/('ROADBLD_GROUNDING_CORRECTION_'+run.area+'_'+stamp+'.json')
    result = {'schema':'environmentpipeline.roadbld_continuity_correction.v1',
        'revision':run.revision,'transaction_token':run.transaction_token,
        'previous_reports_sha256':{k:_sha(v) for k,v in previous.items()},
        'previous_clipping_receipt':str(old_clip_path),
        'previous_participants_sha256':_sha(participant),
        'original_candidate_paths':sorted(b['clipped_mesh'] for b in bindings.values()),
        'preserved_native_input_geometry_sha256':original_hashes,
        'in_place_candidate_mutation':True,'saved':False,'receipt':str(result_path)}
    pending = _PendingCorrection(run,snapshots,result_path)
    run._tick_running = True
    try:
        sampler = LandscapeSampler(run)
        ground,prepared = ground_native_geos(run,sampler,max_seconds=600.,
            landscape_actor_path=sampler.path,source_meshes=originals)
        ground['previous_grounding_report_sha256'] = _sha(previous['grounding_report'])
        ground['preserved_native_input_geometry_sha256'] = original_hashes
        with grounding_path.open('x',encoding='utf-8') as stream:
            json.dump(ground,stream,indent=2,allow_nan=False)
        # clip_native_outputs also has its own exact rollback. This outer
        # snapshot covers any later failure in the final proof/receipt phase.
        pending.wrote_candidates = True
        clipping = clip.clip_native_outputs(run.plan,run.owned_actors(),run.guard,
            generation_id=run.revision+'_continuity_'+stamp[-14:-1],max_seconds=600.,
            prepared_native_meshes={s['component_path']:s for s in prepared},replacement_bindings=bindings)
        assert not clipping['created_asset_paths']
        assert sorted(b['clipped_mesh'] for b in clipping['bindings']) == result['original_candidate_paths']
        unused,verify_bound = _operation(run,600.)
        current_rows,current_surfaces,current_empty = _read_native(run,None,verify_bound)
        final = verify_clipped_source_partition(run.plan,current_rows,current_surfaces,sampler,
            clipping,ground,current_empty,guard=verify_bound)
        assert junctions._owned_state(run) == participant
        for surface in current:
            verify_bound()
            original = originals[surface['component_path']]
            assert _sha(clip._read_geometry(clip._copy_static(original),surface['transform'])) == original_hashes[surface['component_path']]
        assert _sha(json.loads(old_clip_path.read_text(encoding='utf-8'))) == _sha(previous['clipping_report'])
        result.update(status='corrected_same_candidates_physically_verified_pending_owner_lifecycle',
            new_grounding_receipt=str(grounding_path),new_grounding_report_sha256=_sha(ground),
            new_clipping_receipt=clipping['receipt'],new_clipping_report_sha256=_sha(clipping),
            current_candidate_paths=sorted(b['clipped_mesh'] for b in clipping['bindings']),
            physical_validation=final,native_participants_unchanged=True,native_originals_unchanged=True,
            physical_surface_continuous=final['physical_surface_continuous'],source_coverage_accounted=True,
            original_source_coordinates_and_pad_contract_unchanged=True)
        with result_path.open('x',encoding='utf-8') as stream:
            json.dump(result,stream,indent=2,allow_nan=False)
        run.grounding_report,run.clipping_report,run.landscape_sampler = ground,clipping,sampler
        run.state.update(grounding_report=ground,clipping_report=clipping,
            continuity_correction_receipt=str(result_path),native_grounding_validation=final)
        run.write()
        pending.result = result
        return result
    except Exception as exc:
        rollback_correction(run,exc)
        raise
    finally:
        run._tick_running = False


def verify_links(run, previous_reports, correction_result):
    """Return a validation dict; keep snapshots pending through parent gates."""
    try:
        pending = run._pending_correction
        assert pending is not None and pending.status == 'pending'
        assert pending.result == correction_result
        report = _verify_links(run,previous_reports,correction_result)
        pending.links_verified = True
        return report
    except Exception as exc:
        rollback_correction(run,exc)
        raise


def _verify_links(run, previous_reports, correction_result):
    """Read-only linked-receipt and same-candidate verification for the owner."""
    from pathlib import Path
    import geocity_roadbld_junctions as junctions
    run.guard()
    assert correction_result['revision'] == run.revision and correction_result['transaction_token'] == run.transaction_token
    assert {k:_sha(previous_reports[k]) for k in ('grounding_report','clipping_report')} == correction_result['previous_reports_sha256']
    assert _sha(json.loads(Path(correction_result['receipt']).read_text(encoding='utf-8'))) == _sha(correction_result)
    for kind in ('grounding','clipping'):
        report = getattr(run,kind+'_report')
        assert _sha(report) == correction_result['new_'+kind+'_report_sha256']
        path = Path(correction_result['new_'+kind+'_receipt'])
        assert _sha(json.loads(path.read_text(encoding='utf-8'))) == _sha(report)
    assert _sha(json.loads(Path(correction_result['previous_clipping_receipt']).read_text(encoding='utf-8'))) == correction_result['previous_reports_sha256']['clipping_report']
    assert _sha(junctions._owned_state(run)) == correction_result['previous_participants_sha256']
    assert correction_result['current_candidate_paths'] == correction_result['original_candidate_paths']
    return verify_native_delivery(run,run.landscape_sampler,max_seconds=600.,landscape_actor_path=run.landscape_sampler.path)


def verify_native_delivery(run, landscape_z, actors=None, max_seconds=180.0, landscape_actor_path=None):
    """Read-copy actual bound native meshes after grounding, clipping and reopen."""
    assert callable(landscape_z) and landscape_actor_path and landscape_actor_path.startswith(run.plan['named_map'] + '.')
    start, bounded = _operation(run, max_seconds)
    rows, surfaces, empty = _read_native(run, actors, bounded)
    state = getattr(run, 'state', {})
    clipping = getattr(run, 'clipping_report', None) or state.get('clipping_report')
    preclip = getattr(run, 'grounding_report', None) or state.get('grounding_report')
    assert clipping and preclip, 'Final partition requires retained clipping and full preclip physical proofs'
    from pathlib import Path
    immutable = json.loads(Path(clipping['receipt']).read_text(encoding='utf-8-sig'))
    assert _sha(immutable) == _sha(clipping), 'Clipping ledger differs from its immutable recorded receipt'
    proof = verify_clipped_source_partition(run.plan, rows, surfaces, landscape_z,
        clipping, preclip, empty, guard=bounded)
    proof['landscape_actor_path'] = landscape_actor_path
    proof['elapsed_seconds'] = time.monotonic() - start
    proof['component_geometry'] = [{'component_path': surface['component_path'], 'mesh_path': surface['original_mesh_path'],
        'source_road_paths': surface['source_road_paths'], 'native_source_road_paths': surface['native_source_road_paths'],
        'derived_parent_provenance': surface['derived_parent_provenance'], 'material_slots': surface['material_slots'],
        'geometry_sha256': _sha({'vertices_cm': surface['points_cm'], 'triangles': surface['triangles']}),
        'material_ids_sha256': _sha(surface['material_ids']), 'attributes': surface['attributes']} for surface in surfaces]
    return proof
