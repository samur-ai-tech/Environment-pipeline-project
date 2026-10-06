param([Parameter(Mandatory=$true)][string]$PythonExecutable)
$ErrorActionPreference = 'Stop'
$taskManifestPath = Join-Path $PSScriptRoot 'CONTINUATION_MANIFEST.json'
$taskApproval = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'STARTUP_ACTIVATION.json') -Raw | ConvertFrom-Json
$taskManifest = Get-Content -LiteralPath $taskManifestPath -Raw | ConvertFrom-Json
if ($taskApproval.startup_inspection_authorized -ne $true -or $taskApproval.ordinary_generation_authorized -ne $false) { throw 'Explicit startup-only activation required.' }
if ($taskApproval.manager_thread_id -ne $taskManifest.manager_thread_id -or $taskApproval.operator_thread_id -ne $taskManifest.operator_thread_id) { throw 'Activation identity differs.' }
if ((Get-FileHash -LiteralPath $taskManifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskApproval.continuation_manifest_sha256) { throw 'Activation does not bind the reviewed snapshot.' }
& $PythonExecutable (Join-Path $PSScriptRoot 'continuation_manifest.py') --verify-launch
if ($LASTEXITCODE -ne 0) { throw 'Offline continuation verification failed.' }
$taskArea = @($taskManifest.areas | Where-Object { $_.map -eq $taskApproval.map })
if ($taskArea.Count -ne 1) { throw 'Exactly one original map is required.' }
$taskRoot = Split-Path (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent) -Parent
# Recheck receipt/lease immediately before the retained launcher enforces its own
# OWNER=NONE/no-process gate. No release or recovery is synthesized here.
& $PythonExecutable (Join-Path $PSScriptRoot 'continuation_manifest.py') --verify-launch
if ($LASTEXITCODE -ne 0) { throw 'Clean release changed before launch.' }
& (Join-Path $taskRoot 'Staging/SystemCompletion_2026-10-04/launch_editor.ps1') -AreaMap $taskArea[0].map -ExpectedMapSha256 $taskArea[0].map_sha256 -ExpectedManifestSha256 $taskManifest.manifest_sha256 -ExpectedProfileSha256 $taskArea[0].profile_sha256 -ManagerThreadId $taskManifest.manager_thread_id -OperatorThreadId $taskManifest.operator_thread_id
