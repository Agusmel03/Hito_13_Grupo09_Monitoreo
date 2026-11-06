$ErrorActionPreference = 'Stop'
$script:Hito13Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$script:Hito13Compose = Join-Path $script:Hito13Root 'compose.yaml'
$script:Hito13Runtime = Join-Path $script:Hito13Root '.runtime\hito13'
if ((Split-Path $script:Hito13Root -Leaf) -ne 'Hito_13_Grupo09_Monitoreo') { throw 'Carpeta de laboratorio inesperada.' }
if ($env:DOCKER_HOST -or $env:DOCKER_CONTEXT) { throw 'Usar contexto local sin DOCKER_HOST ni DOCKER_CONTEXT.' }
$endpoint = & docker context inspect --format '{{.Endpoints.docker.Host}}'
if ($LASTEXITCODE -ne 0 -or $endpoint -notmatch '^(npipe|unix)://') { throw 'Se requiere Docker local.' }

function Invoke-Hito13Compose {
    param([Parameter(Mandatory=$true)][string[]]$Arguments)
    & docker compose --project-name hito13-g09 --file $script:Hito13Compose @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose fallo: $($Arguments -join ' ')" }
}
function Assert-Hito13 {
    $configText = Invoke-Hito13Compose -Arguments @('config','--format','json')
    $cfg = ($configText -join "`n") | ConvertFrom-Json
    if ($cfg.name -ne 'hito13-g09') { throw 'Proyecto inesperado.' }
    foreach ($prop in $cfg.volumes.PSObject.Properties) {
        if ($prop.Value.external -or $prop.Value.name -notlike 'hito13-g09_*') { throw 'Volumen externo o fuera del proyecto.' }
    }
    foreach ($prop in $cfg.networks.PSObject.Properties) {
        if ($prop.Value.external -or $prop.Value.name -notlike 'hito13-g09_*') { throw 'Red externa o fuera del proyecto.' }
    }
    foreach ($prop in $cfg.services.PSObject.Properties) {
        if ($prop.Value.container_name) { throw 'No se permiten nombres globales de contenedor.' }
        foreach ($port in $prop.Value.ports) {
            if ($port.host_ip -ne '127.0.0.1' -or $port.published -notin @('8013','18183','19013','13013')) { throw 'Puerto fuera del laboratorio.' }
        }
        foreach ($mount in $prop.Value.volumes) {
            if ($mount.type -eq 'bind') {
                $resolved = [IO.Path]::GetFullPath($mount.source)
                if (-not $resolved.StartsWith($script:Hito13Root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Montaje fuera del proyecto.' }
            }
        }
    }
    $ids = @(Invoke-Hito13Compose -Arguments @('ps','--all','--quiet'))
    foreach ($cid in $ids) {
        if (-not $cid) { continue }
        $item = (& docker inspect $cid | ConvertFrom-Json)[0]
        if ($LASTEXITCODE -ne 0 -or $item.Config.Labels.'com.docker.compose.project' -ne 'hito13-g09' -or $item.Config.Labels.'edu.fixture.hito' -ne '13') { throw 'Contenedor fuera de alcance.' }
    }
}
function Get-Hito13Query {
    param([string]$Query)
    $url = 'http://127.0.0.1:19013/api/v1/query?query=' + [Uri]::EscapeDataString($Query)
    $result = Invoke-RestMethod -Uri $url -TimeoutSec 8
    if ($result.status -ne 'success') { throw 'Consulta Prometheus fallida.' }
    return @($result.data.result)
}
function Wait-Hito13Http {
    param([string]$Url)
    for ($attempt=0; $attempt -lt 45; $attempt++) {
        try { $null = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3; return } catch { Start-Sleep -Seconds 2 }
    }
    throw "Endpoint no disponible: $Url"
}
Assert-Hito13


function Get-Hito13RunContext {
    $info = (& docker info --format '{{json .}}' | ConvertFrom-Json)
    $cfg = ((Invoke-Hito13Compose -Arguments @('config','--format','json')) -join "`n") | ConvertFrom-Json
    $hashes = [ordered]@{}
    $files = @(Get-Item -LiteralPath $script:Hito13Compose)
    $files += @(Get-ChildItem (Join-Path $script:Hito13Root 'app') -Filter '*.py' -File)
    $files += @(Get-ChildItem (Join-Path $script:Hito13Root 'monitoring') -Recurse -File)
    $files += @(Get-ChildItem $PSScriptRoot -Filter '*.ps1' -File)
    foreach ($file in $files) { $hashes[$file.FullName.Substring($script:Hito13Root.Length + 1)] = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash }
    $services = @($cfg.services.PSObject.Properties | ForEach-Object { @{service=$_.Name; image=$_.Value.image; cpu=$_.Value.cpus; memory_bytes=$_.Value.mem_limit} })
    return @{utc=[DateTime]::UtcNow.ToString('o'); commit=$null; commit_note='Sin repositorio Git propio; usar SHA256'; docker_version=$info.ServerVersion; docker_cpus=$info.NCPU; docker_memory_bytes=$info.MemTotal; services=$services; source_sha256=$hashes}
}
