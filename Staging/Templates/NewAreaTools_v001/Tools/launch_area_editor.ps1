<#
Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69). Area editor launcher, from the El Wahat fork of the
manager's launch_area_editor.ps1 (Staging/Manager_2026-10-07/Tools). The task folder is this script's parent folder and must
be <project>\Staging\<TASK_FOLDER>; area id, map prefixes, profile path and the three ports come from Tools\area_constants.py
(read with the engine Python: area_constants.py --json); the operator id is ASSIGNMENT.json operator_session_id.
Gates: zero UnrealEditor/UnrealEditor-Cmd processes, last EDITOR_OWNER.txt line OWNER=NONE (read only), ports free,
seal_runtime.py --check passes, PackageRestoreData.json lists no packages; with -Map the saved map sha256 must equal
-ExpectedMapSha256 (and a forensic copy goes to ..\Before\). Without -Map (Purpose create) the editor opens the
project default map and the creation script makes the new map. Writes ..\ASSIGNMENT_RUN.json and
Staging/ParallelEditors/EDITOR_<pid>.json. Never writes EDITOR_OWNER.txt (the sealed menu action owns the lease).
  .\launch_area_editor.ps1 -Purpose create -AvivWord "<words>"
  .\launch_area_editor.ps1 -Purpose pcg -Map <clone map> -ExpectedMapSha256 <64hex> -AvivWord "<words>"   (PCG clone folder only; -Map required)
  .\launch_area_editor.ps1 -Purpose run|verify -Map /Game/.../L_Area -ExpectedMapSha256 <64hex> -AvivWord "<words>"
-AllowLiveEditorPid <pid> (pcg/verify only, added 2026-10-09 under the parallel-editor rule): tolerate exactly that one other
editor (e.g. Aviv's own); it must not own this task's ports. It is never used, closed or saved by this task.
#>
param(
    [Parameter(Mandatory = $true)][ValidateSet('create', 'run', 'verify', 'pcg')][string]$Purpose,
    [string]$Map = '',
    [string]$ExpectedMapSha256 = '',
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$AvivWord,
    [int]$PortWaitSeconds = 1800,
    [int]$AllowLiveEditorPid = 0
)
$ErrorActionPreference = 'Stop'
$R = 'C:\Users\USER\Documents\Unreal Projects\Environmentpipeline'
$T = Split-Path -Parent $PSScriptRoot
if ((Split-Path -Parent $T) -ne (Join-Path $R 'Staging')) { throw "The task folder must be <project>\Staging\<task>: $T (the template never runs in place)" }
$Editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$PY = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$constantsOutput = [string](& $PY -I -B (Join-Path $PSScriptRoot 'area_constants.py') --json 2>&1)
if ($LASTEXITCODE -ne 0) { throw "area_constants.py --json failed (fill it in for this area first): $constantsOutput" }
$C = $constantsOutput | ConvertFrom-Json
if ($C.TASK_FOLDER -ne (Split-Path -Leaf $T)) { throw "area_constants.py TASK_FOLDER $($C.TASK_FOLDER) is not this task folder $T" }
$Operator = [string]((Get-Content -LiteralPath (Join-Path $T 'ASSIGNMENT.json') -Raw -Encoding UTF8 | ConvertFrom-Json).operator_session_id)
if (-not $Operator) { throw 'ASSIGNMENT.json operator_session_id is required' }
$AreaPrefix = $(if ($Purpose -eq 'pcg') { [string]$C.TRIAL_PREFIX } else { [string]$C.AREA_PREFIX })
$CopilotPort = [int]$C.COPILOT_PORT; $PluginPort = [int]$C.PLUGIN_PORT; $NativePort = [int]$C.NATIVE_PORT
$Copilot = "http://127.0.0.1:$CopilotPort/mcp"; $Native = "http://127.0.0.1:$NativePort/mcp"
function Get-Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Write-JsonFile([string]$Path, $Object) { $Object | ConvertTo-Json -Depth 8 | Out-File -LiteralPath $Path -Encoding utf8 }

if ($Purpose -eq 'create') {
    if ($Map) { throw 'Purpose create opens no map' }
} else {                                   # every purpose but create opens a named map (pcg too: no default clone)
    if (-not $Map.StartsWith($AreaPrefix)) { throw "Map must be under $AreaPrefix" }
    if ($ExpectedMapSha256 -notmatch '^[0-9a-f]{64}$') { throw 'ExpectedMapSha256 (64 hex) is required with -Map' }
}
$live = @(Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe' OR Name='UnrealEditor-Cmd.exe'")
if ($AllowLiveEditorPid -ne 0) {
    if ($Purpose -notin @('pcg', 'verify')) { throw '-AllowLiveEditorPid is for pcg/verify only' }
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
    map = $(if ($Map) { $Map } else { $null }); profile_path = [string]$C.PROFILE_REL
    assigned_editor_PID = $editorPid; process_start_utc = $startUtc
    status = 'STARTING_REQUIRES_PREFLIGHT'; editor_live = $true; released_utc = $null; generation_authorized = ($Purpose -eq 'run')
    map_baseline_sha256 = $mapSha; control_endpoints = [ordered]@{ copilot = $Copilot; copilot_internal_port = $PluginPort; native = $Native }
    launch = [ordered]@{ utc = $nowUtc; aviv_word = $AvivWord; arguments = $editorArgs; log = $log; backup = $backup; last_lease_line_read = $lastLease; seal_check = 'passed' }
    other_live_editor_allowed = $(if ($AllowLiveEditorPid -ne 0) { $AllowLiveEditorPid } else { $null })
}
Write-JsonFile $assignmentFile $assignment
Write-JsonFile (Join-Path $T ("ASSIGNMENT_RUN_PID$editorPid.json")) $assignment
$record = [ordered]@{
    schema = 'environmentpipeline.parallel_editor.v1'; pid = $editorPid; process_start_utc = $startUtc; task = "$($C.AREA_ID)_$Purpose"
    operator_thread_id = $Operator; authority = "AVIV_DIRECT_USER_$((Get-Date).ToUniversalTime().ToString('yyyy_MM_dd')): $AvivWord"
    assignment_ref = [ordered]@{ path = ('Staging/' + (Split-Path -Leaf $T) + '/ASSIGNMENT_RUN.json'); sha256 = (Get-Sha $assignmentFile) }
    original_map = $(if ($Map) { $Map } else { [string]$C.MAIN_MAP }); write_scope = @($AreaPrefix)
    read_scope = @([string]$C.AREA_PREFIX, '/Game/Project/Shared/ModelBank/', '/Game/Project/Shared/SurfacePainting/', '/Game/Project/Shared/Atmosphere/ReusableSky/', ([string]$C.GROUND_MI_SOURCE).Substring(0, ([string]$C.GROUND_MI_SOURCE).LastIndexOf('/') + 1))
    file_write_scope = @(('Staging/' + (Split-Path -Leaf $T) + '/'), ('Staging/ModelBank/' + $C.AREA_ID + '/'), "Staging/ParallelEditors/EDITOR_$editorPid.json")
    control_endpoints = [ordered]@{ copilot = $Copilot; native = $Native }
    generation_authorized = ($Purpose -eq 'run'); no_save_all = $true; created_utc = $nowUtc
    written_by = "launch_area_editor.ps1 (operator $Operator)"; editor_live = $true; released_utc = $null
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
