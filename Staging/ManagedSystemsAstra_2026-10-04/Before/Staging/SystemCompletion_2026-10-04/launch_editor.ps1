param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration','/Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration')]
    [string]$AreaMap,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedMapSha256
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$taskLeasePath = Join-Path $taskRoot 'Staging\ModelBank\EDITOR_OWNER.txt'
$taskLease = (Get-Content -LiteralPath $taskLeasePath)[-1]
if ($taskLease -notmatch 'OWNER=NONE(?:\s|$)') { throw 'Another task owns the editor. No startup or lease takeover is permitted.' }
if (@(Get-Process UnrealEditor -ErrorAction SilentlyContinue).Count -ne 0) { throw 'An Unreal editor is already open. Preserve it and obtain an orderly clean release before startup.' }
$taskPython = Join-Path $taskRoot 'Content\Python'
$taskManifestPath = Join-Path $PSScriptRoot 'geocity_runtime_manifest.json'
$taskManifest = Get-Content -LiteralPath $taskManifestPath -Raw | ConvertFrom-Json
foreach ($taskEntry in $taskManifest.modules.PSObject.Properties) {
    $taskSource = Join-Path $taskPython $taskEntry.Value.file
    if ((Split-Path $taskSource -Parent) -ne $taskPython -or (Split-Path $taskSource -Leaf) -ne ($taskEntry.Name+'.py')) { throw 'Unscoped runtime source.' }
    if ((Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.Value.sha256) { throw ('Runtime source differs from the sealed manifest: '+$taskEntry.Name) }
}
$taskStartup = Join-Path $taskPython 'init_unreal.py'
if ((Get-FileHash -LiteralPath $taskStartup -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskManifest.startup.sha256) { throw 'Ordinary startup differs from the sealed manifest.' }
$taskMapFile = Join-Path $taskRoot ('Content\'+$AreaMap.Substring(6).Replace('/','\')+'.umap')
if ((Get-FileHash -LiteralPath $taskMapFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedMapSha256.ToLowerInvariant()) { throw 'The original saved map differs from the reviewed startup baseline.' }
$taskRestorePath = Join-Path $taskRoot 'Saved\Autosaves\PackageRestoreData.json'
if (Test-Path -LiteralPath $taskRestorePath) {
    $taskRestoreText = [System.Text.Encoding]::Unicode.GetString([System.IO.File]::ReadAllBytes($taskRestorePath)).TrimStart([char]0xFEFF)
    $taskRestore = $taskRestoreText | ConvertFrom-Json
    if (@($taskRestore.Packages).Count -ne 0) { throw 'Pending package recovery requires reconciliation before an original-map startup.' }
    if ($taskRestore.RestoreEnabled -ne $false) {
        $taskRestoreBackup = Join-Path $PSScriptRoot ('Before\PackageRestoreData_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ')+'.json')
        Copy-Item -LiteralPath $taskRestorePath -Destination $taskRestoreBackup
        $taskRestore.RestoreEnabled = $false
        [System.IO.File]::WriteAllText($taskRestorePath,($taskRestore | ConvertTo-Json -Depth 20),[System.Text.UnicodeEncoding]::new($false,$false))
    }
}
if ((Get-Content -LiteralPath $taskLeasePath)[-1] -ne $taskLease -or @(Get-Process UnrealEditor -ErrorAction SilentlyContinue).Count -ne 0) { throw 'Editor ownership changed during startup preparation.' }
$taskExecutable = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$taskProject = Join-Path $taskRoot 'Environmentpipeline.uproject'
$taskStart = [System.Diagnostics.ProcessStartInfo]::new()
$taskStart.FileName = $taskExecutable
$taskStart.WorkingDirectory = $taskRoot
$taskStart.UseShellExecute = $false
$taskStart.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$taskStart.CreateNoWindow = $true
$taskStart.Arguments = '"'+$taskProject+'" "'+$AreaMap+'" -NoAutoSave -NoRestoreOpenAssetTabs -ini:Engine:[/Script/HoudiniEngineRuntime.HoudiniRuntimeSettings]:bPauseCookingOnStart=True -ini:EditorPerProjectUserSettings:[/Script/UnrealEd.EditorLoadingSavingSettings]:bAutoSaveEnable=False,[/Script/UnrealEd.EditorLoadingSavingSettings]:RestoreOpenAssetTabsOnRestart=NeverRestore'
# The child process sees the normal project entrypoint, with no historical
# RecoveryBootstrap, replacement installer, generator or startup recovery.
$taskStart.EnvironmentVariables['UE_PYTHONPATH'] = $taskPython
$taskProcess = [System.Diagnostics.Process]::Start($taskStart)
$taskNewLease = [DateTime]::UtcNow.ToString('o')+' OWNER=CODEX_SYSTEM_COMPLETION manager_thread_id=01a1063d-1a66-7380-aec4-e0ac89c90829 task=ORDINARY_SYSTEM_COMPLETION assigned_editor_PID='+$taskProcess.Id+' scope=original_maps_normal_menu_named_saves_one_writer_bank_unchanged'
[System.IO.File]::AppendAllText($taskLeasePath,[Environment]::NewLine+$taskNewLease+[Environment]::NewLine)
$taskReceipt = @{pid=$taskProcess.Id; map=$AreaMap; map_sha256=$ExpectedMapSha256.ToLowerInvariant(); actual_pid_lease=$taskNewLease; sources_checked=$true; generation_started=$false; pause_before_python=$true; autosave=$false; original_map=$true}
$taskReceipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'LAUNCH_STATE.json') -Encoding utf8
$taskReceipt | ConvertTo-Json -Depth 5
