"""Split already extracted offline geometry into bounded review packages."""
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAMP = '20261003T213901084762Z'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


original = HERE / ('ALL40_AFFECTED_DEDUP_GEOMETRY_' + STAMP + '.json.gz')
assert sha(original) == '4f5bf006ff935d237c03fa4d44344430609484b158314df59ac3d17a6169167e'
with gzip.open(original, 'rt', encoding='utf-8') as f:
    package = json.load(f)
packages = {}
for stage in ['actual_bound', 'retained_preclip', 'original_native']:
    refs = [r for r in package['surface_references'] if r['stage'] == stage]
    keys = {r['geometry_blob_sha256'] for r in refs if 'geometry_blob_sha256' in r}
    subset = {k: v for k, v in package.items() if k not in ['surface_references', 'geometry_blobs']}
    subset.update(stage=stage, surface_references=refs, geometry_blobs={k: package['geometry_blobs'][k] for k in sorted(keys)})
    path = HERE / ('ALL40_AFFECTED_' + stage.upper() + '_' + STAMP + '.json.gz')
    with gzip.open(path, 'wt', encoding='utf-8', compresslevel=6) as f:
        json.dump(subset, f, separators=(',', ':'), allow_nan=False)
    packages[stage] = dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size, components=len(refs), geometry_blobs=len(keys))
summary_path = HERE / ('ALL40_OFFLINE_REVIEW_' + STAMP + '.json')
summary = json.loads(summary_path.read_text())
for gap in summary['gaps']:
    lo, hi = gap['interval']
    gap['retained_preclip_fully_covers_current_gap'] = any(a <= lo + 1e-13 and b >= hi - 1e-13 for a, b in gap['retained_preclip_asphalt_intervals'])
summary['current_gap_preclip_comparison'] = dict(fully_covered= sum(g['retained_preclip_fully_covers_current_gap'] for g in summary['gaps']), not_fully_covered=sum(not g['retained_preclip_fully_covers_current_gap'] for g in summary['gaps']))
summary['review_geometry_packages'] = packages
summary['preferred_review_input'] = 'This 5 MB summary contains all40 source-segment and station results. Read actual_bound package for the affected58 current components; load retained_preclip/original_native packages only when that comparison is needed. Each package independently deduplicates geometry by content hash and contains complete arrays with no rounding.'
summary_path.write_text(json.dumps(summary, separators=(',', ':'), allow_nan=False) + '\n', encoding='utf-8')
handoff_path = HERE / 'TASK2_DELIVERY_RESULT.json'
h = json.loads(handoff_path.read_text(encoding='utf-8-sig'))
entry = h['all40_exterior_interval_evidence']['offline_review']
entry.update(sha256=sha(summary_path), bytes=summary_path.stat().st_size, review_geometry_packages=packages, current_gap_preclip_comparison=summary['current_gap_preclip_comparison'])
handoff_path.write_text(json.dumps(h, indent=2) + '\n', encoding='utf-8')
print(json.dumps(entry, indent=2))
