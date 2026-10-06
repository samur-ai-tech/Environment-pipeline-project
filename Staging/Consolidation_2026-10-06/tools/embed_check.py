import hashlib, glob, os, sys
H = r"C:/Users/USER/Documents/Pipeline Environment/Houdini"
P = r"C:/Users/USER/Documents/Unreal Projects/Environmentpipeline"
cands = []
for pat in ["GeoCity_city_v015_*/**/*.hdalc", "GeoCity_city_v0*/*.hdalc", "GeoCity_city_v0*/**/*.hdalc", "CityProof/*.hdalc"]:
    cands += glob.glob(os.path.join(H, pat), recursive=True)
cands += glob.glob(P + "/Staging/**/*.hdalc", recursive=True)
cands = sorted(set(os.path.normpath(c) for c in cands))
cdata = {}
for c in cands:
    with open(c, "rb") as f: cdata[c] = f.read()
natives = sys.argv[1:]
for n in natives:
    with open(n, "rb") as f: b = f.read()
    idx = b.find(b"INDX\x00")
    hits = [c for c, d in cdata.items() if d in b]
    emb = None
    print("==", os.path.relpath(n, P), "sha", hashlib.sha256(b).hexdigest()[:8], "size", len(b), "INDX@", idx)
    if idx >= 0:
        # try to locate embedded length: 4 bytes before INDX in UE TArray<uint8> serialization (int32 count)
        ln = int.from_bytes(b[idx-4:idx], "little", signed=True)
        if 0 < ln <= len(b) - idx:
            emb = b[idx:idx+ln]
            print("   embedded_len", ln, "embedded_sha256", hashlib.sha256(emb).hexdigest())
    for h in hits:
        print("   EXACT_EMBED_MATCH:", os.path.relpath(h, H) if h.startswith(os.path.normpath(H)) else h)
    if not hits: print("   no canonical hdalc embedded byte-identical")
