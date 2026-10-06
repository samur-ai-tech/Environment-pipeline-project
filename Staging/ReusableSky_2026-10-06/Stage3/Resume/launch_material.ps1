$ErrorActionPreference='Stop'
$skyProject='C:/Users/USER/Documents/Unreal Projects/Environmentpipeline'
$skyStage=Join-Path $skyProject 'Staging/ReusableSky_2026-10-06/Stage3'
if (@(Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue).Count) {throw 'Recheck assignment before concurrent package authoring'}
$skyArgs='"'+$skyProject+'/Environmentpipeline.uproject" -run=pythonscript -script="'+$skyStage+'/Resume/create_material_commandlet.py" -AllowCommandletRendering -unattended -nosplash -NoAutoSave -NoSaveConfig -abslog="'+$skyStage+'/Resume/MaterialCommandlet.log" -ini:Engine:[/Script/HoudiniEngineRuntime.HoudiniRuntimeSettings]:bPauseCookingOnStart=True -ini:EditorPerProjectUserSettings:[/Script/UnrealEd.EditorLoadingSavingSettings]:bAutoSaveEnable=False,[/Script/UnrealCopilot.UnrealCopilotSettings]:McpPort=19841,[/Script/UnrealCopilot.UnrealCopilotSettings]:UePluginPort=18081,[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:ServerPortNumber=8001'
$skyProc=Start-Process -FilePath 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe' -ArgumentList $skyArgs -WorkingDirectory $skyProject -WindowStyle Hidden -PassThru
[pscustomobject]@{pid=$skyProc.Id;authority='RESUME_MANAGER_RESPONSE.json';world='none (asset authoring only)';writable_asset='/Game/Project/Shared/Atmosphere/ReusableSky/M_EnvironmentCelestial';created_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content (Join-Path $skyStage 'Resume/COMMANDLET_ASSIGNMENT.json')
$skyProc.Id
