"""In-editor on the 4 km clone (Karmei Yosef operator, 2026-10-11). Aviv: strawberry rows at real spacing ("Real spacing")
and "the beds are not aligned to the ground - they need some adjustment to sit on the ground well".
The beds are the strawberry-bed HISM of actor PazFarm_Detail. Each 4 m tile used to sit flat (yaw only) at its start-point
height, so on slopes one end floated and the other sank (steps of 10-36 cm between neighbours).
steps
  probe     read-only: bed component(s), mesh bounds (which local axis the tile runs along), instance count, the old yaw vs
            the layout row direction, dirty packages
  relayout  ARGS.layout (file under Staging/PazFarm_2026-10-08/Georef, default STRAWBERRY_BEDS_V2.json): records every
            current bed transform to receipts/STRAW_BEDS_BEFORE_<utc>.json, clears the bed instances and adds one tile per
            layout entry, GROUND-FITTED: start end on the landscape, the tile's long axis pitched so the far end also sits
            on the landscape, rolled to the cross slope at mid-tile (+-0.5 m), then sunk ARGS.sink_cm (default 3).
            Landscape-only heights (multi trace). Reports the mid-tile float/sink. Map is NOT saved (clone_v2.py save).
  place_variants  Astra StrawberryBeds v005: ARGS.revision / variants / cap / caps / layout / sink_cm. Same ground fit + exact
            joins (tiny local-Y stretch), A/B/C mixed per row, end caps at both ends of each continuous run. Before-state
            receipt as relayout. No save (save_prefix for the dirtied MIs, then clone_v2.py save).
  revert    ARGS.before (receipt file name): restore the recorded mesh, overrides and transforms on the original component;
            any other strawberry components are emptied. No save.
ARGS: expected_pid, step, clone_suffix ('_v2'), ...
"""
import datetime, json, math, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
GEO = ROOT / 'Staging/PazFarm_2026-10-08/Georef'
TRIAL = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial'
CLONE = TRIAL + '/L_KarmeiYosef_31850349_34907601_4km_PCGTrial' + ARGS.get('clone_suffix', '')
BED_NAME = 'SM_PazFarm_StrawberryBed_4m'
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == CLONE, world.get_outermost().get_path_name()
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
pe, pn = json.loads((GEO / 'roads.json').read_text())['pin_local_m_from_area_centre']
XY = lambda e, n: ((pe + e) * 100.0, -(pn + n) * 100.0)
step = ARGS['step']
det = [a for a in eas.get_all_level_actors() if a.get_actor_label() == 'PazFarm_Detail']
assert len(det) == 1, len(det)
det = det[0]
beds = [c for c in det.get_components_by_class(u.InstancedStaticMeshComponent)       # 4 m tiles (any variant) + end caps
        if c.get_editor_property('static_mesh') and c.get_editor_property('static_mesh').get_name().startswith('SM_PazFarm_StrawberryBed')]
tiles = [c for c in beds if c.get_editor_property('static_mesh').get_name().startswith(BED_NAME)]
assert tiles, [c.get_name() for c in beds]
if step in ('probe', 'relayout', 'place_variants'):
    assert len(beds) == 1, ('one bed component expected before this step', [c.get_name() for c in beds])
comp = tiles[0]
mesh = comp.get_editor_property('static_mesh')
bb = mesh.get_bounding_box()
EXT = -1.0 if abs(bb.min.y) > abs(bb.max.y) else 1.0            # tile runs along local -Y (EXT -1) or +Y (EXT +1)
LEN = max(abs(bb.min.y), abs(bb.max.y))


def land_z(x, y):
    hits = u.SystemLibrary.line_trace_multi(world, u.Vector(x, y, 60000.0), u.Vector(x, y, -20000.0), u.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                            False, [], u.DrawDebugTrace.NONE, True)
    for h in (hits[1] if isinstance(hits, tuple) else hits) or []:
        t = h.to_tuple()
        if t[0] and isinstance(t[9], (u.Landscape, u.LandscapeProxy)):
            return t[4].z
    return None


def xf(t):
    q = t.rotation
    return [t.translation.x, t.translation.y, t.translation.z, q.x, q.y, q.z, q.w, t.scale3d.x, t.scale3d.y, t.scale3d.z]


if step == 'probe':
    old = [comp.get_instance_transform(i, True) for i in range(min(5, comp.get_instance_count()))]
    RESULT = {'ok': True, 'component': comp.get_name(), 'class': comp.get_class().get_name(), 'mesh': mesh.get_path_name(),
              'bounds_cm': [[bb.min.x, bb.min.y, bb.min.z], [bb.max.x, bb.max.y, bb.max.z]], 'runs_along': '+Y' if EXT > 0 else '-Y',
              'length_cm': LEN, 'instances': comp.get_instance_count(),
              'old_yaws': [round(t.rotation.rotator().yaw, 2) for t in old], 'dirty': dirty()}

elif step == 'relayout':
    assert dirty() == ([], []), dirty()
    lay = json.loads((GEO / ARGS.get('layout', 'STRAWBERRY_BEDS_V2.json')).read_text())
    sink = float(ARGS.get('sink_cm', 3.0))
    utc = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    before = {'utc': utc, 'pid': pid, 'map': CLONE, 'component': comp.get_name(), 'mesh': mesh.get_path_name(),
              'transforms': [xf(comp.get_instance_transform(i, True)) for i in range(comp.get_instance_count())]}
    bname = 'STRAW_BEDS_BEFORE_%s.json' % utc
    (TASK / 'receipts' / bname).write_text(json.dumps(before), encoding='utf-8')
    ts, floats, skipped, pitches, rolls = [], [], 0, [], []
    for b in lay['beds']:
        sx, sy = XY(b['e'], b['n'])
        yaw = 90.0 - b['row_deg']                                     # same convention as place_farm.py
        ya = math.radians(yaw)
        yh = (-math.sin(ya), math.cos(ya))                            # local +Y, horizontal
        xh = (math.cos(ya), math.sin(ya))                             # local +X, horizontal
        ex, ey = sx + EXT * LEN * yh[0], sy + EXT * LEN * yh[1]
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        zs, ze, zm = land_z(sx, sy), land_z(ex, ey), land_z(mx, my)
        zl, zr = land_z(mx - 50 * xh[0], my - 50 * xh[1]), land_z(mx + 50 * xh[0], my + 50 * xh[1])
        if None in (zs, ze, zm, zl, zr):
            skipped += 1; continue
        yv = u.Vector(EXT * (ex - sx), EXT * (ey - sy), EXT * (ze - zs))
        xv = u.Vector(xh[0] * 100.0, xh[1] * 100.0, zr - zl)
        rot = u.MathLibrary.make_rot_from_yx(yv, xv)
        ts.append(u.Transform(location=u.Vector(sx, sy, zs - sink), rotation=rot, scale=u.Vector(1, 1, 1)))
        floats.append(((zs + ze) / 2 - sink) - zm)                    # + = bed bottom above the ground at mid-tile
        pitches.append(math.degrees(math.atan2(ze - zs, LEN))); rolls.append(math.degrees(math.atan2(zr - zl, 100.0)))
    det.modify(); comp.modify()
    comp.clear_instances()
    comp.add_instances(ts, False, True)
    got = comp.get_instance_count()
    assert got == len(ts), (got, len(ts))
    fl = sorted(floats); q = lambda L, f: round(L[int(f * (len(L) - 1))], 1) if L else None
    ab = sorted(abs(v) for v in pitches); ar = sorted(abs(v) for v in rolls)
    rec = {'utc': utc, 'pid': pid, 'layout': ARGS.get('layout', 'STRAWBERRY_BEDS_V2.json'), 'before_receipt': bname,
           'old_count': len(before['transforms']), 'new_count': got, 'skipped_no_ground': skipped, 'sink_cm': sink,
           'tile': {'mesh': mesh.get_path_name(), 'runs_along': '+Y' if EXT > 0 else '-Y', 'length_cm': LEN},
           'mid_tile_float_cm': {'min': q(fl, 0), 'p05': q(fl, .05), 'median': q(fl, .5), 'p95': q(fl, .95), 'max': q(fl, 1)},
           'abs_pitch_deg': {'median': q(ab, .5), 'max': q(ab, 1)}, 'abs_roll_deg': {'median': q(ar, .5), 'max': q(ar, 1)},
           'dirty': dirty()}
    (TASK / 'receipts' / ('STRAW_BEDS_RELAYOUT_%s.json' % utc)).write_text(json.dumps(rec, indent=2), encoding='utf-8')
    RESULT = {'ok': True, **rec}

elif step == 'place_variants':
    # Astra StrawberryBeds v005 (Aviv's "one last fix"): 3 tile variants mixed along each row (never the same twice in a row),
    # the same ground fit as relayout plus a tiny local-Y stretch (3D length / 4 m, <0.5 %) so a pitched tile ends exactly on
    # the next tile's start, and the optional end cap closing both ends of every continuous run (row start: cap turned 180 deg
    # about the tile's up axis at the first pivot; row end: at the last tile's transformed far end, same orientation).
    # The existing bed component takes variant A; new Static HISM components (attached to the root) take B, C and the cap.
    assert dirty() == ([], []), dirty()
    MF = TRIAL + '/PazFarm/' + ARGS.get('revision', 'StrawberryBeds_v005') + '/Meshes/'
    variants = [u.load_asset(MF + n) for n in ARGS.get('variants', [BED_NAME + '_A', BED_NAME + '_B', BED_NAME + '_C'])]
    assert all(variants), ARGS.get('variants')
    cap = u.load_asset(MF + ARGS.get('cap', 'SM_PazFarm_StrawberryBedEnd')) if ARGS.get('caps', True) else None
    vb = variants[0].get_bounding_box()
    ext = -1.0 if abs(vb.min.y) > abs(vb.max.y) else 1.0
    ln = max(abs(vb.min.y), abs(vb.max.y))
    for m in variants:
        b2 = m.get_bounding_box(); assert abs(max(abs(b2.min.y), abs(b2.max.y)) - 400.0) < 1.0, (m.get_name(), b2.min.y, b2.max.y)
    sink = float(ARGS.get('sink_cm', 3.0))
    utc = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    before = {'utc': utc, 'pid': pid, 'map': CLONE, 'component': comp.get_name(), 'mesh': mesh.get_path_name(),
              'overrides': [m.get_path_name() if m else None for m in comp.get_editor_property('override_materials')],
              'transforms': [xf(comp.get_instance_transform(i, True)) for i in range(comp.get_instance_count())]}
    bname = 'STRAW_BEDS_BEFORE_%s.json' % utc
    (TASK / 'receipts' / bname).write_text(json.dumps(before), encoding='utf-8')
    lay = json.loads((GEO / ARGS.get('layout', 'STRAWBERRY_BEDS_V2.json')).read_text())

    def fit(b):
        sx, sy = XY(b['e'], b['n'])
        ya = math.radians(90.0 - b['row_deg'])                       # same yaw convention as place_farm.py / relayout
        yh = (-math.sin(ya), math.cos(ya)); xh = (math.cos(ya), math.sin(ya))
        ex, ey = sx + ext * ln * yh[0], sy + ext * ln * yh[1]
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        zs, ze = land_z(sx, sy), land_z(ex, ey)
        zl, zr = land_z(mx - 50 * xh[0], my - 50 * xh[1]), land_z(mx + 50 * xh[0], my + 50 * xh[1])
        if None in (zs, ze, zl, zr):
            return None
        rot = u.MathLibrary.make_rot_from_yx(u.Vector(ext * (ex - sx), ext * (ey - sy), ext * (ze - zs)), u.Vector(xh[0] * 100.0, xh[1] * 100.0, zr - zl))
        stretch = math.sqrt(ln * ln + (ze - zs) ** 2) / ln
        return u.Transform(location=u.Vector(sx, sy, zs - sink), rotation=rot, scale=u.Vector(1.0, stretch, 1.0))

    rows = []
    for b in lay['beds']:
        th = math.radians(b['row_deg'])
        rows.append((b['plot'], round(-b['e'] * math.sin(th) + b['n'] * math.cos(th), 2), b['e'] * math.cos(th) + b['n'] * math.sin(th), b))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    runs, run, prev, skipped = [], [], None, 0
    for plot, v, uu, b in rows:
        t = fit(b)
        if t is None:
            skipped += 1
            if run:
                runs.append(run)
            run, prev = [], None; continue
        if prev and prev[0] == (plot, v) and abs(uu - prev[1] - 4.0) < 0.05:
            run.append(t)
        else:
            if run:
                runs.append(run)
            run = [t]
        prev = ((plot, v), uu)
    if run:
        runs.append(run)
    per = [[] for _ in variants]; caps, seed, stretches = [], 12345, []
    for r in runs:
        last = -1
        for t in r:
            seed = (seed * 1103515245 + 12345) & 0x7fffffff
            k = seed % len(variants)
            if k == last:
                k = (k + 1 + (seed >> 8) % (len(variants) - 1)) % len(variants)
            per[k].append(t); last = k; stretches.append(t.scale3d.y)
        if cap:
            r0 = r[0].rotation.rotator()
            fwd, right = u.MathLibrary.get_forward_vector(r0), u.MathLibrary.get_right_vector(r0)
            caps.append(u.Transform(location=r[0].translation, scale=u.Vector(1, 1, 1),
                                    rotation=u.MathLibrary.make_rot_from_yx(u.Vector(-right.x, -right.y, -right.z), u.Vector(-fwd.x, -fwd.y, -fwd.z))))
            endp = u.MathLibrary.transform_location(r[-1], u.Vector(0.0, ext * ln, 0.0))
            caps.append(u.Transform(location=endp, rotation=r[-1].rotation.rotator(), scale=u.Vector(1, 1, 1)))
    sds = u.get_engine_subsystem(u.SubobjectDataSubsystem)
    top = sds.k2_gather_subobject_data_for_instance(det)[0]
    rootc = det.root_component
    det.modify(); comp.modify()

    def new_comp(m):
        hh, _ = sds.add_new_subobject(u.AddNewSubobjectParams(parent_handle=top, new_class=u.HierarchicalInstancedStaticMeshComponent))
        c = u.SubobjectDataBlueprintFunctionLibrary.get_object(u.SubobjectDataBlueprintFunctionLibrary.get_data(hh))
        c.set_mobility(u.ComponentMobility.STATIC)
        if c.get_attach_parent() is None:
            c.attach_to_component(rootc, '', u.AttachmentRule.KEEP_RELATIVE, u.AttachmentRule.KEEP_RELATIVE, u.AttachmentRule.KEEP_RELATIVE, False)
        c.set_static_mesh(m)
        return c
    comp.set_editor_property('override_materials', [])
    comp.set_static_mesh(variants[0]); comp.clear_instances(); comp.add_instances(per[0], False, True)
    made = {variants[0].get_name(): comp}
    for m, ts in zip(variants[1:], per[1:]):
        c = new_comp(m); c.add_instances(ts, False, True); made[m.get_name()] = c
    if cap:
        c = new_comp(cap); c.add_instances(caps, False, True); made[cap.get_name()] = c
    got = {k: c.get_instance_count() for k, c in made.items()}
    st = sorted(stretches)
    rec = {'utc': utc, 'pid': pid, 'revision': ARGS.get('revision', 'StrawberryBeds_v005'), 'before_receipt': bname,
           'old_mesh': mesh.get_path_name(), 'old_count': len(before['transforms']), 'instances': got,
           'tiles': sum(len(p) for p in per), 'runs': len(runs), 'caps': len(caps), 'skipped_no_ground': skipped, 'sink_cm': sink,
           'stretch': {'median': round(st[len(st) // 2], 5), 'max': round(st[-1], 5)},
           'components': {k: [c.get_name(), str(c.get_editor_property('mobility')).split('.')[-1].split(':')[0],
                              c.get_attach_parent().get_name() if c.get_attach_parent() else None] for k, c in made.items()},
           'dirty': dirty()}
    (TASK / 'receipts' / ('STRAW_BEDS_V005_PLACE_%s.json' % utc)).write_text(json.dumps(rec, indent=2), encoding='utf-8')
    RESULT = {'ok': True, **rec}

elif step == 'revert':
    # restores the recorded mesh, overrides and transforms on the original bed component; other strawberry components emptied
    before = json.loads((TASK / 'receipts' / ARGS['before']).read_text())
    ts = [u.Transform(location=u.Vector(*v[0:3]), rotation=u.Quat(v[3], v[4], v[5], v[6]).rotator(), scale=u.Vector(*v[7:10]))
          for v in before['transforms']]
    orig = [c for c in beds if c.get_name() == before['component']][0]
    det.modify()
    for c in beds:
        c.modify(); c.clear_instances()
    if before.get('mesh'):
        orig.set_static_mesh(u.load_asset(before['mesh'].split('.')[0]))
    if 'overrides' in before:
        orig.set_editor_property('override_materials', [u.load_asset(p.split('.')[0]) if p else None for p in before['overrides']])
    orig.add_instances(ts, False, True)
    RESULT = {'ok': True, 'restored': orig.get_instance_count(), 'emptied': [c.get_name() for c in beds if c != orig], 'dirty': dirty()}
