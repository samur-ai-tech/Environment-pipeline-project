"""Read retained modular Blender files into exact native import bindings; never save sources."""
import collections
import hashlib
import json
from pathlib import Path
import bpy

HERE = Path(__file__).resolve().parent
BANK = HERE.parent
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p, v): Path(p).write_text(json.dumps(v, indent=2, allow_nan=False)+'\n', encoding='utf-8')
def value(s):
    try: return list(s.default_value)
    except TypeError: return s.default_value

families = read(BANK/'MODULAR_SOURCE_FAMILIES.json')['families']
output = {'schema':'environmentpipeline.modular_native_source_bindings.v1', 'families':[],
          'native_imported':False, 'sources_modified':False}

def material(mat):
    nodes = list(mat.node_tree.nodes) if mat.node_tree else []
    principled = [n for n in nodes if n.type == 'BSDF_PRINCIPLED']
    assert len(principled) == 1, (mat.name, 'unsupported_surface_graph')
    bsdf = principled[0]
    names = ['Base Color','Metallic','Roughness','Alpha','Normal','Emission Color','Emission Strength']
    inputs = {n:{'default':value(bsdf.inputs[n]), 'links':[
        {'node':l.from_node.name,'type':l.from_node.type,'output':l.from_socket.name}
        for l in bsdf.inputs[n].links]} for n in names}
    graph=[]; images=[]
    for node in nodes:
        record={'name':node.name,'type':node.type,'inputs':{}}
        for socket in node.inputs:
            if hasattr(socket,'default_value'):
                try: default=value(socket)
                except (ValueError,TypeError): default=str(socket.default_value)
                record['inputs'][socket.name]={'default':default,'links':[
                    {'node':l.from_node.name,'output':l.from_socket.name} for l in socket.links]}
        if node.type=='NORMAL_MAP': record.update(space=node.space,uv_map=node.uv_map)
        if node.type=='UVMAP': record['uv_map']=node.uv_map
        if node.type=='TEX_IMAGE' and node.image:
            path=Path(bpy.path.abspath(node.image.filepath))
            assert path.is_file(), ('missing_image',mat.name,str(path))
            record.update(image=str(path),sha256=sha(path),colorspace=node.image.colorspace_settings.name,
                          interpolation=node.interpolation,extension=node.extension,projection=node.projection)
            images.append({'node':node.name,'path':str(path),'sha256':sha(path),
                           'colorspace':node.image.colorspace_settings.name,
                           'outputs':[{'socket':s.name,'destinations':[l.to_node.name+'.'+l.to_socket.name for l in s.links]}
                                      for s in node.outputs if s.is_linked]})
        graph.append(record)
    return {'source_material':mat.name,'prepared_material_name':mat.name,
            'backface_culling':mat.use_backface_culling,'diffuse_color':list(mat.diffuse_color),
            'principled_inputs':inputs,'linked_images':images,'graph':graph}

for family in families:
    aid=family['parent_asset_id']; assembly_path=Path(family['source_files']['assembly'])
    assembly=read(assembly_path); fid=assembly['id']; sources=[('reconstruction',assembly['blend'],assembly['modules'])]
    extension_path=assembly_path.parent/'ExtensionBand/EXTENSION.json'
    if extension_path.is_file():
        extension=read(extension_path)
        sources.append(('extension',extension['blend'],extension['source_derived_parts']))
    entry={'id':fid,'family_id':family['family_id'],'parent_asset_id':aid,
           'parent_catalog_row':family['parent_catalog_row'],'rights_state':family['original_rights_state'],
           'explicit_hold':family['parent_explicit_hold_preserved'],
           'hold_reasons':family['parent_hold_reasons_preserved'],
           'assembly_path':str(assembly_path),'assembly_sha256':sha(assembly_path),
           'readback_path':str(assembly_path.parent/'READBACK.json'),
           'readback_sha256':sha(assembly_path.parent/'READBACK.json'),'sets':[]}
    for kind,blend,records in sources:
        before=sha(blend)
        bpy.ops.wm.open_mainfile(filepath=blend,load_ui=False,use_scripts=False)
        part_set={'kind':kind,'blend':blend,'blend_sha256':before,'materials':{},'parts':[]}
        for rec in records:
            ob=bpy.data.objects.get(rec['name']); assert ob and ob.type=='MESH',rec['name']
            mesh=ob.data; mesh.calc_loop_triangles()
            slots=[s.material.name if s.material else None for s in ob.material_slots]
            assert all(slots),('empty_material_slot',rec['name'])
            for slot in ob.material_slots:
                if slot.material.name not in part_set['materials']:
                    part_set['materials'][slot.material.name]=material(slot.material)
            counts=collections.Counter(t.material_index for t in mesh.loop_triangles)
            uv_names=[u.name for u in mesh.uv_layers]
            assert uv_names[0]=='SourceRenderUV',(fid,rec['name'],uv_names)
            fbx=Path(rec['fbx']); assert sha(fbx)==rec['sha256'],('changed_fbx',str(fbx))
            native='/Game/Project/Shared/ModelBank/Prepared/Modular/'+fid+'/'+('Modules' if kind=='reconstruction' else 'ExtensionBand')+'/'+rec['name']
            part_set['parts'].append({'name':rec['name'],'fbx':str(fbx),'fbx_sha256':rec['sha256'],
                'native_package':native,'source_material_slots':slots,'slot_triangle_counts':dict(counts),
                'triangles':len(mesh.loop_triangles),'uv_channels':uv_names,
                'render_uv_name':next((u.name for u in mesh.uv_layers if u.active_render),None),
                'local_bounds_m':rec['local_bounds_m'],
                'assembly_translation_m':rec.get('original_assembly_translation_m',rec.get('assembly_translation_m')),
                'source_role_label':rec['role'],'verified_architectural_role':None,
                'neighbors':rec.get('assembly_neighbors',[]),
                'sample_local_vertices_m':[list(v.co) for v in list(mesh.vertices)[:32]],
                'enabled':False})
        assert sha(blend)==before,('source_changed',blend)
        entry['sets'].append(part_set)
    output['families'].append(entry)
    write(HERE/'SOURCE_BINDINGS.json',output)
    print('SOURCE_BINDINGS_SAVED',fid,sum(len(s['parts']) for s in entry['sets']),flush=True)
output['family_count']=len(output['families'])
output['part_count']=sum(len(s['parts']) for f in output['families'] for s in f['sets'])
assert output['family_count']==20 and output['part_count']==609
write(HERE/'SOURCE_BINDINGS.json',output)
