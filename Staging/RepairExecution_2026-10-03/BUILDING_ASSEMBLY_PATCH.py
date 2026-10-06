"""Append to the retained GeoCity PythonModule after the other repair patches.

Normal geographic building fallback, through the existing Engine native point
output. Nothing runs on import. The assembly contract is supplied by the HDA
string parameter ``building_assembly_contract_json``. Canonical catalog rows,
their eligibility and explicit holds are never changed by this module.
"""

ASSEMBLY_MODULE_PATHS = {
    "window4": "/Game/ModularCourtyard/Meshes/SM_wall_windows_4x4_01.SM_wall_windows_4x4_01",
    "plain4": "/Game/ModularCourtyard/Meshes/SM_wall_4x4_01.SM_wall_4x4_01",
    "plain2": "/Game/ModularCourtyard/Meshes/SM_wall_4x2_01.SM_wall_4x2_01",
    "plain1": "/Game/ModularCourtyard/Meshes/SM_Wall_4x1_01.SM_Wall_4x1_01",
    "door": "/Game/ModularCourtyard/Meshes/SM_Steeldoor.SM_Steeldoor",
}


def _assembly_cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _assembly_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _assembly_area(ring):
    return sum(_assembly_cross(ring[i], ring[(i + 1) % len(ring)])
               for i in range(len(ring))) / 2.0


def _assembly_clean_ring(ring):
    """Remove duplicate/collinear vertices without moving the geographic edge."""
    cleaned = []
    for value in ring:
        point = (float(value[0]), float(value[1]))
        if not all(math.isfinite(v) for v in point):
            raise ValueError("assembly_nonfinite_footprint")
        if not cleaned or math.dist(point, cleaned[-1]) > 1e-7:
            cleaned.append(point)
    if len(cleaned) > 1 and math.dist(cleaned[0], cleaned[-1]) < 1e-7:
        cleaned.pop()
    changed = True
    while changed and len(cleaned) > 3:
        changed = False
        for i, point in enumerate(cleaned):
            before, after = cleaned[i - 1], cleaned[(i + 1) % len(cleaned)]
            a, b = _assembly_sub(point, before), _assembly_sub(after, point)
            if abs(_assembly_cross(a, b)) <= 1e-8 and sum(a[j] * b[j] for j in (0, 1)) >= 0:
                del cleaned[i]
                changed = True
                break
    if len(cleaned) < 3 or abs(_assembly_area(cleaned)) < 1.0:
        raise ValueError("assembly_degenerate_footprint")
    if _assembly_area(cleaned) < 0:
        cleaned.reverse()
    return cleaned


def _assembly_on_segment(p, a, b, tol=1e-7):
    ab, ap = _assembly_sub(b, a), _assembly_sub(p, a)
    return (abs(_assembly_cross(ab, ap)) <= tol * max(1.0, math.hypot(*ab))
            and min(a[0], b[0]) - tol <= p[0] <= max(a[0], b[0]) + tol
            and min(a[1], b[1]) - tol <= p[1] <= max(a[1], b[1]) + tol)


def _assembly_intersects(a, b, c, d, proper=False):
    ab, cd = _assembly_sub(b, a), _assembly_sub(d, c)
    values = (_assembly_cross(ab, _assembly_sub(c, a)),
              _assembly_cross(ab, _assembly_sub(d, a)),
              _assembly_cross(cd, _assembly_sub(a, c)),
              _assembly_cross(cd, _assembly_sub(b, c)))
    eps_ab = 1e-7 * max(1.0, math.hypot(*ab))
    eps_cd = 1e-7 * max(1.0, math.hypot(*cd))
    opposite_ab = ((values[0] > eps_ab and values[1] < -eps_ab) or
                   (values[0] < -eps_ab and values[1] > eps_ab))
    opposite_cd = ((values[2] > eps_cd and values[3] < -eps_cd) or
                   (values[2] < -eps_cd and values[3] > eps_cd))
    if opposite_ab and opposite_cd:
        return True
    return (not proper and any((_assembly_on_segment(c, a, b),
                               _assembly_on_segment(d, a, b),
                               _assembly_on_segment(a, c, d),
                               _assembly_on_segment(b, c, d))))


def _assembly_inside(point, ring):
    if any(_assembly_on_segment(point, ring[i], ring[(i + 1) % len(ring)])
           for i in range(len(ring))):
        return True
    x, z = point
    inside = False
    for i, a in enumerate(ring):
        b = ring[(i + 1) % len(ring)]
        if (a[1] > z) != (b[1] > z):
            crossing = a[0] + (z - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x < crossing:
                inside = not inside
    return inside


def _assembly_rectangle(a, tangent, start, end, thickness):
    inward = (-tangent[1], tangent[0])
    p = (a[0] + tangent[0] * start, a[1] + tangent[1] * start)
    q = (a[0] + tangent[0] * end, a[1] + tangent[1] * end)
    return [p, q, (q[0] + inward[0] * thickness, q[1] + inward[1] * thickness),
            (p[0] + inward[0] * thickness, p[1] + inward[1] * thickness)]


def _assembly_polygon_contained(polygon, ring):
    samples = list(polygon) + [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                               for a, b in zip(polygon, polygon[1:] + polygon[:1])]
    if any(not _assembly_inside(p, ring) for p in samples):
        return False
    return not any(_assembly_intersects(a, b, ring[i], ring[(i + 1) % len(ring)], True)
                   for a, b in zip(polygon, polygon[1:] + polygon[:1])
                   for i in range(len(ring)))


def _assembly_clip_convex(subject, clip):
    """Intersection of a footprint triangle and a CCW wall rectangle."""
    output = list(subject)
    for a, b in zip(clip, clip[1:] + clip[:1]):
        edge = _assembly_sub(b, a)
        original, output = output, []
        if not original:
            break
        previous = original[-1]
        before = _assembly_cross(edge, _assembly_sub(previous, a))
        for current in original:
            after = _assembly_cross(edge, _assembly_sub(current, a))
            if (before >= -1e-8) != (after >= -1e-8):
                fraction = before / (before - after)
                output.append((previous[0] + fraction * (current[0] - previous[0]),
                               previous[1] + fraction * (current[1] - previous[1])))
            if after >= -1e-8:
                output.append(current)
            previous, before = current, after
    unique = []
    for p in output:
        if not unique or math.dist(p, unique[-1]) > 1e-7:
            unique.append(p)
    if len(unique) > 1 and math.dist(unique[0], unique[-1]) < 1e-7:
        unique.pop()
    if len(unique) < 3 or _assembly_area(unique) < 1e-9:
        return []
    return unique


def _assembly_contract(parent, area_id):
    parm = parent.parm("building_assembly_contract_json")
    if parm is None:
        raise ValueError("assembly_contract_parameter_missing")
    contract = json.loads(parm.evalAsString() or "{}")
    if not contract.get("enabled"):
        return None
    if contract.get("schema") != "environmentpipeline.native_building_assembly.v1":
        raise ValueError("assembly_contract_schema_mismatch")
    if area_id not in contract.get("scope_area_ids", []):
        raise ValueError("assembly_area_outside_explicit_scope")
    for key, path in ASSEMBLY_MODULE_PATHS.items():
        module = contract.get("modules", {}).get(key, {})
        if module.get("path") != path or module.get("actual_named_or_dependency_hold", True):
            raise ValueError("assembly_module_path_or_actual_hold_invalid:" + key)
        if module.get("dependency_status") != "closed" or not module.get("native_measurement_source"):
            raise ValueError("assembly_module_dependency_or_measurement_missing:" + key)
        if module.get("route_hold_preserved") is not True:
            raise ValueError("assembly_canonical_route_hold_must_remain:" + key)
        bounds = module.get("min_cm", []) + module.get("max_cm", [])
        if len(bounds) != 6 or not all(math.isfinite(float(v)) for v in bounds):
            raise ValueError("assembly_native_bounds_invalid:" + key)
        if any(float(module["max_cm"][i]) <= float(module["min_cm"][i]) for i in range(3)):
            raise ValueError("assembly_native_bounds_degenerate:" + key)
        slots = module.get("material_slots", [])
        if not slots or any(not re.fullmatch(r"/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+", p) for p in slots):
            raise ValueError("assembly_native_material_slots_invalid:" + key)
    if not re.fullmatch(r"/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+", contract.get("closure_material_path", "")):
        raise ValueError("assembly_native_closure_material_invalid")
    return contract


def _assembly_tiles(span):
    """Bounded width scaling; small residuals are absorbed into complete bays."""
    if span < 0.5:
        return [("closure", span)] if span > 1e-7 else []
    windows = int(span // 4.0)
    remainder = span - windows * 4.0
    if windows and remainder < 0.5:
        return [("window4", span / windows)] * windows
    output = [("window4", 4.0)] * windows
    if remainder >= 3.0:
        output.append(("window4", remainder))
    elif remainder >= 1.5:
        output.append(("plain2", remainder))
    elif remainder >= 0.5:
        output.append(("plain1", remainder))
    return output


def assembly_layout(feature, contract):
    """Pure layout against the corrected pad; no raw terrain reads or app calls."""
    area_id, osm_id = str(feature["area_id"]), str(feature["osm_id"])
    if not feature.get("closed", False) or feature.get("holes", False):
        raise ValueError("assembly_requires_single_closed_hole_free_pad")
    ring = _assembly_clean_ring(feature["ring_xz_m"])
    if len(ring) > int(contract.get("max_footprint_vertices", 128)):
        raise ValueError("assembly_footprint_vertex_limit")
    for i, a in enumerate(ring):
        b = ring[(i + 1) % len(ring)]
        for j in range(i + 1, len(ring)):
            if j in (i, (i + 1) % len(ring)) or i == (j + 1) % len(ring):
                continue
            if _assembly_intersects(a, b, ring[j], ring[(j + 1) % len(ring)]):
                raise ValueError("assembly_self_intersecting_footprint")
    triangles = _triangles(ring)
    base, height = float(feature["base_m"]), float(feature["height_m"])
    if not math.isfinite(base) or not math.isfinite(height) or not 2.65 <= height <= 48.0:
        raise ValueError("assembly_height_outside_supported_2p65_to_48m")
    stories = max(1, int(math.floor(height / 3.2 + 0.5)))
    story_height = height / stories
    if not 2.65 <= story_height <= 4.4:
        raise ValueError("assembly_story_height_outside_supported_bounds")
    thickness = float(contract.get("closure_thickness_m", 0.56))
    if not 0.545 <= thickness <= 0.65:
        raise ValueError("assembly_closure_thickness_outside_measured_envelopes")
    edges = []
    for i, a in enumerate(ring):
        delta = _assembly_sub(ring[(i + 1) % len(ring)], a)
        length = math.hypot(*delta)
        if length < 0.05:
            raise ValueError("assembly_edge_too_short")
        edges.append({"index": i, "a": a, "length": length,
                      "tangent": (delta[0] / length, delta[1] / length)})
    trims = []
    for i, edge in enumerate(edges):
        previous = edges[i - 1]["tangent"]
        current = edge["tangent"]
        turn = math.atan2(_assembly_cross(previous, current), sum(a * b for a, b in zip(previous, current)))
        trim = max(thickness, thickness * math.tan(turn / 2.0) + 0.02) if turn > 0 else thickness
        trims.append(trim)
    usable = []
    for i, edge in enumerate(edges):
        start, end = trims[i], edge["length"] - trims[(i + 1) % len(edges)]
        if end < start:
            # The whole short edge becomes a generated closed corner strip.
            start = end = edge["length"] / 2.0
        rectangle = _assembly_rectangle(edge["a"], edge["tangent"], start, end, thickness)
        if end - start > 0.05 and not _assembly_polygon_contained(rectangle, ring):
            raise ValueError("assembly_native_wall_strip_leaves_geographic_footprint:edge" + str(i))
        edge.update(start_m=start, end_m=end, native_span_m=end - start)
        usable.append(end - start)
    door = contract["modules"]["door"]
    door_width = (float(door["max_cm"][1]) - float(door["min_cm"][1])) / 100.0
    door_height = (float(door["max_cm"][2]) - float(door["min_cm"][2])) / 100.0
    entrance_edge = max(range(len(edges)), key=lambda i: (usable[i], -i))
    if usable[entrance_edge] < door_width + 1.0 or door_height >= story_height - 0.05:
        raise ValueError("assembly_no_safe_true_door_opening")
    record = {"schema": "environmentpipeline.native_building_assembly_record.v1",
              "status": "complete", "source_feature": {"area_id": area_id, "osm_id": osm_id},
              "footprint_xz_m": ring, "footprint_area_m2": _assembly_area(ring),
              "base_m": base, "height_m": height, "height_rule": feature.get("height_rule", "unknown"),
              "stories": stories, "story_height_m": story_height, "edges": edges,
              "entrance_edge_index": entrance_edge, "wall_placements": [], "generated_parts": [],
              "closure_policy": "native_wall_bays_and_fillers_with_clipped_corner_solids_full_footprint_slabs_and_true_door_opening"}

    def solid(outline, bottom, top, role, floor, label):
        if top <= bottom + 1e-8 or len(outline) < 3 or _assembly_area(outline) < 1e-9:
            return
        record["generated_parts"].append({"part_id": area_id + ":" + osm_id + ":" + label,
            "role": role, "floor": floor, "outline_xz_m": outline,
            "bottom_y_m": bottom, "top_y_m": top, "material_path": (contract.get("slab_material_path", contract["closure_material_path"]) if role in ("assembly_floor_slab", "assembly_roof_slab") else contract["closure_material_path"])})

    def clipped_strip(edge, start, end, bottom, top, role, floor, label):
        if end - start < 1e-7:
            return
        rectangle = _assembly_rectangle(edge["a"], edge["tangent"], start, end, thickness)
        for ti, indices in enumerate(triangles):
            piece = _assembly_clip_convex([ring[j] for j in indices], rectangle)
            solid(piece, bottom, top, role, floor, label + ":t" + str(ti))

    def native(key, edge, start, width, bottom, module_height, floor, slot):
        module = contract["modules"][key]
        low = [float(v) / 100.0 for v in module["min_cm"]]
        high = [float(v) / 100.0 for v in module["max_cm"]]
        pitch, native_height = high[1] - low[1], high[2] - low[2]
        along_scale, vertical_scale = width / pitch, module_height / native_height
        if key == "door":
            if abs(along_scale - 1.0) > 1e-6 or abs(vertical_scale - 1.0) > 1e-6:
                raise ValueError("assembly_door_must_keep_native_scale")
        elif not (0.5 - 1e-6 <= along_scale <= 1.5 + 1e-6 and 0.65 <= vertical_scale <= 1.1 + 1e-6):
            raise ValueError("assembly_native_bay_scale_outside_contract")
        tangent, a = edge["tangent"], edge["a"]
        inward = (-tangent[1], tangent[0])
        anchor = (a[0] + tangent[0] * start, a[1] + tangent[1] * start)
        position = (anchor[0] - inward[0] * low[0] + tangent[0] * high[1] * along_scale,
                    bottom - low[2] * vertical_scale,
                    anchor[1] - inward[1] * low[0] + tangent[1] * high[1] * along_scale)
        placement = area_id + ":" + osm_id + ":assembly:f" + str(floor) + ":e" + str(edge["index"]) + ":s" + str(slot)
        record["wall_placements"].append({"placement_id": placement, "path": module["path"],
            "module_key": key, "asset_id": module["asset_id"], "role": "building_module",
            "rule": "measured_native_facade_assembly", "P": position,
            "orient": _quaternion(_rotation(tangent)), "scale": [1.0, vertical_scale, along_scale],
            "native_scale": [1.0, along_scale, vertical_scale], "floor": floor,
            "edge_index": edge["index"], "slot": slot, "edge_start_m": start,
            "edge_end_m": start + width, "facing_outward_xz": [tangent[1], -tangent[0]],
            "footprint_xz_m": _assembly_rectangle(a, tangent, start, start + width, high[0] - low[0]),
            "material_slots": module["material_slots"], "ground_contact_y_m": base,
            "source_area_id": area_id, "source_osm_id": osm_id,
            "selection_source": "explicit_scoped_native_assembly_contract",
            "catalog_release": False, "height_rule": record["height_rule"]})

    slab = float(contract.get("floor_slab_thickness_m", 0.18))
    if not 0.05 <= slab <= 0.3:
        raise ValueError("assembly_slab_thickness_invalid")
    for floor in range(stories):
        bottom, top = base + floor * story_height, base + (floor + 1) * story_height
        solid(ring, bottom, bottom + slab, "assembly_floor_slab", floor, "floor" + str(floor))
        for edge in edges:
            index = edge["index"]
            clipped_strip(edge, 0.0, edge["start_m"], bottom, top, "assembly_corner_closure", floor,
                          "f" + str(floor) + ":e" + str(index) + ":start")
            clipped_strip(edge, edge["end_m"], edge["length"], bottom, top, "assembly_corner_closure", floor,
                          "f" + str(floor) + ":e" + str(index) + ":end")
            spans = [(edge["start_m"], edge["end_m"])]
            if floor == 0 and index == entrance_edge:
                door_start = (edge["start_m"] + edge["end_m"] - door_width) / 2.0
                door_end = door_start + door_width
                native("door", edge, door_start, door_width, bottom, door_height, floor, -1)
                clipped_strip(edge, door_start, door_end, bottom + door_height, top,
                              "assembly_door_lintel", floor, "door_lintel")
                spans = [(edge["start_m"], door_start), (door_end, edge["end_m"])]
                record["entrance_opening"] = {"edge_index": index, "start_m": door_start,
                    "end_m": door_end, "bottom_y_m": bottom, "top_y_m": bottom + door_height,
                    "native_door_path": door["path"], "closed_wall_behind_door": False}
            slot = 0
            for start, end in spans:
                cursor = start
                for key, width in _assembly_tiles(end - start):
                    if key == "closure":
                        clipped_strip(edge, cursor, cursor + width, bottom, top,
                                      "assembly_small_infill", floor, "f" + str(floor) + ":e" + str(index) + ":s" + str(slot))
                    else:
                        native(key, edge, cursor, width, bottom, story_height, floor, slot)
                    cursor += width
                    slot += 1
                if abs(cursor - end) > 1e-6:
                    raise ValueError("assembly_wall_interval_not_closed")
    solid(ring, base + height - slab, base + height, "assembly_roof_slab", stories, "roof")
    if not any(p["module_key"] == "window4" for p in record["wall_placements"]):
        raise ValueError("assembly_no_native_window_bay")
    record["module_count"] = len(record["wall_placements"])
    record["generated_closed_solid_count"] = len(record["generated_parts"])
    record["coverage_check"] = {"all_edge_story_intervals_closed": True, "full_footprint_floor_and_roof": True,
                                "native_module_envelopes_inside_footprint": True, "real_door_opening": True,
                                "native_asset_mesh_topology_not_reauthored": True}
    return record


def cook_normal_building_assembly_points(node):
    """Input 0: selected native points; input 1: corrected geographic pads."""
    geo, parent = node.geometry(), node.parent()
    geo.clear()
    selected, pads = (input_node.geometry() for input_node in node.inputs()[:2])
    geo.merge(selected)
    area_id = str(pads.prims()[0].attribValue("source_area_id")) if pads.prims() else _package_for_sop(node)["area_id"]
    contract = _assembly_contract(parent, area_id)
    if contract is None:
        return
    if len(node.inputs()) < 3 or node.inputs()[2] is None:
        raise ValueError("assembly_final_corrected_terrain_input_missing")
    final_height = _grid_array(_volume(node.inputs()[2].geometry(), "height"))
    if parent.evalParm("modular_pilot_enabled") or parent.evalParm("module_test_enabled"):
        raise ValueError("normal_assembly_cannot_share_experimental_module_pilot")
    if selected.findGlobalAttrib("bank_catalog_readback_json") is None:
        raise ValueError("assembly_selected_native_receipt_missing")
    receipt = json.loads(selected.attribValue("bank_catalog_readback_json"))
    whole_ids = {str(p.attribValue("source_osm_id")) for p in selected.points()
                 if p.attribValue("bank_role") == "whole_building"}
    digest = hashlib.sha256(json.dumps(contract, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    records, unsupported, module_instances, seen_ids = [], [], [], set()
    for primitive in sorted(pads.prims(), key=lambda p: str(p.attribValue("source_osm_id"))):
        osm_id = str(primitive.attribValue("source_osm_id"))
        if osm_id in whole_ids:
            continue
        if osm_id in seen_ids:
            raise ValueError("assembly_duplicate_source_osm_id:" + osm_id)
        seen_ids.add(osm_id)
        feature = {"area_id": str(primitive.attribValue("source_area_id")), "osm_id": osm_id,
            "ring_xz_m": [(float(v.point().position()[0]), float(v.point().position()[2])) for v in primitive.vertices()],
            "base_m": float(primitive.attribValue("base_m")), "height_m": float(primitive.attribValue("height_m")),
            "height_rule": str(primitive.attribValue("height_rule")), "closed": primitive.isClosed(),
            "holes": bool(primitive.attribValue("has_holes")) if pads.findPrimAttrib("has_holes") else False}
        try:
            record = assembly_layout(feature, contract)
            contact_samples = list(record["footprint_xz_m"])
            for item in record["wall_placements"]:
                if item["floor"] == 0:
                    contact_samples.extend(item["footprint_xz_m"])
            elevations = _sample_grid(final_height, [p[0] for p in contact_samples],
                                      [p[1] for p in contact_samples])
            tolerance = float(contract.get("terrain_contact_tolerance_m", 0.04))
            max_delta = max(abs(float(y) - record["base_m"]) for y in elevations)
            if not math.isfinite(max_delta) or max_delta > tolerance:
                raise ValueError("assembly_final_terrain_does_not_support_native_envelope:delta_m=%.6f" % max_delta)
            record["terrain_contact"] = {"sample_count": len(contact_samples),
                "max_absolute_base_delta_m": max_delta, "tolerance_m": tolerance,
                "source": "explicit_final_corrected_heightfield_input", "supported": True}
        except ValueError as error:
            unsupported.append({"source_area_id": area_id, "source_osm_id": osm_id,
                                "status": "unsupported_original_shell_retained", "reason": str(error),
                                "height_m": feature["height_m"], "base_m": feature["base_m"]})
            continue
        records.append(record)
        module_instances.extend(record["wall_placements"])
    for item in module_instances:
        point = geo.createPoint()
        point.setPosition(item["P"])
        strings = {"unreal_instance": item["path"], "bank_asset_id": item["asset_id"],
            "bank_role": "building_module", "placement_rule": item["rule"],
            "placement_id": item["placement_id"], "source_area_id": item["source_area_id"],
            "source_osm_id": item["source_osm_id"], "source_detail_id": "",
            "bank_selection_source": item["selection_source"], "bank_catalog_sha256": receipt.get("catalog_sha256", ""),
            "assembly_contract_sha256": digest, "assembly_module_key": item["module_key"]}
        for key, value in strings.items():
            point.setAttribValue(_attr(geo, hou.attribType.Point, key, ""), value)
        orient = _attr(geo, hou.attribType.Point, "orient", (0.0, 0.0, 0.0, 1.0))
        point.setAttribValue(orient, item["orient"])
        point.setAttribValue(_attr(geo, hou.attribType.Point, "scale", (1.0, 1.0, 1.0)), item["scale"])
        for key in ("floor", "edge_index", "slot"):
            point.setAttribValue(_attr(geo, hou.attribType.Point, key, 0), item[key])
        for index, material in enumerate(item["material_slots"]):
            point.setAttribValue(_attr(geo, hou.attribType.Point, "unreal_material" + str(index), ""), material)
    summary = {"schema": "environmentpipeline.native_building_assembly_summary.v1", "contract_sha256": digest,
        "scope_area_id": area_id, "whole_native_building_count": len(whole_ids),
        "unmatched_geographic_building_count": len(seen_ids), "assembled_building_count": len(records),
        "native_module_point_count": len(module_instances), "unsupported_count": len(unsupported),
        "unsupported": unsupported, "assembled_osm_ids": [r["source_feature"]["osm_id"] for r in records],
        "appearance_accepted": False, "native_mesh_1_to_1_whole_building_policy_preserved": True,
        "canonical_catalog_holds_unchanged": True}
    receipt["instances"] = list(receipt.get("instances", [])) + module_instances
    receipt["nonbuilding_instances"] = list(receipt.get("nonbuilding_instances", [])) + module_instances
    receipt["building_module_instances"] = module_instances
    receipt["building_assembly"] = summary
    receipt["native_building_assembly_records"] = records
    expected = {}
    for item in receipt["instances"]:
        expected[item["path"]] = expected.get(item["path"], 0) + 1
    receipt["expected_mesh_counts"] = expected
    receipt["expected_native_instance_count"] = len(receipt["instances"])
    receipt["generator_revision"] = "r015_geographic_native_assembly"
    _set_detail(geo, "bank_catalog_readback_json", json.dumps(receipt, sort_keys=True, allow_nan=False))
    _set_detail(geo, "building_assembly_records_json", json.dumps(records, sort_keys=True, allow_nan=False))
    _set_detail(geo, "building_assembly_summary_json", json.dumps(summary, sort_keys=True, allow_nan=False))
    _set_detail(geo, "bank_instances", len(receipt["instances"]))
    _set_detail(geo, "unreal_output_name", "bank_instances")
    report = parent.evalParm("bank_receipt_file").strip()
    if report:
        Path(report).write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")


_assembly_original_building_replacement = cook_permanent_building_replacement


def cook_permanent_building_replacement(node):
    """Remove shells only for whole native or fully closed recorded assemblies."""
    _assembly_original_building_replacement(node)
    geo, native_points = node.geometry(), node.inputs()[1].geometry()
    if native_points.findGlobalAttrib("building_assembly_records_json") is None:
        return
    records = json.loads(native_points.attribValue("building_assembly_records_json"))
    complete_ids = {r["source_feature"]["osm_id"] for r in records if r["status"] == "complete"}
    source_id = geo.findPrimAttrib("source_osm_id")
    if source_id and complete_ids:
        geo.deletePrims([p for p in geo.prims() if p.attribValue(source_id) in complete_ids], keep_points=False)
    for record in records:
        if record["status"] != "complete":
            raise ValueError("building_replacement_received_incomplete_assembly")
        generated = generated_geometry(record)
        output = generated.findPrimAttrib("unreal_output_name")
        for primitive in generated.prims():
            primitive.setAttribValue(output, record["source_feature"]["area_id"] + "_buildings")
        geo.merge(generated)
    _set_detail(geo, "native_assembly_replaced_osm_ids_json", json.dumps(sorted(complete_ids)))
    _set_detail(geo, "building_assembly_summary_json", native_points.attribValue("building_assembly_summary_json"))


def configure_normal_building_assembly_graph(asset):
    """Root integrator calls explicitly before updating the existing definition.

    This helper changes only the retained asset's SOP connections. It does not
    cook, alter any Unreal asset, write a catalog, or acquire an editor lease.
    """
    selector = asset.node("nonbuilding_catalog_selector")
    pads = asset.node("centroid_buildings_and_ground_pads")
    replacement = asset.node("catalog_wholebuilding_replacement")
    bank_merge = asset.node("modular_wall_points")
    tree_filter = asset.node("bank_filtered_trees")
    pole_filter = asset.node("bank_filtered_street_poles")
    if any(item is None for item in (selector, pads, replacement, bank_merge, tree_filter, pole_filter)):
        raise ValueError("assembly_required_retained_graph_nodes_missing")
    terrain = selector.inputs()[3] if len(selector.inputs()) > 3 else None
    if terrain is None:
        raise ValueError("assembly_existing_selector_final_terrain_input_missing")
    assembly = asset.node("normal_building_assembly_points")
    if assembly is None:
        assembly = asset.createNode("python", "normal_building_assembly_points")
    assembly.setInput(0, selector)
    assembly.setInput(1, pads)
    assembly.setInput(2, terrain)
    assembly.parm("python").set("hou.pwd().parent().hdaModule().cook_stage(hou.pwd(), 'cook_normal_building_assembly_points')")
    replacement.setInput(1, assembly)
    bank_merge.setInput(0, assembly)
    # Proxy reports merge into the same receipt file. Force the complete native
    # ledger before either report, regardless of Unreal's output traversal order.
    tree_filter.setInput(1, assembly)
    pole_filter.setInput(1, assembly)
    return {"assembly_node": assembly.path(), "inputs": [selector.name(), pads.name(), terrain.name()],
            "native_output": "modular_wall_points -> output_bank_instances",
            "proxy_report_dependencies": {tree_filter.name(): {"input_1": assembly.name()},
                                          pole_filter.name(): {"input_1": assembly.name()}},
            "generated_closure_output": "catalog_wholebuilding_replacement -> bank_inspection_switch_3 -> output_buildings"}
