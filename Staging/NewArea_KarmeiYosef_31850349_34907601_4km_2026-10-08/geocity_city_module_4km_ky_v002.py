"""Embedded PythonModule for GeoCity city generation.

The OSM features come only from SideFX Labs Import/Filter. This module validates
the package, samples the DSM, and builds deterministic geometry from Labs output.
"""

import hashlib
import csv
import json
import math
import os
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET

import hou
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SCHEMA = "Environmentpipeline city source package v1"
ROLES = ("osm_xml", "dsm_geotiff", "control_points")
GRID_SAMPLES = 4033
GRID_SPACING_M = 1.0
EARTH_RADIUS_M = 6373000.0  # SideFX Labs 22.0.429 OSM Import's haversine radius.


def _fail(message):
    raise hou.NodeError("GeoCity city: " + message)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _number(value, label):
    try:
        result = float(value)
    except (TypeError, ValueError):
        _fail("%s is not a number" % label)
    if not math.isfinite(result):
        _fail("%s is not finite" % label)
    return result


def _bounds_from_xml(path):
    # Read only the OSM header. Labs remains the sole reader of OSM features.
    for _, element in ET.iterparse(str(path), events=("start",)):
        if element.tag == "bounds":
            return {
                "west": _number(element.attrib.get("minlon"), "OSM minlon"),
                "south": _number(element.attrib.get("minlat"), "OSM minlat"),
                "east": _number(element.attrib.get("maxlon"), "OSM maxlon"),
                "north": _number(element.attrib.get("maxlat"), "OSM maxlat"),
            }
        if element.tag in ("node", "way", "relation"):
            break
    _fail("OSM XML has no <bounds> header: %s" % path)


def _factors(lat0):
    phi = math.radians(lat0)
    a = 6378137.0
    flattening = 1.0 / 298.257223563
    e2 = flattening * (2.0 - flattening)
    denom = 1.0 - e2 * math.sin(phi) ** 2
    mlat = math.pi / 180.0 * a * (1.0 - e2) / denom ** 1.5
    mlon = math.pi / 180.0 * a * math.cos(phi) / math.sqrt(denom)
    return mlat, mlon


def _haversine(lat_a, lon_a, lat_b, lon_b):
    a = math.radians(lat_a)
    b = math.radians(lat_b)
    dlat = b - a
    dlon = math.radians(lon_b - lon_a)
    s = math.sin(dlat / 2.0) ** 2 + math.cos(a) * math.cos(b) * math.sin(dlon / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(s)))


def load_package(package_file):
    package_path = Path(os.path.expandvars(os.path.expanduser(str(package_file)))).resolve()
    if not package_path.is_file():
        _fail("package JSON is missing: %s" % package_path)
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail("cannot read package JSON %s: %s" % (package_path, exc))
    if package.get("schema") != SCHEMA:
        _fail("unsupported package schema in %s: %r" % (package_path, package.get("schema")))
    area_id = package.get("area_id")
    if not isinstance(area_id, str) or not area_id or not all(c.isalnum() or c == "_" for c in area_id):
        _fail("area_id must be a nonempty identifier")
    entries = package.get("files")
    if not isinstance(entries, list):
        _fail("files[] is missing")
    files = {}
    for entry in entries:
        role = entry.get("role")
        if role not in ROLES or role in files:
            _fail("duplicate or unsupported file role: %r" % role)
        rel = entry.get("path")
        if not isinstance(rel, str) or not rel or Path(rel).is_absolute():
            _fail("file role %s requires a relative path" % role)
        full = (package_path.parent / rel).resolve()
        try:
            full.relative_to(package_path.parent)
        except ValueError:
            _fail("file role %s escapes its package directory" % role)
        if not full.is_file():
            _fail("file role %s is missing: %s" % (role, full))
        actual_size = full.stat().st_size
        if actual_size != entry.get("bytes"):
            _fail("file role %s has %d bytes, expected %r" % (role, actual_size, entry.get("bytes")))
        actual_hash = _sha256(full)
        if actual_hash.lower() != str(entry.get("sha256", "")).lower():
            _fail("file role %s SHA-256 mismatch: %s" % (role, full))
        files[role] = {"path": str(full).replace("\\", "/"), "sha256": actual_hash, "bytes": actual_size}
    if set(files) != set(ROLES):
        _fail("files[] must have exactly the roles %s" % (", ".join(ROLES)))
    if "EPSG:4326" not in str(package.get("horizontal_crs", "")):
        _fail("horizontal_crs must declare EPSG:4326")
    if "EGM2008" not in str(package.get("vertical_datum", "")):
        _fail("vertical_datum must declare EGM2008 metres")
    bounds = {key: _number(package.get("area_bounds", {}).get(key), "area_bounds." + key)
              for key in ("west", "south", "east", "north")}
    if bounds["east"] <= bounds["west"] or bounds["north"] <= bounds["south"]:
        _fail("area_bounds has nonpositive extent")
    osm_bounds = _bounds_from_xml(files["osm_xml"]["path"])
    for key in bounds:
        if abs(bounds[key] - osm_bounds[key]) > 1e-9:
            _fail("OSM <bounds> %s=%r differs from package %r" % (key, osm_bounds[key], bounds[key]))
    lon0 = _number(package.get("origin", {}).get("lon0"), "origin.lon0")
    lat0 = _number(package.get("origin", {}).get("lat0"), "origin.lat0")
    if abs(lon0 - (bounds["west"] + bounds["east"]) / 2.0) > 1e-9 or abs(lat0 - (bounds["south"] + bounds["north"]) / 2.0) > 1e-9:
        _fail("origin must be the OSM bounds centre")
    mlat, mlon = _factors(lat0)
    declared = package.get("local_frame", {})
    if abs(_number(declared.get("Mlat_m_per_deg"), "Mlat_m_per_deg") - mlat) > 0.01:
        _fail("declared Mlat differs from the WGS84 formula")
    if abs(_number(declared.get("Mlon_m_per_deg"), "Mlon_m_per_deg") - mlon) > 0.01:
        _fail("declared Mlon differs from the WGS84 formula")
    d_ns = _haversine(bounds["south"], bounds["west"], bounds["north"], bounds["west"])
    d_ew = _haversine(bounds["south"], bounds["west"], bounds["south"], bounds["east"])
    frame = {
        "east_scale": mlon * (bounds["east"] - bounds["west"]) / d_ew,
        "east_offset": -mlon * (lon0 - bounds["west"]),
        "south_scale": -mlat * (bounds["north"] - bounds["south"]) / d_ns,
        "south_offset": mlat * (lat0 - bounds["south"]),
        "Mlat_m_per_deg": mlat, "Mlon_m_per_deg": mlon,
        "labs_length_m": d_ns, "labs_height_m": d_ew,
        "lon0": lon0, "lat0": lat0,
    }
    try:
        controls = json.loads(Path(files["control_points"]["path"]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail("cannot read control_points JSON: %s" % exc)
    points = controls.get("points")
    if not isinstance(points, list) or not points:
        _fail("control_points JSON has no points[]")
    names = set()
    for item in points:
        name = item.get("name")
        if not isinstance(name, str) or not name or name in names:
            _fail("control point names must be unique and nonempty")
        names.add(name)
        _number(item.get("lon"), "control longitude")
        _number(item.get("lat"), "control latitude")
    return {"path": str(package_path).replace("\\", "/"), "sha256": _sha256(package_path),
            "area_id": area_id, "bounds": bounds, "files": files, "frame": frame, "controls": points,
            "vertical_datum": package["vertical_datum"]}


def source_path(package_file, role):
    return load_package(package_file)["files"][role]["path"]


def _package_for_sop(node):
    return load_package(node.evalParm("package_file"))


def _set_detail(geometry, name, value):
    if geometry.findGlobalAttrib(name) is None:
        geometry.addAttrib(hou.attribType.Global, name, value)
    geometry.setGlobalAttribValue(name, value)


def cook_metadata(node):
    info = _package_for_sop(node)
    geo = node.geometry()
    raw = node.inputs()[0].geometry()
    if len(raw.prims()) == 0:
        _fail("Labs OSM Import returned zero primitives")
    for key, expected in (("min_lon", info["bounds"]["west"]),
                          ("min_lat", info["bounds"]["south"]),
                          ("max_lon", info["bounds"]["east"]),
                          ("max_lat", info["bounds"]["north"])):
        actual = float(raw.attribValue(key))
        expected_f32 = struct.unpack("f", struct.pack("f", expected))[0]
        if abs(actual - expected_f32) > 1e-5:
            _fail("Labs %s=%r disagrees with float32 bounds %r" % (key, actual, expected_f32))
    for key, expected in (("map_length", info["frame"]["labs_length_m"]),
                          ("map_height", info["frame"]["labs_height_m"])):
        if abs(float(raw.attribValue(key)) - expected) > 0.001:
            _fail("Labs %s disagrees with XML bounds projection" % key)
    for key in ("east_scale", "east_offset", "south_scale", "south_offset"):
        _set_detail(geo, key, float(info["frame"][key]))
    _set_detail(geo, "area_id", info["area_id"])
    _set_detail(geo, "package_sha256", info["sha256"])
    _set_detail(geo, "control_count", len(info["controls"]))


def read_geotiff(path):
    with Image.open(path) as image:
        tags = image.tag_v2
        if 33550 not in tags or 33922 not in tags:
            _fail("DSM GeoTIFF lacks pixel scale/tie point")
        scale = tuple(float(v) for v in tags[33550])
        tie = tuple(float(v) for v in tags[33922])
        keys = tuple(int(v) for v in tags.get(34735, ()))
        key_map = {}
        for k in range(4, len(keys) - 3, 4):
            key_id, location, count, value = keys[k:k+4]
            if location == 0 and count == 1:
                key_map[key_id] = value
        if key_map.get(2048) != 4326 or key_map.get(1025) != 2:
            _fail("DSM GeoTIFF must be EPSG:4326 PixelIsPoint")
        if image.mode != "F" or len(scale) < 2 or len(tie) < 5 or scale[0] <= 0 or scale[1] <= 0:
            _fail("DSM GeoTIFF must be single-band float32 with a valid geotransform")
        if abs(tie[0]) > 1e-12 or abs(tie[1]) > 1e-12:
            _fail("DSM GeoTIFF tie point must start at pixel (0, 0)")
        data = np.asarray(image, dtype=np.float32).copy()
    if not np.isfinite(data).all():
        _fail("DSM GeoTIFF has NaN or infinite elevations")
    return data, tie[3], tie[4], scale[0], scale[1]


def sample_dsm(info, lon, lat):
    raster, lon00, lat00, sx, sy = read_geotiff(info["files"]["dsm_geotiff"]["path"])
    u = (np.asarray(lon, dtype=np.float64) - lon00) / sx
    v = (lat00 - np.asarray(lat, dtype=np.float64)) / sy
    if np.min(u) < 0 or np.max(u) > raster.shape[1]-1 or np.min(v) < 0 or np.max(v) > raster.shape[0]-1:
        _fail("DSM crop does not cover the requested grid/control point")
    i = np.clip(np.floor(u).astype(np.int64), 0, raster.shape[1]-2)
    j = np.clip(np.floor(v).astype(np.int64), 0, raster.shape[0]-2)
    fu = u-i
    fv = v-j
    values = (1-fv)*(1-fu)*raster[j,i] + (1-fv)*fu*raster[j,i+1] + fv*(1-fu)*raster[j+1,i] + fv*fu*raster[j+1,i+1]
    return values


def _volume(geo, name):
    for primitive in geo.prims():
        if isinstance(primitive, hou.Volume) and primitive.attribValue("name") == name:
            return primitive
    _fail("heightfield lacks volume layer %s" % name)


def cook_terrain(node):
    info = _package_for_sop(node)
    geo = node.geometry()
    half = (GRID_SAMPLES-1)/2.0
    height = _volume(geo, "height")
    if height.resolution() != (GRID_SAMPLES, GRID_SAMPLES, 1):
        _fail("heightfield resolution is %r, expected %d square" % (height.resolution(), GRID_SAMPLES))
    p00 = height.indexToPos((0,0,0))
    p10 = height.indexToPos((1,0,0))
    p01 = height.indexToPos((0,1,0))
    if max(abs(p00[0]+half), abs(p00[2]+half), abs(p10[2]-p00[2]-1.0),
           abs(p01[0]-p00[0]-1.0)) > 1e-5:
        _fail("heightfield grid is not centred east/south at 1 m")
    coordinate = np.arange(GRID_SAMPLES, dtype=np.float64)-half
    lon = info["frame"]["lon0"] + coordinate/info["frame"]["Mlon_m_per_deg"]
    lat = info["frame"]["lat0"] - coordinate/info["frame"]["Mlat_m_per_deg"]
    lon_grid, lat_grid = np.meshgrid(lon, lat)
    heights = np.asarray(sample_dsm(info, lon_grid, lat_grid), dtype=np.float32)
    height.setAllVoxels(heights.flatten(order="F").tolist())
    for primitive in geo.prims():
        if geo.findPrimAttrib("unreal_output_name") is None:
            geo.addAttrib(hou.attribType.Prim, "unreal_output_name", "")
        primitive.setAttribValue("unreal_output_name", info["area_id"] + "_terrain_intake")
    _set_detail(geo, "source_area_id", info["area_id"])
    _set_detail(geo, "source_package_sha256", info["sha256"])
    _set_detail(geo, "dsm_sha256", info["files"]["dsm_geotiff"]["sha256"])
    _set_detail(geo, "vertical_datum", info["vertical_datum"])
    _set_detail(geo, "terrain_min_m", float(heights.min()))
    _set_detail(geo, "terrain_max_m", float(heights.max()))
    _set_detail(geo, "terrain_grid_samples", GRID_SAMPLES)


def cook_controls(node):
    info = _package_for_sop(node)
    geo = node.geometry()
    geo.clear()  # The metadata input establishes a cook dependency, not geometry to retain.
    name_attrib = geo.addAttrib(hou.attribType.Point, "control_name", "")
    lon_attrib = geo.addAttrib(hou.attribType.Point, "longitude", 0.0)
    lat_attrib = geo.addAttrib(hou.attribType.Point, "latitude", 0.0)
    osm_node_attrib = geo.addAttrib(hou.attribType.Point, "nearest_osm_node_id", "")
    local_x_attrib = geo.addAttrib(hou.attribType.Point, "local_x_east_m", 0.0)
    local_z_attrib = geo.addAttrib(hou.attribType.Point, "local_z_south_m", 0.0)
    lon = np.array([float(item["lon"]) for item in info["controls"]], dtype=np.float64)
    lat = np.array([float(item["lat"]) for item in info["controls"]], dtype=np.float64)
    heights = sample_dsm(info, lon, lat)
    for item, xlon, ylat, elevation in zip(info["controls"], lon, lat, heights):
        x = (xlon-info["frame"]["lon0"])*info["frame"]["Mlon_m_per_deg"]
        z = -(ylat-info["frame"]["lat0"])*info["frame"]["Mlat_m_per_deg"]
        point = geo.createPoint()
        point.setPosition((float(x), float(elevation), float(z)))
        point.setAttribValue(name_attrib, item["name"])
        point.setAttribValue(lon_attrib, float(xlon))
        point.setAttribValue(lat_attrib, float(ylat))
        point.setAttribValue(osm_node_attrib, str(item.get("nearest_node", {}).get("id", "")))
        point.setAttribValue(local_x_attrib, float(x))
        point.setAttribValue(local_z_attrib, float(z))
    _set_detail(geo, "source_area_id", info["area_id"])
    _set_detail(geo, "control_sha256", info["files"]["control_points"]["sha256"])
    _set_detail(geo, "unreal_output_name", info["area_id"] + "_controls_intake")


# City-stage rules use Labs features. No OSM node/way parser is present here.
ROAD_WIDTH_M = {"secondary": 12.0, "secondary_link": 7.0, "tertiary": 9.0, "residential": 7.0,
                "service": 4.0, "footway": 2.2, "path": 1.6,
                "track": 3.0, "unclassified": 6.0,
                # Karmei Yosef 4 km v002 (Aviv 2026-10-11): road 44 and its links were dropped by v001.
                "trunk": 12.0, "trunk_link": 7.0, "primary": 10.0, "primary_link": 7.0}
ROAD_CLASSES = {"secondary", "secondary_link", "tertiary", "residential", "service", "unclassified",
                "trunk", "trunk_link", "primary", "primary_link"}
FOOTPATH_CLASSES = {"footway", "path", "track"}
# v002: rural highways get no 1.5 m sidewalks (road surface and road bed only)
NO_SIDEWALK_CLASSES = {"trunk", "trunk_link", "primary", "primary_link"}


def _local_box(info):
    b, f = info["bounds"], info["frame"]
    return ((b["west"]-f["lon0"])*f["Mlon_m_per_deg"],
            (b["east"]-f["lon0"])*f["Mlon_m_per_deg"],
            -(b["north"]-f["lat0"])*f["Mlat_m_per_deg"],
            -(b["south"]-f["lat0"])*f["Mlat_m_per_deg"])


def _output_context(geometry,info,seed):
    frame=info["frame"]
    for name,value in (("source_area_id",info["area_id"]),
                       ("source_package_sha256",info["sha256"]),
                       ("generation_seed",int(seed)),
                       ("origin_lon",frame["lon0"]),("origin_lat",frame["lat0"]),
                       ("Mlon_m_per_deg",frame["Mlon_m_per_deg"]),
                       ("Mlat_m_per_deg",frame["Mlat_m_per_deg"])):
        _set_detail(geometry,name,value)


def _xy(primitive):
    points = [(float(v.point().position()[0]), float(v.point().position()[2]))
              for v in primitive.vertices()]
    if len(points) > 2 and math.dist(points[0], points[-1]) < 1e-5:
        points.pop()
    return points


def _signed_area(points):
    return 0.5*sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points, points[1:]+points[:1]))


def _centroid(points):
    twice = 2.0*_signed_area(points)
    if abs(twice) < 1e-9:
        return (sum(x for x,_ in points)/len(points), sum(z for _,z in points)/len(points))
    cx = sum((a[0]+b[0])*(a[0]*b[1]-b[0]*a[1]) for a,b in zip(points, points[1:]+points[:1]))/(3*twice)
    cz = sum((a[1]+b[1])*(a[0]*b[1]-b[0]*a[1]) for a,b in zip(points, points[1:]+points[:1]))/(3*twice)
    return cx,cz


def _point_in_polygon(point,polygon):
    x,z=point
    inside=False
    for (x0,z0),(x1,z1) in zip(polygon,polygon[1:]+polygon[:1]):
        if (z0>z)!=(z1>z) and x<(x1-x0)*(z-z0)/(z1-z0)+x0:
            inside=not inside
    return inside


def _dsm_local(info, x, z):
    frame = info["frame"]
    lon = frame["lon0"] + np.asarray(x, dtype=np.float64)/frame["Mlon_m_per_deg"]
    lat = frame["lat0"] - np.asarray(z, dtype=np.float64)/frame["Mlat_m_per_deg"]
    return sample_dsm(info, lon, lat)


def _stable_fraction(*values):
    key = "|".join(str(v) for v in values).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big") / 18446744073709551616.0


def _attr(geo, kind, name, default):
    find = {hou.attribType.Prim: geo.findPrimAttrib,
            hou.attribType.Point: geo.findPointAttrib,
            hou.attribType.Global: geo.findGlobalAttrib}[kind]
    return find(name) or geo.addAttrib(kind, name, default)


def _mesh_preview_material(node):
    path=str(node.parent().evalParm("mesh_preview_material")).strip()
    if not re.fullmatch(r"/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+",path):
        _fail("mesh_preview_material must be a native /Game/...Asset.Asset path")
    return path


def _add_polygon(geo, xyz, attr_values, attrs):
    polygon = geo.createPolygon()
    uv_attrib=geo.findPointAttrib("uv")
    normal_attrib=geo.findPointAttrib("N")
    positions=np.asarray(xyz,dtype=np.float64)
    # Points are private to each face. A face normal and a projection onto its
    # dominant plane provide a noncollapsed tangent basis on horizontal roads,
    # vertical pole/trunk faces, and sloped procedural canopies alike.
    # Houdini's polygon winding convention is opposite this raw cross sum.
    normal=-np.sum(np.cross(positions,np.roll(positions,-1,axis=0)),axis=0)
    magnitude=float(np.linalg.norm(normal))
    if magnitude<=1e-12:
        _fail("attempted to emit a zero-area polygon")
    normal/=magnitude
    dominant=int(np.argmax(np.abs(normal)))
    for position in xyz:
        point = geo.createPoint()
        point.setPosition(tuple(float(v) for v in position))
        if uv_attrib:
            x,y,z=position
            if dominant==1:
                u,v=x,(-z if normal[1]>=0 else z)
            elif dominant==2:
                u,v=x,(y if normal[2]>=0 else -y)
            else:
                u,v=y,(z if normal[0]>=0 else -z)
            point.setAttribValue(uv_attrib,(float(u)/4.0,float(v)/4.0,0.0))
        if normal_attrib:
            point.setAttribValue(normal_attrib,tuple(float(v) for v in normal))
        polygon.addVertex(point)
    for name,value in attr_values.items():
        polygon.setAttribValue(attrs[name], value)
    return polygon


def cook_road_eligibility(node):
    """Retain declared classes and replace Labs' string width with metres."""
    info = _package_for_sop(node)
    src, geo = node.inputs()[0].geometry(), node.geometry()
    geo.clear()
    attrs = {name:_attr(geo, hou.attribType.Prim, name, default) for name,default in
             (("source_osm_id",""),("source_area_id",""),("highway_class",""),
              ("route_role",""),("width",0.0),("width_rule",""))}
    count, omitted, invalid_width = {}, [], []
    scale = float(node.parent().evalParm("road_width_scale"))
    if scale <= 0 or scale > 4:
        _fail("road_width_scale must be in (0,4]")
    for primitive in src.prims():
        cls = str(primitive.attribValue("highway"))
        osm_id = str(primitive.attribValue("hou_id"))
        if cls not in ROAD_WIDTH_M:
            omitted.append(osm_id+":"+cls)
            continue
        coords = _xy(primitive)
        if len(coords) < 2:
            omitted.append(osm_id+":short")
            continue
        raw = str(primitive.attribValue("width")).strip() if src.findPrimAttrib("width") else ""
        match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(?:m|metres?)?\s*", raw, flags=re.I)
        if match and 0.5 <= float(match.group(1)) <= 35.0:
            width, rule = float(match.group(1))*scale, "osm_width_m"
        else:
            width, rule = ROAD_WIDTH_M[cls]*scale, "class_fallback"
            if raw:
                invalid_width.append(osm_id+":"+raw)
        line = geo.createPolygon(is_closed=False)
        for x,z in coords:
            point = geo.createPoint()
            point.setPosition((x,0.0,z))
            line.addVertex(point)
        values = {"source_osm_id":osm_id,"source_area_id":info["area_id"],
                  "highway_class":cls,"route_role":"road" if cls in ROAD_CLASSES else "footpath",
                  "width":width,"width_rule":rule}
        for name,value in values.items():
            line.setAttribValue(attrs[name], value)
        count[cls] = count.get(cls,0)+1
    _set_detail(geo,"road_class_counts_json",json.dumps(count,sort_keys=True))
    _set_detail(geo,"road_omitted_json",json.dumps(omitted,sort_keys=True))
    _set_detail(geo,"road_bad_width_json",json.dumps(invalid_width,sort_keys=True))
    _output_context(geo,info,node.parent().evalParm("seed"))


def _building_height(primitive, seed, area_m2):
    height_text = str(primitive.attribValue("height")) if primitive.geometry().findPrimAttrib("height") else ""
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(?:m|metres?)?\s*", height_text, flags=re.I)
    if match and 2.0 <= float(match.group(1)) <= 250.0:
        return float(match.group(1)), "osm_height_m"
    levels = (str(primitive.attribValue("building_levels")).strip()
              if primitive.geometry().findPrimAttrib("building_levels") else "")
    if re.fullmatch(r"\d+",levels) and 1 <= int(levels) <= 60:
        return float(int(levels)*3.2), "osm_levels_x_3.2m"
    kind = str(primitive.attribValue("building"))
    osm_id = str(primitive.attribValue("hou_id"))
    rnd = _stable_fraction(seed,osm_id,"height")
    if kind in ("commercial","public","mosque"):
        floors = 3+int(rnd*4)
    elif area_m2 > 450:
        floors = 3+int(rnd*4)
    else:
        floors = 2+int(rnd*4)
    return floors*3.2, "seeded_rule_not_measured"


def cook_building_pads(node):
    """Select centroid-in-area footprints and set deterministic flat pad elevations."""
    info = _package_for_sop(node)
    seed = int(node.parent().evalParm("seed"))
    src,geo = node.inputs()[0].geometry(),node.geometry()
    geo.clear()
    attrs = {name:_attr(geo,hou.attribType.Prim,name,default) for name,default in
             (("source_osm_id",""),("source_area_id",""),("building_class",""),
              ("height_m",0.0),("height_rule",""),("base_m",0.0),
              ("unreal_output_name",""),("unreal_material",""),
              ("Cd",(0.72,0.66,0.56)))}
    xmin,xmax,zmin,zmax = _local_box(info)
    keep,drop = [],[]
    candidates=[]
    for primitive in src.prims():
        osm_id = str(primitive.attribValue("hou_id"))
        coords = _xy(primitive)
        if len(coords)<3 or abs(_signed_area(coords))<1.0:
            drop.append(osm_id+":degenerate")
            continue
        cx,cz = _centroid(coords)
        if not (xmin <= cx <= xmax and zmin <= cz <= zmax):
            drop.append(osm_id+":centroid_outside")
            continue
        area_m2 = abs(_signed_area(coords))
        candidates.append((primitive,osm_id,coords,area_m2))
    # Labs may surface a small, untagged multipolygon inner as a building.
    # Geometric containment suppresses its duplicate shell; the outer hole
    # itself remains a recorded form limitation until a native boolean pass.
    accepted=[]
    for primitive,osm_id,coords,area_m2 in sorted(candidates,key=lambda item:-item[3]):
        explicit_height=(str(primitive.attribValue("height")).strip()
                         if src.findPrimAttrib("height") else "")
        explicit_levels=(str(primitive.attribValue("building_levels")).strip()
                         if src.findPrimAttrib("building_levels") else "")
        parent=next((outer_id for _,outer_id,outer,outer_area in accepted
                     if area_m2<0.25*outer_area and not explicit_height and not explicit_levels
                     and all(_point_in_polygon(v,outer) for v in coords)),None)
        if parent:
            drop.append(osm_id+":contained_small_polygon_in_"+parent)
            continue
        accepted.append((primitive,osm_id,coords,area_m2))
    for primitive,osm_id,coords,area_m2 in sorted(accepted,key=lambda item:item[1]):
        height,rule = _building_height(primitive,seed,area_m2)
        elevations = _dsm_local(info,[x for x,_ in coords],[z for _,z in coords])
        base = float(np.median(elevations))
        # Houdini's polygon normal is +Y for positive signed area in X/Z.
        if _signed_area(coords)<0:
            coords.reverse()
        attributes = {"source_osm_id":osm_id,"source_area_id":info["area_id"],
                      "building_class":str(primitive.attribValue("building")),
                      "height_m":height,"height_rule":rule,"base_m":base,
                      "unreal_output_name":info["area_id"]+"_buildings",
                      "unreal_material":_mesh_preview_material(node),
                      "Cd":(0.72,0.66,0.56)}
        _add_polygon(geo,[(x,base,z) for x,z in coords],attributes,attrs)
        keep.append(osm_id)
    _set_detail(geo,"building_kept_ids_json",json.dumps(sorted(keep)))
    _set_detail(geo,"building_dropped_json",json.dumps(sorted(drop)))
    _set_detail(geo,"seed",seed)
    _output_context(geo,info,seed)


def _grid_array(volume):
    return np.asarray(volume.allVoxels(),dtype=np.float32).reshape((GRID_SAMPLES,GRID_SAMPLES),order="F")


def _rasterize(primitives, value=255):
    image = Image.new("L",(GRID_SAMPLES,GRID_SAMPLES),0)
    draw = ImageDraw.Draw(image)
    for primitive in primitives:
        coords = _xy(primitive)
        if len(coords)>=3:
            draw.polygon([(x+2016.0,z+2016.0) for x,z in coords],fill=value)
    return np.asarray(image,dtype=np.float32)/255.0


def cook_city_terrain(node):
    """DSM heightfield with generated corridor/pad corrections and paint masks."""
    cook_terrain(node)
    info = _package_for_sop(node)
    geo = node.geometry()
    height = _volume(geo,"height")
    raw = _grid_array(height)
    roads = node.inputs()[1].geometry()
    pads = node.inputs()[2].geometry()
    road_mask = _rasterize(roads.prims())
    xmin,xmax,zmin,zmax=_local_box(info)
    axis=np.arange(GRID_SAMPLES,dtype=np.float32)-2016.0
    area_pixels=((axis[:,None]>=zmin)&(axis[:,None]<=zmax)&
                 (axis[None,:]>=xmin)&(axis[None,:]<=xmax))
    road_mask*=area_pixels
    pad_mask = _rasterize(pads.prims())
    # A conservative 3x3 smoothing removes DSM pixel steps only in roadbeds.
    padded = np.pad(raw,1,mode="edge")
    smoothed = sum(padded[a:a+GRID_SAMPLES,b:b+GRID_SAMPLES]
                   for a in range(3) for b in range(3))/9.0
    corrected = raw*(1.0-0.55*road_mask)+smoothed*(0.55*road_mask)
    base_image = Image.new("F",(GRID_SAMPLES,GRID_SAMPLES),0.0)
    base_draw = ImageDraw.Draw(base_image)
    for primitive in pads.prims():
        coords = _xy(primitive)
        if len(coords)>=3:
            base_draw.polygon([(x+2016.0,z+2016.0) for x,z in coords],fill=float(primitive.attribValue("base_m")))
    base_values = np.asarray(base_image,dtype=np.float32)
    corrected = np.where(pad_mask>0.5,base_values,corrected).astype(np.float32)
    height.setAllVoxels(corrected.flatten(order="F").tolist())
    dz,dx = np.gradient(corrected,GRID_SPACING_M,GRID_SPACING_M)
    degrees = np.degrees(np.arctan(np.hypot(dx,dz)))
    steep = np.clip((degrees-15.0)/20.0,0.0,1.0).astype(np.float32)
    ground = (1.0-steep).astype(np.float32)
    layer_data = (("Ground",ground,0),("Steep",steep,0),
                  ("RoadBed",road_mask,1),("BuildingPad",pad_mask,1))
    # Reuse the native mask volume; each added volume has exactly its transform.
    native_mask = _volume(geo,"mask")
    native_mask.setAttribValue("name","Ground")
    native_mask.setAllVoxels(ground.flatten(order="F").tolist())
    material_path=str(node.parent().evalParm("landscape_material")).strip()
    if not re.fullmatch(r"/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+",material_path):
        _fail("landscape_material must be a native /Game/...Asset.Asset path")
    bake_root=str(node.parent().evalParm("landscape_layerinfo_bake_root")).strip()
    if not re.fullmatch(r"/Game/[A-Za-z0-9_]+(?:/[A-Za-z0-9_]+)*",bake_root):
        _fail("landscape_layerinfo_bake_root must be a /Game/... content folder")
    if not re.fullmatch(r"[A-Za-z0-9_]+",info["area_id"]):
        _fail("area_id cannot form a safe Unreal LayerInfo bake folder")
    layerinfo_bake_folder=bake_root+"/"+info["area_id"]+"/LayerInfos"
    landscape_mode=int(node.parent().evalParm("landscape_output_mode"))
    if landscape_mode not in (0,1):
        _fail("landscape_output_mode must be 0 (generate) or 1 (update existing)")
    if landscape_mode == 1:
        edit_layer_name=str(node.parent().evalParm("landscape_update_edit_layer")).strip()
        if not re.fullmatch(r"[A-Za-z0-9_]+",edit_layer_name):
            _fail("landscape_update_edit_layer must be a simple existing Edit Layer name")
        output_mode_attr = _attr(geo,hou.attribType.Prim,"unreal_landscape_output_mode",0)
        edit_layer_attr = _attr(geo,hou.attribType.Prim,"unreal_landscape_editlayer_name","")
        clear_layer_attr = _attr(geo,hou.attribType.Prim,"unreal_landscape_editlayer_clear",0)
    name_attr = _attr(geo,hou.attribType.Prim,"name","")
    material = _attr(geo,hou.attribType.Prim,"unreal_material","")
    no_weight = _attr(geo,hou.attribType.Prim,"unreal_landscape_layer_noweightblend",0)
    out_name = _attr(geo,hou.attribType.Prim,"unreal_output_name","")
    bake_folder_attr = _attr(geo,hou.attribType.Prim,"unreal_bake_folder","")
    layer_min = _attr(geo,hou.attribType.Prim,"unreal_landscape_layer_min",0.0)
    layer_max = _attr(geo,hou.attribType.Prim,"unreal_landscape_layer_max",1.0)
    def set_landscape_routing(prim):
        prim.setAttribValue(out_name,info["area_id"]+"_landscape")
        prim.setAttribValue(material,material_path)
        prim.setAttribValue(bake_folder_attr,layerinfo_bake_folder)
        if landscape_mode == 1:
            prim.setAttribValue(output_mode_attr,1)
            prim.setAttribValue(edit_layer_attr,edit_layer_name)
            prim.setAttribValue(clear_layer_attr,1)
    for prim in (height,native_mask):
        set_landscape_routing(prim)
    height.setAttribValue(layer_min,-256.0)
    height.setAttribValue(layer_max,255.9921875)
    native_mask.setAttribValue(no_weight,0)
    native_mask.setAttribValue(layer_min,0.0)
    native_mask.setAttribValue(layer_max,1.0)
    for name,values,nonweight in layer_data[1:]:
        layer = geo.createVolume(GRID_SAMPLES,GRID_SAMPLES,1)
        layer.setTransform(hou.Matrix4(height.transform()) *
                           hou.hmath.buildTranslate(height.vertex(0).point().position()))
        layer.setAttribValue(name_attr,name)
        layer.setAllVoxels(values.flatten(order="F").tolist())
        layer.setAttribValue(no_weight,nonweight)
        layer.setAttribValue(layer_min,0.0)
        layer.setAttribValue(layer_max,1.0)
        set_landscape_routing(layer)
    _set_detail(geo,"landscape_layerinfo_bake_folder",layerinfo_bake_folder)
    _set_detail(geo,"unreal_landscape_layer_nonweightblended","RoadBed BuildingPad")
    _set_detail(geo,"terrain_correction","DSM; road 3x3 smoothing at 0.55; flat building pads")
    _set_detail(geo,"raw_min_m",float(raw.min()))
    _set_detail(geo,"raw_max_m",float(raw.max()))
    _set_detail(geo,"corrected_min_m",float(corrected.min()))
    _set_detail(geo,"corrected_max_m",float(corrected.max()))
    _set_detail(geo,"roadbed_pixels",int(np.count_nonzero(road_mask)))
    _set_detail(geo,"buildingpad_pixels",int(np.count_nonzero(pad_mask)))
    _output_context(geo,info,node.parent().evalParm("seed"))


def _sample_grid(array,x,z):
    u = np.clip(np.asarray(x,dtype=np.float64)+2016.0,0,GRID_SAMPLES-1)
    v = np.clip(np.asarray(z,dtype=np.float64)+2016.0,0,GRID_SAMPLES-1)
    i = np.minimum(np.floor(u).astype(np.int64),GRID_SAMPLES-2)
    j = np.minimum(np.floor(v).astype(np.int64),GRID_SAMPLES-2)
    fu,fv = u-i,v-j
    return ((1-fu)*(1-fv)*array[j,i]+fu*(1-fv)*array[j,i+1]+
            (1-fu)*fv*array[j+1,i]+fu*fv*array[j+1,i+1])


def _clip_polygon(points,box):
    xmin,xmax,zmin,zmax = box
    polygon = list(points)
    for axis,limit,greater in ((0,xmin,True),(0,xmax,False),(1,zmin,True),(1,zmax,False)):
        if not polygon:
            break
        result=[]
        prev=polygon[-1]
        prev_inside=(prev[axis]>=limit) if greater else (prev[axis]<=limit)
        for current in polygon:
            curr_inside=(current[axis]>=limit) if greater else (current[axis]<=limit)
            if curr_inside != prev_inside:
                denominator=current[axis]-prev[axis]
                t=(limit-prev[axis])/denominator if abs(denominator)>1e-12 else 0.0
                result.append((prev[0]+t*(current[0]-prev[0]),prev[1]+t*(current[1]-prev[1])))
            if curr_inside:
                result.append(current)
            prev,prev_inside=current,curr_inside
        polygon=result
    clean=[]
    for point in polygon:
        if not clean or math.dist(point,clean[-1])>1e-4:
            clean.append(point)
    if len(clean)>2 and math.dist(clean[0],clean[-1])<1e-4:
        clean.pop()
    return clean if len(clean)>=3 and abs(_signed_area(clean))>1e-4 else []


def _condition_surface_polygon(coords):
    """Remove clipped slivers/collinear vertices and orient a ground face up."""
    coords=list(coords)
    if len(coords)<3:
        return []
    # Clipping can insert vertices on the same edge. Those can leave a
    # zero-UV-area triangle when Unreal triangulates an otherwise valid face.
    changed=True
    while changed and len(coords)>3:
        changed=False
        for index in range(len(coords)):
            a,b,c=coords[index-1],coords[index],coords[(index+1)%len(coords)]
            ab=(b[0]-a[0],b[1]-a[1])
            bc=(c[0]-b[0],c[1]-b[1])
            cross=abs(ab[0]*bc[1]-ab[1]*bc[0])
            if cross<=1e-6*max(math.hypot(*ab),math.hypot(*bc),1.0):
                del coords[index]
                changed=True
                break
    if len(coords)<3 or abs(_signed_area(coords))<1e-3:
        return []
    if _signed_area(coords)<0:
        coords.reverse()
    # Avoid starting an n-gon fan at a vertex collinear with a nonadjacent edge.
    if len(coords)>3:
        def minimum_fan_area(values):
            a=values[0]
            return min(abs((values[i][0]-a[0])*(values[i+1][1]-a[1])-
                           (values[i][1]-a[1])*(values[i+1][0]-a[0]))/2
                       for i in range(1,len(values)-1))
        coords=max((coords[i:]+coords[:i] for i in range(len(coords))),
                   key=minimum_fan_area)
        if minimum_fan_area(coords)<1e-6:
            return []
    return coords


def _source_segments(source):
    starts,ends,features=[],[],[]
    for primitive in source.prims():
        coords=_xy(primitive)
        for a,b in zip(coords,coords[1:]):
            if math.dist(a,b)>1e-4:
                starts.append(a)
                ends.append(b)
                features.append((str(primitive.attribValue("source_osm_id")),
                                 str(primitive.attribValue("highway_class")),
                                 float(primitive.attribValue("width"))))
    if not starts:
        _fail("road source has no valid segments")
    return np.asarray(starts,dtype=np.float64),np.asarray(ends,dtype=np.float64),features


def _nearest_segment(point,segments):
    starts,ends,features=segments
    delta=ends-starts
    numerator=np.sum((np.asarray(point)-starts)*delta,axis=1)
    denom=np.sum(delta*delta,axis=1)
    fraction=np.clip(numerator/np.maximum(denom,1e-12),0.0,1.0)
    close=starts+fraction[:,None]*delta
    d2=np.sum((close-np.asarray(point))**2,axis=1)
    idx=int(np.argmin(d2))
    return features[idx],close[idx],float(math.sqrt(d2[idx]))


import math
import heapq
import numpy as np

_lineage_cache = None

def _indexed_lineage_rank(point, segments):
    """Exact nearest two distinct source IDs; grid boxes prune distant segments."""
    global _lineage_cache
    if _lineage_cache is None or _lineage_cache['segments'] is not segments:
        starts, ends, features = segments
        delta = ends - starts
        denom = np.maximum(np.sum(delta * delta, axis=1), 1e-12)
        cell = 32.0
        bins = {}
        for i, (a, b) in enumerate(zip(starts, ends)):
            lo = np.floor(np.minimum(a, b) / cell).astype(np.int64)
            hi = np.floor(np.maximum(a, b) / cell).astype(np.int64)
            for x in range(int(lo[0]), int(hi[0]) + 1):
                for z in range(int(lo[1]), int(hi[1]) + 1):
                    bins.setdefault((x,z), []).append(i)
        assert bins, 'road source has no valid segments'
        _lineage_cache = {'segments':segments, 'delta':delta, 'denom':denom,
                          'bins':bins, 'cell':cell,
                          'bounds':(min(x for x,z in bins), max(x for x,z in bins),
                                    min(z for x,z in bins), max(z for x,z in bins))}
    cached = _lineage_cache
    starts, ends, features = segments
    cell, bins = cached['cell'], cached['bins']
    p = np.asarray(point, dtype=np.float64)
    cx, cz = (int(math.floor(float(v)/cell)) for v in p)
    bx0, bx1, bz0, bz1 = cached['bounds']
    seen = set()
    by_id = {}
    radius = 0
    previous_radius = -1
    while True:
        fresh = set()
        for x in range(max(cx-radius,bx0), min(cx+radius,bx1)+1):
            for z in range(max(cz-radius,bz0), min(cz+radius,bz1)+1):
                if previous_radius >= 0 and abs(x-cx) <= previous_radius and abs(z-cz) <= previous_radius:
                    continue
                fresh.update(bins.get((x,z), ()))
        fresh.difference_update(seen)
        if fresh:
            indices = np.asarray(sorted(fresh), dtype=np.int64)
            selected_starts = starts[indices]
            selected_delta = cached['delta'][indices]
            fraction = np.clip(np.sum((p-selected_starts)*selected_delta,axis=1)/cached['denom'][indices],0.0,1.0)
            close = selected_starts + fraction[:,None]*selected_delta
            distances = np.sqrt(np.sum((close-p)**2,axis=1))
            for i, distance in zip(indices,distances):
                osm_id, cls, width = features[int(i)]
                # Original source order decides equal-distance segments of one ID.
                candidate = (float(distance), int(i), osm_id, cls, width)
                if osm_id not in by_id or candidate[:2] < by_id[osm_id][:2]:
                    by_id[osm_id] = candidate
            seen.update(fresh)
        ranked = heapq.nsmallest(2, [(d,osm_id,cls,width) for d,i,osm_id,cls,width in by_id.values()])
        complete = cx-radius <= bx0 and cx+radius >= bx1 and cz-radius <= bz0 and cz+radius >= bz1
        # An unseen segment cannot touch the searched square: its bounding box
        # was registered in every intersected cell. Strict inequality retains ties.
        lower_bound = min(float(p[0])-(cx-radius)*cell, (cx+radius+1)*cell-float(p[0]),
                          float(p[1])-(cz-radius)*cell, (cz+radius+1)*cell-float(p[1]))
        if complete or (len(ranked) >= 2 and ranked[1][0] < lower_bound):
            return ranked
        previous_radius = radius
        radius = 1 if radius == 0 else radius*2


def _lineage(point,segments):
    """A spatial hint only: Labs Road Generator removes way IDs at junctions."""
    ranked=_indexed_lineage_rank(point,segments)
    best=ranked[0]
    second=ranked[1] if len(ranked)>1 else None
    radius=max(best[3]/2+3.0,6.0)
    if best[0]>radius:
        status="unassigned_far_from_centerline"
        authoritative=""
    elif second and second[0]-best[0]<0.75 and second[0]<radius:
        status="ambiguous_near_junction"
        authoritative=""
    else:
        status="nearest_centerline_inferred"
        authoritative=best[1]
    return best,authoritative,status,[item[1] for item in ranked[:2]]


def _surface_attrs(geo):
    _attr(geo,hou.attribType.Point,"uv",(0.0,0.0,0.0))
    _attr(geo,hou.attribType.Point,"N",(0.0,1.0,0.0))
    return {name:_attr(geo,hou.attribType.Prim,name,default) for name,default in
            (("source_osm_id",""),("nearest_osm_id",""),("source_id_status",""),
             ("source_ids_json",""),("nearest_distance_m",0.0),
             ("source_area_id",""),("highway_class",""),
             ("route_role",""),("width_m",0.0),("unreal_output_name",""),
             ("unreal_material",""),
             ("Cd",(0.22,0.22,0.22)))}


def cook_labs_road_half_width(node):
    """Labs 1.2 offsets P by width on each side; source width is full metres."""
    geo=node.geometry();geo.clear();geo.merge(node.inputs()[0].geometry())
    width=geo.findPrimAttrib('width')
    if width is None:_fail('Labs width adapter requires eligible numeric full widths')
    for primitive in geo.prims():
        primitive.setAttribValue(width,float(primitive.attribValue(width))/2.0)
    _set_detail(geo,'labs_width_contract','eligible_full_width_m_divided_by_two_for_each_side')


def cook_complete_road_coverage(node):
    """Keep Labs coverage; complete width-derived joins/caps without overlaps."""
    parent,geo=node.parent(),node.geometry()
    info=_package_for_sop(parent);box=_local_box(info)
    geo.clear()
    triangulated=hou.Geometry()
    divide=hou.sopNodeTypeCategory().nodeVerb('divide')
    divide.setParms({'convex':1,'usemaxsides':1,'numsides':3,'fixsharededges':1})
    divide.execute(triangulated,[node.inputs()[0].geometry()])
    index=([],{})
    counts={'labs_triangles':0,'labs_union_fragments':0,'supplement_fragments':0,
            'caps':0,'corridors':0,'labs_area_m2':0.0,'supplement_area_m2':0.0}
    def retain(polygon,lane):
        polygon=_condition_surface_polygon(_clip_polygon(polygon,box))
        if not polygon:return
        for fragment in _permanent_sidewalk_without_roads(polygon,index):
            for indices in _triangles(fragment):
                triangle=[fragment[i] for i in indices]
                if abs(_signed_area(triangle))<1e-3:continue
                _add_polygon(geo,[(x,0.0,z) for x,z in triangle],{}, {})
                number=len(index[0])
                bounds=(min(p[0] for p in triangle),max(p[0] for p in triangle),
                        min(p[1] for p in triangle),max(p[1] for p in triangle))
                index[0].append((triangle,bounds))
                for iz in range(math.floor(bounds[2]/4),math.floor(bounds[3]/4)+1):
                    for ix in range(math.floor(bounds[0]/4),math.floor(bounds[1]/4)+1):
                        index[1].setdefault((ix,iz),set()).add(number)
                counts[lane+'_fragments']+=1
                counts['labs_area_m2' if lane=='labs_union' else 'supplement_area_m2']+=abs(_signed_area(triangle))
    for primitive in triangulated.prims():
        ring=_xy(primitive)
        if len(ring)<3:continue
        counts['labs_triangles']+=1
        retain(ring,'labs_union')
    starts,ends,features=_source_segments(node.inputs()[1].geometry())
    caps=set()
    for a,b,(_,_,width) in zip(starts,ends,features):
        radius=width/2.0;direction=b-a
        perpendicular=np.asarray((-direction[1],direction[0]))/float(np.linalg.norm(direction))*radius
        retain([tuple(a+perpendicular),tuple(a-perpendicular),tuple(b-perpendicular),tuple(b+perpendicular)],'supplement')
        counts['corridors']+=1
        for point in (a,b):
            key=(round(float(point[0]),4),round(float(point[1]),4),round(radius,4))
            if key in caps:continue
            caps.add(key)
            # Circumscription covers the declared width without a polygonal cap gap.
            cap_radius=radius/math.cos(math.pi/32.0)
            retain([(float(point[0])+cap_radius*math.cos(angle),float(point[1])+cap_radius*math.sin(angle))
                    for angle in np.linspace(0,2*math.pi,32,endpoint=False)],'supplement')
            counts['caps']+=1
    if not geo.prims():_fail('Complete geographic road coverage is empty')
    counts.update(policy='preserved_Labs_union_plus_missing_eligible_width_corridors_joins_caps',
                  source_area_id=info['area_id'],shared_consumers=['RoadBed','road_surfaces','sidewalks'])
    _set_detail(geo,'geographic_road_coverage_json',json.dumps(counts,sort_keys=True))
    _output_context(geo,info,parent.evalParm('seed'))


def cook_road_surfaces(node):
    info=_package_for_sop(node)
    source=node.inputs()[1].geometry()
    segments=_source_segments(source)
    terrain=_grid_array(_volume(node.inputs()[2].geometry(),"height"))
    raw=node.inputs()[0].geometry()
    geo=node.geometry()
    geo.clear()
    attrs=_surface_attrs(geo)
    box=_local_box(info)
    ids=set()
    status_counts={}
    rejected=0
    for primitive in raw.prims():
        coords=_condition_surface_polygon(_clip_polygon(_xy(primitive),box))
        if not coords:
            rejected+=1
            continue
        # Labs can emit non-simple junction polygons; their area centroid may
        # lie arbitrarily far away. The vertex mean stays inside the clip box.
        midpoint=(sum(x for x,_ in coords)/len(coords),sum(z for _,z in coords)/len(coords))
        (distance,nearest_id,cls,width),osm_id,status,candidates=_lineage(midpoint,segments)
        elevations=_sample_grid(terrain,[x for x,_ in coords],[z for _,z in coords])
        role="road" if cls in ROAD_CLASSES else "footpath"
        color=(0.18,0.18,0.19) if role=="road" else (0.46,0.43,0.38)
        values={"source_osm_id":osm_id,"nearest_osm_id":nearest_id,
                "source_id_status":status,"source_ids_json":json.dumps(candidates),
                "nearest_distance_m":distance,"source_area_id":info["area_id"],
                "highway_class":cls,"route_role":role,"width_m":width,
                "unreal_output_name":info["area_id"]+"_road_surfaces",
                "unreal_material":_mesh_preview_material(node),"Cd":color}
        _add_polygon(geo,[(x,float(y)+0.08,z) for (x,z),y in zip(coords,elevations)],values,attrs)
        if osm_id:
            ids.add(osm_id)
        status_counts[status]=status_counts.get(status,0)+1
    _output_context(geo,info,node.parent().evalParm("seed"))
    _set_detail(geo,"represented_road_ids_json",json.dumps(sorted(ids)))
    _set_detail(geo,"lineage_status_counts_json",json.dumps(status_counts,sort_keys=True))
    _set_detail(geo,"discarded_degenerate_faces",rejected)
    _set_detail(geo,"unreal_output_name",info["area_id"]+"_road_surfaces")


def _permanent_exterior_road_edges(raw):
    """Split crossing/overlapping edges before classifying the road union side."""
    edges={}
    rings=[]
    cells={}
    def key(point):return tuple(round(value,4) for value in point)
    for primitive in raw.prims():
        ring=_xy(primitive)
        if len(ring)<3:continue
        rings.append((primitive.number(),ring))
        for iz in range(math.floor(min(p[1] for p in ring)/4),math.floor(max(p[1] for p in ring)/4)+1):
            for ix in range(math.floor(min(p[0] for p in ring)/4),math.floor(max(p[0] for p in ring)/4)+1):
                cells.setdefault((ix,iz),[]).append((primitive.number(),ring))
        for a,b in zip(ring,ring[1:]+ring[:1]):
            if math.dist(a,b)<0.01:continue
            edge_key=tuple(sorted((key(a),key(b))))
            edges.setdefault(edge_key,[]).append((primitive.number(),a,b))
    output={}
    for owners in edges.values():
        number,a,b=owners[0]
        length=math.dist(a,b)
        nx,nz=-(b[1]-a[1])/length,(b[0]-a[0])/length
        candidates={}
        for iz in range(math.floor(min(a[1],b[1])/4),math.floor(max(a[1],b[1])/4)+1):
            for ix in range(math.floor(min(a[0],b[0])/4),math.floor(max(a[0],b[0])/4)+1):
                for owner,ring in cells.get((ix,iz),[]):candidates[owner]=ring
        cuts={0.0,1.0}
        dx,dz=b[0]-a[0],b[1]-a[1]
        def cross(u,v):return u[0]*v[1]-u[1]*v[0]
        for ring in candidates.values():
            for c,d in zip(ring,ring[1:]+ring[:1]):
                edge=(d[0]-c[0],d[1]-c[1]);delta=(c[0]-a[0],c[1]-a[1])
                denominator=cross((dx,dz),edge)
                if abs(denominator)>1e-10:
                    t=cross(delta,edge)/denominator;u=cross(delta,(dx,dz))/denominator
                    if -1e-8<=t<=1+1e-8 and -1e-8<=u<=1+1e-8:
                        cuts.add(round(max(0.0,min(1.0,t)),10))
                elif abs(cross(delta,(dx,dz)))<1e-7*length:
                    for point in (c,d):
                        t=((point[0]-a[0])*dx+(point[1]-a[1])*dz)/(length*length)
                        if 0<t<1:cuts.add(round(t,10))
        cuts=sorted(cuts)
        for low,high in zip(cuts,cuts[1:]):
            if (high-low)*length<0.01:continue
            start=(a[0]+low*dx,a[1]+low*dz);end=(a[0]+high*dx,a[1]+high*dz)
            midpoint=((start[0]+end[0])*0.5,(start[1]+end[1])*0.5)
            covered=[]
            for side in (-1,1):
                sample=(midpoint[0]+side*nx*0.02,midpoint[1]+side*nz*0.02)
                local=cells.get((math.floor(sample[0]/4),math.floor(sample[1]/4)),[])
                covered.append(any(_permanent_point_strictly_inside(sample,ring) for _,ring in local))
            if covered[0]==covered[1]:continue
            # The outside follows union coverage, not the nearest source center.
            outside=1.0 if covered[0] else -1.0
            output.setdefault(number,[]).append((start,end,outside))
    return output


def _permanent_point_strictly_inside(point,ring):
    x,z=point;inside=False
    for a,b in zip(ring,ring[1:]+ring[:1]):
        dx,dz=b[0]-a[0],b[1]-a[1]
        length2=dx*dx+dz*dz
        t=max(0.0,min(1.0,((x-a[0])*dx+(z-a[1])*dz)/length2)) if length2 else 0.0
        if math.hypot(x-a[0]-t*dx,z-a[1]-t*dz)<1e-4:return False
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return inside


def _permanent_road_triangle_index(raw):
    triangles=[];cells={}
    for primitive in raw.prims():
        ring=_condition_surface_polygon(_xy(primitive))
        if not ring:continue
        for indices in _triangles(ring):
            triangle=[ring[i] for i in indices]
            bounds=(min(p[0] for p in triangle),max(p[0] for p in triangle),
                    min(p[1] for p in triangle),max(p[1] for p in triangle))
            number=len(triangles);triangles.append((triangle,bounds))
            for iz in range(math.floor(bounds[2]/4),math.floor(bounds[3]/4)+1):
                for ix in range(math.floor(bounds[0]/4),math.floor(bounds[1]/4)+1):
                    cells.setdefault((ix,iz),set()).add(number)
    return triangles,cells


def _permanent_halfplane(ring,a,b,inside):
    if not ring:return []
    def distance(p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
    def keep(value):return value>=0 if inside else value<=0
    result=[];prior=ring[-1];prior_distance=distance(prior)
    for current in ring:
        current_distance=distance(current)
        if keep(prior_distance)!=keep(current_distance):
            fraction=prior_distance/(prior_distance-current_distance)
            result.append((prior[0]+fraction*(current[0]-prior[0]),
                           prior[1]+fraction*(current[1]-prior[1])))
        if keep(current_distance):result.append(current)
        prior,prior_distance=current,current_distance
    return _condition_surface_polygon(result)


def _permanent_sidewalk_without_roads(coords,index):
    """Subtract full road coverage while retaining every disjoint ribbon fragment."""
    triangles,cells=index
    bounds=(min(p[0] for p in coords),max(p[0] for p in coords),
            min(p[1] for p in coords),max(p[1] for p in coords))
    candidates=set()
    for iz in range(math.floor(bounds[2]/4),math.floor(bounds[3]/4)+1):
        for ix in range(math.floor(bounds[0]/4),math.floor(bounds[1]/4)+1):
            candidates.update(cells.get((ix,iz),()))
    fragments=[coords]
    for number in sorted(candidates):
        triangle,box=triangles[number]
        if box[1]<=bounds[0] or box[0]>=bounds[1] or box[3]<=bounds[2] or box[2]>=bounds[3]:continue
        surviving=[]
        for fragment in fragments:
            fragment_box=(min(p[0] for p in fragment),max(p[0] for p in fragment),
                          min(p[1] for p in fragment),max(p[1] for p in fragment))
            if (box[1]<=fragment_box[0] or box[0]>=fragment_box[1] or
                    box[3]<=fragment_box[2] or box[2]>=fragment_box[3]):
                surviving.append(fragment)
                continue
            intersection=fragment
            for a,b in zip(triangle,triangle[1:]+triangle[:1]):
                intersection=_permanent_halfplane(intersection,a,b,True)
                if not intersection:break
            if not intersection:
                surviving.append(fragment)
                continue
            remaining=fragment
            for a,b in zip(triangle,triangle[1:]+triangle[:1]):
                outside=_permanent_halfplane(remaining,a,b,False)
                if outside:surviving.append(outside)
                remaining=_permanent_halfplane(remaining,a,b,True)
                if not remaining:break
            # The final remaining portion lies within the road triangle.
        fragments=surviving
        if not fragments:break
    return fragments


def cook_sidewalks(node):
    info=_package_for_sop(node)
    segments=_source_segments(node.inputs()[1].geometry())
    terrain=_grid_array(_volume(node.inputs()[2].geometry(),"height"))
    raw=node.inputs()[0].geometry()
    boundary_edges=_permanent_exterior_road_edges(raw)
    road_index=_permanent_road_triangle_index(raw)
    geo=node.geometry()
    geo.clear()
    attrs=_surface_attrs(geo)
    box=_local_box(info)
    ids=set()
    status_counts={}
    rejected=0
    for primitive in raw.prims():
        line=_xy(primitive)
        for a,b,side in boundary_edges.get(primitive.number(),[]):
            if math.dist(a,b)<0.01:
                continue
            midpoint=((a[0]+b[0])*0.5,(a[1]+b[1])*0.5)
            (distance,nearest_id,cls,width),osm_id,status,candidates=_lineage(midpoint,segments)
            edge=np.asarray((b[0]-a[0],b[1]-a[1]),dtype=np.float64)
            perpendicular=np.asarray((-edge[1],edge[0]))/float(np.linalg.norm(edge))
            offset=perpendicular*side*1.5
            coords=_condition_surface_polygon(_clip_polygon(
                [a,b,(b[0]+offset[0],b[1]+offset[1]),
                 (a[0]+offset[0],a[1]+offset[1])],box))
            if not coords:
                rejected+=1
                continue
            values={"source_osm_id":osm_id,"nearest_osm_id":nearest_id,
                    "source_id_status":status,"source_ids_json":json.dumps(candidates),
                    "nearest_distance_m":distance,"source_area_id":info["area_id"],
                    "highway_class":cls,"route_role":"sidewalk","width_m":1.5,
                    "unreal_output_name":info["area_id"]+"_sidewalks",
                    "unreal_material":_mesh_preview_material(node),
                    "Cd":(0.51,0.49,0.44)}
            for fragment in _permanent_sidewalk_without_roads(coords,road_index):
                elevations=_sample_grid(terrain,[x for x,_ in fragment],[z for _,z in fragment])
                _add_polygon(geo,[(x,float(y)+0.16,z) for (x,z),y in zip(fragment,elevations)],values,attrs)
                if osm_id:ids.add(osm_id)
                status_counts[status]=status_counts.get(status,0)+1
    _output_context(geo,info,node.parent().evalParm("seed"))
    _set_detail(geo,"represented_road_ids_json",json.dumps(sorted(ids)))
    _set_detail(geo,"lineage_status_counts_json",json.dumps(status_counts,sort_keys=True))
    _set_detail(geo,"discarded_degenerate_faces",rejected)
    _set_detail(geo,"unreal_output_name",info["area_id"]+"_sidewalks")


def _make_box(geo,center,size,values,attrs):
    cx,cy,cz=center
    sx,sy,sz=size
    x0,x1=cx-sx/2,cx+sx/2
    y0,y1=cy-sy/2,cy+sy/2
    z0,z1=cz-sz/2,cz+sz/2
    vertices=((x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1),
              (x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1))
    for indices in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
        _add_polygon(geo,[vertices[i] for i in indices],values,attrs)


def _make_canopy(geo,x,base,z,radius,height,values,attrs):
    rim=[(x+radius*math.cos(k*math.pi/3),base,z+radius*math.sin(k*math.pi/3)) for k in range(6)]
    apex=(x,base+height,z)
    for k in range(6):
        _add_polygon(geo,[rim[k],rim[(k+1)%6],apex],values,attrs)


def _detail_attrs(geo):
    _attr(geo,hou.attribType.Point,"uv",(0.0,0.0,0.0))
    _attr(geo,hou.attribType.Point,"N",(0.0,1.0,0.0))
    return {name:_attr(geo,hou.attribType.Prim,name,default) for name,default in
            (("detail_id",""),("source_area_id",""),("source_osm_id",""),
             ("detail_kind",""),("unreal_output_name",""),
             ("unreal_material",""),("Cd",(0.0,0.0,0.0)))}


def _exclusion_mask(terrain,layer,radius_px):
    values=np.clip(_grid_array(_volume(terrain,layer))*255.0,0,255).astype(np.uint8)
    image=Image.fromarray(values,mode="L")
    size=2*int(radius_px)+1
    if size>1:
        image=image.filter(ImageFilter.MaxFilter(size))
    return np.asarray(image,dtype=np.uint8)


def cook_vegetation(node):
    """Seeded low-poly tree blockouts on measured ground, excluding generated pads."""
    info=_package_for_sop(node)
    seed=int(node.parent().evalParm("seed"))
    spacing=float(node.parent().evalParm("vegetation_spacing_m"))
    if spacing<8.0 or spacing>80.0:
        _fail("vegetation_spacing_m must be 8..80")
    terrain_geo=node.inputs()[0].geometry()
    height=_grid_array(_volume(terrain_geo,"height"))
    roads=_exclusion_mask(terrain_geo,"RoadBed",5)
    pads=_exclusion_mask(terrain_geo,"BuildingPad",5)
    steep=_grid_array(_volume(terrain_geo,"Steep"))
    xmin,xmax,zmin,zmax=_local_box(info)
    geo=node.geometry()
    geo.clear()
    attrs=_detail_attrs(geo)
    placed=[]
    # Karmei Yosef 4 km v001 (Aviv 2026-10-08): no generated placeholder tree
    # blockouts; vegetation comes from the Unreal PCG tool.
    ix0,ix1=0,0
    iz0,iz1=0,0
    for iz in range(iz0,iz1):
        for ix in range(ix0,ix1):
            if _stable_fraction(info["area_id"],seed,ix,iz,"keep")>0.55:
                continue
            x=(ix+0.5+0.6*(_stable_fraction(seed,ix,iz,"x")-0.5))*spacing
            z=(iz+0.5+0.6*(_stable_fraction(seed,ix,iz,"z")-0.5))*spacing
            if not (xmin+2<x<xmax-2 and zmin+2<z<zmax-2):
                continue
            row,col=int(round(z+2016)),int(round(x+2016))
            if roads[row,col]>0 or pads[row,col]>0 or steep[row,col]>0.3:
                continue
            y=float(_sample_grid(height,[x],[z])[0])
            growth=_stable_fraction(seed,ix,iz,"scale")
            trunk_h=2.1+1.0*growth
            crown_h=2.4+0.9*growth
            radius=1.2+0.3*growth
            detail_id="tree_%d_%d"%(ix,iz)
            common={"detail_id":detail_id,"source_area_id":info["area_id"],
                    "source_osm_id":"","detail_kind":"procedural_tree_blockout",
                    "unreal_output_name":info["area_id"]+"_vegetation",
                    "unreal_material":_mesh_preview_material(node)}
            _make_box(geo,(x,y+trunk_h*0.5,z),(0.28,trunk_h,0.28),
                      dict(common,Cd=(0.35,0.23,0.13)),attrs)
            _make_canopy(geo,x,y+trunk_h-0.3,z,radius,crown_h,
                         dict(common,Cd=(0.18,0.36,0.16)),attrs)
            placed.append(detail_id)
    _output_context(geo,info,seed)
    _set_detail(geo,"detail_ids_json",json.dumps(placed))
    _set_detail(geo,"unreal_output_name",info["area_id"]+"_vegetation")


def cook_street_details(node):
    """Small procedural street poles placed beside known road source segments."""
    info=_package_for_sop(node)
    seed=int(node.parent().evalParm("seed"))
    terrain_geo=node.inputs()[0].geometry()
    height=_grid_array(_volume(terrain_geo,"height"))
    road_mask=_exclusion_mask(terrain_geo,"RoadBed",1)
    pad_mask=_exclusion_mask(terrain_geo,"BuildingPad",2)
    source=node.inputs()[1].geometry()
    geo=node.geometry()
    geo.clear()
    attrs=_detail_attrs(geo)
    box=_local_box(info)
    placed=[]
    for primitive in source.prims():
        if str(primitive.attribValue("route_role"))!="road":
            continue
        coords=_xy(primitive)
        osm_id=str(primitive.attribValue("source_osm_id"))
        width=float(primitive.attribValue("width"))
        accumulated=0.0
        for seg_idx,(a,b) in enumerate(zip(coords,coords[1:])):
            length=math.dist(a,b)
            if length<1.0:
                continue
            count=max(0,int((accumulated+length)//35)-int(accumulated//35))
            for n in range(count):
                station=(int(accumulated//35)+n+1)*35.0-accumulated
                t=station/length
                center=(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]))
                side=1 if _stable_fraction(seed,osm_id,seg_idx,n,"side")>=0.5 else -1
                perp=np.asarray((-(b[1]-a[1]),b[0]-a[0]))/length
                x,z=np.asarray(center)+side*(width/2+2.0)*perp
                if not (box[0]+1<x<box[1]-1 and box[2]+1<z<box[3]-1):
                    continue
                row,col=int(round(z+2016)),int(round(x+2016))
                if pad_mask[row,col]>0 or road_mask[row,col]>0:
                    continue
                y=float(_sample_grid(height,[x],[z])[0])
                detail_id="pole_%s_%d_%d"%(osm_id,seg_idx,n)
                common={"detail_id":detail_id,"source_area_id":info["area_id"],
                        "source_osm_id":osm_id,"detail_kind":"procedural_street_pole",
                        "unreal_output_name":info["area_id"]+"_street_details",
                        "unreal_material":_mesh_preview_material(node)}
                _make_box(geo,(x,y+1.6,z),(0.18,3.2,0.18),
                          dict(common,Cd=(0.18,0.18,0.19)),attrs)
                _make_box(geo,(x,y+3.15,z),(0.65,0.16,0.45),
                          dict(common,Cd=(0.9,0.78,0.48)),attrs)
                placed.append(detail_id)
            accumulated+=length
    _output_context(geo,info,seed)
    _set_detail(geo,"detail_ids_json",json.dumps(placed))
    _set_detail(geo,"unreal_output_name",info["area_id"]+"_street_details")


def cook_city_controls(node):
    cook_controls(node)
    geo=node.geometry()
    terrain=_grid_array(_volume(node.inputs()[1].geometry(),"height"))
    for point in geo.points():
        x,_,z=point.position()
        point.setPosition((x,float(_sample_grid(terrain,[x],[z])[0]),z))
    info=_package_for_sop(node)
    _output_context(geo,info,node.parent().evalParm("seed"))
    _set_detail(geo,"unreal_output_name",info["area_id"]+"_controls")


"""Embedded GeoCity bank interface. DataTable is the catalog runtime authority.

Placement requests use Houdini metres/Y-up. Bounds and anchors in the table use
Unreal centimetres/Z-up. The separately authorized direct-picker pilot emits
one geographic pole without a catalog release. No source mesh is copied into
Houdini.
"""
BANK_FIELDS = ('SchemaVersion AssetId ObjectPath Role VariantId RunEligible '
               'BoundsValid BoundsMinXCm BoundsMinYCm BoundsMinZCm BoundsMaxXCm '
               'BoundsMaxYCm BoundsMaxZCm AnchorValid AnchorZCm OrientationValid '
               'ForwardAxis AssetRevision').split()
BANK_V2_EXTRA_FIELDS = ('FamilyId StyleSet SelectionWeight PlacementScope '
                        'AllowedAreas AllowedZones AllowedPlacementIds ReleaseId '
                        'DecisionId').split()
BANK_V2_FIELDS = BANK_FIELDS + BANK_V2_EXTRA_FIELDS
BANK_V2_SCOPES = {'none', 'exact_ids', 'area_zone'}
BANK_V2_TOKEN = re.compile(r'[A-Za-z0-9_.:-]+')
BANK_NUMBERS = [x for x in BANK_FIELDS if x.endswith('Cm')]
BANK_FLAGS = ['RunEligible', 'BoundsValid', 'AnchorValid', 'OrientationValid']
BANK_TECH_ONLY = {'H0013', 'H0907', 'H0051', 'H0958'}
BANK_TECH_ONLY_TOKEN = re.compile(
    r'(?<![A-Za-z0-9])(?:H0013|H0907|H0051|H0958)(?![A-Za-z0-9])', re.I)
BANK_PILOT_AUTH_SCHEMA = 'GeoCity direct picker pilot authorization v1'
BANK_PILOT_SCOPE = 'single technical pilot; no catalog release'
BANK_PILOT_AUTH_SHA256 = '21d4d25f75988ae77ca483d962fa0a990f18516e69ceaeb5d1aae2f1b65d94f6'
BANK_PILOT_OBJECT = re.compile(
    r"(?:StaticMesh'(?P<typed>/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+)'|"
    r'(?P<bare>/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+))')
MODULE_TEST_OBJECT = (
    '/Game/ModularCourtyard/Meshes/'
    'SM_wall_windows_4x4_01.SM_wall_windows_4x4_01')
MODULE_TEST_PACKAGE_SHA256 = (
    '551f2830e526d38d2e4ba20d8e044a36ca97be15e785d2d2ee0b5dbeef28f07b')
MODULE_TEST_CATALOG_SHA256 = (
    '26a845b22a5a62ca6846fe6f44a4e7adb51783d30c4c5c9e9f3a15f9d9c353f2')
MODULE_TEST_AREA_ID = 'GazaRimal'
MODULE_TEST_OSM_ID = '1010234236'
MODULE_TEST_EDGE_INDEX = 0
MODULE_TEST_WIDTH_M = 4.0


def bank_technical_check_only(row):
    """Recognize restricted IDs in short and full catalog identities."""
    return any(BANK_TECH_ONLY_TOKEN.search(str(row.get(field, '')))
               for field in ('Name', 'AssetId', 'VariantId', 'ObjectPath'))


def bank_bool(value):
    if value in (True, 1, 'True', 'true', '1'):
        return True
    if value in (False, 0, 'False', 'false', '0'):
        return False
    raise ValueError('Invalid Boolean: %r' % (value,))


def bank_parse(table):
    """Read actual translator fields, preserving names, storage and raw values."""
    attributes = {}
    for a in table.pointAttribs():
        attributes[a.name()] = {'type': str(a.dataType()),
                                'storage': str(a.numericDataType()) if a.dataType() != hou.attribData.String else 'String', 'size': a.size()}
    if not table.points():
        return [], attributes
    mapping = {}
    for field in BANK_FIELDS:
        matches = [n for n in attributes if re.fullmatch(
            r'unreal_data_table_\d+_' + re.escape(field), n, flags=re.I)]
        if len(matches) != 1:
            raise ValueError('Expected one translator column for %s: %r' % (field, matches))
        mapping[field] = matches[0]
    key = 'unreal_data_table_rowname'
    if key not in attributes:
        raise ValueError('Missing DataTable row name')
    rows, keys, ids = [], set(), set()
    for point in table.points():
        row = {f: point.attribValue(n) for f, n in mapping.items()}
        row['Name'] = point.attribValue(key)
        if row['Name'] in keys or row['AssetId'] in ids:
            raise ValueError('Duplicate catalog row key or AssetId')
        keys.add(row['Name']); ids.add(row['AssetId'])
        rows.append(row)
    return sorted(rows, key=lambda r: r['Name']), attributes


def bank_evaluate(rows, release_id):
    accepted, rejected = [], []
    for raw in rows:
        row, reasons = dict(raw), []
        try:
            for field in BANK_FLAGS:
                row[field] = bank_bool(row[field])
            for field in BANK_NUMBERS:
                row[field] = float(row[field])
                if not math.isfinite(row[field]):
                    raise ValueError('Nonfinite ' + field)
            if int(row['SchemaVersion']) != 1:
                reasons.append('unsupported_schema')
            if not row['RunEligible']: reasons.append('disabled')
            if bank_technical_check_only(row): reasons.append('technical_check_only')
            if not release_id: reasons.append('no_recorded_release')
            for flag in ['BoundsValid', 'AnchorValid', 'OrientationValid']:
                if not row[flag]: reasons.append(flag + '=false')
            if row['ForwardAxis'] not in ('+X', '-X', '+Y', '-Y'):
                reasons.append('unsupported_forward_axis')
            if not re.fullmatch(r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+', row['ObjectPath']):
                reasons.append('invalid_native_object_path')
            if not re.fullmatch(r'[a-fA-F0-9]{64}', row['AssetRevision']):
                reasons.append('missing_asset_revision')
            if not row['AssetId'] or not row['Role'] or not row['VariantId']:
                reasons.append('missing_identity_or_role')
            if any(row['BoundsMax' + a + 'Cm'] <= row['BoundsMin' + a + 'Cm'] for a in 'XYZ'):
                reasons.append('invalid_bounds')
        except (KeyError, ValueError, TypeError) as exc:
            reasons.append('invalid_field:' + str(exc))
        if reasons:
            rejected.append({'row': raw['Name'], 'reasons': reasons})
        else:
            accepted.append(row)
    return accepted, rejected


def bank_select(rows, role, placement_id, seed):
    candidates = sorted((r for r in rows if r['Role'] == role),
                        key=lambda r: (r['AssetId'], r['VariantId']))
    if not candidates: return None
    token = json.dumps([int(seed), role, placement_id], separators=(',', ':'))
    index = int(hashlib.sha256(token.encode()).hexdigest(), 16) % len(candidates)
    return candidates[index]


def bank_parse_versioned(table):
    """Read native DataTable columns; preserve v1 and require exact v2 layout."""
    names = {attrib.name() for attrib in table.pointAttribs()}
    numbered = {name for name in names if re.fullmatch(r'unreal_data_table_\d+_.+', name)}
    v2_present = any(re.fullmatch(
        r'unreal_data_table_\d+_' + re.escape(field), name, re.I)
        for name in numbered for field in BANK_V2_EXTRA_FIELDS)
    if not v2_present:
        rows, attributes = bank_parse(table)
        if any(int(row['SchemaVersion']) != 1 for row in rows):
            raise ValueError('v2 SchemaVersion requires the complete 27-field table')
        return rows, attributes, 1
    expected = {'unreal_data_table_%d_%s' % (index, field)
                for index, field in enumerate(BANK_V2_FIELDS, 1)}
    if numbered != expected:
        raise ValueError('v2 DataTable has missing, reordered or unknown columns: %r' %
                         sorted(numbered ^ expected))
    if 'unreal_data_table_rowname' not in names:
        raise ValueError('v2 DataTable has no row name attribute')
    numeric_fields = set(BANK_NUMBERS + ['SelectionWeight'])
    integer_fields = set(BANK_FLAGS + ['SchemaVersion'])
    for index, field in enumerate(BANK_V2_FIELDS, 1):
        attrib = table.findPointAttrib('unreal_data_table_%d_%s' % (index, field))
        expected_type = (hou.attribData.Float if field in numeric_fields else
                         hou.attribData.Int if field in integer_fields else
                         hou.attribData.String)
        if attrib.dataType() != expected_type or attrib.size() != 1:
            raise ValueError('v2 DataTable field has wrong HAPI type or tuple size: ' + field)
    attributes = {a.name(): {'type': str(a.dataType()),
                             'storage': str(a.numericDataType())
                             if a.dataType() != hou.attribData.String else 'String',
                             'size': a.size()} for a in table.pointAttribs()}
    rows, row_names, asset_ids, object_paths = [], set(), set(), set()
    for point in table.points():
        row = {field: point.attribValue('unreal_data_table_%d_%s' % (index, field))
               for index, field in enumerate(BANK_V2_FIELDS, 1)}
        row['Name'] = point.attribValue('unreal_data_table_rowname')
        if int(row['SchemaVersion']) != 2:
            raise ValueError('v2 DataTable has a non-v2 or mixed SchemaVersion')
        if not row['Name'] or not row['AssetId']:
            raise ValueError('v2 DataTable has an empty row identity')
        if not row['ObjectPath'] and bank_bool(row['RunEligible']):
            raise ValueError('Enabled v2 DataTable row has no native ObjectPath')
        if (row['Name'] in row_names or row['AssetId'] in asset_ids or
                (row['ObjectPath'] and row['ObjectPath'] in object_paths)):
            raise ValueError('v2 DataTable has duplicate row, AssetId or ObjectPath')
        row_names.add(row['Name']); asset_ids.add(row['AssetId'])
        if row['ObjectPath']:
            object_paths.add(row['ObjectPath'])
        rows.append(row)
    return sorted(rows, key=lambda row: row['Name']), attributes, 2


def bank_v2_tokens(value, field):
    if not isinstance(value, str):
        raise ValueError('%s must be a string' % field)
    if not value:
        return ()
    tokens = value.split('|')
    if (len(tokens) != len(set(tokens)) or
            any(BANK_V2_TOKEN.fullmatch(token) is None for token in tokens)):
        raise ValueError('%s has empty, duplicate, wildcard or invalid tokens' % field)
    return tuple(tokens)


def bank_evaluate_v2(rows, release_id):
    """Fail closed on any invalid enabled row; disabled rows remain evidence."""
    accepted, rejected = [], []
    for raw in rows:
        row, reasons = dict(raw), []
        try:
            for field in BANK_FLAGS:
                row[field] = bank_bool(row[field])
            for field in BANK_NUMBERS + ['SelectionWeight']:
                row[field] = float(row[field])
                if not math.isfinite(row[field]):
                    raise ValueError('Nonfinite ' + field)
            areas = bank_v2_tokens(row['AllowedAreas'], 'AllowedAreas')
            zones = bank_v2_tokens(row['AllowedZones'], 'AllowedZones')
            ids = bank_v2_tokens(row['AllowedPlacementIds'], 'AllowedPlacementIds')
            row['_areas'], row['_zones'], row['_ids'] = areas, zones, ids
            if row['PlacementScope'] not in BANK_V2_SCOPES:
                raise ValueError('Invalid PlacementScope')
            if not row['RunEligible']:
                reasons.append('disabled')
            else:
                if bank_technical_check_only(row):
                    reasons.append('technical_check_only')
                if not release_id or row['ReleaseId'] != release_id:
                    reasons.append('release_id_mismatch')
                if not row['DecisionId']:
                    reasons.append('missing_decision_id')
                if not row['FamilyId'] or not row['StyleSet']:
                    reasons.append('missing_family_or_style')
                if row['SelectionWeight'] <= 0:
                    reasons.append('invalid_selection_weight')
                for flag in ('BoundsValid', 'AnchorValid', 'OrientationValid'):
                    if not row[flag]: reasons.append(flag + '=false')
                if row['ForwardAxis'] not in ('+X', '-X', '+Y', '-Y'):
                    reasons.append('unsupported_forward_axis')
                if not re.fullmatch(r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+', row['ObjectPath']):
                    reasons.append('invalid_native_object_path')
                if not re.fullmatch(r'[a-fA-F0-9]{64}', row['AssetRevision']):
                    reasons.append('missing_asset_revision')
                if not row['AssetId'] or not row['Role'] or not row['VariantId']:
                    reasons.append('missing_identity_or_role')
                if any(row['BoundsMax' + axis + 'Cm'] <=
                       row['BoundsMin' + axis + 'Cm'] for axis in 'XYZ'):
                    reasons.append('invalid_bounds')
                if not areas:
                    reasons.append('missing_allowed_areas')
                if row['PlacementScope'] == 'exact_ids':
                    if not ids or any(':' not in ident or ident.partition(':')[0]
                                      not in areas for ident in ids):
                        reasons.append('invalid_exact_placement_ids')
                elif row['PlacementScope'] == 'area_zone':
                    if not zones or ids:
                        reasons.append('invalid_area_zone_scope')
                else:
                    reasons.append('no_placement_scope')
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError('Invalid v2 row %s: %s' % (raw.get('Name'), exc))
        if reasons:
            rejected.append({'row': raw['Name'], 'enabled': bool(row.get('RunEligible')),
                             'reasons': reasons})
        else:
            accepted.append(row)
    invalid_enabled = [item for item in rejected if item['enabled']]
    if invalid_enabled:
        raise ValueError('Invalid enabled v2 catalog rows: %s' %
                         json.dumps(invalid_enabled, sort_keys=True))
    return accepted, rejected


def bank_select_v2(rows, role, area_id, zone, placement_id, style_set, seed):
    """Weighted rendezvous selection after exact role, area and scope checks."""
    matches = []
    for row in rows:
        if (row['Role'] != role or row['StyleSet'] != style_set or
                area_id not in row['_areas']):
            continue
        if row['PlacementScope'] == 'exact_ids':
            if placement_id not in row['_ids']:
                continue
        elif row['PlacementScope'] == 'area_zone':
            if not zone or zone not in row['_zones']:
                continue
        else:
            continue
        token = json.dumps([int(seed), role, placement_id, row['AssetId'],
                            row['VariantId']], separators=(',', ':'))
        fraction = (int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], 'big')
                    + 1) / (2**64 + 1)
        score = -math.log(fraction) / row['SelectionWeight']
        matches.append((score, row['AssetId'], row['VariantId'], row))
    return min(matches, key=lambda item: item[:3])[3] if matches else None


def bank_pilot_selection(parent, request_geo, eligible, release_id):
    """Validate one owner-authorized geographic pole for the direct UE picker.

    This is separate from the released DataTable path. The authorization file
    records the exact one-site decision; it is not a catalog qualification.
    """
    if not parent.evalParm('bank_pilot_enabled'):
        return None
    if parent.evalParm('bank_inspection_only'):
        _fail('Direct picker pilot requires city mode')
    if eligible or release_id:
        _fail('Direct picker pilot cannot share a catalog release or eligible rows')
    auth_file = parent.evalParm('bank_pilot_authorization_file').strip()
    if not auth_file:
        _fail('Direct picker pilot needs its one-site authorization file')
    auth_path = Path(os.path.expandvars(os.path.expanduser(auth_file))).resolve()
    try:
        auth_bytes = auth_path.read_bytes()
        if hashlib.sha256(auth_bytes).hexdigest() != BANK_PILOT_AUTH_SHA256:
            _fail('Direct picker authorization differs from approved decision record')
        auth = json.loads(auth_bytes.decode('utf-8'))
    except (OSError, UnicodeError, ValueError) as exc:
        _fail('Cannot read direct picker authorization: %s' % exc)
    if not isinstance(auth, dict) or auth.get('schema') != BANK_PILOT_AUTH_SCHEMA:
        _fail('Unsupported direct picker authorization schema')
    if (auth.get('scope') != BANK_PILOT_SCOPE or auth.get('role') != 'street_pole'
            or auth.get('catalog_run_eligible') is not False
            or not str(auth.get('decision', '')).startswith('Aviv ')):
        _fail('Direct picker authorization is not the one-site pole decision')
    if not all(isinstance(auth.get(field), str) and auth[field]
               for field in ('asset_id', 'object_path', 'placement_id',
                             'asset_revision_sha256', 'rights_status', 'visual_status')):
        _fail('Direct picker authorization lacks identity or status')
    if not re.fullmatch(r'[a-fA-F0-9]{64}', auth['asset_revision_sha256']):
        _fail('Direct picker asset revision is invalid')
    if bank_technical_check_only({'AssetId': auth['asset_id'],
                                  'ObjectPath': auth['object_path']}):
        _fail('Technical-check-only asset cannot be used by the direct picker')
    chosen = parent.evalParm('bank_pilot_mesh_ref').strip()
    match = BANK_PILOT_OBJECT.fullmatch(chosen)
    if match is None:
        _fail('Direct picker requires a StaticMesh /Game object reference')
    object_path = match.group('typed') or match.group('bare')
    if object_path != auth['object_path']:
        _fail('Direct picker mesh differs from the authorized object path')
    if request_geo is None:
        _fail('Direct picker pilot has no geographic requests')
    for field in ('placement_id', 'bank_role', 'bank_yaw_degrees',
                  'request_origin', 'source_area_id', 'source_detail_id'):
        if request_geo.findPointAttrib(field) is None:
            _fail('Direct picker pilot request lacks ' + field)
    matches = [point for point in request_geo.points()
               if point.attribValue('placement_id') == auth['placement_id']]
    if len(matches) != 1:
        _fail('Direct picker authorized placement must occur exactly once')
    request = matches[0]
    area_id, delimiter, detail_id = auth['placement_id'].partition(':')
    if (not delimiter or not area_id or not detail_id
            or request.attribValue('bank_role') != 'street_pole'
            or request.attribValue('request_origin') != 'geographic_street_pole'
            or request.attribValue('source_area_id') != area_id
            or request.attribValue('source_detail_id') != detail_id):
        _fail('Direct picker placement is not the authorized geographic pole')
    try:
        anchor_cm = float(auth['anchor_z_cm'])
        if not math.isfinite(anchor_cm):
            raise ValueError('nonfinite anchor')
        yaw = float(request.attribValue('bank_yaw_degrees'))
        if not math.isfinite(yaw):
            raise ValueError('nonfinite yaw')
    except (KeyError, TypeError, ValueError) as exc:
        _fail('Direct picker placement transform is invalid: %s' % exc)
    forward_axis = auth.get('forward_axis')
    if forward_axis not in ('+X', '-X', '+Y', '-Y'):
        _fail('Direct picker forward axis is invalid')
    correction = {'+X': 0, '+Y': 90, '-X': 180, '-Y': -90}[forward_axis]
    orient = hou.Quaternion(-(yaw - correction), hou.Vector3(0, 1, 0))
    position = request.position() - hou.Vector3(0, anchor_cm / 100.0, 0)
    if not all(math.isfinite(v) for v in position):
        _fail('Direct picker position is invalid')
    return {'authorization': auth, 'authorization_sha256': hashlib.sha256(auth_bytes).hexdigest(),
            'request': request, 'object_path': object_path, 'position': position,
            'orient': tuple(orient)}


def building_module_test_selection(parent, pads, rows, schema_version, eligible,
                                   digest, expected_digest, release_enabled,
                                   release_id, style_set):
    """Place one intact native wall module on one measured OSM footprint edge."""
    if not parent.evalParm('module_test_enabled'):
        return None
    if (not parent.evalParm('bank_inspection_only') or
            parent.evalParm('bank_pilot_enabled')):
        _fail('Module test requires isolated inspection mode and the pole pilot off')
    if (schema_version != 2 or len(rows) != 1215 or
            digest != MODULE_TEST_CATALOG_SHA256 or
            expected_digest != MODULE_TEST_CATALOG_SHA256 or eligible or
            release_enabled or release_id or style_set):
        _fail('Module test requires the exact full disabled v2 native catalog')
    chosen = parent.evalParm('module_test_mesh_ref').strip()
    match = BANK_PILOT_OBJECT.fullmatch(chosen)
    if match is None or (match.group('typed') or match.group('bare')) != MODULE_TEST_OBJECT:
        _fail('Module test StaticMesh differs from the pinned native wall module')
    if pads is None:
        _fail('Module test has no geographic building pads')
    for field in ('source_area_id', 'source_osm_id', 'base_m'):
        if pads.findPrimAttrib(field) is None:
            _fail('Module test building pads lack ' + field)
    matches = [prim for prim in pads.prims()
               if prim.attribValue('source_area_id') == MODULE_TEST_AREA_ID and
               str(prim.attribValue('source_osm_id')) == MODULE_TEST_OSM_ID]
    if len(matches) != 1:
        _fail('Module test exact geographic footprint must occur once')
    pad = matches[0]
    coordinates = _xy(pad)
    if len(coordinates) <= MODULE_TEST_EDGE_INDEX:
        _fail('Module test footprint has no pinned edge')
    a = coordinates[MODULE_TEST_EDGE_INDEX]
    b = coordinates[(MODULE_TEST_EDGE_INDEX + 1) % len(coordinates)]
    dx, dz = b[0] - a[0], b[1] - a[1]
    edge_length = math.hypot(dx, dz)
    base = float(pad.attribValue('base_m'))
    if edge_length < MODULE_TEST_WIDTH_M or not math.isfinite(base):
        _fail('Module test edge is shorter than the 4 m module or base is invalid')
    along = (edge_length - MODULE_TEST_WIDTH_M) / 2.0
    position = hou.Vector3(a[0] + along * dx / edge_length,
                           base, a[1] + along * dz / edge_length)
    yaw = math.degrees(math.atan2(dz, dx))
    # The native module spans Unreal local -Y, from its pivot for 400 cm.
    # Unreal -Y maps to Houdini -Z; the existing bank quaternion convention
    # uses the negative of the required Unreal yaw about Houdini +Y.
    orient = hou.Quaternion(-(yaw + 90.0), hou.Vector3(0, 1, 0))
    ident = ('%s:building_%s_edge_%d_wall_0' %
             (MODULE_TEST_AREA_ID, MODULE_TEST_OSM_ID, MODULE_TEST_EDGE_INDEX))
    return {'placement_id': ident, 'object_path': MODULE_TEST_OBJECT,
            'source_area_id': MODULE_TEST_AREA_ID,
            'source_osm_id': MODULE_TEST_OSM_ID,
            'edge_index': MODULE_TEST_EDGE_INDEX,
            'edge_start': a, 'edge_end': b, 'edge_length_m': edge_length,
            'module_width_m': MODULE_TEST_WIDTH_M, 'base_m': base,
            'position': tuple(position), 'orient': tuple(orient),
            'edge_yaw_degrees': yaw,
            'module_package_sha256_recorded': MODULE_TEST_PACKAGE_SHA256}


def _geographic_detail_groups(source, expected_kind):
    """Recover the contact point and identity from an existing detail mesh."""
    declared = json.loads(source.attribValue('detail_ids_json'))
    if len(declared) != len(set(declared)):
        _fail('Duplicate procedural detail ID in ' + expected_kind)
    groups = {}
    for primitive in source.prims():
        detail_id = primitive.attribValue('detail_id')
        area_id = primitive.attribValue('source_area_id')
        osm_id = primitive.attribValue('source_osm_id')
        if primitive.attribValue('detail_kind') != expected_kind or not detail_id or not area_id:
            _fail('Invalid procedural detail identity in ' + expected_kind)
        group = groups.setdefault(detail_id, {'area_id': area_id, 'osm_id': osm_id,
                                              'xmin': math.inf, 'xmax': -math.inf,
                                              'ymin': math.inf, 'zmin': math.inf,
                                              'zmax': -math.inf})
        if group['area_id'] != area_id or group['osm_id'] != osm_id:
            _fail('Conflicting procedural detail identity: ' + detail_id)
        for vertex in primitive.vertices():
            x, y, z = vertex.point().position()
            group['xmin'] = min(group['xmin'], x)
            group['xmax'] = max(group['xmax'], x)
            group['ymin'] = min(group['ymin'], y)
            group['zmin'] = min(group['zmin'], z)
            group['zmax'] = max(group['zmax'], z)
    if set(groups) != set(declared):
        _fail('Procedural detail ledger differs from mesh in ' + expected_kind)
    return [(detail_id, groups[detail_id]) for detail_id in sorted(groups)]


def _street_segment_yaws(source):
    """Use the same eligible road segments that positioned the street poles."""
    yaws = {}
    for primitive in source.prims():
        if str(primitive.attribValue('route_role')) != 'road':
            continue
        osm_id = str(primitive.attribValue('source_osm_id'))
        coords = _xy(primitive)
        for index, (a, b) in enumerate(zip(coords, coords[1:])):
            dx, dz = b[0] - a[0], b[1] - a[1]
            if math.hypot(dx, dz) < 1.0:
                continue
            key = (osm_id, index)
            if key in yaws:
                _fail('Ambiguous road segment for pole requests: %s segment %d' % key)
            yaws[key] = math.degrees(math.atan2(dz, dx)) % 360.0
    return yaws


def cook_city_placement_requests(node):
    """Convert existing tree/pole placements and optional input 1 into points."""
    trees, poles, external, roads = [item.geometry() for item in node.inputs()[:4]]
    seed = int(node.parent().evalParm('seed'))
    yaws = _street_segment_yaws(roads)
    geo = node.geometry()
    geo.clear()
    attrs = {name: geo.addAttrib(hou.attribType.Point, name, default)
             for name, default in (('placement_id', ''), ('bank_role', ''),
                                   ('bank_yaw_degrees', 0.0), ('source_area_id', ''),
                                   ('source_osm_id', ''), ('source_detail_id', ''),
                                   ('request_origin', ''))}
    counts = {'tree': 0, 'street_pole': 0, 'external': 0}
    internal_ids = []

    def add_request(position, values):
        point = geo.createPoint()
        point.setPosition(position)
        for name, attr in attrs.items():
            point.setAttribValue(attr, values.get(name, 0.0 if name == 'bank_yaw_degrees' else ''))

    for detail_id, group in _geographic_detail_groups(trees, 'procedural_tree_blockout'):
        area_id = group['area_id']
        placement_id = area_id + ':' + detail_id
        yaw = 360.0 * _stable_fraction(seed, area_id, detail_id, 'bank_tree_yaw')
        add_request(((group['xmin'] + group['xmax']) / 2.0, group['ymin'],
                     (group['zmin'] + group['zmax']) / 2.0),
                    {'placement_id': placement_id, 'bank_role': 'tree',
                     'bank_yaw_degrees': yaw, 'source_area_id': area_id,
                     'source_detail_id': detail_id, 'request_origin': 'geographic_tree'})
        counts['tree'] += 1
        internal_ids.append(placement_id)

    for detail_id, group in _geographic_detail_groups(poles, 'procedural_street_pole'):
        area_id, osm_id = group['area_id'], group['osm_id']
        parts = detail_id.rsplit('_', 2)
        if len(parts) != 3 or parts[0] != 'pole_' + osm_id:
            _fail('Pole ID cannot identify its road segment: ' + detail_id)
        try:
            segment_index = int(parts[1])
        except ValueError:
            _fail('Invalid pole segment index: ' + detail_id)
        key = (osm_id, segment_index)
        if key not in yaws:
            _fail('Pole request has no eligible road segment: ' + detail_id)
        placement_id = area_id + ':' + detail_id
        add_request(((group['xmin'] + group['xmax']) / 2.0, group['ymin'],
                     (group['zmin'] + group['zmax']) / 2.0),
                    {'placement_id': placement_id, 'bank_role': 'street_pole',
                     'bank_yaw_degrees': yaws[key], 'source_area_id': area_id,
                     'source_osm_id': osm_id, 'source_detail_id': detail_id,
                     'request_origin': 'geographic_street_pole'})
        counts['street_pole'] += 1
        internal_ids.append(placement_id)

    # Input 1 remains optional. It keeps the original placement attributes and
    # still reaches the existing selector, alongside ordinary geographic points.
    for point in external.points():
        values = {name: point.attribValue(name) for name in attrs
                  if external.findPointAttrib(name) is not None}
        values['request_origin'] = 'external'
        add_request(point.position(), values)
        counts['external'] += 1
    _set_detail(geo, 'bank_request_counts_json', json.dumps(counts, sort_keys=True))
    _set_detail(geo, 'bank_internal_request_ids_json', json.dumps(internal_ids))
    _set_detail(geo, 'bank_internal_request_count', len(internal_ids))


def cook_catalog_guard(node):
    """Input 0: native table; input 1: requests; input 2: building pads."""
    parent, geo = node.parent(), node.geometry()
    geo.clear()
    if parent.evalParm('catalog_file').strip():
        _fail('Use the authoritative native DataTable input; CSV runtime fallback is disabled')
    table = node.inputs()[0].geometry()
    pilot_enabled = bool(parent.evalParm('bank_pilot_enabled'))
    module_test_enabled = bool(parent.evalParm('module_test_enabled'))
    if (not table.points() and
            (not parent.evalParm('bank_inspection_only') or pilot_enabled or
             module_test_enabled)):
        _fail('City mode requires the native Unreal DataTable on Geometry input 0')
    try:
        rows, attributes, schema_version = bank_parse_versioned(table)
        release_id = parent.evalParm('catalog_release_id').strip()
        if schema_version == 2:
            eligible, rejected = bank_evaluate_v2(rows, release_id)
        else:
            eligible, rejected = bank_evaluate(rows, release_id)
    except (ValueError, TypeError) as exc:
        _fail('catalog: ' + str(exc))
    canonical = json.dumps(rows, sort_keys=True, separators=(',', ':'), allow_nan=False)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    expected_digest = parent.evalParm('catalog_expected_sha256').strip().lower()
    release_enabled = bool(parent.evalParm('bank_release_enabled'))
    style_set = parent.evalParm('bank_style_set').strip()
    if schema_version == 2:
        # One authorized direct-picker site can coexist with the canonical
        # all-disabled v2 catalog. The pilot still never selects a v2 row.
        if pilot_enabled and (eligible or release_enabled or release_id or style_set):
            _fail('v2 direct picker pilot requires all-disabled rows, release off and blank release/style')
        if expected_digest and (not re.fullmatch(r'[a-f0-9]{64}', expected_digest)
                                or expected_digest != digest):
            _fail('v2 live DataTable digest differs from recorded release digest')
        if eligible:
            if (not release_enabled or not release_id or not expected_digest or
                    not style_set or parent.evalParm('bank_inspection_only')):
                _fail('v2 eligible rows require explicit release, live digest, style and city mode')
            if not any(row['StyleSet'] == style_set for row in eligible):
                _fail('v2 selected style has no eligible catalog row')
        elif release_enabled:
            _fail('v2 release switch is on but the catalog has no eligible rows')
    elif eligible or release_enabled or expected_digest:
        _fail('v1 catalog is inspection/pilot only in GeoCity v003')
    request_geo = node.inputs()[1].geometry() if len(node.inputs()) > 1 and node.inputs()[1] else None
    request_count = len(request_geo.points()) if request_geo is not None else 0
    request_roles = {}
    requests = []
    if request_geo is not None and all(request_geo.findPointAttrib(field) for field in
                                       ('placement_id', 'bank_role', 'bank_yaw_degrees')):
        for point in sorted(request_geo.points(), key=lambda p: p.attribValue('placement_id')):
            role = point.attribValue('bank_role')
            request_roles[role] = request_roles.get(role, 0) + 1
            requests.append({'placement_id': point.attribValue('placement_id'),
                             'bank_role': role, 'P': tuple(point.position()),
                             'bank_yaw_degrees': point.attribValue('bank_yaw_degrees'),
                             'request_origin': point.attribValue('request_origin')
                                 if request_geo.findPointAttrib('request_origin') else ''})
    internal_requests = [item for item in requests
                         if item['request_origin'] in ('geographic_tree',
                                                       'geographic_street_pole')]
    internal_roles = {}
    for item in internal_requests:
        role = item['bank_role']
        internal_roles[role] = internal_roles.get(role, 0) + 1
    pilot = bank_pilot_selection(parent, request_geo, eligible, release_id)
    pad_geo = node.inputs()[2].geometry() if len(node.inputs()) > 2 and node.inputs()[2] else None
    module_test = building_module_test_selection(
        parent, pad_geo, rows, schema_version, eligible, digest, expected_digest,
        release_enabled, release_id, style_set)
    ledger, seen = [], set()
    if request_geo is not None and eligible and pilot is None:
        for field in ('placement_id', 'bank_role', 'bank_yaw_degrees'):
            if not request_geo.findPointAttrib(field): _fail('Missing request ' + field)
        if schema_version == 2:
            for field in ('source_area_id', 'request_origin'):
                if not request_geo.findPointAttrib(field): _fail('Missing v2 request ' + field)
            if (any(row['PlacementScope'] == 'area_zone' for row in eligible)
                    and not request_geo.findPointAttrib('bank_zone')):
                _fail('v2 area_zone rows require a geographic bank_zone attribute')
        for request in sorted(request_geo.points(), key=lambda p: p.attribValue('placement_id')):
            ident, role = request.attribValue('placement_id'), request.attribValue('bank_role')
            if not ident or ident in seen: _fail('Empty/duplicate placement_id')
            seen.add(ident)
            if schema_version == 2:
                area_id = request.attribValue('source_area_id')
                origin = request.attribValue('request_origin')
                expected_origin = {'tree': 'geographic_tree',
                                   'street_pole': 'geographic_street_pole'}.get(role)
                if (not area_id or ident.partition(':')[0] != area_id or
                        origin != expected_origin):
                    _fail('v2 request is not a supported geographic placement: ' + ident)
                zone = (request.attribValue('bank_zone')
                        if request_geo.findPointAttrib('bank_zone') else '')
                row = bank_select_v2(eligible, role, area_id, zone, ident,
                                     style_set, parent.evalParm('seed'))
            else:
                row = bank_select(eligible, role, ident, parent.evalParm('seed'))
            if row is None: continue
            yaw = float(request.attribValue('bank_yaw_degrees'))
            if not math.isfinite(yaw): _fail('Invalid placement yaw')
            # Unreal forward maps into Houdini X/Z. Positive Unreal yaw rotates X toward Z.
            correction = {'+X': 0, '+Y': 90, '-X': 180, '-Y': -90}[row['ForwardAxis']]
            angle = -(yaw - correction)
            orient = hou.Quaternion(angle, hou.Vector3(0, 1, 0))
            position = request.position() - hou.Vector3(0, row['AnchorZCm']/100.0, 0)
            if not all(math.isfinite(v) for v in position): _fail('Invalid placement position')
            point = geo.createPoint(); point.setPosition(position)
            values = {'unreal_instance': row['ObjectPath'], 'bank_asset_id': row['AssetId'],
                      'bank_variant_id': row['VariantId'], 'placement_id': ident,
                      'bank_role': role, 'bank_catalog_sha256': digest,
                      'bank_release_id': release_id, 'bank_asset_revision': row['AssetRevision'],
                      'orient': tuple(orient),
                      'source_area_id': request.attribValue('source_area_id')
                          if request_geo.findPointAttrib('source_area_id') else '',
                      'source_osm_id': request.attribValue('source_osm_id')
                          if request_geo.findPointAttrib('source_osm_id') else '',
                      'source_detail_id': request.attribValue('source_detail_id')
                          if request_geo.findPointAttrib('source_detail_id') else ''}
            if schema_version == 2:
                values.update({'bank_family_id': row['FamilyId'],
                               'bank_style_set': row['StyleSet'],
                               'bank_decision_id': row['DecisionId'],
                               'bank_selection_source': 'catalog_v2',
                               'bank_placement_scope': row['PlacementScope'],
                               'bank_selection_weight': row['SelectionWeight']})
            for key, value in values.items():
                attr = geo.findPointAttrib(key) or geo.addAttrib(hou.attribType.Point, key,
                    (0.0, 0.0, 0.0, 1.0) if key == 'orient' else
                    0.0 if key == 'bank_selection_weight' else '')
                point.setAttribValue(attr, value)
            ledger.append({'placement_id': ident, 'row': row['Name'], 'path': row['ObjectPath'],
                           'P': tuple(position), 'orient': tuple(orient),
                           'selection_source': 'catalog_v2' if schema_version == 2 else 'catalog_v1'})
    if pilot is not None:
        auth, request = pilot['authorization'], pilot['request']
        point = geo.createPoint()
        point.setPosition(pilot['position'])
        values = {'unreal_instance': pilot['object_path'],
                  'bank_asset_id': auth['asset_id'],
                  'bank_variant_id': 'direct_picker_one_site',
                  'placement_id': auth['placement_id'],
                  'bank_role': 'street_pole',
                  'bank_catalog_sha256': digest,
                  'bank_release_id': '',
                  'bank_asset_revision': auth['asset_revision_sha256'],
                  'bank_selection_source': 'direct_picker_pilot',
                  'bank_pilot_authorization_sha256': pilot['authorization_sha256'],
                  'orient': pilot['orient'],
                  'source_area_id': request.attribValue('source_area_id'),
                  'source_osm_id': request.attribValue('source_osm_id')
                      if request_geo.findPointAttrib('source_osm_id') else '',
                  'source_detail_id': request.attribValue('source_detail_id')}
        for key, value in values.items():
            attr = geo.findPointAttrib(key) or geo.addAttrib(hou.attribType.Point, key,
                (0.0, 0.0, 0.0, 1.0) if key == 'orient' else '')
            point.setAttribValue(attr, value)
        ledger.append({'placement_id': auth['placement_id'], 'row': None,
                       'path': pilot['object_path'], 'P': tuple(pilot['position']),
                       'orient': pilot['orient'],
                       'selection_source': 'direct_picker_pilot',
                       'authorization_sha256': pilot['authorization_sha256']})
    if module_test is not None:
        point = geo.createPoint()
        point.setPosition(module_test['position'])
        values = {'unreal_instance': module_test['object_path'],
                  'orient': module_test['orient'],
                  'placement_id': module_test['placement_id'],
                  'bank_role': 'building_wall_technical',
                  'bank_selection_source': 'module_material_test',
                  'bank_catalog_sha256': digest,
                  'bank_release_id': '',
                  'source_area_id': module_test['source_area_id'],
                  'source_osm_id': module_test['source_osm_id']}
        for key, value in values.items():
            attr = geo.findPointAttrib(key) or geo.addAttrib(
                hou.attribType.Point, key,
                (0.0, 0.0, 0.0, 1.0) if key == 'orient' else '')
            point.setAttribValue(attr, value)
        ledger.append({'placement_id': module_test['placement_id'],
                       'row': None, 'path': module_test['object_path'],
                       'P': module_test['position'],
                       'orient': module_test['orient'],
                       'selection_source': 'module_material_test'})
    receipt = {'interface': 'GeoCity bank v%d' % schema_version,
               'schema_version': schema_version,
               'rows': rows, 'attributes': attributes,
               'catalog_sha256': digest, 'release_id': release_id, 'rejected': rejected,
               'expected_catalog_sha256': expected_digest,
               'release_enabled': release_enabled, 'style_set': style_set,
               'eligible_count': len(eligible), 'request_count': request_count,
               'request_roles': request_roles, 'requests': requests,
               'internal_request_count': len(internal_requests),
               'internal_request_roles': internal_roles,
               'internal_request_sample_ids': [item['placement_id']
                                               for item in internal_requests[:10]],
               'instances': ledger,
               'houdini': hou.applicationVersionString(), 'pid': os.getpid()}
    if pilot is not None:
        receipt['direct_picker_pilot'] = {
            'enabled': True, 'scope': BANK_PILOT_SCOPE,
            'authorization_sha256': pilot['authorization_sha256'],
            'asset_id': auth['asset_id'], 'object_path': pilot['object_path'],
            'placement_id': auth['placement_id'], 'role': 'street_pole',
            'catalog_release': False,
            'asset_revision_sha256': auth['asset_revision_sha256'],
            'asset_revision_verification':
                'recorded_from_authorization; not_verified_inside_HARS',
            'rights_status': auth['rights_status'],
            'visual_status': auth['visual_status'],
            'houdini_emitted_points': 1,
            'unreal_asset_resolution': 'not_verified_by_Houdini'}
    if module_test is not None:
        receipt['building_module_technical_test'] = {
            key: value for key, value in module_test.items()
            if key not in ('position', 'orient')}
        receipt['building_module_technical_test'].update({
            'P': module_test['position'], 'orient': module_test['orient'],
            'catalog_release': False, 'material_override_attributes': [],
            'unreal_asset_resolution': 'not_verified_by_Houdini',
            'native_materials': 'must_be_checked_in_Unreal'})
    _set_detail(geo, 'bank_catalog_readback_json', json.dumps(receipt, sort_keys=True))
    _set_detail(geo, 'bank_catalog_sha256', digest)
    _set_detail(geo, 'catalog_input_rows_disabled', sum(not bank_bool(r['RunEligible']) for r in rows))
    _set_detail(geo, 'catalog_rows_disabled', sum(not bank_bool(r['RunEligible']) for r in rows))
    _set_detail(geo, 'bank_instances', len(ledger))
    _set_detail(geo, 'bank_request_count', request_count)
    _set_detail(geo, 'bank_internal_request_count', len(internal_requests))
    _set_detail(geo, 'bank_request_roles_json', json.dumps(request_roles, sort_keys=True))
    _set_detail(geo, 'unreal_output_name', 'bank_instances')
    # Optional evidence export addresses the Unreal Details panel's missing attribute readback.
    report = parent.evalParm('bank_receipt_file').strip()
    if report:
        Path(report).write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding='utf-8')


def cook_bank_proxy_filter(node, role, detail_kind):
    """Keep procedural details unless output 7 emitted their exact bank match."""
    source, bank = [input_node.geometry() for input_node in node.inputs()[:2]]
    geo = node.geometry()
    geo.clear()
    geo.merge(source)
    if not bank.points():
        return
    fields = ('placement_id', 'bank_role', 'source_area_id',
              'source_detail_id', 'unreal_instance')
    if any(bank.findPointAttrib(field) is None for field in fields):
        _fail('Bank instance output lacks proxy-substitution identity')
    matched = set()
    for point in bank.points():
        if point.attribValue('bank_role') != role:
            continue
        area_id = point.attribValue('source_area_id')
        detail_id = point.attribValue('source_detail_id')
        placement_id = point.attribValue('placement_id')
        if (area_id and detail_id and point.attribValue('unreal_instance') and
                placement_id == area_id + ':' + detail_id):
            matched.add((area_id, detail_id))
    if not matched:
        return
    removed = set()
    delete = []
    for prim in geo.prims():
        if prim.attribValue('detail_kind') != detail_kind:
            continue
        key = (prim.attribValue('source_area_id'), prim.attribValue('detail_id'))
        if key in matched:
            delete.append(prim)
            removed.add(key)
    if removed != matched:
        _fail('Bank instance has no matching procedural proxy: %r' % sorted(matched - removed))
    geo.deletePrims(delete)
    removed_ids = {detail_id for _, detail_id in removed}
    remaining_ids = [detail_id for detail_id in json.loads(geo.attribValue('detail_ids_json'))
                     if detail_id not in removed_ids]
    _set_detail(geo, 'detail_ids_json', json.dumps(remaining_ids))


# Embedded measured modular layout solver v004
"""Deterministic measured-wall facade shell solver, independent of Houdini.

The candidate uses an actual native wall's rectangular end sections. Junctions,
residual strips and interior slabs are new geometry, never claimed as bank meshes.
Only the explicitly enabled technical pilot may emit native placement points.
"""

import hashlib
import json
import math


EPS = 1e-8


def digest(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross2(a, b):
    return a[0] * b[1] - a[1] * b[0]


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def mul(a, scalar):
    return [x * scalar for x in a]


def norm(a):
    return math.sqrt(dot(a, a))


def unit(a):
    size = norm(a)
    if size <= EPS:
        raise ValueError("zero_length_edge")
    return mul(a, 1.0 / size)


def area2(ring):
    return sum(cross2(a, b) for a, b in zip(ring, ring[1:] + ring[:1]))


def intersection(a, u, b, v):
    denominator = cross2(u, v)
    if abs(denominator) <= EPS:
        raise ValueError("parallel_offset_edges")
    travel = cross2(sub(b, a), v) / denominator
    return add(a, mul(u, travel)), travel


def _orientation(a, b, c):
    return cross2(sub(b, a), sub(c, a))


def _on_segment(a, b, p):
    return (abs(_orientation(a, b, p)) <= EPS and
            all(min(a[i], b[i]) - EPS <= p[i] <= max(a[i], b[i]) + EPS
                for i in (0, 1)))


def _segments_meet(a, b, c, d):
    signs = (_orientation(a, b, c), _orientation(a, b, d),
             _orientation(c, d, a), _orientation(c, d, b))
    if signs[0] * signs[1] < -EPS and signs[2] * signs[3] < -EPS:
        return True
    return any((_on_segment(a, b, c), _on_segment(a, b, d),
                _on_segment(c, d, a), _on_segment(c, d, b)))


def canonical_feature(raw):
    """Preserve source Float32 coordinates exactly; canonicalize only order."""
    if raw.get("holes") or raw.get("relation_ambiguous"):
        raise ValueError("holes_or_relation_ambiguous")
    if not raw.get("closed", True):
        raise ValueError("open_pad")
    if not raw.get("area_id") or not raw.get("osm_id"):
        raise ValueError("missing_source_identity")
    xyz = [[float(x) for x in vertex] for vertex in raw["ring_xyz_m"]]
    if xyz and norm(sub(xyz[0], xyz[-1])) <= EPS:
        xyz.pop()
    if len(xyz) < 3 or len(xyz) > 64 or any(len(p) != 3 for p in xyz):
        raise ValueError("unsupported_vertex_count")
    if not all(math.isfinite(x) for p in xyz for x in p):
        raise ValueError("nonfinite_pad_coordinate")
    base = float(raw.get("base_m", xyz[0][1]))
    if not math.isfinite(base) or max(abs(p[1] - base) for p in xyz) > 1e-5:
        raise ValueError("nonplanar_pad_base")
    ring = [[p[0], p[2]] for p in xyz]
    if any(norm(sub(a, b)) <= EPS for a, b in zip(ring, ring[1:] + ring[:1])):
        raise ValueError("zero_length_edge")
    if abs(area2(ring)) <= EPS:
        raise ValueError("zero_area_pad")
    if area2(ring) < 0:
        ring.reverse()
    if len(set(tuple(p) for p in ring)) != len(ring):
        raise ValueError("repeated_vertex")
    edges = list(zip(ring, ring[1:] + ring[:1]))
    for i, (a, b) in enumerate(edges):
        for j, (c, d) in enumerate(edges):
            if j <= i or j == i + 1 or (i == 0 and j == len(edges) - 1):
                continue
            if _segments_meet(a, b, c, d):
                raise ValueError("self_intersecting_pad")
    start = min(range(len(ring)), key=lambda i: tuple(ring[i]))
    ring = ring[start:] + ring[:start]
    source_height = float(raw["source_height_m"])
    if not math.isfinite(source_height) or source_height <= 0:
        raise ValueError("invalid_source_height")
    return {
        "area_id": str(raw["area_id"]),
        "osm_id": str(raw["osm_id"]),
        "ring_xz_m": ring,
        "base_m": base,
        "source_height_m": source_height,
        "height_rule": str(raw.get("height_rule", "unknown")),
        "source_sha256": str(raw.get("source_sha256", "")),
    }


def _rotation(tangent):
    """Map native local -Z to edge tangent, +X toward pad interior, +Y up."""
    tx, tz = tangent
    return [[-tz, 0.0, -tx], [0.0, 1.0, 0.0], [tx, 0.0, -tz]]


def _quaternion(matrix):
    trace = sum(matrix[i][i] for i in range(3))
    if trace > 0:
        s = math.sqrt(trace + 1.0) * 2.0
        q = [(matrix[2][1] - matrix[1][2]) / s,
             (matrix[0][2] - matrix[2][0]) / s,
             (matrix[1][0] - matrix[0][1]) / s, s / 4.0]
    else:
        i = max(range(3), key=lambda k: matrix[k][k])
        j, k = (i + 1) % 3, (i + 2) % 3
        s = math.sqrt(max(EPS, 1.0 + matrix[i][i] - matrix[j][j] - matrix[k][k])) * 2.0
        q = [0.0, 0.0, 0.0, 0.0]
        q[i] = s / 4.0
        q[j] = (matrix[i][j] + matrix[j][i]) / s
        q[k] = (matrix[i][k] + matrix[k][i]) / s
        q[3] = (matrix[k][j] - matrix[j][k]) / s
    if q[3] < 0:
        q = [-v for v in q]
    return q


def _contract(wall, policy):
    required = ("sha256", "mesh_ref", "pitch_m", "height_m", "thickness_m",
                "start_connector_local_m",
                "start_x_min_m", "start_x_max_m", "end_x_min_m", "end_x_max_m")
    if any(k not in wall for k in required):
        raise ValueError("missing_native_wall_connector_measurement")
    for key in ("pitch_m", "height_m", "thickness_m"):
        if not math.isfinite(wall[key]) or wall[key] <= 0:
            raise ValueError("invalid_native_wall_" + key)
    if (abs(wall["start_x_min_m"] - wall["end_x_min_m"]) > 2e-5 or
            abs(wall["start_x_max_m"] - wall["end_x_max_m"]) > 2e-5 or
            abs(wall["start_x_min_m"]) > 2e-5 or
            abs(wall["start_x_max_m"] - wall["thickness_m"]) > 2e-5):
        raise ValueError("native_wall_end_sections_differ")
    if not wall.get("uv_present") or not wall.get("material_paths"):
        raise ValueError("native_wall_uv_or_material_missing")
    if (len(wall["start_connector_local_m"]) != 3 or
            not all(math.isfinite(v) for v in wall["start_connector_local_m"])):
        raise ValueError("invalid_wall_start_connector")
    for key in ("max_residual_width_m", "junction_margin_m", "slab_thickness_m",
                "max_seeded_height_delta_m", "max_seeded_height_delta_fraction",
                "angle_min_degrees", "angle_max_degrees"):
        if not isinstance(policy.get(key), (int, float)) or not math.isfinite(policy[key]):
            raise ValueError("invalid_policy_" + key)
    if not (0 < policy["max_residual_width_m"] <= wall["pitch_m"] and
            0 < policy["junction_margin_m"] < wall["thickness_m"] and
            0 < policy["slab_thickness_m"] < wall["height_m"] / 4 and
            0 < policy["max_seeded_height_delta_m"] < wall["height_m"] and
            0 < policy["max_seeded_height_delta_fraction"] <= 0.25 and
            0 < policy["angle_min_degrees"] < policy["angle_max_degrees"] < 180):
        raise ValueError("invalid_policy_bounds")
    if not policy.get("generated_material_path"):
        raise ValueError("missing_generated_material_path")
    return digest({"wall": wall, "policy": policy})


def _vertex(ring, index, wall, policy):
    n = len(ring)
    prev, point, following = ring[index - 1], ring[index], ring[(index + 1) % n]
    incoming = unit(sub(point, prev))
    outgoing = unit(sub(following, point))
    turn = math.degrees(math.atan2(cross2(incoming, outgoing), dot(incoming, outgoing)))
    interior = 180.0 - turn
    supported = policy["angle_min_degrees"] <= interior <= policy["angle_max_degrees"]
    if not supported:
        return {"vertex_index": index, "P_xz_m": point,
                "interior_angle_degrees": interior, "status": "unsupported_corner_angle"}
    thickness = wall["thickness_m"]
    normal_in = [-incoming[1], incoming[0]]
    normal_out = [-outgoing[1], outgoing[0]]
    inner, travel = intersection(add(point, mul(normal_in, thickness)), incoming,
                                 add(point, mul(normal_out, thickness)), outgoing)
    incoming_required = -travel
    outgoing_required = dot(sub(inner, add(point, mul(normal_out, thickness))), outgoing)
    if min(incoming_required, outgoing_required) <= 0:
        return {"vertex_index": index, "P_xz_m": point,
                "interior_angle_degrees": interior, "status": "invalid_inner_miter"}
    reserve_in = incoming_required + policy["junction_margin_m"]
    reserve_out = outgoing_required + policy["junction_margin_m"]
    outer_in = sub(point, mul(incoming, reserve_in))
    outer_out = add(point, mul(outgoing, reserve_out))
    inner_in = add(outer_in, mul(normal_in, thickness))
    inner_out = add(outer_out, mul(normal_out, thickness))
    outline = [outer_in, point, outer_out, inner_out, inner, inner_in]
    if area2(outline) <= EPS:
        raise ValueError("invalid_generated_junction_outline")
    return {"vertex_index": index, "P_xz_m": point,
            "interior_angle_degrees": interior, "status": "generated_measured_interface",
            "incoming_reserve_m": reserve_in, "outgoing_reserve_m": reserve_out,
            "inner_miter_xz_m": inner, "outline_xz_m": outline,
            "native_corner_candidate_status": "not_bound_or_angle_verified"}


def _inset_polygon(ring, amount):
    result = []
    for i, point in enumerate(ring):
        before = unit(sub(point, ring[i - 1]))
        after = unit(sub(ring[(i + 1) % len(ring)], point))
        a = add(point, mul([-before[1], before[0]], amount))
        b = add(point, mul([-after[1], after[0]], amount))
        inner, _ = intersection(a, before, b, after)
        result.append(inner)
    if area2(result) <= EPS:
        raise ValueError("roof_inset_collapsed")
    return result


def evaluate_feature(raw_feature, wall, policy):
    feature = canonical_feature(raw_feature)
    contract_id = _contract(wall, policy)
    root = feature["area_id"] + ":" + feature["osm_id"]
    ring = feature["ring_xz_m"]
    vertices = [_vertex(ring, i, wall, policy) for i in range(len(ring))]
    unsupported = sorted(set(v["status"] for v in vertices
                             if v["status"] != "generated_measured_interface"))
    floor_pitch = wall["height_m"]
    height_rule = feature["height_rule"]
    if height_rule == "seeded_rule_not_measured":
        floors = max(1, int(math.floor(feature["source_height_m"] / floor_pitch + 0.5)))
        height_policy = "nearest_whole_native_storeys_for_seeded_estimate"
    else:
        floors = max(1, int(round(feature["source_height_m"] / floor_pitch)))
        height_policy = "exact_native_storeys_required_for_explicit_height"
        if abs(floors * floor_pitch - feature["source_height_m"]) > 1e-4:
            unsupported.append("explicit_source_height_not_native_multiple")
    if floors > 80:
        unsupported.append("storey_count_limit")
    output_height = floors * floor_pitch
    if height_rule == "seeded_rule_not_measured":
        delta = abs(output_height - feature["source_height_m"])
        if (delta > policy["max_seeded_height_delta_m"] + EPS or
                delta / feature["source_height_m"] > policy["max_seeded_height_delta_fraction"] + EPS):
            unsupported.append("seeded_height_differs_too_much_from_native_storeys")
    walls, generated, edges = [], [], []
    if unsupported:
        return {
            "feature_id": root, "contract_id": contract_id, "source_feature": feature,
            "wall_contract": wall, "policy": policy, "vertices": vertices,
            "edge_ledger": edges, "wall_placements": walls, "generated_parts": generated,
            "floors": floors, "output_height_m": output_height,
            "height_delta_m": output_height - feature["source_height_m"],
            "height_policy": height_policy, "unsupported": sorted(set(unsupported)),
            "door_status": "unresolved_no_measured_entrance_bay",
            "status": "unsupported_no_geometry_emitted", "building_complete": False,
        }
    thickness = wall["thickness_m"]
    pitch = wall["pitch_m"]
    for i, point in enumerate(ring):
        next_point = ring[(i + 1) % len(ring)]
        tangent = unit(sub(next_point, point))
        inward = [-tangent[1], tangent[0]]
        edge_length = norm(sub(next_point, point))
        start = vertices[i]["outgoing_reserve_m"]
        end = edge_length - vertices[(i + 1) % len(ring)]["incoming_reserve_m"]
        available = end - start
        copies = max(0, int(math.floor((available + EPS) / pitch)))
        residual = available - copies * pitch
        reasons = []
        if available <= EPS:
            reasons.append("corner_reservations_overlap_or_short_edge")
        if copies < 1:
            reasons.append("no_full_native_wall_on_edge")
        if residual > policy["max_residual_width_m"] + EPS:
            reasons.append("residual_exceeds_generated_filler_limit")
        if residual < -EPS:
            reasons.append("negative_residual")
        edges.append({
            "edge_index": i, "start_xz_m": point, "end_xz_m": next_point,
            "length_m": edge_length, "start_reserve_m": start,
            "end_reserve_m": edge_length - end, "available_m": available,
            "native_wall_count_per_floor": copies, "native_wall_pitch_m": pitch,
            "native_covered_m": copies * pitch, "filler_width_m": residual,
            "closure_error_m": available - copies * pitch - residual,
            "unsupported": reasons,
        })
        unsupported.extend(reasons)
    if unsupported:
        return {
            "feature_id": root, "contract_id": contract_id, "source_feature": feature,
            "wall_contract": wall, "policy": policy, "vertices": vertices,
            "edge_ledger": edges, "wall_placements": walls, "generated_parts": generated,
            "floors": floors, "output_height_m": output_height,
            "height_delta_m": output_height - feature["source_height_m"],
            "height_policy": height_policy, "unsupported": sorted(set(unsupported)),
            "door_status": "unresolved_no_measured_entrance_bay",
            "status": "unsupported_no_geometry_emitted", "building_complete": False,
        }
    inner_ring = _inset_polygon(ring, thickness)
    for floor in range(floors):
        y = feature["base_m"] + floor * floor_pitch
        for i, vertex in enumerate(vertices):
            generated.append({
                "part_id": f"{root}:f{floor}:junction{i}:c{contract_id[:12]}",
                "role": "generated_corner_junction", "floor": floor,
                "outline_xz_m": vertex["outline_xz_m"], "bottom_y_m": y,
                "top_y_m": y + floor_pitch,
                "material_path": policy["generated_material_path"],
                "interface_basis": "measured_native_wall_0.5m_end_rectangle",
            })
        for edge in edges:
            i = edge["edge_index"]
            a, b = ring[i], ring[(i + 1) % len(ring)]
            tangent = unit(sub(b, a))
            inward = [-tangent[1], tangent[0]]
            cursor = edge["start_reserve_m"]
            rotation = _rotation(tangent)
            orientation = _quaternion(rotation)
            for slot in range(edge["native_wall_count_per_floor"]):
                start_xz = add(a, mul(tangent, cursor))
                end_xz = add(a, mul(tangent, cursor + pitch))
                placement_id = f"{root}:f{floor}:e{i}:w{slot}:c{contract_id[:12]}"
                local_start = wall["start_connector_local_m"]
                origin = [start_xz[0], y, start_xz[1]]
                origin = [origin[j] - dot(rotation[j], local_start) for j in range(3)]
                walls.append({
                    "placement_id": placement_id, "id": placement_id,
                    "unreal_split_attr": "id", "unreal_instance": wall["mesh_ref"],
                    "source_area_id": feature["area_id"], "source_osm_id": feature["osm_id"],
                    "floor": floor, "edge_index": i, "slot": slot,
                    "P": origin, "orient": orientation,
                    "rotation": rotation, "scale": [1.0, 1.0, 1.0],
                    "start_connector_world_m": [start_xz[0], y, start_xz[1]],
                    "end_connector_world_m": [end_xz[0], y, end_xz[1]],
                    "inward_xz": inward, "tangent_xz": tangent,
                    "source_wall_sha256": wall["sha256"],
                })
                cursor += pitch
            if edge["filler_width_m"] > EPS:
                start_xz = add(a, mul(tangent, cursor))
                end_xz = add(a, mul(tangent, cursor + edge["filler_width_m"]))
                generated.append({
                    "part_id": f"{root}:f{floor}:e{i}:filler:c{contract_id[:12]}",
                    "role": "generated_residual_filler", "floor": floor,
                    "outline_xz_m": [start_xz, end_xz,
                                     add(end_xz, mul(inward, thickness)),
                                     add(start_xz, mul(inward, thickness))],
                    "bottom_y_m": y, "top_y_m": y + floor_pitch,
                    "material_path": policy["generated_material_path"],
                    "width_m": edge["filler_width_m"],
                    "interface_basis": "measured_native_wall_0.5m_end_rectangle",
                })
    roof_y = feature["base_m"] + output_height
    for name, lower, upper in (
            ("ground_slab", feature["base_m"], feature["base_m"] + policy["slab_thickness_m"]),
            ("roof_slab", roof_y - policy["slab_thickness_m"], roof_y)):
        generated.append({
            "part_id": f"{root}:{name}:c{contract_id[:12]}", "role": name,
            "floor": -1 if name == "ground_slab" else floors,
            "outline_xz_m": inner_ring, "bottom_y_m": lower, "top_y_m": upper,
            "material_path": policy["generated_material_path"],
            "interface_basis": "inner_offset_of_measured_wall_thickness",
        })
    identifiers = [w["placement_id"] for w in walls] + [p["part_id"] for p in generated]
    if len(identifiers) != len(set(identifiers)):
        raise AssertionError("duplicate_placement_id")
    return {
        "feature_id": root, "contract_id": contract_id, "source_feature": feature,
        "wall_contract": wall, "policy": policy, "vertices": vertices,
        "edge_ledger": edges, "wall_placements": walls, "generated_parts": generated,
        "floors": floors, "output_height_m": output_height,
        "height_delta_m": output_height - feature["source_height_m"],
        "height_policy": height_policy, "unsupported": [],
        "door_status": "unresolved_no_measured_entrance_bay",
        "status": "measured_interface_shell_candidate_not_visual_or_unreal_verified",
        "building_complete": False,
        "native_corner_candidate_status": "not_bound_or_angle_verified",
    }


# Embedded modular Houdini geometry writer v004
"""Read native Houdini exports and materialize the v004 diagnostic outputs."""

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import hou



def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wall_contract(path):
    geo = hou.Geometry()
    geo.loadFromFile(str(path))
    if len(geo.prims()) < 1 or len(geo.points()) < 8:
        raise ValueError("empty_native_wall_export")
    if geo.findVertexAttrib("uv") is None or geo.findVertexAttrib("N") is None:
        raise ValueError("native_wall_uv_or_normals_missing")
    if geo.findPrimAttrib("unreal_input_mesh_name") is None:
        raise ValueError("native_mesh_name_missing")
    names = {str(p.attribValue("unreal_input_mesh_name")) for p in geo.prims()}
    if len(names) != 1:
        raise ValueError("mixed_native_mesh_export")
    mesh = names.pop()
    if not mesh.startswith("/Game/"):
        raise ValueError("native_unreal_mesh_path_invalid")
    if geo.findPrimAttrib("unreal_material") is None:
        raise ValueError("native_materials_missing")
    mats = Counter(str(p.attribValue("unreal_material")) for p in geo.prims())
    if not mats or any(not m for m in mats):
        raise ValueError("native_materials_empty")
    vertices = [list(p.position()) for p in geo.points()]
    z_start = max(p[2] for p in vertices)
    z_end = min(p[2] for p in vertices)
    tol = 2e-5
    ends = []
    for value in (z_start, z_end):
        section = [p for p in vertices if abs(p[2] - value) <= tol]
        if len(section) != 4:
            raise ValueError("native_end_section_not_four_corners")
        xs = [p[0] for p in section]
        ys = [p[1] for p in section]
        if (len(set(round(x, 4) for x in xs)) != 2 or
                len(set(round(y, 4) for y in ys)) != 2):
            raise ValueError("native_end_section_not_rectangular")
        ends.append({"x_min_m": min(xs), "x_max_m": max(xs),
                     "y_min_m": min(ys), "y_max_m": max(ys),
                     "z_m": value, "point_count": len(section)})
    start, end = ends
    height = start["y_max_m"] - start["y_min_m"]
    thickness = start["x_max_m"] - start["x_min_m"]
    if (abs(height - (end["y_max_m"] - end["y_min_m"])) > tol or
            abs(start["y_min_m"] - end["y_min_m"]) > tol or
            abs(thickness - (end["x_max_m"] - end["x_min_m"])) > tol):
        raise ValueError("native_wall_end_sections_not_identical")
    return {
        "source_file": str(Path(path).resolve()), "sha256": sha(path),
        "mesh_ref": "StaticMesh'%s'" % mesh,
        "pitch_m": z_start - z_end, "height_m": height,
        "thickness_m": thickness,
        "start_connector_local_m": [start["x_min_m"], start["y_min_m"], z_start],
        "start_x_min_m": start["x_min_m"],
        "start_x_max_m": start["x_max_m"],
        "end_x_min_m": end["x_min_m"],
        "end_x_max_m": end["x_max_m"],
        "start_end_sections": ends,
        "points": len(geo.points()), "primitives": len(geo.prims()),
        "uv_present": True, "normal_present": True,
        "material_paths": dict(mats),
    }


def read_features(path):
    geo = hou.Geometry()
    geo.loadFromFile(str(path))
    attrs = ("source_area_id", "source_osm_id", "base_m", "height_m", "height_rule")
    if any(geo.findPrimAttrib(key) is None for key in attrs):
        raise ValueError("pad_source_attributes_missing")
    features = []
    for prim in geo.prims():
        if prim.type() != hou.primType.Polygon:
            continue
        features.append({
            "area_id": str(prim.attribValue("source_area_id")),
            "osm_id": str(prim.attribValue("source_osm_id")),
            "ring_xyz_m": [list(v.point().position()) for v in prim.vertices()],
            "base_m": float(prim.attribValue("base_m")),
            "source_height_m": float(prim.attribValue("height_m")),
            "height_rule": str(prim.attribValue("height_rule")),
            "closed": prim.isClosed(),
            "holes": bool(prim.attribValue("has_holes")) if geo.findPrimAttrib("has_holes") else False,
            "source_sha256": sha(path),
        })
    return features


def _point_in_triangle(p, a, b, c):
    return (cross2(sub(b, a), sub(p, a)) >= -1e-10 and
            cross2(sub(c, b), sub(p, b)) >= -1e-10 and
            cross2(sub(a, c), sub(p, c)) >= -1e-10)


def _triangles(ring):
    """Ear clipping for convex and concave simple XZ rings."""
    if area2(ring) <= 0:
        raise ValueError("extrusion_requires_ccw_outline")
    remaining = list(range(len(ring)))
    triangles = []
    while len(remaining) > 3:
        found = False
        for slot in range(len(remaining)):
            a, b, c = [remaining[(slot + offset) % len(remaining)]
                       for offset in (-1, 0, 1)]
            if cross2(sub(ring[b], ring[a]), sub(ring[c], ring[b])) <= 1e-10:
                continue
            if any(_point_in_triangle(ring[other], ring[a], ring[b], ring[c])
                   for other in remaining if other not in (a, b, c)):
                continue
            triangles.append([a, b, c])
            del remaining[slot]
            found = True
            break
        if not found:
            raise ValueError("generated_outline_triangulation_failed")
    triangles.append(remaining)
    return triangles


def _normal(vertices):
    a, b, c = [hou.Vector3(v) for v in vertices[:3]]
    n = (b - a).cross(c - a)
    if n.length() < 1e-10:
        raise ValueError("zero_area_generated_face")
    # Houdini's polygon front and N use the negative raw cross convention.
    return tuple(-component for component in n.normalized())


def generated_geometry(record):
    degenerate_faces = 0
    geo = hou.Geometry()
    geo.setPreferredPrecision(64)
    p_str = {k: geo.addAttrib(hou.attribType.Prim, k, "") for k in
             ("part_id", "role", "face_kind", "source_area_id", "source_osm_id",
              "unreal_material", "unreal_output_name")}
    p_floor = geo.addAttrib(hou.attribType.Prim, "floor", 0)
    v_n = geo.addAttrib(hou.attribType.Vertex, "N", (0.0, 0.0, 0.0))
    v_uv = geo.addAttrib(hou.attribType.Vertex, "uv", (0.0, 0.0, 0.0))
    output_name = "v004_%s_%s_generated" % (
        record["source_feature"]["area_id"], record["source_feature"]["osm_id"])
    expected_faces = 0
    for part in record["generated_parts"]:
        ring = part["outline_xz_m"]
        bottom, top = part["bottom_y_m"], part["top_y_m"]
        if top <= bottom or area2(ring) <= 1e-10:
            raise ValueError("invalid_generated_solid")
        vertices = []
        for y in (bottom, top):
            row = []
            for x, z in ring:
                point = geo.createPoint()
                point.setPosition((x, y, z))
                row.append(point)
            vertices.append(row)
        triangles = _triangles(ring)
        faces = []
        for triangle in triangles:
            faces.append(("bottom", [(0, j) for j in triangle]))
            faces.append(("top", [(1, j) for j in reversed(triangle)]))
        for i in range(len(ring)):
            j = (i + 1) % len(ring)
            faces.append(("side", [(0, i), (1, i), (1, j), (0, j)]))
        expected_faces += len(faces)
        for kind, indices in faces:
            # The closed solid's mathematical winding must be reversed for
            # Houdini fronts; _normal uses the same outward convention.
            face_points = [vertices[row][column] for row, column in reversed(indices)]
            world = [tuple(p.position()) for p in face_points]
            try:
                normal = _normal(world)
            except ValueError:
                # v006: a zero-area generated face adds nothing to the closed shell.
                expected_faces -= 1
                degenerate_faces += 1
                continue
            polygon = geo.createPolygon()
            for point, position in zip(face_points, world):
                vertex = polygon.addVertex(point)
                vertex.setAttribValue(v_n, normal)
                if kind == "side":
                    # Physical metres per tile. Side UVs follow the face's edge.
                    a = world[0]
                    edge = math.hypot(world[-1][0] - a[0], world[-1][2] - a[2])
                    along = math.hypot(position[0] - a[0], position[2] - a[2])
                    vertex.setAttribValue(v_uv, (min(along, edge), position[1] - bottom, 0.0))
                else:
                    vertex.setAttribValue(v_uv, (position[0], position[2], 0.0))
            for key, attr in p_str.items():
                value = (part["part_id"] if key == "part_id" else
                         part["role"] if key == "role" else
                         kind if key == "face_kind" else
                         record["source_feature"]["area_id"] if key == "source_area_id" else
                         record["source_feature"]["osm_id"] if key == "source_osm_id" else
                         part["material_path"] if key == "unreal_material" else
                         output_name)
                polygon.setAttribValue(attr, value)
            polygon.setAttribValue(p_floor, part["floor"])
    if len(geo.prims()) != expected_faces:
        raise AssertionError("generated_face_count_mismatch")
    if degenerate_faces:
        if geo.findGlobalAttrib('degenerate_generated_faces') is None:
            geo.addAttrib(hou.attribType.Global, 'degenerate_generated_faces', 0)
        geo.setGlobalAttribValue('degenerate_generated_faces', degenerate_faces)
    return geo


def wall_points_geometry(record):
    geo = hou.Geometry()
    geo.setPreferredPrecision(64)
    names = ("placement_id", "id", "unreal_split_attr", "unreal_instance",
             "source_area_id", "source_osm_id", "source_wall_sha256")
    attrs = {key: geo.addAttrib(hou.attribType.Point, key, "") for key in names}
    number = {key: geo.addAttrib(hou.attribType.Point, key, 0) for key in ("floor", "edge_index", "slot")}
    orient = geo.addAttrib(hou.attribType.Point, "orient", (0.0, 0.0, 0.0, 1.0))
    scale = geo.addAttrib(hou.attribType.Point, "scale", (1.0, 1.0, 1.0))
    for wall in record["wall_placements"]:
        point = geo.createPoint()
        point.setPosition(wall["P"])
        for key, attr in attrs.items():
            point.setAttribValue(attr, wall[key])
        for key, attr in number.items():
            point.setAttribValue(attr, wall[key])
        point.setAttribValue(orient, wall["orient"])
        point.setAttribValue(scale, (1.0, 1.0, 1.0))
    return geo


def placed_wall_geometry(record, source_path):
    source = hou.Geometry()
    source.loadFromFile(str(source_path))
    if sha(source_path) != record["wall_contract"]["sha256"]:
        raise ValueError("native_wall_changed_before_geometry_placement")
    output = hou.Geometry()
    output.setPreferredPrecision(64)
    for wall in record["wall_placements"]:
        copy = hou.Geometry()
        copy.merge(source)
        rotation = wall["rotation"]
        origin = wall["P"]
        for point in copy.points():
            local = point.position()
            point.setPosition(tuple(origin[i] + sum(rotation[i][j] * local[j]
                                                    for j in range(3)) for i in range(3)))
        attr = copy.addAttrib(hou.attribType.Prim, "placement_id", "")
        for prim in copy.prims():
            prim.setAttribValue(attr, wall["placement_id"])
        output.merge(copy)
    return output


def validate_generated_manifold(geo, record):
    groups = {}
    for prim in geo.prims():
        groups.setdefault(prim.attribValue("part_id"), []).append(prim)
    if len(groups) != len(record["generated_parts"]):
        raise AssertionError("generated_part_count_mismatch")
    minimum_normal_alignment = 1.0
    max_metric_uv_error = 0.0
    for part_id, prims in groups.items():
        incidences = Counter()
        for prim in prims:
            verts = list(prim.vertices())
            positions = [v.point().position() for v in verts]
            actual = hou.Vector3(_normal(positions))
            for vertex in verts:
                assigned = hou.Vector3(vertex.attribValue("N"))
                cosine = actual.dot(assigned)
                if cosine < 0.999999:
                    raise AssertionError("generated_normal_not_aligned")
                minimum_normal_alignment = min(minimum_normal_alignment, cosine)
            for a, b in zip(verts, verts[1:] + verts[:1]):
                key = tuple(sorted((a.point().number(), b.point().number())))
                incidences[key] += 1
                if prim.attribValue("face_kind") == "side":
                    world = (a.point().position() - b.point().position()).length()
                    uv_a, uv_b = hou.Vector3(a.attribValue("uv")), hou.Vector3(b.attribValue("uv"))
                    uv_length = (uv_a - uv_b).length()
                    max_metric_uv_error = max(max_metric_uv_error, abs(world - uv_length))
        if set(incidences.values()) != {2}:
            raise AssertionError("generated_part_nonmanifold:" + part_id)
    return {"closed_manifold_parts": len(groups),
            "polygons": len(geo.prims()), "points": len(geo.points()),
            "minimum_normal_alignment_cosine": minimum_normal_alignment,
            "max_side_uv_metric_error_m": max_metric_uv_error}


def evaluate_pad(path, wall_path, policy, *, area_id=None, osm_id=None):
    features = read_features(path)
    selected = [f for f in features if (area_id is None or f["area_id"] == area_id)
                and (osm_id is None or f["osm_id"] == osm_id)]
    wall = wall_contract(wall_path)
    return [evaluate_feature(feature, wall, policy) for feature in selected]


MODULAR_WALL_CONTRACT = {'source_file': 'C:\\Users\\USER\\Downloads\\BuildGenSingleProof_20261001\\proof_geo\\SM_wall_windows_4x4_01.bgeo.sc', 'sha256': '77d39bc71083da528bd5cd8bab2fc24a565422d82975dbea3acceff238a0ec5b', 'mesh_ref': "StaticMesh'/Game/ModularCourtyard/Meshes/SM_wall_windows_4x4_01.SM_wall_windows_4x4_01'", 'pitch_m': 4.000000209808377, 'height_m': 4.0, 'thickness_m': 0.49999561190605846, 'start_connector_local_m': [3.0517577442878974e-07, 7.474651452296133e-23, -1.220703097715159e-06], 'start_x_min_m': 3.0517577442878974e-07, 'start_x_max_m': 0.4999959170818329, 'end_x_min_m': 3.0517577442878974e-07, 'end_x_max_m': 0.4999959170818329, 'start_end_sections': [{'x_min_m': 3.0517577442878974e-07, 'x_max_m': 0.4999959170818329, 'y_min_m': 7.474651452296133e-23, 'y_max_m': 4.0, 'z_m': -1.220703097715159e-06, 'point_count': 4}, {'x_min_m': 3.0517577442878974e-07, 'x_max_m': 0.4999959170818329, 'y_min_m': 2.4492942345659277e-16, 'y_max_m': 4.0, 'z_m': -4.000001430511475, 'point_count': 4}], 'points': 480, 'primitives': 656, 'uv_present': True, 'normal_present': True, 'material_paths': {'[0]/Game/ModularCourtyard/Mats/MI_Wall_PlasterBrick.MI_Wall_PlasterBrick': 60, '[1]/Game/ModularCourtyard/Mats/Masters/M_windows_balkon.M_windows_balkon': 536, '[2]/Game/ModularCourtyard/Mats/MI_Glass_2.MI_Glass_2': 24, '[3]/Game/ModularCourtyard/Mats/Masters/M_EdgeDecal.M_EdgeDecal': 36}}

MODULAR_POLICY = {'schema': 'modular_layout_measured_interface_policy_v004', 'angle_min_degrees': 75.0, 'angle_max_degrees': 105.0, 'junction_margin_m': 0.01, 'max_residual_width_m': 1.0, 'slab_thickness_m': 0.2, 'max_seeded_height_delta_m': 1.0, 'max_seeded_height_delta_fraction': 0.1, 'generated_material_path': '/Game/ModularCourtyard/Mats/MI_Wall_PlasterBrick.MI_Wall_PlasterBrick', 'generated_material_basis': 'material slot 0 from genuine SM_wall_windows_4x4_01 Node Sync geometry', 'native_corner_mode': 'unbound_pending_genuine_export_and_angle_fit', 'door_mode': 'unresolved_pending_measured_entrance_bay', 'proof_scope': 'isolated_technical_candidate_no_catalog_release'}

# GeoCity modular pilot bridge
"""Versioned technical bridge from GeoCity pads to the measured modular pilot.

This source is embedded in the HDA PythonModule by build_v009.py. The pilot
requires the full disabled native catalog and emits one explicitly selected
building. It does not release any catalog row or claim a complete building.
"""


def _modular_guard(parent, guard):
    if not parent.evalParm('modular_pilot_enabled'):
        return
    if (not parent.evalParm('bank_inspection_only') or
            parent.evalParm('bank_release_enabled') or
            parent.evalParm('bank_pilot_enabled') or
            parent.evalParm('module_test_enabled') or
            parent.evalParm('catalog_release_id').strip() or
            parent.evalParm('bank_style_set').strip()):
        _fail('Modular technical pilot requires inspection mode and no bank release or other pilot')
    chosen = parent.evalParm('modular_pilot_mesh_ref').strip()
    if chosen != MODULAR_WALL_CONTRACT['mesh_ref']:
        _fail('Modular wall picker differs from the measured native wall contract')
    if guard is None or guard.findGlobalAttrib('bank_catalog_readback_json') is None:
        _fail('Modular pilot requires the native DataTable catalog guard')
    try:
        readback = json.loads(guard.attribValue('bank_catalog_readback_json'))
    except (ValueError, TypeError) as exc:
        _fail('Modular catalog readback is invalid: ' + str(exc))
    digest = readback.get('catalog_sha256')
    expected = parent.evalParm('catalog_expected_sha256').strip().lower()
    if (readback.get('schema_version') != 2 or
            len(readback.get('rows', [])) != 1215 or
            len(readback.get('rejected', [])) != 1215 or
            readback.get('eligible_count') != 0 or
            readback.get('instances') or guard.points() or
            not digest or digest != expected):
        _fail('Modular pilot requires 1,215 disabled native rows, zero instances and matching digest')


def _modular_feature(parent, pads):
    if pads is None:
        _fail('Modular pilot requires geographic building pads')
    for name in ('source_area_id', 'source_osm_id', 'base_m', 'height_m', 'height_rule'):
        if pads.findPrimAttrib(name) is None:
            _fail('Modular building pads lack ' + name)
    target = parent.evalParm('modular_target_osm_id').strip()
    if not target:
        _fail('Modular pilot requires an explicit target OSM ID')
    matches = [p for p in pads.prims()
               if str(p.attribValue('source_osm_id')) == target]
    if len(matches) != 1:
        _fail('Modular pilot expected one target pad; found %d' % len(matches))
    pad = matches[0]
    if pad.type() != hou.primType.Polygon or not pad.isClosed():
        _fail('Modular target pad must be one closed polygon')
    return {
        'area_id': str(pad.attribValue('source_area_id')),
        'osm_id': target,
        'ring_xyz_m': [list(v.point().position()) for v in pad.vertices()],
        'base_m': float(pad.attribValue('base_m')),
        'source_height_m': float(pad.attribValue('height_m')),
        'height_rule': str(pad.attribValue('height_rule')),
        'closed': True,
        'holes': bool(pad.attribValue('has_holes'))
            if pads.findPrimAttrib('has_holes') else False,
        'source_sha256': hashlib.sha256(
            Path(parent.evalParm('package_file').strip()).read_bytes()).hexdigest(),
    }


def _modular_record(parent, pads):
    feature = _modular_feature(parent, pads)
    try:
        record = evaluate_feature(feature, MODULAR_WALL_CONTRACT, MODULAR_POLICY)
    except (ValueError, TypeError, ArithmeticError) as exc:
        _fail('Modular layout rejected target pad: ' + str(exc))
    if record['unsupported'] or not record['wall_placements'] or not record['generated_parts']:
        _fail('Modular layout has unsupported conditions: ' + ','.join(record['unsupported']))
    return record


def _modular_summary(record):
    roles = {}
    for part in record['generated_parts']:
        roles[part['role']] = roles.get(part['role'], 0) + 1
    return {
        'status': record['status'],
        'feature_id': record['feature_id'],
        'contract_id': record['contract_id'],
        'source_height_m': record['source_feature']['source_height_m'],
        'height_rule': record['source_feature']['height_rule'],
        'output_height_m': record['output_height_m'],
        'height_delta_m': record['height_delta_m'],
        'floors': record['floors'],
        'wall_count': len(record['wall_placements']),
        'generated_role_counts': roles,
        'wall_mesh_ref': MODULAR_WALL_CONTRACT['mesh_ref'],
        'wall_export_sha256': MODULAR_WALL_CONTRACT['sha256'],
        'native_corner_status': record['native_corner_candidate_status'],
        'door_status': record['door_status'],
        'building_complete': False,
        'catalog_release': False,
        'edge_ledger': record['edge_ledger'],
    }


def cook_modular_generated_buildings(node):
    parent, geo = node.parent(), node.geometry()
    geo.clear()
    if not parent.evalParm('modular_pilot_enabled'):
        return
    guard, pads = (input_node.geometry() for input_node in node.inputs()[:2])
    _modular_guard(parent, guard)
    record = _modular_record(parent, pads)
    geo.merge(generated_geometry(record))
    _set_detail(geo, 'modular_pilot_readback_json',
                json.dumps(_modular_summary(record), sort_keys=True, allow_nan=False))


def cook_modular_wall_points(node):
    parent, geo = node.parent(), node.geometry()
    geo.clear()
    guard, pads = (input_node.geometry() for input_node in node.inputs()[:2])
    if not parent.evalParm('modular_pilot_enabled'):
        geo.merge(guard)
        return
    _modular_guard(parent, guard)
    record = _modular_record(parent, pads)
    geo.merge(guard)
    geo.merge(wall_points_geometry(record))
    _set_detail(geo, 'modular_pilot_readback_json',
                json.dumps(_modular_summary(record), sort_keys=True, allow_nan=False))
    report = parent.evalParm('modular_receipt_file').strip()
    if report:
        Path(report).write_text(json.dumps(record, indent=2, sort_keys=True,
                                          allow_nan=False), encoding='utf-8')



"""GeoCity v011 native DataTable v3 nonbuilding route.

This module is appended to the preserved v009 PythonModule. Its new runtime
input is the native Unreal DataTable on Geometry Input 0. The v3 fields are a
projection of one versioned catalog source; no CSV or JSON is read at cook time.
"""

NONBUILDING_V3_EXTRA = (
    'RequestRole', 'PlacementRule', 'TechnicalPreviewEligible', 'ExplicitHold',
    'PreviewWeight', 'MinSpacingCm', 'PreviewAllowedPlacementIds', 'HoldReasons',
)
NONBUILDING_V3_FIELDS = tuple(BANK_V2_FIELDS) + NONBUILDING_V3_EXTRA
NONBUILDING_RULES = {
    'tree': 'terrain_tree',
    'shrub': 'terrain_shrub',
    'understory': 'terrain_understory',
    'street_pole': 'roadside_pole',
    'street_prop': 'roadside_prop',
    'small_prop': 'zone_ground_prop',
    'sign': 'mount_sign',
    'rooftop_utility': 'roof_anchor',
}
NONBUILDING_PREVIEW_FLAGS = ('TechnicalPreviewEligible', 'ExplicitHold')
NONBUILDING_V3_FLOATS = set(BANK_NUMBERS) | {
    'SelectionWeight', 'PreviewWeight', 'MinSpacingCm',
}
NONBUILDING_V3_INTS = set(BANK_FLAGS) | {
    'SchemaVersion', 'TechnicalPreviewEligible', 'ExplicitHold',
}
_nonbuilding_original_parse = bank_parse_versioned


def _nonbuilding_v3_rows(table):
    names = {attribute.name() for attribute in table.pointAttribs()}
    numbered = {name for name in names
                if re.fullmatch(r'unreal_data_table_\d+_.+', name)}
    expected = {'unreal_data_table_%d_%s' % (index, field)
                for index, field in enumerate(NONBUILDING_V3_FIELDS, 1)}
    if numbered != expected or 'unreal_data_table_rowname' not in names:
        _fail('Nonbuilding bank requires the exact native v3 DataTable layout')
    for index, field in enumerate(NONBUILDING_V3_FIELDS, 1):
        attribute = table.findPointAttrib('unreal_data_table_%d_%s' % (index, field))
        expected_type = (hou.attribData.Int if field in NONBUILDING_V3_INTS else
                         hou.attribData.Float if field in NONBUILDING_V3_FLOATS else
                         hou.attribData.String)
        if attribute is None or attribute.dataType() != expected_type or attribute.size() != 1:
            _fail('Nonbuilding native v3 field type differs: ' + field)
    rows, seen_names, seen_assets, seen_paths = [], set(), set(), set()
    for point in table.points():
        row = {field: point.attribValue('unreal_data_table_%d_%s' % (index, field))
               for index, field in enumerate(NONBUILDING_V3_FIELDS, 1)}
        row['Name'] = point.attribValue('unreal_data_table_rowname')
        if int(row['SchemaVersion']) != 3 or not row['Name'] or not row['AssetId']:
            _fail('Nonbuilding v3 row has invalid schema or identity')
        if (row['Name'] in seen_names or row['AssetId'] in seen_assets or
                (row['ObjectPath'] and row['ObjectPath'] in seen_paths)):
            _fail('Nonbuilding v3 has duplicate row, AssetId or ObjectPath')
        seen_names.add(row['Name'])
        seen_assets.add(row['AssetId'])
        if row['ObjectPath']:
            seen_paths.add(row['ObjectPath'])
        for field in NONBUILDING_PREVIEW_FLAGS + ('RunEligible',):
            if int(row[field]) not in (0, 1):
                _fail('Nonbuilding v3 flag is not Boolean: ' + field)
        role, rule = row['RequestRole'], row['PlacementRule']
        if (role or rule) and NONBUILDING_RULES.get(role) != rule:
            _fail('Nonbuilding row role/rule pair is unsupported: ' + row['AssetId'])
        if (int(row['TechnicalPreviewEligible']) and
                (not role or not row['ObjectPath'] or int(row['ExplicitHold']))):
            _fail('Preview row lacks role/path or has an explicit hold: ' + row['AssetId'])
        if (float(row['PreviewWeight']) < 0 or float(row['MinSpacingCm']) < 0 or
                not math.isfinite(float(row['PreviewWeight'])) or
                not math.isfinite(float(row['MinSpacingCm']))):
            _fail('Nonbuilding v3 weight or spacing is invalid')
        if row['PreviewAllowedPlacementIds']:
            bank_v2_tokens(row['PreviewAllowedPlacementIds'], 'PreviewAllowedPlacementIds')
        rows.append(row)
    if len(rows) < 1215:
        _fail('Nonbuilding bank is missing rows from the 1,215-row baseline')
    return sorted(rows, key=lambda row: row['Name'])


def bank_parse_versioned(table):
    """Project v3 to the preserved v2 selector without releasing a v3 row."""
    names = {attribute.name() for attribute in table.pointAttribs()}
    if 'unreal_data_table_28_RequestRole' not in names:
        return _nonbuilding_original_parse(table)
    rows = _nonbuilding_v3_rows(table)
    projected = []
    for row in rows:
        old = {field: row[field] for field in BANK_V2_FIELDS}
        old['SchemaVersion'] = 2
        old['Name'] = row['Name']
        projected.append(old)
    attributes = {attribute.name(): {
        'type': str(attribute.dataType()),
        'storage': (str(attribute.numericDataType())
                    if attribute.dataType() != hou.attribData.String else 'String'),
        'size': attribute.size(),
    } for attribute in table.pointAttribs()}
    return projected, attributes, 2


def _nonbuilding_active_rows(parent, rows):
    if parent.evalParm('technical_preview_enabled'):
        if (parent.evalParm('bank_release_enabled') or
                parent.evalParm('catalog_release_id').strip() or
                parent.evalParm('bank_style_set').strip()):
            _fail('Technical preview cannot share a catalog release')
        return [row for row in rows if int(row['TechnicalPreviewEligible']) == 1
                and int(row['ExplicitHold']) == 0]
    if not parent.evalParm('bank_release_enabled'):
        return []
    projected = []
    for row in rows:
        if row['RequestRole'] in SURFACE_ROLES:
            continue
        old = {field: row[field] for field in BANK_V2_FIELDS}
        old['SchemaVersion'] = 2
        old['Name'] = row['Name']
        projected.append(old)
    eligible, _ = bank_evaluate_v2(projected, parent.evalParm('catalog_release_id').strip())
    ids = {row['AssetId'] for row in eligible}
    held_enabled = [row['AssetId'] for row in rows if row['AssetId'] in ids and
                    (int(row['ExplicitHold']) or row['HoldReasons'])]
    if held_enabled:
        _fail('Released nonbuilding rows retain an explicit hold: ' +
              ', '.join(held_enabled))
    released = [row for row in rows if row['AssetId'] in ids and
                int(row['RunEligible']) == 1]
    unrouteable = [row['AssetId'] for row in released if
                   NONBUILDING_RULES.get(row['RequestRole']) != row['PlacementRule']]
    if unrouteable:
        _fail('Released rows lack a nonbuilding role and rule: ' +
              ', '.join(unrouteable))
    return released + _permanent_surface_rows(parent, rows)


def cook_nonbuilding_catalog_guard(node):
    """Read only the native v3 DataTable; keep the legacy picker out of v011."""
    parent, geo = node.parent(), node.geometry()
    geo.clear()
    if parent.evalParm('catalog_file').strip():
        _fail('Nonbuilding catalog requires native DataTable input 0')
    if (parent.evalParm('bank_pilot_enabled') or
            parent.evalParm('module_test_enabled') or
            parent.evalParm('modular_pilot_enabled')):
        _fail('Legacy technical pilots cannot share the v3 nonbuilding route')
    table = node.inputs()[0].geometry()
    rows = _nonbuilding_v3_rows(table)
    canonical = json.dumps(rows, sort_keys=True, separators=(',', ':'),
                           allow_nan=False)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    expected = parent.evalParm('catalog_expected_sha256').strip().lower()
    if expected and (not re.fullmatch(r'[a-f0-9]{64}', expected) or
                     expected != digest):
        _fail('Native v3 DataTable digest differs from recorded release digest')
    preview = bool(parent.evalParm('technical_preview_enabled'))
    release_enabled = bool(parent.evalParm('bank_release_enabled'))
    release_id = parent.evalParm('catalog_release_id').strip()
    style_set = parent.evalParm('bank_style_set').strip()
    if preview and (release_enabled or release_id or style_set or
                    any(int(row['RunEligible']) for row in rows)):
        _fail('Technical preview requires the all-disabled catalog and no release')
    active = _nonbuilding_active_rows(parent, rows)
    if release_enabled:
        if (not release_id or not style_set or not expected or
                parent.evalParm('bank_inspection_only') or not active):
            _fail('Release requires decision, style, v3 digest and eligible rows')
    elif any(int(row['RunEligible']) for row in rows):
        _fail('Enabled nonbuilding rows require the release switch')
    requests = node.inputs()[1].geometry()
    request_roles = {}
    for point in requests.points():
        role = point.attribValue('bank_role')
        request_roles[role] = request_roles.get(role, 0) + 1
    receipt = {
        'interface': 'GeoCity nonbuilding bank v3', 'schema_version': 3,
        'rows': rows, 'catalog_sha256': digest, 'expected_catalog_sha256': expected,
        'release_enabled': release_enabled, 'release_id': release_id,
        'style_set': style_set, 'technical_preview_enabled': preview,
        'eligible_count': len(active) if release_enabled else 0,
        'preview_candidate_count': len(active) if preview else 0,
        'request_count': len(requests.points()), 'request_roles': request_roles,
        'instances': [], 'houdini': hou.applicationVersionString(),
        'pid': os.getpid(),
    }
    _set_detail(geo, 'bank_catalog_readback_json',
                json.dumps(receipt, sort_keys=True))
    _set_detail(geo, 'bank_catalog_sha256', digest)
    _set_detail(geo, 'catalog_rows_disabled',
                sum(not int(row['RunEligible']) for row in rows))
    _set_detail(geo, 'bank_instances', 0)
    _set_detail(geo, 'bank_request_count', len(requests.points()))
    _set_detail(geo, 'bank_request_roles_json',
                json.dumps(request_roles, sort_keys=True))
    _set_detail(geo, 'unreal_output_name', 'bank_instances')


def _nonbuilding_ground_ok(x, z, road_mask, pad_mask, steep, box):
    xmin, xmax, zmin, zmax = box
    if not (xmin + 2 < x < xmax - 2 and zmin + 2 < z < zmax - 2):
        return False
    col, row = int(round(x + 2016)), int(round(z + 2016))
    if not (0 <= row < GRID_SAMPLES and 0 <= col < GRID_SAMPLES):
        return False
    return road_mask[row, col] == 0 and pad_mask[row, col] == 0 and steep[row, col] <= 0.3


def _nonbuilding_add_request(geo, attrs, position, values):
    point = geo.createPoint()
    point.setPosition(position)
    for name, attribute in attrs.items():
        point.setAttribValue(attribute, values.get(name, 0.0 if name == 'bank_yaw_degrees' else ''))


class _PlacementPosition:
    """Read an existing request at another candidate ground anchor."""
    def __init__(self, request, position, attributes=None):
        self.request = request
        self._position = tuple(position)
        self.attributes = attributes or {}

    def position(self):
        return self._position

    def attribValue(self, name):
        return self.attributes[name] if name in self.attributes else self.request.attribValue(name)

    def geometry(self):
        return self.request.geometry()


def _roadside_near_road(x, z, roads, distance_m=6.0):
    col, row = int(round(x + 2016)), int(round(z + 2016))
    radius = int(math.ceil(distance_m))
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx*dx + dy*dy > distance_m*distance_m:
                continue
            r, c = row + dy, col + dx
            if 0 <= r < GRID_SAMPLES and 0 <= c < GRID_SAMPLES and roads[r, c] > 0:
                return True
    return False


def _roadside_search(node, anchor, rows, fit, seed, role='street_prop'):
    """Find nearby full-footprint anchors; never alter roads or native dimensions."""
    detail = (anchor.attribValue('source_detail_id') if role == 'street_pole' else
              'streetprop_' + anchor.attribValue('source_detail_id'))
    base = tuple(float(v) for v in anchor.position())
    yaw = float(anchor.attribValue('bank_yaw_degrees'))
    theta = math.radians(yaw)
    tangent, normal = (math.cos(theta), math.sin(theta)), (-math.sin(theta), math.cos(theta))
    spans = []
    for row in rows:
        x = (float(row['BoundsMaxXCm']) - float(row['BoundsMinXCm'])) / 100.0
        z = (float(row['BoundsMaxYCm']) - float(row['BoundsMinYCm'])) / 100.0
        spans.append((z, x) if row['ForwardAxis'] in ('+Y', '-Y') else (x, z))
    along_step = max(2.0, max((x/2.0 + 1.0 for x, z in spans), default=2.0))
    side_step = max(1.0, max((z/2.0 + 1.0 for x, z in spans), default=1.0))
    offsets = [(i*along_step, j*side_step) for i in (0, 1, -1, 2, -2)
               for j in (0, 1, -1, 2, -2, 3, -3)
               if math.hypot(i*along_step, j*side_step) <= 12.0]
    offsets.sort(key=lambda p: (p[0]*p[0]+p[1]*p[1],
                               _stable_fraction(seed, detail, p[0], p[1])))
    attributes = {'bank_role': role, 'placement_rule': NONBUILDING_RULES[role],
                  'bank_yaw_degrees': yaw, 'bank_zone': 'roadside',
                  'source_area_id': anchor.attribValue('source_area_id')}
    state = {'source_detail_id': anchor.attribValue('source_detail_id'),
             'source_osm_id': anchor.attribValue('source_osm_id'),
             'derived_detail_id': detail, 'role': role, 'source_anchor_m': base,
             'policy': 'selected_native_dimensions_full_ground_masks_nearby_roadside',
             'max_anchor_distance_m': 12.0, 'candidate_asset_ids': [r['AssetId'] for r in rows],
             'position_evaluations': 0, 'rejection_reasons': {}, 'valid_positions': []}
    if not rows:
        state['rejection_reasons']['no_active_compatible_candidate'] = 1
        state['result'] = 'no_fitting_roadside_anchor'
        return state
    for along, side in offsets:
        x = base[0] + along*tangent[0] + side*normal[0]
        z = base[2] + along*tangent[1] + side*normal[1]
        state['position_evaluations'] += 1
        if not _roadside_near_road(x, z, fit['roads']):
            reason = 'no_nearby_road'
            state['rejection_reasons'][reason] = state['rejection_reasons'].get(reason, 0) + 1
            continue
        y = float(_sample_grid(fit['height'], [x], [z])[0])
        request = _PlacementPosition(anchor, (x, y, z), attributes)
        fitting = []
        for row in rows:
            reason = _permanent_candidate_rejection(node, row, request, fit)
            if reason:
                state['rejection_reasons'][reason] = state['rejection_reasons'].get(reason, 0) + 1
            else:
                fitting.append(row['AssetId'])
        if fitting:
            state['valid_positions'].append({'P': [x, y, z], 'fitting_asset_ids': fitting})
    state['result'] = 'requests_available' if state['valid_positions'] else 'no_fitting_roadside_anchor'
    return state


def _generated_tree_seed_cell(request, node):
    geo = request.geometry()
    if (node is None or request.attribValue('bank_role') != 'tree' or
            geo.findPointAttrib('source_osm_id') is None or request.attribValue('source_osm_id') or
            geo.findPointAttrib('request_origin') is None or
            request.attribValue('request_origin') != 'geographic_tree'):
        return None
    match = re.fullmatch(r'tree_(-?\d+)_(-?\d+)', str(request.attribValue('source_detail_id')))
    if match is None:
        return None
    spacing = float(node.parent().evalParm('vegetation_spacing_m'))
    if not math.isfinite(spacing) or not 8.0 <= spacing <= 80.0:
        return None
    ix, iz = (int(value) for value in match.groups())
    return (ix*spacing, (ix+1)*spacing, iz*spacing, (iz+1)*spacing)


def _permanent_request_positions(request, node=None, fit=None):
    geo = request.geometry()
    cell = _generated_tree_seed_cell(request, node)
    if cell is not None and fit is not None:
        source = tuple(float(v) for v in request.position())
        seed = int(node.parent().evalParm('seed'))
        offsets = [(x/2.0, z/2.0) for x in range(-4, 5) for z in range(-4, 5)
                   if 0 < x*x+z*z <= 16]
        offsets.sort(key=lambda p: (p[0]*p[0]+p[1]*p[1],
                                   _stable_fraction(seed, request.attribValue('source_detail_id'), p[0], p[1])))
        positions = [request]
        for dx, dz in offsets:
            x, z = source[0]+dx, source[2]+dz
            if cell[0] <= x <= cell[1] and cell[2] <= z <= cell[3]:
                y = float(_sample_grid(fit['height'], [x], [z])[0])
                positions.append(_PlacementPosition(request, (x, y, z)))
        return positions
    if (request.attribValue('bank_role') not in ('street_prop', 'street_pole') or
            geo.findPointAttrib('roadside_search_positions_json') is None):
        return [request]
    raw = request.attribValue('roadside_search_positions_json')
    if not raw:
        return [request]
    return [_PlacementPosition(request, item['P']) for item in json.loads(raw)]


def cook_nonbuilding_requests(node):
    """Derive stable role anchors from GeoCity trees, roads, terrain and pads."""
    parent, geo = node.parent(), node.geometry()
    source, terrain, pads, table = (item.geometry() for item in node.inputs()[:4])
    geo.clear()
    geo.merge(source)
    rule_attr = geo.findPointAttrib('placement_rule') or geo.addAttrib(
        hou.attribType.Point, 'placement_rule', '')
    for point in geo.points():
        rule = {'tree': 'terrain_tree', 'street_pole': 'roadside_pole'}.get(
            point.attribValue('bank_role'), '')
        point.setAttribValue(rule_attr, rule)
    if (not parent.evalParm('nonbuilding_enabled') or
            parent.evalParm('bank_inspection_only')):
        return
    rows = _nonbuilding_v3_rows(table)
    active = _nonbuilding_active_rows(parent, rows)
    active_rules = {row['PlacementRule'] for row in active}
    if not active_rules:
        return
    attrs = {name: geo.findPointAttrib(name) or geo.addAttrib(
        hou.attribType.Point, name, 0.0 if name == 'bank_yaw_degrees' else '')
        for name in ('placement_id', 'bank_role', 'placement_rule', 'bank_yaw_degrees',
                     'source_area_id', 'source_osm_id', 'source_detail_id', 'request_origin')}
    info = _package_for_sop(parent)
    box = _local_box(info)
    height = _grid_array(_volume(terrain, 'height'))
    roads = _exclusion_mask(terrain, 'RoadBed', 2)
    buildings = _exclusion_mask(terrain, 'BuildingPad', 2)
    steep = _grid_array(_volume(terrain, 'Steep'))
    seed = int(parent.evalParm('seed'))
    originals = list(source.points())
    tree_anchors = [point for point in originals if point.attribValue('bank_role') == 'tree']
    pole_anchors = [point for point in originals if point.attribValue('bank_role') == 'street_pole']
    counts = {'terrain_shrub': 0, 'terrain_understory': 0, 'roadside_prop': 0,
              'zone_ground_prop': 0, 'mount_sign': 0, 'roof_anchor': 0}

    for rule, role, radius, anchors in (
            ('terrain_shrub', 'shrub', 3.0, tree_anchors),
            ('terrain_understory', 'understory', 5.0, tree_anchors)):
        if rule not in active_rules:
            continue
        for anchor in anchors:
            base = anchor.attribValue('placement_id')
            angle = 2 * math.pi * _stable_fraction(seed, base, rule)
            x = float(anchor.position()[0]) + radius * math.cos(angle)
            z = float(anchor.position()[2]) + radius * math.sin(angle)
            if not _nonbuilding_ground_ok(x, z, roads, buildings, steep, box):
                continue
            detail = rule + '_' + anchor.attribValue('source_detail_id')
            yaw = 360.0 * _stable_fraction(seed, base, rule, 'yaw')
            _nonbuilding_add_request(geo, attrs,
                (x, float(_sample_grid(height, [x], [z])[0]), z), {
                    'placement_id': info['area_id'] + ':' + detail, 'bank_role': role,
                    'placement_rule': rule, 'bank_yaw_degrees': yaw,
                    'source_area_id': info['area_id'], 'source_detail_id': detail,
                    'request_origin': 'geographic_nonbuilding'})
            counts[rule] += 1

    if 'roadside_prop' in active_rules:
        roadside_rows = [row for row in active if row['RequestRole'] == 'street_prop'
                         and row['PlacementRule'] == 'roadside_prop' and int(row['BoundsValid'])
                         and _permanent_context_matches(parent, row, info['area_id'], 'roadside')]
        for name in ('roadside_search_positions_json', 'roadside_search_json'):
            attrs[name] = geo.findPointAttrib(name) or geo.addAttrib(hou.attribType.Point, name, '')
        roadside_fit = {'box': box, 'height': height, 'steep': steep,
                        'roads': _exclusion_mask(terrain, 'RoadBed', 1),
                        'pads': _exclusion_mask(terrain, 'BuildingPad', 1)}
        roadside_ledger = []
        for anchor in pole_anchors:
            search = _roadside_search(node, anchor, roadside_rows, roadside_fit, seed)
            roadside_ledger.append(search)
            if not search['valid_positions']:
                continue
            detail = 'streetprop_' + anchor.attribValue('source_detail_id')
            _nonbuilding_add_request(geo, attrs,
                search['valid_positions'][0]['P'], {
                    'placement_id': info['area_id'] + ':' + detail,
                    'bank_role': 'street_prop', 'placement_rule': 'roadside_prop',
                    'bank_yaw_degrees': anchor.attribValue('bank_yaw_degrees'),
                    'source_area_id': info['area_id'],
                    'source_osm_id': anchor.attribValue('source_osm_id'),
                    'source_detail_id': detail,
                    'request_origin': 'geographic_nonbuilding',
                    'roadside_search_positions_json': json.dumps(search['valid_positions']),
                    'roadside_search_json': json.dumps(search, sort_keys=True)})
            counts['roadside_prop'] += 1
        _set_detail(geo, 'roadside_request_search_json', json.dumps(roadside_ledger, sort_keys=True))

    if 'roadside_pole' in active_rules:
        pole_rows = [row for row in active if row['RequestRole'] == 'street_pole'
                     and row['PlacementRule'] == 'roadside_pole' and int(row['BoundsValid'])
                     and _permanent_context_matches(parent, row, info['area_id'], 'roadside')]
        for name in ('roadside_search_positions_json', 'roadside_search_json'):
            attrs[name] = geo.findPointAttrib(name) or geo.addAttrib(hou.attribType.Point, name, '')
        pole_fit = {'box': box, 'height': height, 'steep': steep,
                    'roads': _exclusion_mask(terrain, 'RoadBed', 1),
                    'pads': _exclusion_mask(terrain, 'BuildingPad', 1)}
        pole_ledger = []
        for anchor in [point for point in geo.points() if point.attribValue('bank_role') == 'street_pole']:
            search = _roadside_search(node, anchor, pole_rows, pole_fit, seed, 'street_pole')
            pole_ledger.append(search)
            anchor.setAttribValue(attrs['roadside_search_json'], json.dumps(search, sort_keys=True))
            if search['valid_positions']:
                anchor.setAttribValue(attrs['roadside_search_positions_json'], json.dumps(search['valid_positions']))
        existing = (json.loads(geo.attribValue('roadside_request_search_json'))
                    if geo.findGlobalAttrib('roadside_request_search_json') is not None else [])
        _set_detail(geo, 'roadside_request_search_json', json.dumps(existing + pole_ledger, sort_keys=True))

    if 'zone_ground_prop' in active_rules:
        spacing = max(12.0, float(parent.evalParm('vegetation_spacing_m')))
        xmin, xmax, zmin, zmax = box
        for ix in range(math.floor(xmin / spacing), math.ceil(xmax / spacing)):
            for iz in range(math.floor(zmin / spacing), math.ceil(zmax / spacing)):
                if _stable_fraction(info['area_id'], seed, ix, iz, 'ground_keep') > 0.25:
                    continue
                x, z = (ix + 0.5) * spacing, (iz + 0.5) * spacing
                if not _nonbuilding_ground_ok(x, z, roads, buildings, steep, box):
                    continue
                detail = 'groundprop_%d_%d' % (ix, iz)
                _nonbuilding_add_request(geo, attrs,
                    (x, float(_sample_grid(height, [x], [z])[0]), z), {
                        'placement_id': info['area_id'] + ':' + detail,
                        'bank_role': 'small_prop', 'placement_rule': 'zone_ground_prop',
                        'bank_yaw_degrees': 360.0 * _stable_fraction(seed, detail, 'yaw'),
                        'source_area_id': info['area_id'], 'source_detail_id': detail,
                        'request_origin': 'geographic_nonbuilding'})
                counts['zone_ground_prop'] += 1

    if active_rules & {'mount_sign', 'roof_anchor'}:
        required = ('source_area_id', 'source_osm_id', 'base_m', 'height_m')
        if any(pads.findPrimAttrib(field) is None for field in required):
            _fail('Building-pad anchors lack identity or height for sign/roof rules')
        for pad in pads.prims():
            if pad.type() != hou.primType.Polygon or not pad.isClosed():
                continue
            ring = [vertex.point().position() for vertex in pad.vertices()]
            if len(ring) < 3:
                continue
            edges = [(math.hypot(b[0]-a[0], b[2]-a[2]), a, b)
                     for a, b in zip(ring, ring[1:] + ring[:1])]
            length, a, b = max(edges, key=lambda item: item[0])
            if length < 1.0:
                continue
            area_id = str(pad.attribValue('source_area_id'))
            osm_id = str(pad.attribValue('source_osm_id'))
            if area_id != info['area_id'] or not osm_id:
                continue
            base = float(pad.attribValue('base_m'))
            top = base + float(pad.attribValue('height_m'))
            if not all(math.isfinite(value) for value in (base, top)):
                continue
            edge_yaw = math.degrees(math.atan2(b[2]-a[2], b[0]-a[0]))
            if 'mount_sign' in active_rules:
                detail = 'sign_pad_' + osm_id
                _nonbuilding_add_request(geo, attrs,
                    ((a[0]+b[0])/2.0, base+2.5, (a[2]+b[2])/2.0), {
                        'placement_id': area_id + ':' + detail,
                        'bank_role': 'sign', 'placement_rule': 'mount_sign',
                        'bank_yaw_degrees': edge_yaw + 90.0,
                        'source_area_id': area_id, 'source_osm_id': osm_id,
                        'source_detail_id': detail,
                        'request_origin': 'geographic_nonbuilding'})
                counts['mount_sign'] += 1
            if 'roof_anchor' in active_rules:
                detail = 'roof_pad_' + osm_id
                _nonbuilding_add_request(geo, attrs,
                    (sum(v[0] for v in ring)/len(ring), top,
                     sum(v[2] for v in ring)/len(ring)), {
                        'placement_id': area_id + ':' + detail,
                        'bank_role': 'rooftop_utility', 'placement_rule': 'roof_anchor',
                        'bank_yaw_degrees': edge_yaw,
                        'source_area_id': area_id, 'source_osm_id': osm_id,
                        'source_detail_id': detail,
                        'request_origin': 'geographic_nonbuilding'})
                counts['roof_anchor'] += 1
    _set_detail(geo, 'nonbuilding_request_counts_json', json.dumps(counts, sort_keys=True))


def _nonbuilding_choose(candidates, seed, placement_id, preview):
    weighted = []
    for row in sorted(candidates, key=lambda item: item['AssetId']):
        weight = float(row['PreviewWeight'] if preview else row['SelectionWeight'])
        if weight > 0 and math.isfinite(weight):
            weighted.append((row, weight))
    total = sum(weight for _, weight in weighted)
    if total <= 0:
        return None
    threshold = _stable_fraction(seed, placement_id, 'nonbuilding_asset') * total
    for row, weight in weighted:
        threshold -= weight
        if threshold < 0:
            return row
    return weighted[-1][0]


def cook_nonbuilding_selector(node):
    """Resolve each role request against native v3 rows and emit original /Game refs."""
    parent, geo = node.parent(), node.geometry()
    guard, requests, table = (item.geometry() for item in node.inputs()[:3])
    geo.clear()
    geo.merge(guard)
    if (not parent.evalParm('nonbuilding_enabled') or
            parent.evalParm('bank_inspection_only')):
        return
    if parent.evalParm('modular_pilot_enabled') or parent.evalParm('module_test_enabled'):
        _fail('Nonbuilding route cannot share a modular or wall-module pilot')
    if parent.evalParm('bank_pilot_enabled'):
        _fail('Legacy direct picker must be off for catalog-driven nonbuilding selection')
    rows = _nonbuilding_v3_rows(table)
    preview = bool(parent.evalParm('technical_preview_enabled'))
    active = _nonbuilding_active_rows(parent, rows)
    receipt = json.loads(guard.attribValue('bank_catalog_readback_json'))
    if (len(receipt['rows']) != len(rows) or receipt['schema_version'] != 3 or
            (preview and (receipt['eligible_count'] != 0 or
                          receipt['release_enabled']))):
        _fail('Nonbuilding native v3 table or preview release guard differs')
    geo.deletePoints(list(geo.points()))
    catalog_digest = hashlib.sha256(json.dumps(
        rows, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    if receipt['catalog_sha256'] != catalog_digest:
        _fail('Nonbuilding selector and guard read different native v3 rows')
    fit = _permanent_fit_setup(node)
    candidates = {}
    for row in active:
        if (not row['ObjectPath'] or not re.fullmatch(
                r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+', row['ObjectPath']) or
                bank_technical_check_only(row)):
            continue
        candidates.setdefault((row['RequestRole'], row['PlacementRule']), []).append(row)
    diagnostics = {}
    seen_requests, placed, instances = set(), {}, []
    for request in sorted(requests.points(), key=lambda p: (PLACEMENT_PRIORITY.get(p.attribValue('bank_role'),99),p.attribValue('placement_id'))):
        placement_id = request.attribValue('placement_id')
        role = request.attribValue('bank_role')
        rule = request.attribValue('placement_rule')
        diag = diagnostics.setdefault(role, {'requests':0,'candidate_evaluations':0,'fit_rejected':0,'fit_available':0,'no_available_requests':0,'selected_spacing_rejected':0,'placed':0,'rejection_reasons':{},'rejected_requests':[]})
        diag['requests'] += 1
        if role == 'whole_building':
            provenance = _permanent_building_height_rule(request)
            height_counts = diag.setdefault('height_provenance', {})
            height_counts[provenance] = height_counts.get(provenance, 0) + 1
        if not placement_id or placement_id in seen_requests:
            _fail('Nonbuilding request has empty or duplicate placement ID')
        seen_requests.add(placement_id)
        if NONBUILDING_RULES.get(role) != rule:
            _permanent_rejection(diag,'unsupported_request_rule',placement_id)
            continue
        area_id = request.attribValue('source_area_id')
        if placement_id.partition(':')[0] != area_id:
            _fail('Nonbuilding request area and placement ID differ')
        available = []
        available_anchors = {}
        source_anchor = tuple(float(value) for value in request.position())
        position_options = _permanent_request_positions(request, node, fit)
        tree_cell = _generated_tree_seed_cell(request, node)
        if tree_cell is not None:
            diag['bounded_generated_tree_requests'] = diag.get('bounded_generated_tree_requests', 0) + 1
        elif role == 'tree':
            diag['fixed_tree_requests'] = diag.get('fixed_tree_requests', 0) + 1
        for row in candidates.get((role, rule), ()):
            diag['candidate_evaluations'] += 1
            if preview:
                ids = bank_v2_tokens(row['PreviewAllowedPlacementIds'],
                                     'PreviewAllowedPlacementIds')
                if ids and placement_id not in ids:
                    _permanent_rejection(diag,'preview_placement_scope')
                    continue
            else:
                if (row['Role'] != role or
                        row['StyleSet'] != parent.evalParm('bank_style_set').strip()):
                    _permanent_rejection(diag,'release_role_or_style')
                    continue
                _release_areas = bank_v2_tokens(row['AllowedAreas'], 'AllowedAreas')
                if area_id not in _release_areas and 'any_validated_area' not in _release_areas:
                    _permanent_rejection(diag,'release_area')
                    continue
                if (row['PlacementScope'] == 'exact_ids' and
                        placement_id not in bank_v2_tokens(
                            row['AllowedPlacementIds'], 'AllowedPlacementIds')):
                    _permanent_rejection(diag,'release_exact_scope')
                    continue
                if row['PlacementScope'] == 'area_zone':
                    zone = (request.attribValue('bank_zone')
                            if requests.findPointAttrib('bank_zone') else '')
                    if not zone or zone not in bank_v2_tokens(
                            row['AllowedZones'], 'AllowedZones'):
                        _permanent_rejection(diag,'release_zone')
                        continue
                elif row['PlacementScope'] != 'exact_ids':
                    _permanent_rejection(diag,'release_scope')
                    continue
            if rule in ('mount_sign', 'roof_anchor') and (
                    not int(row['AnchorValid']) or not int(row['OrientationValid'])):
                _permanent_rejection(diag,'invalid_attachment_contract')
                continue
            if not int(row['BoundsValid']):
                _permanent_rejection(diag,'invalid_bounds')
                continue
            fitted = False
            selected_anchor = None
            last_reason = None
            for candidate_request in position_options:
                reason = _permanent_candidate_rejection(node, row, candidate_request, fit)
                search_lane = 'tree' if role == 'tree' else 'roadside' if role in ('street_prop', 'street_pole') else None
                if search_lane:
                    key = search_lane + '_position_evaluations'
                    diag[key] = diag.get(key, 0) + 1
                if reason:
                    last_reason = reason
                    if search_lane:
                        reasons = diag.setdefault(search_lane + '_position_rejections', {})
                        reasons[reason] = reasons.get(reason, 0) + 1
                    continue
                fitted = True
                if not _permanent_spacing_ok(row, candidate_request, placed):
                    if search_lane:
                        reasons = diag.setdefault(search_lane + '_position_rejections', {})
                        key = 'footprint_clearance_or_same_role_spacing'
                        reasons[key] = reasons.get(key, 0) + 1
                    continue
                selected_anchor = candidate_request
                break
            if not fitted:
                diag['fit_rejected'] += 1
                _permanent_rejection(diag, last_reason or 'no_fitting_roadside_anchor')
                continue
            diag['fit_available'] += 1
            if selected_anchor is None:
                _permanent_rejection(diag,'footprint_clearance_or_same_role_spacing')
                continue
            available.append(row)
            available_anchors[row['AssetId']] = selected_anchor
        choice_rows = _permanent_building_choice_rows(available, request, preview) if role == 'whole_building' else available
        row = _nonbuilding_choose(choice_rows, int(parent.evalParm('seed')),
                                  placement_id, preview)
        if row is None:
            diag['no_available_requests'] += 1
            _permanent_rejection(diag,'no_available_candidate',placement_id)
            if role == 'tree':
                diag['rejected_requests'][-1].update(
                    source_anchor_m=source_anchor,
                    anchor_search_policy='generated_tree_same_seed_cell_max_2m' if tree_cell is not None else 'fixed_source_tree',
                    candidate_anchor_count=len(position_options),
                    source_seed_cell_xz_m=tree_cell)
            continue
        request = available_anchors[row['AssetId']]
        spacing = float(row['MinSpacingCm']) / 100.0
        position = hou.Vector3(request.position())
        if role != 'whole_building':
            position[1] = float(_sample_grid(fit['height'],[position[0]],[position[2]])[0])
        ground_contact_y = float(position[1])
        yaw = float(request.attribValue('bank_yaw_degrees'))
        if not math.isfinite(yaw):
            _fail('Nonbuilding request yaw is not finite')
        axis = row['ForwardAxis']
        correction = {'+X': 0.0, '+Y': 90.0, '-X': 180.0, '-Y': -90.0}.get(axis, 0.0)
        orient = hou.Quaternion(-(yaw-correction), hou.Vector3(0, 1, 0))
        anchor_cm = float(row['AnchorZCm'] if int(row['AnchorValid']) else
                          row['BoundsMinZCm'])
        cx = (float(row['BoundsMinXCm'])+float(row['BoundsMaxXCm']))/200.0
        cz = (float(row['BoundsMinYCm'])+float(row['BoundsMaxYCm']))/200.0
        position = position - orient.rotate(hou.Vector3(cx, anchor_cm/100.0, cz))
        point = geo.createPoint()
        point.setPosition(position)
        values = {
            'unreal_instance': row['ObjectPath'], 'bank_asset_id': row['AssetId'],
            'bank_variant_id': row['VariantId'], 'placement_id': placement_id,
            'bank_role': role, 'placement_rule': rule,
            'bank_catalog_sha256': catalog_digest,
            'bank_release_id': '' if preview else parent.evalParm('catalog_release_id').strip(),
            'bank_asset_revision': row['AssetRevision'],
            'bank_selection_source': 'v3_technical_preview' if preview else 'v3_release',
            'orient': tuple(orient), 'source_area_id': area_id,
            'source_osm_id': request.attribValue('source_osm_id'),
            'source_detail_id': request.attribValue('source_detail_id'),
        }
        if role == 'whole_building':
            values['building_height_rule'] = _permanent_building_height_rule(request)
        for name, value in values.items():
            attribute = geo.findPointAttrib(name) or geo.addAttrib(
                hou.attribType.Point, name,
                (0.0, 0.0, 0.0, 1.0) if name == 'orient' else '')
            point.setAttribValue(attribute, value)
        diag['placed'] += 1
        center = request.position()
        placed.setdefault('all', []).append({'x':float(center[0]),'z':float(center[2]),'role':role,'spacing':spacing,'clearance_rectangle':_permanent_rectangle(row,request,0.5)})
        instances.append({
            'placement_id': placement_id, 'row': row['Name'],
            'asset_id': row['AssetId'], 'path': row['ObjectPath'],
            'role': role, 'rule': rule, 'P': tuple(position),
            'orient': tuple(orient), 'selection_source': values['bank_selection_source'],
            'catalog_release': not preview,
            'ground_contact_y_m':ground_contact_y,'native_scale':[1,1,1],
            'footprint_xz_m':_permanent_rectangle(row,request),
            'forward_axis':axis,'clearance_m':1.0,
            'selection_anchor_m':tuple(request.position()),
        })
        if role == 'whole_building':
            instances[-1]['building_height_rule'] = _permanent_building_height_rule(request)
            instances[-1]['desired_height_m'] = float(request.attribValue('building_height_m'))
            instances[-1]['native_height_m'] = (float(row['BoundsMaxZCm'])-float(row['BoundsMinZCm']))/100.0
            instances[-1]['height_preference_multiplier'] = _permanent_building_height_preference(row, request)
        if role in ('street_prop', 'street_pole') and request.geometry().findPointAttrib('roadside_search_json') is not None:
            raw_search = request.attribValue('roadside_search_json')
            if raw_search:
                search = json.loads(raw_search)
                instances[-1]['roadside_source_detail_id'] = search['source_detail_id']
                instances[-1]['roadside_source_anchor_m'] = search['source_anchor_m']
        if role == 'tree':
            instances[-1]['source_anchor_m'] = source_anchor
            instances[-1]['anchor_offset_xz_m'] = [float(request.position()[0])-source_anchor[0],
                                                   float(request.position()[2])-source_anchor[2]]
            instances[-1]['anchor_search_policy'] = 'generated_tree_same_seed_cell_max_2m' if tree_cell is not None else 'fixed_source_tree'
            if tree_cell is not None:
                instances[-1]['source_seed_cell_xz_m'] = tree_cell
                if math.hypot(*instances[-1]['anchor_offset_xz_m']) > 1e-6:
                    diag['bounded_tree_relocated'] = diag.get('bounded_tree_relocated', 0) + 1
    receipt['native_table_schema_version'] = 3
    receipt['native_v3_catalog_sha256'] = catalog_digest
    receipt['nonbuilding_mode'] = 'technical_preview' if preview else 'release'
    receipt['original_request_count'] = receipt['request_count']
    receipt['original_request_roles'] = receipt['request_roles']
    receipt['original_requests'] = receipt.get('requests',[])
    receipt['requests'] = [{'placement_id':p.attribValue('placement_id'),'bank_role':p.attribValue('bank_role'),'placement_rule':p.attribValue('placement_rule'),'request_origin':p.attribValue('request_origin'),'bank_zone':p.attribValue('bank_zone'),'P':tuple(p.position())} for p in sorted(requests.points(),key=lambda p:p.attribValue('placement_id'))]
    receipt['request_count'] = len(receipt['requests'])
    receipt['request_roles'] = {role:d['requests'] for role,d in diagnostics.items()}
    receipt['request_scope'] = 'complete_augmented_selector_input'
    receipt['placement_diagnostics'] = diagnostics
    if requests.findGlobalAttrib('roadside_request_search_json') is not None:
        receipt['roadside_request_search'] = json.loads(requests.attribValue('roadside_request_search_json'))
    receipt['building_height_policy'] = 'hard_source_height_or_levels_soft_seeded_preference'
    receipt['active_candidate_roles'] = {role:sum(len(v) for (r,k),v in candidates.items() if r==role) for role in diagnostics}
    receipt['generator_revision'] = 'r018_retained_appearance'
    coverage=parent.node('complete_geographic_road_coverage')
    receipt['road_coverage']=json.loads(coverage.geometry().attribValue('geographic_road_coverage_json'))
    receipt['output_wiring'] = {n.name():[i.name() if i else None for i in n.inputs()] for n in parent.children() if n.type().name()=='output'}
    _set_detail(geo,'bank_request_count',receipt['request_count'])
    _set_detail(geo,'bank_request_roles_json',json.dumps(receipt['request_roles'],sort_keys=True))
    receipt['environment_style_set'] = parent.evalParm('environment_style_set')
    receipt['spatial_policy'] = 'full_concave_containment_oriented_footprint_clearance_priority_terrain_contact_v2'
    receipt['nonbuilding_instances'] = instances
    receipt['instances'] = instances
    _set_detail(geo, 'bank_catalog_readback_json', json.dumps(receipt, sort_keys=True))
    _set_detail(geo, 'bank_instances', len(instances))
    _set_detail(geo, 'nonbuilding_native_v3_sha256', catalog_digest)
    report = parent.evalParm('bank_receipt_file').strip()
    if report:
        Path(report).write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding='utf-8')


"""Landscape-only palette projection appended to the preserved v011 module.

The build script embeds exact v2 catalog IDs and target-layer names below.
Unreal reads the target-layer volumes through the official HeightField route.
No material-instance parameter overrides are used: the installed Landscape
translator does not apply them to generated Landscape material instances.
"""

SURFACE_TEXTURE_CHOICES = (('coastal.BaseGrass1', 'BaseGrass1'), ('coastal.Farmland1', 'Farmland1'), ('coastal.Grass', 'Grass'), ('coastal.Sand1', 'Sand1'), ('coastal.Sand2', 'Sand2'), ('coastal.Soil1', 'Soil1'), ('coastal.Soil2', 'Soil2'), ('coastal.TreeGround', 'TreeGround'), ('starter.SC_CobbleStone_Pebble', 'SC_CobbleStone_Pebble'), ('starter.SC_CobbleStone_Rough', 'SC_CobbleStone_Rough'), ('starter.SC_CobbleStone_Smooth', 'SC_CobbleStone_Smooth'), ('starter.SC_Concrete_Grime', 'SC_Concrete_Grime'), ('starter.SC_Concrete_Poured', 'SC_Concrete_Poured'), ('starter.SC_Concrete_Tiles', 'SC_Concrete_Tiles'), ('starter.SC_Ground_Gravel', 'SC_Ground_Gravel'), ('starter.SC_Rock_Sandstone', 'SC_Rock_Sandstone'), ('mout.Dirt_Path', 'Dirt_Path'), ('mout.Sand_01', 'Sand_01'), ('mout.Sand_02', 'Sand_02'), ('mout.Sand_03', 'Sand_03'), ('mout.Sand_Path', 'Sand_Path'), ('mout.Wet_Sand_01', 'Wet_Sand_01'), ('mout.Wet_Sand_02', 'Wet_Sand_02'), ('mout.Wet_Sand_03', 'Wet_Sand_03'), ('starter.SC_Ground_Grass', 'PB_starter_SC_Ground_Grass'), ('starter.SC_Ground_Moss', 'PB_starter_SC_Ground_Moss'), ('starter.SC_Rock_Basalt', 'PB_starter_SC_Rock_Basalt'), ('starter.SC_Rock_Slate', 'PB_starter_SC_Rock_Slate'), ('starter.SC_Concrete_Panels', 'PB_starter_SC_Concrete_Panels'), ('starter.SC_Brick_Clay_Beveled', 'PB_starter_SC_Brick_Clay_Beveled'), ('starter.SC_Brick_Clay_New', 'PB_starter_SC_Brick_Clay_New'), ('starter.SC_Brick_Clay_Old', 'PB_starter_SC_Brick_Clay_Old'), ('starter.SC_Brick_Cut_Stone', 'PB_starter_SC_Brick_Cut_Stone'), ('starter.SC_Brick_Hewn_Stone', 'PB_starter_SC_Brick_Hewn_Stone'), ('coastal.CL_Cliff_1', 'PB_coastal_CL_Cliff_1'), ('coastal.CL_Rock_04', 'PB_coastal_CL_Rock_04'), ('coastal.CL_Rock_05', 'PB_coastal_CL_Rock_05'), ('coastal.CL_Sand_1_Direct', 'PB_coastal_CL_Sand_1_Direct'), ('coastal.CL_Stone_01', 'PB_coastal_CL_Stone_01'))
SURFACE_SOLID_CHOICES = (('solid.neutral_white', 'PB_solid_neutral_white'), ('solid.neutral_black', 'PB_solid_neutral_black'), ('solid.neutral_gray', 'PB_solid_neutral_gray'), ('solid.sand_pale', 'PB_solid_sand_pale'), ('solid.sand_light', 'PB_solid_sand_light'), ('solid.sand_warm', 'PB_solid_sand_warm'), ('solid.sand_ochre', 'PB_solid_sand_ochre'), ('solid.dirt_tan', 'PB_solid_dirt_tan'), ('solid.dirt_brown', 'PB_solid_dirt_brown'), ('solid.clay_red', 'PB_solid_clay_red'), ('solid.rock_sandstone', 'PB_solid_rock_sandstone'), ('solid.rock_limestone', 'PB_solid_rock_limestone'), ('solid.rock_slate', 'PB_solid_rock_slate'), ('solid.rock_basalt', 'PB_solid_rock_basalt'), ('solid.gravel_light', 'PB_solid_gravel_light'), ('solid.gravel_dark', 'PB_solid_gravel_dark'), ('solid.road_asphalt', 'PB_solid_road_asphalt'), ('solid.road_worn', 'PB_solid_road_worn'), ('solid.concrete_light', 'PB_solid_concrete_light'), ('solid.concrete_mid', 'PB_solid_concrete_mid'), ('solid.concrete_dark', 'PB_solid_concrete_dark'), ('solid.dry_grass', 'PB_solid_dry_grass'), ('solid.grass_green', 'PB_solid_grass_green'), ('solid.moss_green', 'PB_solid_moss_green'), ('solid.snow_white', 'PB_solid_snow_white'), ('solid.wet_sand', 'PB_solid_wet_sand'))
SURFACE_PALETTE_MATERIAL = (
    "/Game/Project/Shared/SurfacePainting/"
    "MI_SurfaceBank_AllLayers.MI_SurfaceBank_AllLayers"
)
SURFACE_PAINT_ROLES = ("Ground", "Steep", "RoadBed", "BuildingPad")


def _surface_linear_channel(srgb_value):
    """Convert one 0..255 sRGB byte to Unreal's linear material value."""
    value = float(srgb_value) / 255.0
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def _surface_custom_rgb(hex_value):
    value = str(hex_value).strip()
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        _fail("Custom surface color must be #RRGGBB sRGB")
    rgb = tuple(_surface_linear_channel(int(value[index:index + 2], 16))
                for index in (1, 3, 5))
    return value.upper(), rgb


def _surface_choice(asset, role):
    """Resolve a saved per-role menu index to a bank layer or custom RGB."""
    index = int(asset.evalParm("paint_%s_choice" % role.lower()))
    texture_count = len(SURFACE_TEXTURE_CHOICES)
    solid_count = len(SURFACE_SOLID_CHOICES)
    if 0 <= index < texture_count:
        option_id, layer_name = SURFACE_TEXTURE_CHOICES[index]
        return {"kind": "texture", "id": option_id, "layer": layer_name}
    if texture_count <= index < texture_count + solid_count:
        preset_id, layer_name = SURFACE_SOLID_CHOICES[index - texture_count]
        return {"kind": "solid", "id": preset_id, "layer": layer_name}
    if index == texture_count + solid_count:
        hex_value, linear_rgb = _surface_custom_rgb(
            asset.evalParm("paint_%s_custom_hex" % role.lower()))
        return {"kind": "custom", "id": "custom." + role.lower(),
                "layer": "PB_Custom_" + role, "hex_srgb": hex_value,
                "linear_rgb": linear_rgb}
    _fail("Surface paint choice is outside the saved bank: %s=%s" %
          (role, index))


def cook_surface_palette(node):
    """Route four terrain roles to selected bank/solid/custom Landscape layers.

    This node only changes the Landscape output branch. Existing road, prop,
    tree and building branches still read the original semantic terrain node.
    """
    geo = node.geometry()  # The Python SOP starts with a writable input copy.
    palette_material = str(node.parent().evalParm("landscape_material")).strip()
    if not re.fullmatch(r"/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+", palette_material):
        _fail("Invalid retained native Landscape material path")
    height = _volume(geo, "height")
    semantic = {
        role: np.clip(_grid_array(_volume(geo, role)).copy(), 0.0, 1.0)
        for role in SURFACE_PAINT_ROLES
    }
    pad = semantic["BuildingPad"]
    road = semantic["RoadBed"] * (1.0 - pad)
    open_ground = np.clip(1.0 - pad - road, 0.0, 1.0)
    weights = {
        "Ground": semantic["Ground"] * open_ground,
        "Steep": semantic["Steep"] * open_ground,
        "RoadBed": road,
        "BuildingPad": pad,
    }
    selections = {role: _surface_choice(node.parent(), role)
                  for role in SURFACE_PAINT_ROLES}
    name_attr = _attr(geo, hou.attribType.Prim, "name", "")
    material_attr = _attr(geo, hou.attribType.Prim, "unreal_material", "")
    noweight_attr = _attr(
        geo, hou.attribType.Prim, "unreal_landscape_layer_noweightblend", 0)
    unit_attr = _attr(geo, hou.attribType.Prim,
                      "unreal_unit_landscape_layer", 0)
    layer_min_attr = _attr(geo, hou.attribType.Prim,
                           "unreal_landscape_layer_min", 0.0)
    layer_max_attr = _attr(geo, hou.attribType.Prim,
                           "unreal_landscape_layer_max", 1.0)
    output_attr = _attr(geo, hou.attribType.Prim, "unreal_output_name", "")
    bake_attr = _attr(geo, hou.attribType.Prim, "unreal_bake_folder", "")
    output_name = height.attribValue(output_attr)
    bake_folder = height.attribValue(bake_attr)
    transform = (hou.Matrix4(height.transform()) *
                 hou.hmath.buildTranslate(
                     height.vertex(0).point().position()))
    geo.deletePrims([_volume(geo, role) for role in SURFACE_PAINT_ROLES])
    height.setAttribValue(material_attr, palette_material)

    # A shared selected target layer receives the sum of all role weights.
    layer_values = {}
    custom_channels = {}
    for role, selection in selections.items():
        layer = selection["layer"]
        if layer not in layer_values:
            layer_values[layer] = np.zeros((GRID_SAMPLES, GRID_SAMPLES),
                                            dtype=np.float32)
        layer_values[layer] += weights[role]
        if selection["kind"] == "custom":
            for suffix, value in zip("RGB", selection["linear_rgb"]):
                channel = layer + "_" + suffix
                custom_channels[channel] = float(value)

    def create_layer(layer_name, values, nonweight):
        volume = geo.createVolume(GRID_SAMPLES, GRID_SAMPLES, 1)
        volume.setTransform(transform)
        volume.setAttribValue(name_attr, layer_name)
        volume.setAllVoxels(np.asarray(values, dtype=np.float32)
                            .flatten(order="F").tolist())
        volume.setAttribValue(material_attr, palette_material)
        volume.setAttribValue(noweight_attr, nonweight)
        volume.setAttribValue(unit_attr, nonweight)
        volume.setAttribValue(layer_min_attr, 0.0)
        volume.setAttribValue(layer_max_attr, 1.0)
        volume.setAttribValue(output_attr, output_name)
        volume.setAttribValue(bake_attr, bake_folder)
        for attr_name in ("unreal_landscape_output_mode",
                          "unreal_landscape_editlayer_name",
                          "unreal_landscape_editlayer_clear"):
            attr = geo.findPrimAttrib(attr_name)
            if attr is not None:
                volume.setAttribValue(attr, height.attribValue(attr))

    for layer, values in layer_values.items():
        create_layer(layer, np.clip(values, 0.0, 1.0), 0)
    for channel, value in custom_channels.items():
        create_layer(channel, np.full((GRID_SAMPLES, GRID_SAMPLES), value,
                                      dtype=np.float32), 1)
    _set_detail(geo, "unreal_landscape_layer_nonweightblended",
                " ".join(custom_channels))
    _set_detail(geo, "surface_palette_schema",
                "environmentpipeline.surface_bank.v2")
    _set_detail(geo, "surface_palette_material", palette_material)
    _set_detail(geo, "surface_palette_choices_json",
                json.dumps(selections, sort_keys=True))


"""Reusable v015 context and spatial policies; no asset/site-specific runtime code."""
NONBUILDING_RULES.update({'whole_building':'building_footprint',
                         'road_surface':'generated_road_material',
                         'sidewalk_surface':'generated_sidewalk_material'})

SURFACE_ROLES = {'road_surface', 'sidewalk_surface'}
PLACEMENT_PRIORITY = {'whole_building':0, 'tree':1, 'street_pole':2,
                      'street_prop':3, 'shrub':4, 'small_prop':5, 'understory':6}

def _permanent_surface_rows(parent, rows):
    """Materials have use/scope/revision contracts, never mesh contact contracts."""
    if parent.evalParm('technical_preview_enabled'):
        return [r for r in rows if r['RequestRole'] in SURFACE_ROLES and
                int(r['TechnicalPreviewEligible']) and not int(r['ExplicitHold']) and not r['HoldReasons']]
    if not parent.evalParm('bank_release_enabled'):
        return []
    selected=[]
    for row in rows:
        if row['RequestRole'] not in SURFACE_ROLES or not int(row['RunEligible']):
            continue
        valid=(not int(row['ExplicitHold']) and not row['HoldReasons'] and
               row['Role']==row['RequestRole'] and NONBUILDING_RULES[row['Role']]==row['PlacementRule'] and
               row['ReleaseId']==parent.evalParm('catalog_release_id').strip() and
               row['DecisionId'] and row['FamilyId'] and row['VariantId'] and
               row['StyleSet']==parent.evalParm('bank_style_set').strip() and
               math.isfinite(float(row['SelectionWeight'])) and float(row['SelectionWeight'])>0 and
               row['PlacementScope']=='area_zone' and not row['AllowedPlacementIds'] and
               bank_v2_tokens(row['AllowedAreas'],'AllowedAreas') and
               bank_v2_tokens(row['AllowedZones'],'AllowedZones') and
               re.fullmatch(r'[a-fA-F0-9]{64}',row['AssetRevision']) and
               re.fullmatch(r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+',row['ObjectPath']))
        if not valid:
            _fail('Invalid enabled generated-surface material contract: '+row['AssetId'])
        selected.append(row)
    return selected

def _permanent_rectangle(row, request, margin=0.0):
    samples=_permanent_footprint(row,request)
    if not margin:
        return [samples[i] for i in (0,2,8,6)]
    p=request.position()
    theta=math.radians(float(request.attribValue('bank_yaw_degrees'))-
                      {'+X':0,'+Y':90,'-X':180,'-Y':-90}.get(row['ForwardAxis'],0))
    c,s=math.cos(theta),math.sin(theta)
    rx=(float(row['BoundsMaxXCm'])-float(row['BoundsMinXCm']))/200.0+margin
    rz=(float(row['BoundsMaxYCm'])-float(row['BoundsMinYCm']))/200.0+margin
    return [(p[0]+x*c-z*s,p[2]+x*s+z*c) for x,z in [(-rx,-rz),(rx,-rz),(rx,rz),(-rx,rz)]]

def _permanent_rectangles_overlap(a,b):
    # Separating axes use actual oriented footprints instead of circumcircles.
    for ring in (a,b):
        for start,end in zip(ring,ring[1:]+ring[:1]):
            axis=(start[1]-end[1],end[0]-start[0])
            pa=[p[0]*axis[0]+p[1]*axis[1] for p in a]
            pb=[p[0]*axis[0]+p[1]*axis[1] for p in b]
            if max(pa)<=min(pb)+1e-8 or max(pb)<=min(pa)+1e-8:
                return False
    return True

def _permanent_spacing_ok(row,request,placed):
    rectangle=_permanent_rectangle(row,request,0.5)
    position=request.position()
    for prior in placed.get('all',()):
        if _permanent_rectangles_overlap(rectangle,prior['clearance_rectangle']):
            return False
        if row['RequestRole']==prior['role'] and math.hypot(position[0]-prior['x'],position[2]-prior['z']) < max(float(row['MinSpacingCm'])/100.0,prior['spacing']):
            return False
    return True

def _permanent_polygon_covers_rectangle(ring,rectangle):
    # Clip the complete concave geographic polygon in rectangle-local space.
    # Its intersection area must equal the entire native footprint area.
    origin=rectangle[0]
    ex=np.asarray(rectangle[1])-origin;ez=np.asarray(rectangle[3])-origin
    width=float(np.linalg.norm(ex));depth=float(np.linalg.norm(ez))
    if width<=0 or depth<=0:
        return False
    ex/=width;ez/=depth
    local=[(float(np.dot(np.asarray(p)-origin,ex)),float(np.dot(np.asarray(p)-origin,ez))) for p in ring]
    clipped=_clip_polygon(local,(0,width,0,depth))
    covered=abs(_signed_area(clipped)) if len(clipped)>=3 else 0.0
    return abs(covered-width*depth)<=max(1e-6,width*depth*1e-8)

def _permanent_ground_samples(row,request):
    # Cover the entire native footprint at the terrain mask's metre resolution.
    rectangle=_permanent_rectangle(row,request,1.0)
    origin=np.asarray(rectangle[0]);ex=np.asarray(rectangle[1])-origin;ez=np.asarray(rectangle[3])-origin
    width=float(np.linalg.norm(ex));depth=float(np.linalg.norm(ez))
    return [tuple(origin+ex*u+ez*v) for u in np.linspace(0,1,max(2,int(math.ceil(width))+1))
            for v in np.linspace(0,1,max(2,int(math.ceil(depth))+1))]

def _permanent_context_matches(parent,row,area,zone):
    style=parent.evalParm('environment_style_set').strip()
    if not style or row['StyleSet'] != style:
        return False
    areas=bank_v2_tokens(row['AllowedAreas'],'AllowedAreas')
    if area not in areas and 'any_validated_area' not in areas:
        return False
    return zone in bank_v2_tokens(row['AllowedZones'],'AllowedZones')

_permanent_previous_requests=cook_nonbuilding_requests
def cook_nonbuilding_requests(node):
    _permanent_previous_requests(node)
    parent,geo=node.parent(),node.geometry()
    zone=geo.findPointAttrib('bank_zone') or geo.addAttrib(hou.attribType.Point,'bank_zone','')
    zones={'tree':'open_ground','shrub':'open_ground','understory':'open_ground',
           'small_prop':'open_ground','street_prop':'roadside','street_pole':'roadside',
           'sign':'building_wall','rooftop_utility':'building_roof'}
    for point in geo.points():
        point.setAttribValue(zone,zones.get(point.attribValue('bank_role'),''))
    if not parent.evalParm('nonbuilding_enabled') or parent.evalParm('bank_inspection_only'):
        return
    active=_nonbuilding_active_rows(parent,_nonbuilding_v3_rows(node.inputs()[3].geometry()))
    if not any(r['RequestRole']=='whole_building' for r in active):
        return
    attrs={name:geo.findPointAttrib(name) or geo.addAttrib(hou.attribType.Point,name,0.0 if name in ('bank_yaw_degrees','building_height_m') else '')
           for name in ('placement_id','bank_role','placement_rule','bank_yaw_degrees','source_area_id',
                         'source_osm_id','source_detail_id','request_origin','bank_zone','building_footprint_json','building_height_m','building_height_rule')}
    for pad in node.inputs()[2].geometry().prims():
        if pad.type()!=hou.primType.Polygon or not pad.isClosed():
            continue
        ring=[(v.point().position()[0],v.point().position()[2]) for v in pad.vertices()]
        if len(ring)<3:
            continue
        x,z=_centroid(ring)
        if not _point_in_polygon((x,z),ring):
            continue
        _,a,b=max((math.hypot(b[0]-a[0],b[1]-a[1]),a,b) for a,b in zip(ring,ring[1:]+ring[:1]))
        osm=str(pad.attribValue('source_osm_id'));area=str(pad.attribValue('source_area_id'))
        detail='building_'+osm
        _nonbuilding_add_request(geo,attrs,(x,float(pad.attribValue('base_m')),z),{
            'placement_id':area+':'+detail,'bank_role':'whole_building','placement_rule':'building_footprint',
            'bank_yaw_degrees':math.degrees(math.atan2(b[1]-a[1],b[0]-a[0])),
            'source_area_id':area,'source_osm_id':osm,'source_detail_id':detail,'request_origin':'geographic_building_footprint',
            'bank_zone':'building_'+str(pad.attribValue('building_class')),
            'building_footprint_json':json.dumps(ring),'building_height_m':float(pad.attribValue('height_m')),
            'building_height_rule':str(pad.attribValue('height_rule'))})

def _permanent_footprint(row,request):
    # Native Unreal centimetres -> Houdini metres. The request anchors the bbox center.
    rx=(float(row['BoundsMaxXCm'])-float(row['BoundsMinXCm']))/200.0
    rz=(float(row['BoundsMaxYCm'])-float(row['BoundsMinYCm']))/200.0
    correction={'+X':0,'+Y':90,'-X':180,'-Y':-90}.get(row['ForwardAxis'],0)
    theta=math.radians(float(request.attribValue('bank_yaw_degrees'))-correction)
    c,s=math.cos(theta),math.sin(theta);p=request.position()
    return [(p[0]+x*c-z*s,p[2]+x*s+z*c) for x,z in
            [(-rx,-rz),(0,-rz),(rx,-rz),(-rx,0),(0,0),(rx,0),(-rx,rz),(0,rz),(rx,rz)]]

def _permanent_fit_setup(node):
    terrain=node.inputs()[3].geometry()
    return {'box':_local_box(_package_for_sop(node.parent())),
            'roads':_exclusion_mask(terrain,'RoadBed',1),
            'pads':_exclusion_mask(terrain,'BuildingPad',1),
            'steep':_grid_array(_volume(terrain,'Steep')),
            'height':_grid_array(_volume(terrain,'height'))}

def _permanent_rejection(diag,reason,placement_id=None):
    counts=diag['rejection_reasons'];counts[reason]=counts.get(reason,0)+1
    if placement_id:
        diag['rejected_requests'].append({'placement_id':placement_id,'reason':reason})

def _permanent_building_height_rule(request):
    if request.geometry().findPointAttrib('building_height_rule') is None:
        return 'missing_height_provenance'
    return str(request.attribValue('building_height_rule')) or 'missing_height_provenance'


def _permanent_building_height_preference(row, request):
    if _permanent_building_height_rule(request) != 'seeded_rule_not_measured':
        return 1.0
    desired = float(request.attribValue('building_height_m'))
    native = (float(row['BoundsMaxZCm']) - float(row['BoundsMinZCm'])) / 100.0
    if not math.isfinite(desired) or not math.isfinite(native) or min(desired, native) <= 0:
        return 1.0
    return max(0.05, (min(desired, native)/max(desired, native))**2)


def _permanent_building_choice_rows(rows, request, preview):
    weight_key = 'PreviewWeight' if preview else 'SelectionWeight'
    choices = []
    for row in rows:
        choice = dict(row)
        choice[weight_key] = float(row[weight_key]) * _permanent_building_height_preference(row, request)
        choices.append(choice)
    return choices


VEGETATION_BASE_ROLES = ('tree', 'shrub', 'understory')
VEGETATION_BASE_HALF_M = 0.75

def _vegetation_base_samples(request, half=VEGETATION_BASE_HALF_M):
    """Terrain vegetation stands on its trunk base, not on its crown footprint.

    v004 (Lebanon hills): judge ground masks, slope and the 0.5 m height spread
    over a 1.5 m square around the request point for tree/shrub/understory.
    Every other role keeps the whole-footprint rule."""
    p = request.position()
    return [(p[0]+dx, p[2]+dz) for dx in (-half, 0.0, half) for dz in (-half, 0.0, half)]

def _permanent_candidate_rejection(node,row,request,fit):
    style=node.parent().evalParm('environment_style_set').strip()
    if not style or row['StyleSet'] != style:
        return 'environment_style'
    areas=bank_v2_tokens(row['AllowedAreas'],'AllowedAreas')
    if request.attribValue('source_area_id') not in areas and 'any_validated_area' not in areas:
        return 'environment_area'
    if request.attribValue('bank_zone') not in bank_v2_tokens(row['AllowedZones'],'AllowedZones'):
        return 'environment_zone'
    samples=_permanent_footprint(row,request)
    if row['RequestRole']=='whole_building':
        ring=json.loads(request.attribValue('building_footprint_json'))
        height=(float(row['BoundsMaxZCm'])-float(row['BoundsMinZCm']))/100.0
        desired=float(request.attribValue('building_height_m'))
        area=(float(row['BoundsMaxXCm'])-float(row['BoundsMinXCm']))*(float(row['BoundsMaxYCm'])-float(row['BoundsMinYCm']))/10000.0
        height_rule = _permanent_building_height_rule(request)
        if height_rule not in ('osm_height_m', 'osm_levels_x_3.2m', 'seeded_rule_not_measured'):
            return 'building_height_provenance'
        if height_rule != 'seeded_rule_not_measured' and not 0.5*desired<=height<=1.5*desired:
            return 'building_height'
        if area<0.45*abs(_signed_area(ring)):
            return 'building_coverage'
        if not _permanent_polygon_covers_rectangle(ring,_permanent_rectangle(row,request)):
            return 'building_footprint'
        return None
    if row['PlacementRule'] in ('mount_sign','roof_anchor'):
        return 'unsupported_attachment_contract'
    samples=(_vegetation_base_samples(request) if row['RequestRole'] in VEGETATION_BASE_ROLES
             else _permanent_ground_samples(row,request))
    if not all(_nonbuilding_ground_ok(x,z,fit['roads'],fit['pads'],fit['steep'],fit['box']) for x,z in samples):
        return 'ground_mask_or_slope'
    heights=_sample_grid(fit['height'],[x for x,z in samples],[z for x,z in samples])
    if float(np.max(heights)-np.min(heights)) > 0.5:
        return 'terrain_height_spread'
    return None

def _permanent_candidate_fits(node,row,request,fit):
    return _permanent_candidate_rejection(node,row,request,fit) is None


def cook_permanent_surface_material(node):
    parent,geo=node.parent(),node.geometry()
    geo.clear();geo.merge(node.inputs()[0].geometry())
    lane='road_surface' if node.name()=='catalog_road_material' else 'sidewalk_surface'
    zone='road' if lane=='road_surface' else 'sidewalk'
    info=_package_for_sop(parent)
    rows=_permanent_surface_rows(parent,_nonbuilding_v3_rows(node.inputs()[1].geometry()))
    candidates=[r for r in rows if r['RequestRole']==lane and _permanent_context_matches(parent,r,info['area_id'],zone)]
    preview=bool(parent.evalParm('technical_preview_enabled'))
    chosen=_nonbuilding_choose(candidates,int(parent.evalParm('seed')),info['area_id']+':'+lane,preview)
    if chosen is None:
        if not preview:
            _fail('Required normal surface lane has no scoped material: '+lane)
        _set_detail(geo,'surface_material_selection_json',json.dumps({'lane':lane,'selected':None,'reason':'no_context_eligible_catalog_material'}))
        return
    # Long planar road/sidewalk faces sampled only at their perimeter can cut
    # through a non-planar Landscape. Brick the actual geographic surface on
    # the same metre grid, then sample every resulting point on that terrain.
    terrain_node=node.inputs()[0]
    if terrain_node is None or len(terrain_node.inputs())<3:
        _fail('Missing permanent surface terrain source: '+lane)
    height=_grid_array(_volume(terrain_node.inputs()[2].geometry(),'height'))
    original=[(_xy(prim),{a.name():prim.attribValue(a) for a in geo.primAttribs()}) for prim in geo.prims()]
    geo.deletePrims(list(geo.prims()),keep_points=False)
    attrs={a.name():a for a in geo.primAttribs()}
    lift=0.08 if lane=='road_surface' else 0.16
    for ring,values in original:
        xmin,xmax=min(p[0] for p in ring),max(p[0] for p in ring)
        zmin,zmax=min(p[1] for p in ring),max(p[1] for p in ring)
        for iz in range(math.floor(zmin),math.ceil(zmax)):
            for ix in range(math.floor(xmin),math.ceil(xmax)):
                cell=_condition_surface_polygon(_clip_polygon(ring,(ix,ix+1,iz,iz+1)))
                if not cell:
                    continue
                heights=_sample_grid(height,[x for x,z in cell],[z for x,z in cell])
                _add_polygon(geo,[(x,float(y)+lift,z) for (x,z),y in zip(cell,heights)],values,attrs)
    if original and not geo.prims():
        _fail('Terrain-conforming surface unexpectedly empty: '+lane)
    material=_attr(geo,hou.attribType.Prim,'unreal_material','')
    uv=geo.findVertexAttrib('uv') or geo.addAttrib(hou.attribType.Vertex,'uv',(0.0,0.0,0.0))
    # Native selected masters multiply UV0 by .25 for base/normal/roughness:
    # one coordinate unit per metre therefore gives their intended four-metre repeat.
    for prim in geo.prims():
        prim.setAttribValue(material,chosen['ObjectPath'])
        for vertex in prim.vertices():
            p=vertex.point().position();vertex.setAttribValue(uv,(p[0],p[2],0.0))
    _set_detail(geo,'surface_material_selection_json',json.dumps({'lane':lane,'asset_id':chosen['AssetId'],
                'path':chosen['ObjectPath'],'style':chosen['StyleSet'],'uv_coordinate_repeat_m':1.0,
                'native_main_texture_repeat_m':4.0,'native_macro_noise_repeat_m':20.0,'technical_preview':preview}))

def cook_permanent_building_replacement(node):
    geo=node.geometry();geo.clear();geo.merge(node.inputs()[0].geometry())
    instances=node.inputs()[1].geometry()
    ids={p.attribValue('source_osm_id') for p in instances.points() if p.attribValue('bank_role')=='whole_building'}
    attr=geo.findPrimAttrib('source_osm_id')
    if ids and attr:
        geo.deletePrims([p for p in geo.prims() if p.attribValue(attr) in ids],keep_points=False)
    _set_detail(geo,'native_building_replaced_osm_ids_json',json.dumps(sorted(ids)))

_permanent_selector_without_material_overrides=cook_nonbuilding_selector
def cook_nonbuilding_selector(node):
    """Emit native slot overrides from saved catalog metadata, preserving source assets."""
    _permanent_selector_without_material_overrides(node)
    geo=node.geometry();parent=node.parent()
    overrides=json.loads(parent.evalParm('bank_instance_materials') or '{}')
    if not isinstance(overrides,dict):_fail('Instance material metadata must map mesh paths to slot paths')
    for mesh,slots in overrides.items():
        if not re.fullmatch(r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+',mesh) or not isinstance(slots,list) or not 1<=len(slots)<=64:
            _fail('Invalid native mesh material metadata')
        if any(not re.fullmatch(r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+',p) for p in slots):
            _fail('Invalid native material slot path')
    affected=0
    if geo.findPointAttrib('unreal_instance'):
        for point in geo.points():
            slots=overrides.get(point.attribValue('unreal_instance'))
            if slots:
                affected+=1
                for index,path in enumerate(slots):
                    attribute=geo.findPointAttrib('unreal_material'+str(index)) or geo.addAttrib(hou.attribType.Point,'unreal_material'+str(index),'')
                    point.setAttribValue(attribute,path)
    digest=hashlib.sha256(json.dumps(overrides,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    _set_detail(geo,'instance_material_metadata_sha256',digest)
    if geo.findGlobalAttrib('bank_catalog_readback_json'):
        receipt=json.loads(geo.attribValue('bank_catalog_readback_json'))
        receipt.update(instance_material_metadata_sha256=digest,instance_material_overridden_placements=affected)
        _set_detail(geo,'bank_catalog_readback_json',json.dumps(receipt,sort_keys=True))
        report=parent.evalParm('bank_receipt_file').strip()
        if report:Path(report).write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding='utf-8')


def cook_stage(node,function_name):
    """Retain exact stage errors from the actual Engine cook, then fail normally."""
    try:
        globals()[function_name](node)
    except Exception:
        import traceback
        parent=node.parent()
        report=parent.evalParm('bank_receipt_file').strip()
        if report:
            error_path=Path(report+'.errors.json')
            errors=json.loads(error_path.read_text()) if error_path.exists() else {}
            errors[node.name()]={'function':function_name,'traceback':traceback.format_exc()}
            error_path.write_text(json.dumps(errors,indent=2),encoding='utf-8')
        raise

# Exact-request proxy substitution remains downstream of native selection.
_bank_proxy_filter_original = cook_bank_proxy_filter

def cook_bank_proxy_filter(node, role, detail_kind):
    _bank_proxy_filter_original(node, role, detail_kind)
    source = node.inputs()[0].geometry()
    result = node.geometry()
    def identities(geometry):
        return sorted({p.attribValue('detail_id') for p in geometry.prims()
                       if p.attribValue('detail_kind') == detail_kind})
    original_ids = identities(source)
    remaining_ids = identities(result)
    removed_ids = sorted(set(original_ids)-set(remaining_ids))
    state = {'source_ids':original_ids,'remaining_ids':remaining_ids,
             'removed_ids':removed_ids,'source_count':len(original_ids),
             'remaining_count':len(remaining_ids),'removed_count':len(removed_ids),
             'remaining_primitives':len(result.prims()),
             'policy':'exact_area_request_identity_native_substitution'}
    _set_detail(result,'proxy_substitution_json',json.dumps(state,sort_keys=True))
    report = node.parent().evalParm('bank_receipt_file').strip()
    if report:
        path = Path(report)
        receipt = json.loads(path.read_text(encoding='utf-8'))
        receipt.setdefault('proxy_outputs',{})[role] = state
        path.write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding='utf-8')


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
    receipt["generator_revision"] = "r018_retained_appearance"
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


"""Append to the retained HDA PythonModule after the other r015 changes.

Input contract retained:
  corrected_dsm_and_generated_masks: [heightfield, complete roads, building pads]
  nonbuilding requests: [source requests, final terrain, building pads, native table]
  nonbuilding selector: input 3 is the same final terrain.

This changes elevation grading only. Source geographic polygons, RoadBed and
BuildingPad masks, native identities and material routing are preserved.
"""


def _terrain_r015_dilate_one(mask):
    padded = np.pad(mask, 1, mode='constant', constant_values=False)
    result = np.zeros_like(mask, dtype=bool)
    for iz in range(3):
        for ix in range(3):
            result |= padded[iz:iz + mask.shape[0], ix:ix + mask.shape[1]]
    return result


def _terrain_r015_polygon_support_core(ring, x0, z0, width, height, half):
    """Minimal exact grid vertices supporting the true geographic polygon.

    ImageDraw rounds polygon coordinates to pixels. Dilation of that rounded
    polygon alone misses some diagonal boundary interpolation vertices. Cover
    the actual intersected cells, then retain all four vertices of each cell.
    """
    result = np.zeros((height, width), dtype=bool)
    xmin, xmax = math.floor(min(p[0] for p in ring)), math.ceil(max(p[0] for p in ring))
    zmin, zmax = math.floor(min(p[1] for p in ring)), math.ceil(max(p[1] for p in ring))
    for iz in range(zmin, zmax):
        for ix in range(xmin, xmax):
            polygon = _clip_polygon(ring, (ix, ix + 1, iz, iz + 1))
            if len(polygon) < 3 or abs(_signed_area(polygon)) <= 1e-10:
                continue
            for px, pz in ((ix, iz), (ix + 1, iz), (ix, iz + 1), (ix + 1, iz + 1)):
                col, row = int(px + half - x0), int(pz + half - z0)
                if 0 <= col < width and 0 <= row < height:
                    result[row, col] = True
    return result


def _terrain_r015_coherent_pad_records(pad_records, shape=(4033, 4033)):
    """Only touching interpolation-support pads share a generated datum.

    Different constants cannot occupy the same Landscape vertex. Reconcile that
    real overlap before generating terrain, native models OR facade assemblies.
    Preserve every geographic footprint and requested building height.
    """
    records = [dict(record) for record in sorted(pad_records, key=lambda item: item['id'])]
    original_bases = {record['id']: float(record['base_m']) for record in records}
    links = list(range(len(records)))
    owner = np.full(shape, -1, dtype=np.int32)
    half = (shape[1] - 1) / 2.0

    def find(index):
        while links[index] != index:
            links[index] = links[links[index]]
            index = links[index]
        return index

    for number, record in enumerate(records):
        ring = record['ring']
        x0 = max(0, int(math.floor(min(p[0] for p in ring) + half)) - 3)
        x1 = min(shape[1], int(math.ceil(max(p[0] for p in ring) + half)) + 4)
        z0 = max(0, int(math.floor(min(p[1] for p in ring) + half)) - 3)
        z1 = min(shape[0], int(math.ceil(max(p[1] for p in ring) + half)) + 4)
        if x0 >= x1 or z0 >= z1:
            continue
        image = Image.new('L', (x1 - x0, z1 - z0), 0)
        ImageDraw.Draw(image).polygon([(x + half - x0, z + half - z0)
                                      for x, z in ring], fill=255)
        core = _terrain_r015_polygon_support_core(ring, x0, z0, x1 - x0, z1 - z0, half)
        occupied = owner[z0:z1, x0:x1]
        # Adjacent fixed vertices also require a shared datum: two unrelated
        # constants on neighbouring vertices would make a one-metre cliff.
        contact = _terrain_r015_dilate_one(core)
        for other in np.unique(occupied[contact]):
            if other >= 0:
                a, b = find(number), find(int(other))
                if a != b:
                    links[max(a, b)] = min(a, b)
        occupied[core] = number
    groups = {}
    for number in range(len(records)):
        groups.setdefault(find(number), []).append(number)
    changed = 0
    maximum_shift = 0.0
    cluster_receipts = []
    for members in groups.values():
        ranked = sorted((float(records[i]['base_m']),
                         max(1.0, abs(_signed_area(records[i]['ring']))), i)
                        for i in members)
        half_weight = sum(weight for base, weight, i in ranked) / 2.0
        accumulated = 0.0
        shared_base = ranked[-1][0]
        for base, weight, i in ranked:
            accumulated += weight
            if accumulated >= half_weight:
                shared_base = base
                break
        for i in members:
            shift = abs(float(records[i]['base_m']) - shared_base)
            changed += int(shift > 1e-6)
            maximum_shift = max(maximum_shift, shift)
            records[i]['base_m'] = shared_base
        if len(members) > 1:
            cluster_receipts.append({'pad_ids': [records[i]['id'] for i in members],
                                     'shared_base_m': shared_base,
                                     'original_min_m': ranked[0][0],
                                     'original_max_m': ranked[-1][0]})
    # Keep separate nearby plateaus, but constrain their height difference to
    # the available gap. Otherwise even a feathered collar has no physical room
    # to bridge two large incompatible constants across a narrow city street.
    root_lookup = np.asarray([find(i) for i in range(len(records))], dtype=np.int32)
    labels = np.full(shape, -1, dtype=np.int32)
    valid = owner >= 0
    labels[valid] = root_lookup[owner[valid]]
    gap_edges = {}
    gap_limit = 12
    for root in groups:
        iz, ix = np.where(labels == root)
        if not len(ix):
            continue
        x0, x1 = max(0, int(ix.min()) - gap_limit), min(shape[1], int(ix.max()) + gap_limit + 1)
        z0, z1 = max(0, int(iz.min()) - gap_limit), min(shape[0], int(iz.max()) + gap_limit + 1)
        local_labels = labels[z0:z1, x0:x1]
        previous = local_labels == root
        for distance in range(1, gap_limit + 1):
            expanded = _terrain_r015_dilate_one(previous)
            band = expanded & ~previous
            for other in np.unique(local_labels[band]):
                other = int(other)
                if other >= 0 and other != root:
                    pair = tuple(sorted((root, other)))
                    gap_edges[pair] = min(distance, gap_edges.get(pair, distance))
            previous = expanded
    group_bases = {root: float(records[members[0]]['base_m']) for root, members in groups.items()}
    group_weights = {root: sum(max(1.0, abs(_signed_area(records[i]['ring']))) for i in members)
                     for root, members in groups.items()}
    # Gap measured on a square grid is conservative for diagonal transitions.
    # This constraint changes generated datum only, never source OSM or DSM.
    allowed_gradient = 0.45
    for iteration in range(128):
        largest_excess = 0.0
        for (a, b), gap in sorted(gap_edges.items()):
            difference = group_bases[a] - group_bases[b]
            excess = abs(difference) - allowed_gradient * gap
            if excess <= 0:
                continue
            largest_excess = max(largest_excess, excess)
            sign = 1.0 if difference > 0 else -1.0
            wa, wb = group_weights[a], group_weights[b]
            group_bases[a] -= sign * excess * wb / (wa + wb)
            group_bases[b] += sign * excess * wa / (wa + wb)
        if largest_excess < 1e-5:
            break
    for root, members in groups.items():
        for i in members:
            records[i]['base_m'] = group_bases[root]
    by_id = {record['id']: record for record in records}
    for cluster in cluster_receipts:
        cluster['shared_base_m'] = by_id[cluster['pad_ids'][0]]['base_m']
    shifts = [abs(record['base_m'] - original_bases[record['id']]) for record in records]
    maximum_shift = max(shifts) if shifts else 0.0
    changed = sum(shift > 1e-6 for shift in shifts)
    residual = max((max(0.0, abs(group_bases[a] - group_bases[b]) - allowed_gradient * gap)
                    for (a, b), gap in gap_edges.items()), default=0.0)
    return records, {'policy': 'coherent_touching_support_and_gap_limited_generated_datums',
                     'pad_count': len(records), 'cluster_count': len(groups),
                     'touching_clusters': cluster_receipts,
                     'pads_with_changed_generated_base': changed,
                     'maximum_generated_base_shift_m': maximum_shift,
                     'neighbor_datum_edges': len(gap_edges),
                     'neighbor_gap_limit_m': gap_limit,
                     'neighbor_datum_max_gradient_m_per_m': allowed_gradient,
                     'neighbor_constraint_residual_m': residual,
                     'source_xy_footprints_and_heights_preserved': True}


_terrain_r015_previous_building_pads = cook_building_pads


def cook_building_pads(node):
    _terrain_r015_previous_building_pads(node)
    geo = node.geometry()
    primitives = list(geo.prims())
    records = [{'id': str(p.attribValue('source_osm_id')),
                'ring': _xy(p), 'base_m': float(p.attribValue('base_m'))}
               for p in primitives if len(_xy(p)) >= 3]
    records, receipt = _terrain_r015_coherent_pad_records(records)
    bases = {record['id']: record['base_m'] for record in records}
    for primitive in primitives:
        base = bases.get(str(primitive.attribValue('source_osm_id')))
        if base is None:
            continue
        primitive.setAttribValue('base_m', float(base))
        for vertex in primitive.vertices():
            position = vertex.point().position()
            position[1] = base
            vertex.point().setPosition(position)
    _set_detail(geo, 'building_support_datums_json', json.dumps(receipt, sort_keys=True))


def _terrain_r015_graded_grid(baseline, pad_records):
    """Local flat support and a smooth collar; unchanged DSM outside collars.

    A complete one-cell halo around the geographic pad supplies the neighbouring
    vertices needed by bilinear sampling AND Landscape triangle interpolation.
    Individual collars blend against the original road-smoothed DSM, never an
    already modified neighbour. Original geographic pad interiors have priority
    over another pad's collar. Contradictory native support is caught downstream.
    """
    rows, cols = baseline.shape
    half = (cols - 1) / 2.0
    weighted_delta = np.zeros_like(baseline, dtype=np.float64)
    total_weight = np.zeros_like(baseline, dtype=np.float64)
    original_owner = np.full(baseline.shape, -1, dtype=np.int32)
    original_base = np.zeros_like(baseline, dtype=np.float32)
    core_min = np.full(baseline.shape, np.inf, dtype=np.float32)
    core_max = np.full(baseline.shape, -np.inf, dtype=np.float32)
    collar_count = 0
    widths = []
    for number, record in enumerate(sorted(pad_records, key=lambda item: item['id'])):
        ring, base = record['ring'], float(record['base_m'])
        if len(ring) < 3:
            continue
        # The first small window measures the original pad's required relief.
        x0 = max(0, int(math.floor(min(p[0] for p in ring) + half)) - 1)
        x1 = min(cols, int(math.ceil(max(p[0] for p in ring) + half)) + 2)
        z0 = max(0, int(math.floor(min(p[1] for p in ring) + half)) - 1)
        z1 = min(rows, int(math.ceil(max(p[1] for p in ring) + half)) + 2)
        if x0 >= x1 or z0 >= z1:
            continue
        image = Image.new('L', (x1 - x0, z1 - z0), 0)
        ImageDraw.Draw(image).polygon([(x + half - x0, z + half - z0)
                                      for x, z in ring], fill=255)
        inside = np.asarray(image) > 0
        if not inside.any():
            continue
        relief = float(np.max(np.abs(baseline[z0:z1, x0:x1][inside] - base)))
        # Smoothstep's maximum derivative is 1.5. A 0.35 m/m correction slope
        # requests a wider collar where the old median pad made a tall cliff.
        # Bound the actual local edit to 32 m; no area-wide terrain filtering.
        width = max(4, min(32, int(math.ceil(1.5 * relief / 0.35))))
        widths.append(width)
        extra = width + 2
        x0 = max(0, x0 - extra)
        x1 = min(cols, x1 + extra)
        z0 = max(0, z0 - extra)
        z1 = min(rows, z1 + extra)
        image = Image.new('L', (x1 - x0, z1 - z0), 0)
        ImageDraw.Draw(image).polygon([(x + half - x0, z + half - z0)
                                      for x, z in ring], fill=255)
        inside = np.asarray(image) > 0
        core = _terrain_r015_polygon_support_core(ring, x0, z0, x1 - x0, z1 - z0, half)
        weight = core.astype(np.float64)
        previous = core
        for distance in range(1, width + 1):
            expanded = _terrain_r015_dilate_one(previous)
            band = expanded & ~previous
            t = min(1.0, float(distance) / width)
            weight[band] = 1.0 - (3.0 * t * t - 2.0 * t * t * t)
            previous = expanded
        region = np.s_[z0:z1, x0:x1]
        total_weight[region] += weight
        weighted_delta[region] += weight * (base - baseline[region])
        original_owner[region][inside] = number
        original_base[region][inside] = base
        core_min[region][core] = np.minimum(core_min[region][core], base)
        core_max[region][core] = np.maximum(core_max[region][core], base)
        collar_count += int(np.count_nonzero((weight > 0) & ~core))
    corrected = (baseline + weighted_delta / np.maximum(1.0, total_weight)).astype(np.float32)
    # A neighbouring collar is soft influence, never permission to disturb a
    # compatible flat support halo. Only contradictory core heights need the
    # downstream support check; ordinary collars cannot create false rejection.
    has_core = np.isfinite(core_min)
    core_spread = np.zeros_like(baseline, dtype=np.float32)
    core_spread[has_core] = core_max[has_core] - core_min[has_core]
    compatible_core = has_core & (core_spread <= 0.03)
    corrected[compatible_core] = core_min[compatible_core]
    # Retain exact plateau interiors, including overlapping OSM pads' existing
    # deterministic source-ID order. A collar can never overwrite that interior.
    interior = original_owner >= 0
    corrected[interior] = original_base[interior]
    # Relax ONLY the free collar vertices with the plateau cores and original
    # DSM outside the collar held fixed. Independent weighted collars alone
    # can leave a seam where a neighbour influences the first free vertex.
    free_collar = (total_weight > 0) & ~has_core
    for iteration in range(32):
        padded = np.pad(corrected, 1, mode='edge')
        relaxed = (padded[:-2, 1:-1] + padded[2:, 1:-1] +
                   padded[1:-1, :-2] + padded[1:-1, 2:]) * 0.25
        corrected[free_collar] = relaxed[free_collar]
    conflict = has_core & (core_spread > 0.03)
    changed = np.abs(corrected - baseline) > 1e-6
    return corrected, {
        'policy': 'local_flat_support_one_cell_halo_adaptive_smoothstep_collar_v1',
        'source_pad_count': len(pad_records),
        'support_halo_cells': 1,
        'support_core_basis': 'four_vertices_of_every_intersected_true_polygon_cell',
        'collar_width_min_m': min(widths) if widths else 0,
        'collar_width_max_m': max(widths) if widths else 0,
        'collar_sample_count': collar_count,
        'conflicting_support_cells': int(np.count_nonzero(conflict)),
        'changed_grid_samples': int(np.count_nonzero(changed)),
        'collar_relaxation_iterations': 32,
        'max_local_correction_m': float(np.max(np.abs(corrected - baseline))),
        'unchanged_outside_local_collars': True,
        'geographic_masks_preserved': True,
    }


_terrain_r015_previous_city_terrain = cook_city_terrain


def cook_city_terrain(node):
    # Preserve all existing native Landscape/layer/material/output attributes.
    _terrain_r015_previous_city_terrain(node)
    info = _package_for_sop(node)
    geo = node.geometry()
    height_volume = _volume(geo, 'height')
    axis = np.arange(GRID_SAMPLES, dtype=np.float64) - (GRID_SAMPLES - 1) / 2.0
    x, z = np.meshgrid(axis, axis)
    raw = np.asarray(_dsm_local(info, x, z), dtype=np.float32)
    road_mask = _grid_array(_volume(geo, 'RoadBed'))
    padded = np.pad(raw, 1, mode='edge')
    smoothed = sum(padded[a:a + GRID_SAMPLES, b:b + GRID_SAMPLES]
                   for a in range(3) for b in range(3)) / 9.0
    baseline = raw * (1.0 - 0.55 * road_mask) + smoothed * (0.55 * road_mask)
    records = [{'id': str(p.attribValue('source_osm_id')),
                'area_id': str(p.attribValue('source_area_id')),
                'building_class': str(p.attribValue('building_class')),
                'height_m': float(p.attribValue('height_m')),
                'height_rule': str(p.attribValue('height_rule')),
                'ring': _xy(p), 'base_m': float(p.attribValue('base_m'))}
               for p in node.inputs()[2].geometry().prims() if len(_xy(p)) >= 3]
    corrected, receipt = _terrain_r015_graded_grid(baseline, records)
    pad_geo = node.inputs()[2].geometry()
    receipt['support_datums'] = json.loads(pad_geo.attribValue('building_support_datums_json'))
    height_volume.setAllVoxels(corrected.flatten(order='F').tolist())
    dz, dx = np.gradient(corrected, GRID_SPACING_M, GRID_SPACING_M)
    degrees = np.degrees(np.arctan(np.hypot(dx, dz)))
    steep = np.clip((degrees - 15.0) / 20.0, 0.0, 1.0).astype(np.float32)
    _volume(geo, 'Steep').setAllVoxels(steep.flatten(order='F').tolist())
    _volume(geo, 'Ground').setAllVoxels((1.0 - steep).flatten(order='F').tolist())
    receipt['max_final_slope_degrees'] = float(np.max(degrees))
    _set_detail(geo, 'terrain_support_grading_json', json.dumps(receipt, sort_keys=True))
    _set_detail(geo, 'terrain_correction', receipt['policy'])
    _set_detail(geo, 'corrected_min_m', float(corrected.min()))
    _set_detail(geo, 'corrected_max_m', float(corrected.max()))


_terrain_r015_previous_requests = cook_nonbuilding_requests


def cook_nonbuilding_requests(node):
    _terrain_r015_previous_requests(node)
    geo = node.geometry()
    if not geo.findPointAttrib('bank_role'):
        return
    height = _grid_array(_volume(node.inputs()[1].geometry(), 'height'))
    for point in geo.points():
        if point.attribValue('bank_role') == 'whole_building':
            p = point.position()
            p[1] = float(_sample_grid(height, [p[0]], [p[2]])[0])
            point.setPosition(p)


def _terrain_r015_support_samples(rectangle):
    """Sample EVERY Landscape cell vertex touched by the support rectangle.

    A planar set of these vertices guarantees both Landscape triangulations and
    the HDA's bilinear sampler yield the same support plane inside the rectangle.
    """
    samples = [tuple(p) for p in rectangle]
    xmin = math.floor(min(p[0] for p in rectangle))
    xmax = math.ceil(max(p[0] for p in rectangle))
    zmin = math.floor(min(p[1] for p in rectangle))
    zmax = math.ceil(max(p[1] for p in rectangle))
    for iz in range(zmin, zmax):
        for ix in range(xmin, xmax):
            intersection = _clip_polygon(rectangle, (ix, ix + 1, iz, iz + 1))
            if len(intersection) >= 3 and abs(_signed_area(intersection)) > 1e-10:
                samples.extend(((ix, iz), (ix + 1, iz),
                                (ix, iz + 1), (ix + 1, iz + 1)))
    return sorted(set(samples))


_terrain_r015_previous_candidate_rejection = _permanent_candidate_rejection


def _permanent_candidate_rejection(node, row, request, fit):
    reason = _terrain_r015_previous_candidate_rejection(node, row, request, fit)
    if reason or row['RequestRole'] != 'whole_building':
        return reason
    rectangle = _permanent_rectangle(row, request)
    samples = _terrain_r015_support_samples(rectangle)
    values = _sample_grid(fit['height'], [p[0] for p in samples], [p[1] for p in samples])
    p = request.position()
    base = float(_sample_grid(fit['height'], [p[0]], [p[2]])[0])
    # 3 cm admits the configured native Landscape's <1 cm height quantisation.
    # It does not admit the former measured 39 cm penetration / 11 cm gap.
    if float(np.max(np.abs(values - base))) > 0.03:
        return 'building_support_not_flat_on_final_terrain'
    return None


_terrain_r015_previous_selector = cook_nonbuilding_selector


def cook_nonbuilding_selector(node):
    _terrain_r015_previous_selector(node)
    geo = node.geometry()
    if not geo.findGlobalAttrib('bank_catalog_readback_json'):
        return
    receipt = json.loads(geo.attribValue('bank_catalog_readback_json'))
    terrain = node.inputs()[3].geometry()
    if terrain.findGlobalAttrib('terrain_support_grading_json'):
        receipt['terrain_support'] = json.loads(terrain.attribValue('terrain_support_grading_json'))
        _set_detail(geo, 'bank_catalog_readback_json', json.dumps(receipt, sort_keys=True))
        report = node.parent().evalParm('bank_receipt_file').strip()
        if report:
            Path(report).write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding='utf-8')


"""Append after retained assembly/terrain patches; nothing runs on import.

Generated decoration requests which failed normal native placement are explicitly
omitted from final proxy output. This is not native substitution. Surveyed trees,
external requests, unreleased areas, and disabled assembly remain unchanged.
"""


_final_proxy_policy_previous_filter = cook_bank_proxy_filter


def _final_proxy_generated_identity(role, detail_id, primitives, request, rejection):
    """Return (omission record, preservation reason), conservatively."""
    origins = {'tree': 'geographic_tree', 'street_pole': 'geographic_street_pole'}
    kinds = {'tree': 'procedural_tree_blockout', 'street_pole': 'procedural_street_pole'}
    rules = {'tree': 'terrain_tree', 'street_pole': 'roadside_pole'}
    if request.get('bank_role') != role or request.get('request_origin') != origins[role]:
        return None, 'surveyed_external_or_unconfirmed_request_origin'
    if request.get('placement_rule') != rules[role]:
        return None, 'unconfirmed_request_rule'
    if rejection.get('reason') != 'no_available_candidate':
        return None, 'no_explicit_failed_native_fit'
    if not primitives:
        return None, 'missing_generated_proxy_primitives'
    areas = {str(p.attribValue('source_area_id')) for p in primitives}
    osms = {str(p.attribValue('source_osm_id')).strip() for p in primitives}
    detail_kinds = {str(p.attribValue('detail_kind')) for p in primitives}
    if len(areas) != 1 or next(iter(areas)) not in ('GazaRimal', 'GazaShujaiya', 'KarmeiYosef_31850349_34907601_4km'):
        return None, 'area_identity_unconfirmed'
    area_id = next(iter(areas))
    if detail_kinds != {kinds[role]} or request.get('placement_id') != area_id + ':' + detail_id:
        return None, 'generated_primitive_identity_mismatch'
    if role == 'tree':
        if not re.fullmatch(r'tree_-?\d+_-?\d+', detail_id) or osms != {''}:
            return None, 'surveyed_or_nonseeded_tree_preserved'
        if rejection.get('anchor_search_policy') != 'generated_tree_same_seed_cell_max_2m':
            return None, 'bounded_generated_tree_fit_unconfirmed'
    else:
        match = re.fullmatch(r'pole_(\d+)_(\d+)_(\d+)', detail_id)
        if not match or osms != {match.group(1)}:
            return None, 'nonprocedural_or_unconfirmed_road_pole_preserved'
    anchor = rejection.get('source_anchor_m', request.get('P'))
    if not isinstance(anchor, (list, tuple)) or len(anchor) != 3:
        return None, 'original_anchor_missing'
    try:
        anchor = [float(v) for v in anchor]
    except (TypeError, ValueError):
        return None, 'original_anchor_invalid'
    if not all(math.isfinite(v) for v in anchor):
        return None, 'original_anchor_invalid'
    return {'detail_id': detail_id, 'placement_id': request['placement_id'],
            'source_area_id': area_id, 'source_osm_id': next(iter(osms)),
            'request_origin': request['request_origin'], 'original_anchor_m': anchor,
            'reason': 'generated_decoration_request_failed_safe_native_fit',
            'native_fit_failure': dict(rejection),
            'native_substitution': False}, None


def cook_bank_proxy_filter(node, role, detail_kind):
    _final_proxy_policy_previous_filter(node, role, detail_kind)
    if role not in ('tree', 'street_pole'):
        return
    parent, result = node.parent(), node.geometry()
    state = json.loads(result.attribValue('proxy_substitution_json'))
    # Never recategorize previous native substitution as an omission.
    state['native_removed_count'] = state['removed_count']
    state['omitted_generated_ids'] = []
    state['omitted_generated_count'] = 0
    state['omitted_generated_requests'] = []
    state['omission_preserved_diagnostics'] = []
    state['omission_policy'] = 'explicit_failed_generated_decoration_only_v1'
    report = parent.evalParm('bank_receipt_file').strip()
    receipt = json.loads(Path(report).read_text(encoding='utf-8')) if report else {}
    scope_failure = None
    if not parent.evalParm('bank_release_enabled') or parent.evalParm('technical_preview_enabled'):
        scope_failure = 'normal_released_generation_required'
    elif (receipt.get('release_enabled') is not True or receipt.get('technical_preview_enabled') is not False
          or receipt.get('nonbuilding_mode') != 'release'
          or receipt.get('request_scope') != 'complete_augmented_selector_input'):
        scope_failure = 'current_normal_selector_receipt_required'
    elif not receipt.get('active_candidate_roles', {}).get(role, 0):
        scope_failure = 'supported_native_role_required'
    elif any(result.findPrimAttrib(key) is None for key in
             ('detail_id', 'detail_kind', 'source_area_id', 'source_osm_id')):
        scope_failure = 'proxy_source_provenance_missing'
    groups = {}
    if scope_failure is None:
        for primitive in result.prims():
            if primitive.attribValue('detail_kind') == detail_kind:
                groups.setdefault(str(primitive.attribValue('detail_id')), []).append(primitive)
        areas = {str(p.attribValue('source_area_id')) for ps in groups.values() for p in ps}
        try:
            if len(areas) != 1 or next(iter(areas)) not in ('GazaRimal', 'GazaShujaiya', 'KarmeiYosef_31850349_34907601_4km'):
                scope_failure = 'named_normal_area_required' if groups else 'no_remaining_generated_proxies'
            elif _assembly_contract(parent, next(iter(areas))) is None:
                scope_failure = 'enabled_scoped_assembly_contract_required'
        except (TypeError, ValueError, KeyError) as exc:
            scope_failure = 'assembly_contract_validation_failed:' + str(exc)
    if scope_failure:
        state['omission_preserved_diagnostics'].append({'reason': scope_failure})
    else:
        requests, rejected = {}, {}
        for record in receipt.get('requests', []):
            requests.setdefault(record.get('placement_id'), []).append(record)
        for record in receipt.get('placement_diagnostics', {}).get(role, {}).get('rejected_requests', []):
            rejected.setdefault(record.get('placement_id'), []).append(record)
        delete = []
        for detail_id in state['remaining_ids']:
            primitives = groups.get(detail_id, [])
            area_id = str(primitives[0].attribValue('source_area_id')) if primitives else ''
            placement_id = area_id + ':' + detail_id
            if len(requests.get(placement_id, [])) != 1 or len(rejected.get(placement_id, [])) != 1:
                record, reason = None, 'unique_current_request_and_failure_required'
            else:
                record, reason = _final_proxy_generated_identity(
                    role, detail_id, primitives, requests[placement_id][0], rejected[placement_id][0])
            if record:
                state['omitted_generated_requests'].append(record)
                delete.extend(primitives)
            else:
                state['omission_preserved_diagnostics'].append({'detail_id': detail_id, 'reason': reason})
        result.deletePrims(delete, keep_points=False)
        omitted = {r['detail_id'] for r in state['omitted_generated_requests']}
        state['omitted_generated_ids'] = sorted(omitted)
        state['omitted_generated_count'] = len(omitted)
        state['remaining_ids'] = [i for i in state['remaining_ids'] if i not in omitted]
        state['remaining_count'] = len(state['remaining_ids'])
        if result.findGlobalAttrib('detail_ids_json') is not None:
            ids = json.loads(result.attribValue('detail_ids_json'))
            _set_detail(result, 'detail_ids_json', json.dumps([i for i in ids if i not in omitted]))
    state['remaining_primitives'] = len(result.prims())
    if state['source_count'] != state['removed_count'] + state['omitted_generated_count'] + state['remaining_count']:
        raise ValueError('proxy_native_omitted_remaining_accounting_mismatch')
    _set_detail(result, 'proxy_substitution_json', json.dumps(state, sort_keys=True))
    if report:
        receipt.setdefault('proxy_outputs', {})[role] = state
        Path(report).write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding='utf-8')


"""Append to the retained r017 PythonModule; nothing evaluates on import.

Integration: add string parms road_provider='houdini',
road_provider_contract_json='{}', route_surface_materials_json='{}'.
No new graph connection, shape package, raw geographic change or native asset
change is required. Raw complete coverage and its Landscape masks are untouched.
The RoadBLD option must remain inactive until the delivered native contract is
complete. The manager owns provider activation and named Unreal saves.
"""


_surface_r018_previous_material = cook_permanent_surface_material
_surface_r018_previous_selector = cook_nonbuilding_selector


def _surface_r018_parm(parent, name, default):
    parm = parent.parm(name)
    return str(parm.eval()).strip() if parm is not None else default


def _surface_r018_index_add(index, ring):
    """Add conditioned triangle coverage to the existing 4m subtraction index."""
    ring = _condition_surface_polygon(ring)
    if not ring:
        return 0.0
    total = 0.0
    for indices in _triangles(ring):
        triangle = [ring[i] for i in indices]
        area = abs(_signed_area(triangle))
        if area <= 1e-6:
            continue
        bounds = (min(p[0] for p in triangle), max(p[0] for p in triangle),
                  min(p[1] for p in triangle), max(p[1] for p in triangle))
        number = len(index[0])
        index[0].append((triangle, bounds))
        for iz in range(math.floor(bounds[2] / 4), math.floor(bounds[3] / 4) + 1):
            for ix in range(math.floor(bounds[0] / 4), math.floor(bounds[1] / 4) + 1):
                index[1].setdefault((ix, iz), set()).add(number)
        total += area
    return total


def _surface_r018_pad_index(parent):
    pads = parent.node('centroid_buildings_and_ground_pads')
    if pads is None:
        _fail('Missing corrected geographic building pads for surface exclusion')
    index = ([], {})
    for prim in pads.geometry().prims():
        ring = _xy(prim)
        if len(ring) >= 3:
            _surface_r018_index_add(index, ring)
    return index


def _surface_r018_line_pieces(ring, box):
    """Clip a true line analytically; outside excursions never create connectors."""
    pieces, current = [], None
    xmin, xmax, zmin, zmax = box
    for source_index, (a, b) in enumerate(zip(ring, ring[1:])):
        lower, upper = 0.0, 1.0
        for axis, minimum, maximum in ((0, xmin, xmax), (1, zmin, zmax)):
            delta = b[axis] - a[axis]
            if abs(delta) <= 1e-15:
                if a[axis] < minimum or a[axis] > maximum:
                    upper = -1.0
                    break
            else:
                first, last = (minimum - a[axis]) / delta, (maximum - a[axis]) / delta
                lower = max(lower, min(first, last))
                upper = min(upper, max(first, last))
        if upper < lower or upper < 0 or lower > 1:
            if current is not None:
                pieces.append(current)
                current = None
            continue
        lower, upper = max(0.0, lower), min(1.0, upper)
        start = a if lower == 0 else (a[0] + lower * (b[0] - a[0]), a[1] + lower * (b[1] - a[1]))
        end = b if upper == 1 else (a[0] + upper * (b[0] - a[0]), a[1] + upper * (b[1] - a[1]))
        if math.dist(start, end) <= 1e-8:
            if current is not None and lower == 0 and upper == 1:
                current['originals'].append((len(current['xy']) - 1, source_index + 1))
            continue
        if current is None or lower != 0:
            if current is not None:
                pieces.append(current)
            current = {'xy': [start], 'originals': [], 'boundaries': []}
            if lower == 0:
                current['originals'].append((0, source_index))
            else:
                current['boundaries'].append(0)
        steps = max(1, int(math.ceil(math.dist(start, end) / 2.0)))
        for step in range(1, steps + 1):
            fraction = step / float(steps)
            current['xy'].append(end if step == steps else
                                 (start[0] + fraction * (end[0] - start[0]),
                                  start[1] + fraction * (end[1] - start[1])))
        if upper == 1:
            current['originals'].append((len(current['xy']) - 1, source_index + 1))
        else:
            current['boundaries'].append(len(current['xy']) - 1)
            pieces.append(current)
            current = None
    if current is not None:
        pieces.append(current)
    return pieces


def _surface_r018_route_export(source, height, info):
    """Preserve source vertices; export bounded pieces on FINAL terrain."""
    records = []
    seen = set()
    for primitive in source.prims():
        cls = str(primitive.attribValue('highway_class'))
        if cls not in ROAD_CLASSES:
            continue
        osm_id = str(primitive.attribValue('source_osm_id'))
        if not osm_id or osm_id in seen:
            _fail('Native road export requires one complete source line per OSM ID: ' + osm_id)
        seen.add(osm_id)
        # This is a source line, not a face: retain duplicate closure vertices.
        ring = [(float(v.point().position()[0]), float(v.point().position()[2]))
                for v in primitive.vertices()]
        if len(ring) < 2:
            _fail('Native road export has a short source line: ' + osm_id)
        pieces = []
        for number, clipped in enumerate(_surface_r018_line_pieces(ring, _local_box(info))):
            xy = clipped['xy']
            elevations = _sample_grid(height, [p[0] for p in xy], [p[1] for p in xy])
            pieces.append({'piece_id': osm_id + ':' + str(number),
                           'points_m': [[float(p[0]), float(y), float(p[1])]
                                        for p, y in zip(xy, elevations)],
                           'original_point_indices': [i for i, _ in clipped['originals']],
                           'original_source_vertex_indices': [i for _, i in clipped['originals']],
                           'boundary_point_indices': clipped['boundaries']})
        records.append({'source_osm_id': osm_id, 'highway_class': cls,
                        'width_m': float(primitive.attribValue('width')),
                        'route_role': 'road',
                        'source_points_xz_m': [[float(x), float(z)] for x, z in ring],
                        'pieces': pieces})
    records.sort(key=lambda record: record['source_osm_id'])
    payload = json.dumps(records, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False)
    xmin, xmax, zmin, zmax = _local_box(info)
    return {'schema': 'environmentpipeline.roadbld_centerlines.v1',
            'area_id': info['area_id'], 'source_sha256': info['sha256'],
            'coordinate_frame': 'houdini_local_m_x_yup_z_to_unreal_cm_x_z_y',
            'centreline_sha256': hashlib.sha256(payload.encode('utf-8')).hexdigest(),
            'area_box_xz_m': [xmin, zmin, xmax, zmax],
            'maximum_sample_spacing_m': 2.0,
            'clip_policy': 'analytic_authoritative_area_box_no_endpoint_snapping',
            'roads': records}


def _surface_r018_provider(parent, export):
    """Suppress HDA vehicle meshes only after a complete retained native delivery."""
    provider = _surface_r018_parm(parent, 'road_provider', 'houdini').casefold()
    if provider == 'houdini':
        return {'provider': 'houdini', 'vehicle_mesh_suppressed': False,
                'vehicle_surfaces_suppressed': False,
                'reason': 'authoritative_houdini_visible_provider'}
    if provider != 'roadbld':
        _fail('road_provider must be houdini or RoadBLD')
    try:
        contract = json.loads(_surface_r018_parm(parent, 'road_provider_contract_json', '{}'))
    except (TypeError, ValueError):
        _fail('RoadBLD provider contract is not valid JSON')
    if not isinstance(contract, dict):
        _fail('RoadBLD provider contract must be an object')
    ids = [record['source_osm_id'] for record in export['roads']]
    if any(not record['pieces'] for record in export['roads']):
        _fail('Native road source includes a way with no in-area line piece')
    piece_ids = sorted(piece['piece_id'] for road in export['roads'] for piece in road['pieces'])
    expected = {'schema': 'environmentpipeline.roadbld_delivery.v1',
                'provider': 'RoadBLD', 'area_id': export['area_id'],
                'source_sha256': export['source_sha256'],
                'centreline_sha256': export['centreline_sha256'],
                'drivable_source_ids': ids, 'source_road_count': len(ids),
                'source_piece_count': len(piece_ids),
                'generated_road_count': len(piece_ids),
                'generated_piece_ids': piece_ids, 'mode': 'authored_native_retained',
                'geometry_validation_passed': True}
    for field, value in expected.items():
        if contract.get(field) != value:
            _fail('Incomplete or stale RoadBLD delivery contract: ' + field)
    named_map = contract.get('named_map', '')
    if (not isinstance(named_map, str) or
            not named_map.startswith('/Game/Project/Areas/' + export['area_id'] + '/') or
            '.' in named_map or ':' in named_map):
        _fail('RoadBLD delivery map is outside the exact geographic area')
    actor_prefix = named_map + '.' + named_map.rsplit('/', 1)[-1] + ':PersistentLevel.'
    network = contract.get('network_actor_path')
    actors = contract.get('road_actor_paths')
    if (not isinstance(network, str) or not network.startswith(actor_prefix) or
            not isinstance(actors, list) or len(actors) != len(piece_ids) or
            len(set(actors)) != len(actors) or
            not all(isinstance(path, str) and path.startswith(actor_prefix) for path in actors)):
        _fail('RoadBLD delivery actor identities are incomplete or outside the saved area')
    deliveries = contract.get('source_delivery')
    if not isinstance(deliveries, list) or len(deliveries) != len(ids):
        _fail('RoadBLD per-source delivery ledger is incomplete')
    expected_pieces = {road['source_osm_id']: sorted(p['piece_id'] for p in road['pieces'])
                       for road in export['roads']}
    delivered_paths = []
    delivered_sources = set()
    for delivery in deliveries:
        osm_id = delivery.get('source_osm_id')
        paths = delivery.get('road_actor_paths')
        if (osm_id not in expected_pieces or osm_id in delivered_sources or
                delivery.get('piece_ids') != expected_pieces[osm_id] or
                not isinstance(paths, list) or len(paths) != len(expected_pieces[osm_id])):
            _fail('RoadBLD per-source piece coverage differs: ' + str(osm_id))
        delivered_sources.add(osm_id)
        delivered_paths.extend(paths)
    if len(set(delivered_paths)) != len(piece_ids) or set(delivered_paths) != set(actors):
        _fail('RoadBLD per-source native actor identities differ')
    if contract.get('phase') == 'native_generated_saved_verified':
        if contract.get('saved') is not True:
            _fail('Final RoadBLD delivery has not been saved')
    elif contract.get('phase') == 'native_generated_validated_pending_save':
        transaction = contract.get('transaction', {})
        if (contract.get('saved') is not False or
                contract.get('livevalidated_editor_transaction') is not True or
                not isinstance(transaction, dict) or
                not isinstance(transaction.get('pid'), int) or transaction['pid'] <= 0 or
                transaction.get('named_map') != named_map or
                not isinstance(transaction.get('revision'), str) or not transaction['revision'] or
                not re.fullmatch(r'[a-fA-F0-9]{64}', str(transaction.get('lease_sha256', ''))) or
                not re.fullmatch(r'[A-Za-z0-9_.:-]{16,256}', str(transaction.get('token', '')))):
            _fail('Pending RoadBLD gate lacks the editor-owned validated transaction')
    else:
        _fail('RoadBLD delivery phase cannot activate the native provider')
    return {**contract, 'vehicle_mesh_suppressed': True,
            'vehicle_surfaces_suppressed': True,
            'contract': contract, 'reason': 'exact_complete_retained_native_delivery'}


def _surface_r018_route_materials(parent):
    # The existing scoped sidewalk material already supports the footway lane.
    # An empty path/track entry exposes the retained Dirt_Path RoadBed mask;
    # it does not remove source ways, widths, complete coverage or requests.
    materials = {'footway': {'path': '/Game/UtopianCity/Materials/MI_ConcreteGrain.MI_ConcreteGrain',
                             'uv_units_per_metre': 1.0},
                 'path': {'path': '', 'uv_units_per_metre': 1.0},
                 'track': {'path': '', 'uv_units_per_metre': 1.0}}
    try:
        override = json.loads(_surface_r018_parm(parent, 'route_surface_materials_json', '{}'))
    except (TypeError, ValueError):
        _fail('route_surface_materials_json is not valid JSON')
    if not isinstance(override, dict) or set(override).difference(materials):
        _fail('Route material overrides must name footway, path or track only')
    for cls, value in override.items():
        if isinstance(value, str):
            value = {'path': value, 'uv_units_per_metre': 1.0}
        if not isinstance(value, dict) or set(value).difference(('path', 'uv_units_per_metre')):
            _fail('Invalid route material entry: ' + cls)
        path = value.get('path', '')
        scale = float(value.get('uv_units_per_metre', 1.0))
        if (not isinstance(path, str) or
                (path and not re.fullmatch(r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+', path)) or
                not math.isfinite(scale) or scale <= 0 or scale > 16):
            _fail('Invalid native route material or UV scale: ' + cls)
        materials[cls] = {'path': path, 'uv_units_per_metre': scale}
    return materials


def _surface_r018_native_source(node):
    # Both grounded surface SOPs have [complete coverage, eligible lines, terrain].
    grounded = node.inputs()[0]
    if grounded is None or len(grounded.inputs()) < 3:
        _fail('Missing authoritative surface/line/final-terrain graph inputs')
    return grounded, grounded.inputs()[1].geometry(), grounded.inputs()[2].geometry()


def cook_permanent_surface_material(node):
    _surface_r018_previous_material(node)
    parent, geo = node.parent(), node.geometry()
    info = _package_for_sop(parent)
    grounded, source, terrain = _surface_r018_native_source(node)
    height = _grid_array(_volume(terrain, 'height'))
    export = _surface_r018_route_export(source, height, info)
    provider = _surface_r018_provider(parent, export)
    is_road = node.name() == 'catalog_road_material'
    route_materials = _surface_r018_route_materials(parent)
    pad_index = _surface_r018_pad_index(parent)
    attrs = {a.name(): a for a in geo.primAttribs()}
    material_attr = attrs['unreal_material']
    vertex_uv = geo.findVertexAttrib('uv')
    remove = []
    additions = []
    statistics = {'lane': 'road_surface' if is_road else 'sidewalk_surface',
                  'policy': 'class_aware_visible_profiles_final_terrain_building_pad_exclusion',
                  'source_coverage_preserved': True, 'road_provider': provider,
                  'class_input_faces': {}, 'class_visible_faces': {},
                  'class_mask_only_faces': {}, 'native_provider_suppressed_faces': 0,
                  'building_pad_excluded_area_m2': 0.0,
                  'route_materials': route_materials}
    if not is_road and grounded.geometry().findGlobalAttrib('joined_sidewalk_geometry_json'):
        statistics['joined_sidewalk'] = json.loads(grounded.geometry().attribValue('joined_sidewalk_geometry_json'))
    for prim in list(geo.prims()):
        cls = str(prim.attribValue('highway_class'))
        statistics['class_input_faces'][cls] = statistics['class_input_faces'].get(cls, 0) + 1
        if provider['vehicle_mesh_suppressed'] and cls in ROAD_CLASSES:
            remove.append(prim)
            statistics['native_provider_suppressed_faces'] += 1
            continue
        chosen = route_materials.get(cls) if is_road else None
        if chosen and not chosen['path']:
            remove.append(prim)
            statistics['class_mask_only_faces'][cls] = statistics['class_mask_only_faces'].get(cls, 0) + 1
            continue
        if chosen:
            prim.setAttribValue(material_attr, chosen['path'])
            for vertex in prim.vertices():
                p = vertex.point().position()
                vertex.setAttribValue(vertex_uv, (p[0] * chosen['uv_units_per_metre'],
                                                 p[2] * chosen['uv_units_per_metre'], 0.0))
        ring = _xy(prim)
        fragments = _permanent_sidewalk_without_roads(ring, pad_index)
        if fragments == [ring]:
            statistics['class_visible_faces'][cls] = statistics['class_visible_faces'].get(cls, 0) + 1
            continue
        statistics['building_pad_excluded_area_m2'] += max(
            0.0, abs(_signed_area(ring)) - sum(abs(_signed_area(f)) for f in fragments))
        values = {a.name(): prim.attribValue(a) for a in geo.primAttribs()}
        remove.append(prim)
        for fragment in fragments:
            additions.append((fragment, values, chosen))
            statistics['class_visible_faces'][cls] = statistics['class_visible_faces'].get(cls, 0) + 1
    if remove:
        geo.deletePrims(remove, keep_points=False)
    lift = 0.08 if is_road else 0.16
    for ring, values, chosen in additions:
        elevations = _sample_grid(height, [p[0] for p in ring], [p[1] for p in ring])
        prim = _add_polygon(geo, [(x, float(y) + lift, z) for (x, z), y in zip(ring, elevations)], values, attrs)
        scale = chosen['uv_units_per_metre'] if chosen else 1.0
        for vertex in prim.vertices():
            p = vertex.point().position()
            vertex.setAttribValue(vertex_uv, (p[0] * scale, p[2] * scale, 0.0))
    statistics['visible_face_count'] = len(geo.prims())
    _set_detail(geo, 'surface_geometry_json', json.dumps(statistics, sort_keys=True, allow_nan=False))
    _set_detail(geo, 'roadbld_centerlines_json', json.dumps(export, sort_keys=True, allow_nan=False))


def _surface_r018_join_candidates(edges, width):
    """Round convex corners; concave ribbons are united by subtraction."""
    def key(p):
        return (round(p[0], 4), round(p[1], 4))
    vertices = {}
    for a, b, values in edges:
        vertices.setdefault(key(a), {'point': a, 'incoming': [], 'outgoing': []})['outgoing'].append((a, b, values))
        vertices.setdefault(key(b), {'point': b, 'incoming': [], 'outgoing': []})['incoming'].append((a, b, values))
    for record in vertices.values():
        incoming, outgoing = record['incoming'], record['outgoing']
        if not incoming or not outgoing:
            continue
        point = record['point']
        values = dict(incoming[0][2])
        ids = sorted({i for edge in incoming + outgoing
                      for i in json.loads(edge[2]['source_ids_json'])})
        values['source_ids_json'] = json.dumps(ids)
        if len(ids) > 1:
            values['source_osm_id'] = ''
            values['source_id_status'] = 'ambiguous_near_junction'
        if len(incoming) != 1 or len(outgoing) != 1:
            # A bounded union disc also handles touching or branching outlines.
            ring = [(point[0] + width * math.cos(angle), point[1] + width * math.sin(angle))
                    for angle in np.linspace(0, 2 * math.pi, 32, endpoint=False)]
            yield ring, values, 'branch_round_join'
            continue
        a, b, _ = incoming[0]
        c, d, _ = outgoing[0]
        first = ((b[0] - a[0]), (b[1] - a[1]))
        second = ((d[0] - c[0]), (d[1] - c[1]))
        turn = math.atan2(first[0] * second[1] - first[1] * second[0],
                          first[0] * second[0] + first[1] * second[1])
        if turn <= 1e-6:
            continue
        first_length = math.hypot(*first)
        start = math.atan2(-first[0] / first_length, first[1] / first_length)
        steps = max(1, int(math.ceil(turn / (math.pi / 16))))
        arc = [(point[0] + width * math.cos(start + turn * step / steps),
                point[1] + width * math.sin(start + turn * step / steps))
               for step in range(steps + 1)]
        yield [point] + arc, values, 'convex_round_join'


def cook_sidewalks(node):
    """Joined drivable-road sidewalks; no walk/track asphalt-road convention."""
    parent, geo = node.parent(), node.geometry()
    info = _package_for_sop(parent)
    segments = _source_segments(node.inputs()[1].geometry())
    height = _grid_array(_volume(node.inputs()[2].geometry(), 'height'))
    raw = node.inputs()[0].geometry()
    boundaries = _permanent_exterior_road_edges(raw)
    # The index includes authoritative road union, true pads and then emitted
    # sidewalk triangles. Therefore corner/strip coverage is never duplicated.
    exclusions = _permanent_road_triangle_index(raw)
    pads = _surface_r018_pad_index(parent)
    for triangle, _ in pads[0]:
        _surface_r018_index_add(exclusions, triangle)
    geo.clear()
    attrs = _surface_attrs(geo)
    box = _local_box(info)
    width = 1.5
    edges, strips = [], []
    represented = set()
    status_counts = {}
    ledger = {'schema': 'environmentpipeline.joined_sidewalks.v1',
              'policy': 'drivable_exterior_union_round_joins_pad_exclusion_no_overlapping_profiles',
              'width_m': width, 'terrain_lift_m': 0.16,
              'maximum_round_join_chord_error_m': width * (1 - math.cos(math.pi / 32)),
              'drivable_edge_count': 0, 'non_drivable_edge_count': 0,
              'strip_candidate_count': 0, 'convex_round_join_count': 0,
              'branch_round_join_count': 0, 'retained_area_m2': 0.0,
              'retained_triangle_count': 0, 'source_coverage_preserved': True}
    for number in sorted(boundaries):
        for a, b, outside in boundaries[number]:
            midpoint = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            (distance, nearest_id, cls, declared), osm_id, status, candidates = _lineage(midpoint, segments)
            if cls not in ROAD_CLASSES or cls in NO_SIDEWALK_CLASSES:
                ledger['non_drivable_edge_count'] += 1
                continue
            if outside > 0:
                a, b = b, a
            length = math.dist(a, b)
            if length < 0.01:
                continue
            # Orient union boundary with interior left and exterior right.
            normal = ((b[1] - a[1]) / length, -(b[0] - a[0]) / length)
            values = {'source_osm_id': osm_id, 'nearest_osm_id': nearest_id,
                      'source_id_status': status, 'source_ids_json': json.dumps(candidates),
                      'nearest_distance_m': distance, 'source_area_id': info['area_id'],
                      'highway_class': cls, 'route_role': 'sidewalk', 'width_m': width,
                      'unreal_output_name': info['area_id'] + '_sidewalks',
                      'unreal_material': _mesh_preview_material(node), 'Cd': (0.51, 0.49, 0.44)}
            edges.append((a, b, values))
            strips.append(([a, b, (b[0] + width * normal[0], b[1] + width * normal[1]),
                            (a[0] + width * normal[0], a[1] + width * normal[1])], values))
            ledger['drivable_edge_count'] += 1
    def retain(ring, values):
        ring = _condition_surface_polygon(_clip_polygon(ring, box))
        if not ring:
            return
        fragments = _permanent_sidewalk_without_roads(ring, exclusions)
        for fragment in fragments:
            for indices in _triangles(fragment):
                triangle = _condition_surface_polygon([fragment[i] for i in indices])
                if not triangle:
                    continue
                elevations = _sample_grid(height, [p[0] for p in triangle], [p[1] for p in triangle])
                _add_polygon(geo, [(x, float(y) + 0.16, z) for (x, z), y in zip(triangle, elevations)], values, attrs)
                ledger['retained_area_m2'] += _surface_r018_index_add(exclusions, triangle)
                ledger['retained_triangle_count'] += 1
                if values['source_osm_id']:
                    represented.add(values['source_osm_id'])
                status = values['source_id_status']
                status_counts[status] = status_counts.get(status, 0) + 1
    for ring, values in strips:
        retain(ring, values)
        ledger['strip_candidate_count'] += 1
    for ring, values, kind in _surface_r018_join_candidates(edges, width):
        retain(ring, values)
        ledger[kind + '_count'] += 1
    _output_context(geo, info, parent.evalParm('seed'))
    _set_detail(geo, 'represented_road_ids_json', json.dumps(sorted(represented)))
    _set_detail(geo, 'lineage_status_counts_json', json.dumps(status_counts, sort_keys=True))
    _set_detail(geo, 'discarded_degenerate_faces', 0)
    _set_detail(geo, 'unreal_output_name', info['area_id'] + '_sidewalks')
    _set_detail(geo, 'joined_sidewalk_geometry_json', json.dumps(ledger, sort_keys=True, allow_nan=False))


def cook_nonbuilding_selector(node):
    _surface_r018_previous_selector(node)
    geo = node.geometry()
    if not geo.findGlobalAttrib('bank_catalog_readback_json'):
        return
    receipt = json.loads(geo.attribValue('bank_catalog_readback_json'))
    reports = {}
    export = None
    for name in ('catalog_road_material', 'catalog_sidewalk_material'):
        surface = node.parent().node(name)
        if surface is None:
            _fail('Missing retained surface material node: ' + name)
        output = surface.geometry()
        if not output.findGlobalAttrib('surface_geometry_json'):
            _fail('Missing completed surface geometry ledger: ' + name)
        reports[name] = json.loads(output.attribValue('surface_geometry_json'))
        current = json.loads(output.attribValue('roadbld_centerlines_json'))
        if export is not None and current != export:
            _fail('Road and sidewalk authoritative centreline exports differ')
        export = current
    provider = reports['catalog_road_material']['road_provider']
    if reports['catalog_sidewalk_material']['road_provider'] != provider:
        _fail('Road and sidewalk visible providers differ')
    receipt['surface_geometry'] = {
        'schema': 'environmentpipeline.class_aware_surface_geometry.v1',
        'road_provider': provider, 'outputs': reports,
        'source_coverage_preserved': True}
    receipt['roadbld_centerlines'] = export
    _set_detail(geo, 'bank_catalog_readback_json', json.dumps(receipt, sort_keys=True, allow_nan=False))
    path = node.parent().evalParm('bank_receipt_file').strip()
    if path:
        Path(path).write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False), encoding='utf-8')


"""Append after the retained r017 normal assembly implementation.

Only a validated building_style_variants field in the existing scoped assembly
contract enables this patch. Native whole-building selection is untouched.
Native bounds, closure/door/height/footprint and final terrain gates are reused.
"""

_STYLE_VARIETY_MESH_PATHS = {
    'closed4': '/Game/ModularCourtyard/Meshes/SM_wall_windows_close_4x4_01.SM_wall_windows_close_4x4_01',
    'single4': '/Game/ModularCourtyard/Meshes/SM_wall_windows_one_4x4_open.SM_wall_windows_one_4x4_open',
    'narrow2': '/Game/ModularCourtyard/Meshes/SM_wall_windowsT2_4x2_01.SM_wall_windowsT2_4x2_01',
}
_STYLE_WALL_SOURCE = '/Game/ModularCourtyard/Mats/MI_Wall_PlasterBrick.MI_Wall_PlasterBrick'
_STYLE_VARIETY_PREVIOUS_CONTRACT = _assembly_contract
_STYLE_VARIETY_PREVIOUS_LAYOUT = assembly_layout
_STYLE_VARIETY_PREVIOUS_COOK = cook_normal_building_assembly_points


def _style_game_path(value):
    return isinstance(value, str) and re.fullmatch(r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+', value)


def _style_surface_indices(module):
    original = module.get('original_material_slots', [])
    return [i for i, path in enumerate(original) if path == _STYLE_WALL_SOURCE]


def _style_validate(contract, area_id):
    styles = contract.get('building_style_variants')
    if not styles or not styles.get('enabled'):
        return None
    if styles.get('schema') != 'environmentpipeline.native_building_styles.v1':
        raise ValueError('building_style_schema_mismatch')
    scopes = set(styles.get('scope_area_ids', []))
    # v005: the profile's own scope list or the general token authorizes the area.
    if area_id not in scopes and 'any_validated_area' not in scopes:
        raise ValueError('building_style_area_outside_scoped_authorization')
    modules = styles.get('modules', {})
    families = [f for f in styles.get('families', []) if f.get('enabled', True)]
    palettes = [p for p in styles.get('palettes', []) if p.get('enabled', True)]
    for entries, label in ((families, 'family'), (palettes, 'palette')):
        ids = [entry.get('id') for entry in entries]
        if len(ids) != len(set(ids)) or any(not isinstance(i, str) or not re.fullmatch(r'[a-z0-9_]+', i) for i in ids):
            raise ValueError('building_style_invalid_' + label + '_identity')
        for entry in entries:
            weight = float(entry.get('weight', 1.0))
            if not math.isfinite(weight) or weight <= 0:
                raise ValueError('building_style_invalid_' + label + '_weight')
    if len(families) < 2 or len(palettes) < 2:
        raise ValueError('building_style_requires_real_mesh_families_and_native_palettes')
    window_paths = set()
    used_keys = set()
    for family in families:
        overrides = family.get('module_overrides', {})
        if not set(overrides) <= {'window4', 'plain4', 'plain2', 'plain1'}:
            raise ValueError('building_style_door_or_unknown_module_override')
        if any(key not in modules for key in overrides.values()):
            raise ValueError('building_style_module_registry_missing')
        used_keys.update(overrides.values())
        window_key = overrides.get('window4')
        window_paths.add(modules[window_key]['path'] if window_key else contract['modules']['window4']['path'])
    if len(window_paths) < 2:
        raise ValueError('building_style_mesh_variety_cannot_be_only_recoloring')
    for key in used_keys:
        module = modules[key]
        if module.get('path') != _STYLE_VARIETY_MESH_PATHS.get(key):
            raise ValueError('building_style_mesh_outside_exact_native_whitelist:' + key)
        if (module.get('actual_named_or_dependency_hold') is not False
                or module.get('dependency_status') != 'closed'
                or module.get('route_hold_preserved') is not True
                or not module.get('native_measurement_source')
                or module.get('axis_contract') != 'X_inward_minusY_along_Z_up'):
            raise ValueError('building_style_native_dependency_measurement_or_axis_unconfirmed:' + key)
        low, high = module.get('min_cm', []), module.get('max_cm', [])
        if len(low) != 3 or len(high) != 3 or not all(math.isfinite(float(v)) for v in low + high):
            raise ValueError('building_style_native_bounds_invalid:' + key)
        if any(float(high[i]) <= float(low[i]) for i in range(3)):
            raise ValueError('building_style_native_bounds_degenerate:' + key)
        if (float(high[0]) - float(low[0])) / 100.0 > float(contract['closure_thickness_m']) + 1e-6:
            raise ValueError('building_style_native_depth_exceeds_retained_closure_envelope:' + key)
        slots = module.get('material_slots', [])
        originals = module.get('original_material_slots', [])
        if not slots or len(slots) != len(originals) or not all(_style_game_path(p) for p in slots + originals):
            raise ValueError('building_style_native_slots_missing:' + key)
        if not _style_surface_indices(module):
            raise ValueError('building_style_native_wall_surface_slot_unconfirmed:' + key)
    for palette in palettes:
        if (palette.get('source_material_path') != _STYLE_WALL_SOURCE
                or palette.get('dependency_status') != 'closed'
                or palette.get('actual_named_or_dependency_hold') is not False
                or not palette.get('native_parameter_evidence')
                or not _style_game_path(palette.get('surface_material_path'))
                or not palette['surface_material_path'].startswith('/Game/Project/Shared/ModelBank/Materials/')):
            raise ValueError('building_style_native_palette_unconfirmed:' + palette['id'])
    return styles


def _assembly_contract(parent, area_id):
    contract = _STYLE_VARIETY_PREVIOUS_CONTRACT(parent, area_id)
    if contract is not None:
        _style_validate(contract, area_id)
    return contract


def _style_order(entries, seed, area_id, osm_id, tag):
    """Stable weighted ordering; changes to material paths do not reshuffle lots."""
    def score(entry):
        identity = '%s|%s|%s|%s|%s' % (seed, area_id, osm_id, tag, entry['id'])
        digest = hashlib.sha256(identity.encode('utf-8')).hexdigest()
        fraction = (int(digest[:15], 16) + 0.5) / float(16 ** 15)
        return (-math.log(fraction) / float(entry.get('weight', 1.0)), entry['id'])
    return sorted(entries, key=score)


def _style_family_contract(contract, styles, family, palette):
    chosen = dict(contract)
    chosen['modules'] = {key: dict(module) for key, module in contract['modules'].items()}
    for key, variant_key in family.get('module_overrides', {}).items():
        chosen['modules'][key] = dict(styles['modules'][variant_key])
    for key, module in chosen['modules'].items():
        if key == 'door':
            continue
        indices = _style_surface_indices(module)
        if not indices:
            raise ValueError('building_style_wall_surface_slot_missing:' + key)
        slots = list(module['material_slots'])
        for index in indices:
            slots[index] = palette['surface_material_path']
        module['material_slots'] = slots
    chosen['closure_material_path'] = palette['surface_material_path']
    return chosen


def assembly_layout(feature, contract):
    styles = _style_validate(contract, feature['area_id'])
    if styles is None:
        return _STYLE_VARIETY_PREVIOUS_LAYOUT(feature, contract)
    seed, area_id, osm_id = int(styles.get('selection_seed', 1337)), feature['area_id'], str(feature['osm_id'])
    families = _style_order([f for f in styles['families'] if f.get('enabled', True)], seed, area_id, osm_id, 'family')
    palettes = _style_order([p for p in styles['palettes'] if p.get('enabled', True)], seed, area_id, osm_id, 'palette')
    palette, rejected = palettes[0], []
    for family in families:
        try:
            selected_contract = _style_family_contract(contract, styles, family, palette)
            record = _STYLE_VARIETY_PREVIOUS_LAYOUT(feature, selected_contract)
            for item in record['wall_placements']:
                if not _assembly_polygon_contained(item['footprint_xz_m'], record['footprint_xz_m']):
                    raise ValueError('building_style_native_envelope_leaves_geographic_footprint')
        except ValueError as error:
            rejected.append({'family_id': family['id'], 'reason': str(error)})
            continue
        record['style_family_id'] = family['id']
        record['style_palette_id'] = palette['id']
        record['style_selection'] = {'policy': 'source_building_stable_weighted_family_and_palette',
            'seed': seed, 'requested_family_order': [f['id'] for f in families], 'rejected_families': rejected,
            'native_mesh_variety': True, 'door_slab_source_height_and_footprint_rules_preserved': True}
        for item in record['wall_placements']:
            item['style_family_id'] = family['id']
            item['style_palette_id'] = palette['id']
            item['material_signature'] = hashlib.sha256(json.dumps(item['material_slots'], separators=(',', ':')).encode()).hexdigest()[:16]
        return record
    # A style miss never destroys previously valid native building coverage.
    record = _STYLE_VARIETY_PREVIOUS_LAYOUT(feature, contract)
    record['style_family_id'] = 'retained_safe_baseline'
    record['style_palette_id'] = 'retained_native_materials'
    record['style_selection'] = {'policy': 'explicit_style_fit_failed_retained_baseline', 'seed': seed,
        'requested_family_order': [f['id'] for f in families], 'rejected_families': rejected}
    for item in record['wall_placements']:
        item['style_family_id'] = record['style_family_id']
        item['style_palette_id'] = record['style_palette_id']
        item['material_signature'] = hashlib.sha256(json.dumps(item['material_slots'], separators=(',', ':')).encode()).hexdigest()[:16]
    return record


def cook_normal_building_assembly_points(node):
    _STYLE_VARIETY_PREVIOUS_COOK(node)
    geo = node.geometry()
    if geo.findGlobalAttrib('building_assembly_records_json') is None:
        return
    records = json.loads(geo.attribValue('building_assembly_records_json'))
    if not records or not any('style_family_id' in record for record in records):
        return
    by_id = {item['placement_id']: item for record in records for item in record['wall_placements']}
    for point in geo.points():
        placement_id = point.attribValue('placement_id')
        item = by_id.get(placement_id)
        values = {'assembly_style_id': item['style_family_id'] if item else '',
            'assembly_palette_id': item['style_palette_id'] if item else '',
            'assembly_material_signature': item['material_signature'] if item else 'retained_native_default'}
        for key, value in values.items():
            point.setAttribValue(_attr(geo, hou.attribType.Point, key, ''), value)
    # Official installed translator reads this attribute-name declaration, then
    # point strings to split instance groups before applying native overrides.
    _set_detail(geo, 'unreal_split_attr', 'assembly_material_signature')
    receipt = json.loads(geo.attribValue('bank_catalog_readback_json'))
    family_counts, palette_counts, rejected_reasons, component_counts = {}, {}, {}, {}
    for record in records:
        family = record['style_family_id']; palette = record['style_palette_id']
        family_counts[family] = family_counts.get(family, 0) + 1
        palette_counts[palette] = palette_counts.get(palette, 0) + 1
        for rejection in record.get('style_selection', {}).get('rejected_families', []):
            reason = rejection['reason']; rejected_reasons[reason] = rejected_reasons.get(reason, 0) + 1
        for item in record['wall_placements']:
            key = (item['path'], tuple(item['material_slots']))
            component_counts[key] = component_counts.get(key, 0) + 1
    summary = {'schema': 'environmentpipeline.native_building_style_summary.v1',
        'family_building_counts': family_counts, 'palette_building_counts': palette_counts,
        'candidate_family_rejection_reasons': rejected_reasons,
        'expected_assembly_mesh_material_counts': [{'mesh': key[0], 'material_slots': list(key[1]), 'instances': count}
            for key, count in sorted(component_counts.items())],
        'official_instance_split_attribute': 'assembly_material_signature',
        'native_part_placement_ids_preserved': True, 'appearance_accepted': False}
    receipt['building_style_variants'] = summary
    receipt['building_assembly']['style_family_counts'] = family_counts
    receipt['building_assembly']['style_palette_counts'] = palette_counts
    _set_detail(geo, 'building_style_summary_json', json.dumps(summary, sort_keys=True))
    _set_detail(geo, 'building_assembly_summary_json', json.dumps(receipt['building_assembly'], sort_keys=True))
    _set_detail(geo, 'bank_catalog_readback_json', json.dumps(receipt, sort_keys=True, allow_nan=False))
    report = node.parent().evalParm('bank_receipt_file').strip()
    if report:
        Path(report).write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False), encoding='utf-8')


"""Candidate append for the retained GeoCity PythonModule; no native side effects.

The source family lane preserves complete source assemblies and their materials.
It is separate from Courtyard bays/palettes, but uses the retained assembly record,
native point translator, final-terrain check, replacement and persistence ledger.
Importing this file alone installs no hook; appending it after the retained module
installs only an assembly_layout wrapper. Production embedding belongs to owner.
"""
import hashlib
import json
import math
import re
from pathlib import Path

SOURCE_FAMILY_PROTOCOL = 'environmentpipeline.retained_source_family_registry.v1'
SOURCE_NATIVE_PROTOCOL = 'environmentpipeline.modular_native_family_readback.v1'
SOURCE_ROUTE_PROTOCOL = 'environmentpipeline.modular_route_authorization.v1'
SOURCE_CAPABILITY_GATES = ('source_reconstruction', 'native_import', 'houdini_repeat',
    'official_engine_output', 'material_appearance', 'named_save', 'fresh_reopen', 'regeneration')
SOURCE_BAND_GATES = ('connection_geometry', 'texture_phase', 'openings_corners_roof')
SOURCE_QUALIFICATION_VALIDATION_GATES = ('houdini_repeat', 'official_engine_output',
    'named_save', 'fresh_reopen', 'regeneration', 'native_material_visual_fidelity',
    'native_reflection_normals_material_culling')
_SOURCE_PART_PATH = re.compile(r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+')
_SOURCE_FAMILY_USE_CONTEXT = {}
_SOURCE_FAMILY_EVIDENCE_CACHE = None


class SourceFamilyQualificationError(ValueError):
    """An explicitly assigned qualification cannot silently fall back."""


def _sf_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode('utf-8')).hexdigest()


def _sf_load_ref(ref):
    if not isinstance(ref, dict) or not isinstance(ref.get('path'), str):
        raise ValueError('source_family_evidence_ref_missing')
    digest = ref.get('sha256', '')
    if not re.fullmatch('[0-9a-f]{64}', digest):
        raise ValueError('source_family_evidence_digest_invalid')
    key = (ref['path'], digest)
    if _SOURCE_FAMILY_EVIDENCE_CACHE is not None and key in _SOURCE_FAMILY_EVIDENCE_CACHE:
        return _SOURCE_FAMILY_EVIDENCE_CACHE[key]
    data = Path(ref['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('source_family_evidence_changed:' + ref['path'])
    value = json.loads(data.decode('utf-8-sig'))
    if _SOURCE_FAMILY_EVIDENCE_CACHE is not None:
        _SOURCE_FAMILY_EVIDENCE_CACHE[key] = value
    return value


def _sf_vec(value, size=3):
    if not isinstance(value, (tuple, list)) or len(value) != size:
        raise ValueError('source_family_vector_shape_invalid')
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in value):
        raise ValueError('source_family_nonfinite_or_non_numeric_transform')
    return [float(v) for v in value]


def _sf_mul(matrix, point):
    return [sum(matrix[i][j] * point[j] for j in range(3)) for i in range(3)]


def _sf_basis(value):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError('source_family_native_basis_missing')
    matrix = [_sf_vec(row) for row in value]
    # Only a measured signed axis permutation is supported by this candidate.
    # No unit multiplication, shear or geometric adaptation is hidden here.
    for row in matrix:
        if sum(abs(v) == 1.0 for v in row) != 1 or any(v not in (-1.0, 0.0, 1.0) for v in row):
            raise ValueError('source_family_native_basis_not_signed_permutation')
    if any(sum(abs(matrix[i][j]) for i in range(3)) != 1 for j in range(3)):
        raise ValueError('source_family_native_basis_nonorthogonal')
    if matrix[2] != [0.0, 0.0, 1.0]:
        raise ValueError('source_family_source_up_not_native_positive_Z')
    determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    return matrix, determinant


def _sf_transformed_bounds(low, high, matrix):
    low, high = _sf_vec(low), _sf_vec(high)
    # Original architecture can contain single-surface roofs/walls. Do not add
    # thickness or reject a legitimate planar source part to make an AABB solid.
    if any(high[i] < low[i] for i in range(3)) or sum(high[i] > low[i] for i in range(3)) < 2:
        raise ValueError('source_family_bounds_degenerate')
    corners = [_sf_mul(matrix, [x, y, z]) for x in (low[0], high[0])
        for y in (low[1], high[1]) for z in (low[2], high[2])]
    return ([min(p[i] for p in corners) for i in range(3)],
            [max(p[i] for p in corners) for i in range(3)])


def _sf_cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def _sf_on(p, a, b):
    return abs(_sf_cross(a, b, p)) <= 1e-7 * max(1.0, math.dist(a, b)) and all(
        min(a[i], b[i])-1e-7 <= p[i] <= max(a[i], b[i])+1e-7 for i in range(2))


def _sf_inside(p, ring):
    if any(_sf_on(p, a, ring[(i+1) % len(ring)]) for i, a in enumerate(ring)):
        return True
    inside = False
    for i, a in enumerate(ring):
        b = ring[(i+1) % len(ring)]
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < a[0] + (p[1]-a[1])*(b[0]-a[0])/(b[1]-a[1]):
            inside = not inside
    return inside


def _sf_proper_cross(a, b, c, d):
    ac, ad, ca, cb = _sf_cross(a, b, c), _sf_cross(a, b, d), _sf_cross(c, d, a), _sf_cross(c, d, b)
    return ac * ad < -1e-14 and ca * cb < -1e-14


def _sf_contained(polygon, ring):
    probes = list(polygon) + [[(a[0]+polygon[(i+1) % len(polygon)][0])/2,
        (a[1]+polygon[(i+1) % len(polygon)][1])/2] for i, a in enumerate(polygon)]
    return all(_sf_inside(p, ring) for p in probes) and not any(
        _sf_proper_cross(a, polygon[(i+1) % len(polygon)], b, ring[(j+1) % len(ring)])
        for i, a in enumerate(polygon) for j, b in enumerate(ring))


def _sf_feature(feature):
    if feature.get('closed') is not True or feature.get('holes'):
        raise ValueError('source_family_requires_single_closed_hole_free_pad')
    ring = [_sf_vec(p, 2) for p in feature.get('ring_xz_m', [])]
    if len(ring) > 3 and math.dist(ring[0], ring[-1]) < 1e-7:
        ring.pop()
    if not 3 <= len(ring) <= 128 or any(math.dist(a, ring[(i+1) % len(ring)]) < 1e-7 for i, a in enumerate(ring)):
        raise ValueError('source_family_pad_vertices_invalid')
    area = sum(a[0]*ring[(i+1) % len(ring)][1]-a[1]*ring[(i+1) % len(ring)][0] for i, a in enumerate(ring))/2
    if abs(area) < 1.0:
        raise ValueError('source_family_pad_area_invalid')
    for i, a in enumerate(ring):
        for j in range(i+1, len(ring)):
            if j in ((i+1) % len(ring), i) or i == (j+1) % len(ring):
                continue
            b, c, d = ring[(i+1) % len(ring)], ring[j], ring[(j+1) % len(ring)]
            if _sf_proper_cross(a, b, c, d) or any((_sf_on(a, c, d), _sf_on(b, c, d), _sf_on(c, a, b), _sf_on(d, a, b))):
                raise ValueError('source_family_self_intersecting_pad')
    base, height = _sf_vec([feature.get('base_m'), feature.get('height_m')], 2)
    if height <= 0:
        raise ValueError('source_family_requested_height_invalid')
    area_id, osm_id = str(feature.get('area_id', '')), str(feature.get('osm_id', ''))
    if not area_id or not osm_id:
        raise ValueError('source_family_source_identity_missing')
    return ring, base, height, area_id, osm_id


def _sf_pad_edge_yaw(feature):
    ring = _sf_feature(feature)[0]
    edges = [(math.dist(a, ring[(i+1) % len(ring)]), tuple(a), tuple(ring[(i+1) % len(ring)]))
        for i, a in enumerate(ring)]
    _, a, b = sorted(edges, key=lambda item: (-item[0], item[1], item[2]))[0]
    return math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))


def _sf_capability(entry, mode, count, family_digest, native_digest):
    capability = entry.get('capabilities', {}).get(mode, {})
    if capability.get('enabled') is not True:
        raise ValueError('source_family_capability_disabled:' + mode)
    counts = capability.get('allowed_repeat_counts', [1] if mode == 'exact_reconstruction' else [])
    if count not in counts:
        raise ValueError('source_family_repeat_count_not_individually_qualified')
    gates = SOURCE_CAPABILITY_GATES + (SOURCE_BAND_GATES if mode == 'one_axis_extension' else ())
    for gate in gates:
        evidence = capability.get('evidence', {}).get(gate, {})
        if (evidence.get('passed') is not True or evidence.get('source_family_sha256') != family_digest
                or evidence.get('native_manifest_sha256') != native_digest or count not in evidence.get('repeat_counts', [])):
            raise ValueError('source_family_capability_evidence_missing_or_stale:' + gate)
        receipt = _sf_load_ref(evidence.get('receipt_ref'))
        if (receipt.get('contract_test_only') or receipt.get('passed') is not True or receipt.get('family_id') != entry['family_id']
                or receipt.get('gate') != gate or receipt.get('source_family_sha256') != family_digest
                or receipt.get('native_manifest_sha256') != native_digest or count not in receipt.get('repeat_counts', [])):
            raise ValueError('source_family_capability_receipt_mismatch:' + gate)
    return capability


def _sf_authorization(entry, family, native, mode, count, area_id, osm_id, qualification=False, connection=False):
    author = _sf_load_ref(entry.get('route_authorization_ref'))
    if (author.get('contract_test_only') or author.get('schema') != SOURCE_ROUTE_PROTOCOL or author.get('approved') is not True
            or author.get('family_id') != family['family_id'] or author.get('parent_asset_id') != family['parent_asset_id']
            or not author.get('manager_thread_id') or author.get('preserve_canonical_holds') is not True
            or author.get('actual_named_or_dependency_hold') is not False
            or author.get('use_scope') != 'retained_complete_family_dependency'
            or area_id not in author.get('allowed_area_ids', []) or mode not in author.get('capabilities', [])
            or count not in author.get('allowed_repeat_counts', [1])
            or author.get('source_family_sha256') != _sf_digest(family)
            or author.get('native_manifest_sha256') != (entry.get('native_manifest_ref') or {}).get('sha256')):
        raise ValueError('source_family_route_or_inherited_hold_authorization_missing')
    ids = author.get('allowed_source_osm_ids', {})
    if author.get('placement_scope') == 'exact_ids':
        if osm_id not in ids.get(area_id, []):
            raise ValueError('source_family_source_id_outside_authorization')
    elif author.get('placement_scope') != 'approved_areas':
        raise ValueError('source_family_placement_scope_unrecognized')
    if native.get('actual_named_or_dependency_hold') is not False or native.get('parent_canonical_hold_preserved') is not True:
        raise ValueError('source_family_native_dependency_hold_or_preservation_invalid')
    expected_execution = 'connection' if connection else ('qualification' if qualification else 'ordinary_selection')
    if author.get('execution_mode') != expected_execution:
        raise ValueError('source_family_execution_mode_not_authorized')
    if author.get('ordinary_selection_authorized') is not (not qualification):
        raise ValueError('source_family_ordinary_selection_authorization_flag_invalid')
    if connection:
        if (qualification or mode != 'exact_reconstruction' or count != 1
                or author.get('connection_without_additional_tests_authorized') is not True
                or author.get('unperformed_validation_remains_pending') is not True):
            raise ValueError('source_family_direct_connection_scope_invalid')
    if qualification:
        if author.get('placement_scope') != 'exact_ids':
            raise ValueError('source_family_qualification_requires_exact_source_ids')
        if not set(SOURCE_QUALIFICATION_VALIDATION_GATES) <= set(author.get('allowed_validation_gates', [])):
            raise ValueError('source_family_qualification_lifecycle_scope_incomplete')
    if qualification or connection:
        source_receipt = _sf_load_ref(entry.get('source_qualification_ref'))
        if (source_receipt.get('contract_test_only') or source_receipt.get('passed') is not True
                or source_receipt.get('family_id') != family['family_id']
                or source_receipt.get('source_family_sha256') != _sf_digest(family)
                or count not in source_receipt.get('repeat_counts_by_capability', {}).get(mode, [])):
            raise ValueError('source_family_qualification_source_capability_not_proven')
        graph_receipt = _sf_load_ref(native.get('material_graph_evidence_ref'))
        if (graph_receipt.get('contract_test_only') or graph_receipt.get('passed') is not True
                or graph_receipt.get('family_id') != family['family_id']
                or graph_receipt.get('source_family_sha256') != _sf_digest(family)
                or graph_receipt.get('native_parts_sha256') != _sf_digest(native.get('parts', {}))
                or any(graph_receipt.get(key) is not True for key in ('source_recipes_bound',
                    'texture_dependencies_complete', 'mesh_slot_order_preserved'))):
            raise ValueError('source_family_qualification_native_material_graph_unverified')
    return author


def _sf_native_parts(family, native, mode, audit_only=False, pending_reflection_authorized=False):
    if native.get('schema') != SOURCE_NATIVE_PROTOCOL or native.get('family_id') != family['family_id']:
        raise ValueError('source_family_native_manifest_identity_invalid')
    if native.get('source_family_sha256') != _sf_digest(family):
        raise ValueError('source_family_native_manifest_source_binding_stale')
    matrix, determinant = _sf_basis(native.get('source_to_native_matrix'))
    basis_receipt = _sf_load_ref(native.get('basis_evidence_ref'))
    if not audit_only and (native.get('contract_test_only') or basis_receipt.get('contract_test_only')):
        raise ValueError('source_family_synthetic_native_fixture_not_runtime_evidence')
    if (basis_receipt.get('family_id') != family['family_id'] or basis_receipt.get('passed') is not True
            or basis_receipt.get('source_family_sha256') != _sf_digest(family)
            or basis_receipt.get('source_to_native_matrix') != matrix
            or basis_receipt.get('native_units') != 'centimetres'
            or basis_receipt.get('source_units') != 'metres'
            or basis_receipt.get('pivot_translation_preserved') is not True
            or basis_receipt.get('sample_vertices_checked', 0) < 3):
        raise ValueError('source_family_native_basis_probe_evidence_invalid')
    if (determinant < 0 and basis_receipt.get('reflection_normals_material_culling_verified') is not True
            and not pending_reflection_authorized):
        raise ValueError('source_family_reflection_appearance_unverified')
    probe_error = _sf_vec([basis_receipt.get('maximum_probe_error_cm')], 1)[0]
    if probe_error < 0 or probe_error > 0.15:
        raise ValueError('source_family_native_probe_error_exceeds_1p5mm')
    kind = 'reconstruction' if mode == 'exact_reconstruction' else 'extension'
    matches = [s for s in family.get('sets', []) if s.get('kind') == kind]
    if len(matches) != 1 or not matches[0].get('parts'):
        raise ValueError('source_family_complete_source_set_missing:' + kind)
    sources = matches[0]['parts']
    names = [p['name'] for p in sources]
    if len(names) != len(set(names)):
        raise ValueError('source_family_duplicate_source_part_identity')
    if not set(names) <= set(basis_receipt.get('verified_part_names', [])):
        raise ValueError('source_family_native_basis_not_verified_for_every_part')
    if mode == 'exact_reconstruction':
        assembly = _sf_load_ref({'path': family.get('assembly_path'), 'sha256': family.get('assembly_sha256')})
        authored = {part['name']: part for part in assembly.get('modules', [])}
        if assembly.get('id') != family['id'] or set(names) != set(authored):
            raise ValueError('source_family_partial_reconstruction_or_source_identity_mismatch')
        for source in sources:
            original = authored[source['name']]
            if (source['fbx_sha256'] != original['sha256']
                    or source['assembly_translation_m'] != original['original_assembly_translation_m']
                    or source['local_bounds_m'] != original['local_bounds_m']):
                raise ValueError('source_family_source_bounds_pivot_or_fbx_changed')
    native_parts = native.get('parts', {})
    selected = []
    for source in sources:
        name = source['name']; part = native_parts.get(name, {})
        expected_path = source['native_package'] + '.' + name
        if (part.get('path') != expected_path or not _SOURCE_PART_PATH.fullmatch(expected_path)
                or part.get('asset_id') != family['family_id'] + '/' + name
                or part.get('source_sha256') != source['fbx_sha256']
                or part.get('actual_named_or_dependency_hold') is not False
                or part.get('dependency_closed') is not True or part.get('pivot_preserved') is not True
                or part.get('source_uv0_probe_alignment_passed') is not True
                or part.get('uv_channel_count_verified') is not True
                or part.get('source_material_slots') != source['source_material_slots']):
            raise ValueError('source_family_native_part_binding_incomplete:' + name)
        slots = part.get('material_slots', [])
        indices = part.get('native_source_slot_indices', [])
        if (not isinstance(slots, list) or not isinstance(indices, list) or not slots
                or len(slots) != len(indices) or len(indices) != len(set(indices))
                or any(isinstance(i, bool) or not isinstance(i, int) or not 0 <= i < len(source['source_material_slots']) for i in indices)
                or any(not isinstance(p, str) or not _SOURCE_PART_PATH.fullmatch(p) for p in slots)):
            raise ValueError('source_family_native_material_slots_incomplete:' + name)
        used_source = {int(index) for index, count in part.get('source_slot_triangle_counts', source.get('slot_triangle_counts', {})).items() if count > 0}
        if not used_source <= set(indices):
            raise ValueError('source_family_used_source_material_slot_missing:' + name)
        low = [v/100 for v in _sf_vec(part.get('min_cm'))]
        high = [v/100 for v in _sf_vec(part.get('max_cm'))]
        expected_low, expected_high = _sf_transformed_bounds(source['local_bounds_m']['min'], source['local_bounds_m']['max'], matrix)
        if max(abs(a-b) for a, b in zip(low+high, expected_low+expected_high)) > 0.0015:
            raise ValueError('source_family_native_scale_axes_or_bounds_mismatch:' + name)
        translation = _sf_mul(matrix, _sf_vec(source['assembly_translation_m']))
        selected.append((source, part, low, high, translation))
    return matrix, selected


def source_family_plan(feature, family, native, entry, mode='exact_reconstruction', repeat_count=1,
                       yaw_degrees=0.0, audit_only=False, contains=None, qualification=False, connection=False):
    """Pure complete-family plan; audit_only never authorizes runtime selection.

    Native meshes already contain the measured source-to-native basis. Apply that
    basis once to assembly translations, convert native cm bounds once to metres,
    then map native XYZ metres to Houdini XZY. Point orient rotates the complete
    family rigidly around up; it never applies a second FBX conversion or scale.
    """
    if mode not in ('exact_reconstruction', 'one_axis_extension'):
        raise ValueError('source_family_unsupported_capability')
    if isinstance(repeat_count, bool) or not isinstance(repeat_count, int) or repeat_count < 1:
        raise ValueError('source_family_repeat_count_invalid')
    if mode == 'exact_reconstruction' and repeat_count != 1:
        raise ValueError('source_family_exact_reconstruction_cannot_repeat')
    if feature.get('requested_floor_count') is not None or feature.get('requested_scale') is not None:
        raise ValueError('source_family_floors_or_geometric_scaling_not_supported')
    ring, base, requested_height, area_id, osm_id = _sf_feature(feature)
    yaw = _sf_vec([yaw_degrees], 1)[0]
    family_digest = _sf_digest(family)
    native_digest = (entry.get('native_manifest_ref') or {}).get('sha256', '')
    authorization = None
    if not audit_only:
        if not qualification and not connection:
            _sf_capability(entry, mode, repeat_count, family_digest, native_digest)
        authorization = _sf_authorization(entry, family, native, mode, repeat_count, area_id, osm_id,
            qualification=qualification, connection=connection)
    pending_reflection_authorized = bool(authorization and (
        (qualification and 'native_reflection_normals_material_culling' in authorization.get('allowed_validation_gates', []))
        or (connection and authorization.get('unperformed_validation_remains_pending') is True)))
    matrix, selected = _sf_native_parts(family, native, mode, audit_only=audit_only,
        pending_reflection_authorized=pending_reflection_authorized)
    pending_gates = []
    if (qualification or connection) and not audit_only:
        pending_gates = ['houdini_repeat', 'official_engine_output', 'named_save', 'fresh_reopen',
            'regeneration', 'native_material_visual_fidelity']
        if (_sf_basis(matrix)[1] < 0 and _sf_load_ref(native['basis_evidence_ref']).get(
                'reflection_normals_material_culling_verified') is not True):
            pending_gates.append('native_reflection_normals_material_culling')
    uses = entry.get('allowed_building_uses', [])
    actual_use = feature.get('building_use', 'unknown') or 'unknown'
    if (uses and actual_use not in uses) or (actual_use != 'unknown' and not uses):
        raise ValueError('source_family_building_use_unqualified')
    expanded = []
    if mode == 'one_axis_extension':
        band = _sf_load_ref(entry.get('extension_rule_ref'))
        axis, pitch = band.get('corridor', {}).get('axis'), band.get('corridor', {}).get('pitch_m')
        if axis not in (0, 1) or isinstance(axis, bool) or band.get('id') != family['id']:
            raise ValueError('source_family_extension_axis_or_identity_invalid')
        pitch = _sf_vec([pitch], 1)[0]
        if pitch <= 0 or band.get('corridor', {}).get('pass') is not True or band['corridor'].get('profile_hausdorff_m', float('inf')) > 0.0015:
            raise ValueError('source_family_extension_connection_unqualified')
        roles = {source.get('source_role_label'): item for item in selected for source in [item[0]]}
        if set(roles) != {'Start', 'Repeat', 'End'} or len(selected) != 3:
            raise ValueError('source_family_extension_requires_complete_start_repeat_end')
        authored = {part['name']: part for part in band.get('source_derived_parts', [])}
        if {item[0]['name'] for item in selected} != set(authored):
            raise ValueError('source_family_extension_source_set_mismatch')
        for source, _, _, _, _ in selected:
            original = authored[source['name']]
            if (source['fbx_sha256'] != original['sha256']
                    or source['assembly_translation_m'] != original['assembly_translation_m']
                    or source['local_bounds_m'] != original['local_bounds_m']):
                raise ValueError('source_family_extension_source_binding_changed')
        step = _sf_mul(matrix, [pitch if i == axis else 0.0 for i in range(3)])
        for role in ('Start', 'Repeat', 'End'):
            indexes = range(repeat_count) if role == 'Repeat' else [0 if role == 'Start' else repeat_count-1]
            for index in indexes:
                source, part, low, high, translation = roles[role]
                expanded.append((source, part, low, high, [translation[i]+index*step[i] for i in range(3)], role, index))
    else:
        expanded = [(*item, 'Exact', 0) for item in selected]
    low = [min(item[2][i]+item[4][i] for item in expanded) for i in range(3)]
    high = [max(item[3][i]+item[4][i] for item in expanded) for i in range(3)]
    height = high[2]-low[2]
    if any(high[i] <= low[i] for i in range(3)):
        raise ValueError('source_family_complete_envelope_not_volumetric')
    policy = entry.get('height_policy', 'match_source_height')
    if policy == 'match_source_height' or feature.get('height_rule') != 'seeded_rule_not_measured':
        if abs(height-requested_height) > float(entry.get('height_tolerance_m', 0.04)):
            raise ValueError('source_family_native_height_does_not_match_measured_source')
    elif policy != 'preserve_native_for_unmeasured_source':
        raise ValueError('source_family_height_policy_unrecognized')
    anchor = [(low[0]+high[0])/2, (low[1]+high[1])/2, low[2]]
    # Geographic centroid is a fitting candidate; containment remains mandatory
    # for concave pads and every native part rectangle. No footprint is reshaped.
    center = [sum(p[i] for p in ring)/len(ring) for i in range(2)]
    angle = math.radians(yaw); cosine, sine = math.cos(angle), math.sin(angle)
    def world(native_point):
        x, z, y = [native_point[i]-anchor[i] for i in (0, 1, 2)]
        return [center[0]+cosine*x-sine*z, base+y, center[1]+sine*x+cosine*z]
    def rectangle(lo, hi):
        return [[p[0], p[2]] for p in (world([lo[0], lo[1], low[2]]), world([hi[0], lo[1], low[2]]),
            world([hi[0], hi[1], low[2]]), world([lo[0], hi[1], low[2]]))]
    envelope = rectangle(low, high)
    predicate = contains or _sf_contained
    if not predicate(envelope, ring):
        raise ValueError('source_family_complete_envelope_leaves_geographic_pad')
    pad_area = abs(sum(a[0]*ring[(i+1) % len(ring)][1]-a[1]*ring[(i+1) % len(ring)][0] for i, a in enumerate(ring))/2)
    envelope_area = (high[0]-low[0])*(high[1]-low[1])
    minimum_coverage = _sf_vec([entry.get('minimum_pad_coverage_ratio', 0.45)], 1)[0]
    if not 0.45 <= minimum_coverage <= 1.0:
        raise ValueError('source_family_minimum_pad_coverage_weaker_than_retained_contract')
    coverage_ratio = envelope_area/pad_area
    if coverage_ratio+1e-9 < minimum_coverage:
        raise ValueError('source_family_envelope_covers_too_little_of_geographic_pad')
    placements = []
    orient = [0.0, -math.sin(angle/2), 0.0, math.cos(angle/2)]
    for slot, (source, part, part_low, part_high, translation, role, repeat_index) in enumerate(expanded):
        lo = [part_low[i]+translation[i] for i in range(3)]
        hi = [part_high[i]+translation[i] for i in range(3)]
        footprint = rectangle(lo, hi)
        if not predicate(footprint, ring):
            raise ValueError('source_family_native_part_leaves_geographic_pad:' + source['name'])
        identifier = '%s:%s:source_family:%s:%s:%s:%s' % (area_id, osm_id, family['family_id'], mode, source['name'], repeat_index)
        slots = list(part['material_slots'])
        placements.append({'placement_id': identifier, 'path': part['path'], 'asset_id': part['asset_id'],
            'module_key': source['name'], 'role': 'building_module', 'rule': 'complete_source_family_assembly',
            'P': world(translation), 'orient': orient, 'scale': [1.0, 1.0, 1.0], 'native_scale': [1.0, 1.0, 1.0],
            # The old cook uses floor==0 solely to collect terrain support probes.
            # Every part contributes horizontal support probes; this is no story.
            'floor': 0, 'architectural_floor_index': None, 'source_region_label': source.get('source_role_label'),
            'edge_index': -1, 'slot': slot, 'footprint_xz_m': footprint, 'ground_contact_y_m': base,
            'source_area_id': area_id, 'source_osm_id': osm_id, 'selection_source': 'explicit_scoped_complete_source_family_contract',
            'catalog_release': False, 'height_rule': feature.get('height_rule', 'unknown'), 'material_slots': slots,
            'style_family_id': family['family_id'], 'style_palette_id': 'source_preserved',
            'material_signature': _sf_digest(slots)[:16], 'source_part_sha256': source['fbx_sha256'],
            'source_assembly_translation_m': source['assembly_translation_m'], 'band_role': role, 'repeat_index': repeat_index})
    if len({p['placement_id'] for p in placements}) != len(placements):
        raise ValueError('source_family_duplicate_placement_identity')
    return {'schema': 'environmentpipeline.native_building_assembly_record.v1', 'status': 'complete',
        'source_feature': {'area_id': area_id, 'osm_id': osm_id}, 'footprint_xz_m': ring,
        'native_family_envelope_xz_m': envelope, 'base_m': base, 'height_m': height,
        'footprint_area_m2': pad_area, 'generated_closed_solid_count': 0,
        'building_use': actual_use, 'building_use_evidence': feature.get('building_use_evidence', {'source': 'not_present_on_retained_pad', 'verified': False}),
        'requested_source_height_m': requested_height, 'height_rule': feature.get('height_rule', 'unknown'),
        'stories': None, 'story_height_m': None, 'architectural_floors_certified': False,
        'source_geometric_tiers_are_floors': False, 'wall_placements': placements, 'generated_parts': [],
        'module_count': len(placements), 'style_family_id': family['family_id'], 'style_palette_id': 'source_preserved',
        'style_selection': {'policy': 'stable_complete_source_family', 'rejected_families': []},
        'closure_policy': 'all_matched_source_parts_or_complete_start_repeat_end_no_generated_substitution',
        'source_family': {'family_id': family['family_id'], 'parent_asset_id': family['parent_asset_id'],
            'parent_catalog_row': family['parent_catalog_row'], 'source_family_sha256': family_digest,
            'native_manifest_sha256': native_digest, 'mode': mode, 'repeat_count': repeat_count,
            'rigid_yaw_degrees': yaw, 'source_to_native_matrix': matrix, 'material_substitution': False,
            'source_facing_verified': entry.get('source_facing_verified') is True,
            'source_geometry_scaled': False, 'appearance_accepted': False, 'runtime_selection_authorized': not audit_only,
            'ordinary_selection_enabled': not audit_only and not qualification,
            'connection_without_additional_tests': connection and not audit_only,
            'qualification_pending': (qualification or connection) and not audit_only,
            'pending_validation_gates': pending_gates,
            'parent_canonical_holds_unchanged': True},
        'coverage_check': {'complete_family': True, 'native_envelope_inside_pad': True,
            'geographic_pad_area_m2': pad_area, 'native_family_envelope_area_m2': envelope_area,
            'native_pad_coverage_ratio': coverage_ratio, 'minimum_pad_coverage_ratio': minimum_coverage,
            'matching_source_connections_only': True, 'terrain_contact': 'retained_cook_must_verify_final_heightfield'}}


def source_family_select(feature, registry, contains=None):
    """Stable weighted qualified ordering; failed fits never weaken fallback."""
    qualification_targets = []
    for entry in registry.get('families', []):
        if entry.get('execution_mode') != 'qualification':
            continue
        scopes = entry.get('qualification_target_source_ids', {})
        if not isinstance(scopes, dict) or not scopes or any(not isinstance(ids, list) or not ids for ids in scopes.values()):
            raise SourceFamilyQualificationError('source_family_qualification_exact_target_configuration_missing')
        if str(feature.get('osm_id')) in scopes.get(str(feature.get('area_id')), []):
            qualification_targets.append(entry)
    if len(qualification_targets) > 1:
        raise SourceFamilyQualificationError('source_family_multiple_qualification_families_assigned_to_one_pad')
    if registry.get('schema') != SOURCE_FAMILY_PROTOCOL or registry.get('enabled') is not True:
        if qualification_targets:
            raise SourceFamilyQualificationError('source_family_requested_qualification_registry_disabled')
        return None, [{'reason': 'source_family_registry_disabled_or_schema_invalid'}]
    entries = registry.get('families', [])
    ids = [entry.get('family_id') for entry in entries]
    if len(ids) != len(set(ids)):
        raise ValueError('source_family_duplicate_registry_identity')
    seed = int(registry.get('selection_seed', 1337))
    def score(entry):
        weight = _sf_vec([entry.get('weight', 1.0)], 1)[0]
        if weight <= 0:
            raise ValueError('source_family_selection_weight_invalid')
        identity = '%s|%s|%s|%s' % (seed, feature['area_id'], feature['osm_id'], entry['family_id'])
        fraction = (int(hashlib.sha256(identity.encode()).hexdigest()[:15], 16)+0.5)/float(16**15)
        return -math.log(fraction)/weight, entry['family_id']
    rejected = []
    candidates = qualification_targets if qualification_targets else [e for e in entries
        if e.get('enabled') is True and e.get('execution_mode', 'ordinary_selection') != 'qualification']
    if qualification_targets and qualification_targets[0].get('enabled') is not True:
        raise SourceFamilyQualificationError('source_family_requested_qualification_entry_disabled')
    for entry in sorted(candidates, key=score):
        try:
            bindings = _sf_load_ref(entry.get('source_bindings_ref'))
            families = [f for f in bindings.get('families', []) if f['family_id'] == entry['family_id']]
            if len(families) != 1:
                raise ValueError('source_family_source_identity_missing_or_duplicate')
            family = families[0]; native = _sf_load_ref(entry.get('native_manifest_ref'))
            execution = entry.get('execution_mode', 'ordinary_selection')
            if execution not in ('ordinary_selection', 'qualification', 'connection'):
                raise ValueError('source_family_unknown_execution_mode')
            qualification = execution == 'qualification'
            connection = execution == 'connection'
            if qualification:
                requested = entry.get('qualification_variations', [])
                variations = [(item['mode'], item['repeat_count']) for item in requested]
            else:
                variations = [(mode, count) for mode, capability in sorted(entry.get('capabilities', {}).items())
                    if capability.get('enabled') is True for count in capability.get('allowed_repeat_counts', [1])]
            def variation_order(value):
                return _sf_digest([seed, feature['area_id'], feature['osm_id'], entry['family_id'], *value])
            for mode, count in sorted(variations, key=variation_order):
                for offset in entry.get('allowed_rigid_yaw_offsets_degrees', [0, 90, 180, 270]):
                    yaw = _sf_pad_edge_yaw(feature) + _sf_vec([offset], 1)[0]
                    try:
                        record = source_family_plan(feature, family, native, entry, mode, count, yaw,
                            contains=contains, qualification=qualification, connection=connection)
                    except (ValueError, OSError, KeyError, TypeError) as error:
                        rejected.append({'family_id': entry['family_id'], 'mode': mode, 'repeat_count': count,
                            'yaw_degrees': yaw, 'reason': str(error)})
                        continue
                    record['style_selection']['rejected_families'] = rejected
                    return record, rejected
            if not variations:
                rejected.append({'family_id': entry['family_id'], 'reason': 'source_family_no_enabled_capabilities'})
        except (ValueError, OSError, KeyError, TypeError) as error:
            rejected.append({'family_id': entry['family_id'], 'reason': str(error)})
    if qualification_targets:
        raise SourceFamilyQualificationError('source_family_requested_qualification_failed:' + json.dumps(rejected, sort_keys=True))
    return None, rejected


# Appending AFTER r018 style wrappers leaves every earlier output path unchanged.
# Its old cook resolves assembly_layout globally when it runs, so no SOP rewiring,
# alternative output bridge, native scene mutation or protected API is necessary.
if 'assembly_layout' in globals():
    _SOURCE_FAMILY_PREVIOUS_LAYOUT = assembly_layout

    def assembly_layout(feature, contract):
        registry_ref = contract.get('source_family_registry_ref')
        if not registry_ref:
            return _SOURCE_FAMILY_PREVIOUS_LAYOUT(feature, contract)
        try:
            registry = _sf_load_ref(registry_ref)
            feature = dict(feature)
            feature.update(_SOURCE_FAMILY_USE_CONTEXT.get((str(feature['area_id']), str(feature['osm_id'])), {}))
            record, rejected = source_family_select(feature, registry,
                contains=globals().get('_assembly_polygon_contained', _sf_contained))
        except SourceFamilyQualificationError:
            raise
        except (ValueError, OSError, KeyError, TypeError) as error:
            record, rejected = None, [{'reason': str(error)}]
        if record is not None:
            return record
        record = _SOURCE_FAMILY_PREVIOUS_LAYOUT(feature, contract)
        record['source_family_selection'] = {'status': 'retained_fallback', 'rejected_families': rejected,
            'holds_preserved': True, 'unqualified_partial_output_emitted': False}
        return record


if 'cook_normal_building_assembly_points' in globals():
    _SOURCE_FAMILY_PREVIOUS_COOK = cook_normal_building_assembly_points

    def cook_normal_building_assembly_points(node):
        """Read only existing identity-bound pad use attributes; never infer use."""
        global _SOURCE_FAMILY_USE_CONTEXT, _SOURCE_FAMILY_EVIDENCE_CACHE
        previous = _SOURCE_FAMILY_USE_CONTEXT
        previous_cache = _SOURCE_FAMILY_EVIDENCE_CACHE
        context = {}
        inputs = node.inputs()
        if len(inputs) > 1 and inputs[1] is not None:
            pads = inputs[1].geometry()
            for primitive in pads.prims():
                if not pads.findPrimAttrib('source_area_id') or not pads.findPrimAttrib('source_osm_id'):
                    continue
                identity = (str(primitive.attribValue('source_area_id')), str(primitive.attribValue('source_osm_id')))
                for name in ('building_use', 'source_building_use', 'building_class', 'source_building_class'):
                    if pads.findPrimAttrib(name):
                        value = primitive.attribValue(name)
                        if isinstance(value, str) and value.strip():
                            raw_value = value.strip()
                            # OSM building=yes records existence, not a known use.
                            # Explicit use and specific building classes keep their guard.
                            generic = name in ('building_class', 'source_building_class') and raw_value == 'yes'
                            context[identity] = {'building_use': 'unknown' if generic else raw_value, 'building_use_evidence': {
                                'source': 'identity_bound_original_pad_attribute', 'attribute': name,
                                'raw_value': raw_value, 'generic_building_existence_only': generic,
                                'source_area_id': identity[0], 'source_osm_id': identity[1], 'verified': True}}
                            break
        _SOURCE_FAMILY_USE_CONTEXT = context
        _SOURCE_FAMILY_EVIDENCE_CACHE = {}
        try:
            return _SOURCE_FAMILY_PREVIOUS_COOK(node)
        finally:
            _SOURCE_FAMILY_USE_CONTEXT = previous
            _SOURCE_FAMILY_EVIDENCE_CACHE = previous_cache


"""Bounded facade/floor capability for the existing source-family registry.

Append to the retained GeoCity PythonModule. Existing SOPs, output attributes,
terrain checks, original families, and the official native instance bridge stay
in place. The same assembly planner serves normal generation and source previews.
"""
PROCEDURAL_FAMILY_CAPABILITY = 'facade_floor_grid'

def procedural_bank_families(contract):
    registry = _sf_load_ref(contract['source_family_registry_ref'])
    if registry.get('schema') != SOURCE_FAMILY_PROTOCOL or not registry.get('enabled'):
        return []
    result = []
    for entry in registry.get('families', []):
        cap = entry.get('capabilities', {}).get(PROCEDURAL_FAMILY_CAPABILITY, {})
        if entry.get('enabled') is True and cap.get('enabled') is True:
            family = _sf_load_ref(entry['procedural_family_ref'])
            if family['family_id'] != entry['family_id'] or not family.get('validation_complete'):
                raise ValueError('procedural_family_unverified_or_identity_mismatch')
            result.append((entry, family))
    return result

def procedural_family_plan(feature, family, horizontal_repeats=1, floor_repeats=1, yaw_degrees=0):
    """Assemble actual family modules at native scale; never stretch source bays."""
    nx,nz=horizontal_repeats,floor_repeats
    allowed=family['capabilities'][PROCEDURAL_FAMILY_CAPABILITY]
    if type(nx) is not int or nx not in allowed['horizontal_repeat_counts'] or type(nz) is not int or nz not in allowed['additional_floor_repeat_counts']:
        raise ValueError('procedural_family_repeat_count_unsupported')
    ring,base,requested_height,area_id,osm_id=_sf_feature(feature)
    axis=family['horizontal_axis'];pitch={i['axis']:i['pitch'] for i in family['interfaces']}
    expanded=[]
    for part in family['modules']:
        hx,z=part['cell'][axis],part['cell'][2]
        for ix in (range(nx) if hx==1 else [0 if hx==0 else nx-1]):
            for iz in (range(nz) if z==1 else [0 if z==0 else nz-1]):
                source_translation=list(part['assembly_translation_m'])
                source_translation[axis]+=ix*pitch[axis];source_translation[2]+=iz*pitch[2]
                # Measured Blender -> native basis, then native cm -> Houdini m.
                translation=[source_translation[0],source_translation[2],-source_translation[1]]
                lo,hi=part['bounds_m'];local_lo=[lo[0],lo[2],-hi[1]];local_hi=[hi[0],hi[2],-lo[1]]
                expanded.append((part,translation,local_lo,local_hi,z,ix,iz))
    if not expanded:raise ValueError('procedural_family_no_parts')
    low=[min(t[k]+lo[k] for _,t,lo,hi,z,ix,iz in expanded) for k in range(3)]
    high=[max(t[k]+hi[k] for _,t,lo,hi,z,ix,iz in expanded) for k in range(3)]
    height=high[1]-low[1]
    if feature.get('height_rule')!='seeded_rule_not_measured' and abs(requested_height-height)>.04:
        raise ValueError('procedural_family_does_not_match_measured_height')
    center=[sum(p[k] for p in ring)/len(ring) for k in range(2)]
    anchor=[(low[0]+high[0])/2,low[1],(low[2]+high[2])/2]
    angle=math.radians(float(yaw_degrees));c,s=math.cos(angle),math.sin(angle)
    def world(p):
        x,y,z=[p[k]-anchor[k] for k in range(3)]
        return [center[0]+c*x-s*z,base+y,center[1]+s*x+c*z]
    def rect(lo,hi):
        return [[p[0],p[2]] for p in [world([x,low[1],z]) for x,z in [(lo[0],lo[2]),(hi[0],lo[2]),(hi[0],hi[2]),(lo[0],hi[2])]]]
    envelope=rect(low,high)
    if not _sf_contained(envelope,ring):raise ValueError('procedural_family_leaves_original_pad')
    pad_area=abs(sum(a[0]*ring[(i+1)%len(ring)][1]-a[1]*ring[(i+1)%len(ring)][0] for i,a in enumerate(ring))/2)
    coverage=(high[0]-low[0])*(high[2]-low[2])/pad_area
    if coverage<.45:raise ValueError('procedural_family_insufficient_pad_coverage')
    items=[];orient=[0.,-math.sin(angle/2),0.,math.cos(angle/2)]
    for slot,(part,t,lo,hi,z,ix,iz) in enumerate(expanded):
        material=part['native']['material_slots'];position=world(t)
        footprint=rect([lo[k]+t[k] for k in range(3)],[hi[k]+t[k] for k in range(3)])
        items.append({'placement_id':'%s:%s:%s:%s:%s:%s'%(area_id,osm_id,family['family_id'],part['name'],ix,iz),
            'path':part['native']['path'],'asset_id':family['family_id']+'/'+part['name'],
            'module_key':part['name'],'role':'building_module','rule':'source_facade_floor_grid',
            'P':position,'orient':orient,'scale':[1.,1.,1.],'native_scale':[1.,1.,1.],
            'floor':0 if z==0 else iz+1,'architectural_floor_index':iz+1 if z==1 else None,
            'edge_index':-1,'slot':slot,'footprint_xz_m':footprint,'ground_contact_y_m':base,
            'source_area_id':area_id,'source_osm_id':osm_id,'selection_source':'retained_source_family_registry',
            'height_rule':feature.get('height_rule','unknown'),'catalog_release':False,
            'material_slots':material,'material_signature':_sf_digest(material)[:16],
            'style_family_id':family['family_id'],'style_palette_id':'source_preserved',
            'source_part_sha256':part['sha256'],'source_region_label':part['role'],
            'houdini_geometry':part['houdini_geometry'],'houdini_geometry_sha256':part['houdini_geometry_sha256'],
            'horizontal_repeat_index':ix,'floor_repeat_index':iz})
    if len({p['placement_id'] for p in items})!=len(items):raise ValueError('duplicate_procedural_family_placement')
    return {'schema':'environmentpipeline.native_building_assembly_record.v1','status':'complete',
        'source_feature':{'area_id':area_id,'osm_id':osm_id},'footprint_xz_m':ring,'native_family_envelope_xz_m':envelope,
        'base_m':base,'height_m':height,'requested_source_height_m':requested_height,'height_rule':feature.get('height_rule'),
        'footprint_area_m2':pad_area,'generated_closed_solid_count':0,'stories':None,'story_height_m':pitch[2],
        'additional_storeys':nz-1,'wall_placements':items,'generated_parts':[],'module_count':len(items),
        'style_family_id':family['family_id'],'style_palette_id':'source_preserved',
        'style_selection':{'policy':'retained_source_facade_floor_grid','rejected_families':[]},
        'closure_policy':'validated_family_specific_ground_floor_side_corner_roof_cells',
        'source_family':{'family_id':family['family_id'],'mode':PROCEDURAL_FAMILY_CAPABILITY,
            'horizontal_repeats':nx,'floor_repeats':nz,'source_geometry_scaled':False,'parent_canonical_holds_unchanged':True},
        'coverage_check':{'complete_family':True,'native_envelope_inside_pad':True,'native_pad_coverage_ratio':coverage,
            'terrain_contact':'retained_cook_must_verify_final_heightfield'}}

_PROCEDURAL_FAMILY_PREVIOUS_LAYOUT=assembly_layout
def assembly_layout(feature,contract):
    feature=dict(feature)
    feature.update(_SOURCE_FAMILY_USE_CONTEXT.get((str(feature['area_id']),str(feature['osm_id'])),{}))
    request=contract.get('procedural_family_request')
    if not contract.get('source_family_registry_ref'):
        return _PROCEDURAL_FAMILY_PREVIOUS_LAYOUT(feature,contract)
    registry=_sf_load_ref(contract['source_family_registry_ref'])
    if not request and any(e.get('execution_mode')=='qualification' and str(feature['osm_id']) in e.get('qualification_target_source_ids',{}).get(str(feature['area_id']),[]) for e in registry.get('families',[])):
        return _PROCEDURAL_FAMILY_PREVIOUS_LAYOUT(feature,contract)
    families=procedural_bank_families(contract)
    if request:
        families=[(e,f) for e,f in families if f['family_id']==request['family_id']]
        if len(families)!=1:raise ValueError('requested_procedural_family_not_registered')
        return procedural_family_plan(feature,families[0][1],request['horizontal_repeats'],request['floor_repeats'],request.get('yaw_degrees',0))
    seed=1337
    families.sort(key=lambda ef:_sf_digest([seed,feature['area_id'],feature['osm_id'],ef[1]['family_id']]))
    for entry,family in families:
        if feature['area_id'] not in entry.get('allowed_area_ids',[]):continue
        if feature.get('building_use','unknown') not in entry.get('allowed_building_uses',('unknown','yes','residential','apartments','house')):continue
        variants=[(x,z) for x in (1,2,3) for z in (1,2,3)]
        variants.sort(key=lambda xz:_sf_digest([feature['osm_id'],family['family_id'],*xz]))
        for nx,nz in variants:
            for yaw in (0,90,180,270):
                try:return procedural_family_plan(feature,family,nx,nz,_sf_pad_edge_yaw(feature)+yaw)
                except ValueError:pass
    return _PROCEDURAL_FAMILY_PREVIOUS_LAYOUT(feature,contract)

def materialize_procedural_record(record):
    """Native Houdini geometry from the exact bank plan used for Unreal points."""
    output=hou.Geometry()
    for item in record['wall_placements']:
        path=Path(item['houdini_geometry']);data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=item['houdini_geometry_sha256']:
            raise ValueError('procedural_geometry_changed_after_validation')
        part=hou.Geometry();part.loadFromFile(str(path))
        rotation=hou.Quaternion(tuple(item['orient'])).extractRotationMatrix3()
        r=rotation.asTuple();p=item['P']
        matrix=hou.Matrix4((r[0],r[1],r[2],0,r[3],r[4],r[5],0,r[6],r[7],r[8],0,p[0],p[1],p[2],1))
        part.transform(matrix)
        for key,value in [('family_id',record['style_family_id']),('placement_id',item['placement_id']),('module_role',item['source_region_label'])]:
            attr=part.addAttrib(hou.attribType.Prim,key,'')
            part.setPrimStringAttribValues(key,[value]*len(part.prims()))
        output.merge(part)
    return output


# User retired ModularCourtyard on 2026-10-06. Keep source assets, exclude outputs.
_RETIRED_COURTYARD_PREVIOUS_LAYOUT = assembly_layout
RETIRED_BUILDING_MODULE_PREFIXES = ('/Game/ModularCourtyard/',)

def assembly_layout(feature, contract):
    record = _RETIRED_COURTYARD_PREVIOUS_LAYOUT(feature, contract)
    blocked = sorted({item.get('path', '') for item in record.get('wall_placements', [])
                      if item.get('path', '').startswith(RETIRED_BUILDING_MODULE_PREFIXES)})
    if blocked:
        # Existing normal cook records the unsupported lot; no retired instances emitted.
        raise ValueError('retired_building_family:ModularCourtyard:no_eligible_replacement:'
                         + str(feature.get('osm_id', '')))
    return record


# Appended to the retained v005 HDA; no alternate construction generator.
_REGISTERED_KIT_PREVIOUS_LAYOUT = assembly_layout

def registered_modular_kits(contract):
    ref = contract.get('source_family_registry_ref')
    if not ref:
        return []
    registry = _sf_load_ref(ref)
    result = []
    for entry in registry.get('modular_kits', []):
        if not entry.get('enabled'):
            continue
        kit = _sf_load_ref(entry['kit_ref'])
        if kit.get('schema') != 'environmentpipeline.registered_native_modular_kit.v1':
            raise ValueError('modular_kit_schema_invalid')
        if kit.get('kit_id') != entry.get('kit_id') or not kit.get('native_validation_complete'):
            raise ValueError('modular_kit_identity_or_validation_invalid')
        result.append((entry, kit))
    return result

def assembly_layout(feature, contract):
    kits = [(entry, kit) for entry, kit in registered_modular_kits(contract)
            if entry['kit_id'] == 'native_modular_courtyard.v001'
            and feature['area_id'] in entry.get('allowed_area_ids', [])]
    if not kits:
        # Retired legacy fallback stays blocked without an explicit registered kit.
        return _REGISTERED_KIT_PREVIOUS_LAYOUT(feature, contract)
    if len(kits) != 1:
        raise ValueError('modular_courtyard_duplicate_kit_registration')
    entry, kit = kits[0]
    # Source-derived families and whole-building precedence remain unchanged.
    record = _RETIRED_COURTYARD_PREVIOUS_LAYOUT(feature, contract)
    used = [p for p in record.get('wall_placements', [])
            if p.get('path', '').startswith('/Game/ModularCourtyard/')]
    if not used:
        return record
    if len(used) != len(record['wall_placements']):
        raise ValueError('modular_kit_mixed_unvalidated_family')
    modules = {m['path']: m for m in kit['construction_modules'].values()}
    materials = set(kit['validated_material_paths'])
    for item in used:
        module = modules.get(item['path'])
        if module is None or item['asset_id'] != module['asset_id']:
            raise ValueError('modular_kit_unregistered_native_module')
        if not set(item['material_slots']).issubset(materials):
            raise ValueError('modular_kit_unvalidated_material_override')
        item['selection_source'] = 'registered_native_modular_kit_after_source_family_fit'
        item['modular_kit_id'] = kit['kit_id']
        item['modular_kit_catalog'] = kit['native_catalog']
    record['modular_kit'] = dict(kit_id=kit['kit_id'],
        registry_id=entry['kit_id'], native_catalog=kit['native_catalog'],
        selection_policy='automatic_after_existing_source_family_fit',
        real_native_modules=True, generated_corner_floor_roof_closures=True,
        bounded_native_bay_scaling=True, original_packages_preserved=True)
    return record
