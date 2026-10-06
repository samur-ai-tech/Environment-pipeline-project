import json, re, collections
S = r"C:/Users/USER/AppData/Local/Temp/claude/C--Users-USER-Documents-Unreal-Projects-Environmentpipeline/ff22121a-53df-4931-b47d-2e304b337189/scratchpad/refs/"
direct = [l.rstrip('\n').split('\t') for l in open(S+'unref_direct.txt') if l.strip()]
trans = set(l.split('\t')[0] for l in open(S+'unref_transitive.txt') if l.strip())
rev = json.load(open(S+'reverse.json'))
def key(p):
    parts = p.split('/')
    if '/RoadBLD/ClippedGeometry/' in p:
        i = parts.index('ClippedGeometry'); return '/'.join(parts[:i+1]) + '/*'
    if '/Prepared/External/' in p: return '/Game/Project/Shared/ModelBank/Prepared/External/*'
    m = re.search(r'/Prepared/Modular/(H\d+)/', p)
    if m: return '/Game/Project/Shared/ModelBank/Prepared/Modular/H*/' + '/'.join(parts[parts.index(m.group(1))+1:-1])
    return '/'.join(parts[:-1])
g = collections.OrderedDict()
for p, sz in sorted(direct):
    g.setdefault(key(p), []).append((p, int(sz)))
out = []
out.append('| Group (folder) | Direct-unreferenced | of which also transitively unreachable | MB (transitively unreachable) |')
out.append('|---|---:|---:|---:|')
tot = [0,0,0.0]
for k, items in g.items():
    t = [x for x in items if x[0] in trans]
    mb = sum(x[1] for x in t)/1e6
    tot[0]+=len(items); tot[1]+=len(t); tot[2]+=mb
    out.append(f'| `{k}` | {len(items)} | {len(t)} | {mb:.1f} |')
out.append(f'| **Total** | **{tot[0]}** | **{tot[1]}** | **{tot[2]:.1f}** |')
open(S+'md_groups_table.md','w').write('\n'.join(out)+'\n')
# listing of transitively-unreachable, grouped, cap 40
lst = []
gt = collections.OrderedDict()
for p, sz in sorted(direct):
    if p in trans: gt.setdefault(key(p), []).append((p, int(sz)))
for k, items in gt.items():
    zero = sum(1 for p,_ in items if not rev.get(p))
    lst.append(f'\n**`{k}`** — {len(items)} packages, {sum(s for _,s in items)/1e6:.1f} MB; {zero} with zero referrers anywhere in Content/Project+Developers, {len(items)-zero} referenced only by other non-LIVE packages')
    for p, sz in items[:40]:
        r = rev.get(p, [])
        rs = (' — referrers: ' + ', '.join('`'+x.split('/')[-1]+'`' for x in r[:3]) + (' …' if len(r)>3 else '')) if r else ''
        lst.append(f'- `{p.split("/")[-1]}` ({sz/1e6:.2f} MB){rs}')
    if len(items) > 40: lst.append(f'- … {len(items)-40} more (not listed)')
open(S+'md_unref_list.md','w').write('\n'.join(lst)+'\n')
print(tot, len(g), len(gt))
