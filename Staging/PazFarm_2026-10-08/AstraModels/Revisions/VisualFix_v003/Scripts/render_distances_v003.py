"""Blender-only, fixed-camera distance evidence for VisualFix_v003.

Usage: blender --background --factory-startup --python render_distances_v003.py
       -- --family pines|strawberry|all [--resume] [--limit N]

Reads model .blend sources and never saves them. Writes only Previews/Distance/
and Reports/distance*. Transparent film excludes ground and shadows from the
measured silhouette. PNG values are decoded directly for displayed sRGB metrics.
"""
import bpy, sys, os, math, json, hashlib, struct, zlib, binascii, time, argparse
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import numpy as np

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Previews' / 'Distance'
REPORT = ROOT / 'Reports'
OUT.mkdir(parents=True, exist_ok=True)
os.environ['TEMP'] = os.environ['TMP'] = str(ROOT / 'Temp')
parser = argparse.ArgumentParser()
parser.add_argument('--family', choices=['pines','strawberry','all'], default='all')
parser.add_argument('--resume', action='store_true')
parser.add_argument('--limit', type=int, default=0)
parser.add_argument('--variants', default='ABC', help='Pine diagnostic subset, e.g. A')
parser.add_argument('--only-distances', default='', help='Diagnostic subset in metres, e.g. 300,1000; excludes top views')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])

SETTINGS = {
    'engine':'CYCLES', 'samples':32, 'adaptive_sampling':False, 'denoising':False,
    'resolution_px':[1920,1080], 'horizontal_fov_deg':60.0,
    'camera_type':'PERSP', 'camera_clip_m':[0.01,10000],
    'view_transform':'Standard', 'look':'None', 'exposure_stops':0.0, 'gamma':1.0,
    'world_color_linear':[0.65,0.70,0.78], 'world_strength':0.35,
    'sun_energy':2.0, 'sun_rotation_xyz_deg':[35,-25,-40], 'sun_angle_deg':5.0,
    'transparent_film':True, 'render_ground':False, 'shadows_in_mask':False,
    'azimuth_deg':-55.0, 'pine_elevation_deg':12.0, 'bed_elevation_deg':35.0,
    'distance_definition':'Euclidean camera-to-declared-target slant distance in metres',
    'samples_seed':1977, 'threads':4,
    'png':'RGBA8 display sRGB; original unrescaled 1920x1080 evidence',
    'pines_distances_m':[5,50,300,1000], 'pine_LOD3_stress_m':4000,
    'beds_distances_m':[2,30,60,150,500],
    'ten_tile_layout':{'rows':5,'row_pitch_m':5.48,'tiles_per_row':2,'tile_length_m':4.0,'positions':'x=(row-2)*5.48, y=0 or 4, z=0; no extra scaling'},
}
SETTINGS_SHA = hashlib.sha256(json.dumps(SETTINGS,sort_keys=True).encode()).hexdigest()

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rounded(seq, n=6): return [round(float(v),n) for v in seq]

def png_read(path):
    """Read actual PNG display bytes, avoiding Blender alpha-mode ambiguity."""
    raw=Path(path).read_bytes(); assert raw[:8]==b'\x89PNG\r\n\x1a\n'
    pos=8; chunks=[]
    while pos<len(raw):
        length=struct.unpack('!I',raw[pos:pos+4])[0]
        typ=raw[pos+4:pos+8]; d=raw[pos+8:pos+8+length]; pos+=length+12
        if typ==b'IHDR': w,h,depth,ctype,_,_,interlace=struct.unpack('!2I5B',d)
        if typ==b'IDAT': chunks.append(d)
    assert depth==8 and ctype in (2,6) and interlace==0,(path,depth,ctype,interlace)
    bpp=4 if ctype==6 else 3; step=w*bpp
    data=np.frombuffer(zlib.decompress(b''.join(chunks)),np.uint8).reshape(h,step+1)
    out=np.zeros((h,step),np.uint8)
    for y in range(h):
        f=int(data[y,0]); row=data[y,1:].astype(np.int32)
        prev=out[y-1].astype(np.int32) if y else np.zeros(step,np.int32)
        if f==1:
            for k in range(bpp): row[k::bpp]=np.cumsum(row[k::bpp])&255
        elif f==2: row=(row+prev)&255
        elif f in (3,4):
            for x in range(step):
                a=int(row[x-bpp]) if x>=bpp else 0; b=int(prev[x]); c=int(prev[x-bpp]) if x>=bpp else 0
                if f==3: v=(a+b)//2
                else:
                    p=a+b-c; pa,pb,pc=abs(p-a),abs(p-b),abs(p-c)
                    v=a if pa<=pb and pa<=pc else (b if pb<=pc else c)
                row[x]=(int(row[x])+v)&255
        else: assert f==0,(path,f)
        out[y]=row
    return out.reshape(h,w,bpp)

def png_write(path,img):
    img=np.asarray(img,np.uint8);h,w=img.shape[:2]
    def chunk(t,d): return struct.pack('!I',len(d))+t+d+struct.pack('!I',binascii.crc32(t+d)&0xffffffff)
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,6 if img.shape[2]==4 else 2,0,0,0))+chunk(b'sRGB',b'\0')+chunk(b'IDAT',zlib.compress(b''.join(b'\0'+r.tobytes() for r in img),6))+chunk(b'IEND',b'')
    path.write_bytes(data)

def diagnostic_background(rgba):
    """Neutral viewing background for magnified crops only, never metrics."""
    a=rgba[...,3:4].astype(np.float32)/255
    return np.rint(rgba[...,:3]*a+128*(1-a)).astype(np.uint8)

def metrics(img):
    assert img.shape==(1080,1920,4),img.shape
    alpha=img[...,3].astype(np.float64)/255
    rgb=img[...,:3].astype(np.float64)
    visible=alpha>.1
    yy,xx=np.nonzero(visible)
    sum_alpha=float(alpha.sum())
    weighted=(rgb*alpha[...,None]).sum(axis=(0,1))/max(sum_alpha,1e-12)
    green=(rgb[...,1]>rgb[...,0]*1.04)&(rgb[...,1]>rgb[...,2]*1.02)
    clipping=bool(np.any(visible[0]) or np.any(visible[-1]) or np.any(visible[:,0]) or np.any(visible[:,-1]))
    high=alpha>.9
    return {
      'equivalent_opaque_pixels':round(sum_alpha,4),
      'alpha_nonzero_pixels':int(np.sum(alpha>0)),
      'alpha_gt_0_1_pixels':int(visible.sum()),'alpha_gt_0_9_pixels':int(high.sum()),
      'bbox_alpha_gt_0_1_px':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)] if len(xx) else None,
      'bbox_size_px':[int(xx.max()+1-xx.min()),int(yy.max()+1-yy.min())] if len(xx) else [0,0],
      'alpha_weighted_lit_srgb':rounded(weighted,3),
      'alpha_weighted_luma_code_value':round(float(np.dot(weighted,[.2126,.7152,.0722])),3),
      'weighted_green_fraction':round(float(alpha[green].sum())/max(sum_alpha,1e-12),5),
      'high_coverage_lit_srgb':rounded(rgb[high].mean(0),3) if high.any() else None,
      'clipped_at_image_border':clipping,
      'background_alpha_zero_pixels':int(np.sum(alpha==0)),
    }

def bbox_world(objects):
    pts=[o.matrix_world@Vector(p) for o in objects for p in o.bound_box]
    return [[min(v[k] for v in pts) for k in range(3)],[max(v[k] for v in pts) for k in range(3)]]

def configure_scene():
    s=bpy.context.scene
    # This only alters the transient render session, never the source .blend.
    for o in s.objects:o.hide_render=True
    for o in list(s.objects):
        if o.type in ('CAMERA','LIGHT'):bpy.data.objects.remove(o,do_unlink=True)
    s.unit_settings.system='METRIC'; s.unit_settings.scale_length=1
    s.render.engine='CYCLES';s.cycles.device='CPU'
    s.cycles.samples=SETTINGS['samples'];s.cycles.use_denoising=False
    s.cycles.use_adaptive_sampling=False;s.cycles.seed=SETTINGS['samples_seed']
    s.cycles.use_animated_seed=False
    s.cycles.max_bounces=4;s.cycles.diffuse_bounces=2;s.cycles.glossy_bounces=2
    s.cycles.transmission_bounces=1;s.cycles.transparent_max_bounces=8
    s.render.threads_mode='FIXED';s.render.threads=SETTINGS['threads']
    s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
    s.render.pixel_aspect_x=s.render.pixel_aspect_y=1
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.color_depth='8'
    s.render.image_settings.compression=15;s.render.film_transparent=True
    s.render.use_border=False;s.render.use_crop_to_border=False
    if hasattr(s.render,'use_motion_blur'):s.render.use_motion_blur=False
    s.use_nodes=False
    s.world=bpy.data.worlds.new('Distance_Fixed_World');s.world.use_nodes=True
    bg=s.world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value=(*SETTINGS['world_color_linear'],1)
    bg.inputs['Strength'].default_value=SETTINGS['world_strength']
    s.view_settings.view_transform='Standard'
    try:s.view_settings.look='None'
    except TypeError:pass
    s.view_settings.exposure=0;s.view_settings.gamma=1
    s.display_settings.display_device='sRGB'
    bpy.ops.object.light_add(type='SUN')
    sun=bpy.context.object;sun.name='Distance_Fixed_Sun';sun.hide_render=False
    sun.data.energy=SETTINGS['sun_energy'];sun.data.angle=math.radians(SETTINGS['sun_angle_deg'])
    sun.rotation_euler=tuple(math.radians(d) for d in SETTINGS['sun_rotation_xyz_deg'])
    bpy.ops.object.camera_add()
    cam=bpy.context.object;cam.name='Distance_Fixed_Camera';cam.data.type='PERSP'
    cam.data.sensor_fit='HORIZONTAL';cam.data.sensor_width=36
    cam.data.lens=36/(2*math.tan(math.radians(SETTINGS['horizontal_fov_deg'])/2))
    cam.data.clip_start=.01;cam.data.clip_end=10000
    cam.data.dof.use_dof=False;s.camera=cam
    bpy.context.preferences.filepaths.temporary_directory=str(ROOT/'Temp')
    return s,cam

def position_camera(cam,target,distance,elevation,top=False):
    target=Vector(target)
    if top:
        direction=Vector((0,0,1))
    else:
        az,el=math.radians(SETTINGS['azimuth_deg']),math.radians(elevation)
        direction=Vector((math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),math.sin(el)))
    cam.location=target+direction*distance
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()
    assert abs((cam.location-target).length-distance)<max(.0001,distance*.000001)

def projected_bounds(scene,cam,objects):
    coords=[world_to_camera_view(scene,cam,o.matrix_world@Vector(p)) for o in objects for p in o.bound_box]
    front=[v for v in coords if v.z>0]
    if not front:return None
    xs=[v.x*1920 for v in front];ys=[(1-v.y)*1080 for v in front]
    return {'bounds_xyxy_unclipped_px':rounded([min(xs),min(ys),max(xs),max(ys)],3),
            'bounding_box_projection_size_px':rounded([max(xs)-min(xs),max(ys)-min(ys)],3),
            'some_bound_corners_behind_camera':len(front)!=len(coords),
            'note':'Projected 3D bounding-box corners, not measured raster silhouette.'}

ALL=[]; rendered=0
SOURCE_TEXTURES={}
def loaded_texture_hashes():
    result={}
    for im in bpy.data.images:
        if im.source=='FILE' and im.filepath:
            p=Path(bpy.path.abspath(im.filepath))
            if p.is_file():result[str(p.resolve())]=sha(p)
    return result

def render_case(scene,cam,objects,base,variant,lod,arrangement,target,distance,elevation,source_hash,top=False):
    global rendered
    if args.only_distances and (top or distance not in [float(v) for v in args.only_distances.split(',')]):return
    name=f'{base}_{lod}_{arrangement}_{"top" if top else str(distance).replace(".","p")+"m"}'
    file=OUT/(name+'.png');meta=OUT/(name+'.json')
    if args.resume and file.exists() and meta.exists():
        old=json.loads(meta.read_text())
        if old.get('source_blend_sha256')==source_hash and old.get('settings_sha256')==SETTINGS_SHA and old.get('png_sha256')==sha(file) and old.get('source_texture_sha256')==SOURCE_TEXTURES and 'texture_hash_capture' not in old:
            ALL.append(old);print('DISTANCE_RESUME',name,flush=True);return
    if args.limit and rendered>=args.limit:return
    for o in scene.objects:
        if o.type=='MESH':o.hide_render=True
    for o in objects:o.hide_render=False
    position_camera(cam,target,distance,elevation,top)
    proj=projected_bounds(scene,cam,objects)
    scene.render.filepath=str(file)
    started=time.monotonic();bpy.ops.render.render(write_still=True)
    elapsed=time.monotonic()-started
    image=png_read(file);measure=metrics(image)
    rec={'id':name,'file':file.relative_to(ROOT).as_posix(),'family':'pines' if base.startswith('Pine') else 'strawberry',
      'variant':variant,'lod':lod,'arrangement':arrangement,'view':'top' if top else 'perspective',
      'requested_distance_m':distance,'actual_target_distance_m':round((cam.location-Vector(target)).length,6),
      'target_m':rounded(target),'camera_position_m':rounded(cam.location),
      'camera_rotation_xyz_deg':rounded([math.degrees(d) for d in cam.rotation_euler]),
      'camera_elevation_deg':90 if top else elevation,'camera_azimuth_deg':None if top else SETTINGS['azimuth_deg'],
      'horizontal_fov_deg':SETTINGS['horizontal_fov_deg'],'lens_mm':round(cam.data.lens,6),
      'resolution_px':[1920,1080],'object_count':len(objects),'object_names':[o.name for o in objects],
      'world_bounds_m':bbox_world(objects),'projected_bounds':proj,'metrics':measure,
      'close_crop_expected':distance in (2,5),'render_seconds':round(elapsed,3),
      'settings_sha256':SETTINGS_SHA,'source_blend_sha256':source_hash,'png_sha256':sha(file)}
    rec['source_texture_sha256']=SOURCE_TEXTURES
    if base.startswith('Pine') and not top:
        b=bbox_world(objects);h=b[1][2]-b[0][2]
        crown_z=b[0][2]+h*.55
        projected=world_to_camera_view(scene,cam,Vector((0,0,crown_z)))
        cutoff=int(np.clip((1-projected.y)*1080,0,1080))
        crown_image=image.copy();crown_image[cutoff:,:,3]=0
        rec['upper_crown_region']={'method':'screen rows above projection of trunk-axis point at 55% asset height; approximate crown region, not a material/object-ID mask','world_z_proxy_m':round(crown_z,5),'image_y_cutoff_px':cutoff,'metrics':metrics(crown_image)}
    if distance>=4000:
        yy,xx=np.nonzero(image[...,3]>0)
        if len(xx):
            x0,x1=max(0,int(xx.min())-5),min(1920,int(xx.max())+6)
            y0,y1=max(0,int(yy.min())-5),min(1080,int(yy.max())+6)
            mag=np.repeat(np.repeat(image[y0:y1,x0:x1],16,axis=0),16,axis=1)
            magpath=OUT/('MAGNIFIED_'+name+'_16x.png');png_write(magpath,diagnostic_background(mag))
            rec['magnified_single']={'file':magpath.relative_to(ROOT).as_posix(),'scale_factor':16,'source_crop_xyxy':[x0,y0,x1,y1],'background_srgb':[128,128,128],'resampling':'nearest-neighbour; diagnostic only'}
    meta.write_text(json.dumps(rec,indent=2)+'\n')
    ALL.append(rec);rendered+=1
    print('DISTANCE_DONE',json.dumps({'id':name,'sec':rec['render_seconds'],'area_px':measure['equivalent_opaque_pixels'],'bbox':measure['bbox_size_px'],'rgb':measure['alpha_weighted_lit_srgb']}),flush=True)
    # Incremental status survives an interrupted render job.
    (REPORT/f'distance_{args.family}_progress.json').write_text(json.dumps({'settings':SETTINGS,'frames':ALL},indent=2)+'\n')

def pine_family():
    global SOURCE_TEXTURES
    source=ROOT/'Blend'/'AleppoPine.blend';source_hash=sha(source)
    bpy.ops.wm.open_mainfile(filepath=str(source));scene,cam=configure_scene()
    SOURCE_TEXTURES=loaded_texture_hashes()
    for variant in args.variants:
        obj=bpy.data.objects['SM_PazFarm_AleppoPine_'+variant]
        lo=bpy.data.objects['SM_PazFarm_AleppoPine_'+variant+'_LOD3']
        b=bbox_world([obj]);height=b[1][2]-b[0][2]
        target=(0,0,b[0][2]+height*.5)
        for distance in SETTINGS['pines_distances_m']:
            for lod,model in [('LOD0',obj),('LOD3',lo)]:
                render_case(scene,cam,[model],'Pine_'+variant,variant,lod,'single',target,distance,SETTINGS['pine_elevation_deg'],source_hash)
        render_case(scene,cam,[lo],'Pine_'+variant,variant,'LOD3','single',target,SETTINGS['pine_LOD3_stress_m'],SETTINGS['pine_elevation_deg'],source_hash)
        top_distance=round(max(b[1][0]-b[0][0],b[1][1]-b[0][1])*2.5,3)
        for lod,model in [('LOD0',obj),('LOD3',lo)]:
            render_case(scene,cam,[model],'Pine_'+variant,variant,lod,'single',target,top_distance,90,source_hash,top=True)
    assert sha(source)==source_hash,'Source .blend changed during the distance render job'
    assert loaded_texture_hashes()==SOURCE_TEXTURES,'Source textures changed during the distance render job'

def bed_family():
    global SOURCE_TEXTURES
    source=ROOT/'Blend'/'Strawberry.blend';source_hash=sha(source)
    bpy.ops.wm.open_mainfile(filepath=str(source));scene,cam=configure_scene()
    SOURCE_TEXTURES=loaded_texture_hashes()
    orig=bpy.data.objects['SM_PazFarm_StrawberryBed_4m']
    low=bpy.data.objects['SM_PazFarm_StrawberryBed_4m_LOD3']
    for arrangement in ('single','ten_tiles'):
        groups={}
        for lod,model in [('LOD0',orig),('LOD3',low)]:
            if arrangement=='single':groups[lod]=[model]
            else:
                made=[]
                for row in range(5):
                    for tile in range(2):
                        copy=model.copy();copy.data=model.data
                        copy.name=f'Distance_{lod}_r{row}_t{tile}'
                        scene.collection.objects.link(copy)
                        copy.location=Vector(model.location)+Vector(((row-2)*5.48,tile*4,0))
                        copy.hide_render=True;made.append(copy)
                groups[lod]=made
        bpy.context.view_layer.update()
        target=(0,2 if arrangement=='single' else 4,.25)
        for distance in SETTINGS['beds_distances_m']:
            for lod in ('LOD0','LOD3'):
                render_case(scene,cam,groups[lod],'Strawberry','bed',lod,arrangement,target,distance,SETTINGS['bed_elevation_deg'],source_hash)
        if arrangement=='ten_tiles':
            for objs in groups.values():
                for o in objs:bpy.data.objects.remove(o,do_unlink=True)
    assert sha(source)==source_hash,'Source .blend changed during the distance render job'
    assert loaded_texture_hashes()==SOURCE_TEXTURES,'Source textures changed during the distance render job'

if args.family in ('pines','all'):pine_family()
if args.family in ('strawberry','all'):bed_family()

def generate_report():
    # Collect both independently rendered families without modifying their sources.
    records=[]
    for p in OUT.glob('*.json'):
        data=json.loads(p.read_text())
        if data.get('settings_sha256')==SETTINGS_SHA and (ROOT/data.get('file','missing')).exists():records.append(data)
    records.sort(key=lambda r:(r['family'],r['variant'],r['arrangement'],r['view'],r['requested_distance_m'],r['lod']))
    file_hash_cache={}
    def current_hash(path):
        path=str(path)
        if path not in file_hash_cache:file_hash_cache[path]=sha(path) if Path(path).is_file() else None
        return file_hash_cache[path]
    source_bindings=[]
    for r in records:
        source=ROOT/'Blend'/('AleppoPine.blend' if r['family']=='pines' else 'Strawberry.blend')
        textures=r.get('source_texture_sha256',{})
        source_bindings.append({'frame':r['id'],'blend_hash_current':current_hash(source)==r['source_blend_sha256'],'texture_hashes_recorded':bool(textures),'texture_hashes_captured_before_render':'texture_hash_capture' not in r and bool(textures),'texture_hashes_current':all(current_hash(p)==h for p,h in textures.items())})
    paired=[];pairs={}
    for r in records:
        k=(r['family'],r['variant'],r['arrangement'],r['view'],r['requested_distance_m'])
        pairs.setdefault(k,{})[r['lod']]=r
    for key,p in pairs.items():
        if not all(k in p for k in ('LOD0','LOD3')):continue
        a,b=png_read(ROOT/p['LOD0']['file']),png_read(ROOT/p['LOD3']['file'])
        aa,bb=a[...,3].astype(float)/255,b[...,3].astype(float)/255
        union=np.maximum(aa,bb).sum();inter=np.minimum(aa,bb).sum()
        ma,mb=aa>.1,bb>.1;binary_union=(ma|mb).sum()
        m0,m3=p['LOD0']['metrics'],p['LOD3']['metrics']
        pair={'key':list(key),'LOD0_frame':p['LOD0']['id'],'LOD3_frame':p['LOD3']['id'],
          'alpha_weighted_silhouette_iou':round(float(inter/max(union,1e-12)),5),
          'silhouette_iou_alpha_gt_0_1':round(float((ma&mb).sum()/max(binary_union,1)),5),
          'LOD3_over_LOD0_opaque_area_ratio':round(m3['equivalent_opaque_pixels']/max(m0['equivalent_opaque_pixels'],1e-12),5),
          'LOD3_minus_LOD0_lit_srgb':rounded(np.asarray(m3['alpha_weighted_lit_srgb'])-m0['alpha_weighted_lit_srgb'],3),
          'LOD3_minus_LOD0_luma_code_value':round(m3['alpha_weighted_luma_code_value']-m0['alpha_weighted_luma_code_value'],3),
          'both_visible':m0['equivalent_opaque_pixels']>0 and m3['equivalent_opaque_pixels']>0,
          'close_crop':p['LOD0']['close_crop_expected']}
        if 'upper_crown_region' in p['LOD0'] and 'upper_crown_region' in p['LOD3']:
            c0=p['LOD0']['upper_crown_region']['metrics'];c3=p['LOD3']['upper_crown_region']['metrics']
            pair['upper_crown_region_comparison']={'LOD0_lit_srgb':c0['alpha_weighted_lit_srgb'],'LOD3_lit_srgb':c3['alpha_weighted_lit_srgb'],'LOD3_minus_LOD0_luma_code_values':round(c3['alpha_weighted_luma_code_value']-c0['alpha_weighted_luma_code_value'],3),'note':'Screen-region proxy above 55% height projection; not a material-ID selection.'}
            pair['upper_crown_region_comparison']['LOD3_over_LOD0_luma_ratio']=round(c3['alpha_weighted_luma_code_value']/max(c0['alpha_weighted_luma_code_value'],1e-9),5)
        warnings=[]
        if not pair['both_visible']:warnings.append('A rendered LOD has zero geometry coverage')
        if not pair['close_crop']:
            if not .65<=pair['LOD3_over_LOD0_opaque_area_ratio']<=1.45:warnings.append('LOD3/LOD0 area ratio outside review band 0.65..1.45')
            if pair['alpha_weighted_silhouette_iou']<.55:warnings.append('Silhouette IoU below review band 0.55')
            if pair['LOD3_minus_LOD0_luma_code_value']>10:warnings.append('LOD3 is more than 10 sRGB luma code values brighter')
            if max(abs(x) for x in pair['LOD3_minus_LOD0_lit_srgb'])>18:warnings.append('A lit RGB channel differs by more than 18 code values')
            if 'upper_crown_region_comparison' in pair:
                c=pair['upper_crown_region_comparison']
                if c['LOD3_over_LOD0_luma_ratio']>1.2 and c['LOD3_minus_LOD0_luma_code_values']>2:warnings.append('Upper-crown proxy brightens over 20 percent and over 2 code values')
        pair['review_flags']=warnings
        pair['diagnostic_status']='REVIEW' if warnings else ('CLOSE_CROP_INFORMATIONAL' if pair['close_crop'] else 'PASS_DIAGNOSTIC_BANDS')
        if key[3]!='top' and key[4]>=150:
            unionmask=(aa>0)|(bb>0);yy,xx=np.nonzero(unionmask)
            if len(xx):
                x0,x1=max(0,int(xx.min())-8),min(1920,int(xx.max())+9)
                y0,y1=max(0,int(yy.min())-8),min(1080,int(yy.max())+9)
                factor=max(2,min(16,420//max(x1-x0,y1-y0)))
                ca=np.repeat(np.repeat(a[y0:y1,x0:x1],factor,axis=0),factor,axis=1)
                cb=np.repeat(np.repeat(b[y0:y1,x0:x1],factor,axis=0),factor,axis=1)
                image=np.zeros((ca.shape[0],ca.shape[1]*2+16,4),np.uint8)
                image[:,:ca.shape[1]]=ca;image[:,ca.shape[1]+16:]=cb
                name=f"MAGNIFIED_{p['LOD0']['id'].replace('_LOD0','')}_{factor}x.png"
                png_write(OUT/name,diagnostic_background(image))
                pair['magnified_comparison']={'file':(OUT/name).relative_to(ROOT).as_posix(),'scale_factor':factor,'source_crop_xyxy':[x0,y0,x1,y1],'left':'LOD0','right':'LOD3','background_srgb':[128,128,128],'resampling':'nearest-neighbour; diagnostic only, never a substitute for full frames'}
        paired.append(pair)
    # Cross-distance colour summary is descriptive; raster samples naturally vary.
    drift=[]
    for family in ('pines','strawberry'):
        for variant in ('ABC' if family=='pines' else ['bed']):
            for arr in (['single'] if family=='pines' else ['single','ten_tiles']):
                for lod in ('LOD0','LOD3'):
                    subset=[r for r in records if r['family']==family and r['variant']==variant and r['arrangement']==arr and r['lod']==lod and r['view']=='perspective' and not r['close_crop_expected']]
                    if not subset:continue
                    subset.sort(key=lambda r:r['requested_distance_m']);ref=subset[0]
                    for r in subset[1:]:
                        drift.append({'frame':r['id'],'baseline_frame':ref['id'],'luma_code_value_delta':round(r['metrics']['alpha_weighted_luma_code_value']-ref['metrics']['alpha_weighted_luma_code_value'],3),'srgb_delta':rounded(np.asarray(r['metrics']['alpha_weighted_lit_srgb'])-ref['metrics']['alpha_weighted_lit_srgb'],3)})
    expected=53 # 3 pines x (8 paired distance + 1 stress + 2 top) + 20 beds
    report={'status':'OFFLINE_DISTANCE_EVIDENCE_COMPLETE' if len(records)==expected else 'PARTIAL_RENDER_SUITE',
      'expected_frames':expected,'actual_frames':len(records),'settings':SETTINGS,'settings_sha256':SETTINGS_SHA,
      'frames':records,'lod_comparisons':paired,'distance_colour_drift':drift,
      'source_bindings':source_bindings,
      'all_frame_source_bindings_current':all(s['blend_hash_current'] and s['texture_hashes_recorded'] and s['texture_hashes_captured_before_render'] and s['texture_hashes_current'] for s in source_bindings),
      'diagnostic_result':'REVIEW_REQUIRED' if any(p['review_flags'] for p in paired) else 'PASS_COMPLETED_PAIRS',
      'pass_criteria':{'scope':'Offline diagnostic bands chosen for this suite; not user acceptance or Unreal validation','all_required_frames_present':len(records)==expected,'fixed_frame_and_settings':all(r['resolution_px']==[1920,1080] and r['settings_sha256']==SETTINGS_SHA for r in records),'all_LOD_pairs_have_nonzero_geometry':all(p['both_visible'] for p in paired),'noncropped_area_ratio_review_band':[.65,1.45],'noncropped_alpha_iou_min_review_band':.55,'noncropped_LOD3_brightening_max_luma_code_values':10,'noncropped_max_abs_rgb_channel_delta':18,'upper_crown_proxy_brightening_review_band':'flag if over20 percent and over2 code values brighter','review_pair_count':sum(bool(p['review_flags']) for p in paired)},
      'interpretation':['No frame is auto-framed or resized; distances are measured to declared targets at fixed 60-degree horizontal FOV.','5m pine and 2m bed/block views intentionally crop; separate hero previews show complete close assets.','Lit sRGB is measured from actual PNG bytes weighted by geometry alpha. Alpha excludes ground and cast shadows.','Small images are limited by pixel coverage; an individual plant may occupy fewer than one equivalent opaque pixel at distance. No mesh can guarantee screen visibility at every resolution or distance.','This is Blender CPU raster evidence only: Unreal Nanite, streaming, HLOD selection, materials and visibility were not tested.','4km pine LOD3 stress frames are additional limits evidence; not evidence of Unreal forest appearance.']}
    (REPORT/'distance_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    html=['<!doctype html><html lang="en"><meta charset="utf-8"><title>Paz Farm v003 fixed-distance evidence</title><style>body{background:#202427;color:#e4e8e7;font:15px system-ui;margin:24px}p{max-width:1100px;line-height:1.5}table{border-collapse:collapse;width:100%;margin:20px 0}th,td{text-align:left;padding:7px;border-bottom:1px solid #45505a}img{background:#777;max-width:100%;height:auto}details{margin:14px 0}summary{cursor:pointer}a{color:#9cd9ff}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}.actual{width:100%;image-rendering:auto}code{font-size:13px}</style><h1>Paz Farm v003 — fixed-distance evidence</h1><p>All source frames are 1920×1080, perspective, horizontal FOV 60°, fixed lighting/exposure and camera-to-target distances. Grey behind alpha is a viewing aid. Open an image at its original size for a true pixel inspection. No far auto-framing. Close frames intentionally crop; complete assets appear in the separate hero gallery.</p><p>Transparent film masks geometry only. Lit RGB is actual PNG sRGB weighted by alpha. Magnified crops below are diagnostic nearest-neighbour enlargements, clearly separate from full frames. Blender results do not verify Unreal/HLOD behaviour.</p>']
    html+=['<table><tr><th>Frame</th><th>Distance m</th><th>Alpha area px</th><th>Bounds px</th><th>Lit sRGB</th><th>Crop?</th></tr>']
    for r in records:
        m=r['metrics'];url=Path(r['file']).name
        html.append(f"<tr><td><a href='{url}'>{r['id']}</a></td><td>{r['actual_target_distance_m']:.3f}</td><td>{m['equivalent_opaque_pixels']:.3f}</td><td>{m['bbox_size_px']}</td><td>{m['alpha_weighted_lit_srgb']}</td><td>{m['clipped_at_image_border']}</td></tr>")
    html.append('</table><h2>Matched LOD comparisons</h2>')
    for p in paired:
        html.append(f"<details><summary>{p['LOD0_frame'].replace('_LOD0','')} — {p['diagnostic_status']}; alpha IoU {p['alpha_weighted_silhouette_iou']:.3f}; LOD3 area ratio {p['LOD3_over_LOD0_opaque_area_ratio']:.3f}; luma change {p['LOD3_minus_LOD0_luma_code_value']:+.2f}</summary><div class='pair'><div>LOD0 actual frame<a href='{p['LOD0_frame']}.png'><img class='actual' src='{p['LOD0_frame']}.png'></a></div><div>LOD3 actual frame<a href='{p['LOD3_frame']}.png'><img class='actual' src='{p['LOD3_frame']}.png'></a></div></div>")
        if p['review_flags']:html.append('<p>Review: '+'; '.join(p['review_flags'])+'</p>')
        if 'upper_crown_region_comparison' in p:
            c=p['upper_crown_region_comparison'];html.append(f"<p>Upper-crown screen proxy: RGB {c['LOD0_lit_srgb']} → {c['LOD3_lit_srgb']}; luma ratio {c['LOD3_over_LOD0_luma_ratio']:.3f}. This is a region proxy, not a material-ID mask.</p>")
        if 'magnified_comparison' in p:
            mag=p['magnified_comparison'];html.append(f"<p>MAGNIFIED {mag['scale_factor']}× pixel crop. LOD0 left; LOD3 right.</p><img src='{Path(mag['file']).name}'>")
        html.append('</details>')
    stress=[r for r in records if 'magnified_single' in r]
    if stress:
        html.append('<h2>4 km stress — MAGNIFIED 16× pixel crops</h2><p>These magnified pixels show the raster limit, not full-size on-screen tree detail. Full-resolution frames are linked in the table.</p>')
        for r in stress:html.append(f"<div><h3>{r['id']}</h3><img src='{Path(r['magnified_single']['file']).name}'></div>")
    html.append('<p><a href="../../Reports/distance_validation.json">Exact settings, camera transforms and measured metrics</a></p></html>')
    (OUT/'INDEX.html').write_text(''.join(html),encoding='utf-8')
    # Human-readable result stays concise and never converts subpixel evidence
    # into a guarantee about native visibility.
    lines=['# Fixed-distance preview evidence — v003','',f"**{report['status']}**: {len(records)} of {expected} full-resolution frames.",'','1920×1080 perspective; horizontal FOV 60°; Cycles CPU 32 samples; no denoising/adaptive sampling; Standard sRGB; exposure 0. World/sun/camera settings remain fixed. Transparent alpha covers geometry only. All distances are camera-to-declared-target slant distances.','', 'See `Previews/Distance/INDEX.html`; full settings and camera transforms are in `Reports/distance_validation.json`. Magnified pairs are diagnostic crops; original full frames are retained.','', '| Asset / arrangement | Distance | LOD0 area px | LOD3 area px | Alpha IoU | LOD3 luma delta |','|---|---:|---:|---:|---:|---:|']
    byid={r['id']:r for r in records}
    for p in paired:
        key=p['key']
        if key[3]=='top' or key[4] not in (150,300,500,1000):continue
        r0,r3=byid[p['LOD0_frame']],byid[p['LOD3_frame']]
        lines.append(f"| {key[0]} {key[1]} {key[2]} | {key[4]} m | {r0['metrics']['equivalent_opaque_pixels']:.3f} | {r3['metrics']['equivalent_opaque_pixels']:.3f} | {p['alpha_weighted_silhouette_iou']:.3f} | {p['LOD3_minus_LOD0_luma_code_value']:+.2f} |")
    lines+=['','## Calibration and source binding','','The initial A check found the smoother LOD3 upper-crown screen region about 42–44% brighter than LOD0. The model author calibrated the shared hull texture by a 0.63 linear-albedo multiplier, then regenerated the pine sources. Final comparison values above use those updated sources. The superseded numerical check remains in `distance_calibration_initial.json`. The crown region is an explicit screen-space proxy above the 55%-height projection, not a material-ID mask.',f"All final frame source/texture bindings current and captured before rendering: **{report['all_frame_source_bindings_current']}**. Each family also verifies those textures and its .blend are unchanged after rendering. Resume requires matching pre-render texture hashes, source hash, settings hash and PNG hash."]
    lines+=['','## Limits','','5 m pine and 2 m bed/block frames intentionally crop at fixed FOV; the separate hero views show complete close assets. Subpixel plants cannot be guaranteed visible in every raster/view. 4 km pine stress frames are included. These renders assess model source appearance in Blender, not Unreal Nanite/HLOD/streaming. Native import, lowest-LOD selection, always-loaded policy, final lighting, save/reopen and acceptance remain with the operator.']
    lines+=['','Diagnostic review bands (not visual acceptance): nonzero alpha in both LODs, area ratio 0.65–1.45, alpha IoU at least 0.55, LOD3 brightening no more than 10 luma code values, absolute channel difference no more than 18. Upper-crown proxy brightening is flagged when both over 20% and over 2 code values. Cropped close views are informational. Individual failures are retained in JSON for review.']
    (REPORT/'distance_notes.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if len(records)==expected and report['all_frame_source_bindings_current']:
        for name in ('distance_all_progress.json','distance_pines_progress.json','distance_strawberry_progress.json'):
            (REPORT/name).unlink(missing_ok=True)
    print('DISTANCE_REPORT',json.dumps({'status':report['status'],'frames':len(records),'pairs':len(paired)}),flush=True)

generate_report()
