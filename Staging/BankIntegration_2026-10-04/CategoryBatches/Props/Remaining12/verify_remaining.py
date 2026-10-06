"""Offline guard/evidence checks; no Unreal import, editor or shared writes."""
import ast
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("props_remaining_offline", HERE / "remaining_props_native.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert "unreal" not in sys.modules
for file in HERE.glob("*.py"):
    ast.parse(file.read_text(encoding="utf-8-sig"))
try:
    module.run("finalize_vehicles")
except AssertionError as error:
    assert str(error) == "reviewed_complete_execution_manifest_path_and_sha256_required"
else:
    raise AssertionError("unbound_entry_not_rejected")
assert "unreal" not in sys.modules
manifest = module.read(HERE / "EXECUTION_MANIFEST.json")
for section in ("files", "payloads", "evidence_files"):
    for path, digest in manifest[section].items():
        assert module.sha(path) == digest, (section, path)
vehicles = module.read(HERE / "VEHICLE_OBSERVATIONS.json")["rows"]
pending = module.read(HERE / "PENDING_NATIVE_JOBS.json")["rows"]
assert len(vehicles) == 2 and len(pending) == 10
assert len({r["asset_id"] for r in vehicles + pending}) == 12
assert all(not r["contact_reviewed"] and not r["material_reviewed"] for r in vehicles)
assert all(r["source_contact_reviewed"] and r["source_material_appearance_reviewed"] for r in vehicles)
assert all(r["anchor_z_cm"] is None and r["ready"] is False for r in pending)
source = module.read(HERE / "VEHICLE_SOURCE_CONTACT.json")["rows"]
assert all(r["source_files_unchanged"] and not r["native_readback_performed"] for r in source)
foodcart = next(r for r in vehicles if "SM_H0043_" in r["asset_id"])
wreck = next(r for r in vehicles if "SM_H0039_" in r["asset_id"])
assert foodcart["anchor_z_cm"] == 14.494669914245605 and wreck["anchor_z_cm"] == 0
# Contact transfer must fail if the native support is absent or displaced.
fixture = {"native_coordinate_contact_bands": [{"z_min_cm": 0, "z_max_cm": 1,
           "vertices": 2, "xy_min": [-1, -1], "xy_max": [1, 1]}]}
module.compare_source_bands([[-1, -1, 0], [1, 1, 0]], fixture)
for points in ([[20, 20, 0], [30, 30, 0]], [[-1, -1, 2], [1, 1, 2]]):
    try:
        module.compare_source_bands(points, fixture)
    except AssertionError:
        pass
    else:
        raise AssertionError("incorrect_native_support_was_accepted")
# Prove the manifest gate stops before any custom/native import on a stale payload.
real_sha = module.sha
module.sha = lambda p: "STALE" if str(p) == next(iter(manifest["payloads"])) else real_sha(p)
try:
    module.run("finalize_vehicles", str(HERE / "EXECUTION_MANIFEST.json"), real_sha(HERE / "EXECUTION_MANIFEST.json"))
except AssertionError as error:
    assert "bound_file_changed" in str(error)
else:
    raise AssertionError("stale_payload_not_rejected")
finally:
    module.sha = real_sha
assert "unreal" not in sys.modules
checks = {"offline_passed": True, "two_prepared_vehicle_contracts": True,
          "ten_individual_pending_records": True, "missing_manifest_rejected_before_native_import": True,
          "raw_source_payload_cannot_bypass_native_finalization": True,
          "stale_bound_payload_rejected_before_native_import": True, "wrong_native_contact_rejected": True,
          "frozen_manifest_sha256": module.sha(HERE.parent / "EXECUTION_MANIFEST.json"),
          "manifest_sha256": module.sha(HERE / "EXECUTION_MANIFEST.json"),
          "native_jobs_executed_here": False, "shared_files_or_content_written_here": False}
(HERE / "CHECKS.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
print(json.dumps(checks))
