"""Read-only: compare project copies of the two Fab packs against the Epic Launcher VaultCache originals (SHA1)."""
import os, hashlib, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uasset_offline import Pkg

PAIRS = [('C:/ProgramData/Epic/EpicGamesLauncher/VaultCache/MWLandsc0bb389159dceV3/data',
          'C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Content/MWLandscapeAutoMaterial'),
         ('C:/ProgramData/Epic/EpicGamesLauncher/VaultCache/HighPoly7a52ca673258V1/data',
          'C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Content/HighPoly_Tree_Model')]


def sha1(f):
    m = hashlib.sha1()
    with open(f, 'rb') as fh:
        for c in iter(lambda: fh.read(1 << 22), b''):
            m.update(c)
    return m.hexdigest()


def norm(x):
    return x.replace(os.sep, '/')


for v, p in PAIRS:
    rels = {}
    for dp, dn, fn in os.walk(v):
        for f in fn:
            full = norm(os.path.join(dp, f)); k = full.find('/Content/')
            rels[full[k + 9:] if k >= 0 else full] = full
    pf = {}
    for dp, dn, fn in os.walk(p):
        for f in fn:
            full = norm(os.path.join(dp, f))
            pf[norm(os.path.relpath(full, os.path.dirname(p)))] = full
    same = 0; diff = []; extra = []
    for r, full in sorted(pf.items()):
        if r in rels:
            if os.path.getsize(full) == os.path.getsize(rels[r]) and sha1(full) == sha1(rels[r]):
                same += 1
            else:
                diff.append(r)
        else:
            extra.append(r)
    missing = [r for r in rels if r not in pf]
    print(os.path.basename(p), 'identical=%d' % same, 'diff=%s' % diff, 'project_only=%s' % extra, 'vault_only=%s' % missing[:20])

f = 'C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Content/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural.uasset'
if os.path.exists(f):
    pk = Pkg(f); print('M_SurfaceBank_Natural saved_by', pk.saved_by, 'ue5', pk.ue5)
