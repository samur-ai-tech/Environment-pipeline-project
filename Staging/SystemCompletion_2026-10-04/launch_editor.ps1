param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration','/Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration')]
    [string]$AreaMap,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedMapSha256,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedManifestSha256,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedProfileSha256,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9-]{36}$')][string]$ManagerThreadId,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9-]{36}$')][string]$OperatorThreadId
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$taskAssignments = Get-Content -LiteralPath (Join-Path $taskRoot 'Staging\ManagedSystemsAstra_2026-10-04\ASSIGNMENTS.json') -Raw | ConvertFrom-Json
$taskWriter = @($taskAssignments.tasks | Where-Object { $_.id -eq 'task4' })
if ($ManagerThreadId -ne $taskAssignments.manager_thread_id -or $taskWriter.Count -ne 1 -or -not $taskWriter[0].thread_id) { throw 'Startup requires the current manager and an unambiguous managed assignment.' }
$taskOperatorRole = 'task4'
$taskScopeHashes = @{}
if ($OperatorThreadId -ne $taskWriter[0].thread_id) {
    $taskBankScope = 'Staging/BankIntegration_2026-10-04/ASSIGNMENT.json'
    $taskBankActivation = 'Staging/ManagedSystemsAstra_2026-10-04/BANK_ACTIVATION.json'
    foreach ($taskScopePath in @($taskBankScope,$taskBankActivation)) {
        $taskScopeHashes[$taskScopePath] = (Get-FileHash -LiteralPath (Join-Path $taskRoot $taskScopePath) -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $taskBank = Get-Content -LiteralPath (Join-Path $taskRoot $taskBankScope) -Raw | ConvertFrom-Json
    $taskActivation = Get-Content -LiteralPath (Join-Path $taskRoot $taskBankActivation) -Raw | ConvertFrom-Json
    if ($taskBank.schema -ne 'environmentpipeline.bank_integration.v1' -or $taskActivation.schema -ne 'environmentpipeline.manager_bank_activation.v1' -or $taskBank.system_owner -ne $ManagerThreadId -or $taskActivation.manager_thread_id -ne $ManagerThreadId -or $taskBank.thread -ne $OperatorThreadId -or $taskActivation.bank_thread_id -ne $OperatorThreadId -or $taskActivation.scope_receipt -ne $taskBankScope) { throw 'Bank startup identities or scope receipts differ from the current manager assignment.' }
    $taskBankPaths = @('/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4','/Game/Project/Shared/ModelBank/Prepared','/Game/Project/Shared/ModelBank/Materials/BankIntegration_20261004')
    foreach ($taskScope in @($taskBank,$taskActivation)) {
        $taskExactBankPaths = @($taskScope.native_save_scope | Where-Object { $_ -like '/Game/*' })
        if (@(Compare-Object $taskExactBankPaths $taskBankPaths).Count) { throw 'Bank startup requires the exact retained catalog/import/material scope.' }
    }
    $taskOperatorRole = 'bank'
}
if ($AreaMap -notin $taskAssignments.native_area_maps) { throw 'Map is outside the managed original areas.' }
$taskLeasePath = Join-Path $taskRoot 'Staging\ModelBank\EDITOR_OWNER.txt'
$taskLease = (Get-Content -LiteralPath $taskLeasePath)[-1]
if ($taskLease -notmatch 'OWNER=NONE(?:\s|$)') { throw 'Another task owns the editor. No startup or lease takeover is permitted.' }
if (@(Get-Process UnrealEditor -ErrorAction SilentlyContinue).Count -ne 0) { throw 'An Unreal editor is already open. Preserve it and obtain an orderly clean release before startup.' }
$taskPython = Join-Path $taskRoot 'Content\Python'
$taskManifestPath = Join-Path $PSScriptRoot 'geocity_runtime_manifest.json'
if ((Get-FileHash -LiteralPath $taskManifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedManifestSha256.ToLowerInvariant()) { throw 'Combined seal differs from the manager-reviewed manifest.' }
$taskManifest = Get-Content -LiteralPath $taskManifestPath -Raw | ConvertFrom-Json
if ($taskManifest.schema -ne 'environmentpipeline.geocity_runtime_sources.v2' -or $taskManifest.startup.file -ne 'init_unreal.py') { throw 'Expected combined startup/configuration seal v2.' }
$taskProfiles = @(Get-ChildItem -Path (Join-Path $taskRoot 'Staging\ModelBank\*\AREA_PROFILE.json') -File | Where-Object { (Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json).map -eq $AreaMap })
if ($taskProfiles.Count -ne 1) { throw 'The named original map requires exactly one canonical profile.' }
if ((Get-FileHash -LiteralPath $taskProfiles[0].FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedProfileSha256.ToLowerInvariant()) { throw 'Current-map profile differs from the reviewed baseline.' }
foreach ($taskEntry in $taskManifest.modules.PSObject.Properties) {
    $taskSource = Join-Path $taskPython $taskEntry.Value.file
    if ((Split-Path $taskSource -Parent) -ne $taskPython -or (Split-Path $taskSource -Leaf) -ne ($taskEntry.Name+'.py')) { throw 'Unscoped runtime source.' }
    if ((Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.Value.sha256) { throw ('Runtime source differs from the sealed manifest: '+$taskEntry.Name) }
}
$taskSupportNames = @('Config/DefaultEngine.ini','Config/DefaultRoadBLD.ini','Staging/SystemCompletion_2026-10-04/launch_editor.ps1','Staging/SystemCompletion_2026-10-04/seal_runtime.py')
if (@(Compare-Object @($taskManifest.support_files.PSObject.Properties.Name) $taskSupportNames).Count) { throw 'Combined seal lacks exact startup/configuration files.' }
foreach ($taskSupport in $taskManifest.support_files.PSObject.Properties) {
    $taskSupportPath = Join-Path $taskRoot $taskSupport.Name
    if ((Get-FileHash -LiteralPath $taskSupportPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskSupport.Value) { throw ('Startup/configuration differs from combined seal: '+$taskSupport.Name) }
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
        New-Item -ItemType Directory -Path (Split-Path $taskRestoreBackup -Parent) -Force | Out-Null
        Copy-Item -LiteralPath $taskRestorePath -Destination $taskRestoreBackup
        $taskRestore.RestoreEnabled = $false
        [System.IO.File]::WriteAllText($taskRestorePath,($taskRestore | ConvertTo-Json -Depth 20),[System.Text.UnicodeEncoding]::new($false,$false))
    }
}
if ((Get-Content -LiteralPath $taskLeasePath)[-1] -ne $taskLease -or @(Get-Process UnrealEditor -ErrorAction SilentlyContinue).Count -ne 0) { throw 'Editor ownership changed during startup preparation.' }
foreach ($taskScopePath in $taskScopeHashes.Keys) {
    if ((Get-FileHash -LiteralPath (Join-Path $taskRoot $taskScopePath) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskScopeHashes[$taskScopePath]) { throw 'Bank startup authority changed during preparation.' }
}
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
$taskNewLease = [DateTime]::UtcNow.ToString('o')+' OWNER=CODEX_MANAGED_SYSTEMS_STARTUP manager_thread_id='+$ManagerThreadId+' operator_thread_id='+$OperatorThreadId+' task='+$taskOperatorRole+' assigned_editor_PID='+$taskProcess.Id+' map='+$AreaMap+' activation=AWAITING_MANAGER_ACTUAL_PID scope=paused_startup_inspection_only'
[System.IO.File]::AppendAllText($taskLeasePath,[Environment]::NewLine+$taskNewLease+[Environment]::NewLine)
$taskReceipt = @{pid=$taskProcess.Id; map=$AreaMap; map_sha256=$ExpectedMapSha256.ToLowerInvariant(); profile=$taskProfiles[0].FullName; profile_sha256=$ExpectedProfileSha256.ToLowerInvariant(); manifest_sha256=$ExpectedManifestSha256.ToLowerInvariant(); manager_thread_id=$ManagerThreadId; operator_thread_id=$OperatorThreadId; actual_pid_lease=$taskNewLease; sources_checked=$true; generation_started=$false; generation_authorized=$false; activation='AWAITING_MANAGER_ACTUAL_PID'; pause_before_python=$true; autosave=$false; original_map=$true}
$taskReceipt.operator_role = $taskOperatorRole
$taskReceipt.bank_scope_sha256 = $taskScopeHashes
$taskReceipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'LAUNCH_STATE.json') -Encoding utf8
$taskReceipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot ('LAUNCH_STATE_PID'+$taskProcess.Id+'.json')) -Encoding utf8
$taskReceipt | ConvertTo-Json -Depth 5
