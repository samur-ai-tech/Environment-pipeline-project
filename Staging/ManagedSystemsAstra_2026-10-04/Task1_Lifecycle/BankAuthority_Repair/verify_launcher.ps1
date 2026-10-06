$ErrorActionPreference='Stop'
$taskOut=$PSScriptRoot
$taskProject=Split-Path (Split-Path (Split-Path (Split-Path $taskOut -Parent) -Parent) -Parent) -Parent
$taskLaunch=Join-Path $taskProject 'Staging/SystemCompletion_2026-10-04/launch_editor.ps1'
$taskTokens=$null; $taskErrors=$null
$taskAst=[System.Management.Automation.Language.Parser]::ParseFile($taskLaunch,[ref]$taskTokens,[ref]$taskErrors)
if ($taskErrors.Count) { throw ($taskErrors | Out-String) }
$taskText=Get-Content -LiteralPath $taskLaunch -Raw
$taskFixture=Join-Path $taskOut 'LauncherFixtures'
New-Item -ItemType Directory -Path (Join-Path $taskFixture 'Staging/ManagedSystemsAstra_2026-10-04'),(Join-Path $taskFixture 'Staging/BankIntegration_2026-10-04') -Force | Out-Null
$taskAssignment=@{manager_thread_id='manager';tasks=@(@{id='task4';thread_id='task4'});native_area_maps=@('/Game/Project/Areas/Fixture/Map')}
$taskScope=@('/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4','/Game/Project/Shared/ModelBank/Prepared','/Game/Project/Shared/ModelBank/Materials/BankIntegration_20261004','Named original dependencies/maps')
$taskBank=@{schema='environmentpipeline.bank_integration.v1';thread='bank';system_owner='manager';native_save_scope=$taskScope}
$taskActivation=@{schema='environmentpipeline.manager_bank_activation.v1';bank_thread_id='bank';manager_thread_id='manager';scope_receipt='Staging/BankIntegration_2026-10-04/ASSIGNMENT.json';native_save_scope=$taskScope;native_authorized_now=$false;ordinary_generation_authorized=$false}
$taskAssignment | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $taskFixture 'Staging/ManagedSystemsAstra_2026-10-04/ASSIGNMENTS.json')
$taskBank | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $taskFixture 'Staging/BankIntegration_2026-10-04/ASSIGNMENT.json')
function Write-Activation { $taskActivation | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $taskFixture 'Staging/ManagedSystemsAstra_2026-10-04/BANK_ACTIVATION.json') }
Write-Activation
# Execute only assignment/identity validation, ending before any lease/process,
# recovery, launch or write operation. No launcher body can run in this test.
$taskPreamble=$taskText.Substring($taskText.IndexOf("`$ErrorActionPreference = 'Stop'"))
$taskPreamble=$taskPreamble.Substring(0,$taskPreamble.IndexOf('$taskLeasePath ='))
$taskPreamble=$taskPreamble.Replace('$taskRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent',"`$taskRoot = '"+$taskFixture.Replace("'","''")+"'")
$taskCheck=[scriptblock]::Create($taskPreamble+"`n[pscustomobject]@{role=`$taskOperatorRole; hashes=`$taskScopeHashes}")
$ManagerThreadId='manager';$OperatorThreadId='bank';$AreaMap='/Game/Project/Areas/Fixture/Map'
$taskChecks=[System.Collections.Generic.List[string]]::new()
$taskResult=& $taskCheck
if ($taskResult.role -ne 'bank' -or $taskResult.hashes.Count -ne 2) { throw 'Bank role/scope receipt failure' }
$taskChecks.Add('Bank inspection startup allowed with native and ordinary generation flags false; truthful bank role and two scope hashes')
$OperatorThreadId='task4'
if ((& $taskCheck).role -ne 'task4') { throw 'Task4 regression' }
$taskChecks.Add('Existing task4 startup identity retained')
$OperatorThreadId='bank'
foreach ($taskBad in @('manager','operator','map','scope','activation_owner')) {
    $ManagerThreadId='manager';$OperatorThreadId='bank';$AreaMap='/Game/Project/Areas/Fixture/Map'
    $taskActivation.manager_thread_id='manager';$taskActivation.native_save_scope=$taskScope
    switch ($taskBad) {
        'manager' { $ManagerThreadId='other' }
        'operator' { $OperatorThreadId='other' }
        'map' { $AreaMap='/Game/Other' }
        'scope' { $taskActivation.native_save_scope=@('/Game/Other') }
        'activation_owner' { $taskActivation.manager_thread_id='other' }
    }
    Write-Activation
    $taskRejected=$false
    try { $null=& $taskCheck } catch { $taskRejected=$true }
    if (-not $taskRejected) { throw ('Expected rejection: '+$taskBad) }
    $taskChecks.Add('Rejected invalid bank startup '+$taskBad)
}
$taskChecks.Add('PowerShell parser reports zero errors for complete launcher; no native launch executed')
@{passed=$taskChecks.Count;checks=@($taskChecks);native_execution=$false;launcher_body_executed=$false} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskOut 'LAUNCHER_CHECKS.json')
Write-Output ('Launcher checks passed: '+$taskChecks.Count)
