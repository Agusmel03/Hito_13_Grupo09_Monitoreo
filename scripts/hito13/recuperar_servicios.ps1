. (Join-Path $PSScriptRoot 'common.ps1')
Invoke-Hito13Compose -Arguments @('start','influxdb','api','blackbox','prometheus','grafana')
Wait-Hito13Http 'http://127.0.0.1:8013/health/live'
Wait-Hito13Http 'http://127.0.0.1:18183/health'
Start-Sleep -Seconds 15
& (Join-Path $PSScriptRoot 'verificar_targets.ps1')
