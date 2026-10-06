import copy,datetime,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
child='/Game/Project/Shared/RoadBLD/Materials/MI_RoadBLD_Asphalt_Road_Worn_GeoCity'
assert json.loads((HERE/'FRESH_material_finish_20261003T203444712261Z.json').read_text())['status']=='passed'
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
preserve=HERE/('AsphaltProfilePreserve_'+stamp);preserve.mkdir()
rows=[]
for area,folder in [('GazaShujaiya','GazaShujaiyaIntegration_2026-10-02'),('GazaRimal','PermanentIntegration_2026-10-02')]:
    target=ROOT/'Staging/ModelBank'/folder/'AREA_PROFILE.json'
    raw=target.read_bytes();before=json.loads(raw.decode('utf-8-sig'));after=copy.deepcopy(before)
    assert after['roadbld_workflow']['enabled']
    after['roadbld_workflow'].setdefault('settings',{})['road_material']=child
    backup=preserve/(area+'_AREA_PROFILE.before.json');backup.write_bytes(raw)
    target.write_text(json.dumps(after,indent=2)+'\n',encoding='utf-8')
    actual=json.loads(target.read_text());assert actual==after
    restored=copy.deepcopy(actual)
    if 'settings' not in before['roadbld_workflow']:del restored['roadbld_workflow']['settings']
    elif 'road_material' not in before['roadbld_workflow']['settings']:del restored['roadbld_workflow']['settings']['road_material']
    else:restored['roadbld_workflow']['settings']['road_material']=before['roadbld_workflow']['settings']['road_material']
    assert restored==before
    rows.append(dict(area=area,path=str(target),backup=str(backup),before_sha256=hashlib.sha256(raw).hexdigest(),after_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),only_changed_field='roadbld_workflow.settings.road_material'))
receipt=HERE/('FRESH_ASPHALT_PROFILES_'+stamp+'.json')
receipt.write_text(json.dumps(dict(status='passed',child=child,profiles=rows),indent=2)+'\n')
print(str(receipt))
