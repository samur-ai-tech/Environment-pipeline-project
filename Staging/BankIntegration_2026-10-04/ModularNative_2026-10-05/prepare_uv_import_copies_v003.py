"""Create FBX import derivatives by changing only reserved UV layer NAME bytes."""
import json,hashlib,struct,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
sha=lambda data:hashlib.sha256(data).hexdigest()
def nodes(data):
 assert data[:23]==b'Kaydara FBX Binary  \x00\x1a\x00'
 version=struct.unpack_from('<I',data,23)[0];fmt='<QQQB' if version>=7500 else '<IIIB';size=struct.calcsize(fmt);out=[]
 def walk(pos,ancestors):
  end,nprops,nbytes,nlen=struct.unpack_from(fmt,data,pos)
  if end==0:return None
  assert pos<end<=len(data)
  name=data[pos+size:pos+size+nlen];ps=pos+size+nlen;pe=ps+nbytes
  assert pe<=end
  out.append((ancestors+(name,),ps,pe,nprops))
  p=pe
  while p<end-size:
   following=walk(p,ancestors+(name,))
   if following is None:break
   p=following
  return end
 p=27
 while True:
  q=walk(p,())
  if q is None:break
  p=q
 return version,out
r=json.loads((HERE/'NATIVE_IMPORT_REQUEST_v002.json').read_text());receipt={'schema':'environmentpipeline.name_only_fbx_uv_import_copies.v1','parts':{},'source_modified':False,'numeric_geometry_uv_normal_tangent_material_bytes_unchanged':True,'native_import_validated':False}
for family in r['families']:
 if family['id'] in ('H0910','H0911'):continue
 for part in family['parts']:
  source=Path(part['fbx']);raw=source.read_bytes();assert sha(raw)==part['fbx_sha256']
  version,tree=nodes(raw);patches=[]
  for path,ps,pe,count in tree:
   if len(path)<2 or path[-2:]!=(b'LayerElementUV',b'Name'):continue
   assert count==1 and raw[ps:ps+1]==b'S'
   n=struct.unpack_from('<I',raw,ps+1)[0];assert ps+5+n==pe
   value=raw[ps+5:pe]
   if re.fullmatch(rb'UVChannel_[0-9]+',value):
    replacement=b'SourceAux_'+value[len(b'UVChannel_'):];assert len(replacement)==len(value)
    patches.append({'start':ps+5,'end':pe,'old':value.decode(),'new':replacement.decode(),'tree_path':[x.decode() for x in path]})
  if not patches:continue
  modified=bytearray(raw)
  for p in patches:modified[p['start']:p['end']]=p['new'].encode()
  modified=bytes(modified);assert len(raw)==len(modified)
  cursor=0;unchanged=hashlib.sha256()
  for p in sorted(patches,key=lambda x:x['start']):
   assert raw[cursor:p['start']]==modified[cursor:p['start']]
   unchanged.update(raw[cursor:p['start']]);cursor=p['end']
  assert raw[cursor:]==modified[cursor:];unchanged.update(raw[cursor:])
  v2,t2=nodes(modified);assert version==v2 and tree==t2
  dest=HERE/'UVImportCopies'/family['id']/(part['name']+'.fbx');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(modified)
  assert dest.read_bytes()==modified and sha(source.read_bytes())==part['fbx_sha256']
  receipt['parts'][part['name']]={'original_fbx':str(source),'original_sha256':part['fbx_sha256'],'import_fbx':str(dest),'import_fbx_sha256':sha(modified),'fbx_version':version,'file_size':len(raw),'name_patches':patches,'all_other_bytes_identical':True,'unchanged_bytes_sha256':unchanged.hexdigest(),'tree_layout_identical':True,'geometry_reexported':False}
 print('UV_NAME_COPIES',family['id'],flush=True)
(HERE/'UV_IMPORT_ADAPTATION_v003.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'copy_count':len(receipt['parts']),'receipt_sha256':sha((HERE/'UV_IMPORT_ADAPTATION_v003.json').read_bytes())}))
