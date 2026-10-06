"""Read-only package and reference inventory in existing Unreal PID 32804.

Writes a JSON receipt beside this script. Does not save, load or switch maps,
change assets, cook, bake, or close any editor window.
"""

import datetime
import json
import os
from pathlib import Path

import unreal


EXPECTED_PID = 32804
EXPECTED_MAP = (
    "/Game/Developers/USER/HoudiniCityProof/"
    "L_B2_OriginalUntitled_Inspection_20261001."
    "L_B2_OriginalUntitled_Inspection_20261001"
)
FOLDERS = {
    "cook": (
        "/Game/Developers/USER/HoudiniCityProof/Cook/"
        "GeoCity_request_wiring_UI_2026_09_30/GeoCity_city_v002/239C90E0"
    ),
    "temp": "/Game/HoudiniEngine/Temp/GeoCity_city_v002/239C90E0",
}


def referencers(asset_path):
    return sorted(
        str(value)
        for value in unreal.EditorAssetLibrary.find_package_referencers_for_asset(
            asset_path, load_assets_to_confirm=False
        )
    )


def package_item(package):
    path = str(package.get_path_name())
    item = {"package": path}
    if path.startswith("/Game/"):
        asset_path = path + "." + path.rsplit("/", 1)[-1]
        item["asset_path"] = asset_path
        try:
            item["registry_referencers"] = referencers(asset_path)
        except Exception as exc:
            item["registry_error"] = repr(exc)
    return item


def main():
    if os.getpid() != EXPECTED_PID:
        raise RuntimeError(f"Wrong editor PID: {os.getpid()} (expected {EXPECTED_PID})")

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    world_path = str(world.get_path_name())
    if world_path != EXPECTED_MAP:
        raise RuntimeError(f"Unexpected editor world: {world_path}")

    now = datetime.datetime.now(datetime.timezone.utc)
    report = {
        "time_utc": now.isoformat(),
        "editor_pid": os.getpid(),
        "editor_world": world_path,
        "method": "Read-only Unreal Python: EditorLoadingAndSavingUtils dirty packages; EditorAssetLibrary registry referencers with load_assets_to_confirm=False; EditorActorSubsystem live components",
        "dirty_content": [],
        "dirty_maps": [],
        "scoped_assets": [],
        "actors": [],
        "live_mesh_references": [],
    }

    report["dirty_content"] = sorted(
        (package_item(pkg) for pkg in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
        key=lambda row: row["package"],
    )
    report["dirty_maps"] = sorted(
        (package_item(pkg) for pkg in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
        key=lambda row: row["package"],
    )

    for kind, folder in FOLDERS.items():
        try:
            paths = sorted(str(value) for value in unreal.EditorAssetLibrary.list_assets(
                folder, recursive=True, include_folder=False
            ))
        except Exception as exc:
            report.setdefault("folder_errors", {})[kind] = repr(exc)
            continue
        for path in paths:
            item = {"kind": kind, "asset_path": path}
            try:
                item["registry_referencers"] = referencers(path)
            except Exception as exc:
                item["registry_error"] = repr(exc)
            report["scoped_assets"].append(item)

    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    for actor in actors:
        actor_item = {
            "label": str(actor.get_actor_label()),
            "class": str(actor.get_class().get_name()),
            "path": str(actor.get_path_name()),
        }
        report["actors"].append(actor_item)
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            try:
                mesh = component.get_editor_property("static_mesh")
                mesh_path = str(mesh.get_path_name()) if mesh else ""
            except Exception:
                continue
            if not (
                mesh_path.startswith("/Game/Developers/USER/HoudiniCityProof/")
                or mesh_path.startswith("/Game/HoudiniEngine/Temp/")
            ):
                continue
            report["live_mesh_references"].append({
                "actor_label": actor_item["label"],
                "actor_path": actor_item["path"],
                "component": str(component.get_name()),
                "mesh": mesh_path,
            })
    report["actors"].sort(key=lambda row: row["label"])
    report["actor_count"] = len(report["actors"])
    report["live_mesh_references"].sort(key=lambda row: (
        row["mesh"], row["actor_label"], row["component"]
    ))

    output = Path(__file__).with_name(f"OPEN_STATE_{now:%Y%m%dT%H%M%SZ}.json")
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    unreal.log(
        f"B2_PID32804_OPEN_STATE {output} dirty_content={len(report['dirty_content'])} "
        f"dirty_maps={len(report['dirty_maps'])} scoped_assets={len(report['scoped_assets'])} "
        f"actors={report['actor_count']}"
    )


main()
