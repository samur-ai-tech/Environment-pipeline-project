"""In-editor, read-only: try to reach the WorldPartitionRuntimeHashSet subobject and read its partitions/HLOD setups."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
wp = world.get_world_settings().get_editor_property('world_partition')
base = wp.get_path_name()
out = {'wp_path': base}
found = None
for n in ('WorldPartitionRuntimeHashSet_0', 'RuntimeHash', 'WorldPartitionRuntimeHashSet'):
    try:
        o = u.find_object(None, base + '.' + n)
        if o:
            found = o; out['found'] = o.get_path_name(); break
    except Exception as e:
        out.setdefault('errs', []).append(repr(e)[:100])
if found:
    out['class'] = found.get_class().get_name()
    for p in ('runtime_partitions', 'RuntimePartitions'):
        try:
            v = found.get_editor_property(p); out[p] = str(v)[:3000]
        except Exception as e:
            out[p] = 'n/a ' + repr(e)[:160]
RESULT = {'ok': True, **out}
