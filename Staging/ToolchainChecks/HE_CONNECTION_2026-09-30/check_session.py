"""One-off official Houdini Engine session/licence check; no cook, bake or save."""

import datetime
import json
import pathlib
import time
import traceback

import unreal


OUT = pathlib.Path(__file__).with_name("runtime_result.json")
HDA_PATH = "/Game/Developers/USER/HoudiniCityProof/B1_probebox.B1_probebox"
result = {
    "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "hda_path": HDA_PATH,
    "activity": "official Public API session plus one standalone cookable instantiation",
    "auto_cook": False,
    "auto_bake": False,
    "asset_save": False,
}
api = None
wrapper = None


def record():
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log("HE_CONNECTION_CHECK " + json.dumps(result, sort_keys=True))


try:
    api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
    result["api_present"] = api is not None
    if api is None:
        raise RuntimeError("Houdini Engine Public API unavailable in Unreal commandlet")

    result["session_valid_before"] = bool(api.is_session_valid())
    if not result["session_valid_before"]:
        api.create_session()
    result["session_valid_after_create"] = bool(api.is_session_valid())
    if not result["session_valid_after_create"]:
        raise RuntimeError("Official Public API did not establish a valid session")

    hda = unreal.load_object(None, HDA_PATH)
    result["existing_hda_found"] = hda is not None
    if hda is None:
        raise RuntimeError("Existing B1 HDA asset not found; no substitute created")

    settings = unreal.HoudiniPublicAPISettings()
    settings.set_editor_property("enable_auto_cook", False)
    settings.set_editor_property("enable_auto_bake", False)
    enum = unreal.HoudiniPublicAPIInstantiationType
    candidates = [name for name in dir(enum) if name.upper() == "COOKABLE"]
    if len(candidates) != 1:
        raise RuntimeError("Cookable enum not found: " + repr(candidates))
    wrapper = api.instantiate(hda, getattr(enum, candidates[0]), settings)
    result["cookable_instantiated"] = wrapper is not None
    result["session_valid_after_instantiate"] = bool(api.is_session_valid())
    record()

    # Give the independent SideFX licence query time to observe the live checkout.
    time.sleep(40)
except Exception:
    result["error"] = traceback.format_exc()
    record()
finally:
    if api is not None:
        try:
            result["session_valid_before_stop"] = bool(api.is_session_valid())
            if result["session_valid_before_stop"]:
                api.stop_session()
            result["session_valid_after_stop"] = bool(api.is_session_valid())
        except Exception:
            result["stop_error"] = traceback.format_exc()
    result["ended_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record()
