import json
import runpy
import unreal
import bank_contracts as C
runpy.run_path(str(C.HERE/'native_bank_ops.py'))['preflight']()
source=C.read(C.HERE/'SOURCE_TRIANGLE_GEOMETRY.json')
jobs={j['asset_id']:j for j in C.read(C.HERE/'EXTERNAL_IMPORT_QUEUE.json')}
out={}
for aid,rows in source.items():
    if (C.HERE/('IMPORTED_'+aid.replace('.','_')+'.json')).exists():continue
    dest=jobs[aid]['destination_package_proposed'];folder=dest.rsplit('/',1)[0]
    assets=[unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(folder,True,False)]
    meshes=[m for m in assets if isinstance(m,unreal.StaticMesh)]
    native=[]
    for mesh in meshes:
        desc=mesh.get_static_mesh_description(0)
        vertices=[]
        for i in range(desc.get_vertex_count()):
            v=desc.get_vertex_position(unreal.VertexID(i));vertices.append([v.x,v.y,v.z])
        triangles=[];i=0
        while len(triangles)<desc.get_triangle_count():
            assert i<2*desc.get_triangle_count()+100
            tid=unreal.TriangleID(i);i+=1
            if not desc.is_triangle_valid(tid):continue
            triangle=[desc.get_vertex_instance_vertex(desc.get_triangle_vertex_instance(tid,k)).get_editor_property('id_value') for k in range(3)]
            assert all(0<=v<len(vertices) for v in triangle)
            triangles.append(triangle)
        native.append({'path':mesh.get_path_name(),'vertices_cm':vertices,'triangles':triangles})
    out[aid]=native
C.write(C.HERE/'NATIVE_TRIANGLE_GEOMETRY.json',out)
print('Targeted native triangle readback saved')
