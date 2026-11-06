. (Join-Path $PSScriptRoot 'common.ps1')
$info = (& docker info --format '{{json .}}' | ConvertFrom-Json)
if ($LASTEXITCODE -ne 0 -or $info.OSType -ne 'linux' -or $info.MemTotal -lt 4GB -or $info.NCPU -lt 2) { throw 'Requiere Docker Linux, 4 GiB de RAM asignada y 2 CPU como minimo.' }
New-Item -ItemType Directory -Force -Path $script:Hito13Runtime | Out-Null
$secretPath = Join-Path $script:Hito13Runtime 'grafana_admin_password'
if (-not (Test-Path -LiteralPath $secretPath)) {
    $secret = [Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N')
    [IO.File]::WriteAllText($secretPath, $secret)
}
Invoke-Hito13Compose -Arguments @('config','--quiet')
Invoke-Hito13Compose -Arguments @('up','-d','--build','influxdb','api','prometheus','blackbox','grafana')
Wait-Hito13Http 'http://127.0.0.1:8013/metrics'
Wait-Hito13Http 'http://127.0.0.1:18183/health'
Wait-Hito13Http 'http://127.0.0.1:19013/-/ready'
Wait-Hito13Http 'http://127.0.0.1:13013/api/health'
Write-Host 'Grafana: http://localhost:13013/d/fixture2030-hito13 (Viewer local sin login)'
Write-Host 'Prometheus: http://localhost:19013/targets'
Start-Sleep -Seconds 15
& (Join-Path $PSScriptRoot 'verificar_targets.ps1')
