"""Offline transaction checks; no Unreal import, editor launch or shared write."""
import ast
import copy
import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch

# SourceFileLoader must not create helper caches outside the owned category.
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("props_offline", HERE / "category_batch.py")
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)
ast.parse((HERE / "category_batch.py").read_text(encoding="utf-8"))
ready = batch.read(HERE / "READY_JOBS.json")
manifest_path = HERE / "EXECUTION_MANIFEST.json"
native_arguments = {"execution_manifest_path": str(manifest_path), "execution_manifest_sha256": batch.sha(manifest_path)}
catalog = batch.read(batch.CATALOG)
records = {r["asset_id"]: r for r in catalog["rows"]}
jobs = ready["rows"]
all_ids = [r["asset_id"] for r in jobs + ready["excluded_rows"]]
expected = {r["asset_id"] for r in catalog["rows"] if r["recorded_category"] in {"SmallProps", "StreetProps"}}
assert len(all_ids) == len(set(all_ids)) and set(all_ids) == expected
for job in jobs:
    record = records[job["asset_id"]]
    assert job["row_name"] == record["catalog_row_name"]
    assert job["preserve"]["source_style"] == record["environment_style_set"]
    assert job["preserve"]["ExplicitHold"] == record["runtime"]["ExplicitHold"]
    if batch.yes(job["preserve"]["ExplicitHold"]):
        assert "RunEligible" not in job["runtime_delta"], job["asset_id"]
    assert "ExplicitHold" not in job["runtime_delta"] and "HoldReasons" not in job["runtime_delta"]
    if job["native_identity"]:
        assert job["native_identity"]["matches_expected"], job["asset_id"]
    for identity in job["material_slots"]:
        assert identity["exists"] and batch.sha(identity["path"]) == identity["sha256"]
reviews = batch.read(HERE / "REVIEW_EVIDENCE.json")["rows"]
assert {r["asset_id"] for r in reviews} == set(batch.NATIVE_HISTORICAL)
assert all(r["ready"] is False and r["material_reviewed"] is False for r in reviews)
assert {r["asset_id"] for r in ready["excluded_rows"]}.isdisjoint(r["asset_id"] for r in reviews)
try:
    batch.integrate_reviewed()
except AssertionError as e:
    assert str(e) == "reviewed_complete_execution_manifest_path_and_sha256_required"
else:
    raise AssertionError("unbound_native_entry_was_not_rejected")
# Supplier-appended category IDs without preparation must be named and rejected,
# without publishing a replacement batch that silently omits the new identity.
real_read = batch.read
captured_intake = {}
def supplier_read(path):
    value = real_read(path)
    if Path(path).resolve() == batch.CATALOG.resolve():
        value = copy.deepcopy(value)
        new = copy.deepcopy(value["rows"][0])
        new["asset_id"], new["recorded_category"] = "OFFLINE_NEW_UNPREPARED_PROP", "SmallProps"
        value["rows"].append(new)
    return value
def capture_intake(name, value):
    assert name == "INTAKE_REQUIRED.json"
    captured_intake.update(value)
with patch.object(batch, "read", supplier_read), patch.object(batch, "write", capture_intake):
    try: batch.build()
    except RuntimeError as e:
        assert "OFFLINE_NEW_UNPREPARED_PROP" in str(e)
    else: raise AssertionError("unprepared_supplier_id_was_not_rejected")
assert captured_intake["asset_ids"] == ["OFFLINE_NEW_UNPREPARED_PROP"]

# Simulate the adapter's transaction branch with explicit fake native modules.
# This validates adapter control flow only; it is not native/material evidence.
fixture = HERE / "OfflineChecks"
fixture.mkdir(exist_ok=True)
for name in ("NATIVE_CONFIGURATIONS.json", "NATIVE_INSTANCE_MATERIALS.json", "NATIVE_VALIDATION.json"):
    (fixture / name).write_text(json.dumps(batch.read(batch.INTEGRATION / name)), encoding="utf-8")
original_source = batch.sha(batch.CATALOG)
original_validation = batch.sha(batch.INTEGRATION / "NATIVE_VALIDATION.json")
fake_c = types.ModuleType("bank_contracts")
fake_c.SOURCE, fake_c.HERE = batch.CATALOG, fixture
fake_c.read, fake_c.sha, fake_c.package_file, fake_c.yes = batch.read, batch.sha, batch.package_file, batch.yes
def owned_write(path, value):
    assert Path(path).resolve().is_relative_to(fixture.resolve())
    Path(path).write_text(json.dumps(value), encoding="utf-8")
fake_c.write = owned_write
fake_n = types.ModuleType("native_bank_ops")
fake_n.preflight = lambda: {"pid": 0, "world": "OFFLINE_SIMULATION", "dirty": {"content": [], "maps": []}}
fake_n.dirty = lambda: {"content": [], "maps": []}
fake_n.dependency_closure = lambda p: {"packages": [p], "missing": []}
class FakeMaterial:
    def __init__(self, path): self.path = path
    def get_path_name(self): return self.path
fake_unreal = types.ModuleType("unreal")
fake_unreal.load_asset = lambda p: FakeMaterial(p)
fake_unreal.MaterialUsage = types.SimpleNamespace(MATUSAGE_INSTANCED_STATIC_MESHES=1)
fake_unreal.MaterialEditingLibrary = types.SimpleNamespace(
    has_material_usage=lambda m, u: True,
    get_used_textures=lambda m: [FakeMaterial("/Game/OfflineFixture/Texture.Texture")])
modules = {"bank_contracts": fake_c, "native_bank_ops": fake_n, "unreal": fake_unreal}
def mock_receipt_write(name, value):
    assert name.startswith("NATIVE_CONSUMPTION") and name.endswith(".json")
    owned_write(fixture / ("MOCK_" + name), value)
with patch.dict(sys.modules, modules), patch.object(batch, "write", mock_receipt_write), patch.object(batch, "_verify_loaded_helper", lambda m, i: None), patch.object(batch, "INTEGRATION", fixture):
    denied = False
    def reject(): raise AssertionError("offline_no_bank_lease")
    before_fixture = batch.sha(fixture / "NATIVE_VALIDATION.json")
    with patch.object(fake_n, "preflight", reject):
        try: batch.integrate_reviewed(**native_arguments)
        except AssertionError as e:
            assert str(e) == "offline_no_bank_lease"
            denied = True
    assert denied and batch.sha(fixture / "NATIVE_VALIDATION.json") == before_fixture
    # Empty texture query must not set readiness.
    with patch.object(fake_unreal.MaterialEditingLibrary, "get_used_textures", lambda m: []):
        result = batch.integrate_reviewed(**native_arguments)
        assert not result["new_validation_ids"] and len(result["pending"]) == 5
    result = batch.integrate_reviewed(**native_arguments)
    assert set(result["new_validation_ids"]) == set(batch.NATIVE_HISTORICAL)
    after = batch.read(fixture / "NATIVE_VALIDATION.json")
    for aid in batch.NATIVE_HISTORICAL:
        assert after[aid]["ready"] and after[aid]["material_reviewed"]
    # Re-running the same inputs is idempotent.
    repeat = batch.integrate_reviewed(**native_arguments)
    # Current source is intentionally unchanged/disabled in this fixture; the
    # adapter can refresh exact validation proof but cannot activate catalog rows.
    assert set(repeat["new_validation_ids"]) == set(batch.NATIVE_HISTORICAL)
assert batch.sha(batch.CATALOG) == original_source
assert batch.sha(batch.INTEGRATION / "NATIVE_VALIDATION.json") == original_validation
# Real helper sources can be imported against a mocked Unreal module without
# running a native entry point. Verify exact code identity and reject a stale body.
real_c_spec = importlib.util.spec_from_file_location("props_verify_bank_contracts", batch.INTEGRATION / "bank_contracts.py")
real_c = importlib.util.module_from_spec(real_c_spec)
real_c_spec.loader.exec_module(real_c)
batch._verify_loaded_helper(real_c, ready["helper_identities"]["bank_contracts"])
batch._verify_loaded_helper(batch, ready["adapter_identity"])
fake_unreal.EditorAssetLibrary = types.SimpleNamespace()
with patch.dict(sys.modules, {"bank_contracts": real_c, "unreal": fake_unreal}):
    real_n_spec = importlib.util.spec_from_file_location("props_verify_native_ops", batch.INTEGRATION / "native_bank_ops.py")
    real_n = importlib.util.module_from_spec(real_n_spec)
    real_n_spec.loader.exec_module(real_n)
    batch._verify_loaded_helper(real_n, ready["helper_identities"]["native_bank_ops"])
    with patch.object(real_n, "preflight", lambda: None):
        rejected = False
        try: batch._verify_loaded_helper(real_n, ready["helper_identities"]["native_bank_ops"])
        except AssertionError as e:
            assert "loaded_helper_code_differs" in str(e)
            rejected = True
        assert rejected
# Mock output remains below OfflineChecks and never appears as native evidence.
batch.write("CHECKS.json", {"adapter_syntax": "passed", "canonical_category_coverage": len(expected),
             "duplicate_ids": 0, "native_source_and_saved_material_identity_checks": "passed",
             "hold_and_style_preservation": "passed", "offline_lease_rejection": "passed",
             "loaded_helper_path_hash_code_identity": "passed", "stale_helper_function_rejection": "passed",
             "complete_manifest_path_sha_payload_binding": "passed",
             "missing_manifest_rejection_before_helper_import": "passed", "supplier_unprepared_identity_rejection": "passed",
             "offline_empty_texture_query_rejection": "passed", "offline_review_merge": "passed",
             "shared_source_and_validation_unchanged": True, "simulation_is_native_evidence": False,
             "actual_native_consumption": "NOT_RUN", "actual_ordinary_generation_save_reopen": "NOT_RUN"})
print(json.dumps(batch.read(HERE / "CHECKS.json")))
