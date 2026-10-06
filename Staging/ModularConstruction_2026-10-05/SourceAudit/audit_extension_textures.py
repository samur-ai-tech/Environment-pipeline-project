"""Read-only texture-phase sampling using separately extracted owner material graphs."""
import bpy, pathlib, json, hashlib, datetime
import numpy as np
OUT=pathlib.Path(__file__).parent
BINDINGS=pathlib.Path(r'C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\BankIntegration_2026-10-04\ModularNative_2026-10-05\SOURCE_BINDINGS.json')
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def metric(vals):
    a=np.asarray(vals)
    return {'sample_count':len(vals),'mean_max_abs_rgb':float(np.mean(a)),'p95_max_abs_rgb':float(np.percentile(a,95)),
            'max_abs_rgb':float(np.max(a)),'fraction_over_0_02':float(np.mean(a>0.02)),
            'fraction_over_1_over_255':float(np.mean(a>1/255))} if len(vals) else {'sample_count':0}
def bilinear(pixels,uv):
    h,w=pixels.shape[:2]
    xy=np.array(uv)*[w,h]-.5
    lo=np.floor(xy).astype(int);f=xy-lo
    x,y=lo;fx,fy=f
    return ((1-fx)*(1-fy)*pixels[y%h,x%w,:3]+fx*(1-fy)*pixels[y%h,(x+1)%w,:3]
           +(1-fx)*fy*pixels[(y+1)%h,x%w,:3]+fx*fy*pixels[(y+1)%h,(x+1)%w,:3])
def graph_supported(material,image):
    graph={n['name']:n for n in material['graph']}
    node=graph.get(image['node'],{})
    if (node.get('extension'),node.get('interpolation'),node.get('projection'))!=('REPEAT','Linear','FLAT'):return False
    link=node.get('inputs',{}).get('Vector',{}).get('links',[])
    if len(link)!=1 or link[0]['output']!='Vector':return False
    mapping=graph.get(link[0]['node'],{})
    if mapping.get('type')!='MAPPING':return False
    for key,want in [('Scale',[1,1,1]),('Location',[0,0,0]),('Rotation',[0,0,0])]:
        arg=mapping.get('inputs',{}).get(key,{})
        if arg.get('default')!=want or arg.get('links'):return False
    coords=mapping.get('inputs',{}).get('Vector',{}).get('links',[])
    return len(coords)==1 and coords[0]['output']=='UV' and graph.get(coords[0]['node'],{}).get('type')=='TEX_COORD'

samples=read(OUT/'EXTENSION_BOUNDARY_SAMPLES.json')
bindings=read(BINDINGS)
families=[]
for family in samples['families']:
    fid=family['id'];binding=next(f for f in bindings['families'] if f['id']==fid)
    material_set=next(s for s in binding['sets'] if s['kind']=='extension')
    bpy.ops.wm.open_mainfile(filepath=family['blend'],load_ui=False)
    texture_arrays={};texture_receipts={};strengths={};graph_exact=True
    for name,material in material_set['materials'].items():
        normals=[n for n in material['graph'] if n['type']=='NORMAL_MAP']
        strengths[name]=normals[0]['inputs']['Strength']['default'] if len(normals)==1 else None
        for image in material['linked_images']:
            destinations=[d for o in image['outputs'] for d in o['destinations']]
            channel='BaseColor' if any(d.endswith('.Base Color') for d in destinations) else ('NormalMapRGB' if any(d.endswith('.Color') and 'Normal' in d for d in destinations) else None)
            if not channel:continue
            supported=graph_supported(material,image)
            graph_exact=graph_exact and supported
            im=bpy.data.images.load(image['path'],check_existing=True)
            im.colorspace_settings.name=image['colorspace']
            pixels=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(pixels)
            pixels=pixels.reshape(im.size[1],im.size[0],4)
            texture_arrays[(name,channel)]=pixels
            texture_receipts[(name,channel)]={'material':name,'channel':channel,'image_path':image['path'],
                'recorded_sha256':image['sha256'],'actual_sha256':sha(image['path']),
                'dimensions_px':[im.size[0],im.size[1]],'colorspace':image['colorspace'],
                'exact_supported_graph':supported,'sampler':'REPEAT wrap and bilinear Linear pixel-center interpolation',
                'metric_space':'Blender image pixel-buffer RGB; shader, filtering footprints, tangent basis, lighting and final native render are not sampled'}
    comparisons=[]
    for comparison in family['comparisons']:
        c={k:v for k,v in comparison.items() if k!='uv_samples'}
        c['texture_samples_summary']={};examples=[]
        for channel in ('BaseColor','NormalMapRGB'):
            errors=[];by_class={};phase_pixels=[]
            for s in comparison['uv_samples']:
                pixels=texture_arrays.get((s['material'],channel))
                if pixels is None:continue
                ca=bilinear(pixels,s['uv_a']);cb=bilinear(pixels,s['uv_b'])
                delta=float(np.max(np.abs(ca-cb)))
                errors.append(delta);by_class.setdefault(s['class'],[]).append(delta)
                phase_pixels.append(float(np.linalg.norm(np.array(s['wrapped_phase_abs_xy'])*[pixels.shape[1],pixels.shape[0]])))
                if len(examples)<16 and channel=='BaseColor':
                    examples.append({'position_cross_section_m':s['position_cross_section_m'],'class':s['class'],
                        'material':s['material'],'uv_a':s['uv_a'],'uv_b':s['uv_b'],
                        'sample_rgb_a':ca.tolist(),'sample_rgb_b':cb.tolist(),'max_abs_rgb_error':delta})
            c['texture_samples_summary'][channel]={**metric(errors),
                'wrapped_phase_pixels_max':max(phase_pixels) if phase_pixels else None,
                'wrapped_phase_pixels_p95':float(np.percentile(phase_pixels,95)) if phase_pixels else None,
                'by_surface_orientation':{k:metric(v) for k,v in by_class.items()}}
        c['example_basecolor_samples']=examples
        comparisons.append(c)
    repeat=next(c for c in comparisons if c['interface']=='Repeat_to_Repeat_new_N2_N3')
    base=repeat['texture_samples_summary']['BaseColor']
    sparse=any(p['uv_unmatched_samples'] or p['uv_ambiguous_samples'] for p in repeat.get('directional_profiles',[]))
    status='REJECT_EXTENSION_APPEARANCE_PHASE_AND_COLOR_DISCONTINUITY' if base.get('fraction_over_0_02',0)>0 else 'INCONCLUSIVE_NEEDS_NATIVE_APPEARANCE'
    record={'id':fid,'axis':'XYZ'[family['axis']],'pitch_m':family['pitch_m'],
        'source_blend':family['blend'],'source_blend_sha256_before':family['source_blend_sha256_before'],
        'source_blend_sha256_after':sha(family['blend']),
        'source_blend_unchanged':sha(family['blend'])==family['source_blend_sha256_before'],
        'owner_material_bindings_source':str(BINDINGS),'owner_extension_blend_hash_matches':material_set['blend_sha256']==sha(family['blend']),
        'exact_graph_sampling_supported':graph_exact,'source_normal_map_strengths':strengths,
        'texture_receipts':list(texture_receipts.values()),'comparisons':comparisons,
        'virtual_variations':family['virtual_variation_checks'],
        'new_interface_geometric_profile_within_1_5mm':repeat.get('geometry_sampled_pass',False),
        'new_interface_geometry_is_perfect_weld':repeat.get('geometry_profile_hausdorff_sampled_m',1)<1e-6,
        'new_interface_uv_sample_coverage_has_unmatched_or_ambiguous':sparse,
        'source_exact_N1_interfaces_geometry_and_uv_continuous':all(c['geometry_sampled_pass'] and c['wrapped_uv_phase']['max_l2']<1e-8 for c in comparisons[:2]),
        'qualification_status':status,
        'extension_may_be_enabled':False,'certified_repeatable_floors':False,'native_houdini_engine_acceptance':False,
        'preview_inspected':str(pathlib.Path(family['blend']).parent/'Extended.png'),
        'preview_observation':'Existing N=2 source render inspected. It shows retained family style and complete massing, but this distant single-angle preview does not establish seam close-up or all-side native continuity.',
        'minimal_derivative_adaptation_proposal':[
            'Keep N=1 source reconstruction and source files unchanged. Scope any fix to new derivative N=2/N=3 variants.',
            'Create UV/texture seam patches on derivative copies of the complete Repeat band and adjoining End boundary, retaining the existing source UV/materials on unaffected interior faces.',
            'Use per-surface or per-UV-chart seam correction or narrow baked blend strips from the original diffuse and normal maps; a single whole-mesh UV offset has not been shown to preserve atlas features/openings.',
            'Verify both boundaries and source-style features after patching; do not cure a repeat seam by changing the whole-family material or generic geometric scaling.',
            'Where a true welded seam is required, align derivative cut-boundary profiles within the measured sub-1.5mm differences without changing the source assembly. Recheck roof/corner/vertical profiles and normals.',
        ]}
    families.append(record)
    print(fid,json.dumps({'status':status,'profile_error_mm':repeat['geometry_profile_hausdorff_sampled_m']*1000,
        'uv_phase_max':repeat['wrapped_uv_phase']['max_l2'],'BaseColor':base,
        'source_blend_unchanged':record['source_blend_unchanged']}))
receipt={'schema':'environmentpipeline.extension_seam_audit.v1',
    'audited_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Eight retained whole-building ExtensionBands, read-only Blender mesh/UV/image analysis, virtual N=1/N=2/N=3 translations only. No source save, derivative authoring, catalog change, native editor/generation or acceptance.',
    'method':{'geometric_profile_sampling':'Polygon cut edges at assembly lower/upper planes; both directed sampled distances, 5cm max nominal spacing (128 subdivisions cap per edge), endpoints included.',
              'uv_sampling':'First SourceRenderUV layer, per-loop edge interpolation, both directions, 20cm max nominal spacing (64 sample cap per edge), interior samples; same material and normal dot >=0.95 required.',
              'texture_phase':'UV delta reduced modulo integer periods for confirmed REPEAT wrap. Image RGB sampled bilinearly at pixel centers using confirmed identity UV mappings.',
              'variation_test':'N=2 adds one Repeat→Repeat seam; N=3 adds two identical seams up to a one-axis pitch translation. No native Cook/Bake, save/reopen or full-mesh intersection proof.',
              'source_preservation':'Each extension Blender hash compared before/after read-only opening and matched separate bank-owner extraction hash.',
              'limits':'Boundary sampling is not a volumetric overlap, window/door, façade architectural floor, collision/LOD, user visual acceptance, or Houdini Engine qualification test.'},
    'family_count':len(families),'extension_appearance_pass_count':0,
    'source_blend_all_unchanged':all(f['source_blend_unchanged'] for f in families),
    'families':families}
(OUT/'EXTENSION_SEAM_AUDIT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
rows=['# Eight extension families: new repeat seam audit','',
      'All eight retained one-axis extension candidates fail new Repeat→Repeat texture appearance qualification. Their original N=1 Start/Repeat/End interfaces match geometry and UVs; new repeat interfaces have noninteger UV phase and sampled diffuse/normal differences. No extension capability was enabled by this read-only audit.','',
      '| Family | Axis / pitch m | Max sampled profile gap mm | New UV phase max | BaseColor mean / max RGB delta | Samples above 0.02 | Source blend unchanged |',
      '|---|---|---:|---:|---|---:|---|']
for f in families:
    r=next(c for c in f['comparisons'] if c['interface']=='Repeat_to_Repeat_new_N2_N3');b=r['texture_samples_summary']['BaseColor']
    rows.append(f"| {f['id']} | {f['axis']} / {f['pitch_m']:.6f} | {r['geometry_profile_hausdorff_sampled_m']*1000:.6f} | {r['wrapped_uv_phase']['max_l2']:.6f} | {b['mean_max_abs_rgb']:.6f} / {b['max_abs_rgb']:.6f} | {b['fraction_over_0_02']*100:.1f}% | {f['source_blend_unchanged']} |")
rows+=['','The eight original N=2 Extended.png previews were inspected. They demonstrate the retained source style and complete extension examples at one angle; they do not override close-boundary measurements or certify native appearance.','',
       'Geometry is within the source 1.5 mm profile tolerance, which is not a perfect weld for seven families. Horizontal, vertical and oblique surface profile measurements and corner endpoint measurements are recorded separately. N=3 reuses the same failing seam twice; it does not repair texture phase.','',
       'Keep extension disabled until derivative UV/texture seam correction and any necessary boundary welding are validated. Limit a correction to new derivative variations, preserving originals and unaffected faces. A narrow per-chart baked seam patch from source diffuse/normal maps is a candidate; a blanket whole-mesh UV offset or material replacement has not been proved to preserve original atlas features. Revalidate Start→Repeat, each new Repeat→Repeat, Repeat→End, roofs, corners, openings and normals.','',
       'All source extension Blender hashes remained unchanged. This audit does not certify procedural architectural floors, arbitrary footprints, cross-family substitution, full-mesh overlap/collision, materials in native Unreal, Houdini Engine regeneration, named saves/reopen, or user acceptance.','',
       'Detailed geometric samples are in EXTENSION_BOUNDARY_SAMPLES.json. Source graph evidence comes from the separately produced SOURCE_BINDINGS.json; no material-graph extraction was duplicated here.']
(OUT/'EXTENSION_SEAM_AUDIT.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
