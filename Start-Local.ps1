param([switch]$Restart, [switch]$InstallApk, [switch]$ConnectDevice, [string]$PythonExecutable)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$defaultPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not $PythonExecutable) { $PythonExecutable = $defaultPython }
$PythonExecutable = (Resolve-Path -LiteralPath $PythonExecutable).Path
if ($PythonExecutable -ne $defaultPython) {
    # An explicitly selected installed Python can reuse this project's dependencies.
    # This does not change Windows execution policies or install another stack.
    $env:PYTHONPATH = (Join-Path $taskRoot '.venv\Lib\site-packages') + ';' + (Join-Path $taskRoot 'backend')
}
$runtime = Join-Path $taskRoot '.runtime'
New-Item -ItemType Directory -Path $runtime -Force | Out-Null
$listener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($listener -and $Restart) {
    foreach ($item in $listener) {
        $server = Get-CimInstance Win32_Process -Filter "ProcessId = $($item.OwningProcess)"
        $parent = Get-CimInstance Win32_Process -Filter "ProcessId = $($server.ParentProcessId)"
        $recordedPid = Get-Content -LiteralPath (Join-Path $runtime 'buyer-backend.pid') -ErrorAction SilentlyContinue
        $legacyOwned = $parent.ExecutablePath -eq $defaultPython -and $parent.CommandLine -match 'app.run_preview'
        $directOwned = $server.ExecutablePath -eq $PythonExecutable -and "$($server.ProcessId)" -eq "$recordedPid"
        if ($server.CommandLine -notmatch 'app.run_preview' -or (-not $legacyOwned -and -not $directOwned)) {
            throw 'Port 8000 belongs to another application; it was not stopped.'
        }
        Stop-Process -Id $server.ProcessId -ErrorAction SilentlyContinue
        if ($legacyOwned) { Stop-Process -Id $parent.ProcessId -ErrorAction SilentlyContinue }
    }
    $listener = $null
}
if (-not $listener) {
    $process = Start-Process -FilePath $PythonExecutable -ArgumentList '-m','app.run_preview','--host','127.0.0.1','--port','8000' -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtime 'buyer-backend.out.log') -RedirectStandardError (Join-Path $runtime 'buyer-backend.err.log') -PassThru
    $process.Id | Set-Content (Join-Path $runtime 'buyer-backend.pid')
}
$ready = $false
for ($attempt=0; $attempt -lt 25; $attempt++) {
    try {
        $config = Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/meta/client-config' -TimeoutSec 2
        if ($config.version -ne '0.8.1' -or $config.buyer_api_version -ne 1) {throw 'API_VERSION_MISMATCH'}
        $ready = $true
        break
    } catch { Start-Sleep -Milliseconds 400 }
}
if (-not $ready) {throw 'Backend unavailable or incompatible. See .runtime/buyer-backend.err.log.'}
$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
if (($InstallApk -or $ConnectDevice) -and (Test-Path -LiteralPath $adb)) {
    $devices = & $adb devices
    if ($devices -match 'AS7J6R4730001975\s+device') {
        & $adb -s AS7J6R4730001975 reverse tcp:8000 tcp:8000
        if ($InstallApk) { & $adb -s AS7J6R4730001975 install -r (Join-Path $taskRoot 'deliverables\AutoExpert_2_0_Alpha_0.8.1.apk') }
        & $adb -s AS7J6R4730001975 shell am start -n com.autoexpert.demo/.MainActivity
    }
}
Write-Output 'Auto Expert 0.8.1 ready: http://127.0.0.1:8000/preview/'
