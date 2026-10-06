from pathlib import Path
import unreal,json,os,sys,hashlib
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BANK=ROOT/'Staging/BankIntegration_2026-10-04/ModularNative_2026-10-05'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
assert os.getpid()==21608
queue=read(BANK/'REPAIR_QUEUE_v004.json')
failed={r['native_package'] for r in queue['failures']}
dirty={p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}
assert dirty==failed and len(dirty)==6
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
assert all(not (ROOT/'Content'/(p[6:]+'.uasset')).exists() for p in failed)
assert not any(getattr(r,k,None) is not None for n in ('geocity_bank_workflow','geocity_roadbld_workflow') for r in getattr(sys.modules.get(n),'ACTIVE',[]) for k in ('watch_tick','save_tick','tick_handle'))
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
pins={}
for family in read(BANK/'RESUME_RESULT_v004.json')['families']:
    for p in read(BANK/'Receipts'/family['family_id']/'FAMILY.json')['parts']:pins.update(p['saved_packages'])
for p,expected in pins.items():assert hashlib.sha256((ROOT/'Content'/(p[6:]+'.uasset')).read_bytes()).hexdigest()==expected
receipt={'pid':os.getpid(),'utc':datetime.now(timezone.utc).isoformat(),'authorization':'Direct user: run the existing system as currently configured',
         'discard_only_failed_never_saved_import_buffers':sorted(failed),'unrelated_dirty_packages':[],
         'saved_import_packages':pins,'quit_method':'unreal.SystemLibrary.quit_editor','saves_requested':False}
(HERE/'IMPORT_EDITOR_EXIT.json').write_text(json.dumps(receipt,indent=2)+'\n')
unreal.SystemLibrary.quit_editor()
