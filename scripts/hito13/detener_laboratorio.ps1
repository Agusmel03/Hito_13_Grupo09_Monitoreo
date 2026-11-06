. (Join-Path $PSScriptRoot 'common.ps1')
Invoke-Hito13Compose -Arguments @('stop','--timeout','20','api','influxdb','prometheus','blackbox','grafana')
Write-Host 'Laboratorio detenido. Contenedores y volumenes conservados.'
