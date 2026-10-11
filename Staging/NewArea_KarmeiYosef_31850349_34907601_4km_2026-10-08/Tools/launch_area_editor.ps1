<#
Karmei Yosef operator (Claude Code session 4a6a1d0c), 2026-10-08. Fork of the manager's launch_area_editor.ps1
(Staging/Manager_2026-10-07/Tools) with this task's folder, identity and its own ports 19852/18092/8012.
Gates: zero UnrealEditor/UnrealEditor-Cmd processes, last EDITOR_OWNER.txt line OWNER=NONE (read only), ports free,
seal_runtime.py --check passes, PackageRestoreData.json lists no packages; with -Map the saved map sha256 must equal
-ExpectedMapSha256 (and a forensic copy goes to ..\Before\). Without -Map (Purpose create) the editor opens the
project default map and the creation script makes the new map. Writes ..\ASSIGNMENT_RUN.json and
Staging/ParallelEditors/EDITOR_<pid>.json. Never writes EDITOR_OWNER.txt (the sealed menu action owns the lease).
  .\launch_area_editor.ps1 -Purpose create -AvivWord "<words>"
  .\launch_area_editor.ps1 -Purpose pcg [-Map <clone map> -ExpectedMapSha256 <64hex>] -AvivWord "<words>"   (PCG trial clone folder only)
  .\launch_area_editor.ps1 -Purpose run|verify -Map /Game/.../L_Area -ExpectedMapSha256 <64hex> -AvivWord "<words>"
-AllowLiveEditorPid <pid> (pcg/verify only, added 2026-10-09 under the parallel-editor rule): tolerate exactly that one other
editor (e.g. Aviv's own); it must not own this task's ports. It is never used, closed or saved by this task.
#>
param(
    [Parameter(Mandatory = $true)][ValidateSet('create', 'run', 'verify', 'pcg', 'wptrial')][string]$Purpose,
    [string]$Map = '',
    [string]$ExpectedMapSha256 = '',
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$AvivWord,
    [int]$PortWaitSeconds = 1800,
    [int]$AllowLiveEditorPid = 0
)
$ErrorActionPreference = 'Stop'
$R = 'C:\Users\USER\Documents\Unreal Projects\Environmentpipeline'
$T = Join-Path $R 'Staging\NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
$Operator = '4a6a1d0c-3246-4c14-af9c-7d81b1106019'
$AreaPrefix = $(if ($Purpose -eq 'pcg') { '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/' } elseif ($Purpose -eq 'wptrial') { '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/' } else { '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/' })
# wptrial (Aviv 2026-10-10, trial on a copy of the clone): a World Partition map keeps its actors under these two mirrors
$TrialMirrors = @('/Game/__ExternalActors__/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/', '/Game/__ExternalObjects__/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/')
$Editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$PY = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$CopilotPort = 19852; $PluginPort = 18092; $NativePort = 8012
$Copilot = "http://127.0.0.1:$CopilotPort/mcp"; $Native = "http://127.0.0.1:$NativePort/mcp"
function Get-Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Write-JsonFile([string]$Path, $Object) { $Object | ConvertTo-Json -Depth 8 | Out-File -LiteralPath $Path -Encoding utf8 }

if ($Purpose -eq 'create') {
    if ($Map) { throw 'Purpose create opens no map' }
} elseif ($Purpose -notin @('pcg', 'wptrial') -or $Map) {
    if (-not $Map.StartsWith($AreaPrefix)) { throw "Map must be under $AreaPrefix" }
    if ($ExpectedMapSha256 -notmatch '^[0-9a-f]{64}$') { throw 'ExpectedMapSha256 (64 hex) is required with -Map' }
}
$live = @(Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe' OR Name='UnrealEditor-Cmd.exe'")
if ($AllowLiveEditorPid -ne 0) {
    if ($Purpose -notin @('pcg', 'verify', 'wptrial')) { throw '-AllowLiveEditorPid is for pcg/verify/wptrial only' }
    $live = @($live | Where-Object { $_.ProcessId -ne $AllowLiveEditorPid })
}
if ($live.Count -ne 0) { throw ('An Unreal editor process is live: ' + (($live | ForEach-Object { "$($_.Name) $($_.ProcessId)" }) -join ', ')) }
$lastLease = [string](Get-Content -LiteralPath (Join-Path $R 'Staging\ModelBank\EDITOR_OWNER.txt') | Where-Object { $_.Trim() } | Select-Object -Last 1)
if ($lastLease -notmatch '(^|\s)OWNER=NONE(\s|$)') { throw "The last EDITOR_OWNER.txt line is not OWNER=NONE: $lastLease" }
foreach ($port in $CopilotPort, $PluginPort, $NativePort) { if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { throw "Port $port is already listening" } }
$sealOutput = [string](& $PY -I -B (Join-Path $R 'Staging\SystemCompletion_2026-10-04\seal_runtime.py') --check 2>&1)
if ($LASTEXITCODE -ne 0) { throw "seal_runtime.py --check failed: $sealOutput" }
$restoreFile = Join-Path $R 'Saved\Autosaves\PackageRestoreData.json'
if (Test-Path -LiteralPath $restoreFile) {
    $restoreText = [Text.Encoding]::Unicode.GetString([IO.File]::ReadAllBytes($restoreFile))
    if ($restoreText -notmatch '"Packages"\s*:\s*\[\s*\]') { throw 'PackageRestoreData.json lists packages; resolve before any launch' }
}
$assignmentFile = Join-Path $T 'ASSIGNMENT_RUN.json'
if (Test-Path -LiteralPath $assignmentFile) {
    $old = Get-Content -LiteralPath $assignmentFile -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($old.editor_live -eq $true) { throw "ASSIGNMENT_RUN.json is still live for PID $($old.assigned_editor_PID); release it first" }
}
$mapSha = $null; $backup = $null; $mapName = 'NoMap_create'
if ($Map) {
    $MapFile = Join-Path $R ('Content' + $Map.Substring(5).Replace('/', '\') + '.umap')
    if (-not (Test-Path -LiteralPath $MapFile)) { throw "Map file not found: $MapFile" }
    $mapSha = Get-Sha $MapFile
    if ($mapSha -ne $ExpectedMapSha256) { throw "Map sha $mapSha differs from $ExpectedMapSha256" }
    $before = Join-Path $T 'Before'; New-Item -ItemType Directory -Force -Path $before | Out-Null
    $mapName = [IO.Path]::GetFileNameWithoutExtension($MapFile)
    $backup = Join-Path $before ($mapName + '_' + $mapSha.Substring(0, 8) + '.umap')
    if (-not (Test-Path -LiteralPath $backup)) { Copy-Item -LiteralPath $MapFile -Destination $backup }
    if ((Get-Sha $backup) -ne $mapSha) { throw "Forensic copy hash differs: $backup" }
}
New-Item -ItemType Directory -Force -Path (Join-Path $T 'Logs') | Out-Null
$log = Join-Path $T ('Logs\' + $Purpose + '_' + $mapName + '_' + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '.log')
$mapArg = if ($Map) { ' "' + $Map + '"' } else { '' }
$editorArgs = '"' + (Join-Path $R 'Environmentpipeline.uproject') + '"' + $mapArg + ' -NoAutoSave -NoSaveConfig -NoRestoreOpenAssetTabs ' +
    '-abslog="' + $log + '" ' +
    '-ini:Engine:[/Script/HoudiniEngineRuntime.HoudiniRuntimeSettings]:bPauseCookingOnStart=True ' +
    '-ini:EditorPerProjectUserSettings:[/Script/UnrealEd.EditorLoadingSavingSettings]:bAutoSaveEnable=False,' +
    '[/Script/UnrealEd.EditorLoadingSavingSettings]:RestoreOpenAssetTabsOnRestart=NeverRestore,' +
    "[/Script/UnrealCopilot.UnrealCopilotSettings]:McpPort=$CopilotPort,[/Script/UnrealCopilot.UnrealCopilotSettings]:UePluginPort=$PluginPort," +
    "[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:ServerPortNumber=$NativePort"
$process = Start-Process -FilePath $Editor -ArgumentList $editorArgs -WorkingDirectory $R -WindowStyle Maximized -PassThru
$editorPid = $process.Id
$startUtc = $process.StartTime.ToUniversalTime().ToString('o')
$nowUtc = [DateTime]::UtcNow.ToString('o')
$assignment = [ordered]@{
    schema = 'environmentpipeline.new_area_run.v1'; operator_session_id = $Operator; purpose = $Purpose
    map = $(if ($Map) { $Map } else { $null }); profile_path = 'Staging/ModelBank/KarmeiYosef_31850349_34907601_4km/AREA_PROFILE.json'
    assigned_editor_PID = $editorPid; process_start_utc = $startUtc
    status = 'STARTING_REQUIRES_PREFLIGHT'; editor_live = $true; released_utc = $null; generation_authorized = ($Purpose -eq 'run')
    map_baseline_sha256 = $mapSha; control_endpoints = [ordered]@{ copilot = $Copilot; copilot_internal_port = $PluginPort; native = $Native }
    launch = [ordered]@{ utc = $nowUtc; aviv_word = $AvivWord; arguments = $editorArgs; log = $log; backup = $backup; last_lease_line_read = $lastLease; seal_check = 'passed' }
    other_live_editor_allowed = $(if ($AllowLiveEditorPid -ne 0) { $AllowLiveEditorPid } else { $null })
}
Write-JsonFile $assignmentFile $assignment
Write-JsonFile (Join-Path $T ("ASSIGNMENT_RUN_PID$editorPid.json")) $assignment
$record = [ordered]@{
    schema = 'environmentpipeline.parallel_editor.v1'; pid = $editorPid; process_start_utc = $startUtc; task = "KarmeiYosef4km_$Purpose"
    operator_thread_id = $Operator; authority = "AVIV_DIRECT_USER_2026_10_08: $AvivWord"
    assignment_ref = [ordered]@{ path = 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/ASSIGNMENT_RUN.json'; sha256 = (Get-Sha $assignmentFile) }
    original_map = $(if ($Map) { $Map } elseif ($Purpose -eq 'pcg') { $AreaPrefix + 'L_KarmeiYosef_31850349_34907601_4km_PCGTrial' } else { $AreaPrefix + 'BankIntegration_v015/L_KarmeiYosef_31850349_34907601_4km' }); write_scope = $(if ($Purpose -eq 'wptrial') { @($AreaPrefix) + $TrialMirrors } else { @($AreaPrefix) })
    read_scope = @('/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/', '/Game/Project/Shared/ModelBank/', '/Game/Project/Shared/SurfacePainting/', '/Game/Project/Shared/Atmosphere/ReusableSky/', '/Game/Project/Areas/Lebanon_33390778_35506639_4km/BankIntegration_v015/Materials/')
    file_write_scope = @('Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/', 'Staging/ModelBank/KarmeiYosef_31850349_34907601_4km/', "Staging/ParallelEditors/EDITOR_$editorPid.json")
    control_endpoints = [ordered]@{ copilot = $Copilot; native = $Native }
    generation_authorized = ($Purpose -eq 'run'); no_save_all = $true; created_utc = $nowUtc
    written_by = "launch_area_editor.ps1 (Karmei Yosef operator $Operator)"; editor_live = $true; released_utc = $null
    other_live_editor_allowed = $(if ($AllowLiveEditorPid -ne 0) { $AllowLiveEditorPid } else { $null })
}
$parallelFile = Join-Path $R "Staging\ParallelEditors\EDITOR_$editorPid.json"
if (Test-Path -LiteralPath $parallelFile) { throw "Parallel record already exists: $parallelFile" }
Write-JsonFile $parallelFile $record
$deadline = (Get-Date).AddSeconds($PortWaitSeconds); $owned = $false
while ((Get-Date) -lt $deadline) {
    if (-not (Get-Process -Id $editorPid -ErrorAction SilentlyContinue)) { throw "Editor PID $editorPid exited during startup (release ASSIGNMENT_RUN.json and EDITOR_$editorPid.json by hand)" }
    $listen = @(Get-NetTCPConnection -LocalPort $CopilotPort -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
    if ($listen.Count -eq 1 -and $listen[0] -eq $editorPid) { $owned = $true; break }
    if ($listen.Count -gt 0) { throw "Port $CopilotPort is owned by $($listen -join ',') instead of $editorPid" }
    Start-Sleep -Seconds 5
}
if (-not $owned) { throw "Port $CopilotPort was not listening for PID $editorPid within $PortWaitSeconds s (editor left running)" }
[ordered]@{ pid = $editorPid; process_start_utc = $startUtc; purpose = $Purpose; map = $Map; map_sha256 = $mapSha; copilot = $Copilot; native = $Native
    parallel_record = $parallelFile; backup = $backup; log = $log } | ConvertTo-Json -Depth 4
