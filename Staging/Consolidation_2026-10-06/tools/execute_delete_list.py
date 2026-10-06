"""Execute one DeletePlan list with hard guards and a receipt. Usage:
  python execute_delete_list.py <list.txt> <receipt.tsv> [--apply] [--skip-regex RE] [--only-regex RE]
Without --apply it is a dry run. Every path must be absolute, inside one of ROOTS, exist, and not touch a MUST_STAY prefix
(unless it is a named carve-out). Receipt rows: path, kind, files, bytes, status."""
import os, re, sys, stat, shutil, time
ROOTS = ("C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/", "C:/Users/USER/Documents/Pipeline Environment/")
UP, PE = ROOTS
MUST_STAY = [UP+p for p in (
 "Content/Project/Areas/GazaShujaiya/", "Content/Project/Shared/ModelBank/", "Content/Project/Shared/Bank_ME", "Content/Project/Shared/SurfacePainting/Appearance_20261003/",
 "Content/Project/Shared/Landscape/", "Content/Project/Shared/Atmosphere/", "Content/Python/", "Config/", "Plugins/", "Environmentpipeline.uproject", "AGENTS.md",
 "Content/StarterContent/", "Content/MWLandscapeAutoMaterial/", "Content/Palms_Pack_01/", "Content/MOUT_Arabian/", "Content/ModularCourtyard/", "Content/WorldBLD/",
 "Staging/SystemCompletion_2026-10-04/", "Staging/ShujaiyaOrdinaryRun_2026-10-05/", "Staging/AppearanceRepair_2026-10-03/", "Staging/BankIntegration_2026-10-04/",
 "Staging/GroundPainting_2026-10-04/", "Staging/ManagedExecution_2026-10-02/", "Staging/RepairExecution_2026-10-03/", "Staging/ModularConstruction_2026-10-05/",
 "Staging/ManagedSystemsAstra_2026-10-04/", "Staging/ToolchainChecks/", "Staging/AssetBankOperator_2026-10-06/", "Staging/ReusableSky_2026-10-06/", "Staging/Consolidation_2026-10-06/",
 "Staging/Briefs_2026-10-06/", "Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/", "Staging/ModelBank/EDITOR_OWNER.txt", "Staging/ModelBank/ME/Sources",
 "Staging/CURRENT_STATE.md", "Staging/WORK_PLAN.md", "Staging/PROJECT_STATUS_2026-10-06.md")] + [PE+p for p in (
 "Houdini/GeoCity_city_v015_PermanentBank/GeoCity_city_v015_PermanentBank.hdalc", "Houdini/GeoCity_city_v015_PermanentBank/geocity_city_module.py",
 "Houdini/GeoCity_city_v015_PermanentBank/definition_receipt.json", "Houdini/GeoCity_city_v015_PermanentBank/revisions/20261005_procedural_ten_families_v003/",
 "Houdini/GeoCity_city_v015_PermanentBank/revisions/20261005_procedural_thirty_families_v004/", "Houdini/GeoCity_city_v015_4km/GeoCity_city_v015_4km.hdalc",
 "Houdini/GeoCity_city_v015_4km/geocity_city_module.py", "ModelBank/", "SourceData/", "Reference/", "AGENTS.md", "CONTRACT.md", "AREA.md")]
CARVE_OUTS = {UP+"Content/Project/Shared/ModelBank/HDA/GeoCity_city_v015_4km.uasset"}
HOLDS = ("H0013", "H0907", "H0051", "H0958", "H0094", "20261003T203730573110_212401627821")
def norm(p): return p.replace("\\", "/").rstrip("/")
def lp(p):  # plain Windows path; the long-path prefix only when the path is long
    w = os.path.abspath(p).replace('/', '\\')
    if len(w) < 240 or w.startswith('\\\\?\\'): return w
    return '\\\\?\\' + w
def touches_must_stay(p):
    pl = norm(p).lower()
    for m in MUST_STAY:
        ml = norm(m).lower()
        if pl == ml or pl.startswith(ml + "/") or ml.startswith(pl + "/"): return m
    return None
def measure(p):
    L = lp(p)
    if os.path.isfile(L): return "file", 1, os.path.getsize(L)
    n = b = 0; hold_hits = []
    for root, dirs, files in os.walk(L):
        for d in dirs:
            if any(h in d for h in HOLDS): hold_hits.append(os.path.join(root, d))
        for f in files:
            if any(h in f for h in HOLDS): hold_hits.append(os.path.join(root, f))
            fp = os.path.join(root, f); n += 1
            try: b += os.path.getsize(fp)
            except OSError: pass
    return ("dir", n, b) if not hold_hits else ("dir-HOLD:"+str(len(hold_hits)), n, b)
def rm(p):
    L = lp(p)
    def onerr(fn, path, exc):
        os.chmod(path, stat.S_IWRITE); fn(path)
    if os.path.isfile(L): os.chmod(L, stat.S_IWRITE); os.remove(L)
    else: shutil.rmtree(L, onerror=onerr)
def main():
    args = sys.argv[1:]; apply = "--apply" in args
    skip = only = None
    if "--skip-regex" in args: skip = re.compile(args[args.index("--skip-regex")+1])
    if "--only-regex" in args: only = re.compile(args[args.index("--only-regex")+1])
    lst, receipt = args[0], args[1]
    rows = []; tot_n = tot_b = 0; problems = 0
    for line in open(lst, encoding="utf-8"):
        p = norm(line.strip())
        if not p: continue
        status = "ok"
        if not p.startswith(ROOTS): status = "REFUSED-outside-roots"
        elif (skip and skip.search(p)) or (only and not only.search(p)): status = "skipped-by-filter"
        elif not (os.path.exists(p) or os.path.exists(lp(p))): status = "missing"
        elif p not in CARVE_OUTS and touches_must_stay(p): status = "REFUSED-must-stay:" + touches_must_stay(p)
        kind, n, b = measure(p) if status in ("ok",) else ("-", 0, 0)
        if kind.startswith("dir-HOLD"): status = "REFUSED-hold-inside"
        if status == "ok":
            tot_n += n; tot_b += b
            if apply:
                try: rm(p); status = "deleted" if not os.path.exists(lp(p)) else "FAILED-still-exists"
                except Exception as e: status = "FAILED:" + str(e)[:80]
        if status.startswith(("REFUSED", "FAILED")): problems += 1
        rows.append((p, kind, n, b, status))
    with open(receipt, "a", encoding="utf-8") as r:
        r.write("# %s list=%s apply=%s\n" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), lst, apply))
        for row in rows: r.write("\t".join(str(x) for x in row) + "\n")
    from collections import Counter
    c = Counter(r[4].split(":")[0] for r in rows)
    print("list=%s apply=%s entries=%d files=%d MB=%.0f statuses=%s problems=%d" % (os.path.basename(lst), apply, len(rows), tot_n, tot_b/1048576, dict(c), problems))
    for r in rows:
        if r[4].startswith(("REFUSED", "FAILED")): print("  ", r[4], r[0])
if __name__ == "__main__": main()
