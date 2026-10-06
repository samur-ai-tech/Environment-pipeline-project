"""Seal source bytes and current authority; does not issue native authorization."""
from pathlib import Path
from . import intake as I
from . import integrity as V
from . import authority as A

def seal():
    names=['intake.py','integrity.py','authority.py','native_supplier.py','source_migration.py','migration_remap.py','post_remap.py','qualification_intake.py','targeted_measurement.py','sealed_run.py']
    paths=[I.HERE/n for n in names]+[I.BANK/'bank_contracts.py',I.BANK/'native_bank_ops.py']
    m={'schema':'environmentpipeline.native_supply_command_manifest.v2','authority':A.authority(),
       'files':{str(p.resolve()):I.sha(p) for p in paths},'queue_sha256':I.sha(I.HERE/'READY_JOBS.json'),
       'native_authorization_granted':False,'policy':'Current manager must activate exact command/action/transaction and actual sole PID after native recovery.'}
    path=I.HERE/'CommandManifests'/(V.digest(m)+'.json');A.immutable_json(path,m)
    I.write('COMMAND_MANIFEST.json',{'path':str(path),'sha256':I.sha(path)})
    print(path)
    return path

if __name__=='__main__':seal()
