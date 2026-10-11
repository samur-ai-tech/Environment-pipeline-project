"""Read-only measured surface QA, bound to reopened source/FBX/texture bytes."""
import bpy, json, hashlib, math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
report=json.loads((ROOT/'Reports/strawberries_v005.json').read_text())
files=[ROOT/'Blend/StrawberryBeds.blend']+[ROOT/a['fbx'] for a in report['assets']]+sorted((ROOT/'Textures').glob('T_PazFarm_Strawberry_*_v005_*.png'))
def hashes():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blend/StrawberryBeds.blend'));results=[]
for rec in report['assets']:
 ob=bpy.data.objects[rec['name']];mesh=ob.data;mesh.calc_loop_triangles();coords=[v.co.copy() for v in mesh.vertices]
 film_faces=[];soil_faces=[]
 for part in rec['component_ranges']:
  polys=list(mesh.polygons[part['start_face']:part['start_face']+part['face_count']])
  if part['role'] in ('film_top','film_sides','film_lowest_mound','film_cap'):film_faces.extend(tuple(p.vertices) for p in polys)
  if part['role']=='soil_edge_burial':soil_faces.extend(p.index for p in polys)
 bvh=BVHTree.FromPolygons(coords,film_faces,all_triangles=False);clearances=[];miss_points=[]
 for tri in mesh.loop_triangles:
  if tri.polygon_index not in soil_faces:continue
  a,b,c=[coords[i] for i in tri.vertices]
  for i in range(9):
   for j in range(9-i):
    point=a*(i/8)+b*(j/8)+c*(1-(i+j)/8)
    if point.z<=0 or abs(point.x)>.544:continue
    location,normal,index,distance=bvh.ray_cast(point+Vector((0,0,1)),Vector((0,0,-1)),2)
    if location is None:miss_points.append(list(point))
    else:clearances.append(point.z-location.z)
 uv=mesh.uv_layers[0];uv_areas=[]
 for tri in mesh.loop_triangles:
  a,b,c=[uv.data[i].uv for i in tri.loops]
  uv_areas.append(abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))/2)
 plant_diameters=[p.get('actual_xy_diameter_m') for p in rec['plants'] if not p['tiny']]
 boundary_misses=all(abs(q[1])<1e-6 or abs(q[1]-rec['length_m'])<1e-6 for q in miss_points)
 results.append({'name':rec['name'],'soil_cover_samples':len(clearances),'soil_cover_ray_misses':len(miss_points),'misses_only_on_intentional_open_end_planes':boundary_misses,'minimum_above_film_clearance_m':min(clearances) if clearances else None,'soil_cover_clearance_passed':bool(clearances) and min(clearances)>-1e-6 and boundary_misses,'UV_zero_area_triangle_count':sum(a<1e-14 for a in uv_areas),'minimum_UV_triangle_area':min(uv_areas),'normal_plant_diameter_range_m':[min(plant_diameters),max(plant_diameters)] if plant_diameters else None})
after=hashes();passed=before==after and all(r['soil_cover_clearance_passed'] and r['UV_zero_area_triangle_count']==0 for r in results)
out={'passed':passed,'method':'Freshly reopened source. Barycentric grid of 45 samples per soil-cover triangle above ground and |X| <= 0.544 m, vertically compared with actual film triangles. UV triangle area measured on every actual loop triangle. Native shading is not tested.','source_files_unchanged_during_qa':before==after,'input_hashes_before':before,'input_hashes_after':after,'assets':results}
(ROOT/'Reports/strawberries_v005_surface_qa.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'passed':passed,'assets':results},indent=2),flush=True)
