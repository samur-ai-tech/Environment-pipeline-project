# Native-inspection findings for the bank-to-HDA interface

2026-09-28. Inspection sidecar only. No canonical bank data or generated asset was modified. Exact existing IDs and paths are in COMBINED_NATIVE_REVIEW.json.

The existing Topic 3 BANK_INTERFACE_REQUIREMENTS.md and bank_field_alias_map.proposed.json remain the proposed wire contract. The following are newly observed reasons to make the semantic mapping explicit. These are requirements for the owner to bind to the existing schema, not instructions to invent data or restructure the bank.

## Requested owner confirmation

| Affected assets | Observed distinction | Required explicit metadata or rule |
|---|---|---|
| H0090 Watertank; H0091 Watertank_001 | IBC caged storage container versus drinking-water dispenser | Separate functional roles and allowed placement zones; neither may default to roof water storage from its filename. |
| H0079 Streetlight | One mesh includes lamp, traffic signals, pedestrian box and Rue du Liban sign | Combined junction assembly representation, mounting/front/road-side orientation, full bounds/clearance, graphic variant approval. Do not bind to the generic lamp pool. |
| H0082/H0083 Streetsign; H0081 cabinet; H0091 dispenser | Sign meanings/posters have not been authenticated | Approved local/period graphic state or explicit hold. Unknown is ineligible, not an assumed generic sign. |
| H0636 Acacia; H0647 Nopal; H0958 CoconutPalm; H0650 AC; H0902/H0903; H0058/H0089 | Visible material/fidelity blockers or unresolved artifacts | Technical eligibility must stay false/unknown for selection until the applicable repair gate passes. Inspection visibility must not become qualification or generation_enabled. |
| H0013/H0016 whole buildings | Integral paving/base extends the placement envelope | Verified local bounds and contact point plus footprint policy; HDA must account for the attached base. Do not substitute bounds-bottom or reported pivot scalar for the measured signed contact vector. |
| H0905/H0906/H0907 Arab buildings | Distinctive domed structures | Landmark/pavilion reserve role requiring an exact local match; no ordinary residential assignment solely from an Arab label. |
| H0039 crushed car; dry/fallen palms | Condition changes intended scene role | Separate damaged/dead/fallen condition from healthy/intact pools and explicit allowed zones. Preserve variants; do not delete. |
| H0077 Stones_Stack; Stone_07/08 | Orderly masonry supply versus natural/decorative boulders | Construction-storage role versus natural stone; neither automatically means rubble. |
| H0647 Nopal; Thicket_01/02; H0089 Tires; H0034 Cart/H0043 Foodcart | A single mesh includes multiple visible plants/stems/tires/accessories | Declare representation as compound/cluster where appropriate and mesh-instance count semantics. One placement_id = one placement; actor count and semantic constituent count are different measures. Preserve footprint and every contact base requirement. |
| Thicket_03 | Tall single-trunk tree-like form, unlike Thicket_01/02 | Distinct form/height/clearance; do not infer low shrub from family name. |
| Palms_01_01 through _16 | Height, curvature, crown clearance and healthy/dry/fallen state vary | Preserve variant IDs and actual envelopes; approved species/maintenance/period evidence; no generic uniform scaling until measured limits exist. |
| Courtyard/storefront/PBG parts | Whole meshes, exterior/interior parts and modules are different | Explicit representation and pairing/backing/connector metadata. Reference-only placement cannot supply module polygons for Labs Building Generator. BG1 remains open. |
| AC Material named MI_baseMaterial_AC | It opens as a base Material graph | Verify actual native class; prefixes are not class evidence. Material/function/instance distinctions need real class and binding receipts. |

## Identity and measurement rules to preserve

1. Keep the existing asset_id unchanged and bind its exact object path. Observed role corrections are attributes, not ID renames. Any future repaired derivative needs a new stable variant identity and asset revision linked to its source; no same-name merge. The bank owner chooses that identity, not this report.
2. Keep catalog row identity, source asset identity, selected variant identity and generated placement_id separate. Sort by stable IDs, never catalog row order, before deterministic selection.
3. Count one mesh instance per placement, then measure ISM/HISM component instance totals, native actor totals and unique placement IDs separately. A cluster with three stems is not three HDA placements. A merged output needs a delivery ledger mapping every placement ID to its output/instance identity.
4. Compare the frozen expected ID multiset and transforms after cook, bake-with-replace and fresh reopen. Detect duplicates by repeated placement IDs plus unexpected coincident transforms/reference pairs; repeated asset IDs across legitimate placements are not duplicates. Do not use actor labels or volatile component instance indices as stable IDs.
5. Save/package lists, layer assets, Temp exclusions and reopen proof remain governed by the Topic 3 runbook. No bank inspection result establishes cook, bake or persistence.
6. Unknown front/up/contact/scale limits, species, graphics, material custom-data channel use or rights remain unknown and blocked for affected uses. Do not auto-fill them from filenames, triangle counts or thumbnail appearance.

Please confirm how these distinctions map to the current functional_role, representation, condition, allowed_zones, technical_state/technical_eligible, variant_id and revision fields. Also identify the small qualified subset intended for Tier 1 when available. A finished full bank is not needed to answer the mapping question. No bank edits or editor action is requested by this coordination note.
