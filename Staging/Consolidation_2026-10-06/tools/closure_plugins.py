import os, re, json, collections
PROJ = r"C:/Users/USER/Documents/Unreal Projects/Environmentpipeline"
S = r"C:/Users/USER/AppData/Local/Temp/claude/C--Users-USER-Documents-Unreal-Projects-Environmentpipeline/ff22121a-53df-4931-b47d-2e304b337189/scratchpad/refs/"
mounts = {'Game': PROJ + '/Content'}
for plug in os.listdir(PROJ + '/Plugins'):
    c = os.path.join(PROJ, 'Plugins', plug, 'Content')
    if os.path.isdir(c): mounts[plug] = c
pat = re.compile(rb'(?<![A-Za-z0-9_/.\-])/(' + b'|'.join(m.encode() for m in mounts) + rb')/[A-Za-z0-9_/.\-]+')
files = {}
for m, root in mounts.items():
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if f.endswith(('.uasset', '.umap')):
                full = os.path.join(dp, f)
                p = '/' + m + '/' + os.path.relpath(full, root).replace(os.sep, '/').rsplit('.', 1)[0]
                files[p.lower()] = (p, full)
numre = re.compile(r'^(.*)_(0|[1-9][0-9]{0,8})$')
base = collections.defaultdict(list)
for k in files:
    mm = numre.match(k)
    if mm: base[mm.group(1)].append(k)
def resolve(r): return [r] if r in files else base.get(r, [])
def refs(full):
    sz = os.path.getsize(full)
    d = open(full, 'rb').read(sz if sz < 64*1024*1024 else 16*1024*1024)
    return set(m.group(0).decode().split('.')[0].rstrip('/').lower() for m in pat.finditer(d))
roots = set(l.strip().lower() for l in open(S + 'all_direct.txt') if l.strip())
live_maps = ['/game/project/areas/gazashujaiya/bankintegration_v015/l_gazashujaiya_bankintegration', '/game/project/areas/gazarimal/bankintegration_v015/l_gazarimal_bankintegration', '/game/project/areas/iran_38196167_46086167_4km/bankintegration_v015/l_iran_38196167_46086167_4km']
seen = set(); q = []
for r in roots | set(live_maps): q += resolve(r)
parent = {}
while q:
    k = q.pop()
    if k in seen: continue
    seen.add(k)
    for r in refs(files[k][1]):
        for x in resolve(r):
            if x not in seen:
                parent.setdefault(x, k); q.append(x)
old = set(p.lower() for p in json.load(open(S + 'closure.json'))['closure'])
new_game = sorted(files[k][0] for k in seen if k.startswith('/game/') and k not in old)
c = collections.Counter(p.split('/')[2] for p in new_game)
print('plugin-aware closure size', len(seen), '| plugin pkgs reached', sum(1 for k in seen if not k.startswith('/game/')))
print('additional /Game packages reached only via plugin content:', len(new_game), dict(c))
for p in new_game[:30]:
    chain = []; k = p.lower()
    while k in parent and len(chain) < 4: k = parent[k]; chain.append(files[k][0])
    print('  ', p, '<-', ' <- '.join(chain))
json.dump({'new_game': new_game}, open(S + 'closure_plugins.json', 'w'), indent=0)
