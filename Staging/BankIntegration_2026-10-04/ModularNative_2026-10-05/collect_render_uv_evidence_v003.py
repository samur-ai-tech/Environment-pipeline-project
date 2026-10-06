"""Read source render-UV identity and distributed per-material probes without source writes."""
import bpy,json,hashlib,collections
from pathlib import Path
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
binding=HERE/'SOURCE_BINDINGS.json'
out={'source_bindings_sha256':sha(binding),'parts':{},'source_modified':False}
for family in json.loads(binding.read_text())['families']:
 for group in family['sets']:
  assert sha(group['blend'])==group['blend_sha256']
  bpy.ops.wm.open_mainfile(filepath=group['blend'],load_ui=False,use_scripts=False)
  for part in group['parts']:
   mesh=bpy.data.objects[part['name']].data
   render=[(i,u) for i,u in enumerate(mesh.uv_layers) if u.active_render]
   assert len(render)==1,(part['name'],len(render))
   index,layer=render[0]
   assert index==0 and layer.name=='SourceRenderUV',(part['name'],index,layer.name)
   by_material=collections.defaultdict(list)
   for poly in mesh.polygons:by_material[poly.material_index].extend(poly.loop_indices)
   selected=set(range(min(24,len(mesh.loops))))
   for indices in [list(range(len(mesh.loops)))]+list(by_material.values()):
    n=min(96 if len(indices)==len(mesh.loops) else 24,len(indices))
    selected.update(indices[round(k*(len(indices)-1)/max(1,n-1))] for k in range(n))
   probes=[{'position_m':list(mesh.vertices[mesh.loops[k].vertex_index].co),'uv0':list(layer.data[k].uv)} for k in sorted(selected)]
   out['parts'][part['name']]={'render_uv_name':layer.name,'render_uv_index':index,'uv_layer_names':[u.name for u in mesh.uv_layers],'probes':probes,'sampled_loop_count':len(probes),'total_loop_count':len(mesh.loops),'material_slots_sampled':sorted(by_material),'full_uv_equivalence':False}
  assert sha(group['blend'])==group['blend_sha256']
 print('RENDER_UV',family['id'],flush=True)
(HERE/'RENDER_UV_EVIDENCE_v003.json').write_text(json.dumps(out,separators=(',',':'))+'\n')
print('RENDER_UV_COMPLETE',len(out['parts']),flush=True)
