"""Read-only Blender mesh/UV interface audit; never save a blend or touch authoring state."""
import bpy, json, pathlib, math, hashlib, datetime
import numpy as np

BASE=pathlib.Path(r'C:\Users\USER\Documents\Pipeline Environment\ModelBank\Modular_2026-10-04\WholeBuildingConversions')
OUT=pathlib.Path(__file__).parent
PLANE_EPS=2e-5
GEO_TOL=0.0015
NORMAL_DOT_MIN=0.95

def read(p): return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def surface(normal):
    n=abs(normal[2])
    return 'horizontal_surface' if n>0.9 else ('vertical_surface' if n<0.25 else 'oblique_surface')

def segments(ob,axis,plane,assembly_translation):
    mesh=ob.data
    uv=mesh.uv_layers[0] if mesh.uv_layers else None
    offset=np.array(assembly_translation)-np.array(ob.matrix_world.translation)
    coords=[ob.matrix_world@v.co for v in mesh.vertices]
    for point in coords:
        for i in range(3): point[i]+=float(offset[i])
    normal_xform=ob.matrix_world.to_3x3().inverted().transposed()
    dims=[i for i in range(3) if i!=axis]
    result=[]; coplanar=[]
    for poly in mesh.polygons:
        loops=list(poly.loop_indices)
        on=[abs(coords[mesh.loops[li].vertex_index][axis]-plane)<PLANE_EPS for li in loops]
        if all(on):
            coplanar.append(poly.index)
            continue
        for j,li in enumerate(loops):
            lj=loops[(j+1)%len(loops)]
            if not(on[j] and on[(j+1)%len(loops)]): continue
            a=coords[mesh.loops[li].vertex_index]; b=coords[mesh.loops[lj].vertex_index]
            if (b-a).length<1e-7: continue
            normal=(normal_xform@poly.normal).normalized()
            slot=poly.material_index
            material=ob.material_slots[slot].material.name if slot<len(ob.material_slots) and ob.material_slots[slot].material else None
            result.append({'a':[a[i] for i in dims],'b':[b[i] for i in dims],
                           'uv_a':list(uv.data[li].uv) if uv else None,'uv_b':list(uv.data[lj].uv) if uv else None,
                           'normal':list(normal),'material':material,'polygon':poly.index,'class':surface(normal)})
    return {'object':ob.name,'axis':axis,'plane_m':plane,'virtual_offset_from_saved_N2_m':offset.tolist(),'uv_layer':uv.name if uv else None,
            'segment_count':len(result),'coplanar_face_count_excluded':len(coplanar),'segments':result}

def percentile(vals,p): return float(np.percentile(vals,p)) if vals else None

def compare(a,b,name):
    asegs=a['segments']; bsegs=b['segments']
    result={'interface':name,'a_object':a['object'],'b_object':b['object'],
            'a_segments':len(asegs),'b_segments':len(bsegs),'directional_profiles':[],
            'uv_samples':[], 'sample_spacing_uv_m':0.2,'sample_spacing_geometry_m':0.05,
            'normal_dot_min_for_uv_matching':NORMAL_DOT_MIN,'geometry_tolerance_m':GEO_TOL}
    if not asegs or not bsegs:
        result['status']='INCONCLUSIVE_MISSING_PROFILE'
        return result
    for source,target,label in [(asegs,bsegs,'A_to_B'),(bsegs,asegs,'B_to_A')]:
        ta=np.array([s['a'] for s in target]); tb=np.array([s['b'] for s in target]); td=tb-ta
        tl=np.sum(td*td,axis=1)
        tnormal=np.array([s['normal'] for s in target]); tmat=[s['material'] for s in target]
        distances=[]; endpoint_distances=[]; by_class={}
        unmatched=0; material_mismatch=0; normal_mismatch=0; ambiguous=0
        for ss in source:
            p0=np.array(ss['a']); p1=np.array(ss['b']); length=np.linalg.norm(p1-p0)
            steps=max(2,min(128,math.ceil(length/0.05)))
            points=p0+(p1-p0)*np.linspace(0,1,steps+1)[:,None]
            delta=points[:,None,:]-ta[None,:,:]
            t=np.clip(np.sum(delta*td[None,:,:],axis=2)/tl[None,:],0,1)
            closest=ta[None,:,:]+t[:,:,None]*td[None,:,:]
            dist=np.sqrt(np.sum((points[:,None,:]-closest)**2,axis=2))
            mins=np.min(dist,axis=1).tolist()
            distances.extend(mins); endpoint_distances.extend([mins[0],mins[-1]])
            by_class.setdefault(ss['class'],[]).extend(mins)

            steps_uv=max(3,min(64,math.ceil(length/0.2)))
            for frac in np.linspace(0.05,0.95,steps_uv):
                point=p0+(p1-p0)*frac
                tt=np.clip(np.sum((point[None,:]-ta)*td,axis=1)/tl,0,1)
                close=ta+tt[:,None]*td
                dd=np.linalg.norm(close-point[None,:],axis=1)
                dots=tnormal@np.array(ss['normal'])
                geometry=dd<=GEO_TOL
                material=np.array([m==ss['material'] for m in tmat])
                facing=dots>=NORMAL_DOT_MIN
                valid=np.where(geometry & material & facing)[0]
                if not len(valid):
                    unmatched+=1
                    if np.any(geometry) and not np.any(geometry&material): material_mismatch+=1
                    if np.any(geometry&material) and not np.any(geometry&material&facing): normal_mismatch+=1
                    continue
                idx=int(valid[np.argmin(dd[valid])])
                if ss['uv_a'] is None or target[idx]['uv_a'] is None:
                    unmatched+=1
                    continue
                uva=np.array(ss['uv_a'])+(np.array(ss['uv_b'])-ss['uv_a'])*frac
                uvb=np.array(target[idx]['uv_a'])+(np.array(target[idx]['uv_b'])-target[idx]['uv_a'])*tt[idx]
                uvdelta=uva-uvb
                phase=np.abs(uvdelta-np.round(uvdelta))
                near=valid[dd[valid]<=dd[idx]+1e-7]
                if len(near)>1:
                    otheruvs=[np.array(target[j]['uv_a'])+(np.array(target[j]['uv_b'])-target[j]['uv_a'])*tt[j] for j in near]
                    if max(np.linalg.norm(u-uvb) for u in otheruvs)>1e-4: ambiguous+=1
                result['uv_samples'].append({'direction':label,'class':ss['class'],
                    'position_cross_section_m':point.tolist(),'material':ss['material'],
                    'geometry_distance_m':float(dd[idx]),'normal_dot':float(dots[idx]),
                    'uv_a':uva.tolist(),'uv_b':uvb.tolist(),
                    'wrapped_phase_abs_xy':phase.tolist(),'wrapped_phase_l2':float(np.linalg.norm(phase))})
        result['directional_profiles'].append({'direction':label,'sample_count':len(distances),
            'profile_max_distance_m':max(distances),'profile_p95_distance_m':percentile(distances,95),
            'corner_endpoint_max_distance_m':max(endpoint_distances),
            'profile_by_surface_orientation':{k:{'samples':len(v),'max_distance_m':max(v),'p95_distance_m':percentile(v,95)} for k,v in by_class.items()},
            'uv_unmatched_samples':unmatched,'material_mismatch_samples':material_mismatch,
            'normal_mismatch_samples':normal_mismatch,'uv_ambiguous_samples':ambiguous})
    phases=[s['wrapped_phase_l2'] for s in result['uv_samples']]
    result['geometry_profile_hausdorff_sampled_m']=max(p['profile_max_distance_m'] for p in result['directional_profiles'])
    result['geometry_sampled_pass']=result['geometry_profile_hausdorff_sampled_m']<=GEO_TOL
    result['wrapped_uv_phase']={'sample_count':len(phases),'max_l2':max(phases) if phases else None,
                                'mean_l2':float(np.mean(phases)) if phases else None,
                                'p95_l2':percentile(phases,95),
                                'fraction_over_1e_4':sum(v>1e-4 for v in phases)/len(phases) if phases else None}
    result['status']='GEOMETRY_SAMPLED_ONLY_APPEARANCE_PENDING'
    return result

result=[]
for ep in sorted(BASE.glob('*/ExtensionBand/EXTENSION.json')):
    e=read(ep); before=sha(e['blend'])
    bpy.ops.wm.open_mainfile(filepath=e['blend'],load_ui=False)
    axis=e['corridor']['axis']; lower=e['corridor']['lower_plane_m']; upper=e['corridor']['upper_plane_m']
    parts={p['role']:bpy.data.objects[p['name']] for p in e['source_derived_parts']}
    translations={p['role']:p['assembly_translation_m'] for p in e['source_derived_parts']}
    start_hi=segments(parts['Start'],axis,lower,translations['Start'])
    rep_lo=segments(parts['Repeat'],axis,lower,translations['Repeat'])
    rep_hi=segments(parts['Repeat'],axis,upper,translations['Repeat'])
    end_lo=segments(parts['End'],axis,upper,translations['End'])
    comparisons=[compare(start_hi,rep_lo,'Start_to_Repeat_original_N1'),
                 compare(rep_hi,end_lo,'Repeat_to_End_original_N1'),
                 compare(rep_hi,rep_lo,'Repeat_to_Repeat_new_N2_N3')]
    record={'id':e['id'],'extension_manifest':str(ep),'blend':e['blend'],
            'source_blend_sha256_before':before,'source_blend_sha256_after':sha(e['blend']),
            'axis':axis,'pitch_m':e['corridor']['pitch_m'],
            'interface_profiles':{'Start_upper':start_hi,'Repeat_lower':rep_lo,'Repeat_upper':rep_hi,'End_lower':end_lo},
            'comparisons':comparisons,
            'virtual_variation_checks':[]}
    for n in (1,2,3):
        placements=[{'role':'Start','axis_offset_m':0.0}]
        placements.extend({'role':'Repeat','repeat_index':k,'axis_offset_m':k*e['corridor']['pitch_m']} for k in range(n))
        placements.append({'role':'End','axis_offset_m':(n-1)*e['corridor']['pitch_m']})
        record['virtual_variation_checks'].append({'repeat_count':n,'placements':placements,
            'new_repeat_interfaces':max(0,n-1),'new_interface_geometry_identical_up_to_translation':True,
            'repeat_cell_span_matches_pitch_error_m':abs((upper-lower)-e['corridor']['pitch_m']),
            'geometry_profile_sampled_pass':all(c.get('geometry_sampled_pass',False) for c in comparisons) if n>1 else all(c.get('geometry_sampled_pass',False) for c in comparisons[:2]),
            'native_generated':False,'saved_example':n==2,'saved_example_is_historical_source_only':n==2})
    result.append(record)
    print(e['id'],json.dumps([{k:c.get(k) for k in ('interface','geometry_profile_hausdorff_sampled_m','geometry_sampled_pass','wrapped_uv_phase')} for c in comparisons]))
(OUT/'EXTENSION_BOUNDARY_SAMPLES.json').write_text(json.dumps({'schema':'environmentpipeline.extension_boundary_samples.v1',
    'audited_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Read-only retained Blender geometry and first UV layer; no source saves, native acceptance or architectural role certification.',
    'families':result},indent=2),encoding='utf-8')
