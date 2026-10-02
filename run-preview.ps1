param(
    [string]$BindAddress = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$Reload
)

$ErrorActionPreference = "Stop"
$previewArgs = @("run", "--project", $PSScriptRoot, "python", "-m", "app.run_preview",
                 "--host", $BindAddress, "--port", "$Port")
if ($Reload) { $previewArgs += "--reload" }
& uv @previewArgs
exit $LASTEXITCODE
