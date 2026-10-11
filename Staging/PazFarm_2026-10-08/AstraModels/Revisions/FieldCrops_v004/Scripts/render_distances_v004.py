"""Offline, fixed-camera source appearance evidence. Never saves source scenes."""
import sys,argparse,random,html
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from distance_core import *

ap=argparse.ArgumentParser()
ap.add_argument('--family',choices=['vines','olives','grass','references','all','report'],default='all')
ap.add_argument('--distances',nargs='*',type=float)
ap.add_argument('--variants',nargs='*')
ap.add_argument('--resume',action='store_true')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=ROOT/'Previews/Distance'; REPORT=ROOT/'Reports'; CACHE=ROOT/'Temp/DistanceCache'
for p in (OUT,REPORT,CACHE):p.mkdir(parents=True,exist_ok=True)
SOURCES={'vines':'VineRows.blend','olives':'Olive.blend','grass':'FieldGrass.blend'}
ALL=[]

def cached_image(rec):
    p=CACHE/(rec['png_sha256']+'.npy')
    if p.exists():return np.load(p)
    img=png_read(ROOT/rec['file']);np.save(p,img);return img

def render_case(scene,cam,objects,family,variant,lod,arrangement,target,distance,elevation,source,source_hash,textures,top=False):
    if args.distances and not top and distance not in args.distances:return
    tag='top' if top else f'{distance:g}m'
    name=f'{family}_{variant}_{arrangement}_{tag}_{lod}'
    file=OUT/(name+'.png');meta=OUT/(name+'.json')
    if args.resume and file.exists() and meta.exists():
        rec=json.loads(meta.read_text())
        if rec.get('source_blend_sha256')==source_hash and rec.get('source_texture_sha256')==textures and rec.get('settings_sha256')==SETTINGS_SHA and rec.get('png_sha256')==sha(file):
            ALL.append(rec);print('RESUME',name,flush=True);return
    for o in scene.objects:
        if o.type=='MESH':o.hide_render=True
    for o in objects:o.hide_render=False
    position_camera(cam,target,distance,elevation,top)
    scene.render.filepath=str(file)
    started=time.monotonic();bpy.ops.render.render(write_still=True)
    img=png_read(file);measure=metrics(img);digest=sha(file)
    np.save(CACHE/(digest+'.npy'),img)
    rec={'id':name,'file':file.relative_to(ROOT).as_posix(),'family':family,'variant':variant,'lod':lod,
         'arrangement':arrangement,'view':'top' if top else 'perspective','requested_distance_m':distance,
         'actual_target_distance_m':round((cam.location-Vector(target)).length,6),'target_m':rounded(target),
         'camera_position_m':rounded(cam.location),'camera_rotation_xyz_deg':rounded([math.degrees(x) for x in cam.rotation_euler]),
         'camera_elevation_deg':90 if top else elevation,'horizontal_fov_deg':60,'lens_mm':round(cam.data.lens,6),
         'resolution_px':[1920,1080],'object_count':len(objects),'object_names':[o.name for o in objects],
         'world_bounds_m':bbox_world(objects),'projected_bounds':projected_bounds(scene,cam,objects),
         'metrics':measure,'close_crop_expected':distance in (2,5),'render_seconds':round(time.monotonic()-started,3),
         'settings_sha256':SETTINGS_SHA,'source_blend':str(source.resolve()),'source_blend_sha256':source_hash,
         'source_texture_sha256':textures,'texture_hash_capture':'before render','png_sha256':digest}
    if family in ('olives','references') and not top:
        b=bbox_world(objects);z=b[0][2]+(b[1][2]-b[0][2])*.55
        projected=world_to_camera_view(scene,cam,Vector((0,0,z)))
        cutoff=int(np.clip((1-projected.y)*1080,0,1080));cropped=img.copy();cropped[cutoff:,:,3]=0
        rec['upper_crown_region']={'method':'screen region above projection of trunk-axis point at 55% height; not material ID','image_y_cutoff_px':cutoff,'metrics':metrics(cropped)}
    meta.write_text(json.dumps(rec,indent=2)+'\n');ALL.append(rec)
    (REPORT/f'distance_{family}_progress.json').write_text(json.dumps({'settings':SETTINGS,'frames':ALL},indent=2)+'\n')
    print('DISTANCE_DONE',name,json.dumps(measure),flush=True)

def clone(scene,model,name,position,angle=0):
    o=model.copy();o.data=model.data;o.name=name;scene.collection.objects.link(o)
    o.location=Vector(position);o.rotation_euler=(0,0,angle);o.hide_render=True
    return o

def family_render(family):
    source=ROOT/'Blend'/SOURCES[family];digest=sha(source)
    bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
    scene,cam=configure_scene();textures=loaded_texture_hashes()
    prefix={'vines':'SM_PazFarm_VineRow_3m_','olives':'SM_PazFarm_Olive_','grass':'SM_PazFarm_Grass'}[family]
    variants={'vines':['A','B','C'],'olives':['A','B','C','Young'],'grass':['Clump_'+x for x in 'ABCDEF']+['Patch_2m_A','Patch_2m_B']}[family]
    distances={'vines':[2,30,150,500],'olives':[5,50,100,300,1000],'grass':[2,15,50,150]}[family]
    for variant in variants:
        if args.variants and variant not in args.variants:continue
        obj=bpy.data.objects[prefix+variant];lo=bpy.data.objects[prefix+variant+'_LOD3']
        b=bbox_world([obj]);h=b[1][2]-b[0][2]
        target=(0,1.5,h*.52) if family=='vines' else (0,0,h*.5)
        elevation={'vines':22,'olives':12,'grass':28}[family]
        for distance in distances:
            for lod,model in [('LOD0',obj),('LOD3',lo)]:
                render_case(scene,cam,[model],family,variant,lod,'single',target,distance,elevation,source,digest,textures)
        if family=='olives' and not args.distances:
            topdist=round(max(b[1][0]-b[0][0],b[1][1]-b[0][1])*2.5,3)
            for lod,model in [('LOD0',obj),('LOD3',lo)]:
                render_case(scene,cam,[model],family,variant,lod,'single',target,topdist,90,source,digest,textures,True)
    if family in ('vines','grass') and not args.variants:
        groups={}
        placements=[]
        if family=='vines':
            arrangement='block_5x10';target=(0,15,1.05)
            for row in range(5):
                for tile in range(10):placements.append((variants[(row+tile)%3],((row-2)*2.75,tile*3,0),0))
        else:
            arrangement='scatter_10x10m';target=(0,0,.3);rng=random.Random(4004)
            for row in range(10):
                for col in range(10):
                    variant=rng.choices(variants[:6],weights=[2,2,2,2,1,1])[0]
                    placements.append((variant,(col-4.5+rng.uniform(-.08,.08),row-4.5+rng.uniform(-.08,.08),0),rng.uniform(0,math.tau)))
            for i,(x,y) in enumerate([(-2.5,-2.5),(2.5,-2.5),(-2.5,2.5),(2.5,2.5)]):
                placements.append((variants[6+i%2],(x,y,0),0))
        for lod in ('LOD0','LOD3'):
            groups[lod]=[clone(scene,bpy.data.objects[prefix+v+('_LOD3' if lod=='LOD3' else '')],f'{arrangement}_{lod}_{i}',pos,angle) for i,(v,pos,angle) in enumerate(placements)]
        bpy.context.view_layer.update()
        for distance in distances:
            for lod in ('LOD0','LOD3'):
                render_case(scene,cam,groups[lod],family,'mixed',lod,arrangement,target,distance,28,source,digest,textures)
        (REPORT/f'{family}_preview_placements.json').write_text(json.dumps({'arrangement':arrangement,'placements':[{'variant':v,'position_m':pos,'z_rotation_rad':angle} for v,pos,angle in placements],'native_placement':False},indent=2)+'\n')
    assert sha(source)==digest,'Source changed during render'
    assert loaded_texture_hashes()==textures,'Texture changed during render'

def references():
    old=ROOT.parent/'VisualFix_v002'
    for family,name in [('Lemon','SM_PazFarm_Lemon_A'),('Avocado','SM_PazFarm_Avocado_A')]:
        source=old/'Blend'/(family+'.blend');digest=sha(source)
        bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);scene,cam=configure_scene()
        textures=loaded_texture_hashes();obj=bpy.data.objects[name];b=bbox_world([obj])
        render_case(scene,cam,[obj],'references',family,'LOD0','single',(0,0,(b[0][2]+b[1][2])*.5),100,12,source,digest,textures)
        assert sha(source)==digest and loaded_texture_hashes()==textures

def report():
    records=[];hashes={}
    expected_ids=set()
    for family,variants,distances in [('vines',list('ABC'),[2,30,150,500]),('olives',['A','B','C','Young'],[5,50,100,300,1000]),('grass',['Clump_'+v for v in 'ABCDEF']+['Patch_2m_A','Patch_2m_B'],[2,15,50,150])]:
        for v in variants:
            for d in distances:
                for lod in ('LOD0','LOD3'):expected_ids.add(f'{family}_{v}_single_{d}m_{lod}')
            if family=='olives':
                for lod in ('LOD0','LOD3'):expected_ids.add(f'olives_{v}_single_top_{lod}')
        if family!='olives':
            arrangement='block_5x10' if family=='vines' else 'scatter_10x10m'
            for d in distances:
                for lod in ('LOD0','LOD3'):expected_ids.add(f'{family}_mixed_{arrangement}_{d}m_{lod}')
    for v in ('Lemon','Avocado'):expected_ids.add(f'references_{v}_single_100m_LOD0')
    assert len(expected_ids)==154
    def current(p):
        p=str(p)
        if p not in hashes:hashes[p]=sha(p) if Path(p).is_file() else None
        return hashes[p]
    for p in OUT.glob('*.json'):
        r=json.loads(p.read_text())
        if r.get('settings_sha256')==SETTINGS_SHA and (ROOT/r['file']).is_file():records.append(r)
    records.sort(key=lambda r:(r['family'],r['variant'],r['arrangement'],r['view'],r['requested_distance_m'],r['lod']))
    bindings=[{'frame':r['id'],'current':current(r['source_blend'])==r['source_blend_sha256'] and bool(r.get('source_texture_sha256')) and all(current(p)==h for p,h in r['source_texture_sha256'].items()) and current(ROOT/r['file'])==r['png_sha256'],'texture_hashes_captured_before_render':r.get('texture_hash_capture')=='before render'} for r in records]
    grouped={};pairs=[]
    for r in records:grouped.setdefault((r['family'],r['variant'],r['arrangement'],r['view'],r['requested_distance_m']),{})[r['lod']]=r
    for key,p in grouped.items():
        if not all(x in p for x in ('LOD0','LOD3')):continue
        a,b=cached_image(p['LOD0']),cached_image(p['LOD3']);aa=a[...,3].astype(float)/255;bb=b[...,3].astype(float)/255
        m0,m3=p['LOD0']['metrics'],p['LOD3']['metrics']
        rec={'key':list(key),'LOD0_frame':p['LOD0']['id'],'LOD3_frame':p['LOD3']['id'],
             'alpha_weighted_silhouette_iou':round(float(np.minimum(aa,bb).sum()/max(np.maximum(aa,bb).sum(),1e-12)),5),
             'LOD3_over_LOD0_opaque_area_ratio':round(m3['equivalent_opaque_pixels']/max(m0['equivalent_opaque_pixels'],1e-12),5),
             'LOD3_minus_LOD0_lit_srgb':rounded(np.asarray(m3['alpha_weighted_lit_srgb'])-m0['alpha_weighted_lit_srgb'],3),
             'LOD3_minus_LOD0_luma_code_value':round(m3['alpha_weighted_luma_code_value']-m0['alpha_weighted_luma_code_value'],3),
             'both_visible':m0['equivalent_opaque_pixels']>0 and m3['equivalent_opaque_pixels']>0,
             'close_crop':p['LOD0']['close_crop_expected'] or m0['clipped_at_image_border'] or m3['clipped_at_image_border']}
        flags=[]
        if not rec['both_visible']:flags.append('zero geometry coverage')
        if not rec['close_crop']:
            if not .65<=rec['LOD3_over_LOD0_opaque_area_ratio']<=1.45:flags.append('area ratio outside 0.65..1.45')
            if rec['alpha_weighted_silhouette_iou']<.55:flags.append('silhouette IoU below 0.55')
            if rec['LOD3_minus_LOD0_luma_code_value']>10:flags.append('LOD3 more than 10 luma values brighter')
            if max(abs(x) for x in rec['LOD3_minus_LOD0_lit_srgb'])>18:flags.append('RGB channel difference exceeds 18')
        rec['review_flags']=flags
        if key[3]!='top' and key[4]>=50:
            yy,xx=np.nonzero((aa>0)|(bb>0))
            if len(xx):
                x0,x1=max(0,int(xx.min())-5),min(1920,int(xx.max())+6);y0,y1=max(0,int(yy.min())-5),min(1080,int(yy.max())+6)
                factor=max(1,min(16,450//max(x1-x0,y1-y0)))
                ca=np.repeat(np.repeat(a[y0:y1,x0:x1],factor,0),factor,1);cb=np.repeat(np.repeat(b[y0:y1,x0:x1],factor,0),factor,1)
                pair=np.zeros((ca.shape[0],ca.shape[1]*2+12,4),np.uint8);pair[:,:ca.shape[1]]=ca;pair[:,ca.shape[1]+12:]=cb
                mp=OUT/f"MAGNIFIED_{p['LOD0']['id'].replace('_LOD0','')}_{factor}x.png";png_write(mp,diagnostic_background(pair))
                rec['magnified_comparison']={'file':mp.relative_to(ROOT).as_posix(),'scale_factor':factor,'source_crop_xyxy':[x0,y0,x1,y1],'left':'LOD0','right':'LOD3','resampling':'nearest-neighbour; diagnostic crop'}
        pairs.append(rec)
    actual_ids={r['id'] for r in records}
    result={'status':'COMPLETE_OFFLINE_EVIDENCE' if actual_ids==expected_ids and all(b['current'] for b in bindings) else 'PARTIAL_OR_STALE',
            'expected_frames':154,'actual_frames':len(records),'settings':SETTINGS,'settings_sha256':SETTINGS_SHA,
            'missing_frames':sorted(expected_ids-actual_ids),'unexpected_frames':sorted(actual_ids-expected_ids),
            'frames':records,'lod_comparisons':pairs,'source_bindings':bindings,'all_frame_source_bindings_current':all(b['current'] and b['texture_hashes_captured_before_render'] for b in bindings),
            'review_pair_count':sum(bool(p['review_flags']) for p in pairs),
            'limits':['Blender source render evidence only. No Unreal, Nanite, HLOD, streaming or native acceptance verified.','Close fixed-distance frames may crop; fitted hero previews show complete assets.','Magnified crops are labeled. Original 1920x1080 frames are retained.','Single small clumps have limited pixel coverage at distance. Scatter evidence is essential.','Review bands are diagnostics, not automatic visual acceptance.']}
    (REPORT/'distance_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    rows=['<!doctype html><html lang="en"><meta charset="utf-8"><title>FieldCrops v004 distance evidence</title><style>body{background:#202427;color:#e4e8e7;font:15px system-ui;margin:24px}a{color:#9cd9ff}img{max-width:100%;background:#808080}details{margin:20px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}td,th{padding:5px;text-align:left;border-bottom:1px solid #45505a}</style><h1>FieldCrops v004 — fixed-distance comparisons</h1><p>1920 × 1080; 60° horizontal field of view; Cycles 16 samples, no denoising; fixed lighting/exposure. Transparent alpha contains geometry only. Distances are camera-to-target slant distances. Full frames are never auto-framed. Close views can crop. All evidence is offline Blender only.</p><p>Magnified crops below have LOD0 left and authored LOD3 right. Open full frames for actual pixel size.</p>']
    rows.append('<table><tr><th>Frame</th><th>Geometry area px</th><th>Lit sRGB</th></tr>')
    for r in records:rows.append(f"<tr><td><a href='{Path(r['file']).name}'>{r['id']}</a></td><td>{r['metrics']['equivalent_opaque_pixels']:.3f}</td><td>{r['metrics']['alpha_weighted_lit_srgb']}</td></tr>")
    rows.append('</table>')
    for p in pairs:
        rows.append(f"<details><summary>{p['LOD0_frame'].replace('_LOD0','')} — area ratio {p['LOD3_over_LOD0_opaque_area_ratio']:.3f}; alpha IoU {p['alpha_weighted_silhouette_iou']:.3f}; luma change {p['LOD3_minus_LOD0_luma_code_value']:+.2f}</summary><div class='pair'><a href='{p['LOD0_frame']}.png'><img loading='lazy' src='{p['LOD0_frame']}.png'></a><a href='{p['LOD3_frame']}.png'><img loading='lazy' src='{p['LOD3_frame']}.png'></a></div>")
        if p['review_flags']:rows.append('<p>Review flags: '+html.escape('; '.join(p['review_flags']))+'</p>')
        if 'magnified_comparison' in p:
            m=p['magnified_comparison'];rows.append(f"<p>MAGNIFIED {m['scale_factor']}×; LOD0 left / LOD3 right</p><img loading='lazy' src='{Path(m['file']).name}'>")
        rows.append('</details>')
    comparisons=[]
    selected=[r for r in records if r['requested_distance_m']==100 and r['view']=='perspective' and ((r['family']=='olives' and r['variant']=='A') or r['family']=='references')]
    if len(selected)==4:
        rows.append('<h2>Olive versus earlier citrus and avocado — 100 m</h2><p>Every crop below uses the same 160 × 160 source-pixel window and 4× nearest-neighbour magnification. Models retain their actual sizes; no silhouette is resized to match another.</p>')
        for r in selected:
            img=cached_image(r);crop=np.repeat(np.repeat(img[460:620,880:1040],4,0),4,1)
            path=OUT/('COMPARE100_'+r['id']+'_4x.png');png_write(path,diagnostic_background(crop))
            cm=r['upper_crown_region']['metrics'];rgb=cm['alpha_weighted_lit_srgb'];sat=(max(rgb)-min(rgb))/max(max(rgb),1e-12)
            comparisons.append({'frame':r['id'],'magnified_file':path.relative_to(ROOT).as_posix(),'upper_crown_lit_srgb':rgb,'saturation_of_mean_rgb':round(sat,5),'source_crop_xyxy':[880,460,1040,620],'magnification':4})
            rows.append(f"<h3>{r['id']}</h3><img loading='lazy' src='{path.name}'>")
        writeup={'method':'Same 100 m camera/FOV/light; actual model scale; alpha-weighted upper-crown screen-region proxy. Saturation of mean RGB is descriptive, not species recognition.','frames':comparisons}
        (REPORT/'olive_citrus_comparison.json').write_text(json.dumps(writeup,indent=2)+'\n')
    rows.append('<p><a href="../../Reports/distance_validation.json">Measured metrics, source hashes and camera transforms</a></p></html>')
    (OUT/'INDEX.html').write_text(''.join(rows),encoding='utf-8')
    byid={r['id']:r for r in records}
    notes=['# FieldCrops v004 — distance evidence','',f"{len(records)} / 154 fixed-camera frames; {len(pairs)} matched LOD pairs.",'',
           '1920 × 1080 perspective, 60° horizontal field of view, Cycles CPU 16 samples, no denoising or adaptive sampling. Standard sRGB view, exposure 0. Geometry-only transparent alpha excludes ground and cast shadows. Each distance is measured from the camera to the declared target, with no far auto-framing. Full camera transforms and source/texture hashes are recorded per frame.','',
           'The separate fitted hero views show the complete models. Close fixed-distance views may crop, especially the 2 m block/scatter and 5 m mature trees. Magnified pixel crops are labelled and do not replace full-resolution evidence.','',
           '| Model / arrangement | Distance | LOD0 area px | Lowest area px | Alpha IoU | Lowest luma change |','|---|---:|---:|---:|---:|---:|']
    for p in pairs:
        k=p['key']
        if k[3]=='top' or k[4] not in (150,300,500,1000):continue
        m0=byid[p['LOD0_frame']]['metrics'];m3=byid[p['LOD3_frame']]['metrics']
        notes.append(f"| {k[0]} {k[1]} {k[2]} | {k[4]} m | {m0['equivalent_opaque_pixels']:.2f} | {m3['equivalent_opaque_pixels']:.2f} | {p['alpha_weighted_silhouette_iou']:.3f} | {p['LOD3_minus_LOD0_luma_code_value']:+.2f} |")
    notes+=['','Area is alpha-weighted equivalent opaque pixels. Lit colour is measured from actual PNG bytes, weighted by geometry alpha. Comparison flags use deliberately simple review bands: area ratio 0.65–1.45, alpha IoU at least 0.55, lowest-LOD brightening at most 10 luma code values and absolute RGB channel difference at most 18. Cropped views are informational. See VISUAL_REVIEW.json for the outcome and interpretation of flagged pairs. These bands are not user acceptance criteria.','',
            'Single small grass clumps become only a few pixels at 150 m; scatter coverage matters more there. No geometry can guarantee visibility at every raster resolution/FOV. This suite verifies source appearance in Blender. Unreal material construction, anti-aliasing, HLOD selection, streaming, native distance appearance and save/reopen remain untested.']
    (REPORT/'distance_notes.md').write_text('\n'.join(notes)+'\n',encoding='utf-8')
    print('REPORT',result['status'],len(records),'frames',len(pairs),'pairs',result['review_pair_count'],'flagged',flush=True)

if args.family in SOURCES:family_render(args.family)
elif args.family=='references':references()
elif args.family=='all':
    for family in SOURCES:family_render(family)
    references()
if args.family=='report':report()
