$ErrorActionPreference='Stop'
$taskProjectRoot='C:\Users\USER\Documents\Unreal Projects\Environmentpipeline'
if (@(Get-Process UnrealEditor -ErrorAction SilentlyContinue).Count) {throw 'Editor must be closed'}
$taskMap='/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration'
$taskMapFile=Join-Path $taskProjectRoot ('Content/'+$taskMap.Substring(6)+'.umap')
$taskMapHash=(Get-FileHash -LiteralPath $taskMapFile).Hash.ToLowerInvariant()
if ($taskMapHash -ne '17d5929a02b03d9e022c0043ec95bcd99ad030574959ecd6b6812a0b5d49fba3') {throw 'Saved map changed'}
$taskSavedLedger=Join-Path $taskProjectRoot 'Staging/ManagedAstra_2026-10-03/ExteriorIntervalStop_20261003T213017494226Z/ROADBLD_WORKFLOW_STATE.json'
if ((Get-FileHash -LiteralPath $taskSavedLedger).Hash.ToLowerInvariant() -ne '7d39f05a9e01130414626c132483a8d260af810f1add2b6eff2012167ce7039c') {throw 'Saved road ownership evidence changed'}
Copy-Item -LiteralPath $taskSavedLedger -Destination (Join-Path $taskProjectRoot 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/ROADBLD_WORKFLOW_STATE.json')
Add-Content -LiteralPath (Join-Path $taskProjectRoot 'Staging/ModelBank/EDITOR_OWNER.txt') -Value ([DateTime]::UtcNow.ToString('o')+' OWNER=NONE released_by=01a10c77-46ba-7001-a657-5014f6205d3a previous_PID=25464 reason=orderly_failed_run_discard_saved_map_unchanged')
$taskManifest=(Get-FileHash -LiteralPath (Join-Path $taskProjectRoot 'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json')).Hash.ToLowerInvariant()
$taskProfile=(Get-FileHash -LiteralPath (Join-Path $taskProjectRoot 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json')).Hash.ToLowerInvariant()
& (Join-Path $taskProjectRoot 'Staging/SystemCompletion_2026-10-04/launch_editor.ps1') -AreaMap $taskMap -ExpectedMapSha256 $taskMapHash -ExpectedManifestSha256 $taskManifest -ExpectedProfileSha256 $taskProfile -ManagerThreadId '01a10c77-46ba-7001-a657-5014f6205d3a' -OperatorThreadId '01a10c77-46ba-7001-a657-5014f6205d3a'
