"""In-editor (Karmei Yosef operator): named saves of the dirty content packages under ARGS.prefix only; refuses if anything
outside that prefix (or a map) is dirty. ARGS: expected_pid, prefix."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
pre = ARGS['prefix'].rstrip('/') + '/'
maps = [p.get_path_name() for p in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
pk = list(u.EditorLoadingAndSavingUtils.get_dirty_content_packages())
other = [p.get_path_name() for p in pk if not p.get_path_name().startswith(pre)]
assert not other, (maps, other)                     # maps are never saved here
ok = u.EditorLoadingAndSavingUtils.save_packages(pk, False) if pk else True
RESULT = {'ok': bool(ok), 'saved': [p.get_path_name() for p in pk],
          'dirty_after': [p.get_path_name() for p in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
