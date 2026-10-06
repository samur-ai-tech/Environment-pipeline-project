# Terre and Hergel model-bank provenance

**Evidence state:** available in the old bank only. Rights for use in Environmentpipeline: **unknown** in the archive evidence below; for `Bank_ME_v3`, see the owner confirmation that follows. This note records archive evidence; it does not grant or verify a license.

## Owner confirmation — 2026-09-27

Aviv confirmed in the manager session on 2026-09-27, in answer to a direct question, that the bank assets are his and that the rights are in order. **Scope:** the 32 Hergel-derived assets in `/Game/Project/Shared/Bank_ME_v3/`. **Effect:** licensing no longer blocks their technical qualification. **Limits:** this is the owner's statement; no receipt, EULA, or per-package licence text is attached. Attribution or redistribution terms for any later exported build are not recorded here. Any asset outside `Bank_ME_v3`, including other Hergel or Terre models, needs its own confirmation. This entry is the source record for the same statement added to the archived `Staging/Archive/PreFinalVision_2026-09-29/Research/ResearchReviews/2026-09-27/02_model_bank_review.md` at 12:50.

## What these banks are

- **Hergel:** an animation-free transfer bank prepared from a user-supplied Unity `Hergel` asset collection. The archived `Sources/Hergel` folder contains 878 FBX/Blender model records, shared textures, per-model reports, and a searchable catalog. The Unreal library catalog lists 878 Hergel records: 859 imported meshes and 19 records with no geometry.
- **Terre:** an animation-free transfer bank prepared from a user-supplied Unity `terre` asset collection. The archived `Sources/Terre` folder contains 1,185 FBX/Blender model records, shared textures, reports, and six SpeedTree `.st` sources. The Unreal library catalog lists 1,185 Terre models; the six trees are additional static imports.
- The unified **Unreal Model Library** was prepared from those two banks for the old `GIS_WorldBLD` project. Its `Reports/library_catalog.json` retains each model's original Unity `Assets/...` source path. The Stage 2 reference is `FULL_INDEX.csv` here.

These are **assembled collections of assets from multiple source families**, not a statement that one person authored every mesh or texture. Recorded source paths include `LeartesStudios`, `ScansFactory`, `HIVEMIND`, `PostApocalypticTown`, and other families. Names in a path identify provenance leads; they do not establish ownership or a license.

## License and ownership evidence

| Scope | What the archive says | Use terms for Environmentpipeline |
| --- | --- | --- |
| Hergel bank as a whole | The transfer README describes formats, texture links, missing maps, and checks. No bank-wide license or proof of ownership is supplied. | **Unknown** |
| Terre bank as a whole | The transfer guide describes model conversion and six SpeedTree sources. No bank-wide license or proof of ownership is supplied. | **Unknown** |
| Hergel NYCAlley kit source pieces | `CityBLD_Kits/Hergel_NYCAlley/Evidence/source_provenance.json` calls them existing user-supplied commercial assets and explicitly asserts no new or transferred license. | **Unknown**; the note is not a use grant |
| Six Terre SpeedTree trees | `.st` sources and textures are present, but no ownership record or applicable tree/texture license was found in the bank documentation. | **Unknown** |
| Other third-party files | Some `License.txt` files occur inside unrelated Unity package/sample folders, such as Animancer. They do not state terms for the whole Hergel or Terre model banks. | **Unknown per model** |

The unified catalog has no license or provenance-note field. Accordingly, that column in `FULL_INDEX.csv` is blank rather than inferred from a folder name.

## Evidence needed before qualification or reuse

1. Identify the rightsholder and exact source package for each selected model, texture, and tree. Use the original Unity path in `FULL_INDEX.csv` and the kit provenance report to trace them.
2. Obtain the relevant purchase receipt, account entitlement, original license/EULA, or an explicit creator permission for each package. Record whether the terms cover use and redistribution in this Unreal project and any later exported build.
3. Confirm that derived kit parts and converted textures inherit suitable rights from their source assets, including the `LeartesStudios/NYCAlley` pieces and Terre rural source family.
4. Record the license evidence and attribution obligations against the exact Stage 2 candidate before treating licensing/provenance as qualified.

## Archive references

- `Unreal_Model_Library_2026-09-24/Reports/library_catalog.json`
- `Unreal_Model_Library_2026-09-24/Sources/Hergel/README_HE.txt`
- `Unreal_Model_Library_2026-09-24/Sources/Terre/README_HE.html`
- `Unreal_Model_Library_2026-09-24/CityBLD_Kits/Hergel_NYCAlley/Evidence/source_provenance.json`
- `Unreal_Model_Library_2026-09-24/Reports/Terre/Reports/speedtree_import.json`
