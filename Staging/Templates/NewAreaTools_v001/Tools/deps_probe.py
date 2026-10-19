"""In-editor, read-only. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the Karmei Yosef tool. Asset-registry facts for deletion and export:
  - referencers of every package under ARGS.delete_folders and of ARGS.delete_packages that live OUTSIDE the delete set
    (must be empty before deleting);
  - the full dependency closure (hard + soft package references) of ARGS.roots, split into /Game content, plugin content
    and engine/script, written to receipts/DEPS_<label>.json with file paths and sizes.
No changes. ARGS: expected_pid, script_file (client), label, roots, delete_folders, delete_packages."""
import importlib.util, json, os
from collections import deque
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
assert os.getpid() == ARGS['expected_pid']
ar = u.AssetRegistryHelpers.get_asset_registry()
opt = u.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True,
                                        include_searchable_names=False, include_soft_management_references=False,
                                        include_hard_management_references=False)
dset = set(ARGS.get('delete_packages', []))
for f in ARGS.get('delete_folders', []):
    for a in ar.get_assets_by_path(f, recursive=True):
        dset.add(str(a.package_name))
outside = {}
for p in sorted(dset):
    refs = [str(r) for r in (ar.get_referencers(p, opt) or [])]
    bad = [r for r in refs if r not in dset and not r.startswith('/Game/__External') and not any(r.startswith(f + '/') for f in ARGS.get('delete_folders', []))]
    if bad:
        outside[p] = bad[:10]


def fpath(pkg):
    if not pkg.startswith('/Game/'):
        return None
    base = ROOT / ('Content' + pkg[5:])
    for ext in ('.umap', '.uasset'):
        if base.with_suffix(ext).exists() if False else Path(str(base) + ext).exists():
            return Path(str(base) + ext)
    return None


seen, q, scripts = set(), deque(ARGS['roots']), set()
while q:
    p = q.popleft()
    if p in seen:
        continue
    seen.add(p)
    for d in ar.get_dependencies(p, opt) or []:
        d = str(d)
        if d.startswith('/Script/'):
            scripts.add(d); continue
        if d in seen:
            continue
        q.append(d)
game, plugin, engine, missing = [], [], [], []
total = 0
for p in sorted(seen):
    if p.startswith('/Game/'):
        fp = fpath(p)
        if fp is None:
            missing.append(p); continue
        sz = fp.stat().st_size
        # bulk data sidecars (.ubulk/.uexp) next to the package
        extra = [x for x in (Path(str(fp)[:-6 if fp.suffix == '.uasset' else -5] + e) for e in ('.ubulk', '.uexp', '.uptnl')) if x.exists()]
        sz += sum(x.stat().st_size for x in extra)
        total += sz
        game.append([p, fp.relative_to(ROOT).as_posix(), sz, [x.relative_to(ROOT).as_posix() for x in extra]])
    elif p.startswith('/Engine/'):
        engine.append(p)
    else:
        plugin.append(p)
tops = {}
for p, f, sz, ex in game:
    k = '/'.join(p.split('/')[:3]) if not p.startswith('/Game/Project/') else '/'.join(p.split('/')[:5])
    tops.setdefault(k, [0, 0]); tops[k][0] += 1; tops[k][1] += sz
rec = {'label': ARGS['label'], 'roots': ARGS['roots'], 'delete_set_packages': len(dset), 'referenced_from_outside': outside,
       'game_packages': len(game), 'game_bytes': total, 'by_top_folder': {k: v for k, v in sorted(tops.items(), key=lambda kv: -kv[1][1])},
       'plugin_packages': sorted({'/'.join(p.split('/')[:2]) for p in plugin}), 'engine_packages': len(engine), 'missing_files': missing[:50], 'script_packages': sorted(scripts),
       'game': game}
(TASK / 'receipts' / ('DEPS_%s.json' % ARGS['label'])).write_text(json.dumps(rec, indent=1), encoding='utf-8')
RESULT = {'ok': True, **{k: v for k, v in rec.items() if k != 'game'}}
