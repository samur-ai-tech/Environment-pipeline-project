"""Run retained lifecycle regressions against staging without replacing runtime."""
from pathlib import Path
OUT=Path(__file__).resolve().parent
original=OUT.parent/'verify_source.py'
source=original.read_text()
source=source.replace('OUT=Path(__file__).resolve().parent','OUT=Path('+repr(str(OUT/'BaselineRegression'))+')')
source=source.replace("bank_path=ROOT/'Content/Python/geocity_bank_workflow.py'",'bank_path=Path('+repr(str(OUT/'geocity_bank_workflow.py'))+')')
(OUT/'BaselineRegression').mkdir(exist_ok=True)
exec(compile(source,str(original),'exec'),{'__file__':str(original),'__name__':'__main__'})
