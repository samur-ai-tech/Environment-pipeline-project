"""Prepare only this owned delivery; leave the consumed category batch frozen."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent
ROOT = FROZEN.parents[3]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def identity(path, expected=None):
    path = Path(path).resolve()
    digest = sha(path)
    assert expected is None or digest == expected, ("evidence_identity_changed", str(path))
    return {"path": str(path), "sha256": digest}


jobs = {r["asset_id"]: r for r in read(FROZEN / "READY_JOBS.json")["rows"]}
template = read(FROZEN / "OBSERVATION_TEMPLATE.json")["rows"]
sources = {r["asset_id"]: r for r in read(HERE / "VEHICLE_SOURCE_CONTACT.json")["rows"]}
legacy = read(FROZEN / "EXECUTION_MANIFEST.json")
for section in ("files", "payloads"):
    for filename, expected in legacy[section].items():
        assert sha(filename) == expected, ("frozen_dependency_changed", filename)
for name, digest in {"category_batch.py": "d9a64d7c58a13c2ace25df30014e9c048cac0737c143549d2d77ccce9b4c9917",
                     "READY_JOBS.json": "f54126646687321c367735e9ac85fe55bf2157d2a3e473086b0cc637fc7b97cb",
                     "EXECUTION_MANIFEST.json": "5e148a873a610c651a0830e24064581953411318f805ac48e308b45a5059ef63"}.items():
    assert sha(FROZEN / name) == digest, ("cached_delivery_changed", name)

vehicles, reviewed_evidence, pending, evidence_files = [], [], [], {}
for source in sources.values():
    aid = source["asset_id"]
    job = jobs[aid]
    assert source["source_files_unchanged"] and not source["source_geometry_changed"]
    assert source["native_package_sha256"] == job["native_identity"]["sha256"]
    identity(source["source_blend"], source["source_sha256"])
    foodcart = "SM_H0043_" in aid
    image_name = "H0043_Foodcart.jpg" if foodcart else "H0039_DestroyedCar.jpg"
    image_hash = ("c592fbc06fa151b9af192acf81819f39b7e2590697e22621b102a434e7ba6210" if foodcart
                  else "cb14810daf348f562d8c1430452fd7904a9571dbaec1809c689d568de2146a35")
    image = identity(ROOT / "Staging/ModelBank/Inspection_2026-09-28_Continuation/Native_Visual_Run_02" / image_name, image_hash)
    minimum = job["configuration_payload"]["bounds_cm"]["min"][2]
    observation = ("Complete wheeled food/coffee cart with integral umbrella, cart body and visible source textures in the retained actual Unreal Lit image."
                   if foodcart else "Complete damaged purple vehicle, missing windows, retained body/wheels and loose front tyre/debris visible in the retained actual Unreal Lit image. Preserve the source atlas appearance; visual suitability for an area remains unaccepted.")
    contact = ("Anchor local Z=14.494669914245605 cm, subtracting this from sampled ground. The source lower 0.05 cm contains 32 wheel-bottom vertices spanning X -29.010..60.720 cm and Y -42.715..35.852 cm; the lower 1 cm contains 456 vertices. No source vertices lie within Z=0 +/-1 cm. An anchor of zero would leave the complete cart about 14.49 cm above ground. Transfer requires the exact native lower-band extent checks."
               if foodcart else "Anchor local Z=0 cm. Source Z=0 +/-1 cm contains 21 vertices spanning X -98.148..117.711 cm and Y -63.051..60.338 cm across separated support regions; the lowest 0.25 cm contains one isolated front-tip vertex at X126.376/Y-39.953. Preserve up to 1.762542 cm local penetration by that tip instead of raising the broad body/wheel support to the isolated minimum. Native lower-band concordance is required before finalization; this is a bounded static-wreck support choice, not evidence of traffic placement.")
    facing = "Preserve the +X source orientation convention at native scale. This consumer places isolated static open-ground clutter with arbitrary yaw and full-footprint spacing; it assigns no service-facing, parking, traffic or roadside orientation."
    review = {"asset_id": aid, "source_sha256": job["native_identity"]["sha256"],
              "anchor_z_cm": minimum if foodcart else 0.0, "forward_axis": "+X",
              "contact_reviewed": False, "facing_reviewed": True, "material_reviewed": False,
              "source_contact_reviewed": True, "source_material_appearance_reviewed": True,
              "observation": observation, "contact": contact, "facing": facing,
              "evidence_receipt": str(HERE / "VEHICLE_REVIEW_EVIDENCE.json"),
              "material_review_scope": "Retained actual source Lit appearance reviewed. The frozen native finalizer must additionally prove exact saved override identity, instancing usage, nonempty source/override texture equality and dependency closure; failure leaves this asset pending.",
              "native_contact_concordance_required": True, "actual_area_output": False,
              "fresh_reopen": False, "final_art_acceptance": False}
    vehicles.append(review)
    reviewed_evidence.append({"asset_id": aid, "image": image, "native_identity": job["native_identity"],
                             "source_blend_identity": identity(source["source_blend"], source["source_sha256"]),
                             "source_native_axis_match": source["unique_source_native_axes"],
                             "axis_match_is_full_geometry_identity": False,
                             "source_triangle_count": sum(r["triangles"] for r in source["objects"]),
                             "source_contact_receipt": identity(HERE / "VEHICLE_SOURCE_CONTACT.json"),
                             "saved_materials": job["material_slots"], "placement_observation": review,
                             "native_contact_check_performed_here": False,
                             "source_files_saved_or_modified": False})
    evidence_files[image["path"]] = image["sha256"]
    evidence_files[str(Path(source["source_blend"]).resolve())] = source["source_sha256"]

for row in template:
    aid = row["asset_id"]
    job = jobs[aid]
    for entry in [job["native_identity"]] + job["material_slots"]:
        assert sha(entry["path"]) == entry["sha256"]
        evidence_files[entry["path"]] = entry["sha256"]
    if aid in sources:
        continue
    rock = "__SM_Stone_" in aid
    pack = "__SM_Pack" in aid
    bounds = job["configuration_payload"]["bounds_cm"]
    dimensions = [b-a for a, b in zip(bounds["min"], bounds["max"])]
    if rock:
        index = aid.rsplit("_", 1)[1]
        image = identity(ROOT / "Staging/ModelBank/Inspection_2026-09-28_Continuation/Native_Visual_Run_02" / ("Stone_" + index + ".jpg"),
                         "a305bdc26165cf6efd41a8a9b73a86a6779ca24003a383642963633a116e5880" if index == "07" else "4e5e89a619c8b18755b9b805d84ce8f5f6bb9306c8aa87ec35e9e7f0f56c2a2f")
        evidence_files[image["path"]] = image["sha256"]
        missing = ["Resolve the exact rock actor/component transform against actual supporting ground in the installed Palms Scene/Showroom reference, or obtain an explicit approved embedment contract.",
                   "A reference Z translation alone is insufficient if ground height, mesh scale or rotation is unknown. The Static Mesh Editor preview floor does not establish an authored contact plane."]
        decision = "No accepted numeric anchor. Minimum-Z grounding would expose the entire buried portion; anchor zero would bury %.3f cm (%.2f percent of native height), neither choice is established by current evidence." % (-bounds["min"][2], -100*bounds["min"][2]/dimensions[2])
        visual = "Historical Unreal Lit rock texture is reviewed. Fresh saved-override usage/texture closure remains a native finalizer condition."
    elif "Parasol" in aid:
        missing = ["Native Lit whole-object and base/underside view: establish whether an integral stable base exists or whether the pole requires a table/socket/host.",
                   "Inspect the precise lower-band points. If host-supported, do not release to ordinary ground scatter; return the exact host interface to the consumer owner.",
                   "Read all three saved override slots and visible canopy/pole/base surfaces."]
        decision = "Z near zero is a candidate only. Full native canopy clearance is %.3f x %.3f x %.3f cm; retain it and the 482 cm configured spacing." % tuple(dimensions)
        visual = "No retained whole-object Lit view located; material-slot existence alone is not appearance review."
    elif "__SM_Bench" in aid:
        missing = ["Native Lit front/back/base views: identify complete seat/back/feet, functional seat-front axis and stable foot support.",
                   "Explain the retained 308.219 x 194.996 x 160 cm dimensions from actual geometry. Do not infer front from its longest axis or scale to a presumed standard size.",
                   "Match the functional facing to the existing roadside_prop orientation contract before supplying a ForwardAxis."]
        decision = "Near-zero anchor and +X remain unaccepted candidates; preserve full footprint and the 600 cm configured spacing."
        visual = "No retained Lit complete-bench view located. Original Bench.fbx import path was G:/_0interioirs/Bench.fbx and is not a local source contract."
    elif pack:
        missing = ["One native Lit batch for the five exact siblings, with per-asset labels and a common size reference, plus their support/underside faces.",
                   "Use the targeted lower bands to distinguish stable packaging/litter support from an isolated crushed corner. Do not choose origin zero or the isolated minimum automatically.",
                   "Confirm original/shared saved atlas appearance on each variant; keep all five in their existing family with the retained family weight budget."]
        decision = "Native dimensions %.3f x %.3f x %.3f cm are small litter-scale geometry. Preserve scale=1 and identity; do not resize to boxes or split the family into five independent selection weights." % tuple(dimensions)
        visual = "No retained native Lit sibling view located. Pack1 import path F:/1_Project/!Modular_biulding/Sigs/Final_fbx/SM_Pack1.fbx is not a local source contract."
    else:
        missing = ["Native Lit whole pile and underside view: establish the intended flat ground support across the mixed litter surfaces.",
                   "Compare lower contact bands and authored origin; decide whether the -3.2067 cm tip is intended shallow penetration or the actual support. No automatic minimum-Z or origin-Z choice.",
                   "Verify the saved instancing derivative preserves the original trash textures on visible faces."]
        decision = "Keep 148.945 x 94.249 x 15.377 cm complete pile geometry and 350 cm spacing. Anchor remains null until support is observed."
        visual = "No retained actual native Lit pile view located."
    pending.append({"asset_id": aid, "object_path": job["object_path"], "native_package_sha256": job["native_identity"]["sha256"],
                    "anchor_z_cm": None, "ready": False, "retained_bounds_cm": bounds, "dimensions_cm": dimensions,
                    "saved_material_slots": job["material_slots"], "required_evidence": missing,
                    "specific_decision": decision, "retained_visual_evidence": visual,
                    "readback_job": "run('read_rock_references', ...)" if rock else "run('inspect_pending_contacts', ...)",
                    "after_readback": "Individual contact/facing/material observations are still required; this probe does not set ready flags."})

write("VEHICLE_OBSERVATIONS.json", {"schema": "environmentpipeline.props_remaining_vehicles_observations.v1", "rows": vehicles,
                                    "execution": "Use remaining_props_native.run('finalize_vehicles', ...) so native contact concordance precedes the cached finalizer.",
                                    "new_native_finalizations_performed_here": 0})
write("VEHICLE_REVIEW_EVIDENCE.json", {"schema": "environmentpipeline.props_vehicle_evidence.v1", "rows": reviewed_evidence,
                                      "measured": "Immutable source scenes and exact current native package identities; lower source contact bands and coordinate matches.",
                                      "reviewed": "Retained actual Unreal Lit source appearance, complete static prop role, bounded support and unconstrained open-ground yaw.",
                                      "inferred": "Transfer of source support to native geometry; executable native contact concordance is required to validate it.",
                                      "not_run": ["native lower-band concordance", "native saved-override usage/texture equality", "catalog/DataTable application", "ordinary output/save/reopen", "final art acceptance"]})
write("PENDING_NATIVE_JOBS.json", {"schema": "environmentpipeline.props_remaining_native_jobs.v1", "rows": pending,
                                   "counts": {"pending_assets": 10, "authored_embedment_rocks": 2, "missing_whole_object_lit_reviews": 8},
                                   "readback_has_no_readiness_authority": True})

worlds = []
for name in ("Showroom", "Scene"):
    package = ROOT / "Content/Palms_Pack_01/Maps" / (name + ".umap")
    worlds.append({"object_path": "/Game/Palms_Pack_01/Maps/" + name + "." + name,
                   "file": str(package), "sha256": sha(package)})
    evidence_files[str(package)] = sha(package)
manifest = dict(legacy)
manifest["schema"] = "environmentpipeline.props_remaining12_execution_binding.v1"
manifest["status"] = "PREPARED_NOT_NATIVE_RUN_REQUIRES_MANAGER_REVIEW"
manifest["files"] = dict(legacy["files"])
manifest["payloads"] = dict(legacy["payloads"])
for name in ("remaining_props_native.py", "prepare_remaining_payloads.py", "read_vehicle_source_contact.py", "verify_remaining.py"):
    manifest["files"][str(HERE / name)] = sha(HERE / name)
manifest["payloads"][str(FROZEN / "EXECUTION_MANIFEST.json")] = sha(FROZEN / "EXECUTION_MANIFEST.json")
for name in ("VEHICLE_SOURCE_CONTACT.json", "VEHICLE_OBSERVATIONS.json", "VEHICLE_REVIEW_EVIDENCE.json", "PENDING_NATIVE_JOBS.json", "README.txt"):
    manifest["payloads"][str(HERE / name)] = sha(HERE / name)
manifest["evidence_files"] = evidence_files
manifest["rock_reference_worlds"] = worlds
manifest["native_entry"] = "remaining_props_native.run(mode, execution_manifest_path=..., execution_manifest_sha256=...)"
manifest["native_modes"] = ["finalize_vehicles", "inspect_pending_contacts", "read_rock_references"]
manifest["native_write_owner"] = "Existing bank integrator only, under actual-PID MANAGER_ACTIVATED lease. Category preparer has no editor lease."
manifest["cached_adapter_policy"] = "Use the exact frozen existing adapter without reload or edits. New module is independently bound. Source changes require renewed manager review."
write("EXECUTION_MANIFEST.json", manifest)
print(json.dumps({"prepared_vehicle_observations": len(vehicles), "pending_native_assets": len(pending),
                  "manifest_sha256": sha(HERE / "EXECUTION_MANIFEST.json"), "frozen_delivery_unchanged": True}))
