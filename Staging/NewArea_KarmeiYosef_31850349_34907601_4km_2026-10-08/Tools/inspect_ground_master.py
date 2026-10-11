"""In-editor, read-only: how the ground master's final colour is wired, the area MI's parent, and PCG texture classes.
ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
L = u.MaterialEditingLibrary
MI = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/BankIntegration_v015/Materials/MI_GeoCityGround_Auto'
mi = u.load_asset(MI)
parent = mi.get_editor_property('parent')
m = parent
r = {'mi_parent': parent.get_path_name(), 'use_material_attributes': m.get_editor_property('use_material_attributes'),
     'num_expressions': L.get_num_material_expressions(m)}
out = {}
for prop in ('MP_MATERIAL_ATTRIBUTES', 'MP_BASE_COLOR'):
    try:
        n = L.get_material_property_input_node(m, getattr(u.MaterialProperty, prop))
        out[prop] = None if n is None else {'node': n.get_name(), 'class': n.get_class().get_name(),
                                            'output': L.get_material_property_input_node_output_name(m, getattr(u.MaterialProperty, prop))}
        if n is not None:
            names = [str(x) for x in L.get_material_expression_input_names(n)]
            ins = L.get_inputs_for_material_expression(m, n)
            out[prop]['inputs'] = [(names[i] if i < len(names) else i, None if x is None else x.get_name() + ':' + x.get_class().get_name()) for i, x in enumerate(ins)][:30]
    except Exception as exc:
        out[prop] = repr(exc)[:200]
r['outputs'] = out
r['pcg_texture_classes'] = [n for n in dir(u) if n.startswith('PCG') and 'Texture' in n]
r['mel_methods'] = [n for n in dir(L) if 'connect' in n or 'input' in n.lower() or 'create' in n][:40]
RESULT = {'ok': True, **r}
