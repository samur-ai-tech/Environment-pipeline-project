import sys,os,re,zlib,gzip,io
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
def cpio_entries(d):
    p=0; out=[]
    while p+76<=len(d):
        h=d[p:p+76]
        if h[:6]!=b'070707': break
        ns=int(h[59:65],8); fs=int(h[65:76],8)
        name=d[p+76:p+76+ns-1].decode('latin1'); data=d[p+76+ns:p+76+ns+fs]; p+=76+ns+fs
        if name=='TRAILER!!!': break
        out.append((name,data))
    return out
src=sys.argv[1]; out=sys.argv[2]; os.makedirs(out,exist_ok=True)
d=open(src,'rb').read()
# gzip members
idx=[m.start() for m in re.finditer(b'\x1f\x8b\x08',d)]
n=0
for i in idx:
    try:
        dec=zlib.decompressobj(16+zlib.MAX_WBITS); data=dec.decompress(d[i:])
    except Exception as e: continue
    n+=1
    k=data.find(b"070707")
    if 0<=k<16:
        data=data[k:]
    if data[:6]==b"070707":
        for name,dd in cpio_entries(data):
            fn=os.path.join(out,'gz%d__'%n+name.replace('/','__').replace(':','_'))
            open(fn,'wb').write(dd)
            print('cpio',n,len(dd),name)
    else:
        fn=os.path.join(out,'gz%d.bin'%n); open(fn,'wb').write(data); print('gz',n,len(data),data[:60])
# plain text sections
txt=re.findall(rb'[\x09\x0a\x0d\x20-\x7e]{40,}',d)
open(os.path.join(out,'plaintext.txt'),'wb').write(b'\n-----\n'.join(txt))
print('plaintext blocks',len(txt))
