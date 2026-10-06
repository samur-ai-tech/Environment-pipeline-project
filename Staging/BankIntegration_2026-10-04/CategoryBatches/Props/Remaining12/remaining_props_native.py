"""Integrator-only evidence/finalization jobs; importing this file is offline-safe.

No editor launch, world switch, asset save, material edit, cook or area generation.
The native entry requires a reviewed complete manifest and the existing bank lease.
"""
import hashlib
import importlib
import importlib.util
import json
import math
import sys
import types
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_receipt(kind, value):
    digest = hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]
    path = HERE / (kind + "_" + digest + ".json")
    if path.exists():
        assert read(path) == value, "immutable_evidence_collision"
    else:
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return str(path)


def gate(path, expected_sha256):
    assert path and expected_sha256, "reviewed_complete_execution_manifest_path_and_sha256_required"
    assert sha(path) == expected_sha256, "reviewed_execution_manifest_sha256_mismatch"
    reviewed = read(path)
    local = read(HERE / "EXECUTION_MANIFEST.json")
    assert reviewed["manager_thread"] == local["manager_thread"], "execution_manifest_manager_mismatch"
    for section in ("files", "payloads", "evidence_files"):
        for filename, digest in local[section].items():
            assert reviewed[section].get(filename) == digest, ("execution_manifest_incomplete", filename)
            assert sha(filename) == digest, ("bound_file_changed", filename)
    # All custom source is bound before any native helper or Unreal import.
    sys.dont_write_bytecode = True
    base_manifest = read(FROZEN / "EXECUTION_MANIFEST.json")
    adapter_path = FROZEN / "category_batch.py"
    existing = [m for m in list(sys.modules.values()) if getattr(m, "__file__", None)
                and Path(m.__file__).resolve() == adapter_path.resolve()]
    if existing:
        assert len(existing) == 1, "duplicate_cached_props_adapter"
        batch = existing[0]
    else:
        spec = importlib.util.spec_from_file_location("props_remaining_frozen_adapter", adapter_path)
        batch = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = batch
        spec.loader.exec_module(batch)
    batch._verify_loaded_helper(batch, {"path": str(adapter_path), "sha256": local["files"][str(adapter_path)]})
    batch._verify_loaded_helper(types.SimpleNamespace(**globals()),
                                {"path": str(HERE / "remaining_props_native.py"),
                                 "sha256": local["files"][str(HERE / "remaining_props_native.py")]})
    batch._require_execution_manifest(path, expected_sha256, read(FROZEN / "READY_JOBS.json"))
    sys.path.insert(0, str(batch.INTEGRATION))
    C = importlib.import_module("bank_contracts")
    N = importlib.import_module("native_bank_ops")
    for name, identity in base_manifest["bank_helper_modules"].items():
        if name in sys.modules:
            batch._verify_loaded_helper(sys.modules[name], identity)
    before = N.preflight()
    # Preflight may load system guards; validate their exact loaded definitions too.
    for name, identity in base_manifest["system_modules"].items():
        if name in sys.modules:
            batch._verify_loaded_helper(sys.modules[name], identity)
    return batch, C, N, importlib.import_module("unreal"), before


def band(vertices, low, high):
    selected = [v for v in vertices if low - 1e-6 <= v[2] <= high + 1e-6]
    return {"z_min_cm": low, "z_max_cm": high, "vertices": len(selected),
            "xy_min": [min(v[i] for v in selected) for i in (0, 1)] if selected else None,
            "xy_max": [max(v[i] for v in selected) for i in (0, 1)] if selected else None}


def compare_source_bands(vertices, source_row):
    measured = []
    for expected in source_row["native_coordinate_contact_bands"]:
        actual = band(vertices, expected["z_min_cm"], expected["z_max_cm"])
        assert bool(actual["vertices"]) == bool(expected["vertices"]), "source_native_contact_presence_mismatch"
        if actual["vertices"]:
            assert all(abs(actual[key][i] - expected[key][i]) <= 0.05
                       for key in ("xy_min", "xy_max") for i in (0, 1)), "source_native_contact_extent_mismatch"
        measured.append(dict(actual, source_vertices=expected["vertices"], extent_tolerance_cm=0.05))
    actual_minimum = min(v[2] for v in vertices)
    expected_minimum = source_row["native_coordinate_contact_bands"][0]["z_min_cm"]
    assert abs(actual_minimum - expected_minimum) <= 0.005, "source_native_minimum_mismatch"
    return measured


def contact_readback(job, U):
    assert sha(job["native_identity"]["path"]) == job["native_identity"]["sha256"], job["asset_id"]
    mesh = U.load_asset(job["object_path"])
    assert isinstance(mesh, U.StaticMesh), job["asset_id"]
    desc = mesh.get_static_mesh_description(0)
    assert desc, "native_mesh_description_unavailable"
    vertices = []
    for number in range(desc.get_vertex_count()):
        vid = U.VertexID(number)
        assert desc.is_vertex_valid(vid), "sparse_vertex_ids_not_certified"
        v = desc.get_vertex_position(vid)
        vertices.append([v.x, v.y, v.z])
    assert vertices and all(math.isfinite(x) for v in vertices for x in v)
    minimum = job["configuration_payload"]["bounds_cm"]["min"][2]
    assert abs(min(v[2] for v in vertices) - minimum) <= 0.005, "retained_minimum_changed"
    bands = [band(vertices, minimum, minimum + width) for width in (0.05, 0.25, 1.0, 3.0)]
    bands += [band(vertices, -0.05, 0.05), band(vertices, -1.0, 1.0)]
    points = sorted(set(tuple(round(x, 4) for x in v) for v in vertices if v[2] <= minimum + 3.0))
    data = {"asset_id": job["asset_id"], "native_path": job["object_path"],
            "native_package_sha256": job["native_identity"]["sha256"],
            "retained_bounds_cm": job["configuration_payload"]["bounds_cm"],
            "contact_bands": bands, "lowest_3cm_unique_vertices": len(points),
            "lowest_3cm_points": points[:5000], "points_truncated": len(points) > 5000,
            "functional_support_accepted": False, "material_appearance_accepted": False}
    return data, vertices


def read_rock_references(U, N, before, local):
    exports = []
    for reference in local["rock_reference_worlds"]:
        assert sha(reference["file"]) == reference["sha256"], "vendor_world_changed"
        world = U.load_asset(reference["object_path"])
        assert isinstance(world, U.World), "vendor_reference_world_not_loadable"
        assert N.preflight() == before, "vendor_load_changed_editor_state_stop_without_save"
        target = HERE / ("RockReference_" + str(before["pid"]) + "_" + uuid.uuid4().hex[:12] + ".t3d")
        task = U.AssetExportTask()
        for key, value in {"object": world, "filename": str(target), "automated": True,
                           "prompt": False, "selected": False, "replace_identical": False,
                           "exporter": U.LevelExporterT3D()}.items():
            task.set_editor_property(key, value)
        succeeded = bool(U.Exporter.run_asset_export_task(task))
        assert N.preflight() == before, "vendor_export_changed_editor_state_stop_without_save"
        assert sha(reference["file"]) == reference["sha256"], "vendor_source_package_changed"
        exports.append({"world": reference["object_path"], "native_export_succeeded": succeeded,
                        "errors": [str(e) for e in task.errors], "export_path": str(target) if target.exists() else None,
                        "export_sha256": sha(target) if target.exists() else None,
                        "source_world_sha256": reference["sha256"], "embedment_accepted": False})
    return write_receipt("ROCK_REFERENCE_READBACK", {"pid": before["pid"], "world": before["world"],
                         "exports": exports, "editor_world_switched": False, "native_dirty_unchanged": True,
                         "decision_required": "Resolve rock instance transforms against the actual source ground. A raw transform or preview-floor screenshot alone does not establish burial depth."})


def run(mode, execution_manifest_path=None, execution_manifest_sha256=None):
    assert mode in ("finalize_vehicles", "inspect_pending_contacts", "read_rock_references"), "unsupported_job"
    batch, C, N, U, before = gate(execution_manifest_path, execution_manifest_sha256)
    local = read(HERE / "EXECUTION_MANIFEST.json")
    if mode == "read_rock_references":
        return {"receipt": read_rock_references(U, N, before, local), "ready_ids": []}
    all_jobs = {r["asset_id"]: r for r in read(FROZEN / "READY_JOBS.json")["rows"]}
    review_payload = read(HERE / "VEHICLE_OBSERVATIONS.json")["rows"]
    sources = {r["asset_id"]: r for r in read(HERE / "VEHICLE_SOURCE_CONTACT.json")["rows"]}
    pending = read(HERE / "PENDING_NATIVE_JOBS.json")["rows"]
    chosen = review_payload if mode == "finalize_vehicles" else pending
    readbacks = []
    for row in chosen:
        job = all_jobs[row["asset_id"]]
        data, vertices = contact_readback(job, U)
        if mode == "finalize_vehicles":
            data["source_native_contact_concordance"] = compare_source_bands(vertices, sources[row["asset_id"]])
            data["functional_support_accepted"] = True
            data["observation"] = row
        data["dependencies"] = N.dependency_closure(job["object_path"].split(".")[0])
        readbacks.append(data)
    assert N.preflight() == before, "contact_readback_changed_editor_state_stop_without_save"
    receipt = write_receipt("VEHICLE_NATIVE_CONTACT" if mode == "finalize_vehicles" else "PENDING_NATIVE_CONTACT",
                            {"pid": before["pid"], "world": before["world"], "rows": readbacks,
                             "native_dirty_unchanged": True, "ordinary_output": False, "fresh_reopen": False})
    if mode == "inspect_pending_contacts":
        return {"receipt": receipt, "ready_ids": [], "visual_and_functional_decisions_pending": True}
    # Only the two individually reviewed vehicle contracts enter the frozen finalizer.
    # Raw source observations deliberately retain false native-ready flags.
    # Only this guarded path can pass the observed appearance/support onward.
    assert all(row["source_contact_reviewed"] and row["source_material_appearance_reviewed"]
               for row in review_payload), "individual_source_observation_missing"
    reviews = [dict(row, evidence_receipt=receipt, contact_reviewed=True, material_reviewed=True)
               for row in review_payload]
    finalized = batch.integrate_reviewed(reviews=reviews, execution_manifest_path=execution_manifest_path,
                                       execution_manifest_sha256=execution_manifest_sha256)
    return {"native_contact_receipt": receipt, "finalization": finalized,
            "shared_build_apply_pending": True, "ordinary_output_save_reopen_pending": True}
