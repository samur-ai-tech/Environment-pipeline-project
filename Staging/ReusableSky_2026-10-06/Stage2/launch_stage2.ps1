$ErrorActionPreference = 'Stop'
$skyProject = 'C:/Users/USER/Documents/Unreal Projects/Environmentpipeline'
$skyRoot = Join-Path $skyProject 'Staging/ReusableSky_2026-10-06/Stage2'
$skyMap = '/Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration'
$skyMapFile = Join-Path $skyProject 'Content/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration.umap'
$skyEditors = @(Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe'")
if (@($skyEditors | Where-Object { $_.CommandLine -like '*L_GazaRimal_BankIntegration*' }).Count) { throw 'Rimal is already open. Resolve ownership before launch.' }
foreach ($skyPort in @(19841,18081,8001)) {
    if (Get-NetTCPConnection -LocalPort $skyPort -State Listen -ErrorAction SilentlyContinue) { throw "Sky port $skyPort is occupied." }
}
New-Item -ItemType Directory -Path (Join-Path $skyRoot 'Before') -Force | Out-Null
$skyHash = (Get-FileHash -LiteralPath $skyMapFile -Algorithm SHA256).Hash.ToLowerInvariant()
$skyBackup = Join-Path $skyRoot ('Before/L_GazaRimal_BankIntegration_'+$skyHash.Substring(0,8)+'.umap')
if (-not (Test-Path -LiteralPath $skyBackup)) { Copy-Item -LiteralPath $skyMapFile -Destination $skyBackup }
$skyArgs = '"'+$skyProject+'/Environmentpipeline.uproject" "'+$skyMap+'" -NoAutoSave -NoSaveConfig -NoRestoreOpenAssetTabs -abslog="'+$skyRoot+'/SkyEditor.log" -ini:Engine:[/Script/HoudiniEngineRuntime.HoudiniRuntimeSettings]:bPauseCookingOnStart=True -ini:EditorPerProjectUserSettings:[/Script/UnrealEd.EditorLoadingSavingSettings]:bAutoSaveEnable=False,[/Script/UnrealEd.EditorLoadingSavingSettings]:RestoreOpenAssetTabsOnRestart=NeverRestore,[/Script/UnrealCopilot.UnrealCopilotSettings]:McpPort=19841,[/Script/UnrealCopilot.UnrealCopilotSettings]:UePluginPort=18081,[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:ServerPortNumber=8001'
$skyProcess = Start-Process -FilePath 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe' -ArgumentList $skyArgs -WorkingDirectory $skyProject -WindowStyle Hidden -PassThru
$skyAssignment = [ordered]@{
    authority='AVIV_DIRECT_USER_STAGE2_CONTINUE_OWN_WINDOW_2026_10_06'; status='STARTING_REQUIRES_NATIVE_PID_PREFLIGHT'; operator_thread_id='01a1118e-256a-7d83-8a2b-ad3293e53281'; manager_session_id='cc37d4d2-3d62-4f53-b689-28432b5527ae'; assigned_editor_PID=$skyProcess.Id; map=$skyMap; map_baseline_sha256=$skyHash; map_backup=$skyBackup; native_package_scope=@('/Game/Project/Shared/Atmosphere/ReusableSky/',$skyMap); excluded=@('/Game/Project/Shared/ModelBank/','Iran map','GazaShujaiya map','all bank/catalog/profile/Houdini/generator/vendor writes'); other_editor_PIDs=@($skyEditors.ProcessId); copilot_endpoint='http://127.0.0.1:19841/mcp'; native_tools_endpoint='http://127.0.0.1:8001/mcp'; copilot_internal_port=18081; no_save_all=$true; generation_authorized=$false; plugin_activation='SunPosition already enabled and saved by Stage 1; no Stage 2 plugin change'; user_authorized_separate_editor=$true; created_utc=[DateTime]::UtcNow.ToString('o')
}
$skyAssignment | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $skyRoot 'ASSIGNMENT.json') -Encoding utf8
$skyAssignment | ConvertTo-Json -Depth 5

