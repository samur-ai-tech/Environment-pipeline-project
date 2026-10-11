"""In-editor (diagnosis, Karmei Yosef operator): override the opacity-mask clip value on area-owned MI copies and match the
alpha-coverage threshold of their area-owned textures. ARGS: expected_pid, mis [paths under the clone], clip (float)."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
L = u.MaterialEditingLibrary
T = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/'
out = {}
for p in ARGS['mis']:
    assert p.startswith(T), p
    mi = u.load_asset(p)
    ov = mi.get_editor_property('base_property_overrides')
    ov.set_editor_property('override_opacity_mask_clip_value', True); ov.set_editor_property('opacity_mask_clip_value', float(ARGS['clip']))
    mi.set_editor_property('base_property_overrides', ov)
    texs = []
    for pn in L.get_texture_parameter_names(mi):
        t = L.get_material_instance_texture_parameter_value(mi, pn)
        if t and t.get_path_name().startswith(T) and t.get_editor_property('do_scale_mips_for_alpha_coverage'):
            t.set_editor_property('alpha_coverage_thresholds', u.Vector4(0.0, 0.0, 0.0, float(ARGS['clip']))); texs.append(t.get_name())
    L.update_material_instance(mi)
    o = mi.get_editor_property('base_property_overrides')
    out[p.rsplit('/', 1)[1]] = {'override': [o.get_editor_property('override_opacity_mask_clip_value'), o.get_editor_property('opacity_mask_clip_value')], 'textures': texs}
RESULT = {'ok': True, 'mis': out}
