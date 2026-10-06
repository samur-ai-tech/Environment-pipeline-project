"""Collect authored component materials for the five whole-building imports.

Run Blender --background --factory-startup --disable-autoexec --python this_file.
Reads existing prepared sources; never saves a Blender source or renders a scene.
Output lives exclusively beside this script. Native material appearance is unrun.
"""
import hashlib
import json
import sys
from pathlib import Path
import bpy

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0,str(HERE))
import category_contracts as C

def val(socket):
    try:return list(socket.default_value)
    except TypeError:return socket.default_value

def recipe(mat,source_name,index):
    assert mat and mat.node_tree,('missing_material_graph',source_name)
    principled=[n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED']
    assert len(principled)==1,('unsupported_surface_graph',source_name)
    bsdf=principled[0]
    names=['Base Color','Metallic','Roughness','Alpha','Normal','Emission Color','Emission Strength']
    inputs={n:{'default':val(bsdf.inputs[n]),'links':[{'node':l.from_node.name,'type':l.from_node.type,'output':l.from_socket.name} for l in bsdf.inputs[n].links]} for n in names}
    images=[]
    for node in mat.node_tree.nodes:
        if node.type!='TEX_IMAGE' or not node.image or not any(s.is_linked for s in node.outputs):continue
        image=Path(bpy.path.abspath(node.image.filepath))
        assert image.is_file(),('missing_linked_image',source_name,str(image))
        images.append({'node':node.name,'path':str(image),'sha256':C.sha(image),'colorspace':node.image.colorspace_settings.name,
            'outputs':[{'socket':s.name,'destinations':[l.to_node.name+'.'+l.to_socket.name for l in s.links]} for s in node.outputs if s.is_linked]})
    extra={n:{'default':val(bsdf.inputs[n]),'links':[{'node':l.from_node.name,'type':l.from_node.type,'output':l.from_socket.name} for l in bsdf.inputs[n].links]}
           for n in ['Transmission Weight','IOR','Coat Weight'] if n in bsdf.inputs}
    return {'slot':index,'source_material':source_name,'prepared_material_name':mat.name,
        'backface_culling':mat.use_backface_culling,'diffuse_color':list(mat.diffuse_color),
        'principled_inputs':inputs,'linked_images':images,'source_additional_surface_parameters':extra,
        'normal_basis':'Preserved prepared Blender Normal Map graph; use existing importer tangent-space conversion; material appearance remains unverified.'}

jobs=C.read(HERE/'EXTERNAL_IMPORT_QUEUE.json')
recipes={r['asset_id']:r for r in C.read(HERE/'EXTERNAL_MATERIAL_RECIPES.json')}
usage=C.read(HERE/'SOURCE_IMPORT_SLOT_USAGE.json') if (HERE/'SOURCE_IMPORT_SLOT_USAGE.json').exists() else {}
failures=[];reused=[];saved=[]
for job in jobs:
    aid=job['asset_id'];path=Path(job['prepared_blend']);before=C.sha(path)
    if aid in recipes and recipes[aid]['prepared_blend_sha256']==before and aid in usage:
        reused.append(aid);continue
    try:
        bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
        objects=[o for o in job['category_object_members'] if o['primary_render']]
        assert len(objects)==job['primary_render_object_count']
        names={o['name'] for o in objects}
        actual={o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render}
        assert names==actual,('prepared_primary_component_set_changed',aid,sorted(names^actual))
        material_map={};material_recipes=[];object_usage=[];used=set()
        for original in objects:
            obj=bpy.data.objects.get(original['name']);assert obj and obj.type=='MESH'
            assert len(obj.material_slots)==len(original['material_slots']),('slot_count_changed',aid,obj.name)
            mappings=[]
            for index,(slot,source_name) in enumerate(zip(obj.material_slots,original['material_slots'])):
                count=sum(p.material_index==index for p in obj.data.polygons)
                if source_name not in material_map:
                    target=len(material_recipes);material_map[source_name]=target
                    material_recipes.append(recipe(slot.material,source_name,target))
                else:
                    target=material_map[source_name]
                    comparison=recipe(slot.material,source_name,target)
                    assert comparison==material_recipes[target],('different_graph_same_source_material',aid,source_name)
                if count:used.add(target)
                mappings.append({'source_slot':index,'recipe_slot':target,'material':source_name,'polygons':count})
            object_usage.append({'object':obj.name,'material_slots':mappings,'source_transform':original['matrix_world']})
        additional=[]
        for mat in material_recipes:
            if float(mat['source_additional_surface_parameters'].get('Transmission Weight',{}).get('default',0))>0:
                additional.append({'source_material':mat['source_material'],'missing_native_behavior':'Source glass/transmission parameter is retained in recipe metadata; existing bank standard-surface importer does not reproduce source transmission. Held import may be retained; native material/readiness review must resolve before ordinary use.'})
        recipes[aid]={'asset_id':aid,'prepared_blend':str(path),'prepared_blend_sha256':before,
            'materials':material_recipes,'source_preserved':True,'native_imported':False,
            'source_material_render':None,'render_kind':'existing_preparation_reused_no_new_render',
            'source_objects':sorted(names),'material_transfer_status':'recipe_saved_native_binding_pending',
            'native_material_behavior_exceptions':additional}
        usage[aid]={'source':str(path),'sha256':before,'used_slots':sorted(used),
                    'slots':[{'index':i,'material':r['source_material']} for i,r in enumerate(material_recipes)],'objects':object_usage,
                    'basis':'Unique source material identities over exact authored component objects; no component, geometry or UV editing.'}
        C.write(HERE/'EXTERNAL_MATERIAL_RECIPES.json',list(recipes.values()))
        C.write(HERE/'SOURCE_IMPORT_SLOT_USAGE.json',usage)
        saved.append(aid);print('WHOLE_RECIPE_SAVED',aid,len(material_recipes),flush=True)
    except Exception as error:
        failures.append({'asset_id':aid,'reason':str(error),'native_import_allowed':False})
        print('WHOLE_RECIPE_BLOCKED',aid,str(error),flush=True)
    finally:
        assert C.sha(path)==before,('prepared_source_changed',aid)
C.write(HERE/'MATERIAL_RECIPE_RESULT.json',{'recipes_saved':saved,'recipes_reused':reused,'failures':failures,
    'prepared_sources_unchanged':True,'source_graph_modified':False,'new_renders':0,'native_execution':False})
