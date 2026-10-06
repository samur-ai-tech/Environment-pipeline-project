# Read-only reference scan: which Content/Project packages, profiles and Python files contain each candidate package path.
import os, re, json, pathlib, sys
ROOT = pathlib.Path(r"C:/Users/USER/Documents/Unreal Projects/Environmentpipeline")
cands = []
def add_dir(d, exts=(".uasset", ".umap")):
    for p in sorted((ROOT/d).rglob("*")):
        if p.suffix in exts:
            rel = p.relative_to(ROOT/"Content").with_suffix("")
            cands.append(("/Game/" + rel.as_posix(), p))
add_dir("Content/Project/Shared/SurfacePainting")
add_dir("Content/Project/Shared/Recovery")
for d in ["Content/Project/Areas/GazaRimal/BankIntegration_v015/Materials",
          "Content/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials",
          "Content/Project/Areas/GazaRimal/BakedSurfacePainting",
          "Content/Project/Areas/GazaRimal/LayerInfos",
          "Content/Project/Areas/GazaRimal/BankIntegration_v015/GazaRimal/LayerInfos",
          "Content/Project/Areas/GazaShujaiya/BankIntegration_v015/GazaShujaiya/LayerInfos",
          "Content/Project/Areas/Iran_38196167_46086167_4km/BankIntegration_v015/Iran_38196167_46086167_4km/LayerInfos"]:
    add_dir(d)
cands.append(("/Game/Project/Areas/GazaRimal/L_GazaRimal_SurfacePainting_20261002", ROOT/"Content/Project/Areas/GazaRimal/L_GazaRimal_SurfacePainting_20261002.umap"))
# absent names to confirm absence of references
for absent in ["/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_Auto",
               "/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_MW",
               "/Game/Project/Shared/SurfacePainting/Auto_20261006/M_GeoCityAuto"]:
    cands.append((absent, None))
pats = {c: re.compile(re.escape(c.encode()) + rb"(?=[\x00.\"'/ ]|$)") for c, _ in cands}
scan = [p for p in (ROOT/"Content/Project").rglob("*") if p.suffix in (".uasset", ".umap")]
text = list((ROOT/"Staging/ModelBank").glob("*/AREA_PROFILE.json")) + list((ROOT/"Content/Python").glob("*.py"))
refs = {c: [] for c, _ in cands}
for p in scan + text:
    try:
        b = p.read_bytes()
    except Exception as e:
        print("ERR", p, e, file=sys.stderr); continue
    if b"/Game/Project/" not in b: continue
    for c, own in cands:
        if own is not None and p == own: continue
        if pats[c].search(b):
            refs[c].append(p.relative_to(ROOT).as_posix())
out = {"scanned_binaries": len(scan), "scanned_text": [t.relative_to(ROOT).as_posix() for t in text], "refs": refs,
       "exists": {c: (own is not None and own.exists()) for c, own in cands}}
json.dump(out, open(sys.argv[1], "w"), indent=1)
for c, _ in cands:
    r = refs[c]
    print(("%3d" % len(r)), c, "<-", "; ".join(x.split("/")[-1] for x in r[:6]) + (" ..." if len(r) > 6 else ""))
