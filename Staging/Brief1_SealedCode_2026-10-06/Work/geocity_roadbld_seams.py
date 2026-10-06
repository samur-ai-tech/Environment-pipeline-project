"""Repair measured asphalt gaps in owner-supplied transient native meshes.

Import is inert. Small seams use <=10cm native boundary extensions. Larger
connector openings require validated endpoint provenance and full-width
parent-corridor strips; obstructing geometry is removed inside those openings.
Original actor controls and source assets stay unchanged. The owner clips,
verifies, binds and saves scoped copies through its existing lifecycle.
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


def _xyz_key(point):
    return round(point[0], 6), round(point[1], 6), round(point[2], 6)


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
        eligibility = grounding._source_eligibility(surface, path, point)
        if eligibility is None:
            continue
        field = fields[surface['component_path']]
        for number, first, second in _boundary_edges(surface, field):
            projection = _edge_projection(point, surface['points_cm'][first], surface['points_cm'][second])
            if projection is None:
                continue
            distance, closest, fraction = projection
            if 1e-7 < distance and distance + extension_cm <= cap_cm:
                proof = None
                if path not in surface['native_source_road_paths']:
                    # A derived connector may extend only its own native edge,
                    # with the entire new triangle inside one existing exact
                    # parent-trim provenance disk (convex, so vertices suffice).
                    support_xy = [point[k]+extension_cm*(point[k]-closest[k])/distance for k in range(2)]
                    fan = [surface['points_cm'][first], surface['points_cm'][second], support_xy]
                    valid = [p for p in eligibility['derived_parent_provenance']
                             if all(math.dist(v[:2], p['native_endpoint_trim']['source_endpoint_world_cm'][:2])
                                    <= float(p['native_endpoint_trim']['pullback_cm'])+.1 for v in fan)]
                    if not valid:
                        continue
                    proof = min(valid, key=lambda p: p['road_actor_path'])
                candidates.append((distance, surface['component_path'], number, first, second, closest, fraction, surface, proof))
    assert candidates, 'Uncovered source point has no genuine same-source asphalt boundary within10cm: ' + json.dumps({'source_road_actor_path': path, 'point_world_cm': point}, allow_nan=False)
    distance, component, number, first, second, closest, fraction, surface, proof = min(candidates, key=lambda row: row[:5])
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
        'whole_fan_derived_parent_provenance': proof,
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


def continuous_gaps(plan, rows, surfaces, bounded, protected=False):
    """Measure every original segment against current eligible triangles."""
    import geocity_roadbld_grounding as g
    fields = [(s, g.AsphaltField(s['points_cm'], s['triangles'], s['material_ids'], s['upward'])) for s in surfaces]
    partition = g.analyze_protected_source_intervals(plan, rows, bounded) if protected else None
    exclusions = {r['piece_id']: {v['segment_index']: v['excluded_union'] for v in r['segments']}
                  for r in partition['source_roads']} if partition else {}
    gaps, segment_count = [], 0
    for row in rows:
        candidates = [(s, f) for s, f in fields if row['road_actor_path'] in s['source_road_paths']]
        assert candidates
        points = [[p[0]*100., p[2]*100., p[1]*100.+plan['settings']['surface_clearance_cm']] for p in row['points_m']]
        for number, (a, b) in enumerate(zip(points, points[1:])):
            if number % 64 == 0:
                bounded()
            segment_count += 1
            physical = g._physical_segment_intervals(a, b, row['road_actor_path'], candidates)
            excluded = exclusions.get(row['piece_id'], {}).get(number, [])
            covered = g._interval_union(physical + excluded)
            cursor = 0.
            for lo, hi in covered + [[1., 1.]]:
                if lo > cursor + 1e-13:
                    gaps.append({'road_actor_path': row['road_actor_path'], 'piece_id': row['piece_id'],
                        'source_osm_id': str(row['source_osm_id']), 'segment': number,
                        'interval': [cursor, lo], 'segment_world_cm': [a, b],
                        'length_cm': (lo-cursor)*math.dist(a[:2], b[:2])})
                cursor = max(cursor, hi)
    return gaps, {'source_piece_count': len(rows), 'segment_count': segment_count,
                  'protected_partition_used': protected, 'analytic_source_coverage_verified': not gaps,
                  'source_sha256': plan['source_sha256'], 'centreline_sha256': plan['centreline_sha256']}


def refresh_surface(surface):
    """Read current transient positions and actual native face normals."""
    import geocity_roadbld_workflow as base
    import geocity_roadbld_clip as clip
    u, mesh = base.unreal, surface['dynamic_mesh']
    points, triangles = clip._read_geometry(mesh, surface['transform'])
    mesh, ids, present = u.GeometryScript_Materials.get_all_triangle_material_i_ds(mesh)
    material_ids = [int(v) for v in u.GeometryScript_List.convert_index_list_to_array(ids)]
    assert present and len(material_ids) == len(triangles)
    flags = []
    for n, material in enumerate(material_ids):
        normal, valid = u.GeometryScript_MeshQueries.get_triangle_face_normal(mesh, n)
        assert valid
        flags.append(material == 0 and normal.z > .25)
    surface.update(points_cm=points, triangles=triangles, material_ids=material_ids,
                   upward=flags, attributes=clip._mesh_attributes(mesh), dynamic_mesh=mesh)


def _gap_point(gap, fraction=.5):
    a, b = gap['segment_world_cm']
    t = gap['interval'][0] + fraction*(gap['interval'][1]-gap['interval'][0])
    return [a[i]+t*(b[i]-a[i]) for i in range(3)]


def _touches_ring(triangle, ring):
    import geocity_roadbld_grounding as g
    if (max(p[0] for p in triangle) < min(p[0] for p in ring) or
        min(p[0] for p in triangle) > max(p[0] for p in ring) or
        max(p[1] for p in triangle) < min(p[1] for p in ring) or
        min(p[1] for p in triangle) > max(p[1] for p in ring)):
        return False
    if any(g._ring_location(v,ring) != 'exterior' for v in triangle):
        return True
    if any(g._ring_intervals(a,b,ring) for a,b in zip(triangle,triangle[1:]+triangle[:1])):
        return True
    return any((w := g._barycentric(p,*triangle)) is not None and min(w) >= 0. for p in ring)


def _outside_faces(surface, ring, bounded, index=None):
    """Canonical oriented face multiset including every UV and split normal.

    When `index` is a dict it receives hash -> first triangle index; the return
    value is unchanged, so existing callers are unaffected.
    """
    from collections import Counter
    import geocity_roadbld_workflow as base
    u, mesh = base.unreal, surface['dynamic_mesh']
    faces = Counter()
    for number, indices in enumerate(surface['triangles']):
        if number % 128 == 0:
            bounded()
        points = [surface['points_cm'][i] for i in indices]
        if ring is not None and _touches_ring(points,ring):
            continue
        unused,n0,n1,n2,valid = u.GeometryScript_MeshQueries.get_triangle_normals(mesh,number)
        assert valid
        normals = [[float(v.x),float(v.y),float(v.z)] for v in (n0,n1,n2)]
        uvsets = []
        for channel in range(surface['attributes']['uv_sets']):
            u0,u1,u2,valid = u.GeometryScript_MeshQueries.get_triangle_u_vs(mesh,channel,number)
            assert valid
            uvsets.append([[float(v.x),float(v.y)] for v in (u0,u1,u2)])
        corners = [points[i]+normals[i]+[v for channel in uvsets for v in channel[i]] for i in range(3)]
        # Compaction may rotate indices but may not reverse winding or change data.
        ordered = min(corners[i:]+corners[:i] for i in range(3))
        key = _sha([surface['material_ids'][number],ordered])
        faces[key] += 1
        if index is not None:
            index.setdefault(key, number)
    return faces


def _clear_fan_obstructions(proposal, surfaces, bounded):
    """Trim non-asphalt intrusions only inside the exact new asphalt fan."""
    import geocity_roadbld_workflow as base
    import geocity_roadbld_clip as clip
    u = base.unreal
    ring = [p[:2] for p in proposal['boundary_edge_world_cm']+[proposal['support_vertex_world_cm']]]
    changed = []
    for surface in surfaces:
        if proposal['source_road_actor_path'] not in surface['source_road_paths']:
            continue
        if not any(material != 0 and _touches_ring([surface['points_cm'][i] for i in tri],ring)
                   for tri,material in zip(surface['triangles'],surface['material_ids'])):
            continue
        bounded()
        before = _outside_faces(surface,ring,bounded)
        mesh = surface['dynamic_mesh']
        others = u.GeometryScript_MeshEdits.append_mesh(u.DynamicMesh(),mesh,u.Transform())
        asphalt_ids = [n for n,m in enumerate(surface['material_ids']) if m==0]
        other_ids = [n for n,m in enumerate(surface['material_ids']) if m!=0]
        others,deleted = u.GeometryScript_MeshEdits.delete_triangles_from_mesh(
            others,u.GeometryScript_List.convert_array_to_index_list(asphalt_ids),False)
        assert deleted == len(asphalt_ids)
        others = u.GeometryScript_MeshRepair.compact_mesh(others)
        zlo=min(p[2] for p in surface['points_cm'])-1000.;zhi=max(p[2] for p in surface['points_cm'])+1000.
        others = clip._trim(others,surface['transform'],[[p[0]/100.,p[1]/100.] for p in ring],
                            zlo,zhi,u.GeometryScriptBooleanOperation.TRIM_INSIDE)
        mesh,deleted = u.GeometryScript_MeshEdits.delete_triangles_from_mesh(
            mesh,u.GeometryScript_List.convert_array_to_index_list(other_ids),True)
        assert deleted == len(other_ids)
        mesh = u.GeometryScript_MeshEdits.append_mesh(mesh,others,u.Transform())
        surface['dynamic_mesh'] = u.GeometryScript_MeshRepair.compact_mesh(mesh)
        refresh_surface(surface)
        after = _outside_faces(surface,ring,bounded)
        assert not (before-after), 'Small seam changed a face/UV/material/normal outside its exact opening'
        overlap = 0.
        for tri,material in zip(surface['triangles'],surface['material_ids']):
            if material:
                overlap += base._triangle_intersection_area([surface['points_cm'][i][:2] for i in tri],ring)
        assert overlap <= .0001, 'Small seam still has non-asphalt obstruction'
        changed.append({'component_path':surface['component_path'],'outside_faces_preserved':sum(before.values()),
                        'remaining_nonasphalt_overlap_cm2':overlap})
    proposal['nonasphalt_intrusions_removed_within_fan'] = changed


def plan_connector_apron(gap, surfaces, fields):
    """A full-width opening at a measured native parent/connector mouth.

    This is a separate junction geometry operation, not a relaxed seam or
    coverage tolerance. Only a validated endpoint trim can justify it.
    """
    import geocity_roadbld_grounding as g
    path, point = gap['road_actor_path'], _gap_point(gap)
    assert 0 < gap['length_cm'] <= 100., 'Connector opening exceeds one metre'
    proofs = []
    for surface in surfaces:
        eligibility = g._source_eligibility(surface, path, point)
        if eligibility:
            proofs += eligibility.get('derived_parent_provenance', [])
    assert proofs, 'Large gap has no validated native connector endpoint provenance'
    proof = min(proofs, key=lambda p: p['road_actor_path'])
    trim = proof['native_endpoint_trim']
    assert all(math.dist(_gap_point(gap, f)[:2], trim['source_endpoint_world_cm'][:2]) <= trim['pullback_cm']+.1
               for f in (0., .5, 1.)), 'Opening escapes unchanged parent provenance radius'
    parent_width = float(proof['parent_full_width_cm'])
    width = parent_width
    assert 100. <= width <= 1400., 'Unreviewed native carriageway width'
    a, b = gap['segment_world_cm']
    length = math.dist(a[:2], b[:2]); dx, dy = (b[0]-a[0])/length, (b[1]-a[1])/length
    # The complete ring stays in this exact original straight source corridor.
    # Do not extend a rectangle beyond an original vertex into a different leg.
    t0 = max(0., gap['interval'][0]-10./length)
    t1 = min(1., gap['interval'][1]+10./length)
    first = [a[0]+t0*(b[0]-a[0]), a[1]+t0*(b[1]-a[1])]
    last = [a[0]+t1*(b[0]-a[0]), a[1]+t1*(b[1]-a[1])]
    ring = [[first[0]-dy*width/2, first[1]+dx*width/2],
            [last[0]-dy*width/2, last[1]+dx*width/2],
            [last[0]+dy*width/2, last[1]-dx*width/2],
            [first[0]+dy*width/2, first[1]-dx*width/2]]
    owners = [s for s in surfaces if path in s['native_source_road_paths']]
    assert owners
    choices = [(g._closest_xy(point, tri)[0], s['component_path'], n, s)
               for s in owners for n, tri in fields[s['component_path']].faces.items()]
    distance, component, number, carrier = min(choices, key=lambda v: v[:3])
    assert distance <= 60., 'Native parent asphalt is too far from the connector opening'
    for x,y in ring:
        along, across = (x-a[0])*dx+(y-a[1])*dy, -(x-a[0])*dy+(y-a[1])*dx
        assert -.000001 <= along <= length+.000001 and abs(across) <= parent_width/2+.000001
    return {'kind': 'validated_native_connector_carriageway_opening', 'gap': gap,
            'component_path': component, 'parent_asphalt_triangle_index': number,
            'source_road_actor_path': path, 'derived_provenance': proof,
            'ring_world_xy_cm': ring, 'width_cm': width,
            'longitudinal_length_cm': (t1-t0)*length,
            'nearest_parent_asphalt_cm': distance, 'all_existing_source_controls_unchanged': True,
            'carrier_provenance': 'direct native parent source membership; no expanded derived attribution',
            'width_basis': 'validated actual native parent lane width; sidewalks excluded',
            'whole_ring_proof': {'source_segment_world_cm':[a,b], 'parent_lane_width_cm':parent_width,
                'ring_inside_convex_straight_parent_corridor':True},
            'curb_sidewalk_and_duplicate_asphalt_inside_opening_must_be_removed': True}


def plan_join_strips(gap, row, surfaces, fields):
    """Follow the native parent corridor to a fully covered outer cross-section."""
    import geocity_roadbld_grounding as g
    base = plan_connector_apron(gap,surfaces,fields)
    proof = base['derived_provenance']; trim = proof['native_endpoint_trim']
    path, width = gap['road_actor_path'], base['width_cm']
    parents = {proof['parent_road_actor_path'],trim['partner_actor_path']}
    carrier = next(s for s in surfaces if s['component_path']==base['component_path'])
    assert parents.issubset(carrier['native_source_road_paths']), 'Join carrier must already represent both native parent roads'
    points = [[p[0]*100.,p[2]*100.,p[1]*100.] for p in row['points_m']]
    lengths = [math.dist(a[:2],b[:2]) for a,b in zip(points,points[1:])]
    at_segment = sum(lengths[:gap['segment']])
    ends = [at_segment+t*lengths[gap['segment']] for t in gap['interval']]
    if not trim['start']:
        ends = [sum(lengths)-v for v in ends]
        points.reverse()
    minimum = max(ends)+10.
    maximum = float(trim['pullback_cm'])+width
    candidates = [(s,fields[s['component_path']]) for s in surfaces if path in s['source_road_paths']]
    walked, legs, anchor = 0., [], None
    for a,b in zip(points,points[1:]):
        length = math.dist(a[:2],b[:2]); dx,dy = (b[0]-a[0])/length,(b[1]-a[1])/length
        for step in range(1,math.ceil(length/25.)+1):
            distance = min(length,step*25.)
            if walked+distance < minimum:
                continue
            if walked+distance > maximum:
                break
            point = [a[k]+distance/length*(b[k]-a[k]) for k in range(3)]
            left,right = [point[0]-dy*width/2,point[1]+dx*width/2],[point[0]+dy*width/2,point[1]-dx*width/2]
            coverage = g._physical_segment_intervals(left,right,path,candidates)
            if len(coverage)==1 and coverage[0][0]<=1e-13 and coverage[0][1]>=1.-1e-13:
                anchor = {'world_cm':point,'distance_from_source_endpoint_cm':walked+distance,
                          'cross_section_world_xy_cm':[left,right],'coverage':coverage}
                legs.append((a,point)); break
        if anchor:
            break
        if walked+length > maximum:
            break
        legs.append((a,b)); walked += length
    assert anchor, 'No full-width native parent cross-section within the measured endpoint neighbourhood'
    strips = []
    for a,b in reversed(legs):
        length=math.dist(a[:2],b[:2]);dx,dy=(b[0]-a[0])/length,(b[1]-a[1])/length
        ring=[[a[0]-dy*width/2,a[1]+dx*width/2],[b[0]-dy*width/2,b[1]+dx*width/2],
              [b[0]+dy*width/2,b[1]-dx*width/2],[a[0]+dy*width/2,a[1]-dx*width/2]]
        strips.append(dict(base,ring_world_xy_cm=ring,longitudinal_length_cm=length,
            outer_native_cross_section=anchor,consolidated_join_id=proof['road_actor_path'],
            whole_ring_proof={'source_leg_world_cm':[a,b],'parent_lane_width_cm':width,
                'ring_inside_convex_straight_parent_corridor':True},
            neighbourhood_limit_cm=maximum))
    return strips


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


def _append_connector_apron(run, proposal, surfaces, fields, landscape_z, bounded):
    """Replace the measured mouth opening on transient native copies only."""
    import geocity_roadbld_workflow as base
    import geocity_roadbld_grounding as g
    import geocity_roadbld_clip as clip
    u = base.unreal
    carrier = next(s for s in surfaces if s['component_path'] == proposal['component_path'])
    # Earlier strips may renumber the carrier. Select its current native plane.
    middle = [sum(p[k] for p in proposal['ring_world_xy_cm'])/4 for k in range(2)]
    parent_index = min(fields[carrier['component_path']].faces,
        key=lambda n:g._closest_xy(middle,fields[carrier['component_path']].faces[n])[0])
    parent_triangle = fields[carrier['component_path']].faces[parent_index]
    ring = proposal['ring_world_xy_cm']
    left0, left1, right1, right0 = ring
    nx = max(2, math.ceil(proposal['longitudinal_length_cm']/25.))
    ny = max(2, math.ceil(proposal['width_cm']/50.))
    clearance = float(run.plan['settings']['surface_clearance_cm'])
    path = proposal['source_road_actor_path']
    source_road = next(r for r in run.roads if base._path(r) == path)
    thickness = float(base._get(source_road, 'RoadThickness'))
    assert 0 < thickness <= 100., 'Native pavement thickness is unsupported'
    # Read the original native UV plane before boolean trimming can renumber it.
    uv_planes = []
    for channel in range(carrier['attributes']['uv_sets']):
        values = []
        for weights in ((1.,0.,0.), (0.,1.,0.), (0.,0.,1.)):
            unused, valid, uv = u.GeometryScript_MeshQueries.get_interpolated_triangle_uv(
                carrier['dynamic_mesh'], channel, parent_index, u.Vector(*weights))
            assert valid
            values.append([float(uv.x), float(uv.y)])
        uv_planes.append(values)
    points = []
    for ix in range(nx+1):
        for iy in range(ny+1):
            bounded()
            t, v = ix/nx, iy/ny
            left = [left0[k]+t*(left1[k]-left0[k]) for k in range(2)]
            right = [right0[k]+t*(right1[k]-right0[k]) for k in range(2)]
            xy = [left[k]+v*(right[k]-left[k]) for k in range(2)]
            z = float(landscape_z(*xy))+clearance
            if ix in (0, nx) or iy in (0, ny):
                hits = [field.covered(xy) for s, field in
                        ((s, fields[s['component_path']]) for s in surfaces if path in s['source_road_paths'])]
                hits = [hit for hit in hits if hit is not None]
                if hits:
                    edge_z = max(hit[0] for hit in hits)
                    z = edge_z
            points.append([*xy, z])
    count = len(points)
    points += [[p[0], p[1], p[2]-thickness] for p in points]
    faces, top_faces = [], []
    for ix in range(nx):
        for iy in range(ny):
            a = ix*(ny+1)+iy; b = a+ny+1
            for indices in ([a,b,b+1], [a,b+1,a+1]):
                if _unit_normal([points[i] for i in indices])[2] > 0:
                    indices = list(reversed(indices))
                assert -_unit_normal([points[i] for i in indices])[2] > .25, 'Corrected apron is not an upward native surface'
                top_faces.append(indices); faces.append(indices)
                faces.append([i+count for i in reversed(indices)])
    perimeter = ([ix*(ny+1) for ix in range(nx+1)] +
                 [nx*(ny+1)+iy for iy in range(1,ny+1)] +
                 [ix*(ny+1)+ny for ix in range(nx-1,-1,-1)] +
                 list(range(ny-1,0,-1)))
    for a,b in zip(perimeter,perimeter[1:]+perimeter[:1]):
        faces.extend([[a,b+count,b], [a,a+count,b+count]])
    proof = proposal['derived_provenance']
    join_roads = {proof['road_actor_path'], proof['parent_road_actor_path'],
                  proof['native_endpoint_trim']['partner_actor_path']}
    changed, outside = [], {}
    affected = []
    # Diagnostic capture: pre-edit face index and point/triangle lists per affected surface.
    before_index, snapshots = {}, {}
    for surface in surfaces:
        if not join_roads.intersection(surface['native_source_road_paths']):
            continue
        if not any(_touches_ring([surface['points_cm'][i] for i in tri],ring) for tri in surface['triangles']):
            continue
        assert set(surface['native_source_road_paths']).issubset(join_roads), 'Opening would alter a nonparticipating native road'
        affected.append(surface)
        before_index[surface['component_path']] = {}
        snapshots[surface['component_path']] = (surface['points_cm'], surface['triangles'], surface['material_ids'])
        outside[surface['component_path']] = _outside_faces(surface,ring,bounded,before_index[surface['component_path']])
    assert carrier in affected
    for surface in affected:
        bounded()
        before = _sha({'points':surface['points_cm'], 'triangles':surface['triangles']})
        # Remove all classes in the opening, including raised curb/sidewalk.
        # Asphalt added under an obstructing old curb is never a valid repair.
        zlo = min(p[2] for p in surface['points_cm'])-1000.
        zhi = max(p[2] for p in surface['points_cm'])+1000.
        surface['dynamic_mesh'] = clip._trim(surface['dynamic_mesh'], surface['transform'],
            [[p[0]/100.,p[1]/100.] for p in ring], zlo, zhi, u.GeometryScriptBooleanOperation.TRIM_INSIDE)
        surface['dynamic_mesh'] = u.GeometryScript_MeshRepair.compact_mesh(surface['dynamic_mesh'])
        refresh_surface(surface)
        assert surface['triangles'], 'Opening removed an entire native component'
        if before != _sha({'points':surface['points_cm'], 'triangles':surface['triangles']}):
            changed.append(surface['component_path'])
    mesh = carrier['dynamic_mesh']
    indices = []
    for point in points:
        local = u.MathLibrary.inverse_transform_location(carrier['transform'], u.Vector(*point))
        mesh, index = u.GeometryScript_MeshEdits.add_vertex_to_mesh(mesh, local, True)
        assert index >= 0
        indices.append(int(index))
    for number, face in enumerate(faces):
        if number % 32 == 0:
            bounded()
        mesh, triangle = u.GeometryScript_MeshEdits.add_triangle_to_mesh(mesh, u.IntVector(*(indices[i] for i in face)), 0, True)
        assert triangle >= 0
        mesh, valid = u.GeometryScript_Materials.set_triangle_material_id(mesh, triangle, 0, True)
        assert valid
        for channel, plane in enumerate(uv_planes):
            values = []
            for index in face:
                w = g._barycentric(points[index], *parent_triangle)
                assert w is not None
                values.append(u.Vector2D(*(sum(w[i]*plane[i][k] for i in range(3)) for k in range(2))))
            uv = u.GeometryScriptUVTriangle(); uv.uv0,uv.uv1,uv.uv2 = values
            mesh, valid = u.GeometryScript_UVs.set_mesh_triangle_u_vs(mesh, channel, triangle, uv, True)
            assert valid
        normal, valid = u.GeometryScript_MeshQueries.get_triangle_face_normal(mesh, triangle)
        assert valid
        normals = u.GeometryScriptTriangle(); normals.vector0 = normals.vector1 = normals.vector2 = normal
        mesh, valid = u.GeometryScript_Normals.set_mesh_triangle_normals(mesh, triangle, normals, number != len(faces)-1)
        assert valid
    carrier['dynamic_mesh'] = mesh
    refresh_surface(carrier)
    outside_counts = {}
    for surface in affected:
        after_index = {}
        after = _outside_faces(surface,ring,bounded,after_index)
        before = outside[surface['component_path']]
        if before-after:
            _record_opening_failure(run, proposal, carrier, surface, ring, before, after,
                                    before_index[surface['component_path']], after_index,
                                    snapshots[surface['component_path']], affected, changed)
        assert not (before-after), 'Opening changed a native face/UV/material/normal outside its exact footprint'
        outside_counts[surface['component_path']] = sum(before.values())
    # Actual raw curb/sidewalk triangles must have no positive-area remnant
    # in the opening. This checks every involved component, not a midpoint.
    from geocity_roadbld_workflow import _triangulate_ring, _triangle_intersection_area
    mask = _triangulate_ring(ring)
    obstructing_area = 0.
    for surface in surfaces:
        if not join_roads.intersection(surface['native_source_road_paths']):
            continue
        for face, material in zip(surface['triangles'], surface['material_ids']):
            if material == 0:
                continue
            tri = [surface['points_cm'][i][:2] for i in face]
            obstructing_area += sum(_triangle_intersection_area(tri, t) for t in mask)
    assert obstructing_area <= .0001, 'Raised curb/sidewalk remains inside the corrected carriageway opening'
    proposal.update(changed_components=sorted(set(changed+[carrier['component_path']])),
        thickness_cm=thickness, top_vertex_count=count, appended_triangle_count=len(faces),
        interpolated_native_uv_sets=len(uv_planes), obstructing_class_overlap_cm2=obstructing_area,
        unchanged_outside_face_counts=outside_counts,
        assets_bound=False, source_controls_changed=False)


def repair_continuous(run, rows, surfaces, landscape_z, bounded, protected=False):
    """Generic full-interval correction on owner-supplied transient meshes."""
    import geocity_roadbld_grounding as g
    initial, unused = continuous_gaps(run.plan, rows, surfaces, bounded, protected)
    assert len(initial) <= 64, 'Unreviewed number of native source interval defects'
    repairs = []
    # Larger endpoint openings need a full carriageway and curb removal first.
    planned, join_ids = [], set()
    by_path = {row['road_actor_path']:row for row in rows}
    fields = {s['component_path']:g.AsphaltField(s['points_cm'],s['triangles'],s['material_ids'],s['upward']) for s in surfaces}
    for gap in initial:
        if gap['length_cm'] <= 10.:
            continue
        planned += plan_join_strips(gap,by_path[gap['road_actor_path']],surfaces,fields)
    assert len(planned) <= 64, 'Unreviewed number of parent-corridor opening strips'
    for proposal in planned:
        fields = {s['component_path']:g.AsphaltField(s['points_cm'],s['triangles'],s['material_ids'],s['upward']) for s in surfaces}
        _append_connector_apron(run, proposal, surfaces, fields, landscape_z, bounded)
        join_ids.add(proposal['consolidated_join_id'])
        repairs.append(proposal)
    gaps, unused = continuous_gaps(run.plan, rows, surfaces, bounded, protected)
    for gap in gaps:
        assert gap['length_cm'] <= 10., 'Large source opening remains after full-width junction correction'
        for attempt in range(16):
            fields = {s['component_path']:g.AsphaltField(s['points_cm'],s['triangles'],s['material_ids'],s['upward']) for s in surfaces}
            a,b = gap['segment_world_cm']; path = gap['road_actor_path']
            candidates = [(s,fields[s['component_path']]) for s in surfaces if path in s['source_road_paths']]
            iv = g._physical_segment_intervals(a,b,path,candidates)
            remaining = []
            cursor = gap['interval'][0]
            for lo,hi in iv + [[gap['interval'][1],gap['interval'][1]]]:
                if hi < cursor or lo > gap['interval'][1]:
                    continue
                if lo > cursor+1e-13:
                    remaining.append([cursor,min(lo,gap['interval'][1])])
                cursor = max(cursor,hi)
            if cursor < gap['interval'][1]-1e-13:
                remaining.append([cursor,gap['interval'][1]])
            if not remaining:
                break
            target = dict(gap, interval=remaining[0])
            point = _gap_point(target)
            proposal = plan_boundary_fan(path, point, surfaces, fields, landscape_z, run.plan['settings']['surface_clearance_cm'])
            surface = next(s for s in surfaces if s['component_path']==proposal['component_path'])
            # Extend the native asphalt plane; a terrain sample still gates its
            # height. This avoids creating a steep needle at a narrow boundary.
            tri = fields[surface['component_path']].faces[proposal['parent_asphalt_triangle_index']]
            support = proposal['support_vertex_world_cm']
            support[2] = g._plane_z(g._barycentric(support,*tri),tri)
            assert abs(support[2]-float(landscape_z(*support[:2]))-run.plan['settings']['surface_clearance_cm']) <= 10.
            proposal.update(kind='continuous_native_boundary_fan', gap=target)
            _append_fan(surface,proposal,bounded); refresh_surface(surface)
            _clear_fan_obstructions(proposal,surfaces,bounded)
            repairs.append(proposal)
        else:
            raise AssertionError('Native source seam failed to close within16 bounded append operations')
    remaining, proof = continuous_gaps(run.plan,rows,surfaces,bounded,protected)
    assert not remaining, 'Continuous native source intervals remain uncovered: '+json.dumps(remaining[:4])
    return dict(proof, repairs=repairs, initial_gaps=initial, repair_count=len(repairs),
                consolidated_native_join_count=len(join_ids), original_source_controls_unchanged=True,
                actual_face_normal_cutoff=.25, assets_bound=False)


def verify_before_bind(context, surfaces, bounded):
    """Actual converted triangles, unchanged physical gates, before rebinding."""
    import geocity_roadbld_grounding as g
    plan, rows, sample = context['plan'], context['rows'], context['landscape_z']
    gaps, report = continuous_gaps(plan, rows, surfaces, bounded, protected=True)
    assert not gaps, 'Converted native assets have uncovered exterior intervals: '+json.dumps(gaps[:4])
    fields = [(s,g.AsphaltField(s['points_cm'],s['triangles'],s['material_ids'],s['upward'])) for s in surfaces]
    partition = g.analyze_protected_source_intervals(plan, rows, bounded)
    by_piece = {v['piece_id']:v for v in partition['source_roads']}
    rings = [[[v[0]*100.,v[1]*100.] for v in pad['ring_xz_m']] for pad in plan['protected_building_footprints_xz_m']]
    checked, omitted, maximum = 0, 0, 0.
    clearance = plan['settings']['surface_clearance_cm']
    for row in rows:
        candidates = [(s,f) for s,f in fields if row['road_actor_path'] in s['source_road_paths']]
        probes = list(g._samples(row,clearance,100.))
        points = [[v[0]*100.,v[2]*100.,v[1]*100.+clearance] for v in row['points_m']]
        for segment in by_piece[row['piece_id']]['segments']:
            n = segment['segment_index']; a,b = points[n:n+2]; length = math.dist(a[:2],b[:2])
            for lo,hi in segment['excluded_union']:
                for t in (lo,hi,max(0.,lo-.02/length),min(1.,hi+.02/length)):
                    probes.append(([a[k]+t*(b[k]-a[k]) for k in range(3)],n,t))
        for number,(point,segment,fraction) in enumerate(probes):
            if number % 64 == 0:
                bounded()
            if any(g._ring_location(point,ring)=='interior' for ring in rings):
                omitted += 1
                continue
            hits = [f.covered(point) for s,f in candidates if g._source_eligibility(s,row['road_actor_path'],point) is not None]
            hits = [v for v in hits if v is not None]
            assert hits, 'Converted candidate lacks actual exterior/boundary asphalt'
            z = max(v[0] for v in hits); expected = float(sample(*point[:2]))+clearance
            assert math.isfinite(expected) and abs(z-expected) <= 10., 'Converted asphalt exceeds unchanged10cm height tolerance'
            if fraction in (0.,1.):
                assert abs(z-point[2]) <= 10., 'Converted source control height differs'
            checked += 1; maximum = max(maximum,abs(z-expected))
    return dict(report, physical_probe_count=checked, protected_interior_probe_count=omitted,
                max_height_error_cm=maximum, xy_tolerance_cm=.01, height_tolerance_cm=10.,
                protected_excluded_length_cm=partition['excluded_length_cm'], actual_normals_verified=True,
                source_coverage_accounted=True, physical_surface_continuous=not partition['source_conflicts'])


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
    # Only the new face receives normals; recomputing the entire mesh would
    # alter existing split normals outside this measured repair.
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
