"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69) (GOVERNANCE_RECORD.md RC-14 names this tool). Remove actors Aviv confirmed, by exact label, on the main map
only. Each actor is recorded first (label, path, class, folder, transform, every StaticMesh/ISM component with mesh,
instance count and materials) to receipts/REMOVED_ACTORS_<utc>.json opened in 'x' mode; then destroyed; then checked gone.
Assets on disk are never touched. No save here (save_main_map.py).
ARGS: expected_pid, script_file (client), labels (exact), authority (Aviv's words)."""
import datetime, importlib.util, json, os
from pathlib import Path
import unreal as u
pid = os.getpid(); assert pid == ARGS['expected_pid']
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
MAP = A.MAIN_MAP
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == MAP, world.get_outermost().get_path_name()
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
auth = ARGS.get('authority'); assert isinstance(auth, str) and auth.strip(), 'ARGS.authority is required'
labels = list(ARGS['labels']); assert labels and len(set(labels)) == len(labels), labels
P = lambda o: o.get_path_name() if o else None
by = {}
for a in eas.get_all_level_actors():
    if a.get_actor_label() in labels:
        by.setdefault(a.get_actor_label(), []).append(a)
assert sorted(by) == sorted(labels) and all(len(v) == 1 for v in by.values()), ('each label must match exactly one actor', {k: len(v) for k, v in by.items()}, sorted(set(labels) - set(by)))


def comp(c):
    r = {'name': c.get_name(), 'class': c.get_class().get_name(), 'mesh': P(c.get_editor_property('static_mesh')),
         'materials': [P(c.get_material(i)) for i in range(c.get_num_materials())]}
    if isinstance(c, u.InstancedStaticMeshComponent):
        r['instances'] = c.get_instance_count()
    return r


rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'map': MAP, 'authority': auth, 'actors': []}
for lab in labels:
    a = by[lab][0]
    l, r, s = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
    rec['actors'].append({'label': lab, 'path': P(a), 'class': a.get_class().get_name(), 'folder': str(a.get_folder_path()),
                          'location_cm': [l.x, l.y, l.z], 'rotation_pitch_yaw_roll': [r.pitch, r.yaw, r.roll], 'scale': [s.x, s.y, s.z],
                          'components': [comp(c) for c in a.get_components_by_class(u.StaticMeshComponent)]})
out = TASK / 'receipts' / ('REMOVED_ACTORS_%s.json' % datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
with open(out, 'x', encoding='utf-8') as stream:
    json.dump(rec, stream, indent=2)
for lab in labels:
    assert eas.destroy_actor(by[lab][0]), 'destroy failed: ' + lab
left = [a.get_actor_label() for a in eas.get_all_level_actors() if a.get_actor_label() in labels]
assert not left, left
RESULT = {'ok': True, 'removed': labels, 'record': str(out), 'actors_now': len(eas.get_all_level_actors()),
          'dirty_maps': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
          'dirty_content': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
