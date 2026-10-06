from pathlib import Path
import json,hashlib
import hou
HERE=Path(__file__).resolve().parent
BASE=Path('C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank/revisions')
OLD=BASE/'20261005_modular_source_families_v001/GeoCity_city_v015_PermanentBank_ModularFamilies_v001.hdalc'
DEST=BASE/'20261005_modular_source_families_v002/GeoCity_city_v015_PermanentBank_ModularFamilies_v002.hdalc'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(OLD)=='b5ab917a11c9a4021835fee93df0dcf87a71931cd02f3efd3a90ec23bb735977'
hou.setUpdateMode(hou.updateMode.Manual)
definition=next(d for d in hou.hda.definitionsInFile(str(OLD)) if d.nodeTypeName()=='trackb::geocity_city::15.0')
source=definition.sections()['PythonModule'].contents()
old="""                            context[identity] = {'building_use': value.strip(), 'building_use_evidence': {
                                'source': 'identity_bound_original_pad_attribute', 'attribute': name,
                                'source_area_id': identity[0], 'source_osm_id': identity[1], 'verified': True}}"""
new="""                            raw_value = value.strip()
                            # OSM building=yes records existence, not a known use.
                            # Explicit use and specific building classes keep their guard.
                            generic = name in ('building_class', 'source_building_class') and raw_value == 'yes'
                            context[identity] = {'building_use': 'unknown' if generic else raw_value, 'building_use_evidence': {
                                'source': 'identity_bound_original_pad_attribute', 'attribute': name,
                                'raw_value': raw_value, 'generic_building_existence_only': generic,
                                'source_area_id': identity[0], 'source_osm_id': identity[1], 'verified': True}}"""
assert source.count(old)==1
updated=source.replace(old,new)
compile(updated,'geocity_city_module.py','exec')
DEST.parent.mkdir(parents=True,exist_ok=True)
if not DEST.exists():definition.copyToHDAFile(str(DEST))
hou.hda.installFile(str(DEST))
saved=next(d for d in hou.hda.definitionsInFile(str(DEST)) if d.nodeTypeName()==definition.nodeTypeName())
assert saved.sections()['PythonModule'].contents() in (source,updated)
saved.addSection('PythonModule',updated)
saved.save(str(DEST))
actual=next(d for d in hou.hda.definitionsInFile(str(DEST)) if d.nodeTypeName()==definition.nodeTypeName())
assert actual.sections()['PythonModule'].contents()==updated
assert set(actual.sections())==set(definition.sections())
for name,section in definition.sections().items():
    if name!='PythonModule':assert actual.sections()[name].binaryContents()==section.binaryContents(),name
assert sha(OLD)=='b5ab917a11c9a4021835fee93df0dcf87a71931cd02f3efd3a90ec23bb735977'
(DEST.parent/'geocity_city_module.py').write_text(updated,encoding='utf-8')
receipt={'source_before':str(OLD),'source_before_sha256':sha(OLD),'source_after':str(DEST),'source_after_sha256':sha(DEST),'change':'Interpret only identity-bound building_class=yes as unknown use; retain raw source evidence','other_definition_sections_unchanged':True,'cook_performed':False,'operator_thread_id':'01a10c77-46ba-7001-a657-5014f6205d3a'}
(HERE/'USE_FIX_BUILD.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt))
