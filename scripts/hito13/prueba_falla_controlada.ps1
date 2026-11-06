param([ValidateRange(55,120)][int]$Segundos=55)
. (Join-Path $PSScriptRoot 'common.ps1')
& (Join-Path $PSScriptRoot 'verificar_targets.ps1')
$before = (& docker volume inspect hito13-g09_datos_hito13 --format '{{.Name}}|{{.CreatedAt}}')
if ($LASTEXITCODE -ne 0) { throw 'No se identifico volumen propio.' }
$record = [ordered]@{start_utc=[DateTime]::UtcNow.ToString('o'); failure='stop API only'; duration_requested_seconds=$Segundos; data_operations=0; concurrency=0; latency='No aplica: prueba de disponibilidad, no carga'; integrity='Sin escrituras. Identidad del volumen antes/despues; no acredita integridad logica SQL.'; before_volume=$before}
try {
    Invoke-Hito13Compose -Arguments @('stop','--timeout','10','api')
    Start-Sleep -Seconds $Segundos
    $failed = @(Get-Hito13Query 'probe_success{job="probes",component="api"}')
    $record.failed_probes = $failed
    $record.failure_alerts = (Invoke-RestMethod 'http://127.0.0.1:19013/api/v1/alerts' -TimeoutSec 8).data.alerts
    & (Join-Path $PSScriptRoot 'verificar_targets.ps1') -PermitirFalla
    if ($failed.Count -ne 1 -or [double]$failed[0].value[1] -ne 0) { throw 'No se observo probe_success=0.' }
    if (@($record.failure_alerts | Where-Object { $_.labels.alertname -eq 'ComponenteHTTPNoDisponible' -and $_.labels.component -eq 'api' -and $_.state -eq 'firing' }).Count -ne 1) { throw 'No se observo alerta firing; revisar evaluacion y duracion.' }
    $record.failure_observed = $true
}
finally {
    Invoke-Hito13Compose -Arguments @('start','api')
    Wait-Hito13Http 'http://127.0.0.1:8013/health/live'
    Start-Sleep -Seconds 20
    $record.recovered_probes = @(Get-Hito13Query 'probe_success{job="probes",component="api"}')
    $record.recovered = ($record.recovered_probes.Count -eq 1 -and [double]$record.recovered_probes[0].value[1] -eq 1)
    $record.after_volume = (& docker volume inspect hito13-g09_datos_hito13 --format '{{.Name}}|{{.CreatedAt}}')
    $record.volume_identity_preserved = ($LASTEXITCODE -eq 0 -and $before -eq $record.after_volume)
    $record.end_utc = [DateTime]::UtcNow.ToString('o')
    $dir = Join-Path $script:Hito13Root 'docs\hito13\evidencia'
    $record.context = Get-Hito13RunContext
$record | ConvertTo-Json -Depth 15 | Set-Content -Encoding UTF8 (Join-Path $dir ('falla_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '.json'))
}
if (-not $record.recovered -or -not $record.volume_identity_preserved) { throw 'Recuperacion o identidad de volumen no verificadas.' }
& (Join-Path $PSScriptRoot 'verificar_targets.ps1')
