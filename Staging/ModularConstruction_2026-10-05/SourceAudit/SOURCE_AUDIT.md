# Twenty source-derived families: source audit

Read-only source audit. This receipt records current hashes and manifest consistency; existing Blender results are cited as recorded evidence and were not rerun here.

Counts: 20 families, 585 parts, 24 extension parts for 8 families; 0 duplicate identities; 0 hash failures.

All modules use exact cell-minimum pivots and recorded assembly translations. The nonempty cells form a family-specific corner/facade/core graph. Mating boundaries require their named neighbors; no independent caps are certified. Z tiers are geometric subdivisions and cannot be advertised as architectural floors.

| Family | Parts | Dimensions XYZ, metres | Geometric XYZ cell shape | Material slots / texture files | Extension geometry evidence |
|---|---:|---|---|---:|---|
| H0017 | 63 | 14.3681 × 24.3003 × 30.1631 | 3 × 3 × 7 | 9 / 17 | Exact reconstruction only |
| H0018 | 60 | 17.3497 × 18.3658 × 27.6904 | 3 × 3 × 7 | 4 / 12 | Exact reconstruction only |
| H0019 | 57 | 9.8234 × 19.8930 × 29.5656 | 3 × 3 × 7 | 4 / 12 | Exact reconstruction only |
| H0021 | 50 | 11.3461 × 26.2801 × 23.8159 | 3 × 3 × 6 | 8 / 17 | Exact reconstruction only |
| H0909 | 21 | 16.0557 × 11.7436 × 7.0896 | 3 × 3 × 3 | 1 / 2 | Exact reconstruction only |
| H0910 | 14 | 15.7309 × 11.7436 × 4.4938 | 3 × 3 × 2 | 1 / 1 | Exact reconstruction only |
| H0911 | 17 | 11.6142 × 10.8771 × 4.3964 | 3 × 3 × 2 | 1 / 2 | Y, pitch 1.377769 m, profile error 0.328 mm; recorded N=2 |
| H0917 | 29 | 8.1350 × 8.9161 × 9.3021 | 3 × 3 × 4 | 1 / 2 | Exact reconstruction only |
| H0918 | 18 | 24.6243 × 14.2252 × 8.7094 | 3 × 3 × 3 | 1 / 2 | Exact reconstruction only |
| H0919 | 15 | 18.8108 × 10.2149 × 7.8528 | 3 × 3 × 3 | 1 / 2 | Exact reconstruction only |
| H0920 | 25 | 11.0496 × 13.3459 × 7.1044 | 3 × 3 × 3 | 1 / 2 | Exact reconstruction only |
| H0921 | 24 | 18.2239 × 12.1557 × 8.6042 | 3 × 3 × 3 | 1 / 2 | Y, pitch 1.732191 m, profile error 1.451 mm; recorded N=2 |
| H0923 | 25 | 11.5279 × 8.3497 × 5.5298 | 3 × 3 × 3 | 1 / 2 | Exact reconstruction only |
| H0924 | 25 | 18.0981 × 11.0938 × 6.5207 | 3 × 3 × 3 | 1 / 2 | X, pitch 10.602469 m, profile error 1.392 mm; recorded N=2 |
| H0925 | 25 | 16.8288 × 12.0019 × 8.4486 | 3 × 3 × 3 | 1 / 2 | X, pitch 9.592434 m, profile error 1.400 mm; recorded N=2 |
| H0926 | 24 | 21.1994 × 10.0756 × 7.9164 | 3 × 3 × 3 | 1 / 2 | X, pitch 2.349596 m, profile error 0.001 mm; recorded N=2 |
| H0927 | 23 | 10.7314 × 11.9424 × 11.2563 | 3 × 3 × 3 | 1 / 2 | Y, pitch 2.458146 m, profile error 1.353 mm; recorded N=2 |
| H0929 | 24 | 15.3063 × 9.7226 × 11.1307 | 3 × 3 × 4 | 1 / 2 | Exact reconstruction only |
| H0930 | 25 | 15.7123 × 9.5264 × 6.1194 | 3 × 3 × 3 | 1 / 2 | X, pitch 5.224355 m, profile error 0.566 mm; recorded N=2 |
| H0931 | 21 | 17.2297 × 12.2914 × 8.4086 | 3 × 3 × 3 | 1 / 2 | X, pitch 10.912155 m, profile error 0.369 mm; recorded N=2 |

Adaptation risks:

- Treat exact reconstruction as a fixed family assembly. Applying a generic length/height module grid changes the original silhouette and disconnects open boundaries.
- Preserve source UVs, material slot order, family-specific texture channel mappings, and the baked geometry transform. Several original materials have sparse or family-specific channel sets.
- Eight band candidates preserve a matching geometric profile; the newly repeated UV boundary is expressly unqualified for texture phase, and floor/opening/roof continuity still needs native visual checks.
- Whole-building bands include start/end/corner/roof coverage as complete sets. Do not substitute independent cell pieces or switch axes.
- All 609 FBX files have consistent FBX 7400 GlobalSettings: UpAxis=2/+1, FrontAxis=1/+1, CoordAxis=0/-1, UnitScaleFactor=1.0 (centimetre metadata). Assembly translations/bounds are metres. Honor importer unit/axis conversion, and verify actual imported bounds before accepting any additional conversion. Cell pivots are not independently verified ground-contact or façade-facing anchors.
- H0017 READBACK omits the duplicate-face-removal field for all 63 parts, so absence is not a proved zero. H0018 records one exact duplicate face removed by FBX import validation; H0021 records three. These explicit source import changes must be retained in native validation accounting.
- Original-source rights/holds remain external release decisions and are not changed by this audit.

Full per-family roles, exact split planes, neighbor checks, FBX GlobalSettings, hash checks, textures, and source texture channel bindings are in SOURCE_AUDIT.json.
