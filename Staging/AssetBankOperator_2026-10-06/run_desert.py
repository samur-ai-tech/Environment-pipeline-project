from pathlib import Path
import unreal
p=Path(unreal.Paths.project_dir(),'Staging/AssetBankOperator_2026-10-06/native_operator.py')
ns={'__file__':str(p)}
exec(p.read_text(),ns)
ns['import_mounted']('BANK_EXPANSION_011','/Game/RealisticDesertPack/')
ns['validate_batch']('BANK_EXPANSION_011')
