"""Shared fixed-camera/PNG measurement helpers; no modelling or native actions."""
import bpy,sys,math,json,hashlib,struct,zlib,binascii,time
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import numpy as np
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SETTINGS={
 'engine':'CYCLES','samples':16,'adaptive_sampling':False,'denoising':False,
 'resolution_px':[1920,1080],'horizontal_fov_deg':60.0,'camera_type':'PERSP',
 'camera_clip_m':[0.01,10000],'view_transform':'Standard','look':'None','exposure_stops':0.0,'gamma':1.0,
 'world_color_linear':[0.65,0.70,0.78],'world_strength':0.35,
 'sun_energy':2.0,'sun_rotation_xyz_deg':[35,-25,-40],'sun_angle_deg':5.0,
 'transparent_film':True,'render_ground':False,'shadows_in_mask':False,
 'azimuth_deg':-55.0,'samples_seed':1977,'threads':4,
 'distance_definition':'Euclidean camera-to-declared-target slant distance in metres',
 'png':'RGBA8 display sRGB, original unrescaled 1920x1080 evidence'
}
SETTINGS_SHA=hashlib.sha256(json.dumps(SETTINGS,sort_keys=True).encode()).hexdigest()


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
            if not row.any() and not prev.any():
                out[y]=0
                continue
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

def loaded_texture_hashes():
    result={}
    for im in bpy.data.images:
        if im.source=='FILE' and im.filepath:
            p=Path(bpy.path.abspath(im.filepath))
            if p.is_file():result[str(p.resolve())]=sha(p)
    return result
