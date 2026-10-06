import os, re, json, collections
ROOT = r"C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Content"
S = r"C:/Users/USER/AppData/Local/Temp/claude/C--Users-USER-Documents-Unreal-Projects-Environmentpipeline/ff22121a-53df-4931-b47d-2e304b337189/scratchpad/refs/"
pat = re.compile(rb'/Game/[A-Za-z0-9_/.\-]+')
numre = re.compile(r'^(.*)_(0|[1-9][0-9]{0,8})$')
unref = [l.split('\t')[0] for l in open(S+'unref_transitive.txt') if l.strip()]
unl = {u.lower(): u for u in unref}
base = collections.defaultdict(list)
for u in unl:
    m = numre.match(u)
    if m: base[m.group(1)].append(u)
referrers = collections.defaultdict(set)
scan_roots = ['Project', 'Developers', '__ExternalActors__', '__ExternalObjects__', 'HoudiniEngine', 'RoadBLD_Generated']
for sr in scan_roots:
    for dp, dn, fn in os.walk(os.path.join(ROOT, sr)):
        for f in fn:
            if not f.endswith(('.uasset', '.umap')): continue
            full = os.path.join(dp, f)
            me = ('/Game/' + os.path.relpath(full, ROOT).replace(os.sep, '/').rsplit('.', 1)[0])
            sz = os.path.getsize(full)
            d = open(full, 'rb').read(min(sz, 64*1024*1024))
            for m in set(pat.findall(d)):
                p = m.decode().split('.')[0].rstrip('/').lower()
                tg = [p] if p in unl else base.get(p, [])
                for t in tg:
                    if t != me.lower(): referrers[t].add(me)
# also Stage1Kit/WorldBLD not scanned (vendor)
out = {}
cat = collections.Counter()
for u in unref:
    r = sorted(referrers.get(u.lower(), []))
    out[u] = r
    folder = '/'.join(u.split('/')[:-1])
    cat[(folder, 'zero_referrers' if not r else 'only_unref_or_hist_referrers')] += 1
json.dump(out, open(S+'reverse.json', 'w'), indent=0)
for (f, k), n in sorted(cat.items()):
    if 'ClippedGeometry/20261003T133607905511_14' in f and n == 1: continue
    print(n, k, f)
