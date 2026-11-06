# Fixture 2030 — Hito 13: Monitoreo y Defensa Final

Laboratorio independiente en `C:\Users\Usuario\Hito_13_Grupo09_Monitoreo`.
Proyecto Docker **hito13-g09**. No se opera Hito 11 ni el original de Hito 12.
La API conserva endpoints funcionales, SQL, base lógica `hito12_g09` y `HITO12_MODE`.
La identidad pública del laboratorio pasa a Hito 13. El dataset sintético propio se prepara explícitamente con el script nuevo de Hito 13; no se migran datos de otros hitos.

## Demo en PowerShell

Requiere Docker Desktop Linux, al menos 4 GiB asignados y 2 CPU; Internet para descargar imágenes la primera vez. Límites agregados máximos: 3.06 GiB RAM y 4.2 CPU (no reservas).

```powershell
Set-Location C:\Users\Usuario\Hito_13_Grupo09_Monitoreo
.\scripts\hito13\iniciar_monitoreo.ps1
# Esperar dos scrapes si es el primer inicio:
.\scripts\hito13\verificar_targets.ps1
.\scripts\hito13\preparar_datos.ps1
.\scripts\hito13\generar_trafico.ps1 -Requests 20
.\scripts\hito13\prueba_falla_controlada.ps1 -Segundos 55
.\scripts\hito13\recuperar_servicios.ps1
# Al finalizar (conserva todos los volúmenes):
.\scripts\hito13\detener_laboratorio.ps1
```

Grafana Viewer local sin login: http://localhost:13013/d/fixture2030-hito13
Prometheus targets: http://localhost:19013/targets; alertas: http://localhost:19013/alerts
API: http://localhost:8013/docs y http://localhost:8013/metrics
InfluxDB: http://localhost:18183/health
Blackbox no publica puerto al host. Grafana usa contraseña admin aleatoria local ignorada por Git, sin login web habilitado. No exponer este laboratorio a otras interfaces ni a Internet.

Se instrumentan API, Prometheus y Grafana; blackbox mide disponibilidad HTTP de API e InfluxDB. **Una probe HTTP no valida consultas ni integridad del motor**. El dashboard compara probes equivalentes y tiempos de API/llamada SQL con sus diferencias explícitas.
`/metrics` se excluye de requests; `/health/live` cuenta como tráfico de control. Los requests se etiquetan por plantilla de ruta; no por ID o query.

Los scripts viejos de Hito 12 y `python -m hito12.cli` están bloqueados para evitar operaciones con identidades heredadas. `compose.compacto.yaml` se retargeteó a Hito 13, pero es un perfil histórico solo API/InfluxDB: usar exclusivamente `compose.yaml` para esta demo.

## Documentación y evidencia

- [Inventario](docs/hito13/inventario_de_componentes.md)
- [Métricas y PromQL](docs/hito13/metricas_y_consultas.md)
- [Alertas y acciones](docs/hito13/alertas_y_umbral.md)
- [Decisiones](docs/hito13/decisiones_de_arquitectura.md)
- [Limitaciones, verificación y pendientes](docs/hito13/limitaciones_y_evidencia.md)
- [Defensa de 19 minutos](docs/hito13/defensa_final.md)

`docs/evidencia/` y el resto de documentos de Hito 12 son **históricos** y pueden contener comandos antiguos: no ejecutarlos. Las evidencias nuevas se guardan solo en `docs/hito13/evidencia/`. Los JSON son resultados reales al correr scripts, no capturas inventadas. La fuente de verdad de las validaciones de esta implementación es `validacion_local.json`, si existe. No se hizo push.


Verificación local reproducible (tras iniciar Docker):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev-lock.txt
.\.venv\Scripts\python.exe -B scripts/hito13/validar_local.py
```

El validador no descarga paquetes ni prepara datos. [Archivos modificados](docs/hito13/archivos_modificados.md). La validación inicial, conservada en `validacion_antes_preparar_dataset.json`, devolvía 503 por base inexistente. El preparador nuevo explicado abajo resuelve esa falta con datos propios.


## Preparar los 51.840 registros sintéticos de Hito 13

Con el laboratorio iniciado y `.venv` instalada como se explica arriba:

```powershell
.\scripts\hito13\preparar_datos.ps1
# Repetir es seguro: valida todas las filas y escribe solo las faltantes.
.\scripts\hito13\preparar_datos.ps1
.\scripts\hito13\generar_trafico.ps1 -Requests 20
```

Reutiliza sin modificar `hito12/dataset.py` (seed 1209, 24 partidos, 90 min, cada 5 s, dos equipos) y `hito12/integrity.py`. Una adaptación de imports carga solo estos módulos con helpers Hito 13, sin importar ni desbloquear `hito12.common` ni su CLI. No modifica los scripts históricos.

Destino fijo: proyecto `hito13-g09`, `127.0.0.1:18183`, volumen lógico Compose `datos_hito13` (nombre efectivo `hito13-g09_datos_hito13`). La base lógica sigue siendo `hito12_g09` para compatibilidad con la API. Se verifican etiquetas Docker, puertos, redes, montaje, recursos e identidad HTTP antes de escribir. No admite URL ni proyecto alternativos.

Genera archivos reproducibles en `.runtime/hito13/dataset/` (ignorados por Git). Carga secuencial en lotes de hasta 1.000, pausa de 50 ms, sin borrados ni reintentos automáticos. Si hay datos parciales compatibles, escribe solo faltantes; si hay datos ajenos, alterados o duplicados, aborta sin sobrescribirlos. Una ejecución simultánea en esta copia se bloquea mediante archivo local; tras una interrupción forzada, comprobar que no haya otra preparación antes de retirar exclusivamente `.runtime/hito13/preparacion-dataset.lock`.

Comprueba por lectura completa conteos por partido, ausencia de duplicados y SHA256 de todos los campos. Luego consulta P001 a resolución 5m, exige HTTP 200 y valida sus 36 agregados contra el oráculo. Cada ejecución guarda `docs/hito13/evidencia/*_dataset.json`, con fecha, huellas, recursos, volumen, latencias, operaciones, escrituras e integridad. Un lote sin confirmación puede haberse aplicado: la siguiente ejecución verifica lo existente antes de escribir. Las evidencias anteriores con base ausente y HTTP 503 se conservan como históricas; no describen necesariamente el estado posterior a esta preparación.


Preparación comprobada: 51.840 filas, 0 duplicados, integridad completa correcta y estadísticas HTTP 200 (36 agregados validados). Segunda ejecución: 0 filas escritas, mismo total y SHA256. Evidencias: [primera carga](docs/hito13/evidencia/20261106T025927628580Z_dataset.json) y [repetición idempotente](docs/hito13/evidencia/20261106T030027368832Z_dataset.json). Los cinco servicios se dejan activos para la demo.
