"""Category-local input/receipt paths for the retained bank importer.

No Unreal operation or shared write occurs when importing this module.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREP = ROOT / 'Staging/BankPreparation_2026-10-04'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write(path, value):
    target = Path(path).resolve()
    assert target.is_relative_to(HERE), ('category_receipt_outside_scope', str(target))
    target.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def package_file(obj):
    assert obj.startswith('/Game/'), obj
    return ROOT / 'Content' / (obj.split('.')[0][6:] + '.uasset')
