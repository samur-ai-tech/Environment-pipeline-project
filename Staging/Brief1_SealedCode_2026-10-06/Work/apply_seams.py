"""Apply the Part B diagnostic to the working copy of geocity_roadbld_seams.py (exact, once-only replacements)."""
from pathlib import Path
here = Path(__file__).resolve().parent
path = here / 'geocity_roadbld_seams.py'
text = path.read_text(encoding='utf-8')

RECORDER = '''

def _ring_distance_cm(triangle, ring):
    """Smallest XY distance from the triangle's corners to the ring's edges."""
    best = None
    for corner in triangle:
        for a, b in zip(ring, ring[1:] + ring[:1]):
            hit = _edge_projection(corner, a, b)
            if hit is not None and (best is None or hit[0] < best):
                best = hit[0]
    return best


def _record_opening_failure(run, proposal, carrier, surface, ring, before, after, before_index, after_index,
                            snapshot, affected, changed, sample_limit=50):
    """Write a bounded sidecar next to the run ledger before the opening assertion; never raises.

    Faces are identified by their canonical hash (material, positions, normals, UVs). A
    missing face whose material and corner positions reappear among the added faces is an
    attribute-only change (normals/UVs); otherwise its geometry is missing. Positions of
    missing faces come from the pre-edit point/triangle lists kept in `snapshot`.
    """
    import datetime
    try:
        import geocity_roadbld_workflow as base
        old_points, old_triangles, old_materials = snapshot
        missing, added = before - after, after - before

        def position_key(number, points, triangles, materials):
            return _sha([materials[number], sorted(_xyz_key(points[i]) for i in triangles[number])])

        def face(number, points, triangles, materials):
            corners = [list(points[i]) for i in triangles[number]]
            return {'triangle_index': number, 'material_id': materials[number], 'vertices_world_cm': corners,
                    'min_distance_to_ring_cm': _ring_distance_cm(corners, ring)}

        added_positions = {}
        for key in added:
            number = after_index.get(key)
            if number is not None:
                added_positions.setdefault(position_key(number, surface['points_cm'], surface['triangles'], surface['material_ids']), []).append(number)
        classes, missing_rows = {'attribute_only': 0, 'geometry_missing': 0, 'unindexed': 0}, []
        for key, count in missing.items():
            number = before_index.get(key)
            if number is None:
                classes['unindexed'] += 1
                row = {'hash': key, 'count': count, 'classification': 'unindexed'}
            else:
                twins = added_positions.get(position_key(number, old_points, old_triangles, old_materials), [])
                kind = 'attribute_only' if twins else 'geometry_missing'
                classes[kind] += 1
                row = dict(face(number, old_points, old_triangles, old_materials), hash=key, count=count,
                           classification=kind, same_positions_after_triangle_indices=twins[:8])
            if len(missing_rows) < sample_limit:
                missing_rows.append(row)
        added_rows = []
        for key, count in added.items():
            if len(added_rows) >= sample_limit:
                break
            number = after_index.get(key)
            row = {'hash': key, 'count': count}
            if number is not None:
                row.update(face(number, surface['points_cm'], surface['triangles'], surface['material_ids']))
            added_rows.append(row)
        provenance = proposal.get('derived_provenance') or {}
        gap = proposal.get('gap') or {}
        payload = {'schema': 'environmentpipeline.roadbld_opening_failure_diagnostic.v1',
                   'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   'error': 'Opening changed a native face/UV/material/normal outside its exact footprint',
                   'run': {'revision': getattr(run, 'revision', None), 'transaction_token': getattr(run, 'transaction_token', None),
                           'pid': run.state.get('pid'), 'area_id': getattr(run, 'area', None), 'named_map': run.p.get('map'),
                           'source_sha256': run.plan.get('source_sha256'), 'centreline_sha256': run.plan.get('centreline_sha256'),
                           'phase': run.state.get('phase'), 'pending_correction': getattr(run, '_pending_correction', None) is not None,
                           'ledger': str(run.state_path)},
                   'opening': {'kind': proposal.get('kind'), 'consolidated_join_id': proposal.get('consolidated_join_id'),
                               'source_road_actor_path': proposal.get('source_road_actor_path'),
                               'carrier_component_path': proposal.get('component_path'),
                               'join_roads': {'road_actor_path': provenance.get('road_actor_path'),
                                              'parent_road_actor_path': provenance.get('parent_road_actor_path'),
                                              'partner_actor_path': (provenance.get('native_endpoint_trim') or {}).get('partner_actor_path')},
                               'gap': {key: gap.get(key) for key in ('road_actor_path', 'segment', 'interval', 'length_cm', 'segment_world_cm')},
                               'ring_world_xy_cm': ring, 'ring_sha256': _sha(ring), 'width_cm': proposal.get('width_cm'),
                               'longitudinal_length_cm': proposal.get('longitudinal_length_cm'),
                               'affected_component_paths': [s['component_path'] for s in affected],
                               'changed_component_paths': list(changed)},
                   'failing_surface': {'component_path': surface['component_path'], 'is_carrier': surface is carrier,
                                       'geometry_actor_path': surface.get('geometry_actor_path'),
                                       'original_mesh_path': surface.get('original_mesh_path'),
                                       'source_road_paths': surface.get('source_road_paths'),
                                       'native_source_road_paths': surface.get('native_source_road_paths'),
                                       'uv_sets': (surface.get('attributes') or {}).get('uv_sets'),
                                       'triangles_before': len(old_triangles), 'triangles_after': len(surface['triangles'])},
                   'outside_faces': {'before_total': sum(before.values()), 'after_total': sum(after.values()),
                                     'before_distinct': len(before), 'after_distinct': len(after),
                                     'missing_total': sum(missing.values()), 'missing_distinct': len(missing),
                                     'added_total': sum(added.values()), 'added_distinct': len(added),
                                     'missing_classification': classes,
                                     'missing_min_distance_to_ring_cm': min((r['min_distance_to_ring_cm'] for r in missing_rows
                                                                            if r.get('min_distance_to_ring_cm') is not None), default=None)},
                   'sample_limit': sample_limit, 'missing_samples': missing_rows, 'added_samples': added_rows}
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S%f')
        target = run.state_path.with_name('ROADBLD_OPENING_FAILURE_%s_%s.json' % (run.revision, stamp))
        with target.open('x', encoding='utf-8') as stream:
            json.dump(payload, stream, indent=2, allow_nan=False)
        proposal['opening_failure_diagnostic'] = str(target)
        if getattr(base, 'unreal', None) is not None:
            base.unreal.log_error('GeoCity RoadBLD opening diagnostic written: ' + str(target))
        return str(target)
    except Exception as exc:
        try:
            import geocity_roadbld_workflow as base
            if getattr(base, 'unreal', None) is not None:
                base.unreal.log_error('GeoCity RoadBLD opening diagnostic could not be written: ' + repr(exc))
        except Exception:
            pass
        return None
'''

pairs = [
    (
        "def _xy_key(point):\n    return round(point[0], 6), round(point[1], 6)\n",
        "def _xy_key(point):\n    return round(point[0], 6), round(point[1], 6)\n\n\n"
        "def _xyz_key(point):\n    return round(point[0], 6), round(point[1], 6), round(point[2], 6)\n",
    ),
    (
        "def _outside_faces(surface, ring, bounded):\n"
        "    \"\"\"Canonical oriented face multiset including every UV and split normal.\"\"\"\n",
        "def _outside_faces(surface, ring, bounded, index=None):\n"
        "    \"\"\"Canonical oriented face multiset including every UV and split normal.\n\n"
        "    When `index` is a dict it receives hash -> first triangle index; the return\n"
        "    value is unchanged, so existing callers are unaffected.\n    \"\"\"\n",
    ),
    (
        "        ordered = min(corners[i:]+corners[:i] for i in range(3))\n"
        "        faces[_sha([surface['material_ids'][number],ordered])] += 1\n"
        "    return faces\n",
        "        ordered = min(corners[i:]+corners[:i] for i in range(3))\n"
        "        key = _sha([surface['material_ids'][number],ordered])\n"
        "        faces[key] += 1\n"
        "        if index is not None:\n"
        "            index.setdefault(key, number)\n"
        "    return faces\n",
    ),
    (
        "def _append_connector_apron(run, proposal, surfaces, fields, landscape_z, bounded):\n",
        RECORDER.lstrip('\n') + "\n\ndef _append_connector_apron(run, proposal, surfaces, fields, landscape_z, bounded):\n",
    ),
    (
        "    changed, outside = [], {}\n"
        "    affected = []\n",
        "    changed, outside = [], {}\n"
        "    affected = []\n"
        "    # Diagnostic capture: pre-edit face index and point/triangle lists per affected surface.\n"
        "    before_index, snapshots = {}, {}\n",
    ),
    (
        "        affected.append(surface)\n"
        "        outside[surface['component_path']] = _outside_faces(surface,ring,bounded)\n",
        "        affected.append(surface)\n"
        "        before_index[surface['component_path']] = {}\n"
        "        snapshots[surface['component_path']] = (surface['points_cm'], surface['triangles'], surface['material_ids'])\n"
        "        outside[surface['component_path']] = _outside_faces(surface,ring,bounded,before_index[surface['component_path']])\n",
    ),
    (
        "    outside_counts = {}\n"
        "    for surface in affected:\n"
        "        after = _outside_faces(surface,ring,bounded)\n"
        "        before = outside[surface['component_path']]\n"
        "        assert not (before-after), 'Opening changed a native face/UV/material/normal outside its exact footprint'\n",
        "    outside_counts = {}\n"
        "    for surface in affected:\n"
        "        after_index = {}\n"
        "        after = _outside_faces(surface,ring,bounded,after_index)\n"
        "        before = outside[surface['component_path']]\n"
        "        if before-after:\n"
        "            _record_opening_failure(run, proposal, carrier, surface, ring, before, after,\n"
        "                                    before_index[surface['component_path']], after_index,\n"
        "                                    snapshots[surface['component_path']], affected, changed)\n"
        "        assert not (before-after), 'Opening changed a native face/UV/material/normal outside its exact footprint'\n",
    ),
]
for old, new in pairs:
    if text.count(old) != 1:
        raise SystemExit('seams: expected exactly one occurrence of %r' % old[:70])
    text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8', newline='\n')
print('patched geocity_roadbld_seams.py', len(pairs), 'sites')
