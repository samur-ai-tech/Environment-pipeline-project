"""In-editor (WP trial only): move the vegetation/landscape HLOD layer into the persistent 'Non-Spatially Loaded HLODs' setup by
editing the RuntimePartitions array element through StructBase.import_text (the 'set' console command is blocked in the editor).
Falls back to reporting what the element type allows. Not saved here. ARGS: expected_pid, log, hashset_path."""
import os, re
from pathlib import Path
import unreal as u
assert os.getpid() == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
hs = u.find_object(None, ARGS['hashset_path'])
arr = hs.get_editor_property('RuntimePartitions')
el = arr[0]
out = {'elem_type': type(el).__name__, 'elem_methods': [n for n in dir(el) if not n.startswith('_')][:20]}
line = [l for l in Path(ARGS['log']).read_text(encoding='utf-8', errors='replace').splitlines() if 'RuntimePartitions(0)=' in l][-1]
val = line.split('RuntimePartitions(0)=', 1)[1].strip()
ref = re.search(r'HLODLayers=\("(/Script/Engine\.HLODLayer\'[^\']*HLODLayer_Merged[^\']*\')"\)', val).group(1)
new = val.replace('HLODLayers=("%s")' % ref, 'HLODLayers=()', 1)
new = new.replace('(RowDisplayName="Non-Spatially Loaded HLODs",', '(Name="NonSpatialHLODs",HLODLayers=("%s"),RowDisplayName="Non-Spatially Loaded HLODs",' % ref, 1)
try:
    ok = el.import_text(new)
    out['import_text'] = str(ok)
    out['export_after'] = el.export_text()[:400] if hasattr(el, 'export_text') else None
    hs.modify()
    hs.set_editor_property('RuntimePartitions', [el])
    out['set'] = 'ok'
except Exception as e:
    out['error'] = repr(e)[:300]
u.SystemLibrary.execute_console_command(world, 'obj dump %s' % ARGS['hashset_path'])
RESULT = {'ok': True, **out}
