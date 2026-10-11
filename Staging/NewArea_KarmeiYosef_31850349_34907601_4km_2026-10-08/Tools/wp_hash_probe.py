"""In-editor, read-only: the World Partition runtime hash (class, partitions, HLOD setups) via export_text/properties."""
import os, re
import unreal as u
assert os.getpid() == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
ws = world.get_world_settings()
out = {}
wp = None
for getter in (lambda: ws.get_editor_property('world_partition'), lambda: world.get_world_partition()):
    try:
        wp = getter()
        if wp:
            break
    except Exception as e:
        out.setdefault('getter_errs', []).append(repr(e)[:120])
out['wp'] = wp.get_class().get_name() if wp else None
if wp:
    for p in ('runtime_hash', 'editor_hash', 'default_hlod_layer'):
        try:
            v = wp.get_editor_property(p); out[p] = v.get_class().get_name() if hasattr(v, 'get_class') and v else str(v)
            if p == 'runtime_hash' and v:
                rh = v
                out['rh_props'] = {}
                for q in ('runtime_partitions', 'runtime_partitions_streaming_policy'):
                    try:
                        out['rh_props'][q] = str(rh.get_editor_property(q))[:3000]
                    except Exception as e:
                        out['rh_props'][q] = 'n/a ' + repr(e)[:80]
                out['rh_doc'] = [l for l in (rh.__class__.__doc__ or '').splitlines() if '``' in l][:30]
        except Exception as e:
            out[p] = 'n/a ' + repr(e)[:100]
out['desc_doc'] = [l for l in (getattr(u, 'RuntimePartitionDesc', type('x', (), {})).__doc__ or '').splitlines() if '``' in l][:20]
out['hlodsetup_doc'] = [l for l in (getattr(u, 'RuntimePartitionHLODSetup', type('x', (), {})).__doc__ or '').splitlines() if '``' in l][:20]
RESULT = {'ok': True, **out}
