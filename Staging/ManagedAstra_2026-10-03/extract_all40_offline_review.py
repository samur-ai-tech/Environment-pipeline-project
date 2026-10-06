"""Single-owner offline extraction of an immutable captured dataset. No Unreal imports."""
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCE = HERE / 'ALL40_INTERVALS_20261003T213901084762Z.json'
EXPECTED = 'b90d29863efb84d7afb18954c927cb4d361012117e71a540cecbd7966995d2fc'


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, separators=(',', ':'), allow_nan=False) + '\n', encoding='utf-8')


assert file_sha(SOURCE) == EXPECTED
module_path = ROOT / 'Content/Python/geocity_roadbld_grounding.py'
assert file_sha(module_path) == '62a8a28a03803fb845bafa2ce820b742a83cb35134b25cf192fcd532bbf6233d'
spec = importlib.util.spec_from_file_location('captured_grounding_offline', module_path)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
d = json.loads(SOURCE.read_text(encoding='utf-8-sig'))
affected = {x for gap in d['gaps'] for x in gap['same_source_components']}
pieces = {gap['piece_id'] for gap in d['gaps']}
actual = {s['component_path']: s for s in d['actual_bound_surfaces'] if s['component_path'] in affected}
preclip = {s['component_path']: s for s in d['affected_retained_preclip_grounded_arrays']}
records = {r['piece_id']: r for r in d['road_records']}
fields = {k: g.AsphaltField(s['points_cm'], s['triangles'], s['material_ids'], s['upward']) for k, s in preclip.items()}
gaps = []
for gap in d['gaps']:
    row = records[gap['piece_id']]
    segment = next(x for x in row['continuous_segments'] if x['segment'] == gap['segment'])
    a, b = segment['source_endpoints_cm']
    candidates = [(preclip[k], fields[k]) for k in gap['same_source_components'] if k in fields]
    before = g._physical_segment_intervals(a, b, gap['road_actor_path'], candidates)
    probes = [x for x in row['boundary_and_gap_probes'] if x['segment'] == gap['segment']]
    gaps.append(dict(gap, source_segment=segment, retained_preclip_asphalt_intervals=before,
                     captured_candidate_height_and_protected_probes=probes,
                     retained_preclip_covers_entire_segment=(len(before) == 1 and before[0][0] <= 1e-13 and before[0][1] >= 1-1e-13)))

geometry_keys = ['points_cm', 'triangles', 'material_ids', 'upward']
blobs = {}
refs = []
eligibility = []


def add(stage, surface):
    geom = {k: surface[k] for k in geometry_keys if k in surface}
    normals = surface.get('actual_face_normals_local_all_materials', surface.get('face_normals_local_all_materials'))
    if normals is not None:
        geom['face_normals_local_all_materials'] = normals
    if not geom:
        refs.append(dict(stage=stage, **surface))
        return
    key = g._sha(geom)
    blobs.setdefault(key, geom)
    meta = {k: v for k, v in surface.items() if k not in geometry_keys + ['actual_face_normals_local_all_materials', 'face_normals_local_all_materials']}
    refs.append(dict(stage=stage, geometry_blob_sha256=key, **meta))
    if stage == 'actual_bound':
        eligibility.append(dict(component_path=surface['component_path'], geometry_blob_sha256=key,
                                vertices=len(surface['points_cm']), triangles=len(surface['triangles']),
                                material_id_face_counts=dict(collections.Counter(surface['material_ids'])),
                                eligible_upward_asphalt_faces=sum(surface['upward']),
                                invalid_face_normals=sum(not n['valid'] for n in normals),
                                normal_z_over_025_faces=sum(n['valid'] and n['xyz'][2] > .25 for n in normals),
                                source_road_paths=surface['source_road_paths']))


for stage, surfaces in [('actual_bound', actual.values()), ('retained_preclip', preclip.values()),
                        ('original_native', d['affected_original_native_surfaces'])]:
    for surface in surfaces:
        add(stage, surface)
package = dict(schema='environmentpipeline.captured_affected_geometry.v1', source_receipt_sha256=EXPECTED,
               coordinate_note='points_cm are captured world coordinates; normals are captured mesh-local coordinates. Frames and provenance remain in surface references.',
               reconstruction='For each surface_reference merge geometry_blobs[geometry_blob_sha256] with reference metadata; face_normals_local_all_materials is normalized across stages. No precision rounding or triangle removal.',
               affected_piece_ids=sorted(pieces), surface_references=refs, geometry_blobs=blobs)
geometry_path = HERE / 'ALL40_AFFECTED_DEDUP_GEOMETRY_20261003T213901084762Z.json.gz'
with gzip.open(geometry_path, 'wt', encoding='utf-8', compresslevel=3) as stream:
    json.dump(package, stream, separators=(',', ':'), allow_nan=False)
summary_path = HERE / 'ALL40_OFFLINE_REVIEW_20261003T213901084762Z.json'
summary = dict(schema='environmentpipeline.all40_compact_offline_review.v1', source_receipt=str(SOURCE),
               source_receipt_sha256=EXPECTED, source_piece_count=40, source_segment_count=3337,
               station_samples=6711, gap_count=len(gaps), affected_piece_ids=sorted(pieces),
               preclip_full_segment_coverage_count=sum(x['retained_preclip_covers_entire_segment'] for x in gaps),
               affected_geometry_package=str(geometry_path), affected_geometry_package_sha256=file_sha(geometry_path),
               affected_geometry_package_bytes=geometry_path.stat().st_size,
               geometry_blob_count=len(blobs), surface_reference_count=len(refs),
               surface_counts_by_stage=dict(collections.Counter(x['stage'] for x in refs)),
               actual_surface_material_normal_eligibility=eligibility, gaps=gaps,
               source_rows=d['source_rows'], all40_road_records=d['road_records'],
               protected_source_partition=d['protected_source_partition'],
               protected_building_footprints_xz_m=d['plan']['protected_building_footprints_xz_m'],
               immutable_clipping_ledger_proof=d['immutable_clipping_ledger_proof'],
               height_issue_probes=d['height_issues'],
               interpretation='Offline replay using unchanged frozen helper and captured data. Retained preclip arrays are diagnostic evidence, not current bound geometry. Raw filter variants are not acceptance. No editor calls, source edits, new capture, Cook, save, or acceptance-gate changes.')
write(summary_path, summary)
handoff_path = HERE / 'TASK2_DELIVERY_RESULT.json'
handoff = json.loads(handoff_path.read_text(encoding='utf-8-sig'))
handoff['all40_exterior_interval_evidence']['offline_review'] = dict(path=str(summary_path), sha256=file_sha(summary_path), bytes=summary_path.stat().st_size,
    geometry_path=str(geometry_path), geometry_sha256=file_sha(geometry_path), geometry_bytes=geometry_path.stat().st_size,
    preclip_full_segment_coverage_count=summary['preclip_full_segment_coverage_count'], gap_count=len(gaps),
    surface_counts_by_stage=summary['surface_counts_by_stage'])
handoff_path.write_text(json.dumps(handoff, indent=2) + '\n', encoding='utf-8')
print(json.dumps(handoff['all40_exterior_interval_evidence']['offline_review'], indent=2))
