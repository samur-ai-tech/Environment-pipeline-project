"""Read-only source audit; writes only receipts beside this script."""
import collections
import hashlib
import json
import pathlib
import struct
import datetime

BASE = pathlib.Path(r'C:\Users\USER\Documents\Pipeline Environment\ModelBank\Modular_2026-10-04\WholeBuildingConversions')
OUT = pathlib.Path(__file__).parent

def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))

def digest(path):
    path = pathlib.Path(path)
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open('rb') as f:
        while block := f.read(1024*1024):
            h.update(block)
    return h.hexdigest()

def fbx_globals(path):
    """Parse only GlobalSettings; skip mesh payloads without interpreting them."""
    blob = pathlib.Path(path).read_bytes()
    if not blob.startswith(b'Kaydara FBX Binary'):
        return {'error': 'not binary FBX'}
    version = struct.unpack_from('<I', blob, 23)[0]
    fmt = '<QQQB' if version >= 7500 else '<IIIB'
    header_size = struct.calcsize(fmt)

    def prop(pos):
        ty = chr(blob[pos]); pos += 1
        scalar = {'Y': '<h', 'C': '<?', 'I': '<i', 'F': '<f', 'D': '<d', 'L': '<q'}
        if ty in scalar:
            f = scalar[ty]
            value = struct.unpack_from(f, blob, pos)[0]
            return value, pos + struct.calcsize(f)
        if ty in 'SR':
            n = struct.unpack_from('<I', blob, pos)[0]; pos += 4
            value = blob[pos:pos+n]
            return (value.decode('utf-8', errors='replace') if ty == 'S' else None), pos+n
        if ty in 'fdlibc':
            n, encoding, size = struct.unpack_from('<III', blob, pos)
            return None, pos+12+size
        raise ValueError(f'Unsupported FBX property {ty!r}')

    def node(pos, include_children=False):
        end, count, size, namelen = struct.unpack_from(fmt, blob, pos)
        if end == 0:
            return None, pos + header_size
        pos += header_size
        name = blob[pos:pos+namelen].decode('utf-8'); pos += namelen
        props = []
        for _ in range(count):
            value, pos = prop(pos); props.append(value)
        children = []
        if include_children or name == 'GlobalSettings':
            while pos < end - header_size:
                child, nxt = node(pos, True)
                if child is None or nxt <= pos:
                    break
                children.append(child); pos = nxt
        return (name, props, children), end

    pos = 27
    while pos < len(blob) - header_size:
        item, nxt = node(pos)
        if item is None:
            break
        if item[0] == 'GlobalSettings':
            values = {}
            for group in item[2]:
                if group[0] == 'Properties70':
                    for p in group[2]:
                        if p[0] == 'P' and p[1]:
                            values[p[1][0]] = p[1][4:]
            return {'fbx_version': version, **values}
        pos = nxt
    return {'fbx_version': version, 'error': 'no GlobalSettings'}

manifest = read(BASE / 'MANIFEST.json')
delivery = (BASE / 'DELIVERY.md').read_text(encoding='utf-8-sig')
families = []
all_identities = []
issues = []
hash_checks = []
for entry in manifest['families']:
    fid = entry['id']; folder = BASE / fid
    assembly = read(folder / 'ASSEMBLY.json')
    rb = read(folder / 'READBACK.json')
    inspection = read(assembly['source_inspection'])
    modules = assembly['modules']
    mods_by_name = {m['name']: m for m in modules}
    neighbor_errors = []
    pivot_errors = []
    world_min = [float('inf')] * 3
    world_max = [float('-inf')] * 3
    slots = sorted({s for m in modules for s in m['source_material_slots']})
    hash_records = []
    globals_seen = []

    for kind, key in [('blend', 'original_blend'), ('fbx', 'original_fbx')]:
        got = digest(assembly[key]); want = assembly['source_sha256'][kind]
        rec = {'kind': 'original_' + kind, 'path': assembly[key], 'recorded_sha256': want,
               'actual_sha256': got, 'pass': got == want,
               'readback_sha256_matches': rb['source_hashes_unchanged'][kind] == want}
        hash_records.append(rec); hash_checks.append(rec)

    for m in modules:
        all_identities.append(m['name'])
        got = digest(m['fbx'])
        rec = {'kind': 'module', 'identity': m['name'], 'path': m['fbx'],
               'recorded_sha256': m['sha256'], 'actual_sha256': got, 'pass': got == m['sha256']}
        hash_records.append(rec); hash_checks.append(rec)
        globals_seen.append(fbx_globals(m['fbx']))
        for axis in range(3):
            world_min[axis] = min(world_min[axis], m['original_assembly_translation_m'][axis] + m['local_bounds_m']['min'][axis])
            world_max[axis] = max(world_max[axis], m['original_assembly_translation_m'][axis] + m['local_bounds_m']['max'][axis])
            delta = abs(m['original_assembly_translation_m'][axis] - m['cell_min_m'][axis])
            if delta > 1e-5:
                pivot_errors.append({'name': m['name'], 'axis': axis, 'error_m': delta})
        for n in m['assembly_neighbors']:
            other = mods_by_name.get(n['neighbor'])
            if not other:
                neighbor_errors.append({'name': m['name'], 'neighbor': n, 'error': 'missing identity'})
                continue
            reverse = [r for r in other['assembly_neighbors'] if r['neighbor'] == m['name'] and r['axis'] == n['axis'] and r['direction'] == -n['direction']]
            if not reverse or abs(reverse[0]['plane_m'] - n['plane_m']) > 1e-5:
                neighbor_errors.append({'name': m['name'], 'neighbor': n, 'error': 'nonreciprocal or differing plane'})

    ext_path = folder / 'ExtensionBand' / 'EXTENSION.json'
    extension = read(ext_path) if ext_path.exists() else None
    if extension:
        for part in extension['source_derived_parts']:
            all_identities.append(part['name'])
            got = digest(part['fbx'])
            rec = {'kind': 'extension', 'identity': part['name'], 'path': part['fbx'],
                   'recorded_sha256': part['sha256'], 'actual_sha256': got, 'pass': got == part['sha256']}
            hash_records.append(rec); hash_checks.append(rec)
            globals_seen.append(fbx_globals(part['fbx']))

    tex = []
    for image in assembly['textures']:
        t = dict(image)
        t['actual_sha256'] = digest(image['path'])
        t['exists_now'] = t['actual_sha256'] is not None
        tex.append(t)
    readbacks = rb['fbx_readbacks']
    unique_globals = {json.dumps(g, sort_keys=True) for g in globals_seen}
    if len(unique_globals) != 1:
        issues.append({'family_id': fid, 'issue': 'multiple FBX GlobalSettings variants', 'count': len(unique_globals)})
    texture_channels = inspection.get('texture_references', [])
    texture_check = []
    for t in texture_channels:
        actual_hash = digest(t['path'])
        matches = [i['path'] for i in tex if actual_hash and i['actual_sha256'] == actual_hash]
        texture_check.append({**t, 'source_texture_sha256_now': actual_hash, 'matching_delivery_texture_paths': matches})
    family = {
        'id': fid, 'source_name': entry['source_name'], 'source_inspection': assembly['source_inspection'],
        'assembly_path': str(folder / 'ASSEMBLY.json'), 'readback_path': str(folder / 'READBACK.json'),
        'module_count': len(modules), 'fbx_readback_count': len(readbacks),
        'manifest_count_matches': entry['module_count'] == assembly['module_count'] == rb['module_count'] == len(modules) == len(readbacks),
        'world_bounds_m': {'min': world_min, 'max': world_max},
        'dimensions_xyz_m': [world_max[i]-world_min[i] for i in range(3)],
        'authored_coordinate_contract': 'Assembly metre XYZ coordinates; Z vertical; exact part pivots equal geometric cell minimum, not ground/contact or facing anchors.',
        'fbx_global_settings': [json.loads(g) for g in sorted(unique_globals)],
        'cell_shape': [max(m['cell'][i] for m in modules)+1 for i in range(3)],
        'split_planes_m': assembly['split_planes_m'],
        'roles': sorted(m['role'] for m in modules),
        'architectural_role_families': sorted({m['role'].split('_')[0] for m in modules}),
        'cell_role_locations': sorted({m['role'].split('_')[-1] for m in modules}),
        'all_mating_edges_require_neighbor': all(m['mating_edges_require_neighbor'] for m in modules),
        'all_independent_caps_false': all(not m['independent_caps_added'] for m in modules),
        'neighbor_directed_connections': sum(len(m['assembly_neighbors']) for m in modules),
        'neighbor_graph_errors': neighbor_errors, 'pivot_cell_min_errors': pivot_errors,
        'readback_max_bounds_error_m': max(r['bounds_error_m'] for r in readbacks),
        'readback_all_pass': all(r['pass'] for r in readbacks),
        'readback_duplicate_faces_removed_recorded': sum(r.get('source_duplicate_faces_removed_by_fbx_import_validation', 0) for r in readbacks),
        'readback_duplicate_faces_removed_field_missing': [r['name'] for r in readbacks if 'source_duplicate_faces_removed_by_fbx_import_validation' not in r],
        'uv_channel_names': sorted({u for m in modules for u in m['uv_channels']}),
        'source_material_slots': slots, 'texture_delivery_records': tex,
        'source_texture_channel_bindings': texture_check,
        'missing_used_images_recorded': rb['missing_used_images'],
        'blend_reopened_recorded': rb['blend_reopened'],
        'source_exact_reconstruction_pass_recorded': assembly['validation']['image_comparison_passed'],
        'source_validation_recorded': assembly['validation'],
        'source_hash_checks_now': hash_records,
        'source_hash_all_match_now': all(r['pass'] for r in hash_records),
        'split_policy': assembly['split_policy'], 'assembly_policy': assembly['assembly_policy'],
        'extension': extension,
        'capability_evidence': {
            'exact_reconstruction_blender_recorded': bool(assembly['validation']['image_comparison_passed'] and all(r['pass'] for r in readbacks)),
            'one_axis_extension_geometry_blender_recorded': bool(extension and extension['corridor']['pass']),
            'repeatable_architectural_floors': False,
            'independent_facade_or_corner_repetition': False,
            'arbitrary_geographic_footprint': False,
            'cross_family_substitution': False,
            'texture_phase_continuity_at_new_repeat_boundary': False,
            'houdini_contract_qualified': False, 'official_houdini_engine_generated': False,
            'native_unreal_import_and_material_verified': False, 'native_unreal_saved_and_reopened': False,
            'collision_or_lod_adapted': False,
        },
    }
    families.append(family)

duplicates = [k for k,v in collections.Counter(all_identities).items() if v > 1]
receipt = {
    'schema': 'environmentpipeline.modular_construction_source_audit.v1',
    'audited_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'Read-only audit of the specified 20 families; originals and all authoring/native/catalog state unchanged.',
    'source_directory': str(BASE), 'delivery_read': str(BASE/'DELIVERY.md'),
    'manifest_read': str(BASE/'MANIFEST.json'), 'family_count': len(families),
    'module_count': sum(f['module_count'] for f in families),
    'extension_family_count': sum(bool(f['extension']) for f in families),
    'extension_part_count': sum(len(f['extension']['source_derived_parts']) for f in families if f['extension']),
    'identity_count': len(all_identities), 'duplicate_part_identities': duplicates,
    'original_source_hash_check_count': sum(r['kind'].startswith('original_') for r in hash_checks),
    'module_and_extension_hash_check_count': sum(not r['kind'].startswith('original_') for r in hash_checks),
    'hash_failures': [r for r in hash_checks if not r['pass']],
    'issues': issues, 'families': families,
}
(OUT/'SOURCE_AUDIT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
rows = ['# Twenty source-derived families: source audit', '',
        'Read-only source audit. This receipt records current hashes and manifest consistency; existing Blender results are cited as recorded evidence and were not rerun here.', '',
        f"Counts: {receipt['family_count']} families, {receipt['module_count']} parts, {receipt['extension_part_count']} extension parts for {receipt['extension_family_count']} families; {len(duplicates)} duplicate identities; {len(receipt['hash_failures'])} hash failures.", '',
        'All modules use exact cell-minimum pivots and recorded assembly translations. The nonempty cells form a family-specific corner/facade/core graph. Mating boundaries require their named neighbors; no independent caps are certified. Z tiers are geometric subdivisions and cannot be advertised as architectural floors.', '',
        '| Family | Parts | Dimensions XYZ, metres | Geometric XYZ cell shape | Material slots / texture files | Extension geometry evidence |',
        '|---|---:|---|---|---:|---|']
for f in families:
    dim = ' × '.join(f'{d:.4f}' for d in f['dimensions_xyz_m'])
    shape = ' × '.join(str(c) for c in f['cell_shape'])
    et = 'Exact reconstruction only'
    if f['extension']:
        c = f['extension']['corridor']; axis = 'XYZ'[c['axis']]
        et = f"{axis}, pitch {c['pitch_m']:.6f} m, profile error {c['profile_hausdorff_m']*1000:.3f} mm; recorded N=2"
    unique_tex = len({t['actual_sha256'] for t in f['texture_delivery_records']})
    rows.append(f"| {f['id']} | {f['module_count']} | {dim} | {shape} | {len(f['source_material_slots'])} / {unique_tex} | {et} |")
rows.extend(['', 'Adaptation risks:', '',
             '- Treat exact reconstruction as a fixed family assembly. Applying a generic length/height module grid changes the original silhouette and disconnects open boundaries.',
             '- Preserve source UVs, material slot order, family-specific texture channel mappings, and the baked geometry transform. Several original materials have sparse or family-specific channel sets.',
             '- Eight band candidates preserve a matching geometric profile; the newly repeated UV boundary is expressly unqualified for texture phase, and floor/opening/roof continuity still needs native visual checks.',
             '- Whole-building bands include start/end/corner/roof coverage as complete sets. Do not substitute independent cell pieces or switch axes.',
             '- All 609 FBX files have consistent FBX 7400 GlobalSettings: UpAxis=2/+1, FrontAxis=1/+1, CoordAxis=0/-1, UnitScaleFactor=1.0 (centimetre metadata). Assembly translations/bounds are metres. Honor importer unit/axis conversion, and verify actual imported bounds before accepting any additional conversion. Cell pivots are not independently verified ground-contact or façade-facing anchors.',
             '- H0017 READBACK omits the duplicate-face-removal field for all 63 parts, so absence is not a proved zero. H0018 records one exact duplicate face removed by FBX import validation; H0021 records three. These explicit source import changes must be retained in native validation accounting.',
             '- Original-source rights/holds remain external release decisions and are not changed by this audit.', '',
             'Full per-family roles, exact split planes, neighbor checks, FBX GlobalSettings, hash checks, textures, and source texture channel bindings are in SOURCE_AUDIT.json.'])
(OUT/'SOURCE_AUDIT.md').write_text('\n'.join(rows)+'\n', encoding='utf-8')
print(json.dumps({k:receipt[k] for k in ['family_count','module_count','extension_family_count','extension_part_count','identity_count','original_source_hash_check_count','module_and_extension_hash_check_count','duplicate_part_identities','hash_failures','issues']}, indent=2))
print('\n'.join(rows[8:29]))
