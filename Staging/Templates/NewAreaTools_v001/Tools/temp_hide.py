"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69). Editor-only temporary hide/unhide of actors by exact label
(set_is_temporarily_hidden_in_editor: a transient flag, never saved, nothing deleted), for captures that show the map with
chosen actors hidden (e.g. generated Bldg_ blocks before Aviv decides on their removal). Refuses if the dirty package lists change.
ARGS: expected_pid, labels (exact actor labels), hide (bool)."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
d0 = dirty()
want = list(ARGS['labels'])
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors() if a.get_actor_label() in want}
assert sorted(acts) == sorted(want), ('labels not found exactly', sorted(set(want) - set(acts)))
for a in acts.values():
    a.set_is_temporarily_hidden_in_editor(bool(ARGS['hide']))
d1 = dirty()
assert d1 == d0, ('temporary hide changed the dirty lists', d0, d1)
RESULT = {'ok': True, 'hidden': bool(ARGS['hide']), 'labels': sorted(acts),
          'now_hidden': {k: a.is_temporarily_hidden_in_editor() for k, a in acts.items()}, 'dirty': d1}
