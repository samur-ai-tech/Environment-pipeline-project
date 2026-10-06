"""Offline-only maintenance in a fresh Python process; never import into Unreal."""
from pathlib import Path
import hashlib
import runpy
import sys

def main():
    assert 'unreal' not in sys.modules and Path(sys.executable).name.lower().startswith('python'),'offline_Python_only'
    here=Path(__file__).resolve().parent
    runner=runpy.run_path(str(here/'sealed_run.py'))
    names=['integrity','intake','authority','native_supplier','source_migration','migration_remap','sealed_run',
           'seal_commands','verify_supplier','qualification_intake','semantic_material_supply','publish_ready']
    files={str(here/(n+'.py')):hashlib.sha256((here/(n+'.py')).read_bytes()).hexdigest() for n in names}
    mods=runner['load_exact'](here,files,names)
    command=sys.argv[1] if len(sys.argv)>1 else 'verify'
    if command=='refresh':
        mods['intake'].build()
        mods['seal_commands'].seal()
        mods['verify_supplier'].verify()
        mods['qualification_intake'].build()
        mods['publish_ready'].build()
    elif command=='verify':mods['verify_supplier'].verify()
    elif command=='semantic':mods['semantic_material_supply'].build()
    elif command=='publish':mods['publish_ready'].build()
    else:raise ValueError(command)

if __name__=='__main__':main()
