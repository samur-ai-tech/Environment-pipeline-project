"""Compare surfaces under differing triangulations using every triangle's probes."""
import json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
source=json.loads((HERE/'SOURCE_TRIANGLE_GEOMETRY.json').read_text())
native=json.loads((HERE/'NATIVE_TRIANGLE_GEOMETRY.json').read_text())
results={}
def mesh(vertices,triangles):
    verts=[Vector(v) for v in vertices]
    triangles=[t for t in triangles if (verts[t[1]]-verts[t[0]]).cross(verts[t[2]]-verts[t[0]]).length>1e-7]
    area=sum((verts[t[1]]-verts[t[0]]).cross(verts[t[2]]-verts[t[0]]).length/2 for t in triangles)
    return verts,triangles,BVHTree.FromPolygons(verts,triangles,all_triangles=True),area
def compare(first,second):
    vertices,triangles,_,area=first;tree=second[2];maximum=0;count=0
    for tri in triangles:
        a,b,c=[vertices[i] for i in tri]
        for p in [a,b,c,(a+b+c)/3,(a+b)/2,(b+c)/2,(c+a)/2]:
            hit=tree.find_nearest(p);assert hit[0] is not None
            maximum=max(maximum,hit[3]);count+=1
    return {'samples':count,'max_distance_cm':maximum}
for aid in ['external.H0045','external.H0056']:
    s=source[aid][0];n=native[aid][0]
    a=mesh([[p[0],-p[1],p[2]] for p in s['vertices_cm']],s['triangles'])
    b=mesh(n['vertices_cm'],n['triangles'])
    ab=compare(a,b);ba=compare(b,a)
    rel=abs(a[3]-b[3])/max(a[3],b[3])
    results[aid]={'native_path':n['path'],'source_triangles':len(s['triangles']),'native_triangles':len(n['triangles']),
        'source_to_native':ab,'native_to_source':ba,'source_area_cm2':a[3],'native_area_cm2':b[3],
        'relative_area_difference':rel,'distance_tolerance_cm':0.01,'relative_area_tolerance':0.0001,
        'method':'Every nonzero triangle: vertices, edge midpoints and centroid against opposite surface BVH; separate total area comparison',
        'passed':max(ab['max_distance_cm'],ba['max_distance_cm'])<=0.01 and rel<=0.0001,
        'visual_acceptance':False}
(HERE/'IMPORT_SURFACE_EQUIVALENCE.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
