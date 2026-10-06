"""Read-only, source-proven classification of native multiway road junctions.

The SDK's corner scan tests every nearby endpoint pair.  This module accepts a
pair only when a current native junction and an unchanged third source road
prove a multiway intersection.  Final acceptance also requires live road-top
triangles at both original endpoints.  Importing this module does nothing.
"""
import hashlib
import json
import math


SCHEMA = 'environmentpipeline.roadbld_native_topology.v1'


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode('utf-8')).hexdigest()


def _xyz(value):
    return [float(value.x), float(value.y), float(value.z)]


def _original(row, plan):
    clearance = float(plan['settings']['surface_clearance_cm'])
    return [[float(p[0]) * 100.0, float(p[2]) * 100.0,
             float(p[1]) * 100.0 + clearance] for p in row['points_m']]


def _endpoint(row, points, start):
    index = 0 if start else len(points) - 1
    originals = list(row['original_point_indices'])
    assert index in originals and index not in row['boundary_point_indices'], 'Endpoint is not an original in-area source vertex'
    source_index = row['original_source_vertex_indices'][originals.index(index)]
    return {'start': bool(start), 'export_point_index': index,
            'original_source_vertex_index': int(source_index),
            'original_endpoint_world_cm': list(points[index])}


def _nearest(point, row, points):
    anchors = sorted(set(row['original_point_indices'] + row['boundary_point_indices']))
    assert len(anchors) >= 2
    best = None
    for first, second in zip(anchors, anchors[1:]):
        a, b = points[first], points[second]
        dx, dy = b[0] - a[0], b[1] - a[1]
        norm = dx * dx + dy * dy
        if norm <= 1e-12:
            continue
        t = max(0.0, min(1.0, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / norm))
        closest = [a[0] + t * dx, a[1] + t * dy]
        distance = math.hypot(point[0] - closest[0], point[1] - closest[1])
        record = {'distance_cm': distance, 'closest_xy_cm': closest,
                  'segment_export_point_indices': [first, second],
                  'segment_original_xy_cm': [[a[0], a[1]], [b[0], b[1]]],
                  'segment_fraction': t, 'segment_interior': 0.0 < t < 1.0}
        if best is None or distance < best['distance_cm']:
            best = record
    assert best is not None, 'Source centerline is degenerate'
    return best


def _surface_z(point, a, b, c):
    """Exact XY triangle coverage and barycentric world Z; vertical faces fail."""
    ux, uy = b[0] - a[0], b[1] - a[1]
    vx, vy = c[0] - a[0], c[1] - a[1]
    determinant = ux * vy - uy * vx
    if abs(determinant) <= 1e-8:
        return None
    px, py = point[0] - a[0], point[1] - a[1]
    s = (px * vy - py * vx) / determinant
    t = (ux * py - uy * px) / determinant
    if s < -1e-9 or t < -1e-9 or s + t > 1.0 + 1e-9:
        return None
    return a[2] + s * (b[2] - a[2]) + t * (c[2] - a[2])


def _geometry(run, geo, endpoints, base):
    import geocity_roadbld_clip as clip
    meshes = []
    for component in geo.get_components_by_class(base.unreal.MeshComponent):
        run.guard()
        assert component.get_class().get_name() == 'StaticMeshComponent', 'Unsupported junction component type'
        source = component.static_mesh
        assert source is not None
        copied = clip._copy_static(source)
        points, indices = clip._read_geometry(copied, component.get_world_transform())
        assert indices and all(all(math.isfinite(v) for v in p) for p in points)
        meshes.append({'component_path': base._path(component), 'mesh_path': base._path(source),
                       'world_geometry_sha256': clip._sha({'vertices_cm': points, 'triangles': indices}),
                       'triangle_count': len(indices), 'material_slots': clip._materials(component),
                       'points': points, 'indices': indices, 'dynamic_mesh': copied})
    assert meshes, 'Native junction has no actual mesh component'
    coverage = []
    for endpoint in endpoints:
        point = endpoint['original_endpoint_world_cm']
        surfaces = []
        for mesh in meshes:
            for index, triangle in enumerate(mesh['indices']):
                if index % 512 == 0:
                    run.guard()
                vertices = [mesh['points'][i] for i in triangle]
                # Renderer and the native complex collision reject backfaces.
                # A downward extrusion face is not a visible road top, even
                # when its interpolated plane lies above an upward surface.
                normal, valid = base.unreal.GeometryScript_MeshQueries.get_triangle_face_normal(mesh['dynamic_mesh'], index)
                assert valid
                if normal.z <= .25:
                    continue
                z = _surface_z(point, *vertices)
                if z is not None:
                    surfaces.append((z, mesh['component_path'], mesh['mesh_path'], index, vertices))
        assert surfaces, 'Original junction endpoint is not covered by retained native triangles'
        # RoadGeo contains road surfaces only; choose the uppermost covering
        # face so the road underside cannot stand in for the visible road top.
        z, component, mesh, triangle, vertices = max(surfaces, key=lambda item: item[0])
        error = abs(z - point[2])
        assert error <= 10.0, 'Native road top differs from original final-ground endpoint by more than10cm'
        coverage.append({'road_actor_path': endpoint['road_actor_path'], 'start': endpoint['start'],
                         'point_world_cm': point, 'component_path': component, 'mesh_path': mesh,
                         'triangle_index': triangle, 'triangle_world_cm': vertices,
                         'interpolated_road_top_z_cm': z, 'surface_height_error_cm': error,
                         'covered': True})
    return {'required': True, 'passed': True, 'height_tolerance_cm': 10.0,
            'endpoint_coverage': coverage,
            'visible_upward_faces_only': True,
            'component_geometry': [{k: v for k, v in mesh.items() if k not in ('points', 'indices', 'dynamic_mesh')} for mesh in meshes]}


def classify_native_junction_issues(run, issues, require_final_geometry=True):
    """Return unresolved original issue structs and accepted JSON proof rows.

    Requires plan, guard, network, roads; compatible with the saved-map inspector
    proxy.  Never changes actors, controls, assets, callbacks, receipts or maps.
    Preliminary proofs defer triangle validation and cannot establish delivery.
    """
    issues = list(issues)
    if not issues:
        return [], []
    import geocity_roadbld_workflow as base
    run.guard()
    assert len(run.roads) == len(run.plan['roads']) == run.plan['source_piece_count']
    sources = {base._path(road): (road, row) for road, row in zip(run.roads, run.plan['roads'])}
    assert len(sources) == len(run.roads)
    groups = list(base._tool('RoadBLDDiscoveryToolset', 'ListJunctions', run.network))
    junctions = []
    for group in groups:
        if str(base._get(base._get(group, 'Network'), 'RefPath')) != base._path(run.network):
            continue
        if base._get(group, 'bStale') or base._get(group, 'bRebuildInProgress'):
            continue
        junctions.extend(list(base._get(group, 'Junctions')))
    source_cache, geometry_cache = {}, {}

    def source(path):
        if path not in source_cache:
            actor, row = sources[path]
            expected = _original(row, run.plan)
            info = base._tool('RoadBLDDiscoveryToolset', 'DescribeRoad', actor)
            current = [_xyz(base._get(p, 'Location')) for p in base._get(info, 'ControlPoints')]
            assert len(current) == len(expected) and all(math.dist(a, b) <= 0.1 for a, b in zip(current, expected)), 'Multiway source controls changed'
            lanes = list(base._get(info, 'LeftLanes')) + list(base._get(info, 'RightLanes'))
            widths = [sum(float(base._get(lane, field)) for lane in lanes) for field in ('WidthAtStart', 'WidthAtEnd')]
            width = float(row['width_m']) * 100.0
            assert math.isfinite(width) and width > 0 and all(abs(v - width) <= 0.1 for v in widths), 'Native source width differs'
            source_cache[path] = (row, expected, {'road_actor_path': path, 'source_osm_id': str(row['source_osm_id']),
                'piece_id': row['piece_id'], 'full_width_cm': width,
                'original_controls_sha256': _sha(expected), 'current_controls_sha256': _sha(current),
                'native_full_width_start_end_cm': widths, 'control_point_count': len(current),
                'source_coordinates_unchanged': True})
        return source_cache[path]

    unresolved, proofs = [], []
    for issue in issues:
        run.guard()
        try:
            kind = str(base._get(issue, 'Kind'))
            assert kind in ('UnjoinedCorner', 'SharpLinkedCorner')
            pair = sorted([(str(base._get(base._get(issue, field), 'RefPath')), bool(base._get(issue, flag)))
                           for field, flag in (('Road', 'bStart'), ('OtherRoad', 'bOtherStart'))])
            assert pair[0][0] != pair[1][0] and all(path in sources for path, unused in pair)
            endpoints = []
            for path, start in pair:
                row, points, provenance = source(path)
                endpoints.append(dict(_endpoint(row, points, start), road_actor_path=path,
                                      source_osm_id=provenance['source_osm_id'], piece_id=provenance['piece_id']))
            assert math.dist(endpoints[0]['original_endpoint_world_cm'][:2], endpoints[1]['original_endpoint_world_cm'][:2]) <= 100.0
            accepted = None
            for junction in sorted(junctions, key=lambda item: str(base._get(item, 'Id'))):
                participants = sorted(str(base._get(ref, 'RefPath')) for ref in base._get(junction, 'Roads'))
                assert len(participants) == len(set(participants))
                if len(participants) < 3 or not all(path in participants for path, unused in pair) or not set(participants).issubset(sources):
                    continue
                geo_path = str(base._get(junction, 'Id'))
                assert geo_path.startswith(run.plan['named_map'] + '.')
                geo = base.unreal.load_object(None, geo_path)
                assert isinstance(geo, base.unreal.RoadGeo)
                assert sorted(base._path(road) for road in base._get(geo, 'SourceRoads')) == participants
                provenance = [source(path)[2] for path in participants]
                third_support = []
                for path in participants:
                    if path in {p for p, unused in pair}:
                        continue
                    row, points, record = source(path)
                    nearest = [_nearest(endpoint['original_endpoint_world_cm'], row, points) for endpoint in endpoints]
                    if all(value['distance_cm'] <= record['full_width_cm'] * 0.5 for value in nearest):
                        third_support.append({'road_actor_path': path, 'source_osm_id': record['source_osm_id'],
                                              'piece_id': record['piece_id'], 'half_width_cm': record['full_width_cm'] * 0.5,
                                              'endpoint_source_support': nearest})
                if not third_support:
                    continue
                geometry = {'required': False, 'passed': False, 'deferred_until_final_alignment_and_clipping': True}
                if require_final_geometry:
                    cache_key = (geo_path, _sha(endpoints))
                    if cache_key not in geometry_cache:
                        geometry_cache[cache_key] = _geometry(run, geo, endpoints, base)
                    geometry = geometry_cache[cache_key]
                accepted = {'schema': SCHEMA, 'classification': 'source_proven_native_multiway_intersection',
                    'issue_kind': kind, 'issue_pair': endpoints, 'issue_pair_key': _sha(pair),
                    'network_actor_path': base._path(run.network), 'junction_actor_path': geo_path,
                    'junction_source_actor_paths': participants, 'junction_corner_count': int(base._get(junction, 'CornerCount')),
                    'source_participants': provenance, 'third_source_support': third_support,
                    'source_sha256': run.plan['source_sha256'], 'centreline_sha256': run.plan['centreline_sha256'],
                    'network_stale': False, 'network_rebuilding': False,
                    'source_coordinate_changes': 0, 'geometry': geometry,
                    'final_geometry_verified': bool(require_final_geometry)}
                break
            assert accepted is not None, 'No current source-proven native multiway junction covers this issue'
            proofs.append(accepted)
        except Exception:
            # Retain the original typed issue. Callers must repair or reject it;
            # unsupported topology, removed pad-overlap points and API failures
            # never become an ignored warning or a positive proof.
            unresolved.append(issue)
    proofs.sort(key=lambda row: row['issue_pair_key'])
    return unresolved, proofs
