"""Build an offline, evidence-linked review ledger without modifying bank sources."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
INDEX = HERE / "BANK_CANDIDATE_INDEX_2026-09-29.csv"
DISPOSITION = HERE / "BANK_1215_DISPOSITION_RECORD_2026-09-29.csv"
INVENTORY = HERE / "UnifiedCatalogV2_2026-10-01" / "inventory_snapshot_v8.csv"
CATALOG = HERE / "UnifiedCatalogV2_2026-10-01" / "catalog_v2_full_disabled.csv"
INSPECTION = HERE / "Connection_2026-09-30" / "candidate_inspection.json"
POLE_AUTH = HERE / "DirectPickerPilot_2026-10-01" / "authorization.json"
LEDGER = HERE / "BANK_ASSETID_REVIEW_LEDGER_2026-10-01.csv"
REPORT = HERE / "BANK_ASSETID_REVIEW_LEDGER_2026-10-01.EN.md"

TECH_ONLY = {
    "SM_H0013_Building_04",
    "SM_H0907_Arab_x3_fbx",
    "SM_H0051_Garbagebin",
    "SM_H0958_CoconutPalm",
}
# The two identities are inferred from the prior two-palm qualification queue;
# the later shortlist only says "both earlier proposed" without naming them.
PALM_DECLINE_INFERRED = {"SM_Palm_01_03_G", "SM_Palm_01_08_G"}
SLATE_EXCLUDED = {"SM_H0094_Woodenpole"}
POLE_ID = "current_AssetsvilleTown__Meshes__StreetProps__SM_utility_pole_1"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def by_id(rows: list[dict[str, str]], key: str, label: str) -> dict[str, dict[str, str]]:
    ids = [row[key] for row in rows]
    assert len(ids) == 1215, (label, len(ids))
    assert len(set(ids)) == 1215, (label, "duplicate AssetId")
    return {row[key]: row for row in rows}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def human(value: str) -> str:
    return value.replace("_", " ").replace("  ", " ").strip()


def unique_join(parts: list[str], separator: str = "; ") -> str:
    return separator.join(dict.fromkeys(part.strip() for part in parts if part and part.strip()))


def asset_kind(row: dict[str, str]) -> str:
    cls = row["native_class"]
    scope = row["source_scope"]
    if row["record_kind"] == "family_candidate":
        members = [Path(p).name for p in row["family_member_paths"].split("|") if p]
        return f"Source family {row['name']} ({len(members)} recorded members: {', '.join(members)})"
    if cls == "StaticMesh":
        return f"Current Unreal StaticMesh {row['name']} ({human(row['representation'])})"
    if scope == "external":
        ext = Path(row["source_path"]).suffix.lower() or "source file"
        return f"External {ext} candidate {row['name']} ({human(row['representation'])})"
    if cls:
        return f"Current Unreal {cls} {row['name']}; a dependency/configuration candidate, not an instanced mesh"
    return f"Current package {row['name']}; native class unresolved in the recorded registry query"


def possible_role(row: dict[str, str], disposition: str) -> str:
    role = human(row["functional_role"]) or "unclassified role"
    place = human(row["placement"])
    if disposition == "exclude":
        return "Sky/lighting setup outside the geographic model bank; no bank placement role."
    if row["asset_id"] == POLE_ID:
        return "[documented: one-site authorization] Street pole at GazaRimal:pole_144276113_2_2 only; no general request mapping or area scope."
    if row["native_class"] in {"Material", "MaterialFunction", "MaterialInstanceConstant"}:
        return f"Possible {role} material/dependency for authored surfaces; no direct model instancing."
    if row["native_class"] == "FoliageType_InstancedStaticMesh":
        return "Possible vegetation configuration; inspect its referenced mesh separately."
    if row["native_class"] == "ObjectRedirector":
        return "Redirector only; resolve its target before considering a mesh role."
    if row["record_kind"] == "family_candidate":
        return f"[inference] Family may supply {role}; exact member and local placement role are undecided."
    return f"[inference] Possible {role}" + (f" at {place}" if place else "") + "; exact geographic request mapping is undecided."


def check_summary(row: dict[str, str], ins: dict, cat: dict[str, str]) -> str:
    checks = []
    if row["source_scope"] == "current":
        checks.append("[measured: v8] Indexed current package file exists")
        if ins.get("class"):
            checks.append(f"native class {ins['class']} resolved")
        elif row["native_class"]:
            checks.append(f"native class {row['native_class']} recorded; see per-class inspection limit")
        else:
            checks.append("native class unresolved")
        if ins.get("mesh"):
            checks.append("native AABB/material slots/LOD and Nanite queried")
            if row["native_triangles"]:
                checks.append(f"reported LOD0 triangles {row['native_triangles']}")
            if row["native_material_slots"]:
                checks.append(f"material slots {row['native_material_slots']}")
        if "unresolved_dependencies" in ins:
            checks.append(
                f"recursive registry dependency check: {len(ins.get('unresolved_dependencies') or [])} unresolved"
            )
        if row["native_preview_state"] == "observed_partial":
            checks.append("partial native visual preview recorded")
    else:
        members = ins.get("source_members") or []
        checks.append(f"[measured: v8] {len(members)} source member file(s) hashed")
        if ins.get("fbx_inspection_paths"):
            checks.append("source FBX geometry inspected in Blender 5.2.2")
        checks.append("not imported into this Unreal project")
    checks.append("[measured: 2026-10-01] v2 native catalog metadata row read disabled and rejected in GazaRimal; no asset placement")
    if row["asset_id"] == POLE_ID:
        checks.append("[measured: direct-picker pilot] Exact source mesh cooked, baked and saved at one authorized site; fresh reopen and same-input replace-bake retained one pole component and 16 map actors")
    assert cat["RunEligible"].lower() == "false"
    return unique_join(checks)


def missing_checks(row: dict[str, str], ins: dict, disposition: str) -> str:
    cls = row["native_class"]
    gaps = []
    if disposition == "exclude":
        return "No bank qualification work while finally excluded; any reversal would reopen rights, visual, technical and role checks."
    if row["record_kind"] == "family_candidate":
        gaps.append("member-level identity/visual comparison and exact mesh choice")
    elif row["source_scope"] == "external":
        gaps.append("native Unreal import, dependency closure, material appearance, scale/axis/contact and runtime cost")
    elif cls == "StaticMesh":
        gaps.append("semantic footprint/contact, front/up direction, shader appearance, collision, UV/LOD transitions and runtime cost")
        if row["native_preview_state"] != "observed_partial" and row["asset_id"] != POLE_ID:
            gaps.append("individual native visual preview")
    elif cls == "ObjectRedirector":
        gaps.append("resolve redirector to a current loadable mesh, then inspect that exact target")
    elif cls in {"Material", "MaterialFunction", "MaterialInstanceConstant"}:
        gaps.append("surface assignment, shader appearance and source/texture terms; direct model role inapplicable")
    elif cls == "FoliageType_InstancedStaticMesh":
        gaps.append("referenced mesh identity, species/zone fit, material/wind/LOD and instancing behaviour")
    else:
        gaps.append("native class/load resolution and target identity")
    unresolved = ins.get("unresolved_dependencies") or []
    if unresolved:
        gaps.append(f"{len(unresolved)} unresolved dependency path(s): {', '.join(unresolved)}")
    assignments = ins.get("material_assignments") or []
    unassigned = [str(a.get("slot", "<unnamed>")) for a in assignments if not a.get("material")]
    if unassigned:
        gaps.append("unassigned material slot(s): " + ", ".join(unassigned))
    if row["name"] == "SM_H0958_CoconutPalm":
        gaps.append("source-backed foliage mask/two-sided repair and its native appearance; derivative is not adopted")
    if row["name"] == "SM_H0636_Acacia":
        gaps.append("opaque white foliage cards and missing mask/source information must be repaired and rechecked")
    if row["name"] == "SM_H0013_Building_04":
        gaps.append("actual footprint and support points; earlier apparent paving was editor preview floor")
    if row["name"] == "SM_H0051_Garbagebin":
        gaps.append("bin-only height/support points and attached litter clearance")
    if row["asset_id"] == POLE_ID:
        gaps.append("pilot visual judgment, exact rights terms, semantic contact/cross-arm clearance, general catalog release and placement on other sites/areas")
        gaps.append("Cook/LayerInfo package-reference audit; the one-site repeat bake left residue")
    else:
        gaps.append("exact rights/source-to-file and Aviv visual/use decision; scoped generation and lifecycle proof")
    return unique_join(gaps)


def hold(row: dict[str, str], disposition: str) -> str:
    name = row["name"]
    if disposition == "exclude":
        return "final_exclude_sky_lighting"
    if name in TECH_ONLY and row["source_package"] == "Bank_ME_v3":
        return "technical_check_only"
    if name == "SM_H0636_Acacia" and row["source_package"] == "Bank_ME_v3":
        return "repair_hold_opaque_foliage_cards"
    if row["asset_id"] == POLE_ID:
        return "one_site_direct_picker_pilot_only_catalog_disabled"
    if name in PALM_DECLINE_INFERRED and row["source_package"] == "Palms_Pack_01":
        return "declined_from_current_review_slate_id_inferred"
    if name in SLATE_EXCLUDED and row["source_package"] == "Bank_ME_v3":
        return "excluded_from_current_review_slate"
    return "all_disabled_reserve"


def next_action(row: dict[str, str], ins: dict, disposition: str) -> str:
    if disposition == "exclude":
        return "Keep source preserved; no bank action unless Aviv explicitly reverses the sky/lighting exclusion."
    if row["name"] in PALM_DECLINE_INFERRED and row["source_package"] == "Palms_Pack_01":
        return "Keep out of current shortlist; reconcile the exact declined IDs with Aviv's decision record before any further selection."
    if row["name"] == "SM_H0094_Woodenpole":
        return "Keep off current shortlist; preserve native preview/dependency evidence."
    if row["name"] == "SM_H0958_CoconutPalm":
        return "Prepare source-backed mask and two-sided repair checklist against the original mesh; keep derivative and source distinct."
    if row["name"] == "SM_H0636_Acacia":
        return "Trace missing foliage texture/mask source and prepare isolated repair/recheck proposal."
    if row["asset_id"] == POLE_ID:
        return "Reconcile the exact one-site pilot receipt, asset revision and source/rights record; no catalog release or added site."
    if row["record_kind"] == "family_candidate":
        return "List exact members and compare existing hashes/roles offline; nominate one member for a later scoped native check."
    if row["source_scope"] == "external":
        return "Reconcile existing member hashes, source product and texture references; prepare a bounded import/visual check request, without importing now."
    if row["native_class"] == "ObjectRedirector":
        return "Trace the recorded redirector target offline; carry any later review under the resolved mesh AssetId."
    if row["native_class"] != "StaticMesh":
        return "Trace existing dependency and intended surface/configuration role offline; do not treat this package as an instance mesh."
    if ins.get("unresolved_dependencies"):
        return "Identify the unresolved dependency paths from the saved registry receipt and find exact source packages; defer material repair until scoped."
    if row["native_preview_state"] != "observed_partial":
        return "Prepare this exact AssetId and recorded AABB/dependencies for a later bounded native visual and anchor check."
    return "Reconcile recorded preview with AABB/dependencies; prepare exact anchor, direction, clearance and cost checks for a later bounded session."


def rights_decision(row: dict[str, str], disposition: str) -> str:
    aid = row["asset_id"]
    package = row["source_package"]
    if disposition == "exclude":
        return f"No current bank-use decision for {aid}; only Aviv may explicitly reverse this exclusion."
    if row["native_class"] == "ObjectRedirector":
        return f"No use decision on redirector {aid}. Resolve its exact mesh target first; Aviv must decide rights for that target and dependencies if selected."
    if row["name"] in PALM_DECLINE_INFERRED and package == "Palms_Pack_01":
        return f"The two declined palm IDs are unrecorded here; {aid} is a probable match only. Keep disabled. If Aviv identifies and reconsiders this exact ID, he must then decide its rights/use after package terms are verified."
    if package == "Bank_ME_v3":
        return f"Aviv's existing permission covers technical qualification of {aid} only. For generation/distribution, Aviv must decide exact allowed use after its originating product, mesh, textures and applicable terms are matched."
    if row["asset_id"] == POLE_ID:
        return f"Aviv allowed only {aid} at GazaRimal:pole_144276113_2_2 as a technical pilot. He must decide any broader use separately after account, acquisition date, applicable terms and exact dependency match."
    if row["record_kind"] == "family_candidate":
        return f"Aviv must name exact members of {aid}, then confirm account/creator permission, product/version/terms and intended generation/distribution scope for each selected member."
    if package == "StarterContent":
        return f"Aviv must identify the engine/source terms covering {aid} and decide intended generation/distribution use; do not assume a Fab receipt is needed."
    return f"For {aid}, Aviv must confirm authorized account or creator grant, acquisition/date/terms, exact model and dependency mapping, and intended generation/distribution scope."


def visual_decision(row: dict[str, str], disposition: str) -> str:
    aid, name = row["asset_id"], row["name"]
    if disposition == "exclude":
        return "No bank visual selection while excluded; sky appearance belongs to the separately owned lighting/sky work."
    if row["native_class"] == "ObjectRedirector":
        return f"No visual selection for redirector {aid}; Aviv reviews the resolved target mesh only."
    if name in PALM_DECLINE_INFERRED and row["source_package"] == "Palms_Pack_01":
        return f"The two earlier palm proposals were declined, but their exact IDs are not recorded here. Treat {aid} as a probable match and keep it off the current slate pending Aviv's exact ID clarification."
    if name in TECH_ONLY and row["source_package"] == "Bank_ME_v3":
        return f"{aid} is technical-check-only. Aviv must later decide exact geographic/style/condition fit and allowed role/area before any use."
    if name == "SM_H0094_Woodenpole":
        return f"{aid} is excluded from the current shortlist; only Aviv can request renewed visual selection."
    if aid == POLE_ID:
        return f"Aviv must inspect the one-site result for {aid} and decide pole appearance, cross-arm direction, contact and roadside clearance; no general site approval exists."
    if row["record_kind"] == "family_candidate":
        return f"Aviv must select or reject exact member(s) of {aid}, then decide role, condition/style and allowed area or zone from visual evidence."
    role = human(row["functional_role"]) or "proposed role"
    return f"Aviv must accept or reject {aid} for {role}, including style/condition, local relevance and exact allowed area/zone after an individual visual review."


def main() -> None:
    index_rows = read_csv(INDEX)
    disposition_rows = read_csv(DISPOSITION)
    inventory_rows = read_csv(INVENTORY)
    catalog_rows = read_csv(CATALOG)
    inspection_rows = json.loads(INSPECTION.read_text(encoding="utf-8-sig"))
    pole_auth = json.loads(POLE_AUTH.read_text(encoding="utf-8-sig"))
    index = by_id(index_rows, "asset_id", "index")
    dispositions = by_id(disposition_rows, "asset_id", "disposition")
    inventory = by_id(inventory_rows, "asset_id", "v8 inventory")
    catalog = by_id(catalog_rows, "AssetId", "disabled v2 catalog")
    inspection = by_id(inspection_rows, "asset_id", "v8 inspection")
    keys = set(index)
    assert keys == set(dispositions) == set(inventory) == set(catalog) == set(inspection)
    assert pole_auth["asset_id"] == POLE_ID and pole_auth["catalog_run_eligible"] is False

    anomalies: list[str] = []
    for aid, row in index.items():
        disp, inv, cat, ins = dispositions[aid], inventory[aid], catalog[aid], inspection[aid]
        for field in ("family_id", "source_scope", "source_package", "rights_state"):
            if field in disp and disp[field] != row[field]:
                anomalies.append(f"{aid}: disposition {field} differs")
        for field in ("family_id", "name", "source_scope", "source_package", "source_path", "record_kind", "functional_role", "native_class", "rights_state", "technical_state"):
            if inv[field] != row[field]:
                anomalies.append(f"{aid}: inventory {field} differs")
        if cat["FamilyId"] != row["family_id"] or ins["family_id"] != row["family_id"]:
            anomalies.append(f"{aid}: family crosswalk differs")
        if row["source_scope"] == "current" and row["native_class"] == "StaticMesh":
            if cat["ObjectPath"] != row["unreal_object_path"]:
                anomalies.append(f"{aid}: v2 object path differs")
        elif cat["ObjectPath"]:
            anomalies.append(f"{aid}: non-native-mesh v2 object path is nonblank")
        if row["qualified"] != "no" or row["generation_enabled"] != "false":
            anomalies.append(f"{aid}: index eligibility unexpectedly changed")
        if cat["RunEligible"] != "false" or float(cat["SelectionWeight"]) != 0.0:
            anomalies.append(f"{aid}: catalog eligibility unexpectedly changed")
        if cat["ReleaseId"] or cat["DecisionId"]:
            anomalies.append(f"{aid}: unexpected release/decision ID")
        if disp["final_state"] not in {"reserve", "exclude"}:
            anomalies.append(f"{aid}: unexpected final disposition")
    assert not anomalies, "\n".join(anomalies[:30])

    headers = [
        "AssetId", "Name", "FamilyId", "RecordKind", "SourceScope", "SourcePackage",
        "SourcePath", "SourceMemberCount", "SourceMemberNames", "CurrentFilePresence", "UnrealObjectPath",
        "NativeClass", "WhatAssetIs", "PossibleEnvironmentalRole", "RoleBasis",
        "PreliminaryIndexDecision", "PreliminaryDecisionReason", "FinalDisposition20260929",
        "CurrentReviewHold", "TechnicalState", "RightsState", "RecordedChecks",
        "NativePreviewState", "RecordedVisualObservation", "UnresolvedDependencyCount",
        "UnresolvedDependencyPaths", "MeasuredDimensionsCm", "ReportedTriangles",
        "ReportedMaterialSlots", "PriorTechnicalGaps", "MissingChecks",
        "SafeNextTechnicalAction", "ExactAvivRightsDecisionNeeded",
        "ExactAvivVisualDecisionNeeded", "CatalogRowName", "CatalogObjectPath",
        "CatalogRunEligible", "Qualified", "GenerationEnabled", "Generated",
        "VisuallyVerified", "Accepted", "EvidenceRefs",
    ]
    output = []
    checked_member_paths = 0
    for row in index_rows:
        aid = row["asset_id"]
        disp, cat, ins = dispositions[aid], catalog[aid], inspection[aid]
        unresolved = ins.get("unresolved_dependencies") or []
        member_paths = [Path(p) for p in row["family_member_paths"].split("|") if p]
        members = [p.name for p in member_paths]
        checked_member_paths += len(member_paths)
        present = sum(p.is_file() for p in member_paths)
        assert len(member_paths) == int(row["member_count"]), (aid, "member count mismatch")
        assert present == len(member_paths), (aid, "missing source member file")
        dimensions = " × ".join(row[f"dimensions_{axis}_cm"] for axis in "xyz") if row["dimensions_x_cm"] else ""
        source_refs = unique_join([
            "BANK_CANDIDATE_INDEX_2026-09-29.csv (v8 contents)",
            "BANK_1215_DISPOSITION_RECORD_2026-09-29.csv",
            "UnifiedCatalogV2_2026-10-01/inventory_snapshot_v8.csv",
            "UnifiedCatalogV2_2026-10-01/catalog_v2_full_disabled.csv",
            "Connection_2026-09-30/candidate_inspection.json",
            row["inspection_evidence"],
            "BANK_DISTINCT_CANDIDATE_SHORTLIST_2026-10-01.EN.md" if row["name"] in PALM_DECLINE_INFERRED | SLATE_EXCLUDED or aid == POLE_ID else "",
            "DirectPickerPilot_2026-10-01/authorization.json" if aid == POLE_ID else "",
            "../TrackA_Tests/HoudiniCityProof/GeoCity_direct_picker_UI_2026-10-01/RESULT.md" if aid == POLE_ID else "",
            "../TrackA_Tests/HoudiniCityProof/GeoCity_v006_update_UI_2026-10-01/rimal_v6_live_receipt.json",
        ], " | ")
        output.append({
            "AssetId": aid,
            "Name": row["name"],
            "FamilyId": row["family_id"],
            "RecordKind": row["record_kind"],
            "SourceScope": row["source_scope"],
            "SourcePackage": row["source_package"],
            "SourcePath": row["source_path"],
            "SourceMemberCount": row["member_count"],
            "SourceMemberNames": " | ".join(members),
            "CurrentFilePresence": f"{present}/{len(member_paths)} files present on 2026-10-01",
            "UnrealObjectPath": row["unreal_object_path"],
            "NativeClass": row["native_class"],
            "WhatAssetIs": asset_kind(row),
            "PossibleEnvironmentalRole": possible_role(row, disp["final_state"]),
            "RoleBasis": "[documented] partial native preview plus source semantics" if row["native_preview_state"] == "observed_partial" else "[inference] source name/path and inventory classification only",
            "PreliminaryIndexDecision": row["decision"],
            "PreliminaryDecisionReason": row["decision_reason"],
            "FinalDisposition20260929": disp["final_state"],
            "CurrentReviewHold": hold(row, disp["final_state"]),
            "TechnicalState": row["technical_state"],
            "RightsState": row["rights_state"],
            "RecordedChecks": f"[measured: 2026-10-01] {present}/{len(member_paths)} source member files present; " + check_summary(row, ins, cat),
            "NativePreviewState": row["native_preview_state"],
            "RecordedVisualObservation": row["native_visual_observation"] or row["source_visual_observation"],
            "UnresolvedDependencyCount": str(len(unresolved)),
            "UnresolvedDependencyPaths": " | ".join(unresolved),
            "MeasuredDimensionsCm": dimensions,
            "ReportedTriangles": row["native_triangles"],
            "ReportedMaterialSlots": row["native_material_slots"],
            "PriorTechnicalGaps": row["technical_gaps"],
            "MissingChecks": missing_checks(row, ins, disp["final_state"]),
            "SafeNextTechnicalAction": next_action(row, ins, disp["final_state"]),
            "ExactAvivRightsDecisionNeeded": rights_decision(row, disp["final_state"]),
            "ExactAvivVisualDecisionNeeded": visual_decision(row, disp["final_state"]),
            "CatalogRowName": cat["Name"],
            "CatalogObjectPath": cat["ObjectPath"],
            "CatalogRunEligible": "false",
            "Qualified": "no",
            "GenerationEnabled": "false",
            "Generated": row["generated"],
            "VisuallyVerified": row["visually_verified"],
            "Accepted": row["accepted"],
            "EvidenceRefs": source_refs,
        })

    with LEDGER.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    again = read_csv(LEDGER)
    assert len(again) == 1215 and len({r["AssetId"] for r in again}) == 1215
    assert [r["AssetId"] for r in again] == [r["asset_id"] for r in index_rows]
    assert all(r["CatalogRunEligible"] == "false" and r["Qualified"] == "no" and r["GenerationEnabled"] == "false" and r["Accepted"] == "no" for r in again)
    assert checked_member_paths == 1320

    final_counts = Counter(r["FinalDisposition20260929"] for r in again)
    holds = Counter(r["CurrentReviewHold"] for r in again)
    source_counts = Counter(r["SourceScope"] for r in again)
    kinds = Counter(r["RecordKind"] for r in again)
    classes = Counter(r["NativeClass"] or "external_or_unresolved" for r in again)
    rights = Counter(r["RightsState"] for r in again)
    unresolved_rows = sum(bool(r["UnresolvedDependencyPaths"]) for r in again)
    report = f"""# AssetId-level model-bank review ledger — 2026-10-01

This is an **offline crosswalk and per-AssetId review**, not a model qualification, release or visual acceptance. The CSV preserves the exact 1,215 AssetIds and index order, adds one assessment row for each, and keeps the historical preliminary index decision separate from the final 2026-09-29 disposition and later 2026-10-01 selection holds. No source asset, native DataTable, HDA, Unreal session, Houdini session or Linear item was changed.

## Scope and result

- [measured: source CSV/JSON crosswalk and current filesystem] **1,215 unique AssetIds**, **324 families**, {source_counts['current']} current and {source_counts['external']} external rows; {kinds['asset_candidate']} asset candidates and {kinds['family_candidate']} family candidates. All {checked_member_paths} recorded source-member path references currently resolve to files, and each row's member count matches its path list. The index, disposition, v8 inventory, v2 disabled catalog and v8 candidate-inspection JSON have identical AssetId sets. Family, scope, source package, rights state, native class and technical state match across applicable records. The 898 current native StaticMesh paths match the disabled v2 catalog; the 317 other catalog paths are blank by design.
- [documented: final disposition] **{final_counts['reserve']} reserve, {final_counts['exclude']} exclude**. The two final exclusions are `SM_Sky_sphere_overcast` and `SM_Sky_sphere_sunday`; the index's 28 preliminary `decision=exclude` suggestions are not the final disposition.
- [measured: disabled catalog and live GazaRimal receipts] All 1,215 v2 rows remain `RunEligible=false`, weight zero and have blank ReleaseId/DecisionId. v004/v006 native readback observed 1,215 disabled rows and zero catalog model instances. The row metadata's transport is not native placement of the corresponding models.
- [measured: v8 inspection] {classes['StaticMesh']} current StaticMeshes had native bounds, material-slot, LOD/Nanite and dependency queries; {unresolved_rows} candidate rows reach at least one unresolved dependency. The external source and family rows were hashed but were not imported into this project. {sum(r['NativePreviewState'] == 'observed_partial' for r in again)} current rows have only partial native visual previews.
- [documented: owner decision; measured: direct-picker receipt] Four exact `Bank_ME_v3` rows (`H0013`, `H0907`, `H0051`, `H0958`) remain **technical-check-only**. `SM_H0636_Acacia` retains a foliage repair hold. `SM_utility_pole_1` has one-site direct-picker pilot permission at `GazaRimal:pole_144276113_2_2`; the official one-site cook, named bake, fresh reopen and same-input replace-bake held at one pole component and 16 map actors, while Cook/LayerInfo residue remained. Its canonical v2 row stays disabled. `SM_H0094_Woodenpole` is out of the current review slate.
- [inference, held conservatively] The later shortlist says Aviv declined "both earlier proposed" `Palms_Pack_01` meshes but does not give AssetIds. The preceding two-palm qualification queue named `SM_Palm_01_03_G` and `SM_Palm_01_08_G`; those two rows are marked `declined_from_current_review_slate_id_inferred`. This does **not** alter their final 2026-09-29 reserve disposition. Confirm the exact two IDs against Aviv's decision record before changing any source index or asking for renewed selection. All 33 Palms Pack rows remain disabled.

## How to read the CSV

`WhatAssetIs` and `PossibleEnvironmentalRole` use the exact indexed name, native class, representation and semantic role; a role based on names and paths is explicitly an inference. `RecordedChecks` summarizes the existing per-AssetId native or source inspection and the disabled table transport. `RecordedVisualObservation` quotes prior index evidence where available; it is not a new visual review. `PriorTechnicalGaps` preserves the original index wording even where later v8 measurements addressed a narrow part of it; `MissingChecks` states the remaining practical checks after the measured native/source inspection. `SafeNextTechnicalAction` is a preparation or future bounded check, never a release instruction. The rights and visual columns identify decisions Aviv must make for each exact ID, with deferral for excluded/held rows.

The v8 registry query measured 898 current StaticMeshes, but local AABBs, zero unresolved dependencies and package presence do not certify anchor, direction, shader appearance, collision, runtime cost or contextual suitability. The 27 external family records are grouping candidates, not selectable meshes. Nonmesh classes (materials, material functions, foliage configurations and redirectors) are explicitly identified so a row's catalog presence cannot be mistaken for a usable StaticMesh.

## Source and verification fingerprints

| File | SHA-256 |
| --- | --- |
| `{INDEX.name}` | `{sha256(INDEX)}` |
| `{DISPOSITION.name}` | `{sha256(DISPOSITION)}` |
| `{INVENTORY.relative_to(HERE)}` | `{sha256(INVENTORY)}` |
| `{CATALOG.relative_to(HERE)}` | `{sha256(CATALOG)}` |
| `{INSPECTION.relative_to(HERE)}` | `{sha256(INSPECTION)}` |
| `{LEDGER.name}` | `{sha256(LEDGER)}` |

The script reparses the written CSV and verifies 1,215 unique IDs in source order; exact ID sets, selected metadata and all-disabled flags are asserted. Counts: current/external `{dict(source_counts)}`, final dispositions `{dict(final_counts)}`, record kinds `{dict(kinds)}`, current review holds `{dict(holds)}`, rights states `{dict(rights)}`. No live application check was run for this ledger.

## Sources and limits

- [measured: `BANK_CANDIDATE_INDEX_2026-09-29.csv` (v8 content), `Connection_2026-09-30/candidate_inspection.json`, `BANK_1215_DISPOSITION_RECORD_2026-09-29.csv`, `UnifiedCatalogV2_2026-10-01/inventory_snapshot_v8.csv`, `UnifiedCatalogV2_2026-10-01/catalog_v2_full_disabled.csv`]
- [documented: `Connection_2026-09-30/RESULT.md`, `UnifiedCatalogV2_2026-10-01/FULL_DISABLED_CATALOG_RESULT.md`, `BANK_DISTINCT_CANDIDATE_SHORTLIST_2026-10-01.EN.md`, `RIGHTS_DECISION_PACKET_2026-09-29.EN.md`, `DirectPickerPilot_2026-10-01/authorization.json`, `../TrackA_Tests/HoudiniCityProof/GeoCity_direct_picker_UI_2026-10-01/RESULT.md`, `../CURRENT_STATE.md`]
- [not run: live editor/Houdini, new mesh previews, new rights-account verification, placement or qualification tests]
"""
    REPORT.write_text(report, encoding="utf-8")
    print(json.dumps({
        "ledger": str(LEDGER), "report": str(REPORT), "rows": len(again),
        "unique_ids": len({r["AssetId"] for r in again}), "families": len({r["FamilyId"] for r in again}),
        "final_dispositions": dict(final_counts), "review_holds": dict(holds),
        "unresolved_dependency_rows": unresolved_rows, "source_member_paths_present": checked_member_paths, "sha256": sha256(LEDGER),
    }, indent=2))


if __name__ == "__main__":
    main()
