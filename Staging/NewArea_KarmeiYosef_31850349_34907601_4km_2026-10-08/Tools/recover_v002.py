"""In-editor recovery after the FAILED v002 menu run (2026-10-11 08:07Z, 'failed_bake_save_verification: Duplicate Landscapes
after bake'). Aviv: "Recover + rerun". Cause: the new v002 HDA baked its Landscape under the same name, Unreal renamed the
previous run's Landscape to '<name>_old_0', so the ledger path (by name) pointed at the NEW Landscape and the old one was never
retired. This removes ONLY that renamed previous Landscape, checks one Landscape and unique baked labels, and saves the main
map (named save of that map only). The rerun in regenerate mode (v002 actor kept) then verifies and saves through the sealed
workflow. step 'probe' is read-only; step 'recover' acts. ARGS: expected_pid, step.
"""
import datetime, hashlib, json, os
from collections import Counter
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
MAP = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/BankIntegration_v015/L_KarmeiYosef_31850349_34907601_4km'
PFX = MAP + '.L_KarmeiYosef_31850349_34907601_4km:PersistentLevel.'
OLDP = PFX + 'KarmeiYosef_31850349_34907601_4km_landscape_old_0'
NEWP = PFX + 'KarmeiYosef_31850349_34907601_4km_landscape'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == MAP
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
P = lambda a: a.get_path_name()
acts = eas.get_all_level_actors()
lands = {P(a): a for a in acts if isinstance(a, u.Landscape)}
hda = [a for a in acts if a.get_class().get_name() == 'HoudiniAssetActor']
labels = Counter(a.get_actor_label() for a in acts if not isinstance(a, u.Landscape))
dup_labels = sorted(k for k, v in labels.items() if v > 1)
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
info = {'landscapes': sorted(lands), 'hda_actors': [P(a) + ' | ' + a.get_actor_label() for a in hda], 'actor_count': len(acts),
        'duplicate_labels': dup_labels, 'dirty': dirty()}
if ARGS['step'] == 'probe':
    RESULT = {'ok': True, **info}
else:
    assert set(lands) == {OLDP, NEWP}, info['landscapes']
    assert len(hda) == 1 and hda[0].get_actor_label().endswith('_KY_v002'), info['hda_actors']
    assert not dup_labels, dup_labels
    before_map_sha = sha(ROOT / ('Content' + MAP[5:] + '.umap'))
    assert eas.destroy_actor(lands[OLDP])
    left = [P(a) for a in eas.get_all_level_actors() if isinstance(a, u.Landscape)]
    assert left == [NEWP], left
    assert u.EditorLoadingAndSavingUtils.save_map(world, MAP)
    rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'authority': 'Aviv 2026-10-11: "Recover + rerun"',
           'failed_run': 'menu run 06:23Z, failed_bake_save_verification: Duplicate Landscapes after bake (08:07:43Z)',
           'removed': OLDP, 'kept_landscape': NEWP, 'hda_actor': info['hda_actors'], 'actor_count_before': len(acts),
           'actor_count_after': len(eas.get_all_level_actors()), 'map_sha256_before': before_map_sha,
           'map_sha256_after': sha(ROOT / ('Content' + MAP[5:] + '.umap')), 'dirty_before': info['dirty'], 'dirty_after': dirty(),
           'next': 'fresh editor, menu run in regenerate mode (v002 actor kept) -> sealed verify/save/ledger'}
    (TASK / 'receipts' / 'RECOVER_V002_FAILED_RUN.json').write_text(json.dumps(rec, indent=2), encoding='utf-8')
    RESULT = {'ok': True, **rec}
