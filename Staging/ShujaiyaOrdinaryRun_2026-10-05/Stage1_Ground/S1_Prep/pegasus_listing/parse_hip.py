import sys,os
def parse(path,outdir):
    d=open(path,'rb').read()
    p=0; ents=[]
    while p<len(d):
        h=d[p:p+76]
        if h[:6]!=b'070707': print('bad magic at',p,h[:20]); break
        ns=int(h[59:65],8); fs=int(h[65:76],8)
        name=d[p+76:p+76+ns-1].decode('latin1')
        data=d[p+76+ns:p+76+ns+fs]
        p=p+76+ns+fs
        if name=='TRAILER!!!': break
        ents.append((name,len(data)))
        fn=os.path.join(outdir,name.replace('/','__').replace(':','_'))
        open(fn,'wb').write(data)
    return ents
if __name__=='__main__':
    src,out=sys.argv[1],sys.argv[2]
    os.makedirs(out,exist_ok=True)
    e=parse(src,out)
    print(len(e),'entries')
    for n,s in e: print(s,n)
