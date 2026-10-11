"""In-editor (Karmei Yosef operator), 2026-10-08. With the clone loaded at startup: delete its HoudiniAssetActor (the
clone is never generated) and named-save the clone map only. Original 4 km map must stay c7c858c5. ARGS: expected_pid."""
import datetime, hashlib, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
SRC = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/BankIntegration_v015/L_KarmeiYosef_31850349_34907601_4km'
DST = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/L_KarmeiYosef_31850349_34907601_4km_PCGTrial'
f = lambda pkg: ROOT / ('Content' + pkg[5:] + '.umap')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pid = os.getpid(); assert pid == ARGS['expected_pid']
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == DST
assert dirty() == ([], []), dirty()
before = sha(f(DST))
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
hdas = [x for x in actors.get_all_level_actors() if x.get_class().get_name() == 'HoudiniAssetActor']
removed = [x.get_path_name() for x in hdas]
for x in hdas:
    assert actors.destroy_actor(x)
del hdas
assert u.EditorLoadingAndSavingUtils.save_map(world, DST)
all_actors = actors.get_all_level_actors()
receipt = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'source': SRC, 'clone': DST,
           'clone_sha256_before_cleanup': before, 'clone_sha256': sha(f(DST)), 'source_sha256': sha(f(SRC)),
           'source_unchanged': sha(f(SRC)) == 'c7c858c50ca986d8f9791d394134bc6532c02e50f1971e0a0e302dfee96fca24',
           'removed_houdini_actors': removed, 'actor_count': len(all_actors),
           'landscapes': len([x for x in all_actors if isinstance(x, u.Landscape)]), 'dirty_after': dirty(),
           'history': 'clone duplicated 13:50Z in PID 40064 without loading it; cleanup after a fresh startup on the clone',
           'note': 'clone references the 4 km area Bake/ meshes; a later 4 km regeneration can replace them'}
assert receipt['source_unchanged'] and receipt['dirty_after'] == ([], [])
(TASK / 'receipts' / 'PCG_CLONE.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
RESULT = {'ok': True, **receipt}
