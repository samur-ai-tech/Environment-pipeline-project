$listener = Get-NetTCPConnection -State Listen -LocalPort 18811 -ErrorAction SilentlyContinue
if ($listener) {
    Write-Output 'Houdini connection is already listening on port 18811.'
    exit 0
}
$connectionProcess = Start-Process -FilePath 'C:/Program Files/Side Effects Software/Houdini 22.0.429/bin/hython.exe' -ArgumentList 'C:/Users/USER/.codex/vendor_imports/start_houdini_mcp_session.py' -WindowStyle Hidden -PassThru -RedirectStandardOutput 'C:/Users/USER/.codex/vendor_imports/houdini_rpc_stdout.log' -RedirectStandardError 'C:/Users/USER/.codex/vendor_imports/houdini_rpc_stderr.log'
Write-Output "Started empty Houdini connection session: PID $($connectionProcess.Id)."
