"""In-editor: named save of dirty packages under the clone's PazFarm/ and Masks/ folders only; refuse anything else.
ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
TRIAL = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial'
pk = list(u.EditorLoadingAndSavingUtils.get_dirty_content_packages())
names = [p.get_path_name() for p in pk]
other = [n for n in names if not n.startswith((TRIAL + '/PazFarm/', TRIAL + '/Masks/'))]
assert not other, other
if pk:
    assert u.EditorLoadingAndSavingUtils.save_packages(pk, False)
RESULT = {'ok': True, 'saved': len(pk), 'left_dirty_content': [p.get_path_name() for p in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
