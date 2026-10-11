"""In-editor (Karmei Yosef operator, WP trial only, 2026-10-10). Aviv wants an ALWAYS-LOADED instancing HLOD for trees. The
converter's RuntimeHashSet has three HLOD setups: 'HLODLayer_Instanced' (grid 1), 'HLODLayer_Merged' (grid 2) and an empty
'Non-Spatially Loaded HLODs' setup on a persistent partition. The vegetation/landscape layer (..._HLODLayer_Merged, now
Instancing) sits in setup 2, so it streams. This moves that layer into the persistent setup by rewriting RuntimePartitions with
the engine's own 'set' command (Python cannot edit these structs). The current value is taken from an 'obj dump' line in this
editor's log (ARGS.log, ARGS.line_contains). Not saved here. ARGS: expected_pid, log, hashset_path.
"""
import os, re
from pathlib import Path
import unreal as u
assert os.getpid() == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
line = [l for l in Path(ARGS['log']).read_text(encoding='utf-8', errors='replace').splitlines() if 'RuntimePartitions(0)=' in l][-1]
val = line.split('RuntimePartitions(0)=', 1)[1].strip()
merged_ref = re.search(r'HLODLayers=\("(/Script/Engine\.HLODLayer\'[^\']*HLODLayer_Merged[^\']*\')"\)', val).group(1)
# setup 2 loses the layer, the persistent setup gains it
new = val.replace('HLODLayers=("%s")' % merged_ref, 'HLODLayers=()', 1)
new = new.replace('(RowDisplayName="Non-Spatially Loaded HLODs",', '(Name="NonSpatialHLODs",HLODLayers=("%s"),RowDisplayName="Non-Spatially Loaded HLODs",' % merged_ref, 1)
assert new != val and new.count('HLODLayer_Merged') == val.count('HLODLayer_Merged')
hs = u.find_object(None, ARGS['hashset_path'])
hs.modify()
u.SystemLibrary.execute_console_command(world, 'set %s RuntimePartitions (%s)' % (ARGS['hashset_path'], new))
u.SystemLibrary.execute_console_command(world, 'obj dump %s' % ARGS['hashset_path'])
RESULT = {'ok': True, 'old_len': len(val), 'new_len': len(new), 'merged_ref': merged_ref[-60:]}
