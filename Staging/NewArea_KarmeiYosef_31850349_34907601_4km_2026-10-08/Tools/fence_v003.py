"""In-editor (Karmei Yosef operator, own editor on the 4 km PCG clone), 2026-10-09. Paz Farm fence v003 (Aviv: the fence must
wrap around the road leading to the barn and go around the farm; two gates = his yellow marks; plus the defects found:
flat panels stair-stepping on slopes, gaps under the rail, rails not meeting, wire reading as a pale wall at distance).
Route: Staging/PazFarm_2026-10-08/Georef/FENCE_ROUTE_V003.json (metres from the pin). Reversible: the before-state of the fence
HISMs, posts and gate is written once to receipts/PAZFARM_FENCE_V003_BEFORE.json; 'revert' restores it.
steps (ARGS.step):
  probe   read-only: road-surface hits along the route (GeoCity road mesh), inward shift needed per edge, terrain slopes, mesh bounds.
  place   v003 meshes (copies of fence panel + gate with Nanite off, in <clone>/PazFarm/v003/Meshes), route edges shifted inward
          where they would stand on a road (ARGS.edge_shift_m {edge: metres}), panels chained end to end and pitched to the
          terrain, posts at every run end and corner, gate 1 moved, gate 2 spawned. No save.
  trim    remove strawberry-bed instances left outside the new fence (ARGS.beds_en [[e, n], ...] = bed start points);
          removed transforms go to receipts/PAZFARM_FENCE_V003_TRIMMED.json. No save.
  revert  restore the before-state (and re-add trimmed beds). No save.
  save    named saves: dirty content under <clone>/PazFarm/ only, then the clone map.
ARGS: expected_pid, step [, edge_shift_m].
"""
import datetime, hashlib, json, math, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
GEO = ROOT / 'Staging/PazFarm_2026-10-08/Georef'
TRIAL = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial'
CLONE = TRIAL + '/L_KarmeiYosef_31850349_34907601_4km_PCGTrial'
V1, V3 = TRIAL + '/PazFarm', TRIAL + '/PazFarm/v003'
BEFORE = TASK / 'receipts' / 'PAZFARM_FENCE_V003_BEFORE.json'
PANEL, POST, GATE, CORNER = 'SM_PazFarm_Fence_Mesh_3m', 'SM_PazFarm_Fence_Post', 'SM_PazFarm_Gate_Double_6m', 'SM_PazFarm_Fence_Corner'
EAL = u.EditorAssetLibrary
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == CLONE
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
all_actors = eas.get_all_level_actors()
actors = {a.get_actor_label(): a for a in all_actors if a.get_actor_label().startswith('PazFarm_')}
roads = [a for a in all_actors if a.get_actor_label().endswith(('_road_surfaces', '_sidewalks'))]
step = ARGS['step']
pe, pn = json.loads((GEO / 'roads.json').read_text())['pin_local_m_from_area_centre']
XY = lambda e, n: ((pe + e) * 100.0, -(pn + n) * 100.0)          # metres from pin -> Unreal cm (X east, Y south)
EN = lambda x, y: (x / 100.0 - pe, -y / 100.0 - pn)
R = json.loads((GEO / 'FENCE_ROUTE_V003.json').read_text())
V = [complex(e, n) for e, n in R['vertices_m']]
area2 = sum((V[i].real * V[(i + 1) % len(V)].imag - V[(i + 1) % len(V)].real * V[i].imag) for i in range(len(V)))
INWARD = 1j if area2 > 0 else -1j                                # CCW: interior on the left of travel
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
mesh_path = lambda m: m.get_path_name().split('.')[0] if m else None
not_land = [a for a in all_actors if not isinstance(a, (u.Landscape, u.LandscapeProxy))]
not_road = [a for a in all_actors if a not in roads]


def trace(z, ignore, complex_=False):
    x, y = XY(z.real, z.imag)
    hit = u.SystemLibrary.line_trace_single(world, u.Vector(x, y, 60000.0), u.Vector(x, y, -20000.0),
                                            u.TraceTypeQuery.TRACE_TYPE_QUERY1, complex_, ignore, u.DrawDebugTrace.NONE, True)
    h = hit[1] if isinstance(hit, tuple) else hit
    t = h.to_tuple() if h is not None else None
    return t[4].z if t and t[0] else None


ground = lambda z: trace(z, not_land)
on_road = lambda z: trace(z, not_road, True) is not None


def shifted_route(shift):
    """Offset each edge inward by shift[i] metres and re-intersect neighbours (straight-line joins)."""
    n = len(V)
    lines = []
    for i in range(n):
        p0, p1 = V[i], V[(i + 1) % n]; d = (p1 - p0) / abs(p1 - p0); s = INWARD * d * shift.get(i, 0.0)
        lines.append((p0 + s, d))
    out = []
    for i in range(n):
        (a, da), (b, db) = lines[i - 1], lines[i]
        den = (da.conjugate() * db).imag
        if abs(den) < 1e-6:
            out.append(b)
        else:
            t = ((b - a).conjugate() * db).imag / den
            out.append(a + da * t)
    return out


if step == 'probe':
    assert roads, 'no road surface actor'
    edges = []
    for i in range(len(V)):
        p0, p1 = V[i], V[(i + 1) % len(V)]; L = abs(p1 - p0); d = (p1 - p0) / L
        hits, need, zs = 0, 0.0, []
        k = 0.0
        while k <= L + 1e-6:
            z = p0 + d * k
            zs.append(ground(z))
            if on_road(z):
                hits += 1
                m = 0.0
                while m < 20.0 and (on_road(z + INWARD * d * m) or on_road(z + INWARD * d * (m + 0.6))):
                    m += 0.25
                need = max(need, m + 0.6)
            k += 0.5
        zz = [v for v in zs if v is not None]
        slopes = [abs(zz[j + 6] - zz[j]) / 300.0 for j in range(0, len(zz) - 6)]
        edges.append({'edge': i, 'length_m': round(L, 2), 'samples': len(zs), 'road_hits': hits, 'inward_shift_needed_m': round(need, 2),
                      'z_min_max_cm': [round(min(zz)), round(max(zz))] if zz else None,
                      'max_slope_per_3m_pct': round(100 * max(slopes), 1) if slopes else None})
    b = {}
    for n_ in (PANEL, POST, GATE, CORNER):
        m = u.load_asset(V1 + '/Meshes/' + n_)
        bb = m.get_bounding_box() if m else None
        b[n_] = [[round(bb.min.x, 1), round(bb.min.y, 1), round(bb.min.z, 1)], [round(bb.max.x, 1), round(bb.max.y, 1), round(bb.max.z, 1)]] if m else None
    sanity = []
    for r in json.loads((GEO / 'roads.json').read_text())['roads']:
        pts = r['pts_m_from_pin']
        hit = sum(on_road(complex(*pts[k])) for k in range(0, len(pts), max(1, len(pts) // 8)))
        sanity.append(['%s %s' % (r.get('id'), r.get('highway')), hit, len(range(0, len(pts), max(1, len(pts) // 8)))])
    RESULT = {'ok': True, 'road_sanity_hits_on_osm_centrelines': sanity, 'road_actors': [a.get_actor_label() for a in roads], 'orientation': 'CCW' if area2 > 0 else 'CW',
              'edges': edges, 'bounds': b, 'dirty': dirty()}

elif step == 'trim':
    TRIM = TASK / 'receipts' / 'PAZFARM_FENCE_V003_TRIMMED.json'
    det = actors['PazFarm_Detail']
    beds = [c for c in det.get_components_by_class(u.HierarchicalInstancedStaticMeshComponent)
            if c.get_editor_property('static_mesh').get_name() == 'SM_PazFarm_StrawberryBed_4m'][0]
    removed = json.loads(TRIM.read_text()) if TRIM.exists() else []
    n0 = beds.get_instance_count()
    for e, n in ARGS['beds_en']:
        x, y = XY(e, n)
        best = min(range(beds.get_instance_count()), key=lambda i: (beds.get_instance_transform(i, True).translation.x - x) ** 2 +
                   (beds.get_instance_transform(i, True).translation.y - y) ** 2)
        t = beds.get_instance_transform(best, True); l, r, sc = t.translation, t.rotation.rotator(), t.scale3d
        dist = math.hypot(l.x - x, l.y - y)
        assert dist < 50.0, ('no bed within 0.5 m of', e, n, dist)
        removed.append({'en': [e, n], 'loc': [l.x, l.y, l.z], 'rot': [r.roll, r.pitch, r.yaw], 'scale': [sc.x, sc.y, sc.z]})
        det.modify(); beds.modify(); beds.remove_instance(best)
    TRIM.write_text(json.dumps(removed, indent=1), encoding='utf-8')
    RESULT = {'ok': True, 'beds_before': n0, 'beds_after': beds.get_instance_count(), 'removed': removed, 'dirty': dirty()}

elif step in ('place', 'revert'):
    det = actors['PazFarm_Detail']
    hisms = {mesh_path(c.get_editor_property('static_mesh')).rsplit('/', 1)[1]: c
             for c in det.get_components_by_class(u.HierarchicalInstancedStaticMeshComponent)}
    gate = actors['PazFarm_Gate']

    def xf(t):
        l, r, s = t.translation, t.rotation.rotator(), t.scale3d
        return {'loc': [l.x, l.y, l.z], 'rot': [r.roll, r.pitch, r.yaw], 'scale': [s.x, s.y, s.z]}

    def mk(d):
        return u.Transform(location=u.Vector(*d['loc']), rotation=u.Rotator(roll=d['rot'][0], pitch=d['rot'][1], yaw=d['rot'][2]), scale=u.Vector(*d['scale']))

    if step == 'place' and not BEFORE.exists():
        gl, gr = gate.get_actor_location(), gate.get_actor_rotation()
        snap = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid,
                'gate': {'mesh': mesh_path(gate.static_mesh_component.get_editor_property('static_mesh')), 'loc': [gl.x, gl.y, gl.z],
                         'rot': [gr.roll, gr.pitch, gr.yaw], 'scale': [gate.get_actor_scale3d().x, gate.get_actor_scale3d().y, gate.get_actor_scale3d().z]}}
        for name in (PANEL, POST):
            c = hisms[name]
            snap[name] = {'mesh': mesh_path(c.get_editor_property('static_mesh')),
                          'instances': [xf(c.get_instance_transform(i, True)) for i in range(c.get_instance_count())]}
        BEFORE.write_text(json.dumps(snap), encoding='utf-8')
    before = json.loads(BEFORE.read_text())
    sds = u.get_engine_subsystem(u.SubobjectDataSubsystem)

    def comp_for(mesh_obj):
        name = mesh_obj.get_name()
        if name in hisms:
            return hisms[name]
        root = sds.k2_gather_subobject_data_for_instance(det)[0]
        handle, _ = sds.add_new_subobject(u.AddNewSubobjectParams(parent_handle=root, new_class=u.HierarchicalInstancedStaticMeshComponent))
        c = u.SubobjectDataBlueprintFunctionLibrary.get_object(u.SubobjectDataBlueprintFunctionLibrary.get_data(handle))
        c.set_static_mesh(mesh_obj); hisms[name] = c
        return c

    det.modify()
    if step == 'revert':
        for name in (PANEL, POST):
            c = hisms[name]; c.modify(); c.clear_instances()
            c.set_static_mesh(u.load_asset(before[name]['mesh']))
            c.add_instances([mk(d) for d in before[name]['instances']], False, True)
        if CORNER in hisms:
            hisms[CORNER].modify(); hisms[CORNER].clear_instances()
        g = before['gate']; gate.modify()
        gate.static_mesh_component.set_static_mesh(u.load_asset(g['mesh']))
        gate.set_actor_location_and_rotation(u.Vector(*g['loc']), u.Rotator(roll=g['rot'][0], pitch=g['rot'][1], yaw=g['rot'][2]), False, False)
        gate.set_actor_scale3d(u.Vector(*g['scale']))
        for a in all_actors:
            if a.get_actor_label() == 'PazFarm_Gate_2':
                eas.destroy_actor(a)
        TRIM = TASK / 'receipts' / 'PAZFARM_FENCE_V003_TRIMMED.json'
        if TRIM.exists():
            beds = [c for c in det.get_components_by_class(u.HierarchicalInstancedStaticMeshComponent)
                    if c.get_editor_property('static_mesh').get_name() == 'SM_PazFarm_StrawberryBed_4m'][0]
            beds.modify(); beds.add_instances([mk(d) for d in json.loads(TRIM.read_text())], False, True)
            TRIM.rename(TRIM.with_suffix('.restored.json'))
        RESULT = {'ok': True, 'reverted': True, 'dirty': dirty()}
    else:
        # v003 mesh copies, Nanite off (diamond wire geometry merges into a sheet under Nanite simplification)
        sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
        v3 = {}
        for name in (PANEL, GATE):
            path = V3 + '/Meshes/' + name
            m = u.load_asset(path) if EAL.does_asset_exist(path) else EAL.duplicate_asset(V1 + '/Meshes/' + name, path)
            s = m.get_editor_property('nanite_settings')
            if s.enabled:
                s.set_editor_property('enabled', False); sms.set_nanite_settings(m, s, True)
            v3[name] = m
        post_m, corner_m = u.load_asset(V1 + '/Meshes/' + POST), u.load_asset(V1 + '/Meshes/' + CORNER)
        shift = {int(k): float(v) for k, v in (ARGS.get('edge_shift_m') or {}).items()}
        W = shifted_route(shift)
        n = len(W)
        gates = R['gates']
        # gate spans in (edge, t0, t1) metres along the shifted edge
        spans = {}
        for g in gates:
            i = g['edge']; p0, p1 = W[i], W[(i + 1) % n]; L = abs(p1 - p0); d = (p1 - p0) / L
            if g.get('spans_edge'):
                t0, t1 = 0.0, L                                          # gate spans the whole short edge
            else:
                gc = complex(g['e'], g['n']); t = ((gc - p0) * d.conjugate()).real
                t0 = max(0.0, t - g['width_m'] / 2); t1 = min(L, t0 + g['width_m'])
            spans.setdefault(i, []).append((t0, t1, g))
        z_of = lambda z: ground(z)
        panels, posts, gate_xf, pitches = [], [], [], []
        SINK = 3.0                                                       # cm into the ground
        def run(i, a, b):
            p0, p1 = W[i], W[(i + 1) % n]; L = abs(p1 - p0); d = (p1 - p0) / L
            length = b - a
            if length < 0.4:
                return
            k = max(1, round(length / 3.0))
            step_m = length / k
            yaw = -math.degrees(math.atan2(d.imag, d.real))
            for j in range(k):
                s0, s1 = p0 + d * (a + j * step_m), p0 + d * (a + (j + 1) * step_m)
                z0, z1 = z_of(s0), z_of(s1)
                if z0 is None or z1 is None:
                    continue
                horiz = step_m * 100.0; dz = z1 - z0
                pitch = math.degrees(math.atan2(dz, horiz)); pitches.append(abs(pitch))
                x, y = XY(s0.real, s0.imag)
                panels.append(u.Transform(location=u.Vector(x, y, z0 - SINK), rotation=u.Rotator(roll=0.0, pitch=pitch, yaw=yaw),
                                          scale=u.Vector(math.hypot(horiz, dz) / 300.0, 1.0, 1.0)))
            # no separate end posts: every run ends at the next panel's start post or at a gate's own posts
        for i in range(n):
            L = abs(W[(i + 1) % n] - W[i]); cur = 0.0
            for t0, t1, g in sorted(spans.get(i, []), key=lambda s: s[0]):
                run(i, cur, t0)
                p0 = W[i]; d = (W[(i + 1) % n] - p0) / L; c = p0 + d * ((t0 + t1) / 2)
                ga, gb = z_of(p0 + d * t0), z_of(p0 + d * t1)
                x, y = XY(c.real, c.imag)
                gate_xf.append({'loc': [x, y, (ga + gb) / 2 - SINK], 'yaw': -math.degrees(math.atan2(d.imag, d.real)),
                                'pitch': math.degrees(math.atan2(gb - ga, (t1 - t0) * 100.0)), 'scale_x': (t1 - t0) / 6.0, 'yellow': g['px_centre']})
                cur = t1
            run(i, cur, L)
        # corners: plain posts already end every run; add a corner piece where the turn is close to 90 degrees
        corners = []
        for i in range(n):
            din = (W[i] - W[i - 1]) / abs(W[i] - W[i - 1]); dout = (W[(i + 1) % n] - W[i]) / abs(W[(i + 1) % n] - W[i])
            turn = abs(math.degrees(math.atan2((din.conjugate() * dout).imag, (din.conjugate() * dout).real)))
            if 70 <= turn <= 110:
                # stays along +X and +Y of the piece (Unreal Y = X turned +90 deg seen from above, i.e. clockwise in e/n)
                best = None
                for xa in (-din, dout):
                    ya = xa * -1j                                        # e/n vector for local +Y (clockwise from X)
                    other = dout if xa == -din else -din
                    err = abs(math.degrees(math.atan2((ya.conjugate() * other).imag, (ya.conjugate() * other).real)))
                    if best is None or err < best[0]:
                        best = (err, xa)
                if best[0] <= 25:
                    x, y = XY(W[i].real, W[i].imag); z = z_of(W[i])
                    corners.append(u.Transform(location=u.Vector(x, y, z - SINK), rotation=u.Rotator(roll=0.0, pitch=0.0, yaw=-math.degrees(math.atan2(best[1].imag, best[1].real))), scale=u.Vector(1, 1, 1)))
        cp, cpost = hisms[PANEL], hisms[POST]
        cp.modify(); cpost.modify()
        cp.clear_instances(); cp.set_static_mesh(v3[PANEL]); cp.add_instances(panels, False, True)
        cpost.clear_instances(); cpost.add_instances(posts, False, True)
        cc = comp_for(corner_m); cc.modify(); cc.clear_instances()
        if corners:
            cc.add_instances(corners, False, True)
        gate.modify()
        gate.static_mesh_component.set_static_mesh(v3[GATE])
        g0 = gate_xf[0]
        gate.set_actor_location_and_rotation(u.Vector(*g0['loc']), u.Rotator(roll=0.0, pitch=g0['pitch'], yaw=g0['yaw']), False, False)
        gate.set_actor_scale3d(u.Vector(g0['scale_x'], 1.0, 1.0))
        g2 = [a for a in eas.get_all_level_actors() if a.get_actor_label() == 'PazFarm_Gate_2']
        if len(gate_xf) > 1:
            g1 = gate_xf[1]
            a2 = g2[0] if g2 else eas.spawn_actor_from_object(v3[GATE], u.Vector(*g1['loc']), u.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
            a2.set_actor_label('PazFarm_Gate_2'); a2.set_folder_path('PazFarm'); a2.modify()
            a2.static_mesh_component.set_static_mesh(v3[GATE])
            a2.set_actor_location_and_rotation(u.Vector(*g1['loc']), u.Rotator(roll=0.0, pitch=g1['pitch'], yaw=g1['yaw']), False, False)
            a2.set_actor_scale3d(u.Vector(g1['scale_x'], 1.0, 1.0))
        rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'edge_shift_m': shift,
               'route_m': [[round(z.real, 3), round(z.imag, 3)] for z in W], 'panels': len(panels), 'posts': len(posts), 'corners': len(corners),
               'gates': gate_xf, 'max_pitch_deg': round(max(pitches), 2) if pitches else None,
               'panel_scale_range': [round(min(t.scale3d.x for t in panels), 3), round(max(t.scale3d.x for t in panels), 3)]}
        (TASK / 'receipts' / 'PAZFARM_FENCE_V003_PLACE.json').write_text(json.dumps(rec, indent=1), encoding='utf-8')
        RESULT = {'ok': True, **{k: v for k, v in rec.items() if k != 'route_m'}, 'dirty': dirty()}

elif step == 'save':
    d = dirty()
    assert d[0] in ([CLONE], []), d
    other = [p for p in d[1] if not p.startswith(V1 + '/')]
    assert not other, 'dirty outside the clone PazFarm folder: %s' % other
    pk = list(u.EditorLoadingAndSavingUtils.get_dirty_content_packages())
    if pk:
        assert u.EditorLoadingAndSavingUtils.save_packages(pk, False)
    assert u.EditorLoadingAndSavingUtils.save_map(world, CLONE)
    f = ROOT / ('Content' + CLONE[5:] + '.umap')
    rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'saved_content': d[1],
           'map_sha256': hashlib.sha256(f.read_bytes()).hexdigest(), 'map_bytes': f.stat().st_size, 'dirty_after': dirty()}
    (TASK / 'receipts' / 'PAZFARM_FENCE_V003_SAVE.json').write_text(json.dumps(rec, indent=1), encoding='utf-8')
    RESULT = {'ok': True, **rec}
