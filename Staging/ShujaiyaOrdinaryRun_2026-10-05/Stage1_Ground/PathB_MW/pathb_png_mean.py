"""Offline ground-colour check for Path B captures (pure Python PNG decoder; no PIL/numpy, no unreal).

Usage: python pathb_png_mean.py <image.png> x0,y0,x1,y1 [more boxes]
MEASURED reference (MW preview 01_middle, 1879x820): boxes 1250,520,1500,640 80,380,280,500 1100,650,1400,780 300,450,450,560
mean sRGB ~ (204-216, 167-178, 126-135) = the orange Aviv rejected. Supports 8-bit RGB/RGBA non-interlaced PNG.
"""
import zlib, struct, sys
def load(path):
    data=open(path,'rb').read(); assert data[:8]==b'\x89PNG\r\n\x1a\n'
    pos=8; idat=b''; w=h=None
    while pos<len(data):
        n=struct.unpack('>I',data[pos:pos+4])[0]; t=data[pos+4:pos+8]; c=data[pos+8:pos+8+n]; pos+=12+n
        if t==b'IHDR': w,h,bd,ct,_,_,il=struct.unpack('>IIBBBBB',c); assert bd==8 and il==0
        elif t==b'IDAT': idat+=c
        elif t==b'IEND': break
    bpp={2:3,6:4,0:1,4:2}[ct]; raw=zlib.decompress(idat); stride=w*bpp; rows=[]; prev=bytearray(stride); i=0
    for y in range(h):
        f=raw[i]; line=bytearray(raw[i+1:i+1+stride]); i+=1+stride
        if f==1:
            for x in range(bpp,stride): line[x]=(line[x]+line[x-bpp])&255
        elif f==2:
            for x in range(stride): line[x]=(line[x]+prev[x])&255
        elif f==3:
            for x in range(stride): line[x]=(line[x]+(((line[x-bpp] if x>=bpp else 0)+prev[x])>>1))&255
        elif f==4:
            for x in range(stride):
                a=line[x-bpp] if x>=bpp else 0; b=prev[x]; c=prev[x-bpp] if x>=bpp else 0
                p=a+b-c; pa=abs(p-a); pb=abs(p-b); pc=abs(p-c)
                line[x]=(line[x]+(a if pa<=pb and pa<=pc else (b if pb<=pc else c)))&255
        rows.append(bytes(line)); prev=line
    return w,h,bpp,rows
def mean(path,box=None):
    w,h,bpp,rows=load(path); x0,y0,x1,y1=box or (0,0,w,h); s=[0,0,0]; n=0
    for y in range(y0,y1):
        r=rows[y]
        for x in range(x0,x1):
            o=x*bpp
            for k in range(3): s[k]+=r[o+k]
            n+=1
    return [round(v/n,1) for v in s],(w,h)
if __name__=='__main__':
    p=sys.argv[1]; boxes=[tuple(map(int,b.split(','))) for b in sys.argv[2:]] or [None]
    for b in boxes: print(b, mean(p,b))
