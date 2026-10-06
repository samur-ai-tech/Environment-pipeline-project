"""Append to the retained r017 PythonModule; nothing evaluates on import.

Integration: add string parms road_provider='houdini',
road_provider_contract_json='{}', route_surface_materials_json='{}'.
No new graph connection, shape package, raw geographic change or native asset
change is required. Raw complete coverage and its Landscape masks are untouched.
The RoadBLD option must remain inactive until the delivered native contract is
complete. The manager owns provider activation and named Unreal saves.
"""


_surface_r018_previous_material = cook_permanent_surface_material
_surface_r018_previous_selector = cook_nonbuilding_selector


def _surface_r018_parm(parent, name, default):
    parm = parent.parm(name)
    return str(parm.eval()).strip() if parm is not None else default


def _surface_r018_index_add(index, ring):
    """Add conditioned triangle coverage to the existing 4m subtraction index."""
    ring = _condition_surface_polygon(ring)
    if not ring:
        return 0.0
    total = 0.0
    for indices in _triangles(ring):
        triangle = [ring[i] for i in indices]
        area = abs(_signed_area(triangle))
        if area <= 1e-6:
            continue
        bounds = (min(p[0] for p in triangle), max(p[0] for p in triangle),
                  min(p[1] for p in triangle), max(p[1] for p in triangle))
        number = len(index[0])
        index[0].append((triangle, bounds))
        for iz in range(math.floor(bounds[2] / 4), math.floor(bounds[3] / 4) + 1):
            for ix in range(math.floor(bounds[0] / 4), math.floor(bounds[1] / 4) + 1):
                index[1].setdefault((ix, iz), set()).add(number)
        total += area
    return total


def _surface_r018_pad_index(parent):
    pads = parent.node('centroid_buildings_and_ground_pads')
    if pads is None:
        _fail('Missing corrected geographic building pads for surface exclusion')
    index = ([], {})
    for prim in pads.geometry().prims():
        ring = _xy(prim)
        if len(ring) >= 3:
            _surface_r018_index_add(index, ring)
    return index


def _surface_r018_line_pieces(ring, box):
    """Clip a true line analytically; outside excursions never create connectors."""
    pieces, current = [], None
    xmin, xmax, zmin, zmax = box
    for source_index, (a, b) in enumerate(zip(ring, ring[1:])):
        lower, upper = 0.0, 1.0
        for axis, minimum, maximum in ((0, xmin, xmax), (1, zmin, zmax)):
            delta = b[axis] - a[axis]
            if abs(delta) <= 1e-15:
                if a[axis] < minimum or a[axis] > maximum:
                    upper = -1.0
                    break
            else:
                first, last = (minimum - a[axis]) / delta, (maximum - a[axis]) / delta
                lower = max(lower, min(first, last))
                upper = min(upper, max(first, last))
        if upper < lower or upper < 0 or lower > 1:
            if current is not None:
                pieces.append(current)
                current = None
            continue
        lower, upper = max(0.0, lower), min(1.0, upper)
        start = a if lower == 0 else (a[0] + lower * (b[0] - a[0]), a[1] + lower * (b[1] - a[1]))
        end = b if upper == 1 else (a[0] + upper * (b[0] - a[0]), a[1] + upper * (b[1] - a[1]))
        if math.dist(start, end) <= 1e-8:
            if current is not None and lower == 0 and upper == 1:
                current['originals'].append((len(current['xy']) - 1, source_index + 1))
            continue
        if current is None or lower != 0:
            if current is not None:
                pieces.append(current)
            current = {'xy': [start], 'originals': [], 'boundaries': []}
            if lower == 0:
                current['originals'].append((0, source_index))
            else:
                current['boundaries'].append(0)
        steps = max(1, int(math.ceil(math.dist(start, end) / 2.0)))
        for step in range(1, steps + 1):
            fraction = step / float(steps)
            current['xy'].append(end if step == steps else
                                 (start[0] + fraction * (end[0] - start[0]),
                                  start[1] + fraction * (end[1] - start[1])))
        if upper == 1:
            current['originals'].append((len(current['xy']) - 1, source_index + 1))
        else:
            current['boundaries'].append(len(current['xy']) - 1)
            pieces.append(current)
            current = None
    if current is not None:
        pieces.append(current)
    return pieces


def _surface_r018_route_export(source, height, info):
    """Preserve source vertices; export bounded pieces on FINAL terrain."""
    records = []
    seen = set()
    for primitive in source.prims():
        cls = str(primitive.attribValue('highway_class'))
        if cls not in ROAD_CLASSES:
            continue
        osm_id = str(primitive.attribValue('source_osm_id'))
        if not osm_id or osm_id in seen:
            _fail('Native road export requires one complete source line per OSM ID: ' + osm_id)
        seen.add(osm_id)
        # This is a source line, not a face: retain duplicate closure vertices.
        ring = [(float(v.point().position()[0]), float(v.point().position()[2]))
                for v in primitive.vertices()]
        if len(ring) < 2:
            _fail('Native road export has a short source line: ' + osm_id)
        pieces = []
        for number, clipped in enumerate(_surface_r018_line_pieces(ring, _local_box(info))):
            xy = clipped['xy']
            elevations = _sample_grid(height, [p[0] for p in xy], [p[1] for p in xy])
            pieces.append({'piece_id': osm_id + ':' + str(number),
                           'points_m': [[float(p[0]), float(y), float(p[1])]
                                        for p, y in zip(xy, elevations)],
                           'original_point_indices': [i for i, _ in clipped['originals']],
                           'original_source_vertex_indices': [i for _, i in clipped['originals']],
                           'boundary_point_indices': clipped['boundaries']})
        records.append({'source_osm_id': osm_id, 'highway_class': cls,
                        'width_m': float(primitive.attribValue('width')),
                        'route_role': 'road',
                        'source_points_xz_m': [[float(x), float(z)] for x, z in ring],
                        'pieces': pieces})
    records.sort(key=lambda record: record['source_osm_id'])
    payload = json.dumps(records, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False)
    xmin, xmax, zmin, zmax = _local_box(info)
    return {'schema': 'environmentpipeline.roadbld_centerlines.v1',
            'area_id': info['area_id'], 'source_sha256': info['sha256'],
            'coordinate_frame': 'houdini_local_m_x_yup_z_to_unreal_cm_x_z_y',
            'centreline_sha256': hashlib.sha256(payload.encode('utf-8')).hexdigest(),
            'area_box_xz_m': [xmin, zmin, xmax, zmax],
            'maximum_sample_spacing_m': 2.0,
            'clip_policy': 'analytic_authoritative_area_box_no_endpoint_snapping',
            'roads': records}


def _surface_r018_provider(parent, export):
    """Suppress HDA vehicle meshes only after a complete retained native delivery."""
    provider = _surface_r018_parm(parent, 'road_provider', 'houdini').casefold()
    if provider == 'houdini':
        return {'provider': 'houdini', 'vehicle_mesh_suppressed': False,
                'vehicle_surfaces_suppressed': False,
                'reason': 'authoritative_houdini_visible_provider'}
    if provider != 'roadbld':
        _fail('road_provider must be houdini or RoadBLD')
    try:
        contract = json.loads(_surface_r018_parm(parent, 'road_provider_contract_json', '{}'))
    except (TypeError, ValueError):
        _fail('RoadBLD provider contract is not valid JSON')
    if not isinstance(contract, dict):
        _fail('RoadBLD provider contract must be an object')
    ids = [record['source_osm_id'] for record in export['roads']]
    if any(not record['pieces'] for record in export['roads']):
        _fail('Native road source includes a way with no in-area line piece')
    piece_ids = sorted(piece['piece_id'] for road in export['roads'] for piece in road['pieces'])
    expected = {'schema': 'environmentpipeline.roadbld_delivery.v1',
                'provider': 'RoadBLD', 'area_id': export['area_id'],
                'source_sha256': export['source_sha256'],
                'centreline_sha256': export['centreline_sha256'],
                'drivable_source_ids': ids, 'source_road_count': len(ids),
                'source_piece_count': len(piece_ids),
                'generated_road_count': len(piece_ids),
                'generated_piece_ids': piece_ids, 'mode': 'authored_native_retained',
                'geometry_validation_passed': True}
    for field, value in expected.items():
        if contract.get(field) != value:
            _fail('Incomplete or stale RoadBLD delivery contract: ' + field)
    named_map = contract.get('named_map', '')
    if (not isinstance(named_map, str) or
            not named_map.startswith('/Game/Project/Areas/' + export['area_id'] + '/') or
            '.' in named_map or ':' in named_map):
        _fail('RoadBLD delivery map is outside the exact geographic area')
    actor_prefix = named_map + '.' + named_map.rsplit('/', 1)[-1] + ':PersistentLevel.'
    network = contract.get('network_actor_path')
    actors = contract.get('road_actor_paths')
    if (not isinstance(network, str) or not network.startswith(actor_prefix) or
            not isinstance(actors, list) or len(actors) != len(piece_ids) or
            len(set(actors)) != len(actors) or
            not all(isinstance(path, str) and path.startswith(actor_prefix) for path in actors)):
        _fail('RoadBLD delivery actor identities are incomplete or outside the saved area')
    deliveries = contract.get('source_delivery')
    if not isinstance(deliveries, list) or len(deliveries) != len(ids):
        _fail('RoadBLD per-source delivery ledger is incomplete')
    expected_pieces = {road['source_osm_id']: sorted(p['piece_id'] for p in road['pieces'])
                       for road in export['roads']}
    delivered_paths = []
    delivered_sources = set()
    for delivery in deliveries:
        osm_id = delivery.get('source_osm_id')
        paths = delivery.get('road_actor_paths')
        if (osm_id not in expected_pieces or osm_id in delivered_sources or
                delivery.get('piece_ids') != expected_pieces[osm_id] or
                not isinstance(paths, list) or len(paths) != len(expected_pieces[osm_id])):
            _fail('RoadBLD per-source piece coverage differs: ' + str(osm_id))
        delivered_sources.add(osm_id)
        delivered_paths.extend(paths)
    if len(set(delivered_paths)) != len(piece_ids) or set(delivered_paths) != set(actors):
        _fail('RoadBLD per-source native actor identities differ')
    if contract.get('phase') == 'native_generated_saved_verified':
        if contract.get('saved') is not True:
            _fail('Final RoadBLD delivery has not been saved')
    elif contract.get('phase') == 'native_generated_validated_pending_save':
        transaction = contract.get('transaction', {})
        if (contract.get('saved') is not False or
                contract.get('livevalidated_editor_transaction') is not True or
                not isinstance(transaction, dict) or
                not isinstance(transaction.get('pid'), int) or transaction['pid'] <= 0 or
                transaction.get('named_map') != named_map or
                not isinstance(transaction.get('revision'), str) or not transaction['revision'] or
                not re.fullmatch(r'[a-fA-F0-9]{64}', str(transaction.get('lease_sha256', ''))) or
                not re.fullmatch(r'[A-Za-z0-9_.:-]{16,256}', str(transaction.get('token', '')))):
            _fail('Pending RoadBLD gate lacks the editor-owned validated transaction')
    else:
        _fail('RoadBLD delivery phase cannot activate the native provider')
    return {**contract, 'vehicle_mesh_suppressed': True,
            'vehicle_surfaces_suppressed': True,
            'contract': contract, 'reason': 'exact_complete_retained_native_delivery'}


def _surface_r018_route_materials(parent):
    # The existing scoped sidewalk material already supports the footway lane.
    # An empty path/track entry exposes the retained Dirt_Path RoadBed mask;
    # it does not remove source ways, widths, complete coverage or requests.
    materials = {'footway': {'path': '/Game/UtopianCity/Materials/MI_ConcreteGrain.MI_ConcreteGrain',
                             'uv_units_per_metre': 1.0},
                 'path': {'path': '', 'uv_units_per_metre': 1.0},
                 'track': {'path': '', 'uv_units_per_metre': 1.0}}
    try:
        override = json.loads(_surface_r018_parm(parent, 'route_surface_materials_json', '{}'))
    except (TypeError, ValueError):
        _fail('route_surface_materials_json is not valid JSON')
    if not isinstance(override, dict) or set(override).difference(materials):
        _fail('Route material overrides must name footway, path or track only')
    for cls, value in override.items():
        if isinstance(value, str):
            value = {'path': value, 'uv_units_per_metre': 1.0}
        if not isinstance(value, dict) or set(value).difference(('path', 'uv_units_per_metre')):
            _fail('Invalid route material entry: ' + cls)
        path = value.get('path', '')
        scale = float(value.get('uv_units_per_metre', 1.0))
        if (not isinstance(path, str) or
                (path and not re.fullmatch(r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+', path)) or
                not math.isfinite(scale) or scale <= 0 or scale > 16):
            _fail('Invalid native route material or UV scale: ' + cls)
        materials[cls] = {'path': path, 'uv_units_per_metre': scale}
    return materials


def _surface_r018_native_source(node):
    # Both grounded surface SOPs have [complete coverage, eligible lines, terrain].
    grounded = node.inputs()[0]
    if grounded is None or len(grounded.inputs()) < 3:
        _fail('Missing authoritative surface/line/final-terrain graph inputs')
    return grounded, grounded.inputs()[1].geometry(), grounded.inputs()[2].geometry()


def cook_permanent_surface_material(node):
    _surface_r018_previous_material(node)
    parent, geo = node.parent(), node.geometry()
    info = _package_for_sop(parent)
    grounded, source, terrain = _surface_r018_native_source(node)
    height = _grid_array(_volume(terrain, 'height'))
    export = _surface_r018_route_export(source, height, info)
    provider = _surface_r018_provider(parent, export)
    is_road = node.name() == 'catalog_road_material'
    route_materials = _surface_r018_route_materials(parent)
    pad_index = _surface_r018_pad_index(parent)
    attrs = {a.name(): a for a in geo.primAttribs()}
    material_attr = attrs['unreal_material']
    vertex_uv = geo.findVertexAttrib('uv')
    remove = []
    additions = []
    statistics = {'lane': 'road_surface' if is_road else 'sidewalk_surface',
                  'policy': 'class_aware_visible_profiles_final_terrain_building_pad_exclusion',
                  'source_coverage_preserved': True, 'road_provider': provider,
                  'class_input_faces': {}, 'class_visible_faces': {},
                  'class_mask_only_faces': {}, 'native_provider_suppressed_faces': 0,
                  'building_pad_excluded_area_m2': 0.0,
                  'route_materials': route_materials}
    if not is_road and grounded.geometry().findGlobalAttrib('joined_sidewalk_geometry_json'):
        statistics['joined_sidewalk'] = json.loads(grounded.geometry().attribValue('joined_sidewalk_geometry_json'))
    for prim in list(geo.prims()):
        cls = str(prim.attribValue('highway_class'))
        statistics['class_input_faces'][cls] = statistics['class_input_faces'].get(cls, 0) + 1
        if provider['vehicle_mesh_suppressed'] and cls in ROAD_CLASSES:
            remove.append(prim)
            statistics['native_provider_suppressed_faces'] += 1
            continue
        chosen = route_materials.get(cls) if is_road else None
        if chosen and not chosen['path']:
            remove.append(prim)
            statistics['class_mask_only_faces'][cls] = statistics['class_mask_only_faces'].get(cls, 0) + 1
            continue
        if chosen:
            prim.setAttribValue(material_attr, chosen['path'])
            for vertex in prim.vertices():
                p = vertex.point().position()
                vertex.setAttribValue(vertex_uv, (p[0] * chosen['uv_units_per_metre'],
                                                 p[2] * chosen['uv_units_per_metre'], 0.0))
        ring = _xy(prim)
        fragments = _permanent_sidewalk_without_roads(ring, pad_index)
        if fragments == [ring]:
            statistics['class_visible_faces'][cls] = statistics['class_visible_faces'].get(cls, 0) + 1
            continue
        statistics['building_pad_excluded_area_m2'] += max(
            0.0, abs(_signed_area(ring)) - sum(abs(_signed_area(f)) for f in fragments))
        values = {a.name(): prim.attribValue(a) for a in geo.primAttribs()}
        remove.append(prim)
        for fragment in fragments:
            additions.append((fragment, values, chosen))
            statistics['class_visible_faces'][cls] = statistics['class_visible_faces'].get(cls, 0) + 1
    if remove:
        geo.deletePrims(remove, keep_points=False)
    lift = 0.08 if is_road else 0.16
    for ring, values, chosen in additions:
        elevations = _sample_grid(height, [p[0] for p in ring], [p[1] for p in ring])
        prim = _add_polygon(geo, [(x, float(y) + lift, z) for (x, z), y in zip(ring, elevations)], values, attrs)
        scale = chosen['uv_units_per_metre'] if chosen else 1.0
        for vertex in prim.vertices():
            p = vertex.point().position()
            vertex.setAttribValue(vertex_uv, (p[0] * scale, p[2] * scale, 0.0))
    statistics['visible_face_count'] = len(geo.prims())
    _set_detail(geo, 'surface_geometry_json', json.dumps(statistics, sort_keys=True, allow_nan=False))
    _set_detail(geo, 'roadbld_centerlines_json', json.dumps(export, sort_keys=True, allow_nan=False))


def _surface_r018_join_candidates(edges, width):
    """Round convex corners; concave ribbons are united by subtraction."""
    def key(p):
        return (round(p[0], 4), round(p[1], 4))
    vertices = {}
    for a, b, values in edges:
        vertices.setdefault(key(a), {'point': a, 'incoming': [], 'outgoing': []})['outgoing'].append((a, b, values))
        vertices.setdefault(key(b), {'point': b, 'incoming': [], 'outgoing': []})['incoming'].append((a, b, values))
    for record in vertices.values():
        incoming, outgoing = record['incoming'], record['outgoing']
        if not incoming or not outgoing:
            continue
        point = record['point']
        values = dict(incoming[0][2])
        ids = sorted({i for edge in incoming + outgoing
                      for i in json.loads(edge[2]['source_ids_json'])})
        values['source_ids_json'] = json.dumps(ids)
        if len(ids) > 1:
            values['source_osm_id'] = ''
            values['source_id_status'] = 'ambiguous_near_junction'
        if len(incoming) != 1 or len(outgoing) != 1:
            # A bounded union disc also handles touching or branching outlines.
            ring = [(point[0] + width * math.cos(angle), point[1] + width * math.sin(angle))
                    for angle in np.linspace(0, 2 * math.pi, 32, endpoint=False)]
            yield ring, values, 'branch_round_join'
            continue
        a, b, _ = incoming[0]
        c, d, _ = outgoing[0]
        first = ((b[0] - a[0]), (b[1] - a[1]))
        second = ((d[0] - c[0]), (d[1] - c[1]))
        turn = math.atan2(first[0] * second[1] - first[1] * second[0],
                          first[0] * second[0] + first[1] * second[1])
        if turn <= 1e-6:
            continue
        first_length = math.hypot(*first)
        start = math.atan2(-first[0] / first_length, first[1] / first_length)
        steps = max(1, int(math.ceil(turn / (math.pi / 16))))
        arc = [(point[0] + width * math.cos(start + turn * step / steps),
                point[1] + width * math.sin(start + turn * step / steps))
               for step in range(steps + 1)]
        yield [point] + arc, values, 'convex_round_join'


def cook_sidewalks(node):
    """Joined drivable-road sidewalks; no walk/track asphalt-road convention."""
    parent, geo = node.parent(), node.geometry()
    info = _package_for_sop(parent)
    segments = _source_segments(node.inputs()[1].geometry())
    height = _grid_array(_volume(node.inputs()[2].geometry(), 'height'))
    raw = node.inputs()[0].geometry()
    boundaries = _permanent_exterior_road_edges(raw)
    # The index includes authoritative road union, true pads and then emitted
    # sidewalk triangles. Therefore corner/strip coverage is never duplicated.
    exclusions = _permanent_road_triangle_index(raw)
    pads = _surface_r018_pad_index(parent)
    for triangle, _ in pads[0]:
        _surface_r018_index_add(exclusions, triangle)
    geo.clear()
    attrs = _surface_attrs(geo)
    box = _local_box(info)
    width = 1.5
    edges, strips = [], []
    represented = set()
    status_counts = {}
    ledger = {'schema': 'environmentpipeline.joined_sidewalks.v1',
              'policy': 'drivable_exterior_union_round_joins_pad_exclusion_no_overlapping_profiles',
              'width_m': width, 'terrain_lift_m': 0.16,
              'maximum_round_join_chord_error_m': width * (1 - math.cos(math.pi / 32)),
              'drivable_edge_count': 0, 'non_drivable_edge_count': 0,
              'strip_candidate_count': 0, 'convex_round_join_count': 0,
              'branch_round_join_count': 0, 'retained_area_m2': 0.0,
              'retained_triangle_count': 0, 'source_coverage_preserved': True}
    for number in sorted(boundaries):
        for a, b, outside in boundaries[number]:
            midpoint = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            (distance, nearest_id, cls, declared), osm_id, status, candidates = _lineage(midpoint, segments)
            if cls not in ROAD_CLASSES:
                ledger['non_drivable_edge_count'] += 1
                continue
            if outside > 0:
                a, b = b, a
            length = math.dist(a, b)
            if length < 0.01:
                continue
            # Orient union boundary with interior left and exterior right.
            normal = ((b[1] - a[1]) / length, -(b[0] - a[0]) / length)
            values = {'source_osm_id': osm_id, 'nearest_osm_id': nearest_id,
                      'source_id_status': status, 'source_ids_json': json.dumps(candidates),
                      'nearest_distance_m': distance, 'source_area_id': info['area_id'],
                      'highway_class': cls, 'route_role': 'sidewalk', 'width_m': width,
                      'unreal_output_name': info['area_id'] + '_sidewalks',
                      'unreal_material': _mesh_preview_material(node), 'Cd': (0.51, 0.49, 0.44)}
            edges.append((a, b, values))
            strips.append(([a, b, (b[0] + width * normal[0], b[1] + width * normal[1]),
                            (a[0] + width * normal[0], a[1] + width * normal[1])], values))
            ledger['drivable_edge_count'] += 1
    def retain(ring, values):
        ring = _condition_surface_polygon(_clip_polygon(ring, box))
        if not ring:
            return
        fragments = _permanent_sidewalk_without_roads(ring, exclusions)
        for fragment in fragments:
            for indices in _triangles(fragment):
                triangle = _condition_surface_polygon([fragment[i] for i in indices])
                if not triangle:
                    continue
                elevations = _sample_grid(height, [p[0] for p in triangle], [p[1] for p in triangle])
                _add_polygon(geo, [(x, float(y) + 0.16, z) for (x, z), y in zip(triangle, elevations)], values, attrs)
                ledger['retained_area_m2'] += _surface_r018_index_add(exclusions, triangle)
                ledger['retained_triangle_count'] += 1
                if values['source_osm_id']:
                    represented.add(values['source_osm_id'])
                status = values['source_id_status']
                status_counts[status] = status_counts.get(status, 0) + 1
    for ring, values in strips:
        retain(ring, values)
        ledger['strip_candidate_count'] += 1
    for ring, values, kind in _surface_r018_join_candidates(edges, width):
        retain(ring, values)
        ledger[kind + '_count'] += 1
    _output_context(geo, info, parent.evalParm('seed'))
    _set_detail(geo, 'represented_road_ids_json', json.dumps(sorted(represented)))
    _set_detail(geo, 'lineage_status_counts_json', json.dumps(status_counts, sort_keys=True))
    _set_detail(geo, 'discarded_degenerate_faces', 0)
    _set_detail(geo, 'unreal_output_name', info['area_id'] + '_sidewalks')
    _set_detail(geo, 'joined_sidewalk_geometry_json', json.dumps(ledger, sort_keys=True, allow_nan=False))


def cook_nonbuilding_selector(node):
    _surface_r018_previous_selector(node)
    geo = node.geometry()
    if not geo.findGlobalAttrib('bank_catalog_readback_json'):
        return
    receipt = json.loads(geo.attribValue('bank_catalog_readback_json'))
    reports = {}
    export = None
    for name in ('catalog_road_material', 'catalog_sidewalk_material'):
        surface = node.parent().node(name)
        if surface is None:
            _fail('Missing retained surface material node: ' + name)
        output = surface.geometry()
        if not output.findGlobalAttrib('surface_geometry_json'):
            _fail('Missing completed surface geometry ledger: ' + name)
        reports[name] = json.loads(output.attribValue('surface_geometry_json'))
        current = json.loads(output.attribValue('roadbld_centerlines_json'))
        if export is not None and current != export:
            _fail('Road and sidewalk authoritative centreline exports differ')
        export = current
    provider = reports['catalog_road_material']['road_provider']
    if reports['catalog_sidewalk_material']['road_provider'] != provider:
        _fail('Road and sidewalk visible providers differ')
    receipt['surface_geometry'] = {
        'schema': 'environmentpipeline.class_aware_surface_geometry.v1',
        'road_provider': provider, 'outputs': reports,
        'source_coverage_preserved': True}
    receipt['roadbld_centerlines'] = export
    _set_detail(geo, 'bank_catalog_readback_json', json.dumps(receipt, sort_keys=True, allow_nan=False))
    path = node.parent().evalParm('bank_receipt_file').strip()
    if path:
        Path(path).write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False), encoding='utf-8')
