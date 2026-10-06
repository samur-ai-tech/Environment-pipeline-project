$ErrorActionPreference='Stop'
$skyRoot=Join-Path $PSScriptRoot '.'
if (Get-Process -Id 5200 -ErrorAction SilentlyContinue) { throw 'Initial sky process still running.' }
Copy-Item -LiteralPath (Join-Path $skyRoot 'ASSIGNMENT.json') -Destination (Join-Path $skyRoot 'ASSIGNMENT_PID5200.json')
Copy-Item -LiteralPath (Join-Path $skyRoot 'SkyEditor.log') -Destination (Join-Path $skyRoot 'SkyEditor_PID5200.log')
$skyLaunch=Get-Content -LiteralPath (Join-Path $skyRoot 'launch_sky.ps1') -Raw
# Reopen proves project descriptor activation without the temporary enable flag.
$skyLaunch=$skyLaunch.Replace(' -EnablePlugins=SunPosition','')
& ([scriptblock]::Create($skyLaunch))
