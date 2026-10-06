"""Resume prepared jobs; keep exact per-asset failures separate from saved imports."""
import json
import runpy
import types
import bank_contracts as C
native=types.SimpleNamespace(**runpy.run_path(str(C.HERE/'native_bank_ops.py')))
importer=runpy.run_path(str(C.HERE/'import_prepared.py'))
importer['import_one'].__globals__['N']=native

def run(start,stop):
    results=[]
    for job in C.read(C.HERE/'EXTERNAL_IMPORT_QUEUE.json')[start:stop]:
        aid=job['asset_id']
        try:
            report=importer['import_one'](aid)
            results.append({'asset_id':aid,'saved':report['saved']})
        except Exception as exc:
            progress=C.read(C.HERE/'NATIVE_IMPORT_PROGRESS.json')
            progress.update(error=repr(exc),dirty=native.dirty())
            assert progress['asset_id']==aid
            C.write(C.HERE/('IMPORT_PENDING_'+aid.replace('.','_')+'.json'),progress)
            results.append({'asset_id':aid,'saved':False,'error':repr(exc)})
    C.write(C.HERE/('IMPORT_BATCH_'+str(start)+'_'+str(stop)+'.json'),results)
    print(json.dumps({'saved':sum(r['saved'] for r in results),'failures':[r for r in results if not r['saved']]}))
    return results
