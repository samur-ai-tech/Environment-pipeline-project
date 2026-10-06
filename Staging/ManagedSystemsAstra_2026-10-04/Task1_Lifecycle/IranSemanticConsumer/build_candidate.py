"""Compose staging only against exact retained lifecycle baseline."""
import ast
import difflib
import hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
baseline=OUT/'Before/geocity_bank_workflow.py'
source=baseline.read_text(encoding='utf-8')
assert hashlib.sha256(baseline.read_bytes()).hexdigest()=='f349d1289b8344e72339babddf80d538405a65a2ad31243ddc167d70b87022ce'
def replace(old,new,count=1):
    global source
    assert source.count(old)==count,(old,source.count(old))
    source=source.replace(old,new)
helpers=(OUT/'lifecycle_helpers.py').read_text()
helpers=helpers[helpers.index('def _consumer_json'):]
replace('class GeoCityRun:',helpers+'\nclass GeoCityRun:')
replace('    def configure_and_bind(self,w):',(OUT/'lifecycle_methods.py').read_text()+'\n    def configure_and_bind(self,w):')
replace('        self.guard_processes()\n        w.set_auto_cooking_enabled(False)',
        '        self.guard_processes()\n        consumer_strings=self.consumer_parameter_strings(w)\n        w.set_auto_cooking_enabled(False)')
replace("        for name,value in strings.items():", "        strings.update(consumer_strings)\n        for name,value in strings.items():")
replace("        for name,value in bools.items():", "        self.state['consumer_parameter_readback']={name:w.get_string_parameter_value(name) for name in consumer_strings}\n        self.write()\n        for name,value in bools.items():")
replace("            self.state['outputs']=outputs", "            self.verify_consumer_receipt(receipt)\n            self.state['outputs']=outputs")
# Keep both 120s waits and all prior native counts/Bake/save gates unchanged.
replace("if self.p.get('landscape_grass',{}).get('enabled'):","if self.p.get('landscape_grass',{}).get('enabled') or self.p.get('landscape_semantics') is not None:",3)
replace("if (self.p.get('landscape_grass',{}).get('enabled')\n", "if ((self.p.get('landscape_grass',{}).get('enabled') or self.p.get('landscape_semantics') is not None)\n")
replace("                grass=geocity_landscape_workflow.verify_landscape(self,landscapes[0],json.loads(self.receipt.read_text()))",
        "                complete_receipt=json.loads(self.receipt.read_text())\n                self.verify_consumer_receipt(complete_receipt)\n                grass=geocity_landscape_workflow.verify_landscape(self,landscapes[0],complete_receipt)")
replace("        self.state['landscape_grass_connection']=geocity_landscape_workflow.prepare(self)\n",
        "        self.state['landscape_grass_connection']=geocity_landscape_workflow.prepare(self)\n        if self.p.get('landscape_semantics') is not None:\n            self.state['semantic_native_binding']=_semantic_prepared_binding(self.p,self.state['landscape_grass_connection'])\n        self.write()\n")
replace("        self.state['reviewed_dirty_packages']=sorted(self.reviewed_dirty_packages)\n",
        "        self.state['reviewed_dirty_packages']=sorted(self.reviewed_dirty_packages)\n        if self.p.get('building_rules_json') is not None:\n            self.state['building_rules_binding']=_building_rules_binding(self.p)\n")
ast.parse(source)
candidate=OUT/'geocity_bank_workflow.py'
candidate.write_text(source,encoding='utf-8')
(OUT/'SOURCE_PATCH.diff').write_text(''.join(difflib.unified_diff(baseline.read_text().splitlines(True),source.splitlines(True),fromfile='Content/Python/geocity_bank_workflow.py',tofile='Content/Python/geocity_bank_workflow.py')),encoding='utf-8')
assert (ROOT/'Content/Python/geocity_bank_workflow.py').read_bytes()==baseline.read_bytes()
print(hashlib.sha256(candidate.read_bytes()).hexdigest())
