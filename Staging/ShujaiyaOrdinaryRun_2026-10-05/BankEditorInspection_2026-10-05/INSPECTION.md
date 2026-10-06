# Bank editor inspection (read-only), 2026-10-05

Scope: the 20 modular building-kit families (609 parts) imported into PID 21608. Nothing was executed, saved or changed. Structured data is in `INSPECTION.json` in this folder.

## Important first: the editor was not in the stopped state

- [measured] Exactly one UnrealEditor.exe was running: PID 21608.
- [measured] After the 13:59Z stop, a **v004 resume** started at 14:31Z. It was activated by operator thread `01a10c77-46ba-7001-a657-5014f6205d3a`, not the bank operator named in the brief (`01a1067c-...`). Its lease line has no `manager_thread_id`.
- [measured] The resume was importing about one part per second during this inspection.
- [measured] It finished at 14:47:48Z with status `COMPLETE_WITH_REPAIR_QUEUE`: 34 reused + 569 imported and saved + 6 failed = 609.
- [measured] The lease now reads `IMPORT_COMPLETE_REPAIR_QUEUE native_authorized_now=false running_imports=0`.
- **No MCP or editor calls were made.** The importer checks after every part that the dirty-package set is a subset of its own, so any side effect from an inspection could have failed the other chat's next part. Every finding below comes from files. Most of them are the importer's own readbacks, taken inside the live editor at import time.
- Labels used: **[measured]** = read from files now; **[importer]** = the importer's live-editor readback, read from file; **[code]**; **[inferred]**; **[not measured]**.

## Q7. State compared with the 13:59Z stop receipt

- Dirty packages now [importer]: only the 6 failed, never-saved meshes, all under `/Game/Project/Shared/ModelBank/Prepared/Modular/`:
  - `H0017/Modules/SM_H0017_Tier01_WestFacade`, `Tier03_EastFacade`, `Tier04_EastFacade`, `Tier05_EastFacade`, `Tier05_WestFacade`
  - `H0019/Modules/SM_H0019_Roof_EastFacade`
  - Maps: none.
- The 15 packages that were dirty at the stop (9 `M_*`, 5 `T_*_NormalRGB`, `SM_H0017_Ground_SWCorner`) [measured]: all are now saved, and each `.uasset` sha256 matches its receipt pin.
- Cooking paused: true [inferred]. Every batch asserts `is_asset_cooking_paused()`, and every batch succeeded.
- Callbacks [not measured]: the v004 boundary no longer runs `geocity_runtime_guard.verify()`.

## Q1. Textures (74 used by the 41 modular materials)

- [importer] Settings come from MaterialReceipts (`get_used_textures`); [measured] source formats and sizes come from the PNG/JPEG headers.
- Color textures (36): sRGB on, `TC_DEFAULT`. Mostly 4096² PNG; some 2048² JPEG.
- Data/ORM textures (18): sRGB off, `TC_MASKS`, so they are linear. G drives Roughness and B drives Metallic. The AO channel (R) is not connected, as in the source.
- Normal maps (20): `T_*_NormalRGB`, sRGB off, `TC_VECTOR_DISPLACEMENTMAP`, flip_green off. They are sampled as LinearColor and decoded in the shader.
  - This is **deliberately not TC_NORMALMAP**: it keeps the source blue channel and applies one green flip. The decode is correct.
  - Cost: about 1.6 GiB of uncompressed GPU memory including mips. That risks pressure on the texture streaming pool (blurry mips).
- The only off-policy texture: `/Game/Project/Shared/ModelBank/Prepared/Dependencies/Textures/T_3b3c4559d236d5d74fc1_color`.
  - It uses `TC_EDITOR_ICON` (uncompressed UI format); the source is a non-power-of-two 1274x888 RGBA image. This is the Recovery_RGBA8 case.
  - It is used by the AC-front materials `M_7e5df697466e78c7c5a3` (H0017) and `M_a9eff272846ae541957c` (H0021).
  - The effect is cosmetic only.
- Duplicate: an older shared `.../Prepared/Dependencies/Textures/T_f64380cbb2cfca811599_normal` (TC_NORMALMAP) sits next to the modular NormalRGB copy of the same file. The modular materials do not use it.
- [not measured] Mip settings, LOD group and streaming flags.
- **Verdict: texture settings are consistent and are not why parts fail to connect.**

## Q2. Materials

- [code + importer] There are 41 **standalone `UMaterial`s**, one per recipe hash, under `.../Prepared/Modular/Dependencies/Materials/M_*`.
  - There is no kit master, no material instances and no parameters, so there is no parent chain.
  - Texture samples have the texture hard-wired, so "parameter bound or empty" does not apply.
- All referenced textures exist on disk.
- Two materials are constant grey (0.502), two-sided, with no textures: `M_889b72fa4da16cf39f50` (H0017 "standard1") and `M_2c17222f042762592741` (H0021 "standard").
  - This matches the untextured source, but they will look like a default material.
- [not measured] Checker or compile-error state (needs a live read).

## Q3. Slot mapping

- [importer vs SOURCE_BINDINGS.json] Three examples:
  - `/Game/Project/Shared/ModelBank/Prepared/Modular/H0910/Modules/SM_H0910_Ground_SECorner`: slot 0 `Arab_x8` → `M_194fa2264db1fbe3eec8` (171 triangles).
  - `.../H0017/Modules/SM_H0017_Ground_SWCorner`: 9 source slots, 2 used.
    - Slot 0 `_Building_5_M4` → `M_d6c8b66c8065206f9aea` (634 triangles).
    - Slot 1 `_lambert2` → `M_a93c0c04295da45cc845` (696 triangles).
  - `.../H0018/Modules/SM_H0018_Tier03_EastFacade`: `standardSurface9SG`, `5SG`, `6SG` and `8SG` → `M_137731c1...`, `M_de1dd835...`, `M_df4390a0...` and `M_ad422b74...`.
- Full sweep of all 603 saved receipts (1019 slots):
  - Every slot is bound to a modular `M_*`. **0 are WorldGridMaterial or None.**
  - Face counts per slot are asserted equal to the source.
  - The 746 unused source slots are dropped.
  - The only name differences come from FBX namespace stripping (e.g. `acbody1`), and they are matched as intended.
- [inferred] The 6 failed meshes stopped at the triangle check, which runs before `set_material`. They are dirty and unsaved, and almost certainly still carry import-default slots.

## Q4. Normal strength

- [code] The "importer ignores normal strength" blocker is about `Staging/BankIntegration_2026-10-04/import_prepared.py` `material_for` (lines 116-118), which wires normal RGB straight into Normal. **The modular adapter does not use that function.**
- Its own `material_for` (`modular_native_adapter_v004.py` lines 153-165, unchanged since v001) works like this:
  - It decodes `(2r-1, 1-2g, 2b-1)`.
  - It scales by `(s, s, clamp(s,0,1))`, adds `(0, 0, 1-clamp(s,0,1))` and normalizes.
  - This equals Blender's Normal Map node.
- [importer] Strengths in use run from 0 to 2.84 and are recorded per material. `M_ad422b748ef80ff9a1e1` has strength 0, so its normal map renders flat, as in Blender.
- The stop status text that repeats this blocker is stale for the modular route.
- [not measured] Visual verification.

## Q5. Consumer: no family is reachable [measured]

- Production HDA package `.../ModelBank/HDA/GeoCity_city_v015_PermanentBank.uasset` (357eeac6...) is identical to its pre-change backup.
- The production `hdalc` and `geocity_city_module.py` (e67b6e15...) are the derivative's base. The production module contains 0 `source_family` code, and its Courtyard lane is hard-wired to `/Game/ModularCourtyard/...` paths and recolors slots.
- Both AREA_PROFILE.json files are identical to their backups and contain 0 `source_family_registry_ref`.
- The complete-family branch exists only in the unpromoted derivative: `Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank/revisions/20261005_modular_source_families_v001/` (`ordinary_selection_enabled=false`).
- FAMILY.json now exists for all 20 families: 18 complete, plus H0017 at 58/63 and H0019 at 56/57. No consumer has used them yet.
- **The normalizer cannot accept the new receipts.** `Staging/ModularConstruction_2026-10-05/ContractAudit/normalize_bank_readback.py` `APPROVED_REQUESTS` (lines 15-20) lists only the `8a253d5b...` and `f738f677...` (v002) requests. The 18 new FAMILY.json files and all 569 new parts carry the v003 request `1fa6654d...`, so the lookup on line 52 fails for them.
- Every part has `procedural_eligible=false`; every family has `enabled=false` and `explicit_hold=true`.

## Q6. Screenshot

Skipped. A close-up needs a spawned actor, a camera move or an open asset editor, which are all excluded; and another operator was writing to the editor at the time.

## Why parts do not "connect": top 3 root causes

1. **(c) No consumer branch.** Nothing in production reads these families (see Q5).
2. **(c) Each part needs its own assembly offset.**
   - [importer] Every mesh keeps its source-object origin as its pivot, and every part has a distinct `native_assembly_translation_cm` (14/14 in H0910, 58/58 in H0017).
   - With those offsets applied, parts meet exactly on shared faces. For example, in H0017 the Ground_Core x-max of 299.1 equals the EastFacade x-min of 299.1.
   - Placed at a common origin, or through the Courtyard lane, they overlap and do not join.
   - Only the unpromoted consumer applies these offsets: it multiplies the source `assembly_translation_m` by its basis matrix (derivative module line 6395).
   - Other facts: no part has collision, and each has one LOD.
   - Scope limit: all 603 receipts have `full_geometry_or_uv_equivalence=false` (UV0 checked only at probe points), and the repeat seams of the 8 extension bands are unqualified. So visible texture seams across part boundaries are **not measured** here.
3. **(b) 6 failed meshes, limited to those parts.**
   - Native triangle count = source − 1 in all six. They are unsaved and probably still carry default slots.
   - This keeps H0017 and H0019 incomplete, and the consumer contract rejects incomplete families.

**Verdict:** mainly **(c) missing consumer branch**, including the per-part placement the consumer must apply. **(b)** applies only to the 6 failed meshes. **(a) texture settings are not a cause.**

## Smallest proposed fixes (none executed)

1. **Consumer:**
   - After manager review, add the v003 request `1fa6654d...` to `APPROVED_REQUESTS` in `normalize_bank_readback.py`.
   - Root then normalizes and binds the 18 complete FAMILY.json receipts into the registry.
   - The manager then promotes the dated derivative HDA into the canonical native HDA and merges `building_assembly_contract.source_family_registry_ref` into both profiles.
2. **Placement:** this already exists in the unpromoted consumer, so nothing new is needed once it is promoted. For any manual check, place each part at its `native_assembly_translation_cm` instead of at a common origin.
3. **Failed parts:** add the measured native triangle count as a roundtrip allowance after a per-slot face-count check, using the existing `roundtrip_slot_triangle_counts` mechanism. Then reimport in place, so `set_material` runs, and do a named save.
4. **Optional:**
   - Set `T_3b3c4559d236d5d74fc1_color` to `TC_DEFAULT`; it is a shared texture, so its owner must do it.
   - Use `TC_BC7` with sRGB off for the NormalRGB textures. This keeps the same decode at about a quarter of the memory.
5. **Optional:** a short read-only live check, now that `running_imports=0`: slot readback on the 6 dirty meshes, the material compile state, and callbacks.
