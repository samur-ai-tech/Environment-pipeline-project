"""Offline fresh-process verification of delivered strawberry/tunnel sources and FBXs."""
import bpy, json, sys, math
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
def bounds(ob):
    pts=[ob.matrix_world@v.co for v in ob.data.vertices]
    return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
result={'verification':'Fresh offline Blender process: source reopen, FBX reimport, UV, dimensions, triangles, texture paths and exact module end geometry.', 'assets':[]}
for short,family in [('StrawberryBed_4m','Strawberry'),('LowTunnel_4m','LowTunnel')]:
    name='SM_PazFarm_'+short
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blend'/(family+'.blend')))
    ob=bpy.data.objects[name];bb=bounds(ob);ob.data.calc_loop_triangles()
    a={(round(v.co.x,6),round(v.co.z,6)) for v in ob.data.vertices if abs(v.co.y)<1e-6}
    b={(round(v.co.x,6),round(v.co.z,6)) for v in ob.data.vertices if abs(v.co.y-4)<1e-6}
    rec={'name':name,'source_bounds_m':bb,'source_triangle_count':len(ob.data.loop_triangles),'source_uv_layers':[l.name for l in ob.data.uv_layers],
         'source_zero_area_triangles':sum(t.area<1e-12 for t in ob.data.loop_triangles),
         'source_object_origin_m':list(ob.location),'source_unit_scale':bpy.context.scene.unit_settings.scale_length,
         'seam':{'tile_translation_m':[0,4,0],'end_vertex_coordinates_match':a==b,'start_boundary_vertex_positions':len(a),'end_boundary_vertex_positions':len(b),
         'all_geometry_within_Y_0_4':bb[0][1]>=-1e-6 and bb[1][1]<=4+1e-6},
         'source_texture_paths':[]}
    for im in bpy.data.images:
        if im.filepath:
            p=Path(bpy.path.abspath(im.filepath))
            rec['source_texture_paths'].append({'file':im.filepath,'relative':im.filepath.startswith('//'),'exists':p.is_file(),'resolution':list(im.size),'source':im.source})
    if short=='LowTunnel_4m':
        used={v for p in ob.data.polygons if p.material_index==1 for v in p.vertices};neighbors={v:set() for v in used}
        for e in ob.data.edges:
            x,y=e.vertices
            if x in used and y in used:neighbors[x].add(y);neighbors[y].add(x)
        components=[]
        while used:
            todo=[used.pop()];component=[]
            while todo:
                v=todo.pop();component.append(v)
                for n in neighbors[v]:
                    if n in used:used.remove(n);todo.append(n)
            ys=[ob.data.vertices[i].co.y for i in component];components.append([min(ys),max(ys)])
        intervals=sorted(components);two=sorted(intervals+[[a+4,b+4] for a,b in intervals])
        rec['seam']['steel_hoop_Y_intervals_per_module_m']=intervals
        rec['seam']['two_module_hoops_do_not_overlap']=all(two[i][1]<two[i+1][0] for i in range(len(two)-1))
        rec['seam']['last_hoop_parameter']='include_terminal_hoop, default false'
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
    bpy.ops.import_scene.fbx(filepath=str(ROOT/'FBX'/(name+'.fbx')),use_image_search=False)
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)==1,(name,len(meshes))
    imported=meshes[0];imported.data.calc_loop_triangles();ib=bounds(imported)
    rec['fbx_reimport']={'mesh_count':len(meshes),'bounds_m':ib,'dimensions_m':[ib[1][i]-ib[0][i] for i in range(3)],'triangles':len(imported.data.loop_triangles),
        'uv_layers':[l.name for l in imported.data.uv_layers],'zero_area_triangles':sum(t.area<1e-12 for t in imported.data.loop_triangles),
        'bounds_match_source_tolerance_0_00001_m':max(abs(ib[a][k]-bb[a][k]) for a in range(2) for k in range(3))<1e-5,
        'material_slots':len(imported.data.materials)}
    assert rec['seam']['end_vertex_coordinates_match']
    assert rec['seam']['all_geometry_within_Y_0_4']
    assert rec['fbx_reimport']['bounds_match_source_tolerance_0_00001_m']
    assert not rec['fbx_reimport']['zero_area_triangles']
    assert rec['fbx_reimport']['triangles']==rec['source_triangle_count']
    assert rec['fbx_reimport']['uv_layers']
    assert all(t['relative'] and t['exists'] and t['resolution']==[1024,1024] for t in rec['source_texture_paths'])
    result['assets'].append(rec)
result['passed']=True
(ROOT/'Reports'/'strawberries_qa.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('STRAWBERRY_FBX_SOURCE_QA_PASS',json.dumps([(r['name'],r['fbx_reimport']['triangles'],r['fbx_reimport']['dimensions_m']) for r in result['assets']]))
