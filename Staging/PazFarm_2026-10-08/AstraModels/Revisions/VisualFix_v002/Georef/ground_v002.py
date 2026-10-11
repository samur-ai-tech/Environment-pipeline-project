"""Offline procedural Paz Farm overlay. Writes only beside this revision.

Run with Blender's bundled Python (numpy required); no Blender/Unreal session is
opened. Original layout/placements/texture are read only. The reference image is
read ONLY for the comparison page; no reference pixels enter the deliverable.
"""
import json, math, hashlib, struct, zlib, binascii, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FARM = HERE.parents[3]
GEO = FARM / 'Georef'
PREV = ROOT / 'Previews'
REPORT = ROOT / 'Reports'
for p in (PREV, REPORT):
    p.mkdir(exist_ok=True)
S = json.loads((HERE / 'GROUND_SETTINGS.json').read_text())
L = json.loads((GEO / 'LAYOUT.json').read_text())
P = json.loads((GEO / 'PLACEMENTS.json').read_text())
OLD = json.loads((GEO / 'FARM_GROUND.json').read_text())
SIZE, N, RES = S['extent']['size_m'], S['extent']['pixels'], S['extent']['metres_per_pixel']
E0, N1 = S['extent']['west_edge_m_from_pin'], S['extent']['north_edge_m_from_pin']
assert all(S['extent'][k] == OLD[k] for k in ('size_m','pixels','metres_per_pixel','west_edge_m_from_pin','north_edge_m_from_pin'))
A, B = complex(*L['fit']['a']), complex(*L['fit']['b'])
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
E, NN = E0 + (xx + .5) * RES, N1 - (yy + .5) * RES
del xx, yy
SC = ((E + 1j * NN - B) / A).real.astype(np.float32)
rng = np.random.default_rng(S['seed'])

def smoothstep(lo, hi, x):
    t = np.clip((x-lo)/(hi-lo), 0, 1)
    return t*t*(3-2*t)

def noise(scale, seed):
    """Cubic-interpolated value noise, never nearest-neighbour enlarged blocks."""
    x, y = (E-E0)/scale, (N1-NN)/scale
    ix, iy = x.astype(np.int32), y.astype(np.int32)
    fx, fy = x-ix, y-iy
    fx, fy = fx*fx*(3-2*fx), fy*fy*(3-2*fy)
    grid = np.random.default_rng(seed).normal(0, 1, (int(iy.max())+2, int(ix.max())+2)).astype(np.float32)
    return ((grid[iy,ix]*(1-fx)+grid[iy,ix+1]*fx)*(1-fy)+(grid[iy+1,ix]*(1-fx)+grid[iy+1,ix+1]*fx)*fy).astype(np.float32)

nlarge, nmid, nfine = noise(17, 70), noise(3.2, 71), noise(.6, 72)
nsoil = .40*nlarge + .45*nmid + .15*nfine

def line_distance(a, b):
    x0,y0 = a; dx,dy = b[0]-x0,b[1]-y0
    q = np.clip(((E-x0)*dx+(NN-y0)*dy)/(dx*dx+dy*dy or 1e-9),0,1)
    return np.hypot(E-(x0+q*dx),NN-(y0+q*dy))

def polygon(poly):
    inside = np.zeros((N,N),bool)
    dist = np.full((N,N),np.inf,np.float32)
    for a,b in zip(poly,poly[1:]+poly[:1]):
        x1,y1 = a; x2,y2 = b
        inside ^= ((y1>NN)!=(y2>NN)) & (E < (x2-x1)*(NN-y1)/(y2-y1 if y2!=y1 else 1e-9)+x1)
        np.minimum(dist,line_distance(a,b),out=dist)
    return inside,np.where(inside,dist,-dist)

def poly_alpha(poly, width):
    inside, sd = polygon(poly)
    return inside, smoothstep(-width/2,width/2,sd)

def srgb(c): return np.asarray(c,np.float32)

premul = np.zeros((N,N,3),np.float32)
alpha = np.zeros((N,N),np.float32)
def over(col,a):
    global premul,alpha
    premul *= 1-a[...,None]
    premul += col*a[...,None]
    alpha = a+alpha*(1-a)

def rows(st):
    t = math.radians(st['row_direction_deg'])
    return E*math.cos(t)+NN*math.sin(t), -E*math.sin(t)+NN*math.cos(t)

def basecol(rgb): return np.broadcast_to(srgb(rgb),(N,N,3)).copy()

phase_reports = {}
plot_stats = {}
plot_masks = {}
for idx,(name, plot) in enumerate(L['plots'].items()):
    st = S['plots'][name]; mode = st['mode']
    inside,a = poly_alpha(plot['polygon_m'],S['edge_feather_m'])
    plot_masks[name] = inside
    if mode in ('bare','soil_under_models'):
        col = basecol(st['base_rgb'])
        if 'faint_tillage_pitch_m' in st:
            u,v = rows(st)
            col += (st['faint_tillage_rgb_amplitude']*np.cos(2*np.pi*v/st['faint_tillage_pitch_m']))[...,None]
    elif mode == 'fine_furrows':
        u,v = rows(st)
        # Fine furrows with restrained longitudinal irregularity. A single global
        # phase retains the measured row direction without wavy macro-banding.
        furrow = np.cos(2*np.pi*v/st['row_pitch_m'])
        strength = .86+.10*np.tanh(nmid)
        col = basecol(st['base_rgb']) + furrow[...,None]*strength[...,None]*srgb(st['row_rgb_amplitude'])
    elif mode == 'strawberry':
        u,v = rows(st)
        items = [p for p in P['items'] if p['kind']=='strawberry_bed' and abs(p['row_deg']-st['row_direction_deg'])<.01]
        t = math.radians(st['row_direction_deg']); cs,sn = math.cos(t),math.sin(t)
        byrow = {}
        for p in items:
            pu,pv = p['e']*cs+p['n']*sn,-p['e']*sn+p['n']*cs
            k = round(pv/st['row_pitch_m']-.5)
            byrow.setdefault(k,[]).append((pu,pv))
        band = np.zeros_like(E)
        errors = []
        extents = []
        for k,pts in sorted(byrow.items()):
            center = float(np.median([x[1] for x in pts]))
            errors += [abs(x[1]-center) for x in pts]
            us = sorted(x[0] for x in pts)
            # Split any non-contiguous run; each model occupies u..u+4m from its
            # documented short-end pivot, preserving the actual existing phase.
            runs=[]; start=last=us[0]
            for pos in us[1:]:
                if pos-last > st['bed_length_m']+.05:
                    runs.append((start,last+st['bed_length_m'])); start=pos
                last=pos
            runs.append((start,last+st['bed_length_m']))
            cross = 1-smoothstep(st['shoulder_band_width_m']/2-st['shoulder_edge_softness_m'],st['shoulder_band_width_m']/2+st['shoulder_edge_softness_m'],abs(v-center))
            for lo,hi in runs:
                along = smoothstep(lo-.35,lo+.2,u)*(1-smoothstep(hi-.2,hi+.35,u))
                np.maximum(band,cross*along,out=band)
                extents.append({'v_m':round(center,5),'u_min_m':round(lo,5),'u_max_m':round(hi,5)})
        col = basecol(st['lane_rgb'])+(srgb(st['shoulder_rgb'])-srgb(st['lane_rgb']))*band[...,None]
        phase_reports[name] = {'tiles_used':len(items),'rows':len(byrow),'max_tile_cross_axis_error_m':max(errors),'phase_method':'median actual PLACEMENTS cross-axis per row; 4m extent from short-end pivot','band_width_m':st['shoulder_band_width_m'],'runs':extents}
    elif mode == 'patchy_green':
        u,v = rows(st)
        patch = smoothstep(-.9,.9,nlarge*.7+nmid*.3)
        stripe = .5+.5*np.cos(2*np.pi*v/st['row_pitch_m'])
        cover = np.clip(.12+.77*patch+.12*(stripe-.5),0,1)
        col = basecol(st['soil_rgb']) + (srgb(st['crop_rgb'])-srgb(st['soil_rgb']))*cover[...,None]
    elif mode == 'split_green':
        u,v = rows(st)
        distance = abs((v+st['row_pitch_m']/2)%st['row_pitch_m']-st['row_pitch_m']/2)
        band = 1-smoothstep(st['crop_band_width_m']/2-.3,st['crop_band_width_m']/2+.3,distance)
        west = basecol(st['west_lane_rgb'])+(srgb(st['west_crop_rgb'])-srgb(st['west_lane_rgb']))*band[...,None]
        east = basecol(st['east_lane_rgb'])+(srgb(st['east_crop_rgb'])-srgb(st['east_lane_rgb']))*band[...,None]
        split_width_px = st['split_softness_m']/L['fit']['scale_m_per_px']
        blend = smoothstep(st['west_split_screenshot_x']-split_width_px,st['west_split_screenshot_x']+split_width_px,SC)
        col = west*(1-blend[...,None])+east*blend[...,None]
        # Sparse smooth soil interruptions, not a checker grid or fake tree dots.
        breaks = smoothstep(.6,1.2,nmid)*smoothstep(.0,.6,nlarge)*.55
        col = col*(1-breaks[...,None])+srgb(st['pale_interrupt_rgb'])*breaks[...,None]
        del west,east
    else: raise ValueError(mode)
    col += st['noise_rgb_amplitude']*nsoil[...,None]
    over(col,a)
    sample = col[inside]
    plot_stats[name] = {'mode':mode,'area_from_mask_m2':round(float(inside.sum()*RES*RES),2),'ground_only_mean_srgb':np.round(sample.mean(0),2).tolist(),'ground_only_p05_srgb':np.round(np.quantile(sample,.05,axis=0),2).tolist(),'ground_only_p95_srgb':np.round(np.quantile(sample,.95,axis=0),2).tolist(),'reference_whole_plot_target_srgb':st['appearance_target_rgb'],'row_direction_deg':st.get('row_direction_deg'),'row_pitch_m':st.get('row_pitch_m')}
    print('PLOT',name,flush=True)
    del col

def pxpoly(coords):
    return [[(A*complex(x,-y)+B).real,(A*complex(x,-y)+B).imag] for x,y in coords]
apron = S['barn_south_apron']
_,aa = poly_alpha(pxpoly(apron['polygon_screenshot_px']),apron['feather_m'])
over(srgb(apron['rgb'])+.9*nsoil[...,None],aa)

def road_layer(line,width,colour,flare=None):
    dist = np.full_like(E,np.inf)
    for a,b in zip(line,line[1:]): np.minimum(dist,line_distance(a,b),out=dist)
    shoulder=S['road_shoulders']
    radius=width/2+shoulder['width_variation_m']*np.tanh(nmid)
    if flare:
        for p,r in flare:
            # Equivalent distance signed against the local junction disk.
            np.minimum(dist,np.hypot(E-p[0],NN-p[1])-r+radius,out=dist)
    a=1-smoothstep(radius,radius+shoulder['feather_m'],dist)
    col=srgb(colour)+shoulder['noise_rgb_amplitude']*nsoil[...,None]
    over(col,a)
    return a

road_masks=[]
for name,r in L['roads'].items():
    st=S['roads'][name]
    assert st['width_m']==r['width_m']
    road_masks.append(road_layer(r['line_m'],st['width_m'],st['rgb']))

def closest_point(p,line):
    best=None
    for a,b in zip(line,line[1:]):
        d=np.asarray(b)-a; q=np.asarray(a)+d*np.clip(np.dot(np.asarray(p)-a,d)/np.dot(d,d),0,1)
        distance=float(np.linalg.norm(q-p))
        if best is None or distance<best[0]: best=distance,q.tolist()
    return best

junctions=[]
for j in S['junctions']:
    start=L['roads'][j['from_road']]['line_m'][j['endpoint']]
    distance,end=closest_point(start,L['roads'][j['to_road']]['line_m'])
    assert distance<=j['max_gap_m'],(j,distance)
    colour=np.mean([S['roads'][j['from_road']]['rgb'],S['roads'][j['to_road']]['rgb']],axis=0)
    road_masks.append(road_layer([start,end],j['width_m'],colour,[(end,j['flare_radius_m'])]))
    junctions.append({**j,'derived_connector_m':[start,end],'gap_m':round(distance,3),'original_vertices_changed':False})

rgb=np.divide(premul,alpha[...,None],out=np.zeros_like(premul),where=alpha[...,None]>0)
rgba=np.dstack([np.rint(np.clip(rgb,0,255)).astype(np.uint8),np.rint(alpha*255).astype(np.uint8)])
rgba[rgba[...,3]==0,:3]=0

def write_png(path,img):
    img=np.asarray(img,np.uint8); h,w=img.shape[:2]
    def chunk(t,d): return struct.pack('!I',len(d))+t+d+struct.pack('!I',binascii.crc32(t+d)&0xffffffff)
    payload=b''.join(b'\0'+row.tobytes() for row in img)
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,6 if img.shape[2]==4 else 2,0,0,0))+chunk(b'sRGB',b'\0')+chunk(b'IDAT',zlib.compress(payload,6))+chunk(b'IEND',b'')
    path.write_bytes(data)

def read_png(path):
    raw=Path(path).read_bytes(); pos=8; chunks=[]; palette=None
    while pos<len(raw):
        length=struct.unpack('!I',raw[pos:pos+4])[0];typ=raw[pos+4:pos+8];d=raw[pos+8:pos+8+length];pos+=12+length
        if typ==b'IHDR': w,h,depth,ctype,_,_,interlace=struct.unpack('!2I5B',d)
        if typ==b'IDAT': chunks.append(d)
    assert depth==8 and ctype in (2,6) and interlace==0,(depth,ctype,interlace)
    bpp=4 if ctype==6 else 3; step=w*bpp
    data=np.frombuffer(zlib.decompress(b''.join(chunks)),np.uint8).reshape(h,step+1)
    out=np.zeros((h,step),np.uint8)
    for y in range(h):
        f=int(data[y,0]); row=data[y,1:].astype(np.int32); prev=out[y-1].astype(np.int32) if y else np.zeros(step,np.int32)
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
        else: assert f==0,f
        out[y]=row
    return out.reshape(h,w,bpp)

def composite(img):
    if img.shape[2]==3: return img
    a=img[...,3:4].astype(np.float32)/255
    return np.rint(img[...,:3]*a+np.array([66,69,69])*(1-a)).astype(np.uint8)

def sample_shot_alignment(img):
    y,x=np.mgrid[0:850,0:1209]
    z=A*(x+.5-1j*(y+.5))+B
    tx=(z.real-E0)/RES-.5; ty=(N1-z.imag)/RES-.5
    ix,iy=np.floor(tx).astype(int),np.floor(ty).astype(int)
    fx,fy=tx-ix,ty-iy
    ix=np.clip(ix,0,N-2);iy=np.clip(iy,0,N-2)
    # Premultiplied resampling prevents black fringes at transparent boundaries.
    work=img.astype(np.float32)
    if work.shape[2]==4: work[...,:3]*=work[...,3:4]/255
    out=((work[iy,ix]*(1-fx[...,None])+work[iy,ix+1]*fx[...,None])*(1-fy[...,None])+(work[iy+1,ix]*(1-fx[...,None])+work[iy+1,ix+1]*fx[...,None])*fy[...,None])
    if out.shape[2]==4:
        out[...,:3]=np.divide(out[...,:3],out[...,3:4]/255,out=np.zeros_like(out[...,:3]),where=out[...,3:4]>0)
    return np.clip(np.rint(out),0,255).astype(np.uint8)

texture=HERE/'T_PazFarm_Ground.png'
write_png(texture,rgba)
assert np.array_equal(read_png(texture),rgba), 'PNG byte round-trip mismatch'
write_png(PREV/'ground_v002_north_up.png',composite(rgba[::2,::2]))
write_png(PREV/'ground_v002_reference_aligned.png',composite(sample_shot_alignment(rgba)))
old_texture=read_png(OLD['texture'])
assert old_texture.shape==rgba.shape
write_png(PREV/'ground_v001_reference_aligned.png',composite(sample_shot_alignment(old_texture)))

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
source_hashes={p.relative_to(FARM).as_posix():sha(p) for p in (GEO/'LAYOUT.json',GEO/'PLACEMENTS.json',GEO/'FARM_GROUND.json')}
ground={**OLD,'texture':str(texture),'revision':'VisualFix_v002','colour_space':'sRGB, explicit byte encoding; alpha linear coverage','north_up':True,'road_colours':{k:v['rgb'] for k,v in S['roads'].items()},'method':'Original procedural fine furrows, smooth soil variation, split low crops, actual-placement-phase strawberry shoulders, soil under orchard meshes, continuous dirt roads, south barn apron; no reference image pixels copied','settings':'GROUND_SETTINGS.json','generator':'ground_v002.py','original_layout_sha256':source_hashes['Georef/LAYOUT.json'],'original_placements_sha256':source_hashes['Georef/PLACEMENTS.json'],'source_trace_coordinates_unchanged':True,'local_junction_connectors':junctions,'uv_contract':{'u':'(E - west_edge_m_from_pin) / size_m','v':'(north_edge_m_from_pin - N) / size_m','E':'metres east from farm pin','N':'metres north from farm pin','pixel_centre_formula':'E=west+(x+0.5)*0.25; N=north-(y+0.5)*0.25','texture_rotation_deg':0,'sampler_address':'Clamp','texture_srgb':True},'texture_sha256':sha(texture)}
(HERE/'FARM_GROUND.json').write_text(json.dumps(ground,indent=2)+'\n')
coverage=np.maximum.reduce(road_masks)
qa={'status':'PASS','revision':'VisualFix_v002','shape':list(rgba.shape),'png_byte_round_trip_match':True,'extent_exact_match_original_metadata':True,'extent':S['extent'],'source_hashes':source_hashes,'output_texture_sha256':sha(texture),'alpha_zero_pixel_count':int(np.sum(rgba[...,3]==0)),'alpha_full_pixel_count':int(np.sum(rgba[...,3]==255)),'alpha_feather_pixel_count':int(np.sum((rgba[...,3]>0)&(rgba[...,3]<255))),'outside_rgba_zero':bool(np.all(rgba[rgba[...,3]==0]==0)),'reference_pixels_used_in_texture':False,'plots':plot_stats,'strawberry_alignment':phase_reports,'local_road_junctions':junctions,'road_core_coverage_pixel_count':int(np.sum(coverage>.99)),'native_import_or_render_performed':False,'limitations':['Ground-only preview intentionally contains no tree crowns, barn roof, fences or strawberry geometry.','sRGB targets are screenshot appearance anchors; lighting/exposure may require native tuning.','Georeference uncertainty remains the original 8.96 m RMS.','1.8 m northeast furrow pitch is an editable visual estimate.']}
assert phase_reports['strawberry_west']['tiles_used']==449
assert phase_reports['strawberry_triangle']['tiles_used']==314
assert max(v['max_tile_cross_axis_error_m'] for v in phase_reports.values())<.02
assert qa['outside_rgba_zero'] and qa['alpha_zero_pixel_count']>0 and qa['alpha_feather_pixel_count']>0
(REPORT/'GROUND_QA.json').write_text(json.dumps(qa,indent=2)+'\n')
html='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Paz Farm ground v002</title><style>body{background:#1c2021;color:#e4e7e6;font:16px system-ui;margin:24px}section{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}img{width:100%}h1{font-size:24px}h2{font-size:18px}p{max-width:1100px;line-height:1.5}</style><h1>Paz Farm ground v002 — offline comparison</h1><p>All three panels use the reference screenshot alignment. Texture is ground only: real tree crowns, strawberry foliage, barn, fence and gate are separate assets. The reference image is not used as texture content. Click an image for full resolution.</p><section>'''
panels=[('Reference photograph','../../../../References/Screenshot%202026-10-08%20175537.png'),('Original procedural ground','ground_v001_reference_aligned.png'),('Revised procedural ground','ground_v002_reference_aligned.png')]
for title,url in panels: html+=f'<div><h2>{title}</h2><a href="{url}"><img src="{url}"></a></div>'
html+='</section><p>Fine northeast furrows 1.8 m; southwest furrows 1.91 m. Two strawberry shoulders align to the unchanged 763 bed positions. Orchards use exposed soil with no painted crowns. The straight screenshot crop is a preview transform only; the deliverable remains north up at its original 512 m / 2048 pixel extent.</p><p><a href="ground_v002_north_up.png">North-up texture preview</a> · <a href="../Georef/GROUND_SETTINGS.json">Editable settings</a> · <a href="../Reports/GROUND_QA.json">Measured QA</a></p></html>'
(PREV/'GROUND_COMPARE.html').write_text(html,encoding='utf-8')
print(json.dumps({'texture':str(texture),'sha256':ground['texture_sha256'],'qa':'PASS','strawberry_tiles':763,'extent_match':True}),flush=True)
