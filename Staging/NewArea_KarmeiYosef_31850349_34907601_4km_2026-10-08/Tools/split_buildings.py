"""In-editor (Karmei Yosef operator, WP/per-building trial 2026-10-10; Aviv: "one object per building, we should do it ... trial
it and make it reversible"). Trial map only: /Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/L_..._WPTrial.
The receipt (WPTrial/BUILDINGS_COMPACT.json) is used ONLY to assign each instance to its building (OSM id); every transform is
copied from the instance itself, never rebuilt from Houdini data. Mapping verified: UE cm = (P0, P2, P1) * 100.
steps (ARGS.step):
  plan     read-only: match every module / whole-building instance in the bank ISM actors to exactly one receipt entry
           (same mesh, <= 2 cm); writes receipts/WPTRIAL_BLD_PLAN.json (per building: source component, index, transform,
           override materials). Refuses on any unmatched instance, unmatched receipt entry or duplicate.
  build    ARGS.start, ARGS.count: create actors 'Bldg_<osm>' (folder Buildings) for that slice of the plan: one instanced
           component per module mesh, the door as its own StaticMeshComponent 'Door' (animatable child later), whole
           buildings as one StaticMeshComponent. Override materials copied from the source component. Idempotent per actor.
  remove   remove the moved instances from the source bank components (all of a component's instances moved -> clear it).
  verify   per-mesh instance totals equal the plan's 'before' totals; actor and component counts.
No save here (the trial save step saves the map). ARGS: expected_pid, step, target ('wptrial' | 'clone_v2').
"""
import datetime, json, math, os
from collections import defaultdict, Counter
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
# ARGS.target: 'wptrial' (2026-10-10 trial, default) | 'clone_v2' (Aviv 2026-10-11 "Split on the clone now": rebuilt clone after
# the v002 regeneration; data from Buildings_v2/compact_buildings_v2.py on the current run's receipt)
TARGET = ARGS.get('target', 'wptrial')
MAP, DATA, PLAN = {
    'wptrial': ('/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/L_KarmeiYosef_31850349_34907601_4km_WPTrial',
                TASK / 'WPTrial', TASK / 'receipts' / 'WPTRIAL_BLD_PLAN.json'),
    'clone_v2': ('/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/L_KarmeiYosef_31850349_34907601_4km_PCGTrial_v2',
                 TASK / 'Buildings_v2', TASK / 'receipts' / 'CLONE_V2_BLD_PLAN.json')}[TARGET]
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == MAP
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
step = ARGS['step']
mp = lambda m: m.get_path_name().split('.')[0] if m else None


def xf(t):
    l, r, s = t.translation, t.rotation.rotator(), t.scale3d
    return [l.x, l.y, l.z, r.roll, r.pitch, r.yaw, s.x, s.y, s.z]


def mk(v):
    return u.Transform(location=u.Vector(v[0], v[1], v[2]), rotation=u.Rotator(roll=v[3], pitch=v[4], yaw=v[5]), scale=u.Vector(v[6], v[7], v[8]))


def bank_components(meshes):
    out = []
    for a in eas.get_all_level_actors():
        if a.get_class().get_name() != 'Actor' or not a.get_actor_label().startswith('bank_instances'):
            continue
        for c in a.get_components_by_class(u.InstancedStaticMeshComponent):
            m = mp(c.get_editor_property('static_mesh'))
            if m in meshes:
                out.append((a, c, m))
    return out


if step == 'plan':
    B = json.loads((DATA / 'BUILDINGS_COMPACT.json').read_text(encoding='utf-8'))
    entries = [dict(e, kind='door' if 'Steeldoor' in e['mesh'] else 'module') for e in B['modules']] + [dict(e, kind='whole') for e in B['whole']]
    meshes = {e['mesh'] for e in entries}
    grid = defaultdict(list)                                           # (mesh, bx, by) -> entry indices, 10 cm buckets
    for k, e in enumerate(entries):
        grid[(e['mesh'], int(math.floor(e['ue'][0] / 10)), int(math.floor(e['ue'][1] / 10)))].append(k)
    used = [None] * len(entries)
    before = Counter(); unmatched = []; dup = []
    plan = defaultdict(lambda: {'parts': []})
    for a, c, m in bank_components(meshes):
        ovr = [mp(x) for x in c.get_editor_property('override_materials')]
        for i in range(c.get_instance_count()):
            t = c.get_instance_transform(i, True); p = t.translation
            before[m] += 1
            bx, by = int(math.floor(p.x / 10)), int(math.floor(p.y / 10))
            best = None
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for k in grid.get((m, bx + dx, by + dy), []):
                        d = math.dist((p.x, p.y, p.z), entries[k]['ue'])
                        if d <= 2.0 and (best is None or d < best[0]):
                            best = (d, k)
            if best is None:
                unmatched.append([m, i, round(p.x), round(p.y)]); continue
            k = best[1]
            if used[k] is not None:
                dup.append([m, i, k]); continue
            used[k] = (c.get_path_name(), i)
            e = entries[k]
            plan[e['osm']]['parts'].append({'kind': e['kind'], 'mesh': m, 'src': c.get_path_name(), 'src_actor': a.get_actor_label(),
                                            'index': i, 'xf': xf(t), 'override': ovr, 'dist_cm': round(best[0], 3)})
    missing = [entries[k]['pid'] for k in range(len(entries)) if used[k] is None]
    ok = not unmatched and not dup and not missing
    res = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'map': MAP, 'ok': ok,
           'entries': len(entries), 'matched': sum(1 for x in used if x is not None), 'unmatched_instances': unmatched[:50],
           'n_unmatched_instances': len(unmatched), 'duplicates': dup[:50], 'missing_receipt_entries': missing[:50], 'n_missing': len(missing),
           'before_totals': dict(before), 'buildings': len(plan),
           'max_dist_cm': max((p['dist_cm'] for b in plan.values() for p in b['parts']), default=None),
           'plan': {k: v for k, v in sorted(plan.items())}}
    PLAN.write_text(json.dumps(res), encoding='utf-8')
    RESULT = {'ok': ok, **{k: v for k, v in res.items() if k != 'plan'},
              'kinds': dict(Counter(p['kind'] for b in plan.values() for p in b['parts']))}

elif step == 'build':
    P = json.loads(PLAN.read_text(encoding='utf-8')); assert P['ok']
    osms = sorted(P['plan'])[ARGS['start']:ARGS['start'] + ARGS['count']]
    existing = {a.get_actor_label() for a in eas.get_all_level_actors() if a.get_actor_label().startswith('Bldg_')}
    sds = u.get_engine_subsystem(u.SubobjectDataSubsystem)
    made = 0; comps = 0
    for osm in osms:
        label = 'Bldg_' + osm
        if label in existing:
            continue
        parts = P['plan'][osm]['parts']
        xs = [p['xf'][0] for p in parts]; ys = [p['xf'][1] for p in parts]; zs = [p['xf'][2] for p in parts]
        pivot = u.Vector((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs))
        actor = eas.spawn_actor_from_class(u.Actor, pivot)
        actor.set_actor_label(label); actor.set_folder_path('Buildings')
        root_h = sds.k2_gather_subobject_data_for_instance(actor)[0]
        root = u.SubobjectDataBlueprintFunctionLibrary.get_object(u.SubobjectDataBlueprintFunctionLibrary.get_data(root_h))
        if root is None or not isinstance(root, u.SceneComponent):
            h, _ = sds.add_new_subobject(u.AddNewSubobjectParams(parent_handle=root_h, new_class=u.SceneComponent))
            sds.rename_subobject(h, u.Text('BuildingRoot'))
            rc = u.SubobjectDataBlueprintFunctionLibrary.get_object(u.SubobjectDataBlueprintFunctionLibrary.get_data(h))
            rc.set_mobility(u.ComponentMobility.STATIC)
            root_h = h
        actor.set_actor_location(pivot, False, False)                  # pivot = footprint centre at the lowest base
        def add(cls, name):
            h, fail = sds.add_new_subobject(u.AddNewSubobjectParams(parent_handle=root_h, new_class=cls))
            sds.rename_subobject(h, u.Text(name))
            c = u.SubobjectDataBlueprintFunctionLibrary.get_object(u.SubobjectDataBlueprintFunctionLibrary.get_data(h))
            return c                                   # mobility is set for the whole chain by step fix_attach (static root first)
        by_mesh = defaultdict(list)
        for p in parts:
            by_mesh[(p['kind'], p['mesh'], tuple(p['override']))].append(p)
        for (kind, mesh, ovr), ps in sorted(by_mesh.items()):
            m = u.load_asset(mesh)
            if kind in ('door', 'whole'):
                for n, p in enumerate(ps):
                    c = add(u.StaticMeshComponent, ('Door' if kind == 'door' else 'Building') + ('' if n == 0 else '_%d' % n))
                    c.set_static_mesh(m)
                    c.set_world_transform(mk(p['xf']), False, False)
                    for si, mat in enumerate(ovr):
                        if mat:
                            c.set_material(si, u.load_asset(mat))
                    comps += 1
            else:
                c = add(u.InstancedStaticMeshComponent, mesh.rsplit('/', 1)[1])
                c.set_static_mesh(m)
                for si, mat in enumerate(ovr):
                    if mat:
                        c.set_material(si, u.load_asset(mat))
                c.add_instances([mk(p['xf']) for p in ps], False, True)
                comps += 1
        made += 1
    RESULT = {'ok': True, 'slice': [ARGS['start'], ARGS['count']], 'actors_made': made, 'components': comps, 'skipped_existing': len(osms) - made}

elif step == 'fix_attach':
    # Root cause (2026-10-09): Unreal refuses to attach a STATIC component to a MOVABLE parent. The roots stayed MOVABLE while
    # the last part added was set STATIC, so that attachment was dropped on save (559 window-wall ISMs, 32 whole buildings).
    # Fix: whole chain STATIC top-down, attach detached parts keeping relative (identity) transforms, restore single-mesh
    # transforms from the plan, then check every position.
    P = json.loads(PLAN.read_text(encoding='utf-8')); assert P['ok']
    KR = u.AttachmentRule.KEEP_RELATIVE
    fixed = 0; failed = []; checked = 0; worst = 0.0
    for a in eas.get_all_level_actors():
        lab = a.get_actor_label()
        if not lab.startswith('Bldg_'):
            continue
        comps = a.get_components_by_class(u.SceneComponent)
        root = [c for c in comps if c.get_name().startswith('BuildingRoot')][0]
        a.modify()
        order = [a.root_component, root] + [c for c in comps if c not in (a.root_component, root)]
        for c in order:
            if c is not None and not isinstance(c, u.BillboardComponent):
                c.modify(); c.set_mobility(u.ComponentMobility.STATIC)
        parts = P['plan'].get(lab[5:], {}).get('parts', [])
        singles = {p['mesh']: p['xf'] for p in parts if p['kind'] in ('door', 'whole')}
        for c in comps:
            if c in (a.root_component, root) or isinstance(c, u.BillboardComponent):
                continue
            if c.get_attach_parent() is None:
                if isinstance(c, u.InstancedStaticMeshComponent):
                    c.set_editor_property('relative_location', u.Vector(0, 0, 0))
                    c.set_editor_property('relative_rotation', u.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
                ok = c.attach_to_component(root, '', KR, KR, KR, False)
                if c.get_attach_parent() is None:
                    failed.append([lab, c.get_name()]); continue
                fixed += 1
            if not isinstance(c, u.InstancedStaticMeshComponent):
                m = mp(c.get_editor_property('static_mesh'))
                if m in singles:
                    c.set_world_transform(mk(singles[m]), False, False)
        want = defaultdict(list)
        for p in parts:
            want[p['mesh']].append(p['xf'][:3])
        for c in a.get_components_by_class(u.StaticMeshComponent):
            m = mp(c.get_editor_property('static_mesh'))
            if m not in want:
                continue
            got = [c.get_instance_transform(i, True).translation for i in range(c.get_instance_count())] if isinstance(c, u.InstancedStaticMeshComponent) else [c.get_world_location()]
            for g in got:
                d = min(math.dist((g.x, g.y, g.z), w) for w in want[m]); worst = max(worst, d); checked += 1
    RESULT = {'ok': worst < 1.0 and not failed, 'reattached': fixed, 'attach_failed': failed[:10], 'n_failed': len(failed),
              'positions_checked': checked, 'worst_cm': round(worst, 3)}

elif step == 'remove':
    P = json.loads(PLAN.read_text(encoding='utf-8')); assert P['ok']
    built = {a.get_actor_label()[5:] for a in eas.get_all_level_actors() if a.get_actor_label().startswith('Bldg_')}
    assert built == set(P['plan']), ('not all buildings built', len(built), len(P['plan']))
    by_src = defaultdict(list)
    for b in P['plan'].values():
        for p in b['parts']:
            by_src[p['src']].append(p['index'])
    comps = {c.get_path_name(): (a, c) for a, c, m in bank_components(set(P['before_totals']))}
    cleared, removed = 0, 0
    for src, idx in by_src.items():
        a, c = comps[src]
        a.modify(); c.modify()
        if len(set(idx)) == c.get_instance_count():
            c.clear_instances(); cleared += 1
        else:
            for i in sorted(set(idx), reverse=True):
                c.remove_instance(i)
        removed += len(set(idx))
    RESULT = {'ok': True, 'removed_instances': removed, 'cleared_components': cleared}

elif step == 'verify':
    P = json.loads(PLAN.read_text(encoding='utf-8'))
    now = Counter(); actors = 0; comps = Counter()
    for a in eas.get_all_level_actors():
        lab = a.get_actor_label()
        if lab.startswith('Bldg_'):
            actors += 1
        if lab.startswith('Bldg_') or lab.startswith('bank_instances'):
            for c in a.get_components_by_class(u.StaticMeshComponent):
                m = mp(c.get_editor_property('static_mesh'))
                if m in P['before_totals']:
                    n = c.get_instance_count() if isinstance(c, u.InstancedStaticMeshComponent) else 1
                    now[m] += n
                    if lab.startswith('Bldg_'):
                        comps['ism' if isinstance(c, u.InstancedStaticMeshComponent) else 'smc'] += 1
    left = {m: 0 for m in P['before_totals']}
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith('bank_instances'):
            for c in a.get_components_by_class(u.InstancedStaticMeshComponent):
                m = mp(c.get_editor_property('static_mesh'))
                if m in left:
                    left[m] += c.get_instance_count()
    same = {m: (P['before_totals'][m], now[m]) for m in P['before_totals'] if P['before_totals'][m] != now[m]}
    RESULT = {'ok': not same, 'building_actors': actors, 'expected_buildings': P['buildings'], 'components': dict(comps),
              'mismatch': same, 'left_in_bank_components': {k.rsplit('/', 1)[1]: v for k, v in left.items() if v}}
