"""Translate existing prepared material graphs into saved native import recipes.

Run with Blender --background --disable-autoexec. Reuse completed recipes, do not
render or remodel, and never save any opened original/prepared Blender source.
"""
import hashlib
import json
from pathlib import Path
import bpy

HERE=Path(__file__).resolve().parent
def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value): Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def val(socket):
    try: return list(socket.default_value)
    except TypeError: return socket.default_value

output=HERE/'EXTERNAL_MATERIAL_RECIPES.json'
recipes={r['asset_id']:r for r in read(output)} if output.exists() else {}
failures=[]
reused=[]
for job in read(HERE/'EXTERNAL_IMPORT_QUEUE.json'):
    aid=job['asset_id'];path=Path(job['prepared_blend']);before=sha(path)
    if aid in recipes and recipes[aid]['prepared_blend_sha256']==before:
        reused.append(aid)
        continue
    try:
        bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
        meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
        assert len(meshes)==1,(aid,'multiple_render_objects',len(meshes))
        mappings=[o for o in job['material_mapping_by_source_object'] if o['geometry_role']=='render_lod0']
        assert len(mappings)==1,(aid,'ambiguous_material_object_mapping')
        source_names=mappings[0]['material_slots'];mesh=meshes[0]
        assert len(source_names)==len(mesh.material_slots),(aid,'slot_count_changed')
        materials=[]
        for i,slot in enumerate(mesh.material_slots):
            mat=slot.material;assert mat is not None,(aid,'empty_material_slot',i)
            nodes=list(mat.node_tree.nodes) if mat.node_tree else []
            principled=[n for n in nodes if n.type=='BSDF_PRINCIPLED']
            assert len(principled)==1,(aid,mat.name,'unsupported_surface_graph')
            bsdf=principled[0]
            inputs={n:{'default':val(bsdf.inputs[n]),'links':[{'node':l.from_node.name,'type':l.from_node.type,'output':l.from_socket.name} for l in bsdf.inputs[n].links]} for n in ['Base Color','Metallic','Roughness','Alpha','Normal','Emission Color','Emission Strength']}
            images=[]
            for node in nodes:
                if node.type!='TEX_IMAGE' or not node.image or not any(s.is_linked for s in node.outputs): continue
                image=Path(bpy.path.abspath(node.image.filepath));assert image.is_file(),(aid,'missing_linked_image',str(image))
                images.append({'node':node.name,'path':str(image),'sha256':sha(image),'colorspace':node.image.colorspace_settings.name,
                    'outputs':[{'socket':s.name,'destinations':[l.to_node.name+'.'+l.to_socket.name for l in s.links]} for s in node.outputs if s.is_linked]})
            materials.append({'slot':i,'source_material':source_names[i],'prepared_material_name':mat.name,
                'backface_culling':mat.use_backface_culling,'diffuse_color':list(mat.diffuse_color),
                'principled_inputs':inputs,'linked_images':images,
                'normal_basis':'Prepared Blender Normal Map shader; native imported texture uses matching tangent-space conversion.'})
        recipes[aid]={'asset_id':aid,'prepared_blend':str(path),'prepared_blend_sha256':before,
            'materials':materials,'source_preserved':True,'native_imported':False,
            'source_material_render':None,'render_kind':'existing_preparation_reused_no_new_render',
            'source_object':mesh.name,'material_transfer_status':'recipe_saved_native_binding_pending'}
        write(output,list(recipes.values()))
        print('RECIPE_SAVED',aid,len(materials),flush=True)
    except Exception as error:
        failures.append({'asset_id':aid,'reason':str(error),'native_import_allowed':False})
        print('RECIPE_BLOCKED',aid,str(error),flush=True)
    finally:
        assert sha(path)==before,('prepared_source_changed',aid)
write(HERE/'IMPORT_RECIPE_RESULT.json',{'recipes_saved':len(recipes),'existing_recipes_reused':reused,
    'failures':failures,'native_imported':0,'source_geometry_or_materials_modified':False,'new_renders':0})
