"""Root offline preparation; reads Content, writes only scoped Staging plan/backup/ARGS."""
import hashlib,json,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];REV=HERE/'Revision_2026-10-05'
def sha(file):return hashlib.sha256(Path(file).read_bytes()).hexdigest()
def read(file):return json.loads(Path(file).read_text(encoding='utf-8-sig'))
def write(file,data):
    assert not file.exists(),file
    file.write_text(json.dumps(data,indent=2),encoding='utf-8')
pid=int(sys.argv[1]);baseline=HERE/('GazaRimal_r031_before_epic_PID'+str(pid)+'.json')
base=read(baseline);assert base['pid']==pid and base['area']=='GazaRimal'
assert base['dirty_maps']==base['dirty_content']==[] and base['graph_expression_count']==1015
reference=REV/'EPIC_RESIDENT_CONSUMER_verify_r030_fresh_reopen_PID18844.json'
shared=read(reference);assert sha(reference)=='18eacb5f538be6bfb53bd3749bfc0d39a268947896ecc8d42cb8a51339e6017b'
saved=REV/'EPIC_RESIDENT_CONSUMER_NAMED_SAVE_GazaShujaiya_r030_epic_complete_PID26820.json'
assert sha(saved)=='0939c4a2f543367c775ca780c4f40b10ddd602d1261094a06b2986bec8edce8e'
original=REV/'EPIC_GROUND_verify_GazaShujaiya_r027_fresh_reopen_PID26820.json'
consumer=REV/'EPIC_NATIVE_CONSUMER_CLOSURE_R030.json'
palette=dict(read(consumer)['bindings'],Ground_MacroMask='/Game/StarterContent/Textures/T_MacroVariation.T_MacroVariation')
plan={'schema':'environmentpipeline.epic_resident_consumer_rimal_plan.v1','pid':pid,'world':base['world'],'area':'GazaRimal',
      'textures':palette,'scalars':{k+'_Roughness':.8 for k in ('Sand_01','Sand_02','Dirt_Path','Sand_Path')},
      'vectors':read(original)['plan']['vectors'],'shared_reference_sha256':sha(reference),
      'epic_native_receipt_sha256':'9b7785af647a3eaf5674cf45c8f1b56aa9d80da1f02d0848da46ebad391598b6',
      'original_reference_sha256':sha(original),'resident_save_sha256':sha(saved),'consumer_plan_sha256':sha(consumer)}
plan['scalars'].update(GeoCity_CellScale=1,Ground_SoilBlendStrength=.1,Sand_01_FarScale=2,Dirt_Path_NormalStrength=.2)
plan_file=REV/'EPIC_RIMAL_CONSUMER_PLAN_R031.json';write(plan_file,plan)
target=(ROOT/'Content/Project/Areas/GazaRimal/BankIntegration_v015/Materials/MI_GeoCityGround.uasset').resolve(strict=True)
assert sha(target)==shared['package_sha256'][str(target)]
backup_dir=REV/'EpicRimalBefore_R031';backup_dir.mkdir(exist_ok=False)
backup_copy=backup_dir/target.name;shutil.copy2(target,backup_copy);assert sha(backup_copy)==sha(target)
backup_file=REV/'EPIC_RIMAL_CONSUMER_BACKUP_R031.json'
write(backup_file,{'ready':True,'ready_for_epic_resident_rimal_binding':True,'pid':pid,'world':base['world'],
      'execution_thread_id':'01a10883-481f-7723-bdaa-fed004f15ef1','plan_sha256':sha(plan_file),
      'file_bindings':{str(target):{'backup':str(backup_copy),'sha256':sha(target)}}})
files={'baseline_receipt':baseline,'shared_reference':reference,
       'epic_native_receipt':REV/'EPIC_STARTER_GROUND_NATIVE_READONLY_PID32464.json',
       'source_manifest':REV/'STOCHASTIC_BACKUP_MANIFEST.json','mutation_backup':backup_file,'plan_receipt':plan_file,
       'original_reference':original,'resident_creation':REV/'EPIC_RESIDENT_CONSUMER_apply_r030_consumer_create_two_PID26820.json',
       'resident_ready':REV/'EPIC_RESIDENT_CONSUMER_inspect_r030_consumer_four_ready_PID26820.json',
       'resident_binding':REV/'EPIC_RESIDENT_CONSUMER_bind_r030_complete_epic_bind_PID26820.json','resident_save':saved,
       'resident_failure':REV/'EPIC_RESIDENT_apply_r028_create_only_PID26820.json',
       'resident_previous_failure':REV/'EPIC_RESIDENT_RECOVERY_apply_r028_recovery_create_three_PID26820.json',
       'resident_copy_state':REV/'EPIC_COPY_READ_ONLY_r028_recovery_gamma_stop_PID26820.json',
       'resident_gamma_failure':REV/'EPIC_RESIDENT_GAMMA_apply_r029_gamma_create_two_PID26820.json','consumer_plan_receipt':consumer}
args={'mode':'inspect','label':'r031_epic_before_binding','expected_pid':pid,
      'held_copy_package_sha256':'373286998d7fd485d3d2f3fad44c2a5d6ec8093fd79b7b4f20727a0c93113ed5',
      'shared_reference_helper_sha256':'691d33b3b7ead57a132f2b8354c9f2e0d5eaaed80cc1168ccc9feffcd4ba4fb0',
      'resident_save_helper_sha256':'3814bb161862ce1514b518a7b2ca0c5d70da6f414c0035ba83992871a4a8f95d'}
for key,file in files.items():args[key]=str(file);args[key+'_sha256']=sha(file)
arg_file=HERE/'ARGS_epic_rimal_consumer_inspect.json';write(arg_file,args)
print(json.dumps({'args':str(arg_file),'plan_sha256':sha(plan_file),'backup_sha256':sha(backup_file)}))
