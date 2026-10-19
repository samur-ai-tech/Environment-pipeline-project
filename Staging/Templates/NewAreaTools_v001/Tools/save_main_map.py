"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69). Map-only named save of the MAIN area map (the clone has
pcg_finish.py). Refuses unless the loaded world is the main map, the map is the only dirty map and no content package is
dirty (run save_prefix.py first for new assets). Writes receipts/MAIN_SAVE_<label>.json with the saved sha and counts.
ARGS: expected_pid, label."""
import datetime, hashlib, json, os
from collections import Counter
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
import importlib.util
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
MAIN = A.MAIN_MAP
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == MAIN
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
before = dirty()
assert before[1] == [], 'Dirty content packages (save them by name first): %s' % (before[1],)
assert before[0] in ([], [MAIN]), before[0]
f = ROOT / ('Content' + MAIN[5:] + '.umap')
sha_before = hashlib.sha256(f.read_bytes()).hexdigest()
saved = False
if before[0]:
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAIN)
    saved = True
acts = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
ism = 0
for a in acts:
    for c in a.get_components_by_class(u.InstancedStaticMeshComponent):
        ism += c.get_instance_count()
state = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'label': ARGS['label'], 'map': MAIN,
         'saved': saved, 'sha256_before': sha_before, 'saved_map_sha256': hashlib.sha256(f.read_bytes()).hexdigest(),
         'saved_bytes': f.stat().st_size, 'actors': len(acts), 'bldg_actors': sum(1 for a in acts if a.get_actor_label().startswith('Bldg_')),
         'ism_instances': ism, 'classes': dict(Counter(a.get_class().get_name() for a in acts).most_common(8)), 'dirty_after': dirty()}
(TASK / 'receipts' / ('MAIN_SAVE_%s.json' % ARGS['label'])).write_text(json.dumps(state, indent=2), encoding='utf-8')
RESULT = {'ok': state['dirty_after'] == ([], []), **state}
