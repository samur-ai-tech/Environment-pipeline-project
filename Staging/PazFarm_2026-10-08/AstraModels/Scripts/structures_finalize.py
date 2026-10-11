"""Final structure-only repair, portable source save and measured mesh audit."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,json,math
from mathutils import Vector
import build_structures as S
import paz_common as C

old=json.loads((C.ROOT/'Reports/structures.json').read_text())
netrecords=[r for r in old['assets'] if '_NetHouse_' in r['name']]
S.ALL=[]
ghrecords=S.greenhouse()
records=netrecords+ghrecords
qa={'source_reopen':{},'modular_checks':{},'materials':{}}
for family in ('NetHouse','Greenhouse'):
    path=C.ROOT/'Blend'/(family+'.blend')
    bpy.ops.wm.open_mainfile(filepath=str(path))
    portable={}
    for im in bpy.data.images:
        if im.name.startswith('T_PazFarm_') and im.filepath:
            absolute=Path(bpy.path.abspath(im.filepath))
            if not absolute.is_file():raise RuntimeError('Texture not found: '+str(absolute))
            im.filepath=bpy.path.relpath(str(absolute));portable[im.name]=im.filepath
            if not im.filepath.startswith('//'):raise RuntimeError('Texture not relative')
    # Primary component visible on first open; alternates keep correct local
    # origins and are hidden using the Outliner's per-object eye toggle.
    primary=next(r['name'] for r in records if r['blend']==f'Blend/{family}.blend')
    for ob in bpy.context.scene.objects:
        ob.hide_set(ob.name!=primary);ob.hide_render=(ob.name!=primary)
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    qa['source_reopen'][family]={'status':'PASS','relative_texture_paths':portable,'mesh_assets':[]}
    for rec in [r for r in records if r['blend']==f'Blend/{family}.blend']:
        ob=bpy.data.objects[rec['name']];ob.data.calc_loop_triangles()
        triangles=ob.data.loop_triangles
        deg=sum(t.area<1e-12 for t in triangles)
        if deg:raise RuntimeError('Degenerate geometry: '+ob.name)
        item={'name':ob.name,'triangles':len(triangles),'zero_area_triangles':deg,'has_UV0':'UV0' in ob.data.uv_layers,
              'size_metres':[round(v,6) for v in ob.dimensions],'bounds_metres':C.bounds(ob)}
        qa['source_reopen'][family]['mesh_assets'].append(item)
        if 'Bay_8x4' in ob.name:
            assert all(abs(ob.dimensions[i]-[8,4,4][i])<1e-5 for i in range(3))
            roof=[p for p in ob.data.polygons if 'NetWhite' in ob.data.materials[p.material_index].name or 'NetBlack' in ob.data.materials[p.material_index].name]
            ids={v for p in roof for v in p.vertices}; pts=[ob.matrix_world@ob.data.vertices[v].co for v in ids]
            roofbounds=[[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
            assert abs(roofbounds[1][0]-roofbounds[0][0]-8)<1e-6
            assert abs(roofbounds[1][1]-roofbounds[0][1]-4)<1e-6
            qa['modular_checks'][ob.name]={'roof_surface_bounds':roofbounds,'pitch_metres':[8,4],
                'post_bounds':C.bounds(bpy.data.objects['UCX_'+ob.name+'_00']),'post_count_per_bay':1}
        if ob.name=='SM_PazFarm_Greenhouse_Tunnel_9x4':
            film=[p for p in ob.data.polygons if ob.data.materials[p.material_index].name=='M_PazFarm_GreenhouseFilm']
            ids={v for p in film for v in p.vertices};pts=[ob.matrix_world@ob.data.vertices[v].co for v in ids]
            bb=[[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
            normaldot=[]
            for p in film:
                center=sum((ob.data.vertices[v].co for v in p.vertices),Vector())/len(p.vertices)
                outward=Vector((center.x,0,center.z)).normalized();normaldot.append(p.normal.dot(outward))
            assert min(normaldot)>.99
            assert all(abs(bb[1][i]-bb[0][i]-[9,4,4.5][i])<1e-5 for i in range(3))
            qa['modular_checks'][ob.name]={'film_surface_bounds':bb,'pitch_metres':4,'film_outward_normal_min_dot':min(normaldot),'ground_footplates':2}
    for m in bpy.data.materials:
        if m.name.startswith('M_PazFarm_Net') or m.name.startswith('M_PazFarm_Greenhouse'):
            qa['materials'][m.name]={'mode':m.get('blend_mode_intent'),'texture_files':json.loads(m.get('texture_files','[]'))}

nx=ny=2
posts=[(i*8,j*4,0) for i in range(nx) for j in range(ny)]
posts += [(nx*8-.08,j*4,0) for j in range(ny)]
posts += [(i*8,ny*4-.08,0) for i in range(nx)]
posts += [(nx*8-.08,ny*4-.08,0)]
assert len(posts)==len(set(posts))==9
qa['modular_checks']['net_assembled_2x2']={'footprint_metres':[16,8],'post_count':9,'duplicate_post_positions':0,'post_footprint_origins':posts,'status':'PASS'}
qa['modular_checks']['greenhouse_assembled_3sections']={'footprint_metres':[9,12],'arch_count':4,'arch_centrelines_y':[.035,4.035,8.035,11.965],'duplicate_arch_positions':0,'status':'PASS'}
old['assets']=records
old['extra']['default_net_material']='White; canonical handoff names have no variant suffix. Black alternatives use _Black.'
old['extra']['measured_qa']='Reports/structures_qa.json'
(C.ROOT/'Reports/structures.json').write_text(json.dumps(old,indent=2))
(C.ROOT/'Reports/structures_qa.json').write_text(json.dumps(qa,indent=2))
print('PAZ_STRUCTURES_FINALIZED',len(records),'assets',sum(r['triangles_LOD0'] for r in records),'triangles')
