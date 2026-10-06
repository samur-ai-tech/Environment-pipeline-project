"""Retained native RoadBLD road provider for the existing GeoCity area maps.

GeoCity's official HDA exports original geographic XY plus final-ground heights.
This adapter authors the installed native RoadBLD classes in the same map; it
does not import another geography source, evaluate Houdini, sign in, or bake via
an undocumented dialog. Root integrates build() after the official HDA export.
A live validated transaction gates HDA road removal before the named map save;
the saved delivery receipt then governs ordinary retained replacement.
"""
import datetime
import hashlib
import json
import math
import os
import re
import subprocess
import struct
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import unreal
except ImportError:
    unreal = None  # plan/get_export are ordinary read-only source operations.

ACTIVE = []
EXPORT_SCHEMA = 'environmentpipeline.roadbld_centerlines.v1'
DELIVERY_SCHEMA = 'environmentpipeline.roadbld_delivery.v1'
FRAME = 'houdini_local_m_x_yup_z_to_unreal_cm_x_z_y'
OWNER = 'GeoCity_RoadBLD'
VEHICLE_CLASSES = {'secondary', 'secondary_link', 'tertiary', 'residential', 'service', 'unclassified'}
DEFAULTS = {
    'road_preset': '/RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Street_2Lane',
    'sidewalk_preset': '/RoadBLD/RoadBLD/RoadKit_USA/Presets/Sidewalks/RSP_USA_StandardSidewalk',
    'curb_class': '/RoadBLD/RoadBLD/RoadKit_USA/Presets/RoadModules/RM_USA_Curb.RM_USA_Curb_C',
    'road_material': '/RoadBLD/RoadBLD/DefaultRoadKit/Materials/MI_RoadBLD_Asphalt_Road_Worn',
    'sidewalk_material': '/RoadBLD/RoadBLD/RoadKit_USA/Materials/MI_USA_Sidewalk_WS',
    'sidewalk_width_m': {'secondary': 1.5, 'secondary_link': 1.5, 'tertiary': 1.5,
                         'residential': 1.5, 'service': 0.0, 'unclassified': 1.5},
    'surface_clearance_cm': 5.0,
    'curb_height_cm': 15.0,
    'road_thickness_cm': 5.0,
    'max_turn_radius_cm': 100.0,
    'control_point_tolerance_cm': 0.1,
    'centreline_fit_tolerance_cm': 50.0,
    'ground_profile_tolerance_cm': 10.0,
    'rebuild_timeout_seconds': 600.0,
    'roads_per_tick': 4,
    'max_geometry_issues': 200,
    'area_boundary_tolerance_cm': 2.0,
    'building_overlap_tolerance_m2': 0.0001,
    'mesh_validation_timeout_seconds': 45.0,
}


def _read(value):
    return json.loads(Path(value).read_text(encoding='utf-8-sig')) if isinstance(value, (str, Path)) else json.loads(json.dumps(value))


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest()


def _write(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.pending')
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


def _path(obj):
    if obj is None:
        return None
    if hasattr(obj, 'get_path_name'):
        return obj.get_path_name()
    if hasattr(obj, 'to_string'):
        return obj.to_string()
    text = str(obj)
    match = re.search(r"(/Game/[^\s'\">]+)", text)
    return match.group(1) if match else text


def _names(name):
    stripped = name[1:] if len(name) > 1 and name[0] == 'b' and name[1].isupper() else name
    snake = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', stripped)).lower()
    return (name, snake)


def _get(obj, name):
    error = None
    for candidate in _names(name):
        try:
            return obj.get_editor_property(candidate)
        except Exception as exc:
            error = exc
    raise RuntimeError('Missing reflected property ' + name + ' on ' + str(obj)) from error


def _set(obj, name, value):
    error = None
    for candidate in _names(name):
        try:
            obj.set_editor_property(candidate, value)
            return
        except Exception as exc:
            error = exc
    raise RuntimeError('Cannot set supported property ' + name + ' on ' + str(obj)) from error


def _call(obj, name, *args):
    method = getattr(obj, _names(name)[1], None)
    if callable(method):
        return method(*args)
    # Installed AICallable toolsets expose reflected UFunctions, but do not
    # expose generated Python methods because they lack BlueprintCallable.
    return obj.call_method(name, args=tuple(args))


def _tool(class_name, name, *args):
    cls = getattr(unreal, class_name, None)
    if cls is None:
        raise RuntimeError('Required installed toolset is missing: ' + class_name)
    return _call(unreal.get_default_object(cls), name, *args)


def _plain(value, depth=0):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if depth > 4:
        return str(value)
    if isinstance(value, (list, tuple)) or (unreal and isinstance(value, unreal.Array)):
        return [_plain(item, depth + 1) for item in value]
    if unreal and isinstance(value, unreal.Object):
        return _path(value)
    # Issue structs have fixed, installed fields. Do not dump arbitrary UObject
    # properties, credential state or unrelated packages into receipts.
    result = {}
    for field in ('Kind', 'Message', 'Suggestion', 'Location', 'Radius', 'TriangleCount',
                  'MinAngle', 'LongestEdge', 'GeometryActor', 'Road', 'OtherRoad',
                  'RefPath', 'Name', 'Label', 'Class', 'JobId', 'State', 'RemainingNetworks'):
        try:
            result[field] = _plain(_get(value, field), depth + 1)
        except Exception:
            pass
    if result:
        return result
    if all(hasattr(value, component) for component in ('x', 'y', 'z')):
        return [float(value.x), float(value.y), float(value.z)]
    return str(value)


def _area(ring):
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:] + ring[:1]))


def _clean_ring(ring):
    # Same duplicate/collinear conditioning as the retained module's
    # _assembly_clean_ring; this is a read-only validation representation.
    cleaned = []
    for value in ring:
        point = (float(value[0]), float(value[1]))
        if not cleaned or math.dist(point, cleaned[-1]) > 1e-7:
            cleaned.append(point)
    if len(cleaned) > 1 and math.dist(cleaned[0], cleaned[-1]) < 1e-7:
        cleaned.pop()
    changed = True
    while changed and len(cleaned) > 3:
        changed = False
        for i, point in enumerate(cleaned):
            before, after = cleaned[i - 1], cleaned[(i + 1) % len(cleaned)]
            a, b = (point[0] - before[0], point[1] - before[1]), (after[0] - point[0], after[1] - point[1])
            if abs(a[0] * b[1] - a[1] * b[0]) <= 1e-8 and a[0] * b[0] + a[1] * b[1] >= 0:
                del cleaned[i]
                changed = True
                break
    assert len(cleaned) >= 3 and abs(_area(cleaned)) >= 1.0, 'Unsupported geographic building footprint'
    return cleaned if _area(cleaned) > 0 else list(reversed(cleaned))


def _cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _triangulate_ring(ring):
    """Validate/triangulate an existing pad ring for read-only intersection tests."""
    ring = _clean_ring(ring)
    # Reject self-intersections, including nonadjacent touches. An invalid pad
    # representation cannot justify suppressing the existing HDA road provider.
    edges = list(zip(ring, ring[1:] + ring[:1]))
    for i, (a, b) in enumerate(edges):
        for j in range(i + 1, len(edges)):
            if j == i + 1 or (i == 0 and j == len(edges) - 1):
                continue
            c, d = edges[j]
            orientations = (_cross(a, b, c), _cross(a, b, d), _cross(c, d, a), _cross(c, d, b))
            proper = orientations[0] * orientations[1] < 0 and orientations[2] * orientations[3] < 0
            touch = any(abs(v) <= 1e-8 and _segment_distance(p, u, w) <= 1e-7
                        for v, p, u, w in ((orientations[0], c, a, b), (orientations[1], d, a, b),
                                           (orientations[2], a, c, d), (orientations[3], b, c, d)))
            assert not proper and not touch, 'Self-intersecting geographic building pad'
    remaining = list(range(len(ring)))
    triangles = []
    while len(remaining) > 3:
        ear = None
        for k, i in enumerate(remaining):
            before, after = remaining[k - 1], remaining[(k + 1) % len(remaining)]
            triangle = (ring[before], ring[i], ring[after])
            if _cross(*triangle) <= 1e-10:
                continue
            if any(all(_cross(a, b, ring[j]) >= -1e-10 for a, b in zip(triangle, triangle[1:] + triangle[:1]))
                   for j in remaining if j not in (before, i, after)):
                continue
            ear = k
            triangles.append(triangle)
            break
        assert ear is not None, 'Cannot prove simple geographic building pad coverage'
        remaining.pop(ear)
    triangles.append(tuple(ring[i] for i in remaining))
    assert abs(sum(abs(_area(list(t))) for t in triangles) - _area(ring)) <= max(1e-7, _area(ring) * 1e-9), 'Pad triangulation changed its geographic area'
    return triangles


def _triangle_intersection_area(subject, clip):
    """Exact convex clipping in the existing geographic X/Z plane, in m2."""
    polygon = list(subject)
    if _cross(*clip) < 0:
        clip = tuple(reversed(clip))
    for a, b in zip(clip, clip[1:] + clip[:1]):
        source, polygon = polygon, []
        if not source:
            break
        previous = source[-1]
        before = _cross(a, b, previous)
        for current in source:
            after = _cross(a, b, current)
            if (before >= 0) != (after >= 0):
                fraction = before / (before - after)
                polygon.append((previous[0] + fraction * (current[0] - previous[0]),
                                previous[1] + fraction * (current[1] - previous[1])))
            if after >= 0:
                polygon.append(current)
            previous, before = current, after
    return abs(_area(polygon)) if len(polygon) >= 3 else 0.0


def _bounds(points):
    return min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)


def _grid_cells(bounds, size=16.0):
    return ((x, z) for x in range(math.floor(bounds[0] / size), math.floor(bounds[2] / size) + 1)
            for z in range(math.floor(bounds[1] / size), math.floor(bounds[3] / size) + 1))


def _protected_footprints(profile, receipt, export):
    """Derive exact source rings only after proving full actual HDA pad coverage.

    All current pad IDs are covered by actual assembly/whole-placement receipts.
    Source XML identity, shared projection and assembly ring correspondence are
    checked independently; no Houdini graph is evaluated and no pad is authored.
    """
    source = Path(profile['source'])
    data = _read(source)
    entry = next(item for item in data['files'] if item['role'] == 'osm_xml')
    osm_path = source.parent / entry['path']
    assert hashlib.sha256(osm_path.read_bytes()).hexdigest() == entry['sha256'], 'Original OSM source changed'
    osm = ET.parse(osm_path).getroot()
    nodes = {n.attrib['id']: (float(n.attrib['lon']), float(n.attrib['lat'])) for n in osm.findall('node')}
    ways = {w.attrib['id']: [n.attrib['ref'] for n in w.findall('nd')] for w in osm.findall('way')}
    assemblies = receipt.get('native_building_assembly_records', [])
    assembly_ids = [str(a['source_feature']['osm_id']) for a in assemblies]
    whole = [v for v in receipt.get('nonbuilding_instances', []) if v.get('role') == 'whole_building']
    whole_ids = []
    prefix = export['area_id'] + ':building_'
    for row in whole:
        assert row['placement_id'].startswith(prefix), 'Whole building has unknown geographic identity'
        whole_ids.append(row['placement_id'][len(prefix):])
    assert len(assembly_ids + whole_ids) == len(set(assembly_ids + whole_ids)), 'Duplicate native building/pad coverage'
    pad_ids = sorted(set(assembly_ids + whole_ids))
    count = receipt.get('terrain_support', {}).get('source_pad_count')
    assert count == len(pad_ids), 'Cannot prove every actual geographic building pad; native activation remains disabled'
    frame = {**data['local_frame'], **data['origin']}
    f32 = lambda v: struct.unpack('f', struct.pack('f', v))[0]
    def projected(source_id):
        assert source_id in ways, 'A native geographic pad/source way is absent from original XML'
        refs = ways[source_id]
        assert all(ref in nodes for ref in refs), 'Incomplete original OSM node references'
        return [(f32((nodes[n][0] - frame['lon0']) * frame['Mlon_m_per_deg']),
                 f32(-(nodes[n][1] - frame['lat0']) * frame['Mlat_m_per_deg'])) for n in refs]
    rings = {source_id: _clean_ring(projected(source_id)) for source_id in pad_ids}
    assembly_error = 0.0
    for record in assemblies:
        ring = rings[str(record['source_feature']['osm_id'])]
        actual = _clean_ring(record['footprint_xz_m'])
        assert len(actual) == len(ring), 'HDA/source footprint topology differs'
        for a in actual:
            assembly_error = max(assembly_error, min(math.dist(a, b) for b in ring))
        for b in ring:
            assembly_error = max(assembly_error, min(math.dist(a, b) for a in actual))
    assert assembly_error <= 0.001, 'Source projection differs from actual HDA assembly footprints'
    road_error = 0.0
    for row in export['roads']:
        source_ring = projected(str(row['source_osm_id']))
        for pt in row['source_points_xz_m']:
            road_error = max(road_error, min(math.dist(pt, other) for other in source_ring))
    assert road_error <= 0.001, 'Validation projection differs from actual HDA road source'
    records = [{'source_osm_id': source_id, 'ring_xz_m': rings[source_id]} for source_id in pad_ids]
    return records, {'source_pad_count': len(records), 'assembly_count': len(assemblies), 'whole_building_count': len(whole),
                     'max_assembly_vertex_error_m': assembly_error, 'max_road_vertex_error_m': road_error,
                     'footprints_sha256': _sha(records), 'basis': 'unchanged_original_OSM_verified_against_all_native_pad_ids_and_actual_assembly_rings'}


def get_export(profile, export=None):
    """Read and verify the existing HDA export; never cooks or accesses editor."""
    p = _read(profile)
    source = Path(p['source'])
    source_data = _read(source)
    area = source_data['area_id']
    if export is None:
        export = _read(p['catalog_receipt']).get('roadbld_centerlines')
    if not export:
        raise RuntimeError('Official HDA final-terrain centerline export is missing')
    value = _read(export)
    assert value.get('schema') == EXPORT_SCHEMA, 'Unsupported centerline export schema'
    assert value.get('area_id') == area, 'Centerline export belongs to another area'
    assert value.get('coordinate_frame') == FRAME, 'Unverified coordinate transform'
    assert value.get('source_sha256') == hashlib.sha256(source.read_bytes()).hexdigest(), 'Geographic source changed since export'
    roads = value['roads']
    assert roads and value.get('centreline_sha256') == _sha(roads), 'Centerline digest differs'
    ids = [str(row['source_osm_id']) for row in roads]
    assert len(ids) == len(set(ids)), 'Duplicate geographic road source IDs'
    assert ids == sorted(ids), 'Centerlines must be deterministically sorted by source ID'
    if 'source_road_count' in value:
        assert value['source_road_count'] == len(roads), 'Export count differs'
    box = value.get('area_box_xz_m')
    assert box and len(box) == 4 and all(math.isfinite(float(v)) for v in box), 'Authoritative clipping box is missing'
    assert box[0] < box[2] and box[1] < box[3], 'Invalid area clipping box'
    piece_ids = []
    for row in roads:
        assert row.get('route_role') == 'road' and row['highway_class'] in VEHICLE_CLASSES, 'Nonvehicle feature in native road export'
        width = float(row['width_m'])
        assert math.isfinite(width) and 0.5 <= width <= 35.0, 'Invalid source full road width'
        source_points = row.get('source_points_xz_m')
        assert source_points and all(len(pt) == 2 and all(math.isfinite(float(c)) for c in pt) for pt in source_points), 'Complete source XY provenance is missing'
        assert row.get('pieces'), 'A source road has no clipped native piece'
        retained = []
        for piece in row['pieces']:
            piece_id = str(piece['piece_id'])
            assert piece_id.startswith(str(row['source_osm_id']) + ':'), 'Piece identity does not belong to its source'
            piece_ids.append(piece_id)
            points = piece['points_m']
            assert 2 <= len(points) <= 20000, 'Unsupported clipped control-point count'
            assert all(len(point) == 3 and all(math.isfinite(float(c)) for c in point) for point in points), 'Nonfinite geographic point'
            assert all(box[0] - 1e-6 <= pt[0] <= box[2] + 1e-6 and box[1] - 1e-6 <= pt[2] <= box[3] + 1e-6 for pt in points), 'Native piece escapes the active area box'
            for a, b in zip(points, points[1:]):
                assert math.hypot(b[0] - a[0], b[2] - a[2]) > 1e-5, 'Consecutive duplicate clipped XY'
            originals = piece.get('original_point_indices', [])
            boundary = piece.get('boundary_point_indices', [])
            source_indices = piece.get('original_source_vertex_indices', [])
            assert len(source_indices) == len(originals), 'Original source vertex index mapping is missing'
            anchors = sorted(set(originals + boundary))
            assert anchors and anchors[0] == 0 and anchors[-1] == len(points) - 1, 'Clipped endpoints lost their provenance'
            assert originals == sorted(originals), 'Original vertex mapping is not in source order'
            assert source_indices == sorted(set(source_indices)), 'Original source vertex identity is duplicated or unsorted'
            assert boundary == sorted(set(boundary)), 'Boundary vertex mapping is duplicated or unsorted'
            for indices in (originals, boundary):
                assert all(isinstance(i, int) and 0 <= i < len(points) for i in indices), 'Invalid clipped vertex ledger'
            for index, source_index in zip(originals, source_indices):
                pt = (points[index][0], points[index][2])
                assert isinstance(source_index, int) and 0 <= source_index < len(source_points), 'Original source vertex index is invalid'
                assert math.dist(pt, source_points[source_index]) < 1e-6, 'An original vertex moved in XY'
                retained.append(pt)
            for index in boundary:
                pt = points[index]
                assert min(abs(pt[0] - box[0]), abs(pt[0] - box[2]), abs(pt[2] - box[1]), abs(pt[2] - box[3])) < 1e-6, 'A clip vertex is not on the authoritative box'
            for pt in points:
                assert min(_segment_distance((pt[0], pt[2]), a, b) for a, b in zip(source_points, source_points[1:])) < 1e-6, 'Clipped/densified point leaves original geographic polyline'
        for src in source_points:
            if box[0] + 1e-6 < src[0] < box[2] - 1e-6 and box[1] + 1e-6 < src[1] < box[3] - 1e-6:
                assert any(math.dist(src, pt) < 1e-6 for pt in retained), 'An in-area original geographic vertex was omitted'
    assert len(piece_ids) == len(set(piece_ids)), 'Duplicate clipped piece identity'
    if 'source_piece_count' in value:
        assert value['source_piece_count'] == len(piece_ids), 'Clipped piece count differs'
    return value


def plan(profile, export=None, settings=None):
    """Produce a concrete read-only plan usable before WorldBLD sign-in."""
    p, e = _read(profile), get_export(profile, export)
    receipt = _read(p['catalog_receipt'])
    assert receipt.get('roadbld_centerlines', {}).get('centreline_sha256') == e['centreline_sha256'], 'Validation footprint receipt belongs to another completed HDA cook'
    footprints, footprint_proof = _protected_footprints(p, receipt, e)
    for row in footprints:
        _triangulate_ring(row['ring_xz_m'])
    options = dict(DEFAULTS)
    options['sidewalk_width_m'] = dict(DEFAULTS['sidewalk_width_m'])
    if settings:
        supplied = _read(settings)
        supplied = supplied.get('adapter_settings', supplied)
        assert not set(supplied).difference(DEFAULTS), 'Unknown RoadBLD adapter setting'
        for key, val in supplied.items():
            if key == 'sidewalk_width_m':
                options[key].update(val)
            else:
                options[key] = val
    area = e['area_id']
    assert re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', area), 'Invalid area identifier'
    area_root = '/Game/Project/Areas/' + area
    assert p['map'].startswith(area_root + '/') and p['root'].startswith(area_root + '/'), 'Map/root area differs'
    assert 0.0 <= float(options['surface_clearance_cm']) <= 10.0
    assert 0.0 < float(options['max_turn_radius_cm']) <= 1000.0, 'A broad corner radius would change geography'
    assert 0.0 < float(options['centreline_fit_tolerance_cm']) <= 50.0
    assert 0.0 < float(options['rebuild_timeout_seconds']) <= 900.0
    assert 1 <= int(options['roads_per_tick']) <= 20
    assert 0.0 <= float(options['area_boundary_tolerance_cm']) <= 2.0
    assert 0.0 <= float(options['building_overlap_tolerance_m2']) <= 0.0001
    assert 0.0 < float(options['mesh_validation_timeout_seconds']) <= 45.0
    for width in options['sidewalk_width_m'].values():
        assert 0.0 <= float(width) <= 2.0, 'Unreviewed sidewalk width'
    root = area_root + '/RoadBLD'
    specifications = {}
    jobs = []
    for row in e['roads']:
        spec = {'class': row['highway_class'], 'width_m': float(row['width_m']),
                'sidewalk_width_m': float(options['sidewalk_width_m'][row['highway_class']]),
                'policy': options, 'area_id': area}
        digest = _sha(spec)
        key = row['highway_class'] + '_' + digest[:12]
        specifications[key] = spec
        for piece in row['pieces']:
            jobs.append({'source_osm_id': str(row['source_osm_id']), 'highway_class': row['highway_class'],
                         'width_m': row['width_m'], 'preset_key': key, **piece})
    result = {'schema': 'environmentpipeline.roadbld_plan.v1', 'area_id': area, 'named_map': p['map'],
            'asset_root': root, 'source_sha256': e['source_sha256'], 'centreline_sha256': e['centreline_sha256'],
            'source_road_count': len(e['roads']), 'source_piece_count': len(jobs),
            'drivable_source_ids': [str(r['source_osm_id']) for r in e['roads']],
            'drivable_piece_ids': [str(r['piece_id']) for r in jobs], 'area_box_xz_m': e['area_box_xz_m'],
            'mode': 'authored_native_retained', 'bake_performed': False,
            'coordinate_frame': FRAME, 'settings': options, 'presets': specifications, 'roads': jobs,
            'protected_building_footprints_xz_m': footprints, 'protected_footprint_proof': footprint_proof,
            'hda_suppression': 'validated staged contract; root suppresses and bakes HDA before one named final save'}
    # r018 preserves source lines but excludes visible surfaces inside pads.
    # Diagnose that partition before native writes, without rejecting the
    # already-authorized footprint exclusion policy or changing geography.
    import geocity_roadbld_grounding as grounding
    result['visible_source_partition_diagnostic'] = grounding.analyze_protected_source_intervals(result)
    return result


class RoadBLDRun:
    """One asynchronous, area-owned editor operation; root is the only caller."""
    def __init__(self, profile, export=None, settings=None, reviewed_dirty_packages=(),
                 state_path=None, delivery_path=None, on_complete=None):
        assert unreal is not None, 'RoadBLD authoring requires the existing Unreal editor'
        self.profile_path = str(profile) if isinstance(profile, (str, Path)) else None
        self.p, self.plan = _read(profile), plan(profile, export, settings)
        self.area = self.plan['area_id']
        self.project = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
        self.lease_path = self.project / 'Staging/ModelBank/EDITOR_OWNER.txt'
        self.lease_line = self.lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]
        base = Path(self.p['catalog_receipt']).parent
        self.state_path = Path(state_path or base / 'ROADBLD_WORKFLOW_STATE.json')
        self.delivery_path = Path(delivery_path or base / 'ROADBLD_DELIVERY.json')
        for path in (self.state_path, self.delivery_path):
            assert path.resolve().is_relative_to(self.project / 'Staging'), 'Receipt must remain in project Staging'
            assert path.name not in {'WORKFLOW_STATE.json', 'HDA_CATALOG_RECEIPT.json', 'BUILD_STATE.json'}, 'Cannot overwrite official HDA lifecycle receipt'
        self.actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        self.reviewed_dirty = set(reviewed_dirty_packages)
        self.on_complete = on_complete
        self.tick_handle = None
        self.network = None
        self.roads = []
        self.derived_junction_roads = []
        self.junction_repair = None
        self.clipping_report = None
        self.geo_actors = []
        self.presets = {}
        self.owned_assets = {}
        self.cursor = 0
        self.rebuild_pass = 0
        self.idle_since = None
        self.started = time.monotonic()
        self.job_id = None
        self.revision = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        self.transaction_token = str(uuid.uuid4())
        self.previous = _read(self.delivery_path) if self.delivery_path.is_file() else None
        self.state = {'schema': 'environmentpipeline.roadbld_workflow.v1', 'phase': 'preflight',
                      'pid': os.getpid(), 'area_id': self.area, 'named_map': self.p['map'],
                      'mode': self.plan['mode'], 'bake_performed': False, 'saved': False,
                      'source_sha256': self.plan['source_sha256'], 'centreline_sha256': self.plan['centreline_sha256'],
                      'drivable_source_ids': self.plan['drivable_source_ids'],
                      'drivable_piece_ids': self.plan['drivable_piece_ids'],
                      'source_road_count': self.plan['source_road_count'],
                      'source_piece_count': self.plan['source_piece_count'], 'revision': self.revision}
        self.state['protected_footprint_proof'] = self.plan['protected_footprint_proof']
        self.state['visible_source_partition_diagnostic'] = self.plan['visible_source_partition_diagnostic']

    def guard(self):
        lease = self.lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]
        assert lease == self.lease_line and 'OWNER=NONE' not in lease and f'assigned_editor_PID={os.getpid()}' in lease, 'Root editor lease is missing or changed'
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        assert _path(world.get_outermost()) == self.p['map'], 'Wrong retained area map'
        auth = unreal.get_editor_subsystem(unreal.WorldBLDAuthSubsystem)
        assert auth.has_license_for_tool('RoadBLD'), 'RoadBLD license is not currently authorized; sign in using native WorldBLD UI'
        return world

    def write(self):
        self.state['utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        _write(self.state_path, self.state)

    def tags(self, source_id=None):
        values = [OWNER, 'GeoCityArea_' + self.area, 'GeoCityRevision_' + self.revision]
        if source_id is not None:
            values.append('GeoCitySource_' + str(source_id))
        return values

    def tag(self, actor, source_id=None):
        old = [str(v) for v in _get(actor, 'Tags')]
        wanted = sorted(set(old + self.tags(source_id)))
        if set(old) != set(wanted):
            actor.set_editor_property('tags', [unreal.Name(v) for v in wanted],
                                      notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)

    def preflight(self):
        self.guard()
        process = subprocess.run(['powershell.exe', '-NoProfile', '-Command',
                                  'Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],
                                 capture_output=True, text=True, timeout=10,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        assert process.returncode == 0 and sorted(int(x) for x in process.stdout.split()) == [os.getpid()], 'Exactly one Unreal editor is required'
        dirty = {_path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()}
        dirty.update(_path(x) for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
        assert dirty == self.reviewed_dirty, 'Current dirty packages have not been explicitly reviewed: ' + str(sorted(dirty))
        assert not any(r.tick_handle is not None for r in ACTIVE if r is not self), 'Another RoadBLD operation is active'
        self.initial_actor_paths = {_path(a) for a in self.actor_subsystem.get_all_level_actors()}
        if self.previous:
            assert self.previous.get('schema') == DELIVERY_SCHEMA and self.previous.get('area_id') == self.area
            assert self.previous.get('named_map') == self.p['map'] and self.previous.get('saved') is True
            assert self.previous.get('phase') == 'native_generated_saved_verified'
            self.verify_previous_ownership()
        already_owned = {_path(a) for a in self.actor_subsystem.get_all_level_actors()
                         if {OWNER, 'GeoCityArea_' + self.area}.issubset({str(v) for v in _get(a, 'Tags')})}
        expected_owned = set(self.previous['owned_actor_paths']) if self.previous else set()
        assert already_owned == expected_owned, 'Unrecorded native staged output exists; root must reconcile exact paths before retry'
        # Exercise read-only reflected discovery before creating actors/assets.
        _tool('RoadBLDDiscoveryToolset', 'DescribeNetwork', None, 1)
        required = ('DynamicRoadNetwork', 'RoadSplineAuthoringPoint', 'DynamicRoadLaneProfile',
                    'DynamicRoadDrawPresetMarking', 'RoadBLDDiscoveryToolset', 'RoadBLDBuildToolset',
                    'RoadGeo', 'WorldBLDKitElementComponent', 'LaneType', 'DynamicMesh',
                    'GeometryScriptCopyMeshFromComponentOptions', 'GeometryScript_SceneUtils',
                    'GeometryScript_MeshQueries', 'GeometryScript_List')
        assert all(hasattr(unreal, name) for name in required), 'Required installed RoadBLD reflected types are unavailable'
        for cls, function in (('GeometryScript_SceneUtils', 'copy_mesh_from_component'),
                              ('GeometryScript_MeshQueries', 'get_all_triangle_indices'),
                              ('GeometryScript_MeshQueries', 'get_all_vertex_positions'),
                              ('GeometryScript_List', 'convert_triangle_list_to_array'),
                              ('GeometryScript_List', 'convert_vector_list_to_array')):
            assert callable(getattr(getattr(unreal, cls), function, None)), 'Required native mesh read-copy API is unavailable: ' + function
        for key in ('road_preset', 'sidewalk_preset', 'road_material', 'sidewalk_material'):
            assert unreal.load_asset(self.plan['settings'][key]), 'Native dependency is missing: ' + key
        assert unreal.load_class(None, self.plan['settings']['curb_class']), 'Native curb class is missing'
        self.state['reviewed_dirty_packages'] = sorted(dirty)
        self.state['license_verified'] = True
        self.write()

    def verify_previous_ownership(self):
        actors = {_path(a): a for a in self.actor_subsystem.get_all_level_actors()}
        owned = self.previous['owned_actor_paths']
        assert set(owned).issubset(actors), 'Previous native output is missing; reconcile before replacement'
        for path in owned:
            tags = {str(v) for v in _get(actors[path], 'Tags')}
            assert path.startswith(self.p['map'] + '.') and {OWNER, 'GeoCityArea_' + self.area}.issubset(tags), 'Previous actor ownership differs: ' + path

    def duplicate_blueprint(self, source, destination, spec):
        self.guard()
        assert destination.startswith(self.plan['asset_root'] + '/')
        lib = unreal.EditorAssetLibrary
        digest = _sha(spec)
        asset = unreal.load_asset(destination)
        if asset:
            assert str(lib.get_metadata_tag(asset, 'GeoCityRoadBLDSpecSHA256')) == digest, 'Existing named preset does not match immutable specification: ' + destination
        else:
            asset = lib.duplicate_asset(source, destination)
            assert asset, 'Native preset copy failed: ' + destination
            lib.set_metadata_tag(asset, 'GeoCityRoadBLDSpecSHA256', digest)
            lib.set_metadata_tag(asset, 'GeoCityOwner', OWNER)
            lib.set_metadata_tag(asset, 'GeoCityArea', self.area)
        self.owned_assets[_path(asset.get_outermost())] = asset.get_outermost()
        cls = lib.load_blueprint_class(destination)
        assert cls, 'Copied native preset Blueprint has no generated class'
        return asset, cls, unreal.get_default_object(cls)

    def build_presets(self):
        options = self.plan['settings']
        road_material = unreal.load_asset(options['road_material'])
        sidewalk_material = unreal.load_asset(options['sidewalk_material'])
        curb = unreal.load_class(None, options['curb_class'])
        for key, spec in sorted(self.plan['presets'].items()):
            self.guard()
            sidewalk_class = None
            if spec['sidewalk_width_m'] > 0:
                bp, sidewalk_class, cdo = self.duplicate_blueprint(options['sidewalk_preset'],
                    self.plan['asset_root'] + '/Sidewalks/RSP_' + key, spec)
                for name, value in {'Width': spec['sidewalk_width_m'] * 100.0, 'ZOffset': options['curb_height_cm'],
                                    'Material': sidewalk_material, 'CornerMaterial': sidewalk_material,
                                    'CurbClass': curb, 'SidewalkPartitions': [], 'CurbCutMaterial': sidewalk_material,
                                    'CurbCutLowerAmount': options['curb_height_cm']}.items():
                    _set(cdo, name, value)
                unreal.BlueprintEditorLibrary.compile_blueprint(bp)
                sidewalk_class = unreal.EditorAssetLibrary.load_blueprint_class(_path(bp))
            bp, cls, cdo = self.duplicate_blueprint(options['road_preset'], self.plan['asset_root'] + '/Presets/RP_' + key, spec)
            empty_marking = unreal.DynamicRoadDrawPresetMarking()
            _set(empty_marking, 'MarkingWidth', 0.0)
            _set(empty_marking, 'MarkingMaterial', None)
            lane = unreal.DynamicRoadLaneProfile()
            _set(lane, 'Width', spec['width_m'] * 50.0)
            _set(lane, 'Type', unreal.LaneType.NORMAL)
            _set(lane, 'OuterLaneMarking', empty_marking)
            _set(lane, 'LaneOverlayMaterial', None)
            for name, value in {'PresetName': unreal.Name('GeoCity_' + self.area + '_' + key),
                                'Region': unreal.Name('Unspecified'), 'Description': 'Geographic width, native unmarked surface, scoped GeoCity provider',
                                'LeftLanes': [lane], 'RightLanes': [lane], 'CenterlineMarking': empty_marking,
                                'RoadMaterial': road_material, 'IntersectionMaterial': road_material,
                                'RoadModules': [], 'PropSpawners': [], 'RoadPCGGraph': None,
                                'bEnableLandscapePaint': False, 'LandscapePaintLayerName': unreal.Name('None'),
                                'bEnableRoadEdgeDetail': False, 'bGenerateAbutments': False,
                                'LeftSidewalkPresetClass': sidewalk_class, 'RightSidewalkPresetClass': sidewalk_class,
                                'RoadCrownHeight': 0.0, 'ActorTags': [unreal.Name(t) for t in (OWNER, 'GeoCityArea_' + self.area)]}.items():
                _set(cdo, name, value)
            automation = _get(cdo, 'DefaultAutomations')
            crossing = _get(automation, 'AutomaticCrossings')
            _set(crossing, 'bEnabled', False)
            _set(crossing, 'CrossingStyleClass', None)
            _set(automation, 'AutomaticCrossings', crossing)
            _set(cdo, 'DefaultAutomations', automation)
            unreal.BlueprintEditorLibrary.compile_blueprint(bp)
            cls = unreal.EditorAssetLibrary.load_blueprint_class(_path(bp))
            cdo = unreal.get_default_object(cls)
            self.validate_preset(cdo, spec)
            self.presets[key] = cdo
        self.state['named_preset_paths'] = sorted(self.owned_assets)
        self.state['preset_policy_verified'] = True
        self.write()

    def validate_preset(self, cdo, spec):
        lanes = list(_get(cdo, 'LeftLanes')) + list(_get(cdo, 'RightLanes'))
        assert len(lanes) == 2 and abs(sum(float(_get(l, 'Width')) for l in lanes) - spec['width_m'] * 100.0) < 0.01
        assert not _get(_get(cdo, 'CenterlineMarking'), 'MarkingMaterial')
        assert all(not _get(_get(l, 'OuterLaneMarking'), 'MarkingMaterial') and not _get(l, 'LaneOverlayMaterial') for l in lanes)
        assert not _get(cdo, 'PropSpawners') and not _get(cdo, 'RoadModules') and not _get(cdo, 'RoadPCGGraph')
        assert not _get(cdo, 'bEnableLandscapePaint')
        assert not _get(_get(_get(cdo, 'DefaultAutomations'), 'AutomaticCrossings'), 'bEnabled')
        for name in ('LeftSidewalkPresetClass', 'RightSidewalkPresetClass'):
            sidewalk = _get(cdo, name)
            if spec['sidewalk_width_m']:
                assert sidewalk and abs(float(_get(unreal.get_default_object(sidewalk), 'Width')) - spec['sidewalk_width_m'] * 100.0) < 0.01
            else:
                assert sidewalk is None

    def start(self):
        self.preflight()
        self.build_presets()
        self.guard()
        self.network = self.actor_subsystem.spawn_actor_from_class(unreal.DynamicRoadNetwork, unreal.Vector(0, 0, 0))
        assert self.network, 'Native network spawn failed'
        self.tag(self.network)
        self.network.set_actor_label('GeoCity_' + self.area + '_RoadBLD_' + self.revision)
        self.network.set_folder_path('GeoCity/RoadBLD/' + self.area)
        _set(self.network, 'bUseClipperForSidewalkOffset', True)
        self.state.update(phase='authoring', network_actor_path=_path(self.network))
        self.write()
        self.tick_handle = unreal.register_slate_post_tick_callback(self.tick)
        return self

    def create_road(self, row):
        self.guard()
        preset = self.presets[row['preset_key']]
        road = self.network.add_road_to_road_network(preset, 0.0)
        assert road, 'Native road spawn failed for source ' + str(row['source_osm_id'])
        self.roads.append(road)  # Record immediately, including failed authoring.
        self.tag(road, row['source_osm_id'])
        old_tags = list(_get(road, 'Tags'))
        _set(road, 'Tags', old_tags + [unreal.Name('GeoCityPiece_' + str(row['piece_id']))])
        road.set_actor_label('GeoCity_' + self.area + '_Road_' + str(row['piece_id']).replace(':', '_'))
        road.set_folder_path('GeoCity/RoadBLD/' + self.area)
        for name, value in {'bEnableLandscapeSplineMirroring': False, 'bConformToLandscape': False,
                            'bEnableLandscapePaint': False, 'RoadPCGGraph': None,
                            'bGenerateAbutments': False, 'bEnableRoadEdgeDetail': False,
                            'RoadCrownHeight': 0.0, 'RoadThickness': self.plan['settings']['road_thickness_cm']}.items():
            _set(road, name, value)
        # The installed component defaults reject radii below 10m. Configure
        # only this authored road's native component, preserving global/vendor
        # defaults and the bounded geographic fit required by this area.
        controls = _get(road, 'ControlSpline')
        limits = _get(controls, 'TurnRadiusLimit')
        target_radius = float(self.plan['settings']['max_turn_radius_cm'])
        _set(controls, 'TurnRadiusLimit', unreal.Vector2D(min(limits.x, target_radius), limits.y))
        assert _get(controls, 'TurnRadiusLimit').x <= target_radius
        points = []
        for x, y, z in row['points_m']:
            point = unreal.RoadSplineAuthoringPoint()
            _set(point, 'WorldPosition', unreal.Vector(x * 100.0, z * 100.0, y * 100.0 + self.plan['settings']['surface_clearance_cm']))
            _set(point, 'MaxRadius', self.plan['settings']['max_turn_radius_cm'])
            points.append(point)
        result = road.replace_control_spline_from_authoring_points(points)
        # UE Python maps this bool+OutError API to an empty string on success
        # and None on failure; confirm the complete native controls below.
        assert isinstance(result, str) and not result, 'Native atomic control spline rejected source ' + str(row['source_osm_id']) + ': ' + str(result)
        self.check_road(road, row)

    def check_road(self, road, row):
        info = _tool('RoadBLDDiscoveryToolset', 'DescribeRoad', road)
        points = list(_get(info, 'ControlPoints'))
        largest = 0.0
        if self.junction_repair:
            import geocity_roadbld_junctions as junctions
            junctions.verify_source_road(self, road, row, self.junction_repair)
        else:
            assert len(points) == len(row['points_m']), 'Native spline lost geographic vertices'
            for point, original in zip(points, row['points_m']):
                actual = _get(point, 'Location')
                expected = (original[0] * 100.0, original[2] * 100.0, original[1] * 100.0 + self.plan['settings']['surface_clearance_cm'])
                error = math.dist((actual.x, actual.y, actual.z), expected)
                largest = max(largest, error)
            assert largest <= self.plan['settings']['control_point_tolerance_cm'], 'Native spline moved original geography/ground heights'
        widths = list(_get(info, 'LeftLanes')) + list(_get(info, 'RightLanes'))
        # Exact installed FRoadBLDLaneInfo fields, not the preset's Width.
        for field in ('WidthAtStart', 'WidthAtEnd'):
            total = sum(float(_get(v, field)) for v in widths)
            assert abs(total - row['width_m'] * 100.0) <= 0.1, 'Native paved width differs from full geographic width'
        assert not _get(road, 'bEnableLandscapeSplineMirroring') and not _get(road, 'bConformToLandscape') and not _get(road, 'bEnableLandscapePaint')
        self.state['max_control_point_error_cm'] = max(self.state.get('max_control_point_error_cm', 0), largest)

    def request_rebuild(self):
        self.guard()
        result = _tool('RoadBLDBuildToolset', 'Rebuild', self.network, False, True, False, 0, False)
        assert result.is_complete and not result.error, 'Native rebuild dispatch failed: ' + str(result.error)
        status = json.loads(result.get_value_as_json_string())
        job_id = str(status.get('jobId') or '')
        assert job_id, 'Native licensed rebuild did not return a job ID'
        self.job_id = job_id
        self.rebuild_pass += 1
        self.rebuild_started = time.monotonic()
        self.state.update(phase='rebuilding', rebuild_job_id=job_id, rebuild_pass=self.rebuild_pass)
        self.write()

    def native_geos(self):
        road_paths = {_path(road) for road in self.roads + self.derived_junction_roads}
        output = []
        for actor in self.actor_subsystem.get_all_level_actors():
            if not isinstance(actor, unreal.RoadGeo):
                continue
            references = {_path(v) for v in _get(actor, 'SourceRoads')}
            if references.intersection(road_paths):
                assert references.issubset(road_paths), 'Generated geometry crosses area/network ownership'
                output.append(actor)
        return output

    def owned_actors(self):
        """Collect explicit native attachments and WorldBLD kit child references."""
        owned = ([self.network] if self.network else []) + list(self.roads) + list(self.derived_junction_roads) + self.native_geos()
        pending = list(owned)
        while pending:
            actor = pending.pop()
            children = list(actor.get_attached_actors())
            for kit in actor.get_components_by_class(unreal.WorldBLDKitElementComponent):
                children.extend(_get(kit, 'ElementChildren'))
            for child in children:
                if child is None or child in owned:
                    continue
                assert _path(child) not in self.initial_actor_paths, 'Native kit references a pre-existing foreign actor'
                self.tag(child)
                owned.append(child)
                pending.append(child)
        return owned

    def validate_mesh_footprints(self, actors):
        """Read actual generated native triangles; never alter or clip the mesh.

        Static/spline/dynamic native components use the installed GeometryScript
        read-copy API. ISMs are expanded with each exact native world transform.
        The copied DynamicMesh is transient and is never saved or instanced.
        Any unsupported component, empty RoadGeo, footprint overlap or area
        escape prevents a staged contract and leaves the old delivery intact.
        """
        began = time.monotonic()
        options = self.plan['settings']
        pads = self.plan['protected_building_footprints_xz_m']
        grid = {}
        prepared = []
        for i, row in enumerate(pads):
            box = _bounds(row['ring_xz_m'])
            prepared.append((row['source_osm_id'], box, _triangulate_ring(row['ring_xz_m'])))
            for cell in _grid_cells(box):
                grid.setdefault(cell, []).append(i)
        area = self.plan['area_box_xz_m']
        tolerance = float(options['area_boundary_tolerance_cm']) / 100.0
        maximum_escape = 0.0
        escapes = []
        overlaps = {}
        overlap_examples = []
        triangles_total = components_total = instances_total = 0
        projected_area = 0.0
        by_actor = {}
        seen = set()
        copy_options = unreal.GeometryScriptCopyMeshFromComponentOptions()
        _set(copy_options, 'bWantNormals', False)
        _set(copy_options, 'bWantTangents', False)
        def bounded():
            assert time.monotonic() - began <= options['mesh_validation_timeout_seconds'], 'Native mesh footprint verification exceeded bounded time; refusing unverified provider'
        for actor in actors:
            self.guard()
            # Kit-generated landscape patches cannot modify the authoritative
            # final HDA terrain. Only this generation's owned patches are read.
            patch_type = getattr(unreal, 'LandscapePatchComponent', None)
            if patch_type:
                assert all(not patch.is_enabled() for patch in actor.get_components_by_class(patch_type)), 'Native generated landscape patch remains enabled'
            for component in actor.get_components_by_class(unreal.MeshComponent):
                bounded()
                path = _path(component)
                if path in seen:
                    continue
                seen.add(path)
                if component.get_class().get_name() == 'StaticMeshComponent' and component.static_mesh is None:
                    continue  # Accepted only through complete physical merged-source proof below.
                is_instance = isinstance(component, unreal.InstancedStaticMeshComponent)
                transforms = [component.get_instance_transform(i, world_space=True) for i in range(component.get_instance_count())] if is_instance else [None]
                assert all(transform is not None for transform in transforms) if is_instance else True, 'Native ISM world transform is missing'
                if not transforms:
                    continue
                mesh = unreal.DynamicMesh()
                mesh, local_to_world, outcome = unreal.GeometryScript_SceneUtils.copy_mesh_from_component(component, mesh, copy_options, not is_instance)
                assert outcome == unreal.GeometryScriptOutcomePins.SUCCESS, 'Cannot read actual native mesh component: ' + path + ' outcome=' + str(outcome)
                mesh, triangle_list, triangle_gaps = unreal.GeometryScript_MeshQueries.get_all_triangle_indices(mesh, True)
                mesh, vector_list, vertex_gaps = unreal.GeometryScript_MeshQueries.get_all_vertex_positions(mesh, False)
                indices = list(unreal.GeometryScript_List.convert_triangle_list_to_array(triangle_list))
                vertices = list(unreal.GeometryScript_List.convert_vector_list_to_array(vector_list))
                assert len(indices) == mesh.get_triangle_count(), 'Native triangle read-copy coverage differs'
                if not indices:
                    continue
                assert component.get_num_materials() > 0 and all(component.get_material(i) for i in range(component.get_num_materials())), 'Native generated mesh material is missing: ' + path
                components_total += 1
                for transform in transforms:
                    bounded()
                    instances_total += 1
                    world_vertices = [transform.transform_location(v) for v in vertices] if transform is not None else vertices
                    points = [(float(v.x) / 100.0, float(v.y) / 100.0) for v in world_vertices]
                    assert all(math.isfinite(float(v.x)) and math.isfinite(float(v.y)) and math.isfinite(float(v.z)) for v in world_vertices), 'Native generated mesh has nonfinite vertices'
                    triangles_total += len(indices)
                    by_actor[_path(actor)] = by_actor.get(_path(actor), 0) + len(indices)
                    for triangle_index, index in enumerate(indices):
                        if triangle_index % 512 == 0:
                            bounded()
                        ids = (int(index.x), int(index.y), int(index.z))
                        assert all(0 <= i < len(points) for i in ids), 'Native triangle references an unavailable vertex'
                        triangle = tuple(points[i] for i in ids)
                        box = _bounds(triangle)
                        escape = max(area[0] - box[0], area[1] - box[1], box[2] - area[2], box[3] - area[3], 0.0)
                        maximum_escape = max(maximum_escape, escape)
                        if escape > tolerance and len(escapes) < 10:
                            escapes.append({'component': path, 'triangle_xz_m': triangle, 'escape_cm': escape * 100.0})
                        flat_area = abs(_cross(*triangle)) * 0.5
                        projected_area += flat_area
                        if flat_area <= 1e-12:
                            continue
                        candidates = {i for cell in _grid_cells(box) for i in grid.get(cell, ())}
                        for i in candidates:
                            source_id, pad_box, pad_triangles = prepared[i]
                            if box[2] <= pad_box[0] or pad_box[2] <= box[0] or box[3] <= pad_box[1] or pad_box[3] <= box[1]:
                                continue
                            intersection = sum(_triangle_intersection_area(triangle, pad) for pad in pad_triangles)
                            if intersection > 1e-12:
                                overlaps[source_id] = overlaps.get(source_id, 0.0) + intersection
                                if len(overlap_examples) < 10:
                                    overlap_examples.append({'source_osm_id': source_id, 'component': path,
                                                             'triangle_xz_m': triangle, 'intersection_m2': intersection})
                # Release references to transient copies between components.
                mesh = None
        failures = {key: value for key, value in overlaps.items() if value > options['building_overlap_tolerance_m2']}
        proof = {'schema': 'environmentpipeline.roadbld_native_mesh_fit.v1',
                 'basis': 'actual native generated component triangles in world XY; exact instance transforms; conservative summed projected intersections',
                 'protected_footprints_sha256': self.plan['protected_footprint_proof']['footprints_sha256'],
                 'protected_pad_count': len(pads), 'component_count': components_total, 'instance_geometry_count': instances_total,
                 'triangle_count': triangles_total, 'summed_projected_triangle_area_m2': projected_area,
                 'max_area_escape_cm': maximum_escape * 100.0, 'area_escape_examples': escapes,
                 'overlap_pad_count': len(failures), 'summed_triangle_intersection_m2_by_pad': failures,
                 'overlap_examples': overlap_examples, 'elapsed_seconds': time.monotonic() - began,
                 'passed': not failures and maximum_escape <= tolerance and triangles_total > 0 and projected_area > 0}
        self.state['native_mesh_footprint_validation'] = proof
        self.write()
        accepted_empty = {row['geometry_actor_path'] for row in self.state.get('native_grounding_validation', {}).get('automatic_empty_geometry', [])}
        assert all(by_actor.get(_path(geo), 0) > 0 or _path(geo) in accepted_empty for geo in self.geo_actors), 'A generated RoadGeo lacks actual physically supported geometry'
        assert proof['passed'], 'Native generated pavement/sidewalk/curb violates the exact geographic pad or map-boundary contract; review recorded native mesh conflicts'
        return proof

    def validate(self):
        self.guard()
        assert not self.network.is_road_network_stale(), 'Native network remains stale'
        all_roads = self.roads + self.derived_junction_roads
        networks = list(_tool('RoadBLDDiscoveryToolset', 'DescribeNetwork', self.network, len(all_roads) + 1))
        assert len(networks) == 1, 'Native network discovery did not return exactly one owned network'
        network_info = networks[0]
        assert len(self.roads) == self.plan['source_piece_count'], 'Native clipped-piece coverage differs'
        assert _get(network_info, 'RoadCount') == len(all_roads), 'Native source and derived road coverage differs'
        discovered_roads = {str(_get(_get(row, 'Actor'), 'RefPath')) for row in _get(network_info, 'Roads')}
        assert discovered_roads == {_path(road) for road in all_roads}, 'Native network source-road ownership differs'
        for road, row in zip(self.roads, self.plan['roads']):
            self.check_road(road, row)
        junctions = _tool('RoadBLDDiscoveryToolset', 'FindJunctionIssues', self.network)
        geometry = _tool('RoadBLDDiscoveryToolset', 'FindGeometryIssues', self.network, self.plan['settings']['max_geometry_issues'])
        self.state['junction_issues'] = _plain(junctions)
        self.state['geometry_issues'] = _plain(geometry)
        import geocity_roadbld_topology as topology
        unresolved, automatic_junctions = topology.classify_native_junction_issues(self, junctions)
        self.state['unresolved_junction_issues'] = _plain(unresolved)
        if self.junction_repair:
            self.junction_repair['automatic_native_junctions'] = automatic_junctions
        self.write()
        assert not unresolved and not geometry, 'Native junction or generated-mesh defects remain; prior output is preserved'
        self.geo_actors = self.native_geos()
        assert self.geo_actors, 'Rebuild returned no owned RoadGeo actors'
        if getattr(self, 'grounding_report', None):
            import geocity_roadbld_grounding as grounding
            self.state['native_grounding_validation'] = grounding.verify_native_delivery(self,
                self.landscape_sampler, landscape_actor_path=self.landscape_sampler.path)
        accepted_empty_components = {p for row in self.state.get('native_grounding_validation', {}).get('automatic_empty_geometry', []) for p in row['null_component_paths']}
        covered = set()
        for geo in self.geo_actors:
            self.tag(geo)
            references = {_path(v) for v in _get(geo, 'SourceRoads')}
            covered.update(references)
            assert _get(geo, 'bDisableIntersectionLandscapeAlignment'), 'Native junction landscape alignment was not retained disabled'
            geometry_components = list(geo.get_components_by_class(unreal.MeshComponent))
            assert geometry_components, 'Native geometry actor has no mesh components'
            for component in geometry_components:
                if _path(component) in accepted_empty_components:
                    assert component.get_class().get_name() == 'StaticMeshComponent' and component.static_mesh is None
                    continue
                if isinstance(component, unreal.PrimitiveComponent):
                    assert component.get_num_materials() > 0 and all(component.get_material(i) for i in range(component.get_num_materials())), 'Native road material is missing'
        assert covered == {_path(road) for road in all_roads}, 'Some geographic or derived roads have no generated native geometry'
        # Independent native physical centerline samples must stay within the
        # preserved source corridor; the authored control-point count alone is
        # insufficient to establish a fitted native road.
        fit_max = 0.0
        ground_max = 0.0
        for road, row in zip(self.roads, self.plan['roads']):
            samples = _tool('RoadBLDDiscoveryToolset', 'SampleRoad', road, 200.0)
            assert samples, 'Native physical road centerline is empty'
            for sample in samples:
                location = _get(sample, 'Location')
                point = (location.x / 100.0, location.y / 100.0)
                candidates = []
                for a, b in zip(row['points_m'], row['points_m'][1:]):
                    vx, vz = b[0] - a[0], b[2] - a[2]
                    t = max(0.0, min(1.0, ((point[0] - a[0]) * vx + (point[1] - a[2]) * vz) / (vx * vx + vz * vz)))
                    distance = math.hypot(point[0] - a[0] - t * vx, point[1] - a[2] - t * vz)
                    candidates.append((distance, a[1] + t * (b[1] - a[1])))
                closest, ground = min(candidates, key=lambda v: v[0])
                fit_max = max(fit_max, closest * 100.0)
                ground_max = max(ground_max, abs(location.z - ground * 100.0 - self.plan['settings']['surface_clearance_cm']))
                assert abs(float(_get(sample, 'LeftWidth')) + float(_get(sample, 'RightWidth')) - row['width_m'] * 100.0) <= 0.1, 'Native width differs inside the road'
        assert fit_max <= self.plan['settings']['centreline_fit_tolerance_cm'], 'Rounded native road deviates from geographic centerline'
        assert ground_max <= self.plan['settings']['ground_profile_tolerance_cm'], 'Native vertical profile does not follow exported final ground'
        if self.junction_repair:
            import geocity_roadbld_junctions as junctions
            junctions.verify_derived_roads(self, self.junction_repair)
        owned = self.owned_actors()
        self.validate_mesh_footprints(owned)
        self.state.update(phase='native_generated_verified', geometry_validation_passed=True,
                          generated_road_count=len(self.roads), generated_geometry_count=len(self.geo_actors),
                          max_physical_centerline_error_cm=fit_max, road_actor_paths=[_path(a) for a in self.roads],
                          max_ground_profile_error_cm=ground_max, geometry_actor_paths=[_path(a) for a in self.geo_actors])
        self.state['adapter_settings'] = dict(self.plan['settings'])
        self.state['clipping_report'] = self.clipping_report
        if getattr(self, 'grounding_report', None):
            self.state['grounding_report'] = self.grounding_report
        self.state['junction_repair'] = self.junction_repair
        self.state['derived_junction_roads'] = (self.junction_repair or {}).get('derived_junction_roads', [])
        self.state['actual_native_road_actor_count'] = len(all_roads)
        self.state['derived_junction_road_count'] = len(self.derived_junction_roads)
        self.state['native_component_bindings'] = self.capture_component_bindings(owned)
        self.state['owned_actor_paths'] = sorted(_path(a) for a in owned)
        self.state['source_piece_ledger'] = [dict(row, road_actor_path=_path(road)) for road, row in zip(self.roads, self.plan['roads'])]
        self.state['generated_piece_ids'] = sorted(self.plan['drivable_piece_ids'])
        source_delivery = []
        for source_id in self.plan['drivable_source_ids']:
            rows = sorted((v for v in self.state['source_piece_ledger'] if v['source_osm_id'] == source_id), key=lambda v: v['piece_id'])
            source_delivery.append({'source_osm_id': source_id, 'piece_ids': [v['piece_id'] for v in rows],
                                    'road_actor_paths': [v['road_actor_path'] for v in rows]})
        self.state['source_delivery'] = source_delivery
        self.write()
        return self.state

    def capture_component_bindings(self, actors):
        import geocity_roadbld_clip as clip
        output = []
        for actor in actors:
            for component in actor.get_components_by_class(unreal.MeshComponent):
                assert component.get_class().get_name() == 'StaticMeshComponent', 'Unsupported persistence binding requires explicit measurement'
                mesh = component.static_mesh
                if mesh is None:
                    accepted = {p for row in self.state.get('native_grounding_validation', {}).get('automatic_empty_geometry', []) for p in row['null_component_paths']}
                    assert _path(component) in accepted, 'Unverified null native binding'
                    continue
                points, indices = clip._read_geometry(clip._copy_static(mesh), component.get_world_transform())
                output.append({'actor': _path(actor), 'component': _path(component), 'mesh': _path(mesh),
                               'material_slots': clip._materials(component),
                               'component_world_transform': clip._transform(component.get_world_transform()),
                               'collision': clip._collision(component, mesh),
                               'world_triangle_geometry_sha256': clip._sha({'vertices_cm': points, 'triangles': indices})})
        return output

    def clip_final_geometry(self):
        import geocity_roadbld_clip as clip
        import geocity_roadbld_grounding as grounding
        from geocity_roadbld_landscape import LandscapeSampler
        owned = self.owned_actors()
        for actor in owned:
            self.tag(actor)
        token = self.revision + '_' + datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S%f')
        self.landscape_sampler = LandscapeSampler(self)
        self.grounding_report, prepared = grounding.ground_native_geos(self,
            self.landscape_sampler, max_seconds=600., landscape_actor_path=self.landscape_sampler.path)
        self.state['grounding_report'] = self.grounding_report
        self.clipping_report = clip.clip_native_outputs(self.plan, owned, self.guard, generation_id=token,
            max_seconds=600.,
            prepared_native_meshes={row['component_path']: row for row in prepared})
        for path in self.clipping_report['created_asset_paths']:
            asset = unreal.load_asset(path)
            assert asset
            self.owned_assets[_path(asset.get_outermost())] = asset.get_outermost()
        self.state['clipping_report'] = self.clipping_report
        self.write()

    def finish(self):
        if self.tick_handle is not None:
            unreal.unregister_slate_post_tick_callback(self.tick_handle)
            self.tick_handle = None

    def fail(self, exc):
        self.finish()
        try:
            staged_geos = self.native_geos()
        except Exception:
            staged_geos = self.geo_actors
        self.state.update(phase='failed_' + self.state['phase'], saved=False, error=repr(exc),
                          staged_actor_paths=[_path(a) for a in ([self.network] if self.network else []) + self.roads + self.derived_junction_roads + staged_geos],
                          previous_delivery_preserved=self.previous is not None)
        self.write()
        unreal.log_error('GeoCity RoadBLD: ' + repr(exc))
        # No broad rollback/deletion and no failed map save. Root can review the
        # recorded staged paths; the previous saved receipt is never overwritten.
        if self.on_complete:
            self.on_complete(self, False)

    def tick(self, delta_time):
        # Native asset creation/compilation and autosave may pump Slate while
        # this callback is still executing. A second invocation must never
        # validate the old rebuild timer or start another clipping operation.
        if getattr(self, '_tick_running', False):
            return
        self._tick_running = True
        try:
            self.guard()
            if self.state['phase'] == 'authoring':
                end = min(self.cursor + int(self.plan['settings']['roads_per_tick']), self.plan['source_piece_count'])
                for index in range(self.cursor, end):
                    self.create_road(self.plan['roads'][index])
                self.cursor = end
                self.state['authored_road_count'] = self.cursor
                if self.cursor == self.plan['source_piece_count']:
                    self.request_rebuild()
                elif self.cursor % 20 == 0:
                    self.write()
            elif self.state['phase'] == 'rebuilding':
                assert time.monotonic() - self.rebuild_started < self.plan['settings']['rebuild_timeout_seconds'], 'Native rebuild timeout; do not start another rebuild'
                status = _tool('RoadBLDBuildToolset', 'RebuildStatus', self.job_id)
                name = str(_get(status, 'State')).split('.')[-1].upper()
                if 'RUNNING' in name:
                    return
                assert 'SUCCEEDED' in name, 'Native rebuild did not succeed: ' + str(_plain(status))
                if self.rebuild_pass == 1:
                    if self.junction_repair is None:
                        import geocity_roadbld_junctions as junctions
                        self.junction_repair = junctions.repair_native_corners(self)
                        if self.junction_repair is None:
                            self.state['phase'] = 'conditioning'
                            self.write()
                            return
                    geos = self.native_geos()
                    assert geos, 'Native rebuild produced no geometry'
                    for geo in geos:
                        _set(geo, 'bDisableIntersectionLandscapeAlignment', True)
                    self.request_rebuild()
                else:
                    needs_alignment_pass = False
                    for geo in self.native_geos():
                        if not _get(geo, 'bDisableIntersectionLandscapeAlignment'):
                            _set(geo, 'bDisableIntersectionLandscapeAlignment', True)
                            needs_alignment_pass = True
                    if needs_alignment_pass:
                        self.request_rebuild()
                        return
                    patch_type = getattr(unreal, 'LandscapePatchComponent', None)
                    if patch_type:
                        for actor in self.owned_actors():
                            for patch in actor.get_components_by_class(patch_type):
                                patch.set_is_enabled(False)
                    self.state.update(phase='clipping', native_rebuild_completed=True)
                    self.write()
                    self.clip_final_geometry()
                    self.state['phase'] = 'validating'
                    self.write()
                    self.validate()
                    self.finish()
                    if self.on_complete:
                        self.on_complete(self, True)
            elif self.state['phase'] == 'conditioning':
                # A native SDK license refresh may reject an unchanged edit.
                # The junction helper retains its exact operation checkpoint;
                # yielding to Slate allows the official check to finish.
                import geocity_roadbld_junctions as junctions
                self.junction_repair = junctions.repair_native_corners(self)
                if self.junction_repair is None:
                    return
                geos = self.native_geos()
                assert geos, 'Native conditioning produced no owned geometry'
                for geo in geos:
                    _set(geo, 'bDisableIntersectionLandscapeAlignment', True)
                self.request_rebuild()
        except Exception as exc:
            self.fail(exc)
        finally:
            self._tick_running = False

    def staged_contract(self):
        """Validated, unsaved contract for one root-owned HDA transaction.

        Root verifies its live native paths before passing this to the official
        HDA suppression cook. The token is not a saved delivery or art approval.
        """
        self.guard()
        assert self.tick_handle is None and self.state['phase'] == 'native_generated_verified'
        self.validate()
        keys = ('area_id', 'named_map', 'mode', 'source_sha256', 'centreline_sha256', 'drivable_source_ids',
                'source_road_count', 'source_piece_count', 'generated_road_count', 'generated_piece_ids',
                'source_delivery', 'network_actor_path', 'road_actor_paths', 'geometry_actor_paths',
                'owned_actor_paths', 'geometry_validation_passed', 'protected_footprint_proof',
                'native_mesh_footprint_validation', 'adapter_settings', 'source_piece_ledger',
                'junction_repair', 'derived_junction_roads', 'actual_native_road_actor_count',
                'derived_junction_road_count', 'clipping_report', 'native_component_bindings')
        result = {key: self.state[key] for key in keys}
        for key in ('grounding_report', 'native_grounding_validation'):
            if key in self.state:
                result[key] = self.state[key]
        result.update(schema=DELIVERY_SCHEMA, provider='RoadBLD', phase='native_generated_validated_pending_save', saved=False,
                      coordinate_frame=FRAME, livevalidated_editor_transaction=True, bake_performed=False,
                      transaction={'pid': os.getpid(), 'lease_sha256': hashlib.sha256(self.lease_line.encode('utf-8')).hexdigest(),
                                   'revision': self.revision, 'named_map': self.p['map'], 'token': self.transaction_token})
        return result

    def commit(self, hda_receipt):
        """Finalize after HDA suppression/Bake, before its named final map save.

        Root calls this from its completed-HDA pre-map-save hook. The matching
        HDA receipt proves vehicle surfaces have been suppressed in this same
        transaction. The final named map contains a single visible road provider.
        Native RoadBLD authored actors are retained; no dialog-based bake occurs.
        """
        self.guard()
        assert self.tick_handle is None and self.state['phase'] == 'native_generated_verified'
        if getattr(self, 'grounding_report', None):
            # The official Bake replaces/renames the cooked Landscape. Verify
            # the resulting sole retained collision again with an empty cache.
            from geocity_roadbld_landscape import LandscapeSampler
            self.landscape_sampler = LandscapeSampler(self, saved=True)
        self.validate()
        hda = _read(hda_receipt)
        provider = hda.get('surface_geometry', {}).get('road_provider', {})
        assert provider.get('provider') == 'RoadBLD' and provider.get('vehicle_surfaces_suppressed') is True, 'HDA vehicle surfaces are not confirmed suppressed; refusing overlapping map save'
        for field in ('area_id', 'source_sha256', 'centreline_sha256', 'drivable_source_ids',
                      'source_road_count', 'generated_road_count', 'generated_piece_ids'):
            assert provider.get(field) == self.state[field], 'HDA/native transaction differs: ' + field
        native_contract = provider.get('contract') or provider.get('original_contract')
        assert native_contract and native_contract.get('transaction', {}).get('token') == self.transaction_token, 'HDA suppression used another native transaction'
        self.state['hda_vehicle_surfaces_suppressed'] = True
        self.state['transaction_token'] = self.transaction_token
        owned = self.owned_actors()
        for actor in owned:
            self.tag(actor)
        # Validate and save the named dependency closure before touching the
        # previous generation. A dependency error must preserve old actors.
        self.save_dependencies(owned)
        if self.previous:
            self.verify_previous_ownership()
            paths = set(self.previous['owned_actor_paths'])
            old = [a for a in self.actor_subsystem.get_all_level_actors() if _path(a) in paths]
            # Delete only the previous receipt's tagged generation, after the
            # replacement passed native source/width/junction/material checks.
            for actor in reversed(old):
                self.guard()
                assert self.actor_subsystem.destroy_actor(actor), 'Previous tagged output removal failed'
            assert not paths.intersection(_path(a) for a in self.actor_subsystem.get_all_level_actors())
        world = self.guard()
        assert unreal.EditorLoadingAndSavingUtils.save_packages([world.get_outermost()], False), 'Named retained map save failed'
        self.save_dependencies(owned, include_map=True)
        dirty_maps = {_path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()}
        assert self.p['map'] not in dirty_maps, 'Named map remains dirty'
        assert all(_path(a) in {_path(v) for v in self.actor_subsystem.get_all_level_actors()} for a in owned), 'Retained native output disappeared during save'
        delivery = {key: self.state[key] for key in ('area_id', 'named_map', 'mode', 'source_sha256', 'centreline_sha256',
                    'drivable_source_ids', 'source_road_count', 'source_piece_count', 'generated_road_count',
                    'generated_piece_ids', 'source_delivery', 'network_actor_path',
                    'road_actor_paths', 'geometry_actor_paths', 'geometry_validation_passed',
                    'protected_footprint_proof', 'native_mesh_footprint_validation', 'adapter_settings',
                    'source_piece_ledger', 'junction_repair', 'derived_junction_roads',
                    'actual_native_road_actor_count', 'derived_junction_road_count', 'clipping_report',
                    'native_component_bindings')}
        delivery.update(schema=DELIVERY_SCHEMA, provider='RoadBLD', phase='native_generated_saved_verified', saved=True,
                        revision=self.revision, owned_actor_paths=sorted(_path(a) for a in owned),
                        named_generated_dependency_paths=self.state['named_generated_dependency_paths'],
                        unreferenced_native_staged_packages=self.state.get('unreferenced_native_staged_packages', []),
                        coordinate_frame=FRAME, bake_performed=False, reopened=False,
                        hda_vehicle_surfaces_suppressed=True, utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        for key in ('grounding_report', 'native_grounding_validation'):
            if key in self.state:
                delivery[key] = self.state[key]
        _write(self.delivery_path, delivery)
        self.state.update(phase='native_generated_saved_verified', saved=True, delivery_path=str(self.delivery_path),
                          owned_actor_paths=delivery['owned_actor_paths'])
        self.write()
        return delivery

    def save_dependencies(self, actors, include_map=False):
        self.guard()
        # Failed/nested stages can leave unused named mesh copies in memory.
        # Save only retained bindings and reusable presets; preserve unused
        # copies as exact recorded leftovers without saving or deleting them.
        live_mesh_packages = {_path(component.static_mesh.get_outermost())
                              for actor in actors for component in actor.get_components_by_class(unreal.StaticMeshComponent)
                              if component.static_mesh}
        packages = {path:package for path,package in self.owned_assets.items()
                    if '/ClippedGeometry/' not in path or path in live_mesh_packages}
        seen = set()
        def visit(obj):
            if not isinstance(obj, unreal.Object) or _path(obj) in seen:
                return
            seen.add(_path(obj))
            package = obj.get_outermost()
            path = _path(package)
            if path.startswith(self.plan['asset_root'] + '/'):
                packages[path] = package
            elif path.startswith('/Game/') and path != self.p['map'] and path in {_path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()} and path not in self.reviewed_dirty:
                raise RuntimeError('RoadBLD dirtied a dependency outside its named area scope: ' + path)
            for field in ('StaticMesh', 'OverrideMaterials', 'StoreData', 'SourceDrawPreset', 'LeftSidewalkPreset', 'RightSidewalkPreset',
                          'RoadMaterial', 'IntersectionMaterial', 'Parent', 'TextureParameterValues', 'ParameterValue'):
                try:
                    value = _get(obj, field)
                except RuntimeError:
                    continue
                if isinstance(value, (list, tuple, unreal.Array)):
                    for item in value:
                        if isinstance(item, unreal.Object):
                            visit(item)
                        else:
                            try:
                                visit(_get(item, 'ParameterValue'))
                            except RuntimeError:
                                pass
                elif isinstance(value, unreal.Object):
                    visit(value)
        for actor in actors:
            visit(actor)
            for component in actor.get_components_by_class(unreal.ActorComponent):
                visit(component)
        registry = unreal.AssetRegistryHelpers.get_asset_registry()
        options = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
        pending = list(packages) + ([self.p['map']] if include_map else [])
        expanded = set()
        while pending:
            path = pending.pop()
            if path in expanded:
                continue
            expanded.add(path)
            for dependency in registry.get_dependencies(path, options) or []:
                dep = str(dependency)
                if not dep.startswith(self.plan['asset_root'] + '/') or dep in packages:
                    continue
                asset = unreal.load_asset(dep)
                assert asset, 'Missing owned generated dependency: ' + dep
                packages[dep] = asset.get_outermost()
                pending.append(dep)
        if packages:
            assert unreal.EditorLoadingAndSavingUtils.save_packages([packages[p] for p in sorted(packages)], True), 'Named native dependency save failed'
        dirty = {_path(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}
        assert not dirty.intersection(packages), 'Owned referenced packages remain unsaved'
        self.state['named_generated_dependency_paths'] = sorted(packages)
        self.state['unreferenced_native_staged_packages'] = sorted(path for path in self.owned_assets
            if path not in packages and path.startswith(self.plan['asset_root']+'/ClippedGeometry/') and path in dirty)
        self.write()


def _segment_distance(point, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    denominator = vx * vx + vy * vy
    if denominator <= 1e-20:
        return math.dist(point, a)
    t = max(0.0, min(1.0, ((point[0] - a[0]) * vx + (point[1] - a[1]) * vy) / denominator))
    return math.hypot(point[0] - a[0] - t * vx, point[1] - a[1] - t * vy)


def build(profile, export=None, settings=None, reviewed_dirty_packages=(), state_path=None,
          delivery_path=None, on_complete=None):
    """Begin native generation in the current licensed editor; return live run.

    on_complete(run, True) means generated/validated, before any map save or old
    output removal. Root uses run.staged_contract(), performs HDA suppression
    and Bake, then calls run.commit(hda_receipt) before its named map save. False
    is a failed staged generation with a precise receipt and no saved replacement.
    """
    operation = RoadBLDRun(profile, export, settings, reviewed_dirty_packages, state_path, delivery_path, on_complete)
    ACTIVE.append(operation)
    try:
        return operation.start()
    except Exception as exc:
        operation.fail(exc)
        raise


def preflight(profile, export=None, settings=None, reviewed_dirty_packages=()):
    """Fail before editor mutations when license/source/ownership/API is invalid.

    Uses the already completed official HDA export for read-only source checks.
    Writes only the adapter's bounded preflight state, never the map or content.
    Normal workflow should call this before its first HDA mutation when enabled.
    """
    operation = RoadBLDRun(profile, export, settings, reviewed_dirty_packages)
    operation.preflight()
    return dict(operation.state)


def status(operation=None):
    operation = operation or (ACTIVE[-1] if ACTIVE else None)
    return dict(operation.state) if operation else {'phase': 'not_started'}
