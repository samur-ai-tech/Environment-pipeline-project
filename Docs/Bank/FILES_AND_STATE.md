# Files and bank state

Bank table and six profile bindings checked **18 October 2026** after the accepted native run, permanent HR01 and delivery contact/facing fixes. Modular measurements and earlier output evidence retain their own dates. Refresh this page from the native table/readback, active area profiles and exact import sources when those inputs change. A saved receipt establishes its dated result; live editor ownership comes from the current task records.

## Where files belong

| Purpose | Location | What it contains |
| --- | --- | --- |
| Active Unreal project | `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline` | Project configuration, saved native assets, Python lifecycle and area maps |
| Shared imported bank | `Content/Project/Shared/ModelBank/` in that project | Native tables, materials, imported modular parts, kit records and shared HDA |
| Other referenced native assets | Vendor folders under `Content/` and `Content/Project/Shared/Bank_ME_v3/` | Existing models remain in their original paths; bank membership does not require moving them |
| Original model archives | `C:/Users/USER/Documents/Unreal Projects/GIS_WorldBLD/SourceData/ModelBanks_Archive/` | Hergel, Terre and the Unreal Model Library source/export archives |
| Prepared sources and assembly recipes | `C:/Users/USER/Documents/Pipeline Environment/ModelBank/` | `Prepared_2026-10-04`, `Modular_2026-10-04` and `NativeKits` |
| Geographic area inputs | `C:/Users/USER/Documents/Pipeline Environment/SourceData/` | Area source packages, geographic features, elevation and provenance |
| Houdini definitions | `C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank/` | Retained external HDA revisions and source files |
| Area profiles | [Staging/ModelBank](../../Staging/ModelBank/) `*/AREA_PROFILE.json` | Exact source package, table, catalog digest, native HDA, family registry and output folders for an area |
| Saved area output | `Content/Project/Areas/<AreaId>/` | Maps, area HDA copies, Cook/Bake packages and area-owned details |
| Native lifecycle | [Content/Python](../../Content/Python/) | `geocity_editor_action.py` and `geocity_bank_workflow.py` |

Unreal `/Game/...` paths resolve below the active project's `Content/` directory. An Unreal object path can also contain `.ObjectName`; its package file uses the package path plus `.uasset`.

## Which record answers which question

| Question | Authority | Other views |
| --- | --- | --- |
| Which canonical identity, native path, hold and selection configuration is saved? | Native AnyArea table with its matching typed native readback | Older CSVs and galleries are dated snapshots |
| Which assets and dependencies exist on disk? | The current saved package files and a dated [asset scan](INDEXING.md#refresh-the-saved-file-inventory) | File presence does not establish loadability, material quality or eligibility |
| What can a source family construct? | The exact registry-referenced `ASSEMBLY.json`, capability declaration and validation | Folder names and source-building counts do not define capabilities |
| Which recipe and HDA does this area use? | Its `AREA_PROFILE.json`, referenced registry and native HDA import metadata | The highest numbered candidate revision is not automatically active |
| Was output generated, saved and reopened? | The area's run, save and fresh-reopen receipts | A table save or imported mesh is not an area result |
| Is a model's appearance accepted? | The explicit scoped review/acceptance record | Enabled, imported and geometrically valid are separate states |

## Houdini input catalog

This is the maintained catalog route, not a second bank. The [binding index](../../Staging/HoudiniBankConsolidation_2026-10-18/CATALOG.json) is a dated, reproducible projection of these authorities. It contains pointers/hashes rather than duplicate rows or models. Eligibility always comes from the matching current native readback and applicable route policy.

| Input / lookup key | Actual producer and retained consumer | Where to read / what it proves |
| --- | --- | --- |
| Canonical models: `Name`, `AssetId`, `ObjectPath`, `AssetRevision` | Native AnyArea DataTable → official Geometry Input 0 / `bank_catalog` → numbered point attributes → `bank_parse_versioned` / v3 guard | [Current typed readback](../../Staging/HoudiniBankFixes_2026-10-18/CURRENT_NATIVE_BANK_READBACK.json). Includes bounds in cm, anchor/facing claims, role/request/rule, style/weight, area/scope, release and holds. The row schema and digest are executable contracts; validity flags do not prove physical semantics. |
| Fixed reconstructions: exact `family_id` + revision | Registry `families[].source_bindings_ref`, `native_manifest_ref`, `route_authorization_ref`, `source_qualification_ref` → retained source-family planner | Follow the selected profile's `source_family_registry_ref`; for [Shujaiya](../../Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json) it is [40a73d1d… registry](../../Staging/HoudiniBankFixes_2026-10-18/Registries/40a73d1d0880c47f23cd25f05f8f1f28578543d5a63aa70b4a16ba538bbe98c6.json). Part transforms, source basis, qualification and authorization remain separate. |
| Variable source families: exact manifest path/hash | Registry `families[].procedural_family_ref` → `ASSEMBLY.json` → `procedural_bank_families` / `procedural_family_plan` | Manifest modules carry roles, anchors/restoration translations, interfaces, capabilities, native references/material slots and hash-bound NPZ/FBX/BGEO. The ordinary branch emits native references; `materialize_procedural_record` is a separate uncalled helper. |
| Native construction kit: `kit_id` | Registry `modular_kits[].kit_ref` → `KIT.json` → `registered_modular_kits` / final `assembly_layout` | Current consumer dispatches exactly `native_modular_courtyard.v001`. Inventory is not dispatch: eight configured construction entries, seven selected keys, 96 other members without decoration dispatch. Other kits need their own supported recipe. |
| Area use and actual HDA | `AREA_PROFILE.json`: `source`, `table`, digest/release, `hda`, `building_assembly_contract` → existing configured workflow | [Six-profile binding index](../../Staging/HoudiniBankConsolidation_2026-10-18/CATALOG.json) records five distinct native HDA/source bindings and their registries. `HDA_CATALOG_RECEIPT.json` is historical Cook output, never an input catalog to edit. |
| Delivery evidence and next action | Existing ROW-G01/HDA04 → [appended DELIVERY_ITEMS.json](../../Staging/HoudiniBankFixes_2026-10-18/DELIVERY_ITEMS.json) → [filtered queue](../../Staging/HoudiniBankConsolidation_2026-10-18/DELIVERY_QUEUE.csv) | Fifty selected canonical meshes: 39 new exact-revision contact/facing qualifications and 11 preserved prior reviews, current-row intersection and explicit owners. Assembly modules use their registry/manifests and [native evidence](../../Staging/BankGapValidation_2026-10-18/NATIVE_EVIDENCE.json), not duplicate canonical whole-building rows. |

Refresh the projection from the project root with `python Staging/HoudiniBankConsolidation_2026-10-18/verify_bank.py`. It reads saved inputs and writes only its own `CATALOG.json` and `DELIVERY_QUEUE.csv`; no application launch or evaluation. It rejects digest/identity/revision/source mismatches before publishing. Its input-source pins are documented in `INPUTS.json`; if a legitimate revision changes, the owner must reconcile that revision and its evidence before updating pins. The protected baseline deliberately detects concurrent changes. This check does not publish bank rows, measure contact or qualify rendering.

The [sixth-binding reconciliation](../../Staging/HoudiniBankImprovementRoadmap_2026-10-18/N02/BINDING_RECONCILIATION.json) verifies that the new run profile shares the already verified Shujaiya native HDA, external source bytes and registry. Its current protection snapshot preserves 249 files, including the new target. The only drift from the earlier protection snapshot was the documented manager addition to `AGENTS.md` and three appended ordinary-run acquire/release pairs in `EDITOR_OWNER.txt`; the previous file and the ledger prefix were verified unchanged. Older snapshots remain historical evidence. The delivery CSV's per-item output columns retain their earlier fifty-item scope; use the later run/intersection below for current selection and lifecycle evidence.

## Shared bank snapshot

Native table: `/Game/Project/Shared/ModelBank/DT_EnvironmentBank_AnyArea`.

Current retained result: [18 October permanent bank fixes](../../Staging/HoudiniBankFixes_2026-10-18/RESULT.md). Fresh typed rows: [CURRENT_NATIVE_BANK_READBACK](../../Staging/HoudiniBankFixes_2026-10-18/CURRENT_NATIVE_BANK_READBACK.json). The preceding [marked-item removal](../../Staging/BankMarkedRemoval_2026-10-18/RESULT.txt), [8 October publication](../../Staging/SharedBankConnection_2026-10-08/RESULT.json) and [NATIVE_HANDOFF](../../Staging/SharedBankConnection_2026-10-08/NATIVE_HANDOFF.txt) remain historical evidence for their exact scope.

| Measure | Dated verified state |
| --- | --- |
| Catalog records | 1,295 |
| Native object paths | 1,050; 20 selected unused native model packages were deleted on 18 October |
| Records without a native object path | 245, including 20 disabled user-removal identity records |
| Enabled rows | 66: 64 mesh rows and 2 surface material rows |
| Explicit holds | 1,113; all earlier holds preserved and all 141 user-selected identities excluded |
| Other inactive states | 116: 89 missing a placement role, 26 vegetation rows, 1 placement configuration incomplete |
| Native table SHA256 | `f290477d9222f4b1140be46a157b5db6158d47a1ee2df64311e6742d5cfaef3b` |
| Typed catalog digest | `6f9ee7bacd0622d1e1ac8ca1628618f16806b66dd5edd7e9230be4ff1fe9bd80` |

The earlier 18 October removal transaction removed 20 unreferenced selected model packages and retained 121 selected packages in place because other saved packages depend on them. All 141 are held and ordinary/technical-preview disabled; 77 preview flags were turned off. That transaction left all 1,154 unselected rows and the 66 ordinary-enabled rows unchanged. The later bank fix corrected seven facing values and three contact heights across eight enabled identities, without changing eligibility, roles, bounds, identities, assets or holds. All six current profiles have the resulting digest above. The 1,295 identities remain; deleting all 141 would leave 1,154, below the retained v3 parser's 1,215-row minimum, and would break the current row-set/profile contract. [Fresh native readback](../../Staging/HoudiniBankFixes_2026-10-18/receipts/FRESH_NATIVE_VERIFICATION.json) verified the full saved typed table and the original five HDA/profile bindings; that repair made no map save or generation. The later [same-value native publication verdict](../../Staging/HoudiniBankVerificationLoop_2026-10-18/Review/Iterations/001/VERDICT.md) independently accepted the guarded fill/save/fresh-readback route; changed-value publication remains unexercised.

Visual review: [remaining bank, 1,154 entries](../../Staging/BankMarkedRemoval_2026-10-18/Gallery/INDEX.html) and [excluded dependency reserve, 121 entries](../../Staging/BankMarkedRemoval_2026-10-18/Gallery/RESERVE.html). These reuse saved thumbnails; they do not claim new renders or appearance acceptance. The original marked catalog/export and original source archives remain preserved.

Keep older `DT_EnvironmentBank_v4`, area-scope tables and the AnyArea table distinct. A retained Lebanon table with 101 enabled rows and older v4 counts do not change the shared AnyArea count above.

## Modular representations

| Representation | State and evidence |
| --- | --- |
| Reconstruction import set | 609 parts = 585 exact reconstruction parts in 20 families + 24 older extension parts across eight families. Import history: 569 imported, 34 reused and 6 later repaired/saved/freshly reopened with recorded one-triangle losses. The 24 extensions remain disabled for repeat-to-repeat texture seams; newer procedural derivatives are separate. Read the [six mesh final report](../../Staging/SixMeshRepair_2026-10-07/FINAL_REPORT.txt) and the source `WholeBuildingConversions/DELIVERY.md`. |
| Current source-derived procedural families | 30 families contain 253 modules: 78 in the first ten and 175 in the additional twenty. Current references use `ASSEMBLY_NormalSemantics_v001.json` and corrected `NormalSemantics_v001` BGEO derivatives; original manifests/files remain frozen evidence. Follow actual registry references, not every manifest found by folder search. |
| Registry records | The inspected canonical registry has 50 records: 20 older reconstruction records and 30 procedural references. This is not 50 procedural families. |
| Additional expansion | Six families / 48 native parts have source/native delivery evidence; the expanded shared integration remains a separate candidate. |
| Expanded shared integrator | [HoudiniBankIntegration STATUS](../../Staging/HoudiniBankIntegration_2026-10-07/STATUS.json) describes its own 36-family / 168-variant candidate. It reports native execution and completion still pending. |
| Managed Courtyard successor | The v025 engineering delivery remains inactive; use its [frozen connection handoff](../../Staging/ManagedModularKits_2026-10-07/Operator/Continuation_01a11636/FrozenV025Delivery/CONNECTION_HANDOFF.txt) for append-only deltas and qualification limits. |

These lanes overlap in parent identities and derivatives. Do not add their counts into one total of usable models.

## Resolve the target area

The inspected profile folders below [Staging/ModelBank](../../Staging/ModelBank/) are:

| Profile folder | Imported external HDA source under `GeoCity_city_v015_PermanentBank/revisions/` |
| --- | --- |
| `GazaShujaiyaIntegration_2026-10-02` | `20261018_normal_semantics_v001/20261017_stable_bank_instancers_v001/GeoCity_city_v015_PermanentBank_StableBankInstancers_v001.hdalc` |
| `GazaShujaiya_Run_20261018` | Same saved shared HDA/source and registry as `GazaShujaiyaIntegration_2026-10-02`; separate retained run map/profile |
| `Lebanon_33390778_35506639_4km` | `20261018_normal_semantics_v001/20261007_Lebanon_4km_CurrentBank/GeoCity_city_v015_CurrentBank_4km_v006.hdalc` |
| `KarmeiYosef_31850349_34907601_2km` | `20261018_normal_semantics_v001/20261008_KarmeiYosef_2km/GeoCity_city_v015_CurrentBank_2km_v002.hdalc` |
| `KarmeiYosef_31850349_34907601_4km` | `20261018_normal_semantics_v001/20261008_KarmeiYosef_4km/GeoCity_city_v015_CurrentBank_4km_KY_v002.hdalc` |
| `ElWahatEgypt_29176036_29602273_4km` | `20261018_normal_semantics_v001/20261012_ElWahatEgypt_4km/GeoCity_city_v015_CurrentBank_4km_EW_v002.hdalc` |

For the selected world, read the matching profile's `map`, `hda`, `table`, `row_count`, `catalog_sha256`, `building_assembly_contract.source_family_registry_ref`, source package and output folders. The [18 October fresh-process verification](../../Staging/HoudiniBankFixes_2026-10-18/receipts/FRESH_NATIVE_VERIFICATION.json) loaded all five actual native HDAs and checked exact import-source paths, hashes, embedded bytes and profile references; the [Houdini verification](../../Staging/HoudiniBankFixes_2026-10-18/NORMAL_VERIFICATION.json) also checked their saved registry defaults.

The latest accepted delivery is `/Game/Project/Areas/GazaShujaiya/Run_20261018/L_GazaShujaiya_Run_20261018`: 398 constructed buildings (16 whole / 382 assemblies), 7,849 native transforms, 271 mesh/material groups, 276 baked actors and one Landscape. [Verdict 003](../../Staging/HoudiniBankVerificationLoop_2026-10-18/Review/Iterations/003/VERDICT.md) covers save/fresh-reopen/repeat; [verdict 004](../../Staging/HoudiniBankVerificationLoop_2026-10-18/Review/Iterations/004/VERDICT.md) covers the subsequent saved visible repeat and protected live handoff. Accepted map SHA256: `e775c77ca5d2123c6739f6832f32f8e6f87a05e072fa7bf5c03cee806dcd32e7`. The run uses Houdini roads, with RoadBLD rebuilding disabled. It retains 114 geometric tree proxies and seven intentionally omitted unsuccessful pole requests. Close materials/contact/roof/join review and Aviv's visual acceptance remain open.

The [saved-output intersection](../../Staging/HoudiniBankImprovementRoadmap_2026-10-18/N01_OUTPUT_INTERSECTION.json) finds 190 canonical instances using 48 of the 50 locally reviewed identities, plus 7,659 module instances using 205 module identities. No emitted canonical identity lacks the existing local contact/facing evidence; assembly-module contracts remain separate. This is saved-receipt/revision verification, not a new visual acceptance or generation.

Karmei Yosef 2 km, Karmei Yosef 4 km and El Wahat have retained saved workflow receipts at the earlier catalog digest `12552e1421d7cda8e05b0f00a22d9ac52960fa27c0c3e12502efa7c8a470b41e`. Shujaiya's [17 October connection repair](../../Staging/ConnectionRepair_2026-10-17/RESULT.md) applied that earlier digest through the ordinary menu, saved/reopened, ordinarily replaced without duplicates and saved/reopened again: 7,388 native instances and 398 constructed buildings. The 18 October user-removal transaction changed only inactive bank rows and synchronized profile digests; it did not regenerate any area or rewrite those older Cook receipts. Its new digest is native-table/reopen evidence, not a new area Cook. The linked connection record separates its output evidence from remaining appearance work. Lebanon's inspected workflow remains at baking. Use each area's later receipts for fresh reopen, post-generation edits and appearance; historical run counts are not a new scene inspection.

Rimal and Iran receipts are historical where their old active profiles/maps are absent. Do not recreate missing profiles from old batch scripts. Site-specific models such as Paz Farm and StationCafe can have native area-owned imports outside the canonical bank rows.

## Current evidence and open work

The 17 October [per-model audit][model-audit] and [external requirements comparison][requirements-audit] refine the earlier documentation review. They inspected saved definitions/data and isolated planners; they did not establish a fresh native Cook, appearance, save/reopen or regeneration. Reuse their row, family, module and consumer tables rather than treating these summaries as a second inventory.

| Queue | Dated finding and remaining work |
| --- | --- |
| `ROW-G01` / `HDA04` | The 17 October audit found 53 enabled meshes without individual contact/facing proof. The selected delivery's 39 gaps are now closed with exact-revision evidence, preserving 11 prior reviews: all 50 selected meshes are locally qualified. Fourteen other enabled mesh identities remain outside this task's review; two surface rows have their separate bindings. This does not extend native scene or appearance acceptance. |
| `ROW-V01` | The isolated HDA evaluator trusted flags for injected bad anchors/bounds/axes; no existing canonical row was found with those injected values. The [18 October publication repair](../../Staging/BankPublicationGuard_2026-10-18/RESULT.md) now rejects such changes at the shared existing-row writer before fill, using exact-revision measurements/reviews, and rejects full typed readback differences before save. [Native iteration 001](../../Staging/HoudiniBankVerificationLoop_2026-10-18/Review/Iterations/001/VERDICT.md) passed the same-value fill/save/fresh-readback path; changed-value native publication remains open. The HDA evaluator itself is unchanged; direct unsupported input can still bypass this publication boundary. |
| `HR03` / `MOD-04` | Saved wiring and numerical plans do not establish actual HAPI parts, resolved native identities/transforms/materials, shading/contact or persistence. The 18 enabled fixed families / 465 parts and 30 current procedural families / 253 modules retain their bounded offline evidence and pending native gates. |
| `HDA01` / `MOD-01` / `HR02` | Registration does not override area policy; see the reachability table below. |
| `HDA02` | Six expansion families / 48 modules are absent from all five current registries. Their preparation does not install them. |
| `HDA03` / `MOD-05` | Current Courtyard inventory is 104 identities: eight construction entries, seven potentially emitted keys, configured-unused `plain4` and 96 members without current decoration dispatch. The 96 are not proven defective meshes. |
| `ROW-G02` / `ROW-G04` / `HDA06` | The audit's 193 other inactive rows are a historical count; the current unheld inactive remainder is 116 after exclusions. Separately, the audit identified 187 held attachment cases without required consumer handling; re-intersect with current holds before assigning any case. User-excluded identities are not a repair queue. |
| `HR01` | Repaired in both builders, all 253 current BGEO modules and all required manifest/registry/HDA/profile bindings. The actual uncalled helper passed fresh rotated asymmetric geometry/normal verification; ordinary native-reference output was not activated or changed. See [result](../../Staging/HoudiniBankFixes_2026-10-18/RESULT.md). |
| `HR06` | The inactive PowerPlant alternative entrance token still mismatches its recipe. Outside this task and installed ordinary output; its source-family owner must repair it before adoption. |

Targeted **18 October** validation: [original delivery evidence](../../Staging/BankGapValidation_2026-10-18/DELIVERY_ITEMS.txt) and [result](../../Staging/BankGapValidation_2026-10-18/RESULT.txt) cover the **50 canonical meshes actually used by retained Shujaiya**, including 28 CitySample identities. That read-only run checked exact mesh revisions, ordered material groups, transforms and absence of duplicate bank output; it recorded 11 prior contact/facing reviews and 39 missing proofs. Its dated receipt remains unchanged.

The subsequent explicitly authorized [permanent-fix result](../../Staging/HoudiniBankFixes_2026-10-18/RESULT.md) inspected full native/source geometry for those 39 and appended physical support/facing evidence. Eight identities required ten field corrections; the other 31 received evidence without value changes. The 11 prior reviews remain intact. Named table/HDA saves and a separate fresh-process readback establish persistence; actual terrain contact and appearance in a regenerated area remain separately owned output work.

The original delivery validation preceded the marked-item removal and bank fixes. Saved map output remains unchanged; 42 of its mesh rows are unchanged and eight now have the explicit corrections above. Earlier whole-table/profile hashes are superseded by the current snapshot; old output receipts still describe their old digest. The 17 October queue counts remain dated evidence; the current unheld inactive count is 116. Deleted/reserved user-rejected identities are not a new qualification queue.

The five distinct current registries, consumed by six profiles, contain the 18 fixed and 30 procedural entries, but their authorizations allow only GazaRimal/GazaShujaiya. Actual current-profile reachability is:

| Current area context | Fixed families | Procedural families | Courtyard kit |
| --- | --- | --- | --- |
| GazaShujaiya | 18 | 30 | Allowed |
| GazaShujaiya_Run_20261018 | 18 | 30 | Allowed |
| Lebanon 4 km | 0 | 0 | Allowed |
| Karmei Yosef 2 km | 0 | 0 | Allowed |
| Karmei Yosef 4 km | 0 | 0 | Allowed |
| El Wahat 4 km | 0 | 0 | Allowed |

These are eligibility limits, not successful placement counts. Non-Gaza policies may retain source building shells; report that fallback separately from native bank construction. Changing permissions requires the applicable scoped decision and verification.

Do not revive stale defects: the six historical import failures were repaired as recorded above. Old `ProceduralFamilies/H0920` and active `ProceduralFamilies_Additional20/H0920` share a family ID but are different definitions; use exact paths/hashes. The old H0920 and Additional20/H0020 contain 14 incomplete inactive modules. Candidate readiness remains separate from current output.

### Consolidation verification, 18 October

[CATALOG.json](../../Staging/HoudiniBankConsolidation_2026-10-18/CATALOG.json) verifies the current typed digest, all six profile/release bindings, expected external HDALC bytes embedded in each saved native HDA, direct registry references and all 253 current modules' BGEO/NPZ/FBX hashes and native mesh/material presence. It checks all 39 appended qualifications against their exact saved rows and geometry/image/measurement hashes, preserves the 11 prior rows, and matches all 50 mesh/direct material revisions. The checker is a saved-file projection; separate [normal-transform](../../Staging/HoudiniBankFixes_2026-10-18/NORMAL_VERIFICATION.json), [fresh native persistence](../../Staging/HoudiniBankFixes_2026-10-18/receipts/FRESH_NATIVE_VERIFICATION.json) and later run verdicts above provide their executed evidence. Scene appearance is still open. Continue through the [27-topic execution breakdown](../../Staging/HoudiniBankImprovementRoadmap_2026-10-18/EXECUTION_PLAN.md).

The live Houdini GUI was independently identified as PID 11448, build 22.0.429, clean and Manual, on `ManagedCourtyardBank.hiplc`. `/obj/ManagedCourtyardBank/RetainedCity` resolves to **ManagedCourtyard v008 candidate**, not the current Shujaiya production definition. Metadata-only inspection preserved it. Never promote it based on the common `trackb::geocity_city::15.0` type name. See [session evidence](../../Staging/HoudiniBankConsolidation_2026-10-18/PREFLIGHT.json); PID and ownership are dated observations, not future authority.

## Refresh the baseline before writing

Run this read-only inventory from the active Unreal project root to enumerate current profile bindings:

```powershell
Get-ChildItem -LiteralPath '.\Staging\ModelBank' -Filter AREA_PROFILE.json -Recurse |
    ForEach-Object {
        $bankProfile = Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json
        [pscustomobject]@{
            Profile = $_.FullName
            Map = $bankProfile.map
            HDA = $bankProfile.hda
            Table = $bankProfile.table
            RowCount = $bankProfile.row_count
            CatalogDigest = $bankProfile.catalog_sha256
        }
    }
Get-FileHash -LiteralPath '.\Content\Project\Shared\ModelBank\DT_EnvironmentBank_AnyArea.uasset' -Algorithm SHA256
```

Compare against the matching native readback and selected area's references. Resolve any mismatch before applying a prepared packet. Update this page's check date, receipt links and relevant state after a reviewed publication; keep previous receipts immutable.

[model-audit]: <C:/Users/USER/.codex/visualizations/2026/10/17/01a149ff-e02e-76d0-af81-ccee283412dd/bank_model_configuration_audit/REPORT.txt>
[requirements-audit]: <C:/Users/USER/.codex/visualizations/2026/10/17/01a149ff-e02e-76d0-af81-ccee283412dd/houdini_external_requirements_review/REPORT.txt>
