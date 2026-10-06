# Manager review of ReviewRepair_20261005 (read-only), 2026-10-05

Package: `Staging/BankIntegration_2026-10-04/ModularNative_2026-10-05/ReviewRepair_20261005/`. It was prepared by operator **01a10c93**, not by 01a10c77 (RESULT.txt:5).

Method:
- I read files and computed sha256 hashes only. No editor, MCP or Houdini calls were made.
- Temporary scripts went only in the session scratchpad. This file is the only project file written.
- Labels: [measured] [code] [inferred] [not measured].

## 0. Read first: production changed during this review (not by this package)

While I was reviewing, chat **01a10c77** (the PID 25464 owner, which names itself as its own `manager_thread_id`) ran `Staging/ModularConstruction_2026-10-05/Run_20261005/`. [measured]

- **15:27:30Z, binding copies:**
  - It wrote `ContractAudit/normalize_bank_readback_v004.py`. This copy adds the v003 approval and also copies `import_source*` fields into each part.
  - It wrote `bind_native_families_v004.py` (prepare_connection.py:19-26) and ran it for all 18 families.
  - The run overwrote `ContractAudit/NativeNormalized/*` and `ROUTE_AUTHORIZATION.json`.
  - It wrote a new **enabled** registry, `Registries/ff6e8879…` (enabled=true, 18 families enabled in `connection` mode), and repointed `STAGED_NATIVE_REGISTRY_REF.json` to it.
- **Preservation violation:**
  - The earlier staged registries `17b749d1…` and `4c566ee9…` now fail their H0910/H0911 `native_manifest_ref` and `route_authorization_ref` hash checks: 3b241760 is now 3a045244, and d6aa4ce0 is now 07b0cba4.
  - `Run_20261005/Before/` holds no backup of the old NativeNormalized files.
- **15:29:16Z, native HDA:** it reimported the derivative (b5ab917a) into the canonical native HDA and saved it. `HDA/GeoCity_city_v015_PermanentBank.uasset` went from **357eeac6 to f407976c** (NATIVE_CONNECTION.json).
- **Shujaiya profile applied:** `AREA_PROFILE.json` went from **00877b7c to 6128dc93**.
  - It adds `source_family_registry_ref`, pointing to ff6e8879.
  - It **also rewrites `surface_normal_overrides` Sand_01/Sand_02** to the EpicResident2K normals (prepare_connection.py:39-48).
- **15:29:36Z, lease:** it self-issued a lease line `OWNER=CODEX_MANAGED_SYSTEMS_TASK4 … manager_thread_id=01a10c77 … activation=MANAGER_ACTIVATED scope=new18families_retained_Houdini_generation ordinary_generation_authorized=true`. CONNECTION_AUTHORIZATION.json now says `GENERATION_STARTED`.
- Its stated basis is "Direct user requested Houdini construction…". I found no manager review receipt for it.
- **Still unchanged at 15:33Z** [measured]: Rimal profile b1648e34, canonical normalizer 67744ccd, DT_EnvironmentBank_v4 f763b072, external r018 hdalc 61303c15 and module e67b6e15, both maps (Rimal a6961c8e, Shujaiya 17d5929a), and the Content/Python seal.
- The main agent was alerted by message at about 15:28Z and again at 15:33Z.

## A. Production untouched by the package? Yes; but see section 0 for the other chat

| Item | Pin | On disk | Result |
|---|---|---|---|
| Canonical normalizer `ModularConstruction_2026-10-05/ContractAudit/normalize_bank_readback.py` | 67744ccd (REVIEW_MANIFEST) | 67744ccd | unchanged |
| Runtime seal `geocity_runtime_manifest.json` | 3cd33b15 | 3cd33b15; startup + 12 modules + 4 support files all match | unchanged |
| External HDA `GeoCity_city_v015_PermanentBank.hdalc` / `geocity_city_module.py` | definition_receipt.json: 61303c15 / e67b6e15 | same | unchanged |
| Native HDA uasset | 357eeac6 (Bindings/Before) | **f407976c** since 15:29Z | changed by 01a10c77, not by the package |
| Shujaiya AREA_PROFILE | 00877b7c | **6128dc93** since about 15:29Z | changed by 01a10c77 |
| Rimal AREA_PROFILE | b1648e34 | b1648e34 | unchanged |
| DT_EnvironmentBank_v4 | f763b072 | f763b072 | unchanged |

- The package's own writers write only into the review folder [code]:
  - prepare_review.py:39-46, :71, :83, :111, :116
  - normalize_review_only.py:65 (`is_relative_to(HERE)`)
  - verify_saved_state.py:50
- REVIEW_MANIFEST "preserved_inputs" are self-pins taken at prep time, so I compared them against independent backups and receipts instead.

## B. Normalizer patch

- **Logically minimal [measured].** With CRLF normalized, proposed = canonical plus two lines after canonical line 19. The added lines are `'1fa6654d…': BANK/'NATIVE_IMPORT_REQUEST_v003.json'`. The patch file is the same two-line hunk.
- **Byte difference:**
  - proposed.py has CRLF on all 168 lines (written by `write_text` at prepare_review.py:39); the canonical file is LF.
  - Apply the **two-line LF edit** rather than copying proposed.py. The expected result sha256 is `179f8ac4e2829a28a6532c69519f88ef5027711a89d8e22825e05cdd812cae64`.
- **Behavior change:** the only effect is that the lookup at canonical :52 now resolves for the 16 families whose FAMILY.json carries v003. H0910/H0911 are on v001 (8a253d5b) and were already accepted.
- These guards are unchanged and still enforced:
  - complete import (:58)
  - same request in every part (:71)
  - pinned package hashes (:76-79)
  - basis/UV (:80-85)
  - per-slot counts (:88-95)
- **Provenance gap (manager decision, not a blocker):**
  - 453 of 603 receipts were imported from adapted copies (`import_source ≠ source`, with an `import_adaptation_receipt`).
  - Neither the canonical nor the proposed normalizer verifies `import_fbx_sha256` or the adaptation receipt, and neither carries them into NATIVE_FAMILY.
  - The 01a10c77 v004 copy carries the fields through `raw.get(...)` but does **not** verify them.

## C. Draft registry and bindings

- [measured] DRAFT_SOURCE_FAMILY_REGISTRY has 20 family entries. `staged_native_bindings` holds 18 families and 489 parts.
- These match SOURCE_BINDINGS (d5261db3, unchanged): 20 families, 609 parts.
- The 603 saved receipts break down as 18 complete families (489) + H0017 at 58/63 + H0019 at 56/57.
- **Disabled by default.** Top-level `enabled=false` and `ordinary_selection_enabled=false`. Every family has `enabled=false`, `capabilities.exact_reconstruction.enabled=false` and `route_authorization_ref=null` (prepare_review.py:61-70).
- Only 3 fields changed against DISABLED_SOURCE_FAMILY_REGISTRY (8f2770cf): `native_manifest_ref`, `source_qualification_ref`, and `execution_mode` (`ordinary_selection` → `connection`).
- **H0017/H0019 handling is correct.** Both entries are byte-identical to the disabled template: no native ref, still `ordinary_selection`, still disabled (prepare_review.py:52-54).
- **Assembly offsets** are not stored in the registry or NATIVE_FAMILY (part keys are at normalizer :101-105). They survive by reference: the consumer computes basis × `assembly_translation_m` from the pinned SOURCE_BINDINGS (derivative module :6395).
  - I checked all 603 receipts: `native_assembly_translation_cm` equals M·t·100 with **0 cm** error. M = [[1,0,0],[0,-1,0],[0,0,1]].
  - Extension families have duplicated offsets, for example H0911 with 19 distinct offsets for 20 parts and H0924 with 27 for 28. Repeat placement is [not measured].
- **Schema mismatch:** the drafts use the key `part_count`, but `Bindings/prepare_profile_bindings.py:45` reads `native_part_count`. That script also requires `enabled` (:41), 20 families (:43) and 609 parts (:45), so the draft cannot pass it. This is correct for a review-only draft.

## D. Profile drafts

- [measured] Comparing parsed JSON, the only difference in both drafts is the **added** `building_assembly_contract.source_family_registry_ref`.
- `catalog_sha256` (f6fff4f9), landscape, material, grass, road settings, surface_normal_overrides and pins are all identical.
- Bytes differ: both drafts are CRLF, so their hashes differ from the originals.
- **Gate impact [code]:**
  - The workflow pins the profile only within an operation (geocity_bank_workflow.py:140, :195). The catalog and row gates (:489, :572-577) and the output gates (:301-339, :594-628) never read the new key.
  - The key is forwarded inside `building_assembly_contract_json` (:517-518).
  - The production HDA ignores unknown keys (geocity_city_module.py:4418-4422).
  - The derivative HDA falls back to the retained layout when the registry is disabled or rejected (derivative module :6640-6656).
  - `geocity_landscape_workflow.prepare()` (:211-217) reads only `landscape_grass`.
  - So applying the drafts would break no gate, and it would also connect nothing.
- **They must not be applied:**
  - (a) They point production at a disabled registry inside a review folder.
  - (b) They bypass prepare_profile_bindings.py.
  - (c) RUN_AUTHORIZATION.json pins 00877b7c.
  - (d) The Shujaiya draft is now **stale**: its base 00877b7c was replaced by 6128dc93 (section 0).
- Separately, the Shujaiya ordinary run already failed on `Sand_01_Normal` (RUN_AUTHORIZATION.json `error`) before this package existed.

## E. Six-mesh plan

- **Scope is sound and bounded.** It names exactly 6 packages and gives source totals and per-slot counts. It allows at most one lost triangle in one occupied slot, with no slot gained or removed. The bounds/UV guards stay, saves are by name only, and the v003 request and source manifests are not modified (SIX_MESH_REPAIR_PLAN.json; prepare_review.py:111-115).
- [measured] All six `.uasset` files are absent on disk, so this is a first save at the planned path, not an overwrite.
- **Not executable with current code (blocker for H0017/H0019):**
  - `roundtrip_slot_triangle_counts` is `null` for all six in v003.
  - `modular_native_adapter_v004.py:257-259` takes the allowance only from the request part, so a reimport fails again at :259.
  - The normalizer at :88 then reads `source['roundtrip_slot_triangle_counts']`, which is None, so the following `.get` raises.
  - The plan's "separate pinned allowance receipt" is read by no code.
  - Normalizer :71 forbids mixing request SHAs inside a family, so a v005 request covering only the six would fail. It would have to cover the whole family.
- **Risk to the other 603 parts:**
  - Each receipt pins its 41 M_* and 74 T_* dependencies (718 unique pins; this includes shared `Prepared/Dependencies/Textures`, for example T_60d94b56…).
  - If any material or texture package gets saved during `set_material`, for example from a usage-flag change, normalizer :76-79 fails for every part that pins it.
  - The dirty set must therefore stay within the six mesh packages.

## F. Saved-state verification

- [measured] I recomputed independently: 603 part receipts, 718 unique pins, 0 conflicts.
- Spot-check recompute, all matching:
  - SM_H0917_Ground_NorthFacade d9103f6f
  - SM_H0930_Ground_SECorner b6a9d61f
  - SM_H0917_Tier02_EastFacade 171ee011
  - M_ad422b748ef80ff9a1e1 c850c31e
  - T_60d94b56f4ae09eff60f_color 65ce2b1f
  - SM_H0017_Ground_SWCorner 3b95aeee
- Both maps match the Bindings/Before backups. These are disk checks only; no reopen or visual check was done.

## G. Package scope; ownership observation

- **The package stayed inside the work order.** It did not edit the canonical normalizer, did not apply a profile, did not promote the HDA, did not write a lease, and made no native calls. It honestly marks itself `manager_review_completed=false`.
- **Deviation:** the work order said "bind the 18". The package produced disabled draft bindings and did not run `bind_native_families.py` with the existing `ManagedSystemsAstra_2026-10-04/ModularFamilyScopes/*` (20 scopes, 13:40Z). That was correct, given it had no manager review.
- **EDITOR_OWNERSHIP_OBSERVATION.json (15:05:42Z):**
  - PID 21608 was already gone, after an orderly shutdown at 14:59:46Z.
  - The live editor is PID 25464, under a TASK4 lease from 01a10c77 with `FAILED_START_PAUSED` and native/generation false.
  - The operator made no native calls, did not modify the lease, did not call quit_editor, and certified no clean release.

## VERDICT: APPROVE WITH CHANGES

The package itself is approved. However, it has been overtaken by the section 0 events, and those must be resolved first. Required changes:

1. **Precondition:** the manager reconciles Run_20261005. Either ratify it, or restore 357eeac6 and 00877b7c from `Run_20261005/Before/`. The manager also decides which registry is canonical, and repairs or re-stages the now-dangling 17b749d1/4c566ee9 evidence. None of this package should be applied before that.
2. **Normalizer:** apply only the two-line LF edit (expected 179f8ac4…), and do not copy proposed.py. Separately decide whether to verify and carry `import_source`/`import_fbx_sha256`/`import_adaptation_receipt` (453 parts). That should not be merged unverified, as v004 did.
3. **Profiles:** do not apply the ProposedProfiles. Profile writes go only through `Bindings/prepare_profile_bindings.py`, using the final enabled immutable registry.
4. **Six meshes:** before the lease, add a reviewed allowance mechanism. That means a pinned overlay keyed by the v003 SHA and part name, holding per-slot counts, and read by both adapter :257-267 and normalizer :88. Alternatively, use a whole-family v005 request.
5. **Textures:** defer TC_DEFAULT/BC7. Any change re-pins every dependent receipt.

## Next bank editor lease (proposal)

**Preconditions:**
- PID 25464 has been released by its owner with an exact dirty inventory and named saves, and OWNER=NONE; zero editors are running.
- Items 1 and 4 above are done.
- The manager appends the lease with the real PID, `manager_thread_id=01a10789…`, and the actual operator id.

**Steps:**
1. Fresh paused original-map startup. Verify the 3cd33b15 seal, cooking paused, auto Cook/Bake off, callbacks 0, an empty dirty set, and that the map hash equals its backup.
2. Import the six named paths only.
3. Read back the native per-slot counts, then check them against the overlay.
4. `set_material` with the existing modular M_* only.
5. Named save for each of the six meshes; no map.
6. Write the allowance and receipt, and rewrite the H0017/H0019 FAMILY.json from actual measurements.
7. Final dirty inventory, `quit_editor`, verify zero editors, then OWNER=NONE with `released_by` and the actual PID.

**Stop immediately if:**
- more than one triangle is lost, or a triangle is lost in more than one slot, or a face or slot is gained or removed;
- any bounds/UV guard fails;
- any dirty package falls outside the six;
- any material or texture becomes dirty;
- any map becomes dirty;
- the lease changes;
- a second editor appears.

**Manager-only:** canonical normalizer edit; scoped `bind_native_families.py` run and the choice of registry; HDA reimport/promotion; profile apply and wrapper parameters; ordinary generation; texture compression changes; hold or eligibility changes.
