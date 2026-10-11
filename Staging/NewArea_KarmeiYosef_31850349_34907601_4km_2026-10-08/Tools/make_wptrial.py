"""In-editor (Karmei Yosef operator), 2026-10-10. Aviv: "Yes, let's do a trial on a copy of the clone" (World Partition, HLOD,
one object per building, reversible). Discards the loaded clone's in-memory state (new blank map, no save), then duplicates the
SAVED clone map into its own trial folder without loading the copy (a duplicated world held in Python crashed load_level before).
The clone file must stay byte-identical. ARGS: expected_pid, clone_sha256.
"""
import datetime, hashlib, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
SRC = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/L_KarmeiYosef_31850349_34907601_4km_PCGTrial'
DST = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/L_KarmeiYosef_31850349_34907601_4km_WPTrial'
f = lambda pkg: ROOT / ('Content' + pkg[5:] + '.umap')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pid = os.getpid(); assert pid == ARGS['expected_pid']
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
assert sha(f(SRC)) == ARGS['clone_sha256'], 'clone file changed'
assert not f(DST).exists() and not u.EditorAssetLibrary.does_asset_exist(DST)
before = dirty()
assert before[1] == [] and before[0] in ([SRC], []), before
u.EditorLoadingAndSavingUtils.new_blank_map(False)                     # drop the clone without saving
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() != SRC
assert dirty()[0] in ([], [world.get_outermost().get_path_name()]) and dirty()[1] == [], dirty()
dup = u.EditorAssetLibrary.duplicate_asset(SRC, DST)
assert dup, 'duplicate_asset failed'
assert u.EditorLoadingAndSavingUtils.save_packages([dup.get_outermost()], False)
del dup
assert f(DST).exists()
rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'source': SRC, 'trial_map': DST,
       'source_sha256': sha(f(SRC)), 'source_unchanged': sha(f(SRC)) == ARGS['clone_sha256'], 'trial_sha256': sha(f(DST)),
       'trial_bytes': f(DST).stat().st_size, 'dirty_before': before, 'dirty_after': dirty(),
       'authority': 'Aviv 2026-10-10: "Yes, let\'s do a trial on a copy of the clone"; one object per building: "Can we trial it and make it reversible?"'}
assert rec['source_unchanged']
(TASK / 'receipts' / 'WPTRIAL_COPY.json').write_text(json.dumps(rec, indent=2), encoding='utf-8')
RESULT = {'ok': True, **rec}
