"""One-off, read-only catalog export for the Stage 2 preparation index."""

import csv
import json
from collections import Counter
from pathlib import Path


OLD_PROJECT = Path(r"C:\Users\USER\Documents\Unreal Projects\GIS_WorldBLD")
LIBRARY = OLD_PROJECT / "SourceData" / "ModelBanks_Archive" / "Unreal_Model_Library_2026-09-24"
STAGING = Path(r"C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\ModelBank")


def read_json(path):
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


catalog = read_json(LIBRARY / "Reports" / "library_catalog.json")
assert len(catalog) == 2063, len(catalog)
assert len({(r["bank"], r["id"]) for r in catalog}) == len(catalog)

rows = []
stats = Counter()
for item in catalog:
    bank, number = item["bank"], item["id"]
    source_record_path = LIBRARY / "Sources" / bank / "Reports" / f"{number:04d}.json"
    source_record = read_json(source_record_path)
    assert source_record["catalog_index"] == number
    assert source_record["name"] == item["name"]

    texture_paths = {
        map_info["file"]
        for material in source_record.get("material_maps", {}).values()
        for map_info in material.values()
        if isinstance(map_info, dict) and map_info.get("file")
    }
    for relative_path in texture_paths:
        assert (LIBRARY / "Sources" / bank / relative_path).is_file(), (
            bank, number, relative_path
        )

    native_asset = item.get("native_asset")
    if native_asset:
        assert native_asset.startswith("/Game/")
        native_path = OLD_PROJECT / "Content" / (native_asset[len("/Game/"):] + ".uasset")
        assert native_path.is_file(), native_path
        result = read_json(LIBRARY / "Reports" / bank / "UnrealResults" / f"{number:04d}.json")
        assert result["bank"] == bank and result["id"] == number
        material_count = len(result["materials"])
        geometry = "yes"
    else:
        assert item["status"] == "NO_GEOMETRY"
        native_path = ""
        material_count = 0
        geometry = "no"

    fbx = LIBRARY / item["source_fbx"]
    assert fbx.is_file(), fbx
    status = {"PASS": "passed", "REVIEW": "flagged", "NO_GEOMETRY": "no geometry"}[item["status"]]
    rows.append({
        "id": f"{number:04d}",
        "name": item["name"],
        "source_bank": bank,
        "category": item["category"],
        "old_project_file_path": str(native_path),
        "geometry_present": geometry,
        "import_check_result": status,
        "material_count": material_count,
        "texture_count": len(texture_paths),
        "source_fbx_path": str(fbx),
        "license_or_provenance_note": "",
    })
    stats[(bank, status)] += 1

output = STAGING / "FULL_INDEX.csv"
with output.open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {output}")
print(dict(stats))
