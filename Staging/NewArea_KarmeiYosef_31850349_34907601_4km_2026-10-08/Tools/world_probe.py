"""In-editor, read-only (2026-10-11, after the failed v002 run): landscapes and HDA actors in the loaded world, actor counts by
class, dirty packages. Changes nothing. ARGS: expected_pid."""
import os
from collections import Counter
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
acts = eas.get_all_level_actors()
lands = [{'label': a.get_actor_label(), 'path': a.get_path_name(), 'class': a.get_class().get_name(),
          'material': a.get_editor_property('landscape_material').get_path_name() if a.get_editor_property('landscape_material') else None,
          'bounds_cm': [round(v) for v in (a.get_actor_bounds(False)[1].x, a.get_actor_bounds(False)[1].y, a.get_actor_bounds(False)[1].z)]}
         for a in acts if isinstance(a, u.LandscapeProxy)]
hda = [{'label': a.get_actor_label(), 'path': a.get_path_name()} for a in acts if a.get_class().get_name() == 'HoudiniAssetActor']
RESULT = {'ok': True, 'world': u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_path_name(), 'actors': len(acts),
          'by_class': dict(Counter(a.get_class().get_name() for a in acts).most_common(12)), 'landscapes': lands, 'hda_actors': hda,
          'dirty_maps': sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
          'dirty_content_count': len(u.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
