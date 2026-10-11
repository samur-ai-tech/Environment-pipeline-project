"""In-editor, read-only: properties of the converter's default HLOD layer assets (names, enum values, builder settings)."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
out = {}
for n in ('Instanced', 'Merged'):
    l = u.load_asset('/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/L_KarmeiYosef_31850349_34907601_4km_WPTrial_HLODLayer_' + n)
    d = {}
    for p in [x for x in dir(l) if not x.startswith('_') and not callable(getattr(l, x, None))]:
        try:
            d[p] = str(l.get_editor_property(p))[:160]
        except Exception:
            pass
    bs = l.get_editor_property('hlod_builder_settings') if 'hlod_builder_settings' in dir(l) else None
    if bs:
        d['_bs_class'] = bs.get_class().get_name()
        for p in [x for x in dir(bs) if not x.startswith('_') and not callable(getattr(bs, x, None))]:
            try:
                d['bs.' + p] = str(bs.get_editor_property(p))[:160]
            except Exception:
                pass
    out[n] = d
out['enums'] = [x for x in dir(u) if 'HLOD' in x][:60]
RESULT = {'ok': True, **out}
