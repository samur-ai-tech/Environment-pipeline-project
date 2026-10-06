"""Compile existing source bindings to a closed, hash-bound modular import request."""
import hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def one(links):
    assert len(links)==1,('unsupported_link_count',links)
    return links[0]

def compile_material(m,semantics):
    graph={n['name']:n for n in m['graph']}
    bsdf=[n for n in graph.values() if n['type']=='BSDF_PRINCIPLED'];assert len(bsdf)==1
    bsdf=bsdf[0]
    outs=[s for s in semantics.values() if s.get('is_active_output')]
    assert len(outs)==1 and outs[0]['surface_links']==[{'node':bsdf['name'],'socket':'BSDF','type':'BSDF_PRINCIPLED'}]
    assert not outs[0]['volume_links']
    for n in graph.values():
        if n['type']=='OUTPUT_MATERIAL':assert not n['inputs']['Displacement']['links'] and n['inputs']['Displacement']['default']==[0,0,0]
    params=bsdf['inputs']
    for key in ['Subsurface Weight','Anisotropic','Transmission Weight','Coat Weight','Sheen Weight','Thin Film Thickness','Diffuse Roughness']:
        assert not params[key]['links'] and params[key]['default']==0,(m['source_material'],key)
    assert params['IOR']['default']==1.5 and not params['IOR']['links']
    assert params['Specular Tint']['default']==[1,1,1,1] and not params['Specular Tint']['links']
    assert not params['Specular IOR Level']['links']
    textures={}
    def texture(node_name,kind):
        n=graph[node_name];assert n['type']=='TEX_IMAGE' and n['projection']=='FLAT'
        assert n['interpolation']=='Linear' and n['extension']=='REPEAT'
        assert n['colorspace']==('sRGB' if kind=='color' else 'Non-Color'),(m['source_material'],n['colorspace'],kind)
        link=one(n['inputs']['Vector']['links']);mapping=graph[link['node']]
        assert mapping['type']=='MAPPING' and semantics[mapping['name']]['vector_type']=='POINT'
        for key in ('Location','Rotation','Scale'):assert not mapping['inputs'][key]['links']
        assert mapping['inputs']['Rotation']['default']==[0,0,0]
        upstream=one(mapping['inputs']['Vector']['links'])
        assert graph[upstream['node']]['type']=='TEX_COORD' and upstream['output']=='UV'
        ref={'path':n['image'],'sha256':n['sha256'],'kind':kind,
             'uv_scale':mapping['inputs']['Scale']['default'][:2],
             'uv_offset':mapping['inputs']['Location']['default'][:2], 'uv_channel':0}
        assert sha(ref['path'])==ref['sha256']
        key=digest(ref);textures[key]=ref
        return key
    def channel(name,kind):
        socket=params[name]
        if not socket['links']:return {'constant':socket['default']}
        link=one(socket['links']);node=graph[link['node']]
        if node['type']=='TEX_IMAGE':
            assert link['output'] in ('Color','Alpha')
            return {'texture':texture(node['name'],kind),'output':'RGB' if link['output']=='Color' else 'A'}
        assert node['type']=='SEPARATE_COLOR' and semantics[node['name']]['mode']=='RGB'
        inner=one(node['inputs']['Color']['links']);assert inner['output']=='Color'
        return {'texture':texture(inner['node'],'data'),'output':{'Red':'R','Green':'G','Blue':'B'}[link['output']]}
    channels={name:channel(name,kind) for name,kind in [('Base Color','color'),('Roughness','data'),('Metallic','data'),('Alpha','color'),('Emission Color','color')]}
    assert channels['Alpha']=={'constant':1.0},('unsupported_nonopaque_alpha',m['source_material'])
    assert not params['Emission Strength']['links']
    normal={'constant':[0,0,1], 'strength':0.0}
    if params['Normal']['links']:
        link=one(params['Normal']['links']);n=graph[link['node']]
        assert n['type']=='NORMAL_MAP' and n['space']=='TANGENT' and n['uv_map'] in ('','SourceRenderUV')
        assert semantics[n['name']]['convention']=='OPENGL'
        assert not n['inputs']['Strength']['links']
        strength=float(n['inputs']['Strength']['default']);assert strength>=0
        if n['inputs']['Color']['links']:
            inner=one(n['inputs']['Color']['links']);assert inner['output']=='Color'
            normal={'texture':texture(inner['node'],'normal'),'strength':strength}
        else:
            assert n['inputs']['Color']['default']==[0.5,0.5,1,1]
            normal={'constant':[0,0,1],'strength':strength}
    return {'source_material':m['source_material'],'source_graph_sha256':digest(m),
            'two_sided':not m['backface_culling'],'channels':channels,'textures':textures,
            'normal':normal,'specular':float(params['Specular IOR Level']['default']),
            'emission_strength':float(params['Emission Strength']['default']),
            'normal_strength_rule':'normalize((nx*s,ny*s,1+(nz-1)*clamp(s,0,1)))',
            'normal_strength_reference':'https://raw.githubusercontent.com/blender/blender/blender-v5.2-release/source/blender/gpu/shaders/material/gpu_shader_material_normal_map.glsl',
            'source_graph_supported':True,'visual_fidelity_verified':False,
            'unconnected_source_AO_group':'Retained in source evidence; not connected to source surface, so not added to native surface.'}

def build():
    source=read(HERE/'SOURCE_BINDINGS.json');semantics=read(HERE/'SHADER_SEMANTICS.json')
    duplicate_proof=HERE.parents[1]/'ModularConstruction_2026-10-05/SourceAudit/DUPLICATE_FACE_SLOT_READBACK.json'
    duplicates={r['part_name']:r for r in read(duplicate_proof)['parts']}
    assert set(duplicates)=={'SM_H0018_Tier04_EastFacade','SM_H0021_Roof_Core'}
    assert semantics['source_bindings_sha256']==sha(HERE/'SOURCE_BINDINGS.json')
    request={'schema':'environmentpipeline.modular_native_import_request.v1','family_count':20,'part_count':609,
             'families':[],'files':{},'python_sources':{},'native_authorized':False,
             'selection_changes':False,'map_saves':False,'originals_modified':False}
    def pin(p,expected=None):
        p=str(Path(p).resolve());s=sha(p)
        if expected:assert s==expected,(p,'source_changed')
        request['files'][p]=s
    pin(HERE/'SOURCE_BINDINGS.json');pin(HERE/'SHADER_SEMANTICS.json');pin(duplicate_proof)
    for f in source['families']:
        result={k:f[k] for k in ('id','family_id','parent_asset_id','parent_catalog_row','rights_state','explicit_hold','hold_reasons')}
        result.update(source_family_sha256=digest(f),materials={},parts=[],enabled=False)
        pin(f['assembly_path'],f['assembly_sha256']);pin(f['readback_path'],f['readback_sha256'])
        readback={r['name']:r for r in read(f['readback_path'])['fbx_readbacks']}
        for group in f['sets']:
            pin(group['blend'],group['blend_sha256'])
            maps={}
            for name,m in group['materials'].items():
                compiled=compile_material(m,semantics['families'][f['id']][group['kind']][name])
                key=digest(compiled);result['materials'][key]=compiled;maps[name]=key
                for ref in compiled['textures'].values():pin(ref['path'],ref['sha256'])
            for part in group['parts']:
                pin(part['fbx'],part['fbx_sha256'])
                p=dict(part);p.update(kind=group['kind'],derivative_id=f['family_id']+'/'+part['name'],
                                    material_keys=[maps[n] for n in part['source_material_slots']],
                                    source_readback=readback.get(part['name']),
                                    source_uv0_probes=semantics['uv_probes'][part['name']])
                if part['name'] in duplicates:
                    proof=duplicates[part['name']]
                    assert proof['source_unchanged'] and proof['recorded_fbx_sha256']==part['fbx_sha256']==proof['actual_fbx_sha256_before']==proof['actual_fbx_sha256_after']
                    assert group['blend_sha256']==proof['source_blend_sha256_before']==proof['source_blend_sha256_after']
                    expected_slots=proof['fresh_blender_fbx_readback']['slots']
                    assert [r['material_name'] for r in expected_slots]==part['source_material_slots']
                    assert {str(r['slot_index']):r['triangle_count'] for r in proof['source']['slots'] if r['triangle_count']}==part['slot_triangle_counts']
                    p['roundtrip_slot_triangle_counts']={str(r['slot_index']):r['triangle_count'] for r in expected_slots if r['triangle_count']}
                    p['roundtrip_proof_sha256']=sha(duplicate_proof)
                result['parts'].append(p)
        request['families'].append(result)
    assert sum(len(f['parts']) for f in request['families'])==609
    for p in [HERE/'modular_native_adapter.py',HERE/'run_modular_command.py',HERE/'build_native_request.py',HERE/'inspect_modular_startup.py',HERE.parent/'bank_contracts.py',HERE.parent/'native_bank_ops.py',HERE.parent/'import_prepared.py',HERE.parent/'bank_batch_loader.py']:
        request['python_sources'][str(p.resolve())]=sha(p)
    path=HERE/'NATIVE_IMPORT_REQUEST.json';path.write_text(json.dumps(request,indent=2)+'\n')
    print(json.dumps({'request':str(path),'sha256':sha(path),'families':20,'parts':609,'pins':len(request['files'])}))

if __name__=='__main__':build()
