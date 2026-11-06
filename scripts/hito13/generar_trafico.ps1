param([ValidateRange(1,60)][int]$Requests=20)
. (Join-Path $PSScriptRoot 'common.ps1')
$start = [DateTime]::UtcNow
$rows = @()
for ($i=0; $i -lt $Requests; $i++) {
    $url = 'http://127.0.0.1:8013/health/live'
    if ($i % 2 -eq 1) { $url = 'http://127.0.0.1:8013/api/v1/partidos/P001/estadisticas?desde=2030-06-08T19:00:00Z&hasta=2030-06-08T20:30:00Z&resolucion=5m' }
    $watch = [Diagnostics.Stopwatch]::StartNew()
    try { $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 8; $status = [int]$response.StatusCode }
    catch { if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode } else { $status = 0 } }
    $watch.Stop()
    $rows += [pscustomobject]@{operation=$i+1; status=$status; latency_ms=$watch.Elapsed.TotalMilliseconds; route=$(if ($i%2) {'statistics'} else {'live'})}
    Start-Sleep -Seconds 1
}
$duration = ([DateTime]::UtcNow - $start).TotalSeconds
$record = @{start_utc=$start.ToString('o'); end_utc=[DateTime]::UtcNow.ToString('o'); project='hito13-g09'; operations=$Requests; concurrency=1; duration_seconds=$duration; throughput_completed_per_second=$Requests/$duration; errors=@($rows | Where-Object {$_.status -eq 0 -or $_.status -ge 400}).Count; requests=$rows; writes=0; integrity='Solo GET; no valida integridad logica del dataset.'}
$dir=Join-Path $script:Hito13Root 'docs\hito13\evidencia'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$orderedLatency = @($rows.latency_ms | Sort-Object)
$record.latency_ms = @{method='nearest rank'; p50=$orderedLatency[[Math]::Ceiling(0.50*$Requests)-1]; p95=$orderedLatency[[Math]::Ceiling(0.95*$Requests)-1]; p99=$orderedLatency[[Math]::Ceiling(0.99*$Requests)-1]}
$record.context = Get-Hito13RunContext
$record | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $dir ('trafico_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '.json'))
$rows | Format-Table
Write-Host '503 en estadisticas puede indicar base/tabla sin datos: no se crea ni modifica el dataset.'
