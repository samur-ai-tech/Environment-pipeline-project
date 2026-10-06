# Bank schema mapping response — read-only coordination

Received 2026-09-28 from Inspect GazaRimal model bank, thread 01a0e820-c6d4-7702-8e7b-55fd20f9b020, turn 01a0e8f0-46f3-7d20-b98e-252861413df9. The responder read BANK_INTERFACE_FINDINGS.md only and reports no files/editor changes. This is a proposed semantic mapping, not an approved enum or live transport proof.

| Case | Proposed mapping to existing fields |
|---|---|
| H0090 / H0091 | functional_role ibc_storage_container / drinking_water_dispenser; allowed_zones stays unknown until supported. |
| H0079 | functional_role junction_lighting_signal_assembly, representation compound_instance; orientation/clearance/graphics in technical_gaps and placement_rule_review. |
| Graphic blockers | Describe observed object separately from historical/local authenticity; use technical_gaps and next_evidence_gate. Rights do not authenticate graphics. |
| Fidelity blockers | Preserve partial technical_state; technical_eligible remains false for blocked use; list exact defect and next_evidence_gate. |
| H0013 / H0016 | representation whole_instance; integral paving included in placement envelope. Measured contact must not be replaced by reported pivot-to-bottom. |
| Domed structures | Distinct landmark/pavilion roles, whole_instance, local-reference gate; no generic housing inference. |
| Crushed car, dry/fallen palms | condition distinguishes damaged, dry-standing and dry-fallen. Dry appearance alone does not establish biological death. |
| Masonry supply versus rocks | Separate construction-supply and natural/decorative-stone roles; no unsupported rubble classification. |
| Compound plants/tires/carts | compound_instance describes composition; functional_role describes use. One placement = one mesh instance. |
| Thicket_03 | Distinct tall tree form; actual bounds/clearance, not a low-shrub mapping from its name. |
| Palms | Preserve variant_id, observed condition and envelope; do not invent scale_min/scale_max or botanical suitability. |
| Architectural parts | representation and architectural_role distinguish whole/facade/module; backing/pairing/connectors in placement_rule_review and technical_gaps. BG qualification remains open. |
| AC material | Referenced MI_baseMaterial_AC is native class Material. Integration clarification: H0650 itself remains StaticMesh; do not write Material into the mesh row's native_class. |

Identity response: preserve asset_id, paths and current variant_id. A future repaired derivative needs a stable new variant identity, source linkage and an asset revision. source_revision, index_revision and inspection_revision are different concepts and cannot substitute for an asset revision. Explicit derivative-to-source linkage and asset revision remain a proposed schema addition or sidecar binding; do not overload technical_variant_of without agreement.

Generated placement_id, constituent counts and output/instance mappings belong to the delivery ledger, not source identity. Repeated asset IDs are legitimate across different placements; repeated placement IDs require investigation.

No Tier 1 subset can be declared qualified from Run01/Run02 previews. A small subset can be nominated for qualification; technical eligibility, rights, role qualification and generation_enabled remain separate gates.

Remaining interface closure: bank owner and HDA owner freeze the actual role/representation enum binding, derivative link/revision fields, measured placement metadata, and a qualified subset. No canonical catalog edit was requested or made by this coordination.
