"""Regenerate original PBR formulae at the required 1K, without altering model geometry."""
import bpy,sys,json
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import paz_common as p
p.reset()
for species,color in {'Avocado':(.062,.10,.019),'Lemon':(.92,.70,.029),'Orange':(.95,.29,.009)}.items():
 p.pbr(species+'Fruit',color,.42,kind='noise',res=1024)
p.pbr('NetBinding',(.30,.31,.28),.77,0,'noise',res=1024)
p.pbr('GreenhouseFilmSeam',(.61,.69,.66),.50,0,'film',res=1024,alpha=.62)
receipts=[]
for family in ['Avocado','Lemon','Orange','NetHouse','Greenhouse']:
 path=p.ROOT/'Blend'/(family+'.blend')
 bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
 bpy.context.preferences.filepaths.save_version=0
 texture_info=[]
 for im in bpy.data.images:
  if not im.filepath:continue
  resolved=Path(bpy.path.abspath(im.filepath)).resolve()
  assert resolved.is_relative_to(p.ROOT.resolve()),resolved
  if not resolved.exists():raise RuntimeError(str(resolved))
  im.source='FILE';im.reload();im.filepath=bpy.path.relpath(str(resolved))
  texture_info.append({'name':im.name,'size':list(im.size),'relative':im.filepath.startswith('//')})
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
 receipts.append({'family':family,'textures':texture_info})
(p.ROOT/'Reports/texture_resolution_refresh.json').write_text(json.dumps(receipts,indent=2))
print('REGENERATED_FROM_ORIGINAL_FORMULAE_1K',len(receipts),'families')
