param([switch]$PermitirFalla)
. (Join-Path $PSScriptRoot 'common.ps1')
$targets = (Invoke-RestMethod 'http://127.0.0.1:19013/api/v1/targets' -TimeoutSec 8).data.activeTargets
$probes = @(Get-Hito13Query 'probe_success{job="probes"}')
$rows = @($targets | ForEach-Object { [pscustomobject]@{job=$_.labels.job; instance=$_.labels.instance; health=$_.health; lastScrape=$_.lastScrape; lastError=$_.lastError} })
$rows | Format-Table -AutoSize
$probes | ForEach-Object { Write-Host "$($_.metric.component): probe_success=$($_.value[1])" }
$dir = Join-Path $script:Hito13Root 'docs\hito13\evidencia'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$record = [ordered]@{utc=[DateTime]::UtcNow.ToString('o'); project='hito13-g09'; targets=$rows; probes=$probes; alerts=(Invoke-RestMethod 'http://127.0.0.1:19013/api/v1/alerts' -TimeoutSec 8).data.alerts}
$record.context = Get-Hito13RunContext
$record | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 (Join-Path $dir ('targets_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '.json'))
if (-not $PermitirFalla) {
    if ($targets.Count -ne 6 -or @($targets | Where-Object health -ne 'up').Count -gt 0 -or $probes.Count -ne 2 -or @($probes | Where-Object { [double]$_.value[1] -ne 1 }).Count -gt 0) { throw 'Targets incompletos, scrape fallido o probe fallida. Esperar 20 segundos y repetir.' }
}
