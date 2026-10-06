"""Append to the retained HDA PythonModule after the other r015 changes.

Input contract retained:
  corrected_dsm_and_generated_masks: [heightfield, complete roads, building pads]
  nonbuilding requests: [source requests, final terrain, building pads, native table]
  nonbuilding selector: input 3 is the same final terrain.

This changes elevation grading only. Source geographic polygons, RoadBed and
BuildingPad masks, native identities and material routing are preserved.
"""


def _terrain_r015_dilate_one(mask):
    padded = np.pad(mask, 1, mode='constant', constant_values=False)
    result = np.zeros_like(mask, dtype=bool)
    for iz in range(3):
        for ix in range(3):
            result |= padded[iz:iz + mask.shape[0], ix:ix + mask.shape[1]]
    return result


def _terrain_r015_polygon_support_core(ring, x0, z0, width, height, half):
    """Minimal exact grid vertices supporting the true geographic polygon.

    ImageDraw rounds polygon coordinates to pixels. Dilation of that rounded
    polygon alone misses some diagonal boundary interpolation vertices. Cover
    the actual intersected cells, then retain all four vertices of each cell.
    """
    result = np.zeros((height, width), dtype=bool)
    xmin, xmax = math.floor(min(p[0] for p in ring)), math.ceil(max(p[0] for p in ring))
    zmin, zmax = math.floor(min(p[1] for p in ring)), math.ceil(max(p[1] for p in ring))
    for iz in range(zmin, zmax):
        for ix in range(xmin, xmax):
            polygon = _clip_polygon(ring, (ix, ix + 1, iz, iz + 1))
            if len(polygon) < 3 or abs(_signed_area(polygon)) <= 1e-10:
                continue
            for px, pz in ((ix, iz), (ix + 1, iz), (ix, iz + 1), (ix + 1, iz + 1)):
                col, row = int(px + half - x0), int(pz + half - z0)
                if 0 <= col < width and 0 <= row < height:
                    result[row, col] = True
    return result


def _terrain_r015_coherent_pad_records(pad_records, shape=(1009, 1009)):
    """Only touching interpolation-support pads share a generated datum.

    Different constants cannot occupy the same Landscape vertex. Reconcile that
    real overlap before generating terrain, native models OR facade assemblies.
    Preserve every geographic footprint and requested building height.
    """
    records = [dict(record) for record in sorted(pad_records, key=lambda item: item['id'])]
    original_bases = {record['id']: float(record['base_m']) for record in records}
    links = list(range(len(records)))
    owner = np.full(shape, -1, dtype=np.int32)
    half = (shape[1] - 1) / 2.0

    def find(index):
        while links[index] != index:
            links[index] = links[links[index]]
            index = links[index]
        return index

    for number, record in enumerate(records):
        ring = record['ring']
        x0 = max(0, int(math.floor(min(p[0] for p in ring) + half)) - 3)
        x1 = min(shape[1], int(math.ceil(max(p[0] for p in ring) + half)) + 4)
        z0 = max(0, int(math.floor(min(p[1] for p in ring) + half)) - 3)
        z1 = min(shape[0], int(math.ceil(max(p[1] for p in ring) + half)) + 4)
        if x0 >= x1 or z0 >= z1:
            continue
        image = Image.new('L', (x1 - x0, z1 - z0), 0)
        ImageDraw.Draw(image).polygon([(x + half - x0, z + half - z0)
                                      for x, z in ring], fill=255)
        core = _terrain_r015_polygon_support_core(ring, x0, z0, x1 - x0, z1 - z0, half)
        occupied = owner[z0:z1, x0:x1]
        # Adjacent fixed vertices also require a shared datum: two unrelated
        # constants on neighbouring vertices would make a one-metre cliff.
        contact = _terrain_r015_dilate_one(core)
        for other in np.unique(occupied[contact]):
            if other >= 0:
                a, b = find(number), find(int(other))
                if a != b:
                    links[max(a, b)] = min(a, b)
        occupied[core] = number
    groups = {}
    for number in range(len(records)):
        groups.setdefault(find(number), []).append(number)
    changed = 0
    maximum_shift = 0.0
    cluster_receipts = []
    for members in groups.values():
        ranked = sorted((float(records[i]['base_m']),
                         max(1.0, abs(_signed_area(records[i]['ring']))), i)
                        for i in members)
        half_weight = sum(weight for base, weight, i in ranked) / 2.0
        accumulated = 0.0
        shared_base = ranked[-1][0]
        for base, weight, i in ranked:
            accumulated += weight
            if accumulated >= half_weight:
                shared_base = base
                break
        for i in members:
            shift = abs(float(records[i]['base_m']) - shared_base)
            changed += int(shift > 1e-6)
            maximum_shift = max(maximum_shift, shift)
            records[i]['base_m'] = shared_base
        if len(members) > 1:
            cluster_receipts.append({'pad_ids': [records[i]['id'] for i in members],
                                     'shared_base_m': shared_base,
                                     'original_min_m': ranked[0][0],
                                     'original_max_m': ranked[-1][0]})
    # Keep separate nearby plateaus, but constrain their height difference to
    # the available gap. Otherwise even a feathered collar has no physical room
    # to bridge two large incompatible constants across a narrow city street.
    root_lookup = np.asarray([find(i) for i in range(len(records))], dtype=np.int32)
    labels = np.full(shape, -1, dtype=np.int32)
    valid = owner >= 0
    labels[valid] = root_lookup[owner[valid]]
    gap_edges = {}
    gap_limit = 12
    for root in groups:
        iz, ix = np.where(labels == root)
        if not len(ix):
            continue
        x0, x1 = max(0, int(ix.min()) - gap_limit), min(shape[1], int(ix.max()) + gap_limit + 1)
        z0, z1 = max(0, int(iz.min()) - gap_limit), min(shape[0], int(iz.max()) + gap_limit + 1)
        local_labels = labels[z0:z1, x0:x1]
        previous = local_labels == root
        for distance in range(1, gap_limit + 1):
            expanded = _terrain_r015_dilate_one(previous)
            band = expanded & ~previous
            for other in np.unique(local_labels[band]):
                other = int(other)
                if other >= 0 and other != root:
                    pair = tuple(sorted((root, other)))
                    gap_edges[pair] = min(distance, gap_edges.get(pair, distance))
            previous = expanded
    group_bases = {root: float(records[members[0]]['base_m']) for root, members in groups.items()}
    group_weights = {root: sum(max(1.0, abs(_signed_area(records[i]['ring']))) for i in members)
                     for root, members in groups.items()}
    # Gap measured on a square grid is conservative for diagonal transitions.
    # This constraint changes generated datum only, never source OSM or DSM.
    allowed_gradient = 0.45
    for iteration in range(128):
        largest_excess = 0.0
        for (a, b), gap in sorted(gap_edges.items()):
            difference = group_bases[a] - group_bases[b]
            excess = abs(difference) - allowed_gradient * gap
            if excess <= 0:
                continue
            largest_excess = max(largest_excess, excess)
            sign = 1.0 if difference > 0 else -1.0
            wa, wb = group_weights[a], group_weights[b]
            group_bases[a] -= sign * excess * wb / (wa + wb)
            group_bases[b] += sign * excess * wa / (wa + wb)
        if largest_excess < 1e-5:
            break
    for root, members in groups.items():
        for i in members:
            records[i]['base_m'] = group_bases[root]
    by_id = {record['id']: record for record in records}
    for cluster in cluster_receipts:
        cluster['shared_base_m'] = by_id[cluster['pad_ids'][0]]['base_m']
    shifts = [abs(record['base_m'] - original_bases[record['id']]) for record in records]
    maximum_shift = max(shifts) if shifts else 0.0
    changed = sum(shift > 1e-6 for shift in shifts)
    residual = max((max(0.0, abs(group_bases[a] - group_bases[b]) - allowed_gradient * gap)
                    for (a, b), gap in gap_edges.items()), default=0.0)
    return records, {'policy': 'coherent_touching_support_and_gap_limited_generated_datums',
                     'pad_count': len(records), 'cluster_count': len(groups),
                     'touching_clusters': cluster_receipts,
                     'pads_with_changed_generated_base': changed,
                     'maximum_generated_base_shift_m': maximum_shift,
                     'neighbor_datum_edges': len(gap_edges),
                     'neighbor_gap_limit_m': gap_limit,
                     'neighbor_datum_max_gradient_m_per_m': allowed_gradient,
                     'neighbor_constraint_residual_m': residual,
                     'source_xy_footprints_and_heights_preserved': True}


_terrain_r015_previous_building_pads = cook_building_pads


def cook_building_pads(node):
    _terrain_r015_previous_building_pads(node)
    geo = node.geometry()
    primitives = list(geo.prims())
    records = [{'id': str(p.attribValue('source_osm_id')),
                'ring': _xy(p), 'base_m': float(p.attribValue('base_m'))}
               for p in primitives if len(_xy(p)) >= 3]
    records, receipt = _terrain_r015_coherent_pad_records(records)
    bases = {record['id']: record['base_m'] for record in records}
    for primitive in primitives:
        base = bases.get(str(primitive.attribValue('source_osm_id')))
        if base is None:
            continue
        primitive.setAttribValue('base_m', float(base))
        for vertex in primitive.vertices():
            position = vertex.point().position()
            position[1] = base
            vertex.point().setPosition(position)
    _set_detail(geo, 'building_support_datums_json', json.dumps(receipt, sort_keys=True))


def _terrain_r015_graded_grid(baseline, pad_records):
    """Local flat support and a smooth collar; unchanged DSM outside collars.

    A complete one-cell halo around the geographic pad supplies the neighbouring
    vertices needed by bilinear sampling AND Landscape triangle interpolation.
    Individual collars blend against the original road-smoothed DSM, never an
    already modified neighbour. Original geographic pad interiors have priority
    over another pad's collar. Contradictory native support is caught downstream.
    """
    rows, cols = baseline.shape
    half = (cols - 1) / 2.0
    weighted_delta = np.zeros_like(baseline, dtype=np.float64)
    total_weight = np.zeros_like(baseline, dtype=np.float64)
    original_owner = np.full(baseline.shape, -1, dtype=np.int32)
    original_base = np.zeros_like(baseline, dtype=np.float32)
    core_min = np.full(baseline.shape, np.inf, dtype=np.float32)
    core_max = np.full(baseline.shape, -np.inf, dtype=np.float32)
    collar_count = 0
    widths = []
    for number, record in enumerate(sorted(pad_records, key=lambda item: item['id'])):
        ring, base = record['ring'], float(record['base_m'])
        if len(ring) < 3:
            continue
        # The first small window measures the original pad's required relief.
        x0 = max(0, int(math.floor(min(p[0] for p in ring) + half)) - 1)
        x1 = min(cols, int(math.ceil(max(p[0] for p in ring) + half)) + 2)
        z0 = max(0, int(math.floor(min(p[1] for p in ring) + half)) - 1)
        z1 = min(rows, int(math.ceil(max(p[1] for p in ring) + half)) + 2)
        if x0 >= x1 or z0 >= z1:
            continue
        image = Image.new('L', (x1 - x0, z1 - z0), 0)
        ImageDraw.Draw(image).polygon([(x + half - x0, z + half - z0)
                                      for x, z in ring], fill=255)
        inside = np.asarray(image) > 0
        if not inside.any():
            continue
        relief = float(np.max(np.abs(baseline[z0:z1, x0:x1][inside] - base)))
        # Smoothstep's maximum derivative is 1.5. A 0.35 m/m correction slope
        # requests a wider collar where the old median pad made a tall cliff.
        # Bound the actual local edit to 32 m; no area-wide terrain filtering.
        width = max(4, min(32, int(math.ceil(1.5 * relief / 0.35))))
        widths.append(width)
        extra = width + 2
        x0 = max(0, x0 - extra)
        x1 = min(cols, x1 + extra)
        z0 = max(0, z0 - extra)
        z1 = min(rows, z1 + extra)
        image = Image.new('L', (x1 - x0, z1 - z0), 0)
        ImageDraw.Draw(image).polygon([(x + half - x0, z + half - z0)
                                      for x, z in ring], fill=255)
        inside = np.asarray(image) > 0
        core = _terrain_r015_polygon_support_core(ring, x0, z0, x1 - x0, z1 - z0, half)
        weight = core.astype(np.float64)
        previous = core
        for distance in range(1, width + 1):
            expanded = _terrain_r015_dilate_one(previous)
            band = expanded & ~previous
            t = min(1.0, float(distance) / width)
            weight[band] = 1.0 - (3.0 * t * t - 2.0 * t * t * t)
            previous = expanded
        region = np.s_[z0:z1, x0:x1]
        total_weight[region] += weight
        weighted_delta[region] += weight * (base - baseline[region])
        original_owner[region][inside] = number
        original_base[region][inside] = base
        core_min[region][core] = np.minimum(core_min[region][core], base)
        core_max[region][core] = np.maximum(core_max[region][core], base)
        collar_count += int(np.count_nonzero((weight > 0) & ~core))
    corrected = (baseline + weighted_delta / np.maximum(1.0, total_weight)).astype(np.float32)
    # A neighbouring collar is soft influence, never permission to disturb a
    # compatible flat support halo. Only contradictory core heights need the
    # downstream support check; ordinary collars cannot create false rejection.
    has_core = np.isfinite(core_min)
    core_spread = np.zeros_like(baseline, dtype=np.float32)
    core_spread[has_core] = core_max[has_core] - core_min[has_core]
    compatible_core = has_core & (core_spread <= 0.03)
    corrected[compatible_core] = core_min[compatible_core]
    # Retain exact plateau interiors, including overlapping OSM pads' existing
    # deterministic source-ID order. A collar can never overwrite that interior.
    interior = original_owner >= 0
    corrected[interior] = original_base[interior]
    # Relax ONLY the free collar vertices with the plateau cores and original
    # DSM outside the collar held fixed. Independent weighted collars alone
    # can leave a seam where a neighbour influences the first free vertex.
    free_collar = (total_weight > 0) & ~has_core
    for iteration in range(32):
        padded = np.pad(corrected, 1, mode='edge')
        relaxed = (padded[:-2, 1:-1] + padded[2:, 1:-1] +
                   padded[1:-1, :-2] + padded[1:-1, 2:]) * 0.25
        corrected[free_collar] = relaxed[free_collar]
    conflict = has_core & (core_spread > 0.03)
    changed = np.abs(corrected - baseline) > 1e-6
    return corrected, {
        'policy': 'local_flat_support_one_cell_halo_adaptive_smoothstep_collar_v1',
        'source_pad_count': len(pad_records),
        'support_halo_cells': 1,
        'support_core_basis': 'four_vertices_of_every_intersected_true_polygon_cell',
        'collar_width_min_m': min(widths) if widths else 0,
        'collar_width_max_m': max(widths) if widths else 0,
        'collar_sample_count': collar_count,
        'conflicting_support_cells': int(np.count_nonzero(conflict)),
        'changed_grid_samples': int(np.count_nonzero(changed)),
        'collar_relaxation_iterations': 32,
        'max_local_correction_m': float(np.max(np.abs(corrected - baseline))),
        'unchanged_outside_local_collars': True,
        'geographic_masks_preserved': True,
    }


_terrain_r015_previous_city_terrain = cook_city_terrain


def cook_city_terrain(node):
    # Preserve all existing native Landscape/layer/material/output attributes.
    _terrain_r015_previous_city_terrain(node)
    info = _package_for_sop(node)
    geo = node.geometry()
    height_volume = _volume(geo, 'height')
    axis = np.arange(GRID_SAMPLES, dtype=np.float64) - (GRID_SAMPLES - 1) / 2.0
    x, z = np.meshgrid(axis, axis)
    raw = np.asarray(_dsm_local(info, x, z), dtype=np.float32)
    road_mask = _grid_array(_volume(geo, 'RoadBed'))
    padded = np.pad(raw, 1, mode='edge')
    smoothed = sum(padded[a:a + GRID_SAMPLES, b:b + GRID_SAMPLES]
                   for a in range(3) for b in range(3)) / 9.0
    baseline = raw * (1.0 - 0.55 * road_mask) + smoothed * (0.55 * road_mask)
    records = [{'id': str(p.attribValue('source_osm_id')),
                'area_id': str(p.attribValue('source_area_id')),
                'building_class': str(p.attribValue('building_class')),
                'height_m': float(p.attribValue('height_m')),
                'height_rule': str(p.attribValue('height_rule')),
                'ring': _xy(p), 'base_m': float(p.attribValue('base_m'))}
               for p in node.inputs()[2].geometry().prims() if len(_xy(p)) >= 3]
    corrected, receipt = _terrain_r015_graded_grid(baseline, records)
    pad_geo = node.inputs()[2].geometry()
    receipt['support_datums'] = json.loads(pad_geo.attribValue('building_support_datums_json'))
    height_volume.setAllVoxels(corrected.flatten(order='F').tolist())
    dz, dx = np.gradient(corrected, GRID_SPACING_M, GRID_SPACING_M)
    degrees = np.degrees(np.arctan(np.hypot(dx, dz)))
    steep = np.clip((degrees - 15.0) / 20.0, 0.0, 1.0).astype(np.float32)
    _volume(geo, 'Steep').setAllVoxels(steep.flatten(order='F').tolist())
    _volume(geo, 'Ground').setAllVoxels((1.0 - steep).flatten(order='F').tolist())
    receipt['max_final_slope_degrees'] = float(np.max(degrees))
    _set_detail(geo, 'terrain_support_grading_json', json.dumps(receipt, sort_keys=True))
    _set_detail(geo, 'terrain_correction', receipt['policy'])
    _set_detail(geo, 'corrected_min_m', float(corrected.min()))
    _set_detail(geo, 'corrected_max_m', float(corrected.max()))


_terrain_r015_previous_requests = cook_nonbuilding_requests


def cook_nonbuilding_requests(node):
    _terrain_r015_previous_requests(node)
    geo = node.geometry()
    if not geo.findPointAttrib('bank_role'):
        return
    height = _grid_array(_volume(node.inputs()[1].geometry(), 'height'))
    for point in geo.points():
        if point.attribValue('bank_role') == 'whole_building':
            p = point.position()
            p[1] = float(_sample_grid(height, [p[0]], [p[2]])[0])
            point.setPosition(p)


def _terrain_r015_support_samples(rectangle):
    """Sample EVERY Landscape cell vertex touched by the support rectangle.

    A planar set of these vertices guarantees both Landscape triangulations and
    the HDA's bilinear sampler yield the same support plane inside the rectangle.
    """
    samples = [tuple(p) for p in rectangle]
    xmin = math.floor(min(p[0] for p in rectangle))
    xmax = math.ceil(max(p[0] for p in rectangle))
    zmin = math.floor(min(p[1] for p in rectangle))
    zmax = math.ceil(max(p[1] for p in rectangle))
    for iz in range(zmin, zmax):
        for ix in range(xmin, xmax):
            intersection = _clip_polygon(rectangle, (ix, ix + 1, iz, iz + 1))
            if len(intersection) >= 3 and abs(_signed_area(intersection)) > 1e-10:
                samples.extend(((ix, iz), (ix + 1, iz),
                                (ix, iz + 1), (ix + 1, iz + 1)))
    return sorted(set(samples))


_terrain_r015_previous_candidate_rejection = _permanent_candidate_rejection


def _permanent_candidate_rejection(node, row, request, fit):
    reason = _terrain_r015_previous_candidate_rejection(node, row, request, fit)
    if reason or row['RequestRole'] != 'whole_building':
        return reason
    rectangle = _permanent_rectangle(row, request)
    samples = _terrain_r015_support_samples(rectangle)
    values = _sample_grid(fit['height'], [p[0] for p in samples], [p[1] for p in samples])
    p = request.position()
    base = float(_sample_grid(fit['height'], [p[0]], [p[2]])[0])
    # 3 cm admits the configured native Landscape's <1 cm height quantisation.
    # It does not admit the former measured 39 cm penetration / 11 cm gap.
    if float(np.max(np.abs(values - base))) > 0.03:
        return 'building_support_not_flat_on_final_terrain'
    return None


_terrain_r015_previous_selector = cook_nonbuilding_selector


def cook_nonbuilding_selector(node):
    _terrain_r015_previous_selector(node)
    geo = node.geometry()
    if not geo.findGlobalAttrib('bank_catalog_readback_json'):
        return
    receipt = json.loads(geo.attribValue('bank_catalog_readback_json'))
    terrain = node.inputs()[3].geometry()
    if terrain.findGlobalAttrib('terrain_support_grading_json'):
        receipt['terrain_support'] = json.loads(terrain.attribValue('terrain_support_grading_json'))
        _set_detail(geo, 'bank_catalog_readback_json', json.dumps(receipt, sort_keys=True))
        report = node.parent().evalParm('bank_receipt_file').strip()
        if report:
            Path(report).write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding='utf-8')
