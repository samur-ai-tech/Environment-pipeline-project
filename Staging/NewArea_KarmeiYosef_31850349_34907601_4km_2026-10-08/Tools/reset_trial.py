"""In-editor (Karmei Yosef operator, trial only): drop unsaved trial edits - blank map without saving, delete unsaved new assets
under the trial Shells folder, reload the trial map from disk. ARGS: expected_pid."""
import os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
MAP = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/L_KarmeiYosef_31850349_34907601_4km_WPTrial'
OUT = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/Buildings/Shells'
assert os.getpid() == ARGS['expected_pid']
dirty0 = [x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()] + [x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
assert all(p.startswith('/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/') for p in dirty0), dirty0
u.EditorLoadingAndSavingUtils.new_blank_map(False)
deleted = []
for a in u.EditorAssetLibrary.list_assets(OUT, True, False):
    pkg = a.split('.')[0]
    if not (ROOT / ('Content' + pkg[5:] + '.uasset')).exists():
        assert u.EditorAssetLibrary.delete_asset(pkg), pkg; deleted.append(pkg)
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(MAP)
RESULT = {'ok': True, 'dirty_before': dirty0, 'deleted_unsaved': deleted,
          'world': u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name(),
          'dirty_after': [x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()] + [x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
