"""Read shader-only Blender properties omitted by the retained geometry bindings."""
import bpy, json, hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
binding=HERE/'SOURCE_BINDINGS.json'
out={'source_bindings_sha256':sha(binding),'families':{},'uv_probes':{},'source_modified':False}
for family in json.loads(binding.read_text())['families']:
    result={}
    for group in family['sets']:
        path=group['blend']; assert sha(path)==group['blend_sha256']
        bpy.ops.wm.open_mainfile(filepath=path,load_ui=False,use_scripts=False)
        mats={}
        for name in group['materials']:
            mat=bpy.data.materials[name];nodes={}
            for node in mat.node_tree.nodes:
                fields={}
                for key in ('convention','base','vector_type','mode','is_active_output','target'):
                    if hasattr(node,key):fields[key]=getattr(node,key)
                if node.type=='OUTPUT_MATERIAL':
                    fields['surface_links']=[{'node':l.from_node.name,'socket':l.from_socket.name,'type':l.from_node.type} for l in node.inputs['Surface'].links]
                    fields['volume_links']=[{'node':l.from_node.name,'socket':l.from_socket.name,'type':l.from_node.type} for l in node.inputs['Volume'].links]
                if fields:nodes[node.name]=fields
            mats[name]=nodes
        result[group['kind']]=mats
        for part in group['parts']:
            mesh=bpy.data.objects[part['name']].data
            out['uv_probes'][part['name']]=[
                {'position_m':list(mesh.vertices[loop.vertex_index].co),
                 'uv0':list(mesh.uv_layers[0].data[loop.index].uv)}
                for loop in list(mesh.loops)[:24]]
        assert sha(path)==group['blend_sha256']
    out['families'][family['id']]=result
    (HERE/'SHADER_SEMANTICS.json').write_text(json.dumps(out,indent=2)+'\n')
    print('SHADER_SEMANTICS',family['id'],flush=True)
