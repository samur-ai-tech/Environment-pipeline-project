"""Retained ordinary-prop jobs. Default execution writes this directory only.

The bank integrator may explicitly call integrate_reviewed() inside its leased
Unreal process. Importing this module never imports Unreal or changes shared data.
No generation, map save, eligibility/rights release, or editor launch is provided.
"""
import argparse
import collections
import copy
import hashlib
import importlib
import json
import math
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTEGRATION = HERE.parents[1]
ROOT = HERE.parents[3]
PREP = ROOT / "Staging/BankPreparation_2026-10-04"
CATALOG = ROOT / "Staging/ModelBank/PermanentIntegration_2026-10-02/catalog_v4_source.json"
AREAS = ["GazaRimal", "GazaShujaiya"]
RULES = {"small_prop": "zone_ground_prop", "street_prop": "roadside_prop", "street_pole": "roadside_pole"}
HOST_CONTEXTS = {"roof_or_wall_host_attachment", "sign_host_attachment_or_measured_standalone_pole",
                 "linear_boundary_alignment", "road_or_surface_host"}
# Exact corrections to overbroad preparation triage; they do not release holds.
EXCLUDED_EXTERNAL = {
    "external.H0134": "MetalFooter is a support component; complete supported host is not established.",
    "external.H0151": "Storelight requires a store/overhead attachment frame.",
    "external.H0152": "WallStreetLamp requires a wall attachment frame.",
    "external.H0088": "Tea_Set requires a supporting table/surface; no arbitrary ground scatter.",
    "external.H0093": "Woodenladder requires its measured support/leaning host context.",
    "external.MOUT_FAMILY_HangingLamps": "Hanging fixture family requires overhead hosts.",
    "external.MOUT_FAMILY_MarketStallCovers": "Stall covers require their matching stall host.",
    "external.MOUT_FAMILY_WoodenStakes": "Stakes require boundary/site alignment; no random street scatter.",
}
EXCLUDED_NATIVE = {
    "current_UtopianCity__Meshes__Brut_Master": "Unbound master record has no measured individual StaticMesh prop contract.",
    "current_AssetsvilleTown__Meshes__StreetProps__SM_roofStand_donut": "Roof-mounted commercial sign/stand; requires roof/site host.",
    "current_AssetsvilleTown__Meshes__StreetProps__SM_ladder_01": "Ladder requires measured leaning/support host.",
    "current_AssetsvilleTown__Meshes__StreetProps__SM_ladder_01a": "Ladder requires measured leaning/support host.",
    "current_AssetsvilleTown__Meshes__StreetProps__SM_ladder_small": "Ladder requires measured leaning/support host.",
}
NATIVE_HISTORICAL = {
    "current_Project__Shared__Bank_ME_v3__Props__SM_H0034_Cart": {
        "image": "H0034_Cart.jpg", "anchor_z_cm": -2.0, "forward_axis": "+X",
        "observation": "Complete wooden cart with two wheels, front support and sacks; wood and sack texture visible in the retained Unreal Lit image.",
        "contact": "Paired wheel minima at approximately -2 cm; front support minimum -3.129608 cm. Preserve up to 1.13 cm support penetration rather than lifting both wheels.",
        "facing": "Local X is the cart longitudinal axis. Static open-ground clutter has unconstrained yaw; no functional travel/traffic orientation is claimed.",
    },
    "current_Project__Shared__Bank_ME_v3__Props__SM_H0046_Foodcrate": {
        "image": "H0046_Foodcrate.jpg", "anchor_z_cm": 0.0, "forward_axis": "+Y",
        "observation": "Complete rectangular open lattice crate; textured olive surface; bottom edges visibly support the crate.",
        "contact": "Native lower 1 cm has 2633 vertices spanning the full 32.58 x 48.02 cm footprint. Authored source bottom Z=0 agrees within 0.00001 cm.",
        "facing": "Unconstrained ground-clutter yaw; +Y retained as its existing orientation convention, without assigning a functional front.",
    },
    "current_Project__Shared__Bank_ME_v3__Props__SM_H0058_Gaz": {
        "image": "H0058_Gaz.jpg", "anchor_z_cm": 0.0, "forward_axis": "+X",
        "observation": "Complete upright blue gas cylinder with base ring and top collar; source texture patches retained. No utility hookup or final art approval inferred.",
        "contact": "206 vertices in the native lower 1 cm span the base ring. Source base plane Z=0; measured minimum -0.005653 cm is negligible retained extent.",
        "facing": "Standalone static cylinder has no required horizontal facing; unrestricted yaw preserves its base support.",
    },
    "current_Project__Shared__Bank_ME_v3__Props__SM_H0059_Grill_": {
        "image": "H0059_Grill.jpg", "anchor_z_cm": 0.0, "forward_axis": "+X",
        "observation": "Complete small metal grill with four legs and textured weathered frame; this job uses it as open-ground clutter.",
        "contact": "48 lower-support vertices span X -14.285..14.769 cm and Y -8.416..12.174 cm. Source/native base at Z=0 agrees within 0.000002 cm.",
        "facing": "Unconstrained static-clutter yaw only. No cooking/service-facing placement context is claimed.",
    },
    "current_Project__Shared__Bank_ME_v3__Props__SM_H0089_Tires": {
        "image": "H0089_Tires.jpg", "anchor_z_cm": -0.6557816863059998, "forward_axis": "+X",
        "observation": "Complete three-tyre pile; textured worn rubber, with visible source atlas patches. Preserve this appearance; actual-area art review remains open.",
        "contact": "Lower 1 cm has 210 vertices spanning X -26.413..15.319 cm and Y -20.752..20.752 cm. Preserve measured bottom anchor; do not reorient individual tyres.",
        "facing": "Static tyre pile has no required front; arbitrary yaw with the existing +X convention.",
    },
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def write(name, data):
    target = HERE / name
    assert target.resolve().is_relative_to(HERE.resolve()), "owned_directory_only"
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temp.replace(target)


def yes(value):
    return str(value).lower() in ("1", "true")


def package_file(obj):
    assert obj.startswith("/Game/"), obj
    return ROOT / "Content" / (obj.split(".")[0][6:] + ".uasset")


def file_identity(path, expected=None):
    p = Path(path)
    found = p.is_file()
    actual = sha(p) if found else None
    return {"path": str(p), "exists": found, "sha256": actual,
            "expected_sha256": expected, "matches_expected": found and (expected is None or actual.lower() == expected.lower())}


def _code_fingerprint(code):
    """Compare loaded function semantics to reviewed source, including constants.

    Filenames/line positions are omitted because normal Windows import spellings
    differ; the exact resolved source path and full file SHA are checked separately.
    No module reload or execution of the compiled comparison source occurs.
    """
    def constant(value):
        if isinstance(value, types.CodeType):
            return _code_fingerprint(value)
        if isinstance(value, tuple):
            return [constant(v) for v in value]
        if isinstance(value, frozenset):
            return sorted([constant(v) for v in value], key=lambda v: json.dumps(v, sort_keys=True))
        return repr(value)
    value = {"code": code.co_code.hex(), "constants": [constant(c) for c in code.co_consts],
             "names": code.co_names, "varnames": code.co_varnames, "freevars": code.co_freevars,
             "cellvars": code.co_cellvars, "argcount": code.co_argcount, "posonlyargcount": code.co_posonlyargcount,
             "kwonlyargcount": code.co_kwonlyargcount, "flags": code.co_flags,
             "exceptiontable": getattr(code, "co_exceptiontable", b"").hex()}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _verify_loaded_helper(module, identity):
    path = Path(identity["path"])
    assert Path(module.__file__).resolve() == path.resolve(), ("helper_resolved_path_mismatch", module.__name__)
    assert sha(path) == identity["sha256"], ("helper_source_changed_refresh_reviewed_batch", module.__name__)
    compiled = compile(path.read_text(encoding="utf-8-sig"), str(path), "exec", dont_inherit=True)
    for definition in compiled.co_consts:
        if isinstance(definition, types.CodeType) and not definition.co_name.startswith("<"):
            loaded = getattr(module, definition.co_name, None)
            assert loaded and hasattr(loaded, "__code__"), ("helper_function_missing", module.__name__, definition.co_name)
            assert _code_fingerprint(loaded.__code__) == _code_fingerprint(definition), ("loaded_helper_code_differs_from_reviewed_source", module.__name__, definition.co_name)


def _require_execution_manifest(path, expected_sha256, batch):
    assert path and expected_sha256, "reviewed_complete_execution_manifest_path_and_sha256_required"
    assert sha(path) == expected_sha256, "reviewed_execution_manifest_sha256_mismatch"
    reviewed = read(path)
    local = read(HERE / "EXECUTION_MANIFEST.json")
    assert reviewed["manager_thread"] == batch["system_manager"], "execution_manifest_manager_mismatch"
    for section in ("files", "payloads"):
        for filename, digest in local[section].items():
            assert reviewed[section].get(filename) == digest, ("execution_manifest_incomplete", filename)
            assert sha(filename) == digest, ("frozen_execution_source_or_payload_changed", filename)
    assert sha(HERE / "READY_JOBS.json") == local["payloads"][str(HERE / "READY_JOBS.json")]
    return reviewed


def native_configuration(record, prepared, measurement):
    rt = record["runtime"]
    role = rt["RequestRole"]
    bounds = measurement.get("vertex_bounds_cm", measurement.get("bounds_cm"))
    return {"asset_id": record["asset_id"], "row_name": record["catalog_row_name"],
            "object_path": rt["ObjectPath"], "package_sha256": prepared["current_package_sha256"],
            "role": role, "placement_rule": RULES[role], "contact_kind": "existing_reviewed_contact",
            "anchor_z_cm": float(rt["AnchorZCm"]), "anchor_basis": "Existing retained runtime contract; no change.",
            "bounds_cm": bounds, "forward_axis": rt["ForwardAxis"], "forward_basis": "Existing retained runtime contract.",
            "native_scale": [1, 1, 1], "allowed_areas": AREAS,
            "allowed_zones": "open_ground" if role == "small_prop" else "roadside",
            "style_context": rt["StyleSet"], "source_style_preserved": record["environment_style_set"],
            "family_id": rt["FamilyId"], "min_spacing_cm": float(rt["MinSpacingCm"]),
            "material_slots": measurement["material_slots"], "existing_instance_materials": [],
            "historical_native_images": prepared["native_preview_sources"],
            "rights_state_preserved": record["recorded_rights_state"], "automatic_ground_activation_allowed": True}


def runtime_delta(record, config, reviewed, material_paths, imported, release_id, member_weight):
    rt = record["runtime"]
    changes = {}
    if imported and not rt["ObjectPath"]:
        values = {"ObjectPath": imported["native_path"], "AssetRevision": imported["native_sha256"], "BoundsValid": "true"}
        for axis, lo, hi in zip("XYZ", imported["measurement"]["bounds_cm"]["min"], imported["measurement"]["bounds_cm"]["max"]):
            values["BoundsMin" + axis + "Cm"] = str(lo)
            values["BoundsMax" + axis + "Cm"] = str(hi)
        changes.update(values)
    ready = bool(config and reviewed and material_paths and not yes(rt["ExplicitHold"]) and not record["hold_reasons"])
    if ready and not yes(rt["RunEligible"]):
        changes.update(Role=config["role"], RequestRole=config["role"], PlacementRule=config["placement_rule"],
                       RunEligible="true", BoundsValid="true", AnchorValid="true", OrientationValid="true",
                       AnchorZCm=str(reviewed["anchor_z_cm"]), ForwardAxis=reviewed["forward_axis"],
                       StyleSet=config["style_context"], SelectionWeight=repr(member_weight),
                       PlacementScope="area_zone", AllowedAreas="|".join(AREAS), AllowedZones=config["allowed_zones"],
                       AllowedPlacementIds="", DecisionId="Aviv_BankIntegration_2026-10-04_Nonmodular_v001",
                       ReleaseId=release_id, MinSpacingCm=str(config["min_spacing_cm"]))
        for axis, lo, hi in zip("XYZ", config["bounds_cm"]["min"], config["bounds_cm"]["max"]):
            changes["BoundsMin" + axis + "Cm"] = str(lo)
            changes["BoundsMax" + axis + "Cm"] = str(hi)
    return {k: {"before": rt.get(k), "after": v} for k, v in changes.items() if rt.get(k) != v}


def build():
    """Reconcile existing evidence into executable jobs, without native operations."""
    inputs = {"catalog": CATALOG, "prepared": PREP / "PREPARED_BANK.json",
              "measurements": PREP / "NATIVE_MEASUREMENTS.json", "import_manifest": PREP / "EXTERNAL_IMPORT_MANIFEST.json",
              "budgets": PREP / "FAMILY_WEIGHT_BUDGETS.json", "geometry_families": PREP / "EXACT_GEOMETRY_FAMILIES.json",
              "configurations": INTEGRATION / "NATIVE_CONFIGURATIONS.json", "validation": INTEGRATION / "NATIVE_VALIDATION.json",
              "contact": INTEGRATION / "NATIVE_CONTACT_READBACK.json", "source_contact": INTEGRATION / "SOURCE_CONTACT_READBACK.json",
              "materials": INTEGRATION / "NATIVE_INSTANCE_MATERIALS.json", "import_queue": INTEGRATION / "EXTERNAL_IMPORT_QUEUE.json",
              "material_recipes": INTEGRATION / "EXTERNAL_MATERIAL_RECIPES.json",
              "category_assignment": INTEGRATION / "CategoryBatches/ASSIGNMENT.json",
              "management_transfer": ROOT / "Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/STATE.json"}
    identities = {key: {"path": str(path), "sha256": sha(path)} for key, path in inputs.items()}
    helpers = {name: file_identity(INTEGRATION / (name + ".py")) for name in
               ("bank_contracts", "native_bank_ops", "import_prepared", "apply_bank_configuration", "expanded_native_contracts")}
    data = {key: read(path) for key, path in inputs.items()}
    records = data["catalog"]["rows"]
    prepared = {r["asset_id"]: r for r in data["prepared"]["rows"]}
    category_members = [r for r in records if r["recorded_category"] in ("SmallProps", "StreetProps")]
    missing_preparation = [r["asset_id"] for r in category_members if r["asset_id"] not in prepared]
    if missing_preparation:
        write("INTAKE_REQUIRED.json", {"status": "STOP_UNPREPARED_CATEGORY_IDENTITIES", "asset_ids": missing_preparation,
              "action": "Supplier/integrator must append exact per-asset PREPARED_BANK entries before Props refresh; no row is silently omitted."})
        raise RuntimeError("Unprepared Props identities: " + ", ".join(missing_preparation))
    assignment = data["category_assignment"]
    manager = assignment["system_manager_thread"]
    assert data["management_transfer"]["successor_manager_thread_id"] == manager
    configurations = {r["asset_id"]: r for r in data["configurations"]["rows"]}
    manifest = {r["asset_id"]: r for r in data["import_manifest"]}
    queue = {r["asset_id"]: r for r in data["import_queue"]}
    imports = {read(p)["asset_id"]: (read(p), p) for p in INTEGRATION.glob("IMPORTED_external_*.json")}
    source_contacts = {r["asset_id"]: r for r in data["source_contact"]}
    # Exact projected membership if all five final material checks pass. The
    # retained shared transaction recomputes against whichever actually pass.
    projected_groups = collections.defaultdict(set)
    for record in records:
        rt = record["runtime"]
        if yes(rt["RunEligible"]) and rt["RequestRole"] in RULES:
            key = tuple(rt[k] for k in ("RequestRole", "StyleSet", "AllowedAreas", "AllowedZones", "FamilyId"))
            projected_groups[key].add(record["asset_id"])
    for aid in NATIVE_HISTORICAL:
        cfg = configurations[aid]
        projected_groups[(cfg["role"], cfg["style_context"], "|".join(AREAS), cfg["allowed_zones"], cfg["family_id"])].add(aid)
    jobs, excluded, reviews, intake = [], [], [], []
    for record in records:
        if record["recorded_category"] not in ("SmallProps", "StreetProps"):
            continue
        aid = record["asset_id"]
        p, rt = prepared[aid], record["runtime"]
        config = configurations.get(aid)
        # Keep the reviewed 257-job index/89-exclusion partition. Additional held
        # mount/assembly records remain indexed but belong to a separate lane.
        reason = EXCLUDED_EXTERNAL.get(aid)
        held_attachment_reason = EXCLUDED_NATIVE.get(aid)
        if set(record["hold_reasons"]) & {"mounting_surface_not_measured", "requires_assembly_or_attachment"}:
            held_attachment_reason = "Recorded assembly/mounting contract is unsupported by ordinary ground-prop consumers."
        if p["required_consumer_context"] in HOST_CONTEXTS:
            reason = "Existing explicit consumer: " + p["required_consumer_context"]
        if config and not config.get("automatic_ground_activation_allowed", True):
            reason = json.dumps(config.get("suitability_constraints", []), ensure_ascii=False)
        if "separate_road_or_surface_geometry_lane" in record["hold_reasons"]:
            reason = "Separate road/surface geometry lane; excluded from ground and roadside props."
        if "GroundTilset" in aid:
            reason = "Ground/road/sidewalk tile geometry requires a surface provider."
        if reason:
            excluded.append({"asset_id": aid, "row_name": record["catalog_row_name"], "reason": reason,
                             "object_path": rt["ObjectPath"], "holds": record["hold_reasons"],
                             "RunEligible_preserved": rt["RunEligible"], "work_performed": "scope segregation only"})
            continue
        imp, imp_path = imports.get(aid, (None, None))
        measurement = (imp or {}).get("measurement") or data["contact"].get(aid) or data["measurements"].get(aid)
        if not config and yes(rt["RunEligible"]) and measurement and rt["RequestRole"] in RULES:
            config = native_configuration(record, p, measurement)
        native_path = (imp or {}).get("native_path") or rt["ObjectPath"]
        source_hash = (imp or {}).get("native_sha256") or (config or {}).get("package_sha256") or p.get("current_package_sha256")
        native = file_identity(package_file(native_path), source_hash) if native_path else None
        slots = ((imp or {}).get("native_material_slots") or data["materials"]["mesh_slots"].get(native_path)
                 or data["catalog"].get("instance_materials", {}).get(native_path, []))
        material_identity = [dict(slot=i, object_path=path, **file_identity(package_file(path))) for i, path in enumerate(slots)]
        hold = {"ExplicitHold": rt["ExplicitHold"], "HoldReasons": rt["HoldReasons"], "recorded_reasons": record["hold_reasons"],
                "named_holds": p["named_holds_preserved"], "palm_hold": p["palm_hold_not_released"],
                "rights": record["recorded_rights_state"], "canonical_qualified": record["canonical_qualified"],
                "source_style": record["environment_style_set"], "runtime_style": rt["StyleSet"]}
        blockers = []
        if yes(rt["ExplicitHold"]) or record["hold_reasons"]:
            blockers.append({"kind": "existing_hold_preserved", "exact_reasons": record["hold_reasons"], "action": "Keep disabled; configuration/connection is not hold release."})
        if held_attachment_reason:
            blockers.append({"kind": "held_attachment_separate_from_ground_jobs", "exact_reason": held_attachment_reason,
                             "action": "Retain identity/binding/hold only; no ordinary ground activation or hosted consumer work."})
        if rt["StyleSet"] != "mediterranean_urban":
            blockers.append({"kind": "current_area_style_mismatch", "preserved_style": rt["StyleSet"], "action": "Do not relabel; current Gaza selector requires mediterranean_urban."})
        if native and not native["matches_expected"]:
            blockers.append({"kind": "native_identity_mismatch", "identity": native})
        if any(not m["exists"] for m in material_identity):
            blockers.append({"kind": "missing_named_material_package", "paths": [m["object_path"] for m in material_identity if not m["exists"]]})
        historical = NATIVE_HISTORICAL.get(aid)
        review = None
        if historical:
            assert config and source_contacts.get(aid) and data["contact"].get(aid), aid
            assert data["contact"][aid]["source_sha256"].lower() == config["package_sha256"].lower(), aid
            assert native["matches_expected"] and slots and all(m["exists"] for m in material_identity), aid
            image_path = ROOT / "Staging/ModelBank/Inspection_2026-09-28_Continuation/Native_Visual_Run_02" / historical["image"]
            reviewed_image = file_identity(image_path)
            assert reviewed_image["exists"], aid
            review = dict(historical, asset_id=aid, image_identity=reviewed_image,
                         native_identity=native, material_identities=material_identity,
                         current_native_contact_receipt=str(inputs["contact"]), source_contact_receipt=str(inputs["source_contact"]),
                         source_contact_sha256=source_contacts[aid]["source_sha256"],
                         source_native_axis_matches=source_contacts[aid]["matching_rigid_native_axis_transforms"],
                         review_basis="Retained actual Unreal Lit pixels reviewed in this category chat; current measured geometry/source hashes reused.",
                         material_review="Source texture appearance observed; saved instancing override paths/provenance reused. Integrator must verify native usage and exact texture closure before ready=true.",
                         ready=False, contact_reviewed=True, facing_reviewed=True, material_reviewed=False,
                         runtime_finalization_function="integrate_reviewed", actual_area_output=False, fresh_reopen=False, final_art_acceptance=False)
            reviews.append(review)
        validation = data["validation"].get(aid, {})
        if not yes(rt["RunEligible"]) and config and not validation.get("ready") and not historical:
            missing = [key for key in ("contact_reviewed", "facing_reviewed", "material_reviewed") if not validation.get(key)]
            blockers.append({"kind": "missing_individual_evidence", "missing": missing,
                             "existing_measurements_reused": measurement is not None,
                             "action": "Batch native review of these precise fields; reuse measurements/material copies. Submit explicit observations to integrate_reviewed, never blanket ready flags."})
        actions = []
        if imp:
            actions.append({"kind": "reuse_saved_import_and_register_existing_identity", "helper": "apply_bank_configuration.build",
                            "receipt": str(imp_path), "receipt_sha256": sha(imp_path), "already_catalog_connected": rt["ObjectPath"] == imp["native_path"]})
        elif native_path:
            actions.append({"kind": "reuse_existing_native_configuration" if config else "retain_existing_held_native_binding",
                            "helper": "native_bank_ops.prepare_native_materials(ids)" if aid in configurations else None,
                            "skip_material_creation_if_saved_paths_match": bool(slots), "original_mesh_mutation": False})
        elif aid in manifest:
            source = p["prepared_source"]
            if source["primary_render_object_count"] == 1:
                actions.append({"kind": "import_existing_prepared_source", "helper": "import_prepared.import_one(asset_id)", "import_payload": queue.get(aid, manifest[aid])})
            else:
                asset = read(source["receipt"])
                components = [{"object_name": obj["name"], "bounds_m": obj["bounds_m"], "material_slots": obj["material_slots"]}
                              for obj in asset["objects"] if obj.get("primary_render")]
                blockers.append({"kind": "compound_source_is_not_one_ground_prop", "primary_render_object_count": source["primary_render_object_count"],
                                 "components": components, "action": "Preserve canonical parent identity; bank owner must assign component identities/contracts before independent selection. Do not combine a 60-object industrial scene as one ordinary prop."})
                actions.append({"kind": "preserve_compound_source_identity", "prepared_receipt": source["receipt"]})
        else:
            source = Path(p["source_path"])
            identity = file_identity(source)
            intake_job = {"asset_id": aid, "catalog_row_name": record["catalog_row_name"], "source_identity": identity,
                          "source_record_kind": p["record_kind"], "held_registration_only": True,
                          "required_native_provider": "Installed native asset supplier / sole bank integrator",
                          "operation": "Dependency-closed native intake retaining package references and originals; reconcile individual canonical IDs before selection.",
                          "do_not_fbx_import_uasset": True}
            intake.append(intake_job)
            actions.append({"kind": "native_package_intake", "job": intake_job})
            blockers.append({"kind": "family_record_has_no_individual_native_binding", "source_exists": identity["exists"],
                             "source_record_kind": p["record_kind"], "action": "Retain family ID as a group. Native supplier must bind measured members without treating the example package as the whole family."})
        if historical:
            actions.append({"kind": "finalize_retained_contact_facing_and_material_contract", "helper": "category_batch.integrate_reviewed", "review_receipt": str(HERE / "REVIEW_EVIDENCE.json")})
        elif validation.get("ready") and not yes(rt["RunEligible"]):
            actions.append({"kind": "activate_reviewed_existing_row", "helper": "apply_bank_configuration.build"})
        source = p.get("prepared_source")
        source_identities = ({"fbx": file_identity(source["source_fbx"], source["source_fbx_sha256"]),
                              "blend": file_identity(source["blend"]), "receipt": file_identity(source["receipt"])} if source else {})
        delta_review = historical or (validation if validation.get("ready") else None)
        job = {"asset_id": aid, "row_name": record["catalog_row_name"], "category": record["recorded_category"],
               "lane": "preserved_held_attachment_not_ground" if held_attachment_reason else "ordinary_prop_or_pending_family_intake",
               "name": p["name"], "object_path": native_path, "native_identity": native, "source_identities": source_identities,
               "actions": actions, "configuration_payload": config, "material_slots": material_identity,
               "contact_measurement": measurement, "validation_existing": validation,
               "validation_delta": ({"source_sha256": source_hash, "anchor_z_cm": historical["anchor_z_cm"], "forward_axis": historical["forward_axis"],
                                     "contact_reviewed": True, "facing_reviewed": True, "material_reviewed": "SET_TRUE_ONLY_AFTER_NATIVE_MATERIAL_CHECK", "ready": "SET_TRUE_ONLY_AFTER_NATIVE_MATERIAL_CHECK"} if historical else {}),
               "runtime_delta": runtime_delta(record, config, delta_review, slots, imp,
                    data["catalog"]["normal_use_release_id"],
                    1.0 / len(projected_groups[(config["role"], config["style_context"], "|".join(AREAS), config["allowed_zones"], config["family_id"])])
                    if config and historical else 1.0),
               "runtime_delta_condition": "Projected exact fields if individual finalization succeeds; existing shared build recomputes family weights over actual passing members.",
               "family_budget": {"family_id": rt["FamilyId"], "aggregate_budget": 1.0, "allocation": "1/N over actually eligible members of the same role/style/area/zone; recompute at apply", "already_enabled_weight": rt["SelectionWeight"]},
               "preserve": hold, "already_enabled": yes(rt["RunEligible"]),
               "consumer": {"role": (config or {}).get("role") or rt["RequestRole"], "rule": (config or {}).get("placement_rule") or rt["PlacementRule"],
                            "native_scale": [1, 1, 1], "allowed_areas": AREAS,
                            "host_required": True if held_attachment_reason else False if config else "not_established_for_held_or_family_record",
                            "implementation": "Existing geographic requests -> shared catalog selector -> official Houdini Engine unreal_instance",
                            "replacement": "Existing owned placement identities/ledger; no manual scene spawn", "future_generation_requires_root_profile_patch": True},
               "blockers": blockers, "ordinary_output_completed": False, "saved_original_area_completed": False, "fresh_reopen_completed": False}
        jobs.append(job)
    assert len({j["asset_id"] for j in jobs + excluded}) == len(jobs) + len(excluded)
    ids = {j["asset_id"] for j in jobs}
    # Copy exact existing preparation partitions, never convert duplicate meshes into extra probability.
    budgets = [b for b in data["budgets"] if set(b["asset_ids"]) & ids]
    geometry = [g for g in data["geometry_families"] if set(g["asset_ids"]) & ids]
    counts = {"category_identities_accounted": len(jobs) + len(excluded), "ordinary_jobs": len(jobs),
              "excluded_host_surface_context_jobs": len(excluded), "already_enabled": sum(j["already_enabled"] for j in jobs),
              "historical_review_finalization_jobs": len(reviews), "saved_external_imports_reused": sum(bool(imports.get(j["asset_id"])) for j in jobs),
              "held_jobs_preserved": sum(yes(j["preserve"]["ExplicitHold"]) for j in jobs), "native_family_intake_jobs": len(intake)}
    counts["held_attachment_sublane_jobs"] = sum(j["lane"] == "preserved_held_attachment_not_ground" for j in jobs)
    grouped = collections.defaultdict(list)
    for job in jobs:
        if job["lane"] == "preserved_held_attachment_not_ground":
            group = "preserved_held_attachment_records"
        elif job["already_enabled"]:
            group = "existing_active_contracts_require_original_area_output_reopen"
        elif job["asset_id"] in NATIVE_HISTORICAL:
            group = "five_retained_reviews_material_finalization"
        elif yes(job["preserve"]["ExplicitHold"]):
            group = "existing_hold_binding_preservation"
        elif job["preserve"]["runtime_style"] != "mediterranean_urban":
            group = "preserved_other_style_" + job["preserve"]["runtime_style"]
        else:
            group = "current_gaza_missing_review_" + job["configuration_payload"]["contact_kind"]
        grouped[group].append(job)
    action_groups = []
    observations = []
    for group, members in sorted(grouped.items()):
        entries = []
        for job in members:
            cfg = job["configuration_payload"]
            images = []
            for image_path in (cfg or {}).get("historical_native_images", []):
                images.append(file_identity(image_path))
            entries.append({"asset_id": job["asset_id"], "object_path": job["object_path"],
                "native_identity": job["native_identity"], "ordered_material_identities": job["material_slots"],
                "configuration": cfg, "existing_image_evidence": images, "existing_missing_evidence": job["blockers"],
                "ground_activation_permitted": job["lane"] != "preserved_held_attachment_not_ground" and not yes(job["preserve"]["ExplicitHold"])})
            if group.startswith("current_gaza_missing_review_"):
                observations.append({"asset_id": job["asset_id"], "source_sha256": cfg["package_sha256"],
                    "native_minimum_z_candidate_cm": cfg["bounds_cm"]["min"][2],
                    "anchor_z_cm": None, "forward_axis": None, "contact_reviewed": False, "facing_reviewed": False,
                    "material_reviewed": False, "observation": None, "contact": None, "facing": None,
                    "evidence_receipt": None, "exact_required_contact_decision": cfg.get("review_note", cfg["contact_kind"]),
                    "material_action": "Inspect the listed saved override/slot evidence and actual native Lit appearance, then verify current usage/closure. Do not recreate materials or remeasure complete geometry."})
        action_groups.append({"group": group, "asset_count": len(members), "entries": entries,
            "execution_policy": "Grouped review of exact missing fields using retained source/native measurements and images; no per-model demonstration map, placement loop or new inventory.",
            "consumer_function": "integrate_reviewed(reviews=[explicit individually observed records], execution_manifest_path=..., execution_manifest_sha256=...)" if group.startswith("current_gaza_missing_review_") else None})
    write("GROUPED_ACTIONS.json", {"schema": "environmentpipeline.props_grouped_actions.v1", "groups": action_groups,
          "current_gaza_additional_observation_count": len(observations), "known_category_asset_ids": sorted(expected["asset_id"] for expected in category_members)})
    write("OBSERVATION_TEMPLATE.json", {"schema": "environmentpipeline.props_observation_template.v1", "rows": observations,
          "template_is_readiness_evidence": False, "instruction": "Fill only from actual evidence. Null anchors/facing and false reviewed flags cannot be consumed as ready."})
    assert all(sha(path) == identities[key]["sha256"] for key, path in inputs.items()), "inputs_changed_during_build_rerun"
    write("REVIEW_EVIDENCE.json", {"schema": "environmentpipeline.props_retained_review.v1", "rows": reviews})
    write("REVIEW_QUEUE.json", {"schema": "environmentpipeline.props_missing_review.v1",
          "current_gaza_rows": [{"asset_id": j["asset_id"], "object_path": j["object_path"],
                 "configuration_payload": j["configuration_payload"], "existing_measurement": j["contact_measurement"],
                 "saved_material_slots": j["material_slots"], "missing_evidence": j["blockers"],
                 "submission_function": "integrate_reviewed(reviews=[...])"}
                 for j in jobs if j["configuration_payload"] and not j["already_enabled"]
                 and j["preserve"]["runtime_style"] == "mediterranean_urban"
                 and not yes(j["preserve"]["ExplicitHold"]) and j["asset_id"] not in NATIVE_HISTORICAL],
          "other_styles": [j["asset_id"] for j in jobs if j["preserve"]["runtime_style"] in {"stylized_town", "stylized_egypt"}],
          "instruction": "Reuse the complete saved measurements and instancing material copies. Batch review only missing functional contact/facing/context/appearance; no new inventory or demonstration map."})
    write("READY_JOBS.json", {"schema": "environmentpipeline.props_category_batch.v1", "category": "Props", "counts": counts,
                              "input_identities": identities, "helper_identities": helpers,
                              "adapter_identity": file_identity(HERE / "category_batch.py"),
                              "known_category_asset_ids": sorted(r["asset_id"] for r in category_members),
                              "unprepared_identity_policy": "Fail explicitly and emit INTAKE_REQUIRED.json; never skip supplier-appended category identities.",
                              "rows": jobs, "excluded_rows": excluded, "family_budgets": budgets,
                              "exact_geometry_families": geometry, "native_intake_jobs": intake,
                              "ready_meaning": "Executable actions; ready for activation is separate and per asset. No native operation performed by producer.",
                              "integrator": assignment["bank_integrator_thread"], "system_manager": manager})
    write("HANDOFF.json", {"status": "EXECUTABLE_FULL_ORDINARY_PROP_BATCH_PREPARED_NATIVE_CONSUMPTION_PENDING", "counts": counts,
                          "adapter": str(HERE / "category_batch.py"), "jobs": str(HERE / "READY_JOBS.json"),
                          "adapter_sha256": sha(HERE / "category_batch.py"), "jobs_sha256": sha(HERE / "READY_JOBS.json"),
                          "review_evidence": str(HERE / "REVIEW_EVIDENCE.json"),
                          "system_manager": manager, "bank_integrator": assignment["bank_integrator_thread"],
                          "integrator_next": "After manager-reviewed complete helper manifest and MANAGER_ACTIVATED actual-PID lease, run integrate_reviewed with explicit manifest path+SHA. Grouped remaining observation/repair actions are GROUPED_ACTIONS.json; submit actual observations via reviews argument, then shared build/apply.",
                          "profile_owner_next": "Apply exact resulting PROFILE_BANK_FIELD_PATCH.json; existing original-area ordinary generation/replacement, named saves, reopen and actual Lit review remain necessary.",
                          "shared_writes_by_category": False, "editor_operated_by_category": False, "holds_rights_style_originals_preserved": True,
                          "newly_native_enabled_by_category": 0, "ordinary_generation_completed": False, "fresh_reopen_completed": False})
    runtime_path = ROOT / "Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json"
    runtime = read(runtime_path)
    files = {str(HERE / filename): sha(HERE / filename) for filename in ("category_batch.py", "verify_batch.py", "README.txt")}
    files.update({identity["path"]: identity["sha256"] for identity in helpers.values()})
    files[str(runtime_path)] = sha(runtime_path)
    system_bindings = {}
    for module_name, definition in runtime["modules"].items():
        source_path = ROOT / "Content/Python" / definition["file"]
        assert sha(source_path) == definition["sha256"], ("system_source_seal_drift", module_name)
        files[str(source_path)] = definition["sha256"]
        system_bindings[module_name] = {"path": str(source_path), "sha256": definition["sha256"]}
    payload_names = ("READY_JOBS.json", "REVIEW_EVIDENCE.json", "REVIEW_QUEUE.json", "GROUPED_ACTIONS.json", "OBSERVATION_TEMPLATE.json", "HANDOFF.json")
    write("EXECUTION_MANIFEST.json", {"schema": "environmentpipeline.category_execution_source_binding.v1",
        "manager_thread": manager, "status": "SOURCE_BOUND_NATIVE_NOT_RUN_REQUIRES_MANAGER_REVIEW",
        "files": files, "payloads": {str(HERE / name): sha(HERE / name) for name in payload_names},
        "bank_helper_modules": helpers, "system_modules": system_bindings,
        "cached_module_policy": "Verify exact resolved paths/full file SHA and loaded function code; reject cached stale helpers without hot reload. geocity_runtime_guard verifies all12 sealed system modules at bank preflight.",
        "entry_parameters": ["execution_manifest_path", "execution_manifest_sha256"],
        "native_authoring_requires": "Fresh actual-PID bank lease activation=MANAGER_ACTIVATED and native_authorized_now=true; INSPECTION_ONLY is rejected by current bank preflight.",
        "wrapper_contract": "Integrator wrapper must pass the manager-reviewed complete manifest path and exact SHA. It may pass a combined manifest containing these exact files/payloads. MANAGER_ACTIVATED actual-PID write activation is separately required; INSPECTION_ONLY fails native preflight."})
    print(json.dumps(counts))
    return counts


def integrate_reviewed(reviews=None, execution_manifest_path=None, execution_manifest_sha256=None):
    """Integrator-only native finalization of supplied, individually observed reviews.

    This does not generate/save areas or modify original meshes/materials. It
    verifies current lease, exact asset identity and saved derivative usage/texture
    closure, then merges per-asset validation. Remaining observations must include
    contact/facing/material evidence and an exact source SHA; no blanket flags.
    Shared CSV/DataTable/profile writes remain the existing owners' next actions.
    """
    batch = read(HERE / "READY_JOBS.json")
    _require_execution_manifest(execution_manifest_path, execution_manifest_sha256, batch)
    assert sha(HERE / "category_batch.py") == batch["adapter_identity"]["sha256"], "category_adapter_changed_refresh_batch"
    sys.path.insert(0, str(INTEGRATION))
    N = importlib.import_module("native_bank_ops")
    C = importlib.import_module("bank_contracts")
    unreal = importlib.import_module("unreal")
    _verify_loaded_helper(N, batch["helper_identities"]["native_bank_ops"])
    _verify_loaded_helper(C, batch["helper_identities"]["bank_contracts"])
    _verify_loaded_helper(types.SimpleNamespace(**globals()), batch["adapter_identity"])
    for module_name, identity in batch["helper_identities"].items():
        if module_name in sys.modules:
            _verify_loaded_helper(sys.modules[module_name], identity)
    assert Path(C.HERE).resolve() == INTEGRATION.resolve() and Path(C.SOURCE).resolve() == CATALOG.resolve(), "shared_helper_paths_changed"
    before = N.preflight()
    jobs = {r["asset_id"]: r for r in batch["rows"]}
    historical = read(HERE / "REVIEW_EVIDENCE.json")["rows"]
    incoming = list(historical) + list(reviews or [])
    assert len({r["asset_id"] for r in incoming}) == len(incoming), "duplicate_review_id"
    current = {r["asset_id"]: r for r in C.read(C.SOURCE)["rows"]}
    current_members = {aid for aid, record in current.items() if record["recorded_category"] in ("SmallProps", "StreetProps")}
    assert current_members == set(batch["known_category_asset_ids"]), "category_membership_changed_refresh_prepared_intake_and_batch"
    configs = {r["asset_id"]: r for r in C.read(C.HERE / "NATIVE_CONFIGURATIONS.json")["rows"]}
    validation_path = C.HERE / "NATIVE_VALIDATION.json"
    validation = C.read(validation_path)
    materials = C.read(C.HERE / "NATIVE_INSTANCE_MATERIALS.json")["mesh_slots"]
    results, pending, updates = [], [], {}
    for review in incoming:
        aid = review["asset_id"]
        assert aid in jobs and aid in configs, ("asset_outside_ordinary_configured_props", aid)
        job, cfg, record = jobs[aid], configs[aid], current[aid]
        if yes(record["runtime"]["RunEligible"]) and validation.get(aid, {}).get("ready"):
            results.append({"asset_id": aid, "already_ready": True})
            continue
        assert not C.yes(record["runtime"]["ExplicitHold"]) and not record["hold_reasons"] and not record["runtime"]["HoldReasons"], aid
        assert cfg.get("automatic_ground_activation_allowed", True), aid
        assert not cfg.get("suitability_constraints"), ("specific_context_constraint_requires_consumer_owner", aid)
        for key in ("object_path", "role", "placement_rule", "bounds_cm", "allowed_areas", "allowed_zones",
                    "family_id", "min_spacing_cm", "material_slots", "style_context"):
            assert cfg[key] == job["configuration_payload"][key], ("configuration_contract_drift_refresh_batch", aid, key)
        assert cfg["style_context"] == job["preserve"]["runtime_style"] == record["runtime"]["StyleSet"], ("style_drift", aid)
        assert cfg["package_sha256"].lower() == job["native_identity"]["sha256"].lower() == C.sha(C.package_file(cfg["object_path"])).lower(), aid
        assert review.get("contact_reviewed") and review.get("facing_reviewed"), aid
        if aid not in NATIVE_HISTORICAL:
            assert review.get("material_reviewed") and review.get("observation") and review.get("contact") and review.get("facing"), aid
            assert review["source_sha256"].lower() == cfg["package_sha256"].lower(), aid
            assert review.get("evidence_receipt") and Path(review["evidence_receipt"]).is_file(), aid
        else:
            assert sha(review["image_identity"]["path"]) == review["image_identity"]["sha256"], aid
        slots = materials[cfg["object_path"]]
        assert len(slots) == len(cfg["material_slots"]), aid
        closure = N.dependency_closure(cfg["object_path"].split(".")[0])
        if closure["missing"]:
            pending.append({"asset_id": aid, "kind": "missing_native_mesh_dependency", "paths": closure["missing"]})
            continue
        slot_proofs = []
        for i, (source, target) in enumerate(zip(cfg["material_slots"], slots)):
            assert target == job["material_slots"][i]["object_path"] and C.sha(C.package_file(target)) == job["material_slots"][i]["sha256"], ("material_identity_drift", aid, i)
            mat = unreal.load_asset(target)
            original = unreal.load_asset(source["path"])
            assert mat and original
            usage = unreal.MaterialEditingLibrary.has_material_usage(mat, unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES)
            original_textures = sorted(t.get_path_name() for t in unreal.MaterialEditingLibrary.get_used_textures(original))
            override_textures = sorted(t.get_path_name() for t in unreal.MaterialEditingLibrary.get_used_textures(mat))
            dependency = N.dependency_closure(target.split(".")[0])
            proven = usage and bool(override_textures) and override_textures == original_textures and not dependency["missing"]
            slot_proofs.append({"slot": i, "source_material": source["path"], "override": target, "instancing_usage": usage,
                                "original_textures": original_textures, "override_textures": override_textures,
                                "dependencies": dependency, "passed": proven})
        if not all(p["passed"] for p in slot_proofs):
            pending.append({"asset_id": aid, "kind": "material_usage_or_texture_equivalence_unverified", "slots": slot_proofs,
                            "action": "Inspect exact retained derivative graph/binding; do not clear ready using a successful empty used-textures query."})
            continue
        anchor = float(review["anchor_z_cm"])
        axis = review["forward_axis"]
        assert math.isfinite(anchor) and axis in {"+X", "-X", "+Y", "-Y"}, aid
        updates[aid] = dict(validation.get(aid, {}), source_sha256=cfg["package_sha256"], anchor_z_cm=anchor,
                            forward_axis=axis, ready=True, contact_reviewed=True, facing_reviewed=True, material_reviewed=True,
                            pending=None, review_receipt=str(HERE / "NATIVE_CONSUMPTION.json"),
                            readiness_scope="Individual retained ordinary-prop contract; actual ordinary output/save/reopen/art acceptance remain pending")
        results.append({"asset_id": aid, "native_path": cfg["object_path"], "source_sha256": cfg["package_sha256"],
                        "review": review, "native_material_proof": slot_proofs, "validation_after": updates[aid]})
    assert N.dirty() == before["dirty"], "unexpected_dirty_state_during_review"
    proof_id = hashlib.sha256(json.dumps({"pid": before["pid"], "world": before["world"], "results": results},
                                         sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    proof_name = "NATIVE_CONSUMPTION_" + proof_id + ".json"
    for update in updates.values():
        update["review_receipt"] = str(HERE / proof_name)
    # Reconcile concurrent/incremental category work; never downgrade ready entries.
    latest = C.read(validation_path)
    for aid, update in updates.items():
        if latest.get(aid, {}).get("ready"):
            assert latest[aid]["source_sha256"].lower() == update["source_sha256"].lower(), aid
        latest[aid] = update
    receipt = {"pid": before["pid"], "world": before["world"], "finalized": results, "pending": pending,
                                     "native_dirty_unchanged": True, "shared_catalog_table_apply_pending": True,
                                     "ordinary_generation_completed": False, "fresh_reopen_completed": False}
    if (HERE / proof_name).exists():
        assert read(HERE / proof_name) == receipt, "immutable_native_proof_collision"
    else:
        write(proof_name, receipt)
    write("NATIVE_CONSUMPTION.json", dict(receipt, immutable_receipt=str(HERE / proof_name)))
    if updates:
        C.write(validation_path, latest)
    return {"new_validation_ids": sorted(updates), "pending": pending, "receipt": str(HERE / proof_name)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="Write owned category jobs only; default.")
    args = parser.parse_args()
    build()
