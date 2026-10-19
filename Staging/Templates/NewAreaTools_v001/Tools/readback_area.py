"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the fork of the manager's readback_area.py.
Read-only read-back after a run: counts, dirty state, saved map sha, the last
run's state from memory (never the live ledger), and optional high-resolution screenshots from a high oblique over the
Landscape and one street-level view, written to <this task>/receipts/Captures/<label>_*.png.
ARGS: label, screenshots (bool), expected_pid, script_file (client). Never saves, cooks or changes settings.
"""
import datetime, hashlib, importlib.util, json, math, os
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
pid = os.getpid()
assert pid == ARGS['expected_pid'], (pid, ARGS['expected_pid'])


def p(obj):
    return obj.get_path_name() if hasattr(obj, 'get_path_name') else str(obj)


world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
map_path = world.get_outermost().get_path_name()
map_file = ROOT / ('Content' + map_path[5:] + '.umap')
actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
landscapes = [x for x in actors if isinstance(x, u.Landscape)]
hdas = [p(x) for x in actors if x.get_class().get_name() == 'HoudiniAssetActor']
classes = {}
for x in actors:
    classes[x.get_class().get_name()] = classes.get(x.get_class().get_name(), 0) + 1
ism_instances = 0
for x in actors:
    for c in x.get_components_by_class(u.InstancedStaticMeshComponent):
        ism_instances += c.get_instance_count()
dirty = (sorted(p(x) for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
         sorted(p(x) for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
run_state = None
try:
    import geocity_bank_workflow as bank
    if bank.ACTIVE:
        r = bank.ACTIVE[-1]
        run_state = {k: r.state.get(k) for k in ('phase', 'pid', 'landscape_count', 'baked_actor_count', 'instance_count',
                                                  'actual_instance_count', 'saved_map_sha256', 'error')}
except Exception as exc:  # read-only best effort
    run_state = {'error': repr(exc)}
shots = []
if ARGS.get('screenshots') and landscapes:
    origin, extent = landscapes[0].get_actor_bounds(False)
    out_dir = TASK / 'receipts' / 'Captures'
    out_dir.mkdir(parents=True, exist_ok=True)
    sub = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    size = max(extent.x, extent.y)
    views = [('wide', u.Vector(origin.x - size * 0.9, origin.y - size * 0.9, origin.z + size * 1.1), u.Rotator(roll=0.0, pitch=-40.0, yaw=45.0)),
             ('oblique', u.Vector(origin.x - size * 0.4, origin.y, origin.z + size * 0.35), u.Rotator(roll=0.0, pitch=-30.0, yaw=0.0))]
    for name, loc, rot in views:
        sub.set_level_viewport_camera_info(loc, rot)
        fname = str(out_dir / ('%s_%s.png' % (ARGS['label'], name)))
        ok = u.AutomationLibrary.take_high_res_screenshot(2383, 820, fname)
        shots.append({'shot': name, 'requested': fname, 'queued': bool(ok)})
result = {'pid': pid, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'map': map_path,
          'saved_map_sha256': hashlib.sha256(map_file.read_bytes()).hexdigest() if map_file.exists() else None,
          'saved_map_bytes': map_file.stat().st_size if map_file.exists() else None,
          'actor_count': len(actors), 'landscape_count': len(landscapes), 'hda_actors': hdas, 'ism_instances': ism_instances,
          'classes_top': dict(sorted(classes.items(), key=lambda kv: -kv[1])[:12]), 'dirty': dirty, 'run_state': run_state, 'screenshots': shots}
(TASK / 'receipts').mkdir(exist_ok=True)
(TASK / 'receipts' / ('READBACK_%s_PID%d.json' % (ARGS['label'], pid))).write_text(json.dumps(result, indent=2, default=str), encoding='utf-8')
RESULT = {'ok': True, **result}
