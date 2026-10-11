"""Preview for Aviv (2026-10-10): the two farm roads continued past the old screenshot (inference, not map data) in RED,
their traced parts in YELLOW, over the parcel preview context (Sentinel-2, OSM tracks, parcels). Writes guessed_roads.png."""
import json, math
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
L = json.loads((HERE / 'LAYOUT.json').read_text()); PV = json.loads((HERE / 'PARCELS_V2.json').read_text())
ctx = gdal.Open(str(HERE / 'parcels_context.png'))
img = np.stack([ctx.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1).astype(np.uint8)   # +-700 m, 1 m/px
HALF = 700


def draw(pts, col, w):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(math.hypot(x1 - x0, y1 - y0)) + 2
        for t in np.linspace(0, 1, n):
            c, r = int(x0 + (x1 - x0) * t + HALF), int(HALF - (y0 + (y1 - y0) * t))
            img[max(0, r - w):r + w + 1, max(0, c - w):c + w + 1] = col


for name in ('west_track', 'yard_access_north'):
    traced = L['roads'][name]['line_m']; drawn = PV['roads_drawn'][name]['line_m']
    ext = [p for p in drawn if p not in traced]
    end = [e for e in PV['road_ends'] if e['road'] == name]
    for e in end:
        if e['drawn_extension_m'] > 30:
            fp = e['frame_point']; d = e['dir']; L_ = e['drawn_extension_m']
            draw([fp, [fp[0] + d[0] * L_, fp[1] + d[1] * L_]], (255, 0, 0), 3)
    draw(traced, (255, 230, 0), 2)
crop = img[100:1300, 100:1300]
mem = gdal.GetDriverByName('MEM').Create('', crop.shape[1], crop.shape[0], 3, gdal.GDT_Byte)
for i in range(3): mem.GetRasterBand(i + 1).WriteArray(crop[..., i])
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'guessed_roads.png'), mem)
print([(e['road'], e['drawn_extension_m']) for e in PV['road_ends']])
