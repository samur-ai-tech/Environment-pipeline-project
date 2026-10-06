"""Bounded native SDK corner repair for the retained GeoCity RoadBLD provider.

Root is the sole editor caller. No Houdini/source edit, map save, rebuild or
native vendor asset modification occurs here. Native spawn/author/link APIs
retain source actor/piece identities; explicitly
derived connectors and bounded endpoint trims have a separate ledger.
"""
import hashlib
import json
import math
import re
import time
import copy
from pathlib import Path
from contextlib import contextmanager


def _base():
    import geocity_roadbld_workflow
    return geocity_roadbld_workflow


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def _xyz(value):
    return [float(value.x), float(value.y), float(value.z)]


def _distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _angle(a, start_a, b, start_b):
    e, n = (0, 1) if start_a else (-1, -2)
    f, m = (0, 1) if start_b else (-1, -2)
    u = [a[n][i] - a[e][i] for i in (0, 1)]
    v = [b[m][i] - b[f][i] for i in (0, 1)]
    norm = math.hypot(*u) * math.hypot(*v)
    assert norm > 1e-6, 'Degenerate native corner endpoint segment'
    return math.acos(max(-1.0, min(1.0, -(u[0] * v[0] + u[1] * v[1]) / norm)))


def _condition_end(points, mapping, protected, start, required_cm, trim_cm):
    """Remove only sampling points or genuine vertices inside the corner trim.

    A genuine OSM/boundary vertex outside the actual trim cannot be removed to
    manufacture the SDK's additional one metre post-trim segment margin.
    """
    ordered = list(range(len(points))) if start else list(reversed(range(len(points))))
    end = points[ordered[0]]
    removed = []
    selected = None
    for j in ordered[1:]:
        if _distance(points[j], end) > required_cm + 0.01:
            selected = j
            break
        if mapping[j] in protected:
            assert _distance(points[j], end) <= trim_cm + 0.1, 'A genuine OSM/boundary vertex outside the bounded corner trim prevents the SDK segment margin'
        removed.append(j)
    assert selected is not None, 'Native corner leaves insufficient source road length'
    removed_set = set(removed)
    return [p for i, p in enumerate(points) if i not in removed_set], [v for i, v in enumerate(mapping) if i not in removed_set], [mapping[i] for i in removed]


def _prepare_pair(a, mapping_a, protected_a, start_a, b, mapping_b, protected_b, start_b, radius_cm=100.0):
    original_a, original_b = [list(p) for p in a], [list(p) for p in b]
    a, b = [list(p) for p in a], [list(p) for p in b]
    mapping_a, mapping_b = list(mapping_a), list(mapping_b)
    removed_a, removed_b = [], []
    corner_gap = _distance(a[0 if start_a else -1], b[0 if start_b else -1])
    assert corner_gap <= 100.0, 'CloseCorner requires endpoint distance at most100cm'
    for attempt in range(8):
        angle = _angle(a, start_a, b, start_b)
        assert 0.01 < angle <= math.radians(150), 'Unsupported native corner turn'
        pull = radius_cm * math.tan(angle * 0.5)
        # The actual physical connector receives an independent SDK sample
        # check later; this preflight estimate must already fit the50cm limit.
        assert radius_cm * (1.0 - math.cos(angle * 0.5)) + corner_gap * 0.5 <= 50.0, 'Requested corner cannot fit the original geographic corridor'
        # A native rounded spline retains straight leads before its arc. Keep
        # endpoints separated beyond the SDK's100cm corner search tolerance.
        # The direct native authoring route needs no additional CloseCorner
        # segment margin; protected vertices outside the actual trim survive.
        trim = max(150.0, pull + 25.0)
        assert trim <= 200.0, 'Native connector requires an unreviewed endpoint trim'
        new_a, ids_a, gone_a = _condition_end(a, mapping_a, protected_a, start_a, trim, trim)
        new_b, ids_b, gone_b = _condition_end(b, mapping_b, protected_b, start_b, trim, trim)
        removed_a += gone_a
        removed_b += gone_b
        changed = ids_a != mapping_a or ids_b != mapping_b
        a, mapping_a, b, mapping_b = new_a, ids_a, new_b, ids_b
        if not changed:
            break
    else:
        raise AssertionError('Native corner sampling conditioning did not converge')
    angle = _angle(a, start_a, b, start_b)
    pull = radius_cm * math.tan(angle * 0.5)
    trim = max(150.0, pull + 25.0)
    assert trim <= 200.0
    endpoints = []
    for points, start in ((a, start_a), (b, start_b)):
        e, n = (0, 1) if start else (-1, -2)
        length = _distance(points[e], points[n])
        assert length > trim + 0.01, 'Native connector leaves insufficient source segment'
        endpoint = [points[e][i] + (points[n][i] - points[e][i]) * trim / length for i in range(3)]
        endpoints.append(endpoint)
    corner = [(a[0 if start_a else -1][i] + b[0 if start_b else -1][i]) * 0.5 for i in range(3)]
    assert _distance(*endpoints) > 100.1, 'Opposite native connector endpoints remain inside corner search tolerance'
    return {'conditioned_a': a, 'conditioned_b': b, 'mapping_a': mapping_a, 'mapping_b': mapping_b,
            'removed_a': sorted(set(removed_a)), 'removed_b': sorted(set(removed_b)),
            'expected_a': [endpoints[0] if i == (0 if start_a else len(a) - 1) else p for i, p in enumerate(a)],
            'expected_b': [endpoints[1] if i == (0 if start_b else len(b) - 1) else p for i, p in enumerate(b)],
            'connector_controls': [endpoints[0], corner, endpoints[1]], 'turn_angle_deg': math.degrees(angle),
            'turn_radius_cm': radius_cm, 'pullback_cm': trim, 'arc_tangent_pullback_cm': pull,
            'original_a': original_a, 'original_b': original_b,
            'endpoint_gap_cm': corner_gap}


def _snapshot(road):
    base = _base()
    info = base._tool('RoadBLDDiscoveryToolset', 'DescribeRoad', road)
    controls = list(base._get(info, 'ControlPoints'))
    lanes = list(base._get(info, 'LeftLanes')) + list(base._get(info, 'RightLanes'))
    return {'control_points_world_cm': [_xyz(base._get(p, 'Location')) for p in controls],
            'point_turn_radii_cm': [float(base._get(p, 'TurnRadius')) for p in controls],
            'width_start_cm': sum(float(base._get(v, 'WidthAtStart')) for v in lanes),
            'width_end_cm': sum(float(base._get(v, 'WidthAtEnd')) for v in lanes)}


def _controls_equal(actual, expected, tolerance_cm=0.1):
    assert len(actual) == len(expected), 'Native source/connector control count differs from explicit trim proof'
    assert all(math.dist(a, b) <= tolerance_cm for a, b in zip(actual, expected)), 'Native controls differ from the explicit bounded corner proof'


def _closed_policy(road, selected_radius_cm=100.0):
    base = _base()
    for field in ('bEnableLandscapeSplineMirroring', 'bConformToLandscape', 'bEnableLandscapePaint',
                  'bGenerateAbutments', 'bEnableRoadEdgeDetail'):
        assert not base._get(road, field), 'Native road enables excluded landscape/edge feature: ' + field
    assert not base._get(road, 'RoadPCGGraph'), 'Native road enables excluded PCG'
    assert float(base._get(base._get(road, 'ControlSpline'), 'TurnRadiusLimit').x) <= selected_radius_cm, 'Native instance no longer supports the selected bounded curve'


@contextmanager
def _scoped_radius_default(run, minimum_cm=100.0):
    base = _base()
    unreal = base.unreal
    run.guard()
    cdo = unreal.get_default_object(unreal.RoadControlSplineComponent)
    actor_template = base._get(unreal.get_default_object(unreal.DynamicRoad), 'ControlSpline')
    template_limit = base._get(actor_template, 'TurnRadiusLimit')
    template_before = (float(template_limit.x), float(template_limit.y))
    owned_limits = []
    for actor in run.roads + run.derived_junction_roads:
        component = base._get(actor, 'ControlSpline')
        value = base._get(component, 'TurnRadiusLimit')
        owned_limits.append((component, float(value.x), float(value.y)))
    limits = base._get(cdo, 'TurnRadiusLimit')
    before = (float(limits.x), float(limits.y))
    assert minimum_cm in (50.0, 100.0) and before[0] >= minimum_cm and before[1] >= minimum_cm
    try:
        # Installed CloseCorner cpp62 reads this CDO, and newly spawned native
        # connector components inherit it. No config/asset save is performed.
        # A component CDO has no actor owner. The installed plugin's editor
        # notification dereferences GetOwner(), so use the documented native
        # notification mode for this temporary default value only.
        cdo.set_editor_property('turn_radius_limit', unreal.Vector2D(minimum_cm, before[1]),
                                notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
        actor_template.set_editor_property('turn_radius_limit', unreal.Vector2D(minimum_cm, template_before[1]),
                                           notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
        yield before
    finally:
        cdo.set_editor_property('turn_radius_limit', unreal.Vector2D(*before),
                                notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
        actor_template.set_editor_property('turn_radius_limit', unreal.Vector2D(*template_before),
                                           notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
        # Native archetype restoration propagates to equal instance values.
        # Retain every explicitly configured owned component override.
        for component, x, y in owned_limits:
            component.set_editor_property('turn_radius_limit', unreal.Vector2D(x, y),
                                          notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
        restored = base._get(cdo, 'TurnRadiusLimit')
        assert (float(restored.x), float(restored.y)) == before, 'Temporary native spline CDO limit was not restored'
        restored_template = base._get(actor_template, 'TurnRadiusLimit')
        assert (float(restored_template.x), float(restored_template.y)) == template_before, 'Native actor template limit was not restored'


def _set_points(run, road, points, radii):
    base = _base()
    unreal = base.unreal
    run.guard()
    assert len(points) == len(radii) and len(points) >= 2
    typed = []
    for p, radius in zip(points, radii):
        point = unreal.RoadBLDPoint()
        base._set(point, 'Location', unreal.Vector(*p))
        base._set(point, 'TurnRadius', float(radius))
        typed.append(point)
    # Unlike CreateRoad, SetControlPoints takes ROAD-SURFACE Z directly, does
    # not add5cm, and preserves still-touching endpoint links (cpp1530-1631).
    # The operation coordinator owns scoped defaults, call-local log capture,
    # and before/after reconciliation. Do not hide an empty SDK edit result.
    return base._tool('RoadBLDAuthoringToolset', 'SetControlPoints', road, typed, 0.1, False, False, False)


def _identity_preset(run, road, row):
    base = _base()
    unreal = base.unreal
    original = base._get(road, 'SourceDrawPreset')
    source = base._path(original.get_class()).split('.')[0]
    assert source.startswith(run.plan['asset_root'] + '/'), 'Identity preset must duplicate an existing area-owned native preset'
    destination = run.plan['asset_root'] + '/IdentityPresets/RP_Identity_' + re.sub(r'[^A-Za-z0-9_]', '_', row['piece_id'])
    lib = unreal.EditorAssetLibrary
    asset = unreal.load_asset(destination)
    if asset:
        assert str(lib.get_metadata_tag(asset, 'GeoCityIdentitySourcePreset')) == source, 'Existing identity preset has another source'
    else:
        asset = lib.duplicate_asset(source, destination)
        assert asset, 'Equivalent area-owned identity preset copy failed'
        lib.set_metadata_tag(asset, 'GeoCityIdentitySourcePreset', source)
        lib.set_metadata_tag(asset, 'GeoCityOwner', base.OWNER)
        lib.set_metadata_tag(asset, 'GeoCityArea', run.area)
    cls = lib.load_blueprint_class(destination)
    copied = unreal.get_default_object(cls)
    # Complete Blueprint duplication carries all CDO fields. Independently
    # verify the normal closed preset policy before changing the actor ref.
    run.validate_preset(copied, run.plan['presets'][row['preset_key']])
    assert copied.get_class() != original.get_class(), 'CloseCorner would merge/delete same-class source roads'
    before = _snapshot(road)
    base._set(road, 'SourceDrawPreset', copied)
    assert base._get(road, 'SourceDrawPreset').get_class() == cls
    assert _snapshot(road) == before, 'Identity-only preset assignment changed native source controls/widths'
    run.owned_assets[base._path(asset.get_outermost())] = asset.get_outermost()
    return {'road_actor_path': base._path(road), 'source_preset': source, 'identity_preset': destination,
            'policy': 'complete equivalent area-owned Blueprint copy; distinct class prevents native source merge'}


def _preflight_native_corners(run, recovery=None):
    """Freeze all actual corner tasks and trim proofs before any native edit."""
    base = _base()
    unreal = base.unreal
    run.guard()
    issues = list(base._tool('RoadBLDDiscoveryToolset', 'FindJunctionIssues', run.network))
    assert len(issues) <= 12, 'Unreviewed number of native corner repairs'
    if recovery is None:
        import geocity_roadbld_topology as topology
        issues, automatic_junctions = topology.classify_native_junction_issues(run, issues, require_final_geometry=False)
    else:
        # The sole failed empty connector makes the network stale. Reuse the
        # preceding preflight only after the strict unchanged-source adoption
        # check; no geometry claim or automatic-junction bypass is added.
        automatic_junctions = copy.deepcopy(recovery.get('automatic_native_junctions', []))
        frozen = {p['issue_pair_key']: p for p in automatic_junctions}
        seen = set()
        remaining = []
        for issue in issues:
            pair = sorted([(str(base._get(base._get(issue, field), 'RefPath')), bool(base._get(issue, flag)))
                           for field, flag in (('Road', 'bStart'), ('OtherRoad', 'bOtherStart'))])
            key = _sha(pair)
            if key in frozen:
                proof = frozen[key]
                assert key not in seen and proof['issue_kind'] == str(base._get(issue, 'Kind'))
                assert proof['network_actor_path'] == base._path(run.network)
                assert proof['source_sha256'] == run.plan['source_sha256']
                assert proof['centreline_sha256'] == run.plan['centreline_sha256']
                geo = unreal.load_object(None, proof['junction_actor_path'])
                assert isinstance(geo, unreal.RoadGeo)
                assert sorted(base._path(r) for r in base._get(geo, 'SourceRoads')) == proof['junction_source_actor_paths']
                seen.add(key)
            else:
                remaining.append(issue)
        assert seen == set(frozen), 'Original automatic junction evidence no longer matches'
        issues = remaining
    sources = {base._path(road): (road, row) for road, row in zip(run.roads, run.plan['roads'])}
    assert len(sources) == run.plan['source_piece_count'], 'Original native source actor coverage differs'
    proofs = {}
    for path, (road, row) in sources.items():
        snap = _snapshot(road)
        expected = [[p[0] * 100.0, p[2] * 100.0, p[1] * 100.0 + run.plan['settings']['surface_clearance_cm']] for p in row['points_m']]
        _controls_equal(snap['control_points_world_cm'], expected)
        protected = sorted(set(row['original_point_indices'] + row['boundary_point_indices']))
        proofs[path] = {'source_osm_id': row['source_osm_id'], 'piece_id': row['piece_id'],
                        'original_control_points_world_cm': expected,
                        'expected_control_points_world_cm': [list(p) for p in expected],
                        'original_point_turn_radii_cm': snap['point_turn_radii_cm'],
                        'expected_point_turn_radii_cm': list(snap['point_turn_radii_cm']),
                        'retained_export_point_indices': list(range(len(expected))),
                        'original_source_vertex_export_indices': list(row['original_point_indices']),
                        'boundary_export_indices': list(row['boundary_point_indices']),
                        'protected_indices': protected, 'removed_generated_sample_export_indices': [],
                        'consumed_original_vertices_inside_trim': [], 'end_trims': [],
                        'width_start_cm': snap['width_start_cm'], 'width_end_cm': snap['width_end_cm']}
    tasks = []
    used = set()
    for issue in issues:
        kind = str(base._get(issue, 'Kind'))
        assert kind in ('UnjoinedCorner', 'SharpLinkedCorner'), 'Unsupported native junction issue: ' + kind
        pa = str(base._get(base._get(issue, 'Road'), 'RefPath'))
        pb = str(base._get(base._get(issue, 'OtherRoad'), 'RefPath'))
        assert pa in sources and pb in sources and pa != pb, 'Native corner references a foreign/derived source road'
        sa, sb = bool(base._get(issue, 'bStart')), bool(base._get(issue, 'bOtherStart'))
        assert (pa, sa) not in used and (pb, sb) not in used, 'Multiple corner connectors compete for one source endpoint'
        used.update(((pa, sa), (pb, sb)))
        qa, qb = proofs[pa], proofs[pb]
        pair_inputs = (qa['expected_control_points_world_cm'], qa['retained_export_point_indices'], set(qa['protected_indices']), sa,
                       qb['expected_control_points_world_cm'], qb['retained_export_point_indices'], set(qb['protected_indices']), sb)
        prepared = _prepare_pair(*pair_inputs, radius_cm=100.0)
        short_protected_leg = False
        for proof, start in ((qa, sa), (qb, sb)):
            endpoint = proof['expected_control_points_world_cm'][0 if start else -1]
            for index, source_index in enumerate(proof['retained_export_point_indices']):
                distance = _distance(endpoint, proof['expected_control_points_world_cm'][index])
                if (source_index in proof['protected_indices'] and
                        prepared['pullback_cm'] + 0.1 < distance <= prepared['arc_tangent_pullback_cm'] + 100.01):
                    short_protected_leg = True
        if short_protected_leg:
            # Retain the established short-leg radius policy across ordinary
            # replacements. This selects the curve radius only; conditioning
            # still preserves every genuine vertex outside the actual trim.
            prepared = _prepare_pair(*pair_inputs, radius_cm=50.0)
            prepared['radius_selection_reason'] = 'short protected endpoint leg outside actual trim'
        task = {'a': pa, 'b': pb, 'start_a': sa, 'start_b': sb, 'kind': kind, **prepared}
        tasks.append(task)
        for proof, start, suffix in ((qa, sa, 'a'), (qb, sb, 'b')):
            original_end = list(proof['expected_control_points_world_cm'][0 if start else -1])
            removed = prepared['removed_' + suffix]
            for index in removed:
                if index in proof['protected_indices']:
                    assert _distance(proof['original_control_points_world_cm'][index], original_end) <= prepared['pullback_cm'] + 0.1
                    proof['consumed_original_vertices_inside_trim'].append(index)
                else:
                    proof['removed_generated_sample_export_indices'].append(index)
            proof['expected_control_points_world_cm'] = prepared['expected_' + suffix]
            proof['retained_export_point_indices'] = prepared['mapping_' + suffix]
            proof['expected_point_turn_radii_cm'] = [proof['original_point_turn_radii_cm'][i] for i in prepared['mapping_' + suffix]]
            trim = {'start': start, 'source_endpoint_world_cm': original_end,
                    'native_endpoint_world_cm': prepared['connector_controls'][0 if suffix == 'a' else 2],
                    'pullback_cm': prepared['pullback_cm'], 'turn_radius_cm': prepared['turn_radius_cm'],
                    'removed_export_indices': removed, 'partner_actor_path': pb if suffix == 'a' else pa}
            proof['end_trims'].append(trim)
            task['native_trim_' + suffix] = trim
    for proof in proofs.values():
        proof['expected_controls_sha256'] = _sha(proof['expected_control_points_world_cm'])
    report = {'schema': 'environmentpipeline.roadbld_junction_repair.v1', 'phase': 'preflight_passed',
              'source_piece_count': len(sources), 'planned_corner_count': len(tasks),
              'sourcecontrols_trimproof': proofs, 'derived_junction_roads': [], 'identity_presets': [],
              'automatic_native_junctions': automatic_junctions,
              'original_source_actor_paths': sorted(sources), 'global_cdo_limit_restored': False,
              'rebuild_performed': False, 'saved': False,
              'planned_tasks': tasks, 'planned_tasks_sha256': _sha(tasks),
              'task_index': 0, 'step_index': 0, 'completed_corner_count': 0}
    if recovery is not None:
        assert report['planned_corner_count'] == recovery['planned_corner_count']
        assert _sha(proofs) == _sha(recovery['sourcecontrols_trimproof']), 'Legacy recovery changed the exact preflight trim proof'
    return report


_PENDING_LICENSE = 'RoadBLDToolset: The RoadBLD license check is still running. Retry in a few seconds.'
_POLICY_FIELDS = ('bEnableLandscapeSplineMirroring', 'bConformToLandscape', 'bEnableLandscapePaint',
                  'bGenerateAbutments', 'bEnableRoadEdgeDetail', 'RoadPCGGraph', 'RoadCrownHeight', 'RoadThickness')
_STEPS = ('spawn', 'connector_controls', 'parent_a', 'parent_b', 'link_a', 'link_b', 'record')


def _defaults():
    base = _base()
    cdo = base.unreal.get_default_object(base.unreal.RoadControlSplineComponent)
    template = base._get(base.unreal.get_default_object(base.unreal.DynamicRoad), 'ControlSpline')
    return [[float(v.x), float(v.y)] for v in (base._get(cdo, 'TurnRadiusLimit'), base._get(template, 'TurnRadiusLimit'))]


def _owned_state(run):
    """Read every participant, reciprocal link and native build state, no edits."""
    base = _base()
    run.guard()
    actors = run.roads + run.derived_junction_roads
    paths = [base._path(r) for r in actors]
    # RoadsInNetwork is native internal state, not an editor-readable property.
    # MakeNetworkInfo enumerates it in order; request one extra summary so a
    # foreign member cannot disappear behind the MaxRoads cap.
    infos = list(base._tool('RoadBLDDiscoveryToolset', 'DescribeNetwork', run.network, len(paths) + 1))
    assert len(infos) == 1
    info = infos[0]
    assert str(base._get(base._get(info, 'Actor'), 'RefPath')) == base._path(run.network)
    assert int(base._get(info, 'RoadCount')) == len(paths)
    network_paths = [str(base._get(base._get(row, 'Actor'), 'RefPath')) for row in base._get(info, 'Roads')]
    assert len(paths) == len(set(paths)) and network_paths == paths, 'Native network membership/order changed'
    assert not base._get(info, 'bRebuildInProgress'), 'Cannot condition while a native rebuild runs'
    required = set(run.tags())
    assert required.issubset(str(v) for v in base._get(run.network, 'Tags'))
    state = {'network': base._path(run.network), 'network_roads': network_paths,
             'network_tags': sorted(str(v) for v in base._get(run.network, 'Tags')),
             'stale': bool(base._get(info, 'bStale')), 'rebuilding': False,
             'job_id': str(run.job_id), 'rebuild_pass': run.rebuild_pass,
             'defaults': _defaults(), 'roads': {}}
    for road in actors:
        path = base._path(road)
        tags = sorted(str(v) for v in base._get(road, 'Tags'))
        assert required.issubset(tags), 'Foreign native road ownership'
        info = base._tool('RoadBLDDiscoveryToolset', 'DescribeRoad', road)
        assert str(base._get(base._get(info, 'Network'), 'RefPath')) == state['network']
        controls = list(base._get(info, 'ControlPoints'))
        lanes = list(base._get(info, 'LeftLanes')) + list(base._get(info, 'RightLanes'))
        limits = base._get(base._get(road, 'ControlSpline'), 'TurnRadiusLimit')
        preset = base._get(road, 'SourceDrawPreset')
        snap = {'control_points_world_cm': [_xyz(base._get(p, 'Location')) for p in controls],
                'point_turn_radii_cm': [float(base._get(p, 'TurnRadius')) for p in controls],
                'width_start_cm': sum(float(base._get(l, 'WidthAtStart')) for l in lanes),
                'width_end_cm': sum(float(base._get(l, 'WidthAtEnd')) for l in lanes),
                'preset': base._path(base._get(road, 'SourceDrawPreset')),
                'preset_class': str(base._get(info, 'PresetId')), 'tags': tags,
                'preset_policy': {f: base._plain(base._get(preset, f)) for f in
                    ('RoadMaterial', 'IntersectionMaterial', 'LeftSidewalkPresetClass', 'RightSidewalkPresetClass',
                     'RoadCrownHeight', 'bEnableLandscapePaint', 'bEnableRoadEdgeDetail', 'bGenerateAbutments', 'RoadPCGGraph')},
                'radius_limits': [float(limits.x), float(limits.y)],
                'policy': {f: base._plain(base._get(road, f)) for f in _POLICY_FIELDS}, 'links': {}}
        for end in ('Start', 'End'):
            snap['links'][end] = sorted([{'road': str(base._get(base._get(l, 'Road'), 'RefPath')),
                'start': bool(base._get(l, 'bLinkedToStart')), 'offset': float(base._get(l, 'RightAxisOffset'))}
                for l in base._get(base._get(info, end), 'Links')], key=lambda v: (v['road'], v['start'], v['offset']))
        state['roads'][path] = snap
    for path, snap in state['roads'].items():
        for end, links in snap['links'].items():
            for link in links:
                assert link['road'] in state['roads'], 'Link leaves the owned network'
                opposite = state['roads'][link['road']]['links']['Start' if link['start'] else 'End']
                assert any(v['road'] == path and v['start'] == (end == 'Start') for v in opposite), 'Nonreciprocal native endpoint link'
    for road, row in zip(run.roads, run.plan['roads']):
        preset = base._get(road, 'SourceDrawPreset')
        assert base._path(preset) == base._path(run.presets[row['preset_key']]), 'Original source preset changed'
        run.validate_preset(preset, run.plan['presets'][row['preset_key']])
        _closed_policy(road)
    return state


def _matches(actual, expected, new_link_endpoints=()):
    # Native spline conversion may round world positions/radii by <0.1cm.
    # Only the two NEW link offsets use the existing <=0.1cm verifier gate.
    # Native CreateReciprocalLink calculates +offset/-offset, including -0.0.
    # Existing links and all endpoint identities retain exact hash equality.
    check = copy.deepcopy(actual)
    if set(check['roads']) != set(expected['roads']):
        return False
    for path, snap in check['roads'].items():
        want = expected['roads'][path]
        try:
            _controls_equal(snap['control_points_world_cm'], want['control_points_world_cm'])
        except AssertionError:
            return False
        radii = snap['point_turn_radii_cm']
        if len(radii) != len(want['point_turn_radii_cm']) or any(abs(a-b) > 0.1 for a,b in zip(radii, want['point_turn_radii_cm'])):
            return False
        snap['control_points_world_cm'] = want['control_points_world_cm']
        snap['point_turn_radii_cm'] = want['point_turn_radii_cm']
    for path, end in new_link_endpoints:
        links = check['roads'][path]['links'][end]
        wanted = expected['roads'][path]['links'][end]
        if len(links) != 1 or len(wanted) != 1:
            return False
        link, target = links[0], wanted[0]
        if link['road'] != target['road'] or link['start'] != target['start']:
            return False
        offset = link['offset']
        if not math.isfinite(offset) or abs(offset) > 0.1 or target['offset'] != 0.0:
            return False
        other_end = 'Start' if link['start'] else 'End'
        if (link['road'], other_end) not in [tuple(v) for v in new_link_endpoints]:
            return False
        reciprocal = actual['roads'][link['road']]['links'][other_end]
        if (len(reciprocal) != 1 or reciprocal[0]['road'] != path or
                reciprocal[0]['start'] != (end == 'Start') or offset != -reciprocal[0]['offset']):
            return False
        link['offset'] = target['offset']
    return _sha(check) == _sha(expected)


def _expected_edit(before, task, step, connector_path, proofs):
    after = copy.deepcopy(before)
    after['stale'] = True  # FAuthoringAction::Complete marks its network stale.
    if step in ('connector_controls', 'parent_a', 'parent_b'):
        suffix = step[-1]
        path = connector_path if step == 'connector_controls' else task[suffix]
        points = task['connector_controls'] if step == 'connector_controls' else task['expected_' + suffix]
        radii = ([task['turn_radius_cm']] * 3 if step == 'connector_controls' else
                 [proofs[path]['original_point_turn_radii_cm'][i] for i in task['mapping_' + suffix]])
        snap = after['roads'][path]
        snap['control_points_world_cm'] = copy.deepcopy(points)
        snap['point_turn_radii_cm'] = list(radii)
        # Model the SDK's exact SetControlPoints reciprocal-link preservation.
        for end in ('Start', 'End'):
            keep = []
            for link in snap['links'][end]:
                partner = after['roads'][link['road']]
                partner_end = 'Start' if link['start'] else 'End'
                other_points = partner['control_points_world_cm']
                if _distance(points[0 if end == 'Start' else -1], other_points[0 if link['start'] else -1]) <= 0.1:
                    keep.append(link)
                else:
                    partner['links'][partner_end] = [v for v in partner['links'][partner_end]
                        if not (v['road'] == path and v['start'] == (end == 'Start'))]
            snap['links'][end] = keep
    else:
        suffix = step[-1]
        parent_path, parent_start = task[suffix], task['start_' + suffix]
        connector_start = suffix == 'a'
        for path, start, target, target_start in ((connector_path, connector_start, parent_path, parent_start),
                                                  (parent_path, parent_start, connector_path, connector_start)):
            links = after['roads'][path]['links']['Start' if start else 'End']
            assert not links, 'Refuse duplicate or competing ConnectEndpoints operation'
            links.append({'road': target, 'start': target_start, 'offset': 0.0})
    return after


def _call_with_log(run, callback):
    """Flush both boundaries; only this synchronous SDK call may prove denial."""
    flush = getattr(_base().unreal, 'log_flush', None)
    assert callable(flush), 'Installed Unreal log_flush API is required before native dispatch'
    # Drain older buffered warnings before taking the cursor. The installed
    # unreal_core adapter uses this same native API for its log-stream flush.
    flush()
    path = run.project / 'Saved' / 'Logs' / (run.project.name + '.log')
    with path.open('rb') as log:
        log.seek(0, 2)
        start = log.tell()
        anchor_start = max(0, start - 256)
        log.seek(anchor_start)
        anchor = log.read(start - anchor_start)
        result = callback()
        # UE may buffer RaiseScriptError output until after this Slate callback.
        # Flush before reading, without yielding or dispatching another SDK call.
        flush()
        log.seek(0, 2)
        end = log.tell()
        assert start <= end <= start + 65536, 'SDK log rotated/truncated or suffix exceeds bounded capture'
        log.seek(anchor_start)
        assert log.read(start - anchor_start) == anchor, 'SDK log prefix changed during operation'
        log.seek(start)
        data = log.read(end - start)
    suffix = data.decode('utf-8', errors='replace')
    messages = [line.split('LogScript: Warning: ', 1)[1].strip() for line in suffix.splitlines()
                if 'LogScript: Warning: RoadBLDToolset:' in line]
    pending = messages == [_PENDING_LICENSE]
    # Any other native error/warning prevents treating the call as this denial.
    native_lines = [line for line in suffix.splitlines() if 'RoadBLDToolset:' in line]
    diagnostics = [line for line in suffix.splitlines()
                   if re.search(r': (?:Warning|Error|Fatal):', line)]
    pending = (pending and len(native_lines) == 1 and diagnostics == native_lines
               and bool(data) and data.endswith(b'\n'))
    return result, {'path': str(path), 'start_byte': start, 'end_byte': end,
                    'suffix': suffix, 'sha256': hashlib.sha256(data).hexdigest(), 'exact_pending_license': pending,
                    'boundary_flush_api': 'unreal.log_flush', 'boundary_flush_count': 2}


def _legacy_empty_recovery(run, old):
    """One narrow adoption of the documented pre-checkpoint Shujaiya failure."""
    base = _base()
    assert run.area == 'GazaShujaiya' and run.revision == '20261003T172549017159'
    assert old['phase'] == 'failed_native_corner_repair' and not old.get('completed_corner_count', 0)
    assert old['error'] == "AssertionError('Native source conditioning did not succeed')"
    assert not old['derived_junction_roads'] and len(run.derived_junction_roads) == 1
    connector = run.derived_junction_roads[0]
    assert base._path(connector).endswith(':PersistentLevel.DynamicRoad_86')
    assert old['actual_derived_actor_paths'] == [base._path(connector)]
    assert base._path(run.network) == run.state['network_actor_path'] and base._path(run.network).endswith(':PersistentLevel.DynamicRoadNetwork_1')
    assert run.rebuild_pass == 1 and not old['saved'] and not old['rebuild_performed']
    before = _owned_state(run)
    assert sorted(base._path(r) for r in run.roads) == old['original_source_actor_paths']
    empty = before['roads'][base._path(connector)]
    assert empty['control_points_world_cm'] == [] and empty['point_turn_radii_cm'] == []
    assert empty['links'] == {'Start': [], 'End': []}
    _closed_policy(connector)
    for path, proof in old['sourcecontrols_trimproof'].items():
        snap = before['roads'][path]
        _controls_equal(snap['control_points_world_cm'], proof['original_control_points_world_cm'])
        assert snap['point_turn_radii_cm'] == proof['original_point_turn_radii_cm']
        assert abs(snap['width_start_cm'] - proof['width_start_cm']) <= 0.1
        assert abs(snap['width_end_cm'] - proof['width_end_cm']) <= 0.1
    # This OLD message proves only eligibility for the documented legacy
    # adoption. It never authorizes any future SDK retry.
    log_path = run.project / 'Saved/Logs/Environmentpipeline.log'
    marker = '[2026.10.03-17.26.04:819][707]LogScript: Warning: ' + _PENDING_LICENSE
    assert marker in log_path.read_text(encoding='utf-8', errors='replace').splitlines(), 'Original pending-license evidence missing'
    report = _preflight_native_corners(run, recovery=old)
    assert _sha(_owned_state(run)) == _sha(before), 'Recovery discovery changed original participants'
    first = report['planned_tasks'][0]
    assert empty['preset'] == before['roads'][first['a']]['preset'], 'Empty connector does not match original first task preset'
    assert abs(empty['radius_limits'][0] - first['turn_radius_cm']) <= 0.1
    report['legacy_failure_evidence'] = copy.deepcopy(old)
    report['legacy_failure_sha256'] = _sha(old)
    report['legacy_adoption'] = {'road_actor_path': base._path(connector), 'original_log_line': marker,
        'original_log_path': str(log_path), 'original_sources_unchanged': True,
        'first_task_sha256': _sha(first), 'before_sha256': _sha(before),
        'automatic_proofs_retained_pending_final_geometry': len(report['automatic_native_junctions'])}
    report.update(step_index=1, connector_actor_path=base._path(connector), checkpoint_state=before)
    return report


def _freeze_report(run, report):
    report['checkpoint_version'] = 1
    report['transaction_identity'] = {'token': run.transaction_token, 'revision': run.revision,
        'area': run.area, 'network': _base()._path(run.network), 'source_sha256': run.plan['source_sha256'],
        'centreline_sha256': run.plan['centreline_sha256']}
    report['sourcecontrols_trimproof_sha256'] = _sha(report['sourcecontrols_trimproof'])
    report['automatic_proofs_sha256'] = _sha(report['automatic_native_junctions'])
    report['checkpoint_state'] = report.get('checkpoint_state') or _owned_state(run)
    report['global_defaults_before'] = _defaults()
    report['global_cdo_limit_restored'] = True
    report['operations'] = []
    return report


def _finish_operation(run, report, operation, actual, reconciled=False):
    report['operations'].append({'task_index': report['task_index'], 'step': operation['step'],
        'before_sha256': _sha(operation['before']), 'expected_after_sha256': _sha(operation['expected_after']),
        'actual_after_sha256': _sha(actual), 'attempts': operation['attempts'],
        'started_monotonic': operation['started_monotonic'], 'deadline_monotonic': operation['deadline_monotonic'],
        'reconciled_without_replay': reconciled, 'calls': operation['calls']})
    report['checkpoint_state'] = actual
    report['step_index'] += 1
    report.pop('operation', None)
    report['phase'] = 'conditioning_native_corners'
    run.write()


def _edit_step(run, report, task, connector, step):
    base = _base()
    operation = report.get('operation')
    now = time.monotonic()
    if operation:
        assert operation['step'] == step and operation['task_index'] == report['task_index']
        assert now <= operation['deadline_monotonic'], 'Pending-license operation exceeded its original 60-second deadline'
        if now < operation.get('retry_at_monotonic', 0.0):
            return False
    actual = _owned_state(run)
    if operation is None:
        assert _sha(actual) == _sha(report['checkpoint_state']), 'Native participants changed between checkpoints'
        expected = _expected_edit(actual, task, step, base._path(connector), report['sourcecontrols_trimproof'])
        operation = {'step': step, 'task_index': report['task_index'], 'before': actual,
            'expected_after': expected, 'started_monotonic': now, 'deadline_monotonic': now + 60.0,
            'attempts': 0, 'calls': []}
        if step in ('link_a', 'link_b'):
            suffix = step[-1]
            operation['new_link_endpoints'] = [
                [base._path(connector), 'Start' if suffix == 'a' else 'End'],
                [task[suffix], 'Start' if task['start_' + suffix] else 'End']]
        report['operation'] = operation
        run.write()  # Exact intent survives a missed post-call checkpoint.
    elif _matches(actual, operation['expected_after'], operation.get('new_link_endpoints', ())):
        _finish_operation(run, report, operation, actual, reconciled=True)
        return True
    else:
        assert _sha(actual) == _sha(operation['before']), 'Ambiguous native partial edit; refuse replay'
    suffix = step[-1]
    if step in ('connector_controls', 'parent_a', 'parent_b'):
        road = connector if step == 'connector_controls' else base.unreal.load_object(None, task[suffix])
        want = operation['expected_after']['roads'][base._path(road)]
        callback = lambda: _set_points(run, road, want['control_points_world_cm'], want['point_turn_radii_cm'])
        radius = min(100.0, min(want['point_turn_radii_cm']))
    else:
        a, b = base.unreal.RoadBLDEndpointRef(), base.unreal.RoadBLDEndpointRef()
        base._set(a, 'Road', connector)
        base._set(a, 'bStart', suffix == 'a')
        base._set(b, 'Road', base.unreal.load_object(None, task[suffix]))
        base._set(b, 'bStart', task['start_' + suffix])
        callback = lambda: base._tool('RoadBLDAuthoringToolset', 'ConnectEndpoints', a, b,
            base.unreal.RoadBLDConnectMode.LINK, None, 0.1, task['turn_radius_cm'], False)
        radius = task['turn_radius_cm']
    operation['attempts'] += 1
    run.write()
    assert time.monotonic() <= operation['deadline_monotonic'], 'Native edit deadline expired before dispatch'
    with _scoped_radius_default(run, radius):
        result, capture = _call_with_log(run, callback)
    # Both defaults and all owned radius overrides are restored before even
    # checking whether to yield; no default/config save is ever performed.
    assert _defaults() == report['global_defaults_before']
    report['global_cdo_limit_restored'] = True
    after = _owned_state(run)
    result_network = str(base._get(base._get(result, 'Network'), 'RefPath'))
    capture['result_network'] = result_network
    operation['calls'].append(capture)
    if result_network == base._path(run.network):
        assert not capture['exact_pending_license'], 'Contradictory native result and license denial'
        assert _matches(after, operation['expected_after'], operation.get('new_link_endpoints', ())), 'Native edit differs from exact expected controls/links/policy'
        _finish_operation(run, report, operation, after)
        return True
    assert capture['exact_pending_license'], 'Native edit failed without fresh call-local pending-license evidence'
    # The license gate returns a default FRoadBLDEditResult before editing.
    # A different network, output road, job or warning is not that denial.
    assert (not result_network and not list(base._get(result, 'Roads'))
            and not str(base._get(result, 'RebuildJobId'))
            and not list(base._get(result, 'Warnings'))
            and bool(base._get(result, 'bNeedsRebuild'))), 'Pending-license result is not the installed default denial'
    assert _sha(after) == _sha(operation['before']), 'Pending-license rejection changed native participants'
    now = time.monotonic()
    assert now < operation['deadline_monotonic'], 'Pending-license operation timed out'
    operation['retry_at_monotonic'] = now + 1.0
    report['phase'] = 'waiting_native_license'
    run.write()
    return False


def _spawn_step(run, report, task):
    base = _base()
    before = _owned_state(run)
    assert _sha(before) == _sha(report['checkpoint_state']), 'Native participants changed before spawn'
    # Once dispatch is recorded, an unknown spawn outcome must never respawn.
    assert not report.get('spawn_dispatched'), 'Unreconciled connector spawn; refuse another actor'
    report['spawn_dispatched'] = True
    run.write()
    parent = base.unreal.load_object(None, task['a'])
    connector = run.network.add_road_to_road_network(base._get(parent, 'SourceDrawPreset'), 0.0)
    assert connector, 'Native connector spawn failed'
    run.derived_junction_roads.append(connector)
    report['connector_actor_path'] = base._path(connector)
    run.tag(connector)
    for field in _POLICY_FIELDS:
        base._set(connector, field, base._get(parent, field))
    limits = base._get(base._get(connector, 'ControlSpline'), 'TurnRadiusLimit')
    base._set(base._get(connector, 'ControlSpline'), 'TurnRadiusLimit', base.unreal.Vector2D(task['turn_radius_cm'], limits.y))
    _closed_policy(connector, task['turn_radius_cm'])
    after = _owned_state(run)
    empty = after['roads'][base._path(connector)]
    assert empty['control_points_world_cm'] == [] and empty['links'] == {'Start': [], 'End': []}
    assert empty['preset'] == before['roads'][task['a']]['preset']
    reduced = copy.deepcopy(after)
    reduced['roads'].pop(base._path(connector))
    reduced['network_roads'].remove(base._path(connector))
    reduced['stale'] = before['stale']
    assert _sha(reduced) == _sha(before), 'Connector spawn changed original participants'
    report['operations'].append({'task_index': report['task_index'], 'step': 'spawn',
        'road_actor_path': base._path(connector), 'before_sha256': _sha(before), 'after_sha256': _sha(after)})
    report.update(step_index=1, checkpoint_state=after)
    report.pop('spawn_dispatched')
    run.write()
    return connector


def _record_corner(run, report, task, connector):
    base = _base()
    actual = _owned_state(run)
    assert _sha(actual) == _sha(report['checkpoint_state']), 'Native participants changed before corner record'
    rows = {base._path(r): row for r, row in zip(run.roads, run.plan['roads'])}
    row_a, row_b = rows[task['a']], rows[task['b']]
    derived_id = 'junction:' + '+'.join(sorted((row_a['piece_id'], row_b['piece_id']))) + ':' + str(int(task['start_a'])) + '_' + str(int(task['start_b']))
    tags = set(str(v) for v in base._get(connector, 'Tags'))
    tags.update(('GeoCityDerivedJunction', 'GeoCityDerived_' + derived_id))
    base._set(connector, 'Tags', [base.unreal.Name(v) for v in sorted(tags)])
    connector.set_actor_label('GeoCity_' + run.area + '_' + re.sub(r'[^A-Za-z0-9_]', '_', derived_id))
    connector.set_folder_path('GeoCity/RoadBLD/' + run.area)
    # Legacy empty connector inherited preset defaults before the old failure.
    # Normalize only its closed policy to the original parent before recording.
    parent = base.unreal.load_object(None, task['a'])
    for field in _POLICY_FIELDS:
        base._set(connector, field, base._get(parent, field))
    snap = _snapshot(connector)
    _controls_equal(snap['control_points_world_cm'], task['connector_controls'])
    after = _owned_state(run)
    expected = copy.deepcopy(actual)
    expected['roads'][base._path(connector)]['tags'] = sorted(tags)
    expected['roads'][base._path(connector)]['policy'] = copy.deepcopy(actual['roads'][task['a']]['policy'])
    expected['stale'] = after['stale']  # Native property notifications may mark stale.
    assert _matches(after, expected), 'Corner metadata update changed native controls/links/preset'
    record = {'road_actor_path': base._path(connector), 'derived_id': derived_id,
        'parent_source_osm_ids': [row_a['source_osm_id'], row_b['source_osm_id']],
        'parent_piece_ids': [row_a['piece_id'], row_b['piece_id']],
        'parent_road_actor_paths': [task['a'], task['b']],
        'control_points_world_cm': snap['control_points_world_cm'],
        'control_points_sha256': _sha(snap['control_points_world_cm']),
        'point_turn_radii_cm': snap['point_turn_radii_cm'],
        'full_width_cm': snap['width_start_cm'], 'width_start_cm': snap['width_start_cm'], 'width_end_cm': snap['width_end_cm'],
        'turn_angle_deg': task['turn_angle_deg'], 'turn_radius_cm': task['turn_radius_cm'],
        'arc_tangent_pullback_cm': task['arc_tangent_pullback_cm'],
        'protected_clearance_radius_limit_cm': task.get('protected_clearance_radius_limit_cm'),
        'native_endpoint_trims': [task['native_trim_a'], task['native_trim_b']],
        'sourcecontrols_trimproof': [task['a'], task['b']]}
    assert not any(r['road_actor_path'] == record['road_actor_path'] for r in report['derived_junction_roads'])
    report['derived_junction_roads'].append(record)
    report['completed_corner_count'] = len(report['derived_junction_roads'])
    report['task_index'] += 1
    report['step_index'] = 0
    report.pop('connector_actor_path', None)
    report['checkpoint_state'] = after
    run.write()


def repair_native_corners(run):
    """Advance frozen native edit checkpoints; None means yield to Slate.

    No discovery is repeated once any parent/control/link edit has begun.
    A failed report is preserved, never silently restarted or respawned.
    """
    base = _base()
    run.guard()
    run.check_landscape_policy('junction_authoring')
    report = run.state.get('junction_repair_report')
    try:
        if report is None:
            assert not run.derived_junction_roads, 'Unrecorded derived actors prevent new preflight'
            report = _freeze_report(run, _preflight_native_corners(run))
            run.state['junction_repair_report'] = report
            run.write()
        elif 'checkpoint_version' not in report:
            report = _freeze_report(run, _legacy_empty_recovery(run, report))
            run.state['junction_repair_report'] = report
            run.write()
        assert report['checkpoint_version'] == 1
        assert report['transaction_identity'] == {'token': run.transaction_token, 'revision': run.revision,
            'area': run.area, 'network': base._path(run.network), 'source_sha256': run.plan['source_sha256'],
            'centreline_sha256': run.plan['centreline_sha256']}
        assert _sha(report['planned_tasks']) == report['planned_tasks_sha256'], 'Frozen corner tasks changed'
        assert _sha(report['sourcecontrols_trimproof']) == report['sourcecontrols_trimproof_sha256'], 'Frozen trim proof changed'
        assert _sha(report['automatic_native_junctions']) == report['automatic_proofs_sha256']
        assert report['phase'] != 'failed_native_corner_repair', 'Failed checkpoint requires explicit reconciliation'
        assert _defaults() == report['global_defaults_before']
        if report['phase'] == 'native_corners_authored_pending_rebuild':
            return report
        tasks = report['planned_tasks']
        while report['task_index'] < len(tasks):
            task = tasks[report['task_index']]
            step = _STEPS[report['step_index']]
            if step == 'spawn':
                connector = _spawn_step(run, report, task)
            else:
                connector = base.unreal.load_object(None, report['connector_actor_path'])
                assert connector in run.derived_junction_roads, 'Current connector object/ledger missing'
                if step == 'record':
                    _record_corner(run, report, task, connector)
                elif not _edit_step(run, report, task, connector, step):
                    return None
        for road, row in zip(run.roads, run.plan['roads']):
            verify_source_road(run, road, row, report)
        verify_derived_roads(run, report)
        assert _defaults() == report['global_defaults_before']
        report.update(phase='native_corners_authored_pending_rebuild', global_cdo_limit_restored=True,
            derived_road_count=len(report['derived_junction_roads']),
            total_native_road_count=len(run.roads) + len(report['derived_junction_roads']))
        # Completed operation records retain compact hashes and call evidence;
        # the full final checkpoint still guards the transition to pass2.
        run.write()
        return report
    except Exception as exc:
        if report is not None and report is run.state.get('junction_repair_report'):
            if 'checkpoint_version' not in report:
                # Keep the legacy report byte-for-byte as evidence even when
                # adoption validation fails before its new report is installed.
                run.state['junction_recovery_error'] = repr(exc)
            else:
                report.update(phase='failed_native_corner_repair', error=repr(exc),
                    actual_global_defaults_after=_defaults(),
                    actual_derived_actor_paths=[base._path(r) for r in run.derived_junction_roads])
            run.write()
        raise


def verify_source_road(run, road, row, report):
    """Validate the exact native trim proof instead of relaxing source controls."""
    base = _base()
    run.guard()
    proof = report['sourcecontrols_trimproof'][base._path(road)]
    assert proof['source_osm_id'] == row['source_osm_id'] and proof['piece_id'] == row['piece_id']
    original = [[p[0] * 100.0, p[2] * 100.0, p[1] * 100.0 + run.plan['settings']['surface_clearance_cm']] for p in row['points_m']]
    _controls_equal(proof['original_control_points_world_cm'], original)
    assert _sha(proof['expected_control_points_world_cm']) == proof['expected_controls_sha256']
    actual = _snapshot(road)
    _controls_equal(actual['control_points_world_cm'], proof['expected_control_points_world_cm'])
    assert len(actual['point_turn_radii_cm']) == len(proof['expected_point_turn_radii_cm'])
    assert all(abs(a - b) <= 0.1 for a, b in zip(actual['point_turn_radii_cm'], proof['expected_point_turn_radii_cm']))
    assert abs(actual['width_start_cm'] - row['width_m'] * 100.0) <= 0.1 and abs(actual['width_end_cm'] - row['width_m'] * 100.0) <= 0.1, 'Original source road width changed'
    mapping = proof['retained_export_point_indices']
    assert len(mapping) == len(actual['control_points_world_cm']) and mapping == sorted(set(mapping))
    consumed = set(proof['consumed_original_vertices_inside_trim'])
    for i in proof['protected_indices']:
        if i not in mapping:
            assert i in consumed and any(_distance(original[i], trim['source_endpoint_world_cm']) <= trim['pullback_cm'] + 0.1 for trim in proof['end_trims']), 'Genuine geographic vertex disappeared outside the explicit corner trim'
    changed_end_indices = {0 if trim['start'] else len(mapping) - 1 for trim in proof['end_trims']}
    for i, source_index in enumerate(mapping):
        if i not in changed_end_indices:
            assert math.dist(actual['control_points_world_cm'][i], original[source_index]) <= 0.1, 'Native corner changed an interior source vertex'
    _closed_policy(road)
    return actual


def verify_derived_roads(run, report):
    """Check explicit native connectors against parent corridors and policy.

    Called again after the final native rebuild. Root's mesh/material/clip
    validator covers generated RoadGeo actors including these connector IDs.
    """
    base = _base()
    run.guard()
    by_path = {base._path(v): v for v in run.derived_junction_roads}
    records = report['derived_junction_roads']
    assert set(by_path) == {r['road_actor_path'] for r in records}, 'Derived connector actor ledger differs'
    for record in records:
        road = by_path[record['road_actor_path']]
        snap = _snapshot(road)
        _controls_equal(snap['control_points_world_cm'], record['control_points_world_cm'])
        assert len(snap['point_turn_radii_cm']) == len(record['point_turn_radii_cm']) == len(snap['control_points_world_cm'])
        assert _sha(record['control_points_world_cm']) == record['control_points_sha256']
        assert all(abs(r - record['turn_radius_cm']) <= 0.1 for r in snap['point_turn_radii_cm']), 'Derived native connector turn radius changed'
        assert abs(snap['width_start_cm'] - record['width_start_cm']) <= 0.1 and abs(snap['width_end_cm'] - record['width_end_cm']) <= 0.1, 'Derived native connector width changed'
        _closed_policy(road, record['turn_radius_cm'])
        link_proof = []
        connector_info = base._tool('RoadBLDDiscoveryToolset', 'DescribeRoad', road)
        for i, (parent_path, trim) in enumerate(zip(record['parent_road_actor_paths'], record['native_endpoint_trims'])):
            connector_start = i == 0
            parent = base.unreal.load_object(None, parent_path)
            assert parent, 'Native connector parent is missing'
            parent_info = base._tool('RoadBLDDiscoveryToolset', 'DescribeRoad', parent)
            for info, start, target, target_start in ((connector_info, connector_start, parent_path, trim['start']),
                                                     (parent_info, trim['start'], record['road_actor_path'], connector_start)):
                links = list(base._get(base._get(info, 'Start' if start else 'End'), 'Links'))
                assert len(links) == 1, 'Native corner endpoint has missing or competing links'
                link = links[0]
                assert str(base._get(base._get(link, 'Road'), 'RefPath')) == target
                assert bool(base._get(link, 'bLinkedToStart')) == target_start
                assert abs(float(base._get(link, 'RightAxisOffset'))) <= 0.1
            link_proof.append({'connector_start': connector_start, 'parent_actor_path': parent_path,
                               'parent_start': trim['start'], 'reciprocal': True, 'right_axis_offset_cm': 0.0})
        record['endpoint_link_proof'] = link_proof
        parents = [report['sourcecontrols_trimproof'][path]['original_control_points_world_cm'] for path in record['parent_road_actor_paths']]
        samples = list(base._tool('RoadBLDDiscoveryToolset', 'SampleRoad', road, 25.0))
        assert samples, 'Derived native connector has no physical centerline'
        max_fit = max_ground = 0.0
        width_limits = [report['sourcecontrols_trimproof'][p]['width_start_cm'] for p in record['parent_road_actor_paths']]
        for sample in samples:
            location = _xyz(base._get(sample, 'Location'))
            fits = []
            for parent in parents:
                for a, b in zip(parent, parent[1:]):
                    dx, dy = b[0] - a[0], b[1] - a[1]
                    length = dx * dx + dy * dy
                    if length <= 1e-8:
                        continue
                    t = max(0.0, min(1.0, ((location[0] - a[0]) * dx + (location[1] - a[1]) * dy) / length))
                    fits.append((_distance(location, [a[0] + t * dx, a[1] + t * dy]), a[2] + t * (b[2] - a[2])))
            distance, height = min(fits, key=lambda v: v[0])
            max_fit, max_ground = max(max_fit, distance), max(max_ground, abs(location[2] - height))
            width = float(base._get(sample, 'LeftWidth')) + float(base._get(sample, 'RightWidth'))
            assert min(width_limits) - 0.1 <= width <= max(width_limits) + 0.1, 'Derived connector creates width outside both parent road widths'
        assert max_fit <= 50.0, 'Derived native connector leaves original geographic corridor'
        assert max_ground <= run.plan['settings']['ground_profile_tolerance_cm'], 'Derived connector does not follow the original final-ground road profile'
        record['max_physical_centerline_error_cm'] = max_fit
        record['max_ground_profile_error_cm'] = max_ground
    return records
