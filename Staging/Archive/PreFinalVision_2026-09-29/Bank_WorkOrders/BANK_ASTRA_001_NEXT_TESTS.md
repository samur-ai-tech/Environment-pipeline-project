# BANK-ASTRA-001 — proposed follow-up tests, not authorization

All tasks below require their own scope and exclusive editor window. No Content mutation or generation is authorized by this document. CONTRACT v0.6 remains DRAFT; no BG1/Tier 1/full-city execution follows from the inspection.

## 1. H0958 leaf-material repair proof

**Problem:** existing leaf albedo has imported alpha; `Original_Submesh_1` is Opaque with alpha disconnected. Evidence: `LIVE_OBSERVATIONS.json` observations 21–27.

**Inputs:**

- Mesh: `/Game/Project/Shared/Bank_ME_v3/Vegetation/SM_H0958_CoconutPalm.SM_H0958_CoconutPalm`.
- Material: `/Game/Project/Shared/Bank_ME_v3/Vegetation/Original_Submesh_1.Original_Submesh_1`.
- Albedo: `/Game/Project/Shared/Bank_ME_v3/Vegetation/coconut_palm_leaf_3f6407d492f8_albedo_cdcdc62b95fb29.coconut_palm_leaf_3f6407d492f8_albedo_cdcdc62b95fb29`.
- Normal: `/Game/Project/Shared/Bank_ME_v3/Vegetation/coconut_palm_leaf_n_d2a3401423b4.coconut_palm_leaf_n_d2a3401423b4`.

**Proposed bounded work:** establish the intended source leaf shader, UV mapping and sidedness; authorize a separately identified derived material/mesh variant with original linkage before any save. Assign the existing albedo's alpha as the candidate opacity mask in an appropriate masked material; determine sidedness/shading from source evidence and visual tests rather than silently choosing defaults. Keep original packages intact. Review both textures' one-mip/NoMipmaps configuration as a separate change, since any new mip/compression settings need their own measured before/after comparison.

**Evidence gate:** exact old/new IDs, explicit saved paths and dependency hashes; unchanged originals; close front/back/edge and crown views with the actual UVs; no opaque rectangular cards or missing leaf undersides; mask follows leaflets without unintended holes; distance views report shimmering/popping and measured texture memory/mips; no default materials or material compilation errors. Reopen saved variant in a fresh process and reproduce appearance. Record local species/style suitability separately. Imported alpha alone cannot pass this gate. Houdini generation is a later gate.

## 2. H0013 + H0051 physical placement metadata

**Problem:** local support points, signed contact transform, semantic front/up and scale limits remain UNKNOWN. Historical bounds and pivot-to-bottom arithmetic are not contact measurements. H0013's broad gridded platform was preview scenery.

**Inputs:** exact unmodified packages in `BANK_ASTRA_001_CANDIDATES.json`. H0015 is optional comparative evidence only.

**Proposed bounded work:** first select an approved supported method that exposes exact mesh-local vertex/support coordinates and transforms. Do not write custom editor automation under this brief. Record the actual asset envelope with preview scenery excluded. Define whether catalog contact data represents a local support point or a correction vector, with units, sign, rotation and scale order. Confirm intended façade/use direction using physical features; a camera named Front is insufficient. Establish scale limits against a physical reference, not by fitting a geographic parcel.

**Evidence gate:** numeric local min/max and sampled real support coordinates; declared front/up axes with annotated mesh views; exact instance translation/rotation/scale; transformed support coordinates and differences from a known test surface; physical dimensions/source reference; unchanged original IDs/packages. Once separately authorized, check collision at passages/recesses and bin legs using actual traces or interaction, not merely primitive count. CONTRACT v0.6 §6.2 draft ground-contact rule is within 2 cm at sampled building corners; record its draft status and apply only under the approved test scope. Do not invent a bin tolerance or pass threshold that the project has not specified.

## 3. H0015 surface and performance review

**Problem:** blue/mottled glazing may be intended baked imagery or a conversion issue; the inspected mesh has 201,057 triangles and only LOD0 available.

**Proposed bounded work:** compare the exact source material/texture and intended rendering to the current façade at matching useful views. Inspect seams, normal response, storefront and roof details, and all four current bindings. If repair is needed, name a derived variant and separate approval. Later test representative repeated instances at declared distances under the project performance target; keep H0013 as the distinct taller category.

**Evidence gate:** source-versus-current screenshots with exact materials/texture paths; intended glazing outcome documented; UV/normal defects separated from authored weathering; actual instance count, distances, draw/triangle/texture costs and frame measurements with fixed conditions. No performance pass based only on triangle count. No silent replacement of the contract-named buildings.

## 4. Catalog reconciliation and coverage

**Owner:** bank manager, after editor release. Merge measured field-level additions and the H0013 erratum into canonical records while preserving old receipts, IDs and evidence tags. Do not increase unique-mesh coverage for this repeat inspection. Maintain distinct available/imported/technical-partial/rights/qualified/connected/generated/scene-verified/accepted states.

Broader-family inspection remains separate from these five rows. Rights for packs outside the exact 32 v3 assets need source/license evidence before promotion. Only ask Aviv for genuinely missing source/license documents or a style choice that evidence cannot settle.
