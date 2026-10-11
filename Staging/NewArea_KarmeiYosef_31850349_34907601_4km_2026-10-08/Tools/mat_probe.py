"""In-editor, read-only: materials of the given meshes -> parent chain, blend mode, opacity mask clip value, two-sided,
texture parameters (name, texture, sRGB, compression, alpha-coverage flags). ARGS: expected_pid, meshes."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
L = u.MaterialEditingLibrary
out = {}
for p in ARGS['meshes']:
    m = u.load_asset(p); mats = []
    for i in range(len(m.get_editor_property('static_materials'))):
        mi = m.get_material(i)
        if not mi:
            continue
        base = mi.get_base_material()
        info = {'slot': i, 'mi': mi.get_path_name().split('.')[0], 'base': base.get_path_name().split('.')[0],
                'blend': str(base.get_editor_property('blend_mode')).split('.')[-1].split(':')[0],
                'clip': base.get_editor_property('opacity_mask_clip_value'), 'two_sided': base.get_editor_property('two_sided'),
                'tex': {}}
        try:
            for n in L.get_texture_parameter_names(mi) if isinstance(mi, u.MaterialInstance) else []:
                t = L.get_material_instance_texture_parameter_value(mi, n)
                if t:
                    d = {'tex': t.get_path_name().split('.')[0]}
                    for prop in ('do_scale_mips_for_alpha_coverage', 'alpha_coverage_thresholds', 'compression_settings', 'mip_gen_settings'):
                        try:
                            d[prop] = str(t.get_editor_property(prop))
                        except Exception:
                            pass
                    info['tex'][str(n)] = d
        except Exception as exc:
            info['tex_error'] = repr(exc)[:100]
        try:
            ov = mi.get_editor_property('base_property_overrides')
            info['override_clip'] = [ov.get_editor_property('override_opacity_mask_clip_value'), ov.get_editor_property('opacity_mask_clip_value')]
        except Exception:
            pass
        mats.append(info)
    out[p.rsplit('/', 1)[1]] = mats
RESULT = {'ok': True, 'meshes': out}
