"""Read the two missing wheel-contact source contracts; never save source scenes."""
import hashlib
import itertools
import json
from pathlib import Path
import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
ARCHIVE = Path('C:/Users/USER/Documents/Unreal Projects/GIS_WorldBLD/SourceData/ModelBanks_Archive/Unreal_Model_Library_2026-09-24/Sources/Hergel')
jobs = json.loads((HERE.parent / 'READY_JOBS.json').read_text(encoding='utf-8'))['rows']
results = []
for number in ['0039', '0043']:
    job = next(j for j in jobs if '__SM_H' + number + '_' in j['asset_id'])
    report = json.loads((ARCHIVE / 'Reports' / (number + '.json')).read_text(encoding='utf-8'))
    path = ARCHIVE / report['blend']
    original_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False, use_scripts=False)
    scale = bpy.context.scene.unit_settings.scale_length * 100
    all_vertices, objects = [], []
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH' or obj.name.upper().startswith(('UCX_', 'UBX_', 'USP_', 'UCP_')):
            continue
        coords = np.empty(len(obj.data.vertices) * 3, dtype=np.float64)
        obj.data.vertices.foreach_get('co', coords)
        coords = coords.reshape(-1, 3)
        matrix = np.asarray(obj.matrix_world)
        vertices = (coords @ matrix[:3, :3].T + matrix[:3, 3]) * scale
        all_vertices.append(vertices)
        objects.append({'name': obj.name, 'vertices': len(vertices), 'triangles': sum(len(p.vertices)-2 for p in obj.data.polygons),
                        'bounds_cm': {'min': vertices.min(axis=0).tolist(), 'max': vertices.max(axis=0).tolist()}})
    vertices = np.concatenate(all_vertices)
    low, high = vertices.min(axis=0), vertices.max(axis=0)
    wanted = job['configuration_payload']['bounds_cm']
    transforms = []
    for permutation in itertools.permutations(range(3)):
        for signs in itertools.product((-1, 1), repeat=3):
            a, b = low[list(permutation)] * signs, high[list(permutation)] * signs
            error = max(np.max(np.abs(np.minimum(a,b)-wanted['min'])), np.max(np.abs(np.maximum(a,b)-wanted['max'])))
            if error < 0.006:
                transforms.append({'native_axis_from_source': list(permutation), 'sign': list(signs), 'bounds_error_cm': float(error)})
    assert len(transforms) == 1, ('source_native_axes_not_unique', job['asset_id'], transforms)
    transform = transforms[0]
    native = vertices[:, transform['native_axis_from_source']] * transform['sign']
    zmin = float(native[:,2].min())
    bands = []
    for lower, upper in [(zmin, zmin+0.05), (zmin, zmin+0.25), (zmin, zmin+1), (-0.05,0.05), (-1,1), (zmin,zmin+3)]:
        selected = native[(native[:,2]>=lower-1e-6)&(native[:,2]<=upper+1e-6)]
        bands.append({'z_min_cm': lower, 'z_max_cm': upper, 'vertices': len(selected),
                      'xy_min': selected[:,:2].min(axis=0).tolist() if len(selected) else None,
                      'xy_max': selected[:,:2].max(axis=0).tolist() if len(selected) else None})
    near = native[native[:,2] <= zmin+3]
    levels = []
    for z in sorted(set(np.round(near[:,2], 2))):
        selected = near[np.abs(np.round(near[:,2],2)-z)<0.0001]
        levels.append({'z_cm_rounded': float(z), 'vertices': len(selected),
                       'xy_min': selected[:,:2].min(axis=0).tolist(), 'xy_max': selected[:,:2].max(axis=0).tolist()})
    results.append({'asset_id': job['asset_id'], 'native_path': job['object_path'], 'native_package_sha256': job['native_identity']['sha256'],
                    'source_blend': str(path), 'source_sha256': original_sha, 'objects': objects,
                    'source_bounds_cm': {'min': low.tolist(), 'max': high.tolist()},
                    'unique_source_native_axes': transform, 'native_coordinate_contact_bands': bands, 'lowest_3cm_levels': levels,
                    'source_files_unchanged': hashlib.sha256(path.read_bytes()).hexdigest()==original_sha,
                    'native_readback_performed': False, 'source_geometry_changed': False})
    assert results[-1]['source_files_unchanged']
    (HERE / 'VEHICLE_SOURCE_CONTACT.json').write_text(json.dumps({'rows': results}, indent=2)+'\n', encoding='utf-8')
    print('RETAINED_SOURCE_CONTACT', job['asset_id'], 'minimum', zmin, 'bands', [(b['vertices'],b['xy_min'],b['xy_max']) for b in bands[:3]], flush=True)
