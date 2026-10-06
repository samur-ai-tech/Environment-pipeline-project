param(
    [Parameter(Mandatory=$true)][string]$ManagerActivation,
    [Parameter(Mandatory=$true)][string]$ExpectedBootstrapSha256,
    [Parameter(Mandatory=$true)][string]$ExpectedEntrySha256
)
$ErrorActionPreference = 'Stop'
if ($ManagerActivation -ne 'ROOT_ACTIVATED_REPLACEMENT_EDITOR_STARTUP') { throw 'Root launch activation is required.' }
$taskRoot = 'C:\Users\USER\Documents\Unreal Projects\Environmentpipeline'
$taskFolder = Join-Path $taskRoot 'Staging\ManagedAstra_2026-10-03'
$taskBootstrapFolder = Join-Path $taskFolder 'RecoveryBootstrap'
$taskBootstrap = Join-Path $taskBootstrapFolder 'recovery_startup.py'
$taskEntry = Join-Path $taskBootstrapFolder 'init_unreal.py'
$taskExe = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$taskProject = Join-Path $taskRoot 'Environmentpipeline.uproject'
$taskMap = '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration'
$taskMapFile = Join-Path $taskRoot 'Content\Project\Areas\GazaShujaiya\BankIntegration_v015\L_GazaShujaiya_BankIntegration.umap'
if (@(Get-Process UnrealEditor -ErrorAction SilentlyContinue).Count -ne 0) { throw 'An Unreal editor already exists; no launch.' }
foreach ($taskPath in @($taskExe,$taskProject,$taskBootstrap,$taskEntry,$taskMapFile)) { if (-not (Test-Path -LiteralPath $taskPath)) { throw "Required file missing: $taskPath" } }
if ((Get-FileHash -LiteralPath $taskBootstrap -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedBootstrapSha256) { throw 'Bootstrap hash differs.' }
if ((Get-FileHash -LiteralPath $taskEntry -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedEntrySha256) { throw 'Entrypoint hash differs.' }
if ((Get-FileHash -LiteralPath $taskMapFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'fe56a24d0eb493f70c3582c2167124b79d1930704be0bac8d33683c8d178c0e7') { throw 'Original saved map differs.' }
$taskConfigProof = Get-Content -LiteralPath (Join-Path $taskFolder 'TASK2_SAFE_STARTUP_CONFIG_RECEIPT.json') -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $taskConfigProof.project_config.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskConfigProof.project_config.after_sha256) { throw 'Reviewed early pause configuration differs.' }
if ((Get-FileHash -LiteralPath $taskConfigProof.recovery_manifest.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskConfigProof.recovery_manifest.after_sha256) { throw 'Reviewed disabled recovery manifest differs.' }
$taskRestoreText = [System.Text.Encoding]::Unicode.GetString([System.IO.File]::ReadAllBytes($taskConfigProof.recovery_manifest.path))
if (($taskRestoreText | ConvertFrom-Json).RestoreEnabled -ne $false) { throw 'Package recovery restore is not disabled.' }
$taskLaunchJournal = Join-Path $taskFolder ('REPLACEMENT_LAUNCH_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ') + '.jsonl')
function Write-TaskLaunchJournal([string]$EventName,[object]$Details) {
    $taskEntryText = @{ utc=[DateTime]::UtcNow.ToString('o'); event=$EventName; details=$Details } | ConvertTo-Json -Depth 5 -Compress
    [System.IO.File]::AppendAllText($taskLaunchJournal,$taskEntryText+[Environment]::NewLine)
}
$taskStartInfo = New-Object System.Diagnostics.ProcessStartInfo
$taskStartInfo.FileName = $taskExe
$taskStartupSettings = '-ini:EditorPerProjectUserSettings:[/Script/UnrealEd.EditorLoadingSavingSettings]:bAutoSaveEnable=False,[/Script/UnrealEd.EditorLoadingSavingSettings]:RestoreOpenAssetTabsOnRestart=NeverRestore'
$taskStartInfo.Arguments = '"' + $taskProject + '" "' + $taskMap + '" -NoAutoSave ' + $taskStartupSettings
$taskStartInfo.WorkingDirectory = $taskRoot
$taskStartInfo.UseShellExecute = $false
$taskStartInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$taskStartInfo.CreateNoWindow = $true
$taskExistingPythonPath = $taskStartInfo.EnvironmentVariables['UE_PYTHONPATH']
$taskStartInfo.EnvironmentVariables['UE_PYTHONPATH'] = if ($taskExistingPythonPath) { $taskBootstrapFolder + ';' + $taskExistingPythonPath } else { $taskBootstrapFolder }
$taskStartInfo.EnvironmentVariables['GEOCITY_RECOVERY_STARTUP_TOKEN'] = $ManagerActivation
Write-TaskLaunchJournal 'BEFORE_PROCESS_START' @{ executable=$taskExe; project=$taskProject; map=$taskMap; noAutoSave=$true; startupSettingsOverride=$taskStartupSettings; pauseCookingBeforePython=$true; bootstrap=$taskBootstrap; startupMechanism='process-scoped UE_PYTHONPATH/init_unreal.py'; restoreRecoveryPacks=$false }
$taskProcess = [System.Diagnostics.Process]::Start($taskStartInfo)
Write-TaskLaunchJournal 'AFTER_PROCESS_START' @{ pid=$taskProcess.Id; leaseAcquired=$false }
@{ pid=$taskProcess.Id; journal=$taskLaunchJournal; status='LAUNCHED_WAITING_BOOTSTRAP_ROOT_MUST_ACQUIRE_NEW_PID_LEASE' } | ConvertTo-Json
