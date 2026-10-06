param(
    [Parameter(Mandatory=$true)][string]$ActivationPath,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedActivationSha256
)
$ErrorActionPreference='Stop'
$modularProjectRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
function Get-Sha([string]$File) { return (Get-FileHash -LiteralPath $File -Algorithm SHA256).Hash.ToLowerInvariant() }
if ((Get-Sha $ActivationPath) -ne $ExpectedActivationSha256.ToLowerInvariant()) { throw 'Startup authority changed.' }
$modularAuthority=Get-Content -Raw -LiteralPath $ActivationPath | ConvertFrom-Json
if ($modularAuthority.status -ne 'MODULAR_STARTUP_AUTHORIZED' -or $modularAuthority.startup_authorized -ne $true -or $modularAuthority.native_authorized_now -ne $false -or $modularAuthority.ordinary_generation_authorized -ne $false) { throw 'Only bounded startup inspection is authorized.' }
if ($modularAuthority.manager_thread_id -ne '01a10789-2e6a-7321-ad85-0a2964f8a937' -or $modularAuthority.operator_thread_id -ne '01a1067c-5012-7550-b449-015b53c9d726') { throw 'Wrong manager/operator.' }
if ((Get-Sha $modularAuthority.resumption_path) -ne $modularAuthority.resumption_sha256) { throw 'Bounded human resumption receipt changed.' }
if ($modularAuthority.world -notin @('/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration','/Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration')) { throw 'Original area required.' }
if ((Get-Sha $PSCommandPath) -ne $modularAuthority.launcher_sha256) { throw 'Unreviewed startup entry.' }
if ((Get-Sha $modularAuthority.request_path) -ne $modularAuthority.request_sha256) { throw 'Import request changed.' }
$modularRequest=Get-Content -Raw -LiteralPath $modularAuthority.request_path | ConvertFrom-Json
if ($modularRequest.family_count -ne 20 -or $modularRequest.part_count -ne 609) { throw 'Bounded source scope differs.' }
foreach ($entry in $modularRequest.python_sources.PSObject.Properties) { if ((Get-Sha $entry.Name) -ne $entry.Value) { throw ('Import source changed: '+$entry.Name) } }
$modularLeasePath=Join-Path $modularProjectRoot 'Staging/ModelBank/EDITOR_OWNER.txt'
$modularLease=@(Get-Content -LiteralPath $modularLeasePath | Where-Object { $_.Trim() })[-1]
if ($modularLease -notmatch 'OWNER=NONE(?:\s|$)') { throw 'Editor owned by another task.' }
if (@(Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue).Count -ne 0) { throw 'An editor already runs; window cap is one.' }
$modularManifestPath=Join-Path $modularProjectRoot 'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
if ((Get-Sha $modularManifestPath) -ne $modularAuthority.manifest_sha256) { throw 'Runtime seal changed.' }
$modularManifest=Get-Content -Raw -LiteralPath $modularManifestPath | ConvertFrom-Json
if ($modularManifest.schema -ne 'environmentpipeline.geocity_runtime_sources.v2' -or @($modularManifest.modules.PSObject.Properties).Count -ne 12) { throw 'Exact12module runtime seal required.' }
$modularPython=Join-Path $modularProjectRoot 'Content/Python'
foreach ($entry in $modularManifest.modules.PSObject.Properties) {
    if ($entry.Value.file -ne ($entry.Name+'.py')) { throw 'Noncanonical source path.' }
    if ((Get-Sha (Join-Path $modularPython $entry.Value.file)) -ne $entry.Value.sha256) { throw ('Runtime source changed: '+$entry.Name) }
}
if ($modularManifest.startup.file -ne 'init_unreal.py' -or (Get-Sha (Join-Path $modularPython 'init_unreal.py')) -ne $modularManifest.startup.sha256) { throw 'Startup source changed.' }
foreach ($entry in $modularManifest.support_files.PSObject.Properties) { if ((Get-Sha (Join-Path $modularProjectRoot $entry.Name)) -ne $entry.Value) { throw ('Sealed support changed: '+$entry.Name) } }
$modularMapFile=Join-Path $modularProjectRoot ('Content/'+$modularAuthority.world.Substring(6)+'.umap')
if ((Get-Sha $modularMapFile) -ne $modularAuthority.map_sha256) { throw 'Current saved ground/map changed.' }
if ((Get-Sha $modularAuthority.profile_path) -ne $modularAuthority.profile_sha256) { throw 'Profile changed.' }
if ((Get-Content -Raw -LiteralPath $modularAuthority.profile_path | ConvertFrom-Json).map -ne $modularAuthority.world) { throw 'Profile/map mismatch.' }
if ((Get-Sha $modularAuthority.preservation_path) -ne $modularAuthority.preservation_sha256) { throw 'Preservation baseline changed.' }
$modularPreservation=Get-Content -Raw -LiteralPath $modularAuthority.preservation_path | ConvertFrom-Json
if ($modularPreservation.schema -ne 'environmentpipeline.modular_native_preservation.v1' -or @($modularPreservation.files.PSObject.Properties).Count -lt 16) { throw 'Missing current ground/map preservation pins.' }
foreach ($entry in $modularPreservation.files.PSObject.Properties) { if ((Get-Sha $entry.Name) -ne $entry.Value.ToLowerInvariant()) { throw ('Protected file changed: '+$entry.Name) } }
$modularRestore=Join-Path $modularProjectRoot 'Saved/Autosaves/PackageRestoreData.json'
if (Test-Path -LiteralPath $modularRestore) {
    $restoreText=[System.Text.Encoding]::Unicode.GetString([System.IO.File]::ReadAllBytes($modularRestore)).TrimStart([char]0xFEFF)
    $restoreState=$restoreText | ConvertFrom-Json
    if (@($restoreState.Packages).Count -ne 0) { throw 'Pending recovery must be reconciled; no automatic discard.' }
}
if ((Get-Sha $ActivationPath) -ne $ExpectedActivationSha256.ToLowerInvariant() -or @(Get-Content -LiteralPath $modularLeasePath | Where-Object { $_.Trim() })[-1] -ne $modularLease -or @(Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue).Count -ne 0) { throw 'Authority/editor ownership changed before startup.' }
$modularStart=[System.Diagnostics.ProcessStartInfo]::new()
$modularStart.FileName='C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$modularStart.WorkingDirectory=$modularProjectRoot
$modularStart.UseShellExecute=$false
$modularStart.WindowStyle=[System.Diagnostics.ProcessWindowStyle]::Hidden
$modularStart.CreateNoWindow=$true
$modularStart.Arguments='"'+(Join-Path $modularProjectRoot 'Environmentpipeline.uproject')+'" "'+$modularAuthority.world+'" -NoAutoSave -NoRestoreOpenAssetTabs -ini:Engine:[/Script/HoudiniEngineRuntime.HoudiniRuntimeSettings]:bPauseCookingOnStart=True -ini:EditorPerProjectUserSettings:[/Script/UnrealEd.EditorLoadingSavingSettings]:bAutoSaveEnable=False,[/Script/UnrealEd.EditorLoadingSavingSettings]:RestoreOpenAssetTabsOnRestart=NeverRestore'
$modularStart.EnvironmentVariables['UE_PYTHONPATH']=$modularPython
$modularProcess=[System.Diagnostics.Process]::Start($modularStart)
$modularNewLease=[DateTime]::UtcNow.ToString('o')+' OWNER=CODEX_MANAGED_SYSTEMS_STARTUP manager_thread_id='+$modularAuthority.manager_thread_id+' operator_thread_id='+$modularAuthority.operator_thread_id+' task=modular_bank assigned_editor_PID='+$modularProcess.Id+' map='+$modularAuthority.world+' activation=MODULAR_STARTUP_INSPECTION_ONLY scope=20families609parts_paused_startup native_authorized_now=false ordinary_generation_authorized=false'
[System.IO.File]::AppendAllText($modularLeasePath,[Environment]::NewLine+$modularNewLease+[Environment]::NewLine)
$modularReceipt=@{pid=$modularProcess.Id;world=$modularAuthority.world;activation_path=$ActivationPath;activation_sha256=$ExpectedActivationSha256;request_sha256=$modularAuthority.request_sha256;manifest_sha256=$modularAuthority.manifest_sha256;preservation_sha256=$modularAuthority.preservation_sha256;lease=$modularNewLease;native_authorized_now=$false;pause_on_start=$true;autosave=$false;content_or_map_saved=$false}
$modularReceipt | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 -LiteralPath (Join-Path $PSScriptRoot ('LAUNCH_PID'+$modularProcess.Id+'.json'))
$modularReceipt | ConvertTo-Json -Depth 5
