"""Offline v005 source renders, fixed-distance comparisons and slope proof.

Never saves an opened source. All files and compressed caches stay in v005.
"""
import argparse,sys,html
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from distance_core import *
from mathutils import Matrix

ap=argparse.ArgumentParser()
ap.add_argument('--mode',choices=['singles','block','extras','all','report'],default='all')
ap.add_argument('--distances',nargs='*',type=float)
ap.add_argument('--resume',action='store_true')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=ROOT/'Previews/Distance';CACHE=ROOT/'Temp/DistanceCache';REPORT=ROOT/'Reports'
for p in (OUT,CACHE,REPORT):p.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'Blend/StrawberryBeds.blend'
PREFIX='SM_PazFarm_StrawberryBed_4m_'
PITCH=math.atan(.03)
CONFIG={**SETTINGS,'revision':'StrawberryBeds_v005','single_horizontal_fov_deg':85,
        'single_elevation_deg':45,'single_azimuth_deg':0,
        'block_horizontal_fov_deg':110,'block_elevation_deg':70,'block_azimuth_deg':0,
        'renderer_sha256':sha(__file__),'helper_sha256':sha(Path(__file__).with_name('distance_core.py')),
        'ground_for_metrics':'Holdout ground at actual support plane clips hidden skirts; alpha is visible asset geometry only.',
        'ground_for_beauty':'Matte procedural soil on the same plane; preview only, not exported.',
        'beauty_film_transparent':False,
        'row_centres_m':1.7,'row_count':10,'tiles_per_row':5,'tile_surface_length_m':4,
        'slope':.03,'slope_angle_deg':math.degrees(PITCH),'sink_m':0,
        'row_end_caps':'Both ends; 20 caps plus 50 regular tiles.',
        'cache':'Lossless compressed npz, never uncompressed persistent arrays.'}
CONFIG_SHA=hashlib.sha256(json.dumps(CONFIG,sort_keys=True).encode()).hexdigest()
ALL=[]

def srgb(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4

def required_texture_hashes():
    result={}
    for im in bpy.data.images:
        if im.source=='FILE':
            assert im.filepath,'Required FILE image has no path: '+im.name
            path=Path(bpy.path.abspath(im.filepath))
            assert path.is_file(),'Required texture missing: '+str(path)
            result[str(path.resolve())]=sha(path)
    assert result,'No source textures found'
    return result

def ground(scene,angle):
    mesh=bpy.data.meshes.new('Preview_ground_only')
    mesh.from_pydata([(-10000,-10000,0),(10000,-10000,0),(10000,10000,0),(-10000,10000,0)],[],[(0,1,2,3)])
    obj=bpy.data.objects.new('Preview_ground_only',mesh);scene.collection.objects.link(obj)
    obj.rotation_euler.x=angle
    hold=bpy.data.materials.new('Preview_holdout_only');hold.use_nodes=True
    n=hold.node_tree.nodes;n.clear();h=n.new('ShaderNodeHoldout');out=n.new('ShaderNodeOutputMaterial')
    hold.node_tree.links.new(h.outputs[0],out.inputs['Surface'])
    earth=bpy.data.materials.new('Preview_soil_only');earth.use_nodes=True
    n=earth.node_tree.nodes;b=n.get('Principled BSDF');b.inputs['Roughness'].default_value=.97
    b.inputs['Specular IOR Level'].default_value=.04
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=80
    noise.inputs['Detail'].default_value=3;noise.inputs['Roughness'].default_value=.7
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=(*[srgb(x/255) for x in (99,75,49)],1)
    ramp.color_ramp.elements[1].color=(*[srgb(x/255) for x in (151,124,89)],1)
    tex=n.new('ShaderNodeTexCoord');earth.node_tree.links.new(tex.outputs['Object'],noise.inputs['Vector'])
    earth.node_tree.links.new(noise.outputs['Fac'],ramp.inputs['Fac']);earth.node_tree.links.new(ramp.outputs['Color'],b.inputs['Base Color'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.2;bump.inputs['Distance'].default_value=.008
    earth.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);earth.node_tree.links.new(bump.outputs['Normal'],b.inputs['Normal'])
    obj.data.materials.append(hold)
    return obj,hold,earth

def position(cam,target,distance,elevation,azimuth,fov):
    target=Vector(target);az=math.radians(azimuth);el=math.radians(elevation)
    cam.data.sensor_fit='HORIZONTAL';cam.data.lens=36/(2*math.tan(math.radians(fov)/2))
    cam.location=target+Vector((math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),math.sin(el)))*distance
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()

def cached(rec):
    p=CACHE/(rec['png_sha256']+'.npz')
    if p.exists():
        with np.load(p) as d:return d['rgba']
    arr=png_read(ROOT/rec['file']);np.savez_compressed(p,rgba=arr);return arr

def render(scene,cam,objects,ground_info,name,lod,kind,arrangement,target,distance,elevation,azimuth,fov,source_hash,textures,resolution=(1920,1080)):
    file=OUT/(name+'.png');meta=OUT/(name+'.json')
    if args.resume and file.is_file() and meta.is_file():
        rec=json.loads(meta.read_text())
        if rec.get('source_blend_sha256')==source_hash and rec.get('source_texture_sha256')==textures and rec.get('settings_sha256')==CONFIG_SHA and rec.get('png_sha256')==sha(file):
            ALL.append(rec);print('RESUME',name,flush=True);return
    for o in scene.objects:
        if o.type=='MESH':o.hide_render=True
    for o in objects:o.hide_render=False
    gr,hold,earth=ground_info;gr.hide_render=False;gr.data.materials[0]=hold if kind=='geometry' else earth
    scene.render.resolution_x,scene.render.resolution_y=resolution
    scene.render.film_transparent=(kind=='geometry')
    position(cam,target,distance,elevation,azimuth,fov)
    scene.render.filepath=str(file);started=time.monotonic();bpy.ops.render.render(write_still=True)
    img=png_read(file);digest=sha(file)
    np.savez_compressed(CACHE/(digest+'.npz'),rgba=img)
    rec={'id':name,'file':file.relative_to(ROOT).as_posix(),'lod':lod,'kind':kind,'arrangement':arrangement,
         'distance_m':distance,'actual_target_distance_m':round((cam.location-Vector(target)).length,6),
         'target_m':rounded(target),'camera_position_m':rounded(cam.location),
         'camera_rotation_xyz_deg':rounded([math.degrees(x) for x in cam.rotation_euler]),
         'elevation_deg':elevation,'azimuth_deg':azimuth,'horizontal_fov_deg':fov,'resolution_px':list(resolution),
         'object_count':len(objects),'world_bounds_m':bbox_world(objects),
         'projected_bounds':projected_bounds(scene,cam,objects) if resolution==(1920,1080) else None,
         'ground_slope':math.tan(gr.rotation_euler.x),'ground_mode':'holdout' if kind=='geometry' else 'preview_soil',
         'metrics':metrics(img) if kind=='geometry' else None,'close_crop_expected':arrangement.startswith('single') and distance==1,
         'render_seconds':round(time.monotonic()-started,3),'settings_sha256':CONFIG_SHA,
         'source_blend':'Blend/StrawberryBeds.blend','source_blend_sha256':source_hash,
         'source_texture_sha256':textures,'texture_hash_capture':'before render','png_sha256':digest}
    meta.write_text(json.dumps(rec,indent=2)+'\n');ALL.append(rec)
    (REPORT/('distance_'+args.mode+'_progress.json')).write_text(json.dumps({'settings':CONFIG,'frames':ALL},indent=2)+'\n')
    print('FRAME_DONE',name,json.dumps(rec['metrics']),flush=True)

def clone(scene,model,name,location,rotation):
    o=model.copy();o.data=model.data;o.name=name;scene.collection.objects.link(o)
    o.matrix_world=Matrix.Translation(Vector(location))@rotation.to_4x4();o.hide_render=True
    return o

def block(scene):
    placements=[]
    # Sequence includes all nine directed joins across the ten rows.
    sequences=['AABAC','BBCCA','ABCBA','CCABA','BCABC','ACBBA','CABCC','BAACB','CBABC','ABCCA']
    rot=Matrix.Rotation(PITCH,3,'X')
    for row in range(10):
        x=(row-4.5)*1.7
        for tile,v in enumerate(sequences[row]):
            pos=(x,4*tile*math.cos(PITCH),4*tile*math.sin(PITCH))
            placements.append((PREFIX+v,pos,rot,'tile',row,tile))
        placements.append(('SM_PazFarm_StrawberryBedEnd',(x,0,0),rot@Matrix.Rotation(math.pi,3,'Z'),'start_cap',row,-1))
        placements.append(('SM_PazFarm_StrawberryBedEnd',(x,20*math.cos(PITCH),20*math.sin(PITCH)),rot,'end_cap',row,5))
    groups={}
    for lod in ('LOD0','LOD3'):
        groups[lod]=[clone(scene,bpy.data.objects[n+('_LOD3' if lod=='LOD3' else '')],f'Block_{lod}_{i}',pos,r) for i,(n,pos,r,_,_,_) in enumerate(placements)]
    bpy.context.view_layer.update()
    report={'arrangement':'10 rows by 5 regular tiles plus two optional caps per row','row_centres_m':1.7,'slope':.03,
            'pitch_angle_deg':math.degrees(PITCH),'sink_m':0,'chain_method':'Each origin follows the previous rotated endpoint.',
            'native_placement':False,'placements':[{'base_model':n,'position_m':rounded(pos),'rotation_matrix':[[float(x) for x in row] for row in r],'role':role,'row':ri,'tile':ti} for n,pos,r,role,ri,ti in placements],
            'maximum_join_origin_error_m':max((Vector(placements[row*7+t+1][1])-(Vector(placements[row*7+t][1])+rot@Vector((0,4,0)))).length for row in range(10) for t in range(4))}
    if args.mode in ('block','all'):
        (REPORT/'slope_preview_placements.json').write_text(json.dumps(report,indent=2)+'\n')
    return groups

def run():
    digest=sha(SOURCE);bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False)
    scene,cam=configure_scene();textures=required_texture_hashes()
    flat=ground(scene,0);slope=ground(scene,PITCH)
    def do(objects,gr,name,lod,kind,arr,target,d,elev,az,fov,res=(1920,1080)):
        render(scene,cam,objects,gr,name,lod,kind,arr,target,d,elev,az,fov,digest,textures,res)
    if args.mode in ('singles','all'):
        for v in 'ABC':
            for d in (1,3):
                if args.distances and d not in args.distances:continue
                for lod in ('LOD0','LOD3'):
                    obj=bpy.data.objects[PREFIX+v+('_LOD3' if lod=='LOD3' else '')]
                    target=(0,1.05,.29) if d==1 else (0,2,.19)
                    do([obj],flat,f'single_{v}_{d}m_{lod}',lod,'geometry','single_'+v,target,d,45,0,85)
    if args.mode in ('block','extras','all'):
        groups=block(scene);target=(0,10*math.cos(PITCH),10*math.sin(PITCH)+.18)
        if args.mode in ('block','all'):
            for d in (15,60,150,500,4000):
                if args.distances and d not in args.distances:continue
                for lod in ('LOD0','LOD3'):
                    do(groups[lod],slope,f'block_10x5_{d}m_{lod}',lod,'geometry','block_10x5',target,d,70,0,110)
                    if d!=4000:do(groups[lod],slope,f'field_3pct_{d}m_{lod}',lod,'beauty','block_10x5',target,d,70,0,110)
        if args.mode in ('extras','all'):
            # Camera for the Huelva comparison: look along the furrows from standing eye height.
            ref_target=(.65,2.0,.33)
            eye=Vector((.75,-.35,1.75));vec=eye-Vector(ref_target)
            elev=math.degrees(math.asin(vec.z/vec.length));az=math.degrees(math.atan2(vec.y,vec.x))
            do(groups['LOD0'],slope,'reference_angle_LOD0','LOD0','beauty','reference_angle',ref_target,vec.length,elev,az,46,(800,1200))
            objs=[]
            for i,v in enumerate('ABC'):
                objs.append(clone(scene,bpy.data.objects[PREFIX+v],f'Seam_{v}',(0,i*4,0),Matrix.Identity(3)))
            do(objs,flat,'seams_ABC_grazing_LOD0','LOD0','beauty','seam_strip',(0,6,.19),9,8,-25,82)
            do(objs,flat,'seams_ABC_top_LOD0','LOD0','beauty','seam_strip',(0,6,.19),9,78,-70,82)
    assert sha(SOURCE)==digest,'Source changed during render'
    assert required_texture_hashes()==textures,'Texture changed during render'

def report():
    expected=set()
    for v in 'ABC':
        for d in (1,3):
            for l in ('LOD0','LOD3'):expected.add(f'single_{v}_{d}m_{l}')
    for d in (15,60,150,500,4000):
        for l in ('LOD0','LOD3'):
            expected.add(f'block_10x5_{d}m_{l}')
            if d!=4000:expected.add(f'field_3pct_{d}m_{l}')
    expected.update(['reference_angle_LOD0','seams_ABC_grazing_LOD0','seams_ABC_top_LOD0'])
    records=[json.loads(p.read_text()) for p in OUT.glob('*.json')]
    records=[r for r in records if r.get('settings_sha256')==CONFIG_SHA]
    records.sort(key=lambda r:r['id']);hashcache={}
    def current(p):
        p=str(p)
        if p not in hashcache:hashcache[p]=sha(p) if Path(p).is_file() else None
        return hashcache[p]
    bindings=[{'frame':r['id'],'current':current(ROOT/r['source_blend'])==r['source_blend_sha256'] and current(ROOT/r['file'])==r['png_sha256'] and bool(r['source_texture_sha256']) and all(current(p)==h for p,h in r['source_texture_sha256'].items()),'captured_before_render':r['texture_hash_capture']=='before render'} for r in records]
    byid={r['id']:r for r in records};pairs=[]
    for r in records:
        if r['kind']!='geometry' or r['lod']!='LOD0':continue
        other=byid.get(r['id'].replace('LOD0','LOD3'))
        if not other:continue
        a,b=cached(r),cached(other);aa=a[...,3].astype(float)/255;bb=b[...,3].astype(float)/255
        m0,m3=r['metrics'],other['metrics'];area=m3['equivalent_opaque_pixels']/max(m0['equivalent_opaque_pixels'],1e-12)
        rec={'id':r['id'].replace('_LOD0',''),'LOD0_frame':r['id'],'LOD3_frame':other['id'],
             'arrangement':r['arrangement'],'distance_m':r['distance_m'],
             'alpha_iou':round(float(np.minimum(aa,bb).sum()/max(np.maximum(aa,bb).sum(),1e-12)),5),
             'lowest_area_ratio':round(area,5),'lowest_minus_detailed_luma':round(m3['alpha_weighted_luma_code_value']-m0['alpha_weighted_luma_code_value'],3),
             'lowest_minus_detailed_lit_srgb':rounded(np.asarray(m3['alpha_weighted_lit_srgb'])-m0['alpha_weighted_lit_srgb'],3),
             'both_visible':m0['equivalent_opaque_pixels']>0 and m3['equivalent_opaque_pixels']>0,
             'clipped':m0['clipped_at_image_border'] or m3['clipped_at_image_border'],'review_flags':[]}
        if not rec['both_visible']:rec['review_flags'].append('zero coverage')
        if not rec['clipped']:
            if not .75<=area<=1.25:rec['review_flags'].append('area ratio outside 0.75..1.25')
            if abs(rec['lowest_minus_detailed_luma'])>12:rec['review_flags'].append('absolute luma change greater than 12')
        if r['distance_m']>=60:
            yy,xx=np.nonzero((aa>0)|(bb>0))
            if len(xx):
                x0,x1=max(0,int(xx.min())-4),min(1920,int(xx.max())+5);y0,y1=max(0,int(yy.min())-4),min(1080,int(yy.max())+5)
                factor=max(1,min(24,540//max(x1-x0,y1-y0)))
                ca=np.repeat(np.repeat(a[y0:y1,x0:x1],factor,0),factor,1);cb=np.repeat(np.repeat(b[y0:y1,x0:x1],factor,0),factor,1)
                result=np.zeros((ca.shape[0],ca.shape[1]*2+12,4),np.uint8);result[:,:ca.shape[1]]=ca;result[:,ca.shape[1]+12:]=cb
                fn=OUT/('MAGNIFIED_'+rec['id']+f'_{factor}x.png');png_write(fn,diagnostic_background(result))
                rec['magnified']={'file':fn.relative_to(ROOT).as_posix(),'factor':factor,'crop_xyxy':[x0,y0,x1,y1],'resampling':'nearest-neighbour','left':'LOD0','right':'LOD3'}
        pairs.append(rec)
    actual=set(byid)
    result={'status':'COMPLETE_OFFLINE_EVIDENCE' if actual==expected and all(x['current'] and x['captured_before_render'] for x in bindings) else 'PARTIAL_OR_STALE',
            'expected_frames':len(expected),'actual_frames':len(records),'missing':sorted(expected-actual),'unexpected':sorted(actual-expected),
            'settings':CONFIG,'settings_sha256':CONFIG_SHA,'frames':records,'comparisons':pairs,'bindings':bindings,
            'all_current':all(x['current'] and x['captured_before_render'] for x in bindings),
            'limits':['Offline source renders only; no Unreal import/HLOD/streaming/lighting validation.','Close views can crop; fitted hero views show whole assets.','4000m pixel coverage is resolution and FOV limited; magnified crops are labelled.','Geometry-only holdout-ground coverage excludes skirts and cast shadows. Soil-ground frames are appearance previews, not coverage masks.']}
    (REPORT/'distance_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    rows=['<!doctype html><html lang="en"><meta charset="utf-8"><title>Young strawberry beds — distance review</title><style>body{background:#202522;color:#e9ece6;font:16px/1.5 system-ui;margin:28px}a{color:#c6d9a4}img{max-width:100%;background:#808080}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}details{margin:24px 0}td,th{padding:8px;text-align:left;border-bottom:1px solid #53604c}</style><h1>Young strawberry beds · fixed-distance review</h1><p>Original 1920 × 1080 frames. Singles: 85° horizontal FOV and 45° elevation; 10-row block: 110° FOV and 70° elevation. Camera-to-target distances are exact; no auto-framing at distance. Left detailed / right authored lowest. Ground-masked alpha excludes the hidden skirt. Soil-ground previews below show actual contact on a 3% slope. The whole block fits at 15 m; the 1 m single views intentionally crop for local detail.</p>']
    rows.append('<table><tr><th>Case</th><th>Detailed area px</th><th>Lowest area px</th><th>Lowest lit sRGB</th></tr>')
    for p in pairs:
        r=byid[p['LOD0_frame']];b=byid[p['LOD3_frame']]
        rows.append(f"<tr><td>{p['id']}</td><td>{r['metrics']['equivalent_opaque_pixels']:.2f}</td><td>{b['metrics']['equivalent_opaque_pixels']:.2f}</td><td>{b['metrics']['alpha_weighted_lit_srgb']}</td></tr>")
    rows.append('</table>')
    for p in pairs:
        rows.append(f"<details><summary>{p['id']} · area ratio {p['lowest_area_ratio']:.3f} · luma change {p['lowest_minus_detailed_luma']:+.2f}</summary><div class='pair'><a href='{p['LOD0_frame']}.png'><img loading='lazy' src='{p['LOD0_frame']}.png'></a><a href='{p['LOD3_frame']}.png'><img loading='lazy' src='{p['LOD3_frame']}.png'></a></div>")
        if p['review_flags']:rows.append('<p>Review: '+html.escape(', '.join(p['review_flags']))+'</p>')
        if 'magnified' in p:
            m=p['magnified'];rows.append(f"<p>MAGNIFIED {m['factor']}× · detailed left / lowest right</p><img loading='lazy' src='{Path(m['file']).name}'>")
        rows.append('</details>')
    rows.append('<h2>Ground contact · 1.7 m row centres · 3% slope</h2>')
    for d in (15,60,150,500):
        rows.append(f"<h3>{d} m</h3><div class='pair'><a href='field_3pct_{d}m_LOD0.png'><img loading='lazy' src='field_3pct_{d}m_LOD0.png'></a><a href='field_3pct_{d}m_LOD3.png'><img loading='lazy' src='field_3pct_{d}m_LOD3.png'></a></div>")
    rows.append('<h2>Variant seams</h2><img src="seams_ABC_grazing_LOD0.png"><img src="seams_ABC_top_LOD0.png"><p><a href="../../Reports/distance_validation.json">Measurements, source hashes and exact cameras</a></p></html>')
    (OUT/'INDEX.html').write_text(''.join(rows),encoding='utf-8')
    print('DISTANCE_REPORT',result['status'],len(records),'frames',len(pairs),'pairs',flush=True)

if args.mode=='report':report()
else:run()
