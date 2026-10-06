"""Rerun retained task1 regressions without overwriting accepted receipts."""
from pathlib import Path
out=Path(__file__).resolve().parent/'BaselineRegression'
out.mkdir(exist_ok=True)
original=Path(__file__).resolve().parent.parent/'verify_source.py'
source=original.read_text(encoding='utf-8')
old='OUT=Path(__file__).resolve().parent'
assert source.count(old)==1
source=source.replace(old,old+"/'BankAuthority_Repair'/'BaselineRegression'")
exec(compile(source,str(original),'exec'),{'__file__':str(original),'__name__':'__main__'})
