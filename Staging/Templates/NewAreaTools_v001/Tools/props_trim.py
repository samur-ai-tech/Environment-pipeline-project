"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69) (playbook 10c: props over open land). Applies
receipts/PROPS_PLAN.json (Tools/props_near_roads_plan.py) to the MAIN area map: every plan entry is matched to exactly one
instance in the area-wide bank ISM actors (same mesh, <= 2 cm, 10 cm buckets, as split_buildings.py); 'keep: false' instances
are removed. Street props, poles and building actors are never touched. Reversible: the pre-step map is in ../Before/ and the
removed transforms are written to receipts/PROPS_REMOVED.json.
steps (ARGS.step):
  match   read-only: refuses on any unmatched plan entry or duplicate; writes receipts/PROPS_MATCH.json.
  remove  removes the matched 'keep: false' instances (descending index per component); writes receipts/PROPS_REMOVED.json.
  verify  per-mesh instance totals == before - removed.
No save here (save_main_map.py). ARGS: expected_pid, script_file (client), step.
"""
import datetime, importlib.util, json, math, os
from collections import Counter, defaultdict
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
MAIN = A.MAIN_MAP
PLAN, MATCH, REMOVED = TASK / 'receipts' / 'PROPS_PLAN.json', TASK / 'receipts' / 'PROPS_MATCH.json', TASK / 'receipts' / 'PROPS_REMOVED.json'
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == MAIN
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
mp = lambda m: m.get_path_name().split('.')[0] if m else None
step = ARGS['step']


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


def totals(meshes):
    t = Counter()
    for a, c, m in bank_components(meshes):
        t[m] += c.get_instance_count()
    return t


P = json.loads(PLAN.read_text(encoding='utf-8'))
entries = P['entries']
meshes = {e['mesh'] for e in entries}

if step == 'match':
    grid = defaultdict(list)
    for k, e in enumerate(entries):
        grid[(e['mesh'], int(math.floor(e['ue'][0] / 10)), int(math.floor(e['ue'][1] / 10)))].append(k)
    used = [None] * len(entries); dup = []; other = Counter()
    for a, c, m in bank_components(meshes):
        for i in range(c.get_instance_count()):
            p = c.get_instance_transform(i, True).translation
            bx, by = int(math.floor(p.x / 10)), int(math.floor(p.y / 10))
            best = None
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for k in grid.get((m, bx + dx, by + dy), []):
                        d = math.dist((p.x, p.y, p.z), entries[k]['ue'])
                        if d <= 2.0 and (best is None or d < best[0]):
                            best = (d, k)
            if best is None:
                other[m] += 1; continue              # same mesh used by another role (e.g. street prop): left alone
            if used[best[1]] is not None:
                dup.append([m, i, best[1]]); continue
            used[best[1]] = (c.get_path_name(), i, round(best[0], 3))
    missing = [k for k in range(len(entries)) if used[k] is None]
    ok = not dup and not missing
    res = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'ok': ok, 'entries': len(entries),
           'matched': len(entries) - len(missing), 'n_missing': len(missing), 'missing_sample': [entries[k]['pid'] for k in missing[:20]],
           'duplicates': dup[:20], 'unplanned_same_mesh_instances': dict(other), 'before_totals': dict(totals(meshes)),
           'max_dist_cm': max((x[2] for x in used if x), default=None), 'match': used}
    MATCH.write_text(json.dumps(res), encoding='utf-8')
    RESULT = {k: v for k, v in res.items() if k != 'match'}

elif step == 'remove':
    M = json.loads(MATCH.read_text(encoding='utf-8')); assert M['ok']
    assert dict(totals(meshes)) == M['before_totals'], 'instances changed since match'
    comps = {c.get_path_name(): (a, c) for a, c, m in bank_components(meshes)}
    by_src = defaultdict(list)
    for k, e in enumerate(entries):
        if not e['keep']:
            src, i, _ = M['match'][k]
            by_src[src].append(i)
    removed = []
    for src, idx in by_src.items():
        a, c = comps[src]
        a.modify(); c.modify()
        for i in sorted(set(idx), reverse=True):
            t = c.get_instance_transform(i, True)
            removed.append([mp(c.get_editor_property('static_mesh')), src, [t.translation.x, t.translation.y, t.translation.z],
                            [t.rotation.rotator().roll, t.rotation.rotator().pitch, t.rotation.rotator().yaw], [t.scale3d.x, t.scale3d.y, t.scale3d.z]])
            c.remove_instance(i)
    REMOVED.write_text(json.dumps({'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid,
                                   'margin_m': P['margin_m'], 'removed': removed}), encoding='utf-8')
    RESULT = {'ok': True, 'removed_instances': len(removed), 'components_touched': len(by_src)}

elif step == 'verify':
    M = json.loads(MATCH.read_text(encoding='utf-8'))
    gone = Counter(e['mesh'] for e in entries if not e['keep'])
    now = totals(meshes)
    bad = {m: (M['before_totals'].get(m, 0), gone[m], now[m]) for m in meshes if M['before_totals'].get(m, 0) - gone[m] != now[m]}
    RESULT = {'ok': not bad, 'mismatch': bad, 'kept_small_props': sum(1 for e in entries if e['keep']),
              'instances_now_for_these_meshes': sum(now.values())}
