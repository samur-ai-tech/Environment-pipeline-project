import bpy,sys,json
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
for name in ['Avocado','Lemon','Orange']:
 path=ROOT/'Blend'/(name+'.blend')
 bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
 bpy.context.preferences.filepaths.save_version=0
 for im in bpy.data.images:
  if im.filepath:im.filepath=bpy.path.relpath(im.filepath)
 # Keep each variant in a clearly named source collection.
 for ob in list(bpy.context.scene.objects):
  if not ob.name.startswith('SM_PazFarm_'):continue
  if 'manifest' in ob:ob['manifest']=ob['manifest'].replace('Variant B is clementine: smaller 64 mm fruit diameter versus 84 mm orange A.','Variant B is clementine, with smaller fruit than orange variant A.')
  if ob.name not in bpy.data.collections:
   col=bpy.data.collections.new(ob.name);bpy.context.scene.collection.children.link(col)
   for old in list(ob.users_collection):old.objects.unlink(ob)
   col.objects.link(ob)
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
 print('SOURCE_FINISHED',name)
for f in ['trees.json','trees_progress.json']:
 path=ROOT/'Reports'/f
 path.write_text(path.read_text().replace('Variant B is clementine: smaller 64 mm fruit diameter versus 84 mm orange A.','Variant B is clementine, with smaller fruit than orange variant A.'))
