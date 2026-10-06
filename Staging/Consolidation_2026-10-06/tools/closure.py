import os, re, sys, json, collections
ROOT = r"C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Content"
SCR = r"C:/Users/USER/AppData/Local/Temp/claude/C--Users-USER-Documents-Unreal-Projects-Environmentpipeline/ff22121a-53df-4931-b47d-2e304b337189/scratchpad/refs"
pat = re.compile(rb'/Game/[A-Za-z0-9_/.\-]+')
pat16 = re.compile(rb'(?:/\x00G\x00a\x00m\x00e\x00/\x00)(?:[A-Za-z0-9_/.\-]\x00)+')
def pkg(p):
    p = p.split('.')[0].rstrip('/')
    return p
# index files
files = {}  # lower pkg -> (pkg, path, size)
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if f.endswith('.uasset') or f.endswith('.umap'):
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, ROOT).replace(os.sep, '/')
            p = '/Game/' + rel.rsplit('.', 1)[0]
            files[p.lower()] = (p, full, os.path.getsize(full))
numre = re.compile(r'^(.*)_(0|[1-9][0-9]{0,8})$')
basemap = {}
for k in files:
    m = numre.match(k)
    if m: basemap.setdefault(m.group(1), []).append(k)
def resolve(rl):
    # exact package, else FName-number-split fallback (conservative: all X_N candidates)
    if rl in files: return [rl]
    return basemap.get(rl, [])
def refs_of(full):
    size = os.path.getsize(full)
    with open(full, 'rb') as fh:
        data = fh.read(size if size < 64*1024*1024 else 16*1024*1024)
    out = set()
    for m in pat.findall(data): out.add(pkg(m.decode('ascii')))
    for m in pat16.findall(data): out.add(pkg(m.decode('utf-16-le')))
    return out
roots = set(l.strip() for l in open(os.path.join(SCR, 'all_direct.txt')) if l.strip())
direct = set(r.lower() for r in roots)
seen = set(); direct_res = set()
for r in direct:
    direct_res.update(resolve(r))
queue = list(direct_res)
missing = sorted(set(r for r in roots if not resolve(r.lower())))
edges_from = {}
while queue:
    k = queue.pop()
    if k in seen: continue
    seen.add(k)
    try:
        rs = refs_of(files[k][1])
    except Exception as e:
        print('ERR', k, e, file=sys.stderr); continue
    for r in rs:
        rl = r.lower()
        res = resolve(rl)
        for x in res:
            if x not in seen: queue.append(x)
        if not res and rl != k:
            edges_from.setdefault(rl, files[k][0])
json.dump({'closure': sorted(files[k][0] for k in seen),
           'missing_direct': missing,
           'missing_transitive': {a: b for a, b in sorted(edges_from.items())}}, open(os.path.join(SCR, 'closure.json'), 'w'), indent=0)
# summarize per top-level folder
tot = collections.Counter(); dref = collections.Counter(); tref = collections.Counter(); szt = collections.Counter(); szr = collections.Counter()
for k, (p, full, sz) in files.items():
    top = p.split('/')[2] if p.count('/') > 2 else '(root)'
    if top == 'Project':
        top = '/'.join(p.split('/')[2:5]) if p.count('/')>4 else '/'.join(p.split('/')[2:4])
    tot[top] += 1; szt[top] += sz
    if k in direct_res: dref[top] += 1
    if k in seen: tref[top] += 1; szr[top] += sz
with open(os.path.join(SCR, 'summary.tsv'), 'w') as o:
    o.write('folder\ttotal_pkgs\tdirect_ref\ttransitive_ref\tsizeMB_total\tsizeMB_ref\n')
    for t in sorted(tot):
        o.write(f"{t}\t{tot[t]}\t{dref[t]}\t{tref[t]}\t{szt[t]/1e6:.0f}\t{szr[t]/1e6:.0f}\n")
# unreferenced Project lists
with open(os.path.join(SCR, 'unref_direct.txt'), 'w') as o1, open(os.path.join(SCR, 'unref_transitive.txt'), 'w') as o2:
    for k in sorted(files):
        p, full, sz = files[k]
        if not p.startswith('/Game/Project/'): continue
        if k not in direct_res: o1.write(f"{p}\t{sz}\n")
        if k not in seen: o2.write(f"{p}\t{sz}\n")
print('files', len(files), 'closure', len(seen), 'direct_existing', len(direct_res), 'missing_direct', len(missing), 'missing_trans', len(edges_from))
