"""Stage licensed source files from local Epic acquisition manifests; no editor or Content writes.
Uses retained Legendary readers (GPL-3.0; see IntakeTools/LICENSE). Never authenticates or decrypts.
"""
from pathlib import Path, PurePosixPath
import concurrent.futures, hashlib, json, sys, time, urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'IntakeTools'))
from legendary.models.manifest import Manifest
from legendary.models.json_manifest import JSONManifest
from legendary.models.chunk import Chunk
VAULT=Path('C:/ProgramData/Epic/EpicGamesLauncher/VaultCache/FabLibrary')
PACKS={
 'greasewood':'Megaplants__Greasewood-1b8d0a76',
 'giant_reed':'mediterranean_Vegetation__giant_Reed-b4c4cc88',
 'phoenix_palms':'Palms_Pack_02__Phoenix_canariensis_-cb98e62c',
 'desert':'Realistic_Desert_Pack-3d1ccab4',
 'namaqualand':'Namaqualand_Environment_and_Asset_Pack-295ed897',
 'seasons':'Procedural_Nature_Seasons_Pack-e1958643',
 'downtown':'Downtown_West_Modular_Pack-0faf8b5d',
}
def utc():return datetime.now(timezone.utc).isoformat()
def safe_file(root,rel):
 parts=PurePosixPath(rel).parts
 assert parts and not PurePosixPath(rel).is_absolute() and '..' not in parts
 f=(root/Path(*parts)).resolve();assert f.is_relative_to(root.resolve())
 # Windows long source names remain inside the checked staging root.
 return Path('\\\\?\\'+str(f)) if sys.platform=='win32' and not str(f).startswith('\\\\?\\') else f
def load(key):
 p=VAULT/PACKS[key]/'unreal-engine/manifest';raw=p.read_bytes()
 m=(JSONManifest if raw.startswith(b'{') else Manifest).read_all(raw)
 assert not m.encrypted,'Encrypted manifest requires official Launcher'
 return p,raw,m
def selected(m):
 return [f for f in m.file_manifest_list.elements if f.filename.startswith('Content/') and not any(x in f.filename.lower() for x in ['/maps/','/map/','/demo/','/demos/','/__externalactors__/','/__externalobjects__/','_builtdata.']) and f.filename.endswith(('.uasset','.ubulk','.uexp'))]
def plan(key):
 p,raw,m=load(key);files=selected(m)
 ids={part.guid_num for f in files for part in f.chunk_parts}
 chunks=[c for c in m.chunk_data_list.elements if c.guid_num in ids]
 return {'pack':key,'manifest':str(p),'manifest_sha256':hashlib.sha256(raw).hexdigest(),'source_files':len(files),'source_bytes':sum(f.file_size for f in files),'download_chunks':len(chunks),'download_bytes':sum(c.file_size for c in chunks)},m,files,chunks
def stage(key):
 spec,m,files,chunks=plan(key)
 dest=HERE/'OwnedPackSources'/key;cache=HERE/'OwnedPackChunks'/key
 dest.mkdir(parents=True,exist_ok=True);cache.mkdir(parents=True,exist_ok=True)
 manifest,raw,_=load(key);(dest/'acquisition.manifest').write_bytes(raw)
 bases=m.custom_fields._dict['BaseUrl'].split(',')
 for base in bases:
  u=urllib.parse.urlparse(base)
  assert u.scheme=='https' and u.hostname in ['egs-cloudfront-chunks.epicgamescdn.com','epicgames-download1.akamaized.net','egdownload.fastly-edge.com']
 started=time.monotonic();count=0;last=started
 print(json.dumps({'event':'starting','utc':utc(),**spec}),flush=True)
 def fetch(info):
  target=cache/(info.guid_str+'.raw')
  if target.exists() and hashlib.sha1(target.read_bytes()).digest()==info.sha_hash:return 'reused'
  error=None
  for base in bases:
   try:
    with urllib.request.urlopen(base.rstrip('/')+'/'+info.path,timeout=45) as r:blob=r.read()
    c=Chunk.read_buffer(blob)
    assert not c.encrypted,'Encrypted chunk requires official Launcher'
    data=c.data
    assert hashlib.sha1(data).digest()==info.sha_hash,'chunk SHA1 mismatch'
    tmp=target.with_suffix('.part');tmp.write_bytes(data);tmp.replace(target);return 'downloaded'
   except urllib.error.HTTPError as e:
    if e.code in [401,403]:raise RuntimeError(f'Official Launcher access required: HTTP {e.code}')
    error=e
   except Exception as e:error=e
  raise RuntimeError(type(error).__name__+': '+str(error)[:140])
 counts={'downloaded':0,'reused':0};errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  pending={pool.submit(fetch,c):c for c in chunks}
  for future in concurrent.futures.as_completed(pending):
   c=pending[future]
   try:counts[future.result()]+=1
   except Exception as e:errors.append({'chunk':c.guid_str,'error':str(e)})
   count+=1
   if time.monotonic()-last>20:
    print(json.dumps({'event':'download_progress','pack':key,'done':count,'total':len(chunks),'failed':len(errors)}),flush=True);last=time.monotonic()
 if errors:
  receipt={'pack':key,'status':'DOWNLOAD_INCOMPLETE','utc':utc(),**spec,'chunk_counts':counts,'errors':errors}
  (dest/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({'event':'failed','pack':key,'errors':len(errors)}),flush=True);return receipt
 results=[]
 for f in files:
  assert not f.symlink_target,'Source symlink not supported'
  target=safe_file(dest,f.filename);target.parent.mkdir(parents=True,exist_ok=True)
  if not target.exists() or hashlib.sha1(target.read_bytes()).digest()!=f.hash:
   temp=target.with_suffix(target.suffix+'.part');h=hashlib.sha1();size=0
   with temp.open('wb') as output:
    for part in f.chunk_parts:
     chunk_file=cache/(part.guid_str+'.raw')
     with chunk_file.open('rb') as inp:inp.seek(part.offset);data=inp.read(part.size)
     assert len(data)==part.size
     output.write(data);h.update(data);size+=len(data)
   assert size==f.file_size and h.digest()==f.hash,'Reconstructed source hash mismatch: '+f.filename
   temp.replace(target)
  results.append({'relative_path':f.filename,'path':str(target),'bytes':target.stat().st_size,'manifest_sha1':f.hash.hex(),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'hash_verified':True})
 receipt={'pack':key,'title':m.custom_fields._dict.get('Vault.TitleText'),'listing_url':m.custom_fields._dict.get('Vault.ActionURL') or m.custom_fields._dict.get('Vault.ActionUrl'),'status':'SOURCE_STAGED_HASH_VERIFIED_NOT_NATIVE_IMPORTED','utc':utc(),**spec,'chunk_counts':counts,'elapsed_seconds':round(time.monotonic()-started,1),'licence_basis':'Aviv ownership/licence confirmation 2026-10-06 for technical source preparation; exact acquisition terms pending owner check; no hold release','files':results,'editor_operations':0,'source_vendor_modified':False}
 (dest/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'event':'complete','pack':key,'files':len(results),'seconds':receipt['elapsed_seconds']}),flush=True)
 return receipt
if __name__=='__main__':
 keys=[x for x in sys.argv[1:] if x!='--plan'] or ['greasewood','giant_reed','phoenix_palms','desert','namaqualand']
 if '--plan' in sys.argv:print(json.dumps([plan(k)[0] for k in keys],indent=2))
 else:
  for key in keys:
   try:stage(key)
   except Exception as e:
    import traceback
    (HERE/('STAGE_FAILURE_'+key+'.txt')).write_text(traceback.format_exc(),encoding='utf-8')
    print(json.dumps({'event':'pack_failed','pack':key,'error':type(e).__name__+': '+str(e)[:160]}),flush=True)
