"""Read-only fit candidates from retained pads; this does not authorize placement."""
import ast
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
BASE = Path('C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank/geocity_city_module.py')

def ref(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def main():
    # Use the retained source's actual containment predicate, without importing
    # hou, cooking a graph, or substituting a second construction implementation.
    names = {'_assembly_cross', '_assembly_sub', '_assembly_area', '_assembly_on_segment',
             '_assembly_intersects', '_assembly_inside', '_assembly_polygon_contained'}
    module = ast.parse(BASE.read_text(encoding='utf-8'))
    definitions = [n for n in module.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in definitions} == names
    scope = {'math': math}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(BASE), 'exec'), scope)
    contains = scope['_assembly_polygon_contained']
    source_audit = HERE.parent / 'SourceAudit/SOURCE_AUDIT.json'
    families = load(source_audit)['families']
    pads, provenance = [], []
    for folder in ('PermanentIntegration_2026-10-02', 'GazaShujaiyaIntegration_2026-10-02'):
        location = PROJECT / 'Staging/ModelBank' / folder
        profile_path = location / 'AREA_PROFILE.json'
        receipt_path = location / 'HDA_CATALOG_RECEIPT.json'
        profile = load(profile_path)
        package_path = Path(profile['source'])
        package = load(package_path)
        xml_entry = next(f for f in package['files'] if f['role'] == 'osm_xml')
        xml_path = package_path.parent / xml_entry['path']
        assert ref(xml_path)['sha256'] == xml_entry['sha256'], 'source_osm_changed'
        root = ET.parse(xml_path).getroot()
        nodes = {n.attrib['id']: (float(n.attrib['lon']), float(n.attrib['lat'])) for n in root.findall('node')}
        ways = {w.attrib['id']: w for w in root.findall('way')}
        records = load(receipt_path).get('native_building_assembly_records', [])
        frame = {**package['local_frame'], **package['origin']}
        for record in records:
            osm_id = str(record['source_feature']['osm_id'])
            way = ways[osm_id]
            references = [n.attrib['ref'] for n in way.findall('nd')]
            ring = record['footprint_xz_m']
            projected = [((nodes[n][0]-frame['lon0'])*frame['Mlon_m_per_deg'],
                          -(nodes[n][1]-frame['lat0'])*frame['Mlat_m_per_deg']) for n in references]
            error = max(min(math.dist(p, q) for q in projected) for p in ring)
            assert error < 0.01, ('retained_pad_original_source_mismatch', osm_id, error)
            tags = {t.attrib['k']: t.attrib['v'] for t in way.findall('tag')}
            pads.append({'area_id': profile['map'].split('/')[4], 'osm_id': osm_id,
                'ring_xz_m': ring, 'base_m': record['base_m'], 'height_m': record['height_m'],
                'height_rule': record['height_rule'], 'building_tag': tags.get('building', ''),
                'building_use_tag': tags.get('building:use'), 'source_projection_error_m': error})
        provenance.append({'profile': ref(profile_path), 'source_package': ref(package_path),
                           'source_osm': ref(xml_path), 'retained_hda_receipt': ref(receipt_path)})
    results = []
    for family in families:
        width, depth, height = family['dimensions_xyz_m']
        fits = []
        for pad in pads:
            ring = pad['ring_xz_m']
            area = abs(scope['_assembly_area'](ring))
            coverage = width * depth / area
            if coverage < 0.45 or coverage > 1.0 + 1e-7:
                continue
            if pad['height_rule'] != 'seeded_rule_not_measured' and abs(height-pad['height_m']) > 0.04:
                continue
            # Only unknown or explicitly residential source-use candidates are
            # listed. This is not a certification of this model's building use.
            if pad['building_tag'] not in ('yes', 'house', 'residential', 'apartments', 'detached', 'terrace'):
                continue
            center = [sum(p[i] for p in ring)/len(ring) for i in (0, 1)]
            longest = max(range(len(ring)), key=lambda i: (math.dist(ring[i], ring[(i+1)%len(ring)]), -i))
            edge = [ring[(longest+1)%len(ring)][i]-ring[longest][i] for i in (0, 1)]
            yaw_base = math.degrees(math.atan2(edge[1], edge[0]))
            for offset in (0, 90, 180, 270):
                yaw = yaw_base + offset
                angle = math.radians(yaw)
                c, s = math.cos(angle), math.sin(angle)
                corners = [(center[0]+c*x-s*z, center[1]+s*x+c*z) for x, z in
                           ((-width/2, -depth/2), (width/2, -depth/2), (width/2, depth/2), (-width/2, depth/2))]
                if contains(corners, ring):
                    fits.append({**{k: v for k, v in pad.items() if k != 'ring_xz_m'},
                        'coverage_ratio': coverage, 'rigid_yaw_degrees': yaw,
                        'source_height_difference_m': height-pad['height_m']})
                    break
        fits.sort(key=lambda f: (abs(f['source_height_difference_m']), abs(0.85-f['coverage_ratio']), f['area_id'], f['osm_id']))
        results.append({'id': family['id'], 'family_id': 'source_derived_modular.'+family['id']+'.v001',
            'native_source_dimensions_m': [width, depth, height], 'fit_candidate_count': len(fits),
            'first_candidates': fits[:12], 'capability': 'exact_reconstruction_N1_only',
            'native_basis_or_appearance_qualified': False})
    report = {'schema': 'environmentpipeline.source_family_preliminary_qualification_fit.v1',
        'scope': 'Read-only source-bound geometry fit candidates in existing unmatched retained pads',
        'source_audit': ref(source_audit), 'retained_module': ref(BASE), 'provenance': provenance,
        'retained_unmatched_pad_count': len(pads), 'families': results,
        'limitations': ['Retained HDA receipts are historical geometry baselines, not fresh native map readback.',
            'Actual current final pads, terrain support, native basis/material closure and qualified use must be verified.',
            'No source IDs are assigned, no placement is authorized, no held family enabled by this receipt.',
            'Native height is preserved; geometric tiers are not certified occupied floors.'],
        'native_authoring': False, 'selection_authorized': False}
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE/'QUALIFICATION_FIT_CANDIDATES.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'pads': len(pads), 'families': [{'id': f['id'], 'fits': f['fit_candidate_count']} for f in results]}))

if __name__ == '__main__':
    main()
