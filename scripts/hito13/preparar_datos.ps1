# Solo Hito 13. No invoca ni modifica scripts historicos.
. (Join-Path $PSScriptRoot 'common.ps1')
$python = Join-Path $script:Hito13Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Crear .venv e instalar requirements-dev-lock.txt segun README.' }
& $python -B (Join-Path $PSScriptRoot 'preparar_datos.py')
if ($LASTEXITCODE -ne 0) { throw 'Preparacion Hito 13 fallida. Revisar la evidencia dataset_*.json; no se borro ningun volumen.' }
