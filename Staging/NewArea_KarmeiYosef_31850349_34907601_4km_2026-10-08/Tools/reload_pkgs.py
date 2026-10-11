"""In-editor (Karmei Yosef operator): discard in-memory edits by reloading named packages from disk (paths under this task's
area/clone folders only), then report dirty packages. ARGS: expected_pid, packages [/Game/... package paths]."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
ok = ('/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/', '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/')
pk = []
for p in ARGS['packages']:
    assert p.startswith(ok), p
    a = u.load_asset(p); assert a, p
    pk.append(a.get_outermost())
res = u.EditorLoadingAndSavingUtils.reload_packages(pk, u.ReloadPackagesInteractionMode.ASSUME_POSITIVE)
m = u.load_asset(ARGS['packages'][0])
RESULT = {'ok': True, 'reload': str(res), 'nanite_after': bool(m.get_editor_property('nanite_settings').enabled) if isinstance(m, u.StaticMesh) else None,
          'dirty': [sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                    sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())]}
