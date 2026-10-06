import json
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
reg=unreal.AssetRegistryHelpers.get_asset_registry()
deps=reg.get_dependencies('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky',unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=False,include_soft_management_references=False,include_hard_management_references=False))
RESULT={'engine':unreal.SystemLibrary.get_engine_version(),'entry_asset':'/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky.BP_EnvironmentSky','dependencies':[str(d) for d in deps],'required_plugin':'SunPosition','project_plugin_enabled':True,'PWL_or_MW_dependency':False,'runtime_python_required':False,'migration':'Use Asset Actions > Migrate on BP_EnvironmentSky; enable Sun Position Calculator in the destination. Validated on this UE 5.8 project only.'}
assert not any('/Game/PWL' in str(d) or 'MWLandscape' in str(d) for d in deps)
(root/'DEPENDENCIES.json').write_text(json.dumps(RESULT,indent=2))
