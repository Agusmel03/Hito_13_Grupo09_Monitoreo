# Limitaciones y evidencia

## Actualización: dataset de Hito 13 preparado

La preparación nueva fue ejecutada el 6/11/2026 UTC (noche del 5/11 en Argentina). Evidencias `20261106T025927628580Z_dataset.json` y `20261106T030027368832Z_dataset.json`: primera ejecución 51.840 filas escritas, segunda 0 escrituras sobre las mismas 51.840. Ambas verificaron conteos por partido, cero duplicados y SHA256 de todos los campos mediante lectura completa. Consulta real P001/5m: HTTP 200, 36 agregados coincidentes con oráculo en ambas corridas. Duraciones totales observadas 58,330 s y 6,429 s; no son benchmarks comparables de rendimiento.

La primera corrida registró un HTTP 404 esperado al detectar la base aún inexistente, antes de cargar; no hubo lotes sin confirmación. La segunda no registró errores HTTP. `validacion_antes_preparar_dataset.json` conserva el estado anterior con base ausente. Los apartados de validación inicial y sus 503 más abajo son históricos de la primera implementación; ya no describen la disponibilidad actual de estadísticas tras preparar el dataset.

El generador, validador y bloqueos históricos no se modificaron ni se desbloquearon. `scripts/hito13/preparar_datos.py` adapta únicamente los imports de helpers al cargar los dos módulos locales de funciones, sin importar la CLI histórica. El destino se valida antes de las escrituras; datos existentes incompatibles provocan aborto sin sobrescrituras. La recuperación de carga parcial y el rechazo de duplicados/alteraciones tienen pruebas unitarias; no se interrumpió artificialmente esta carga real.


## Alcance verificable

Implementación: Compose con cinco servicios y seis targets configurados, `/metrics`, dashboard, tres reglas, provisioning y scripts de ciclo de vida/falla. Configuración escrita no equivale a ejecución acreditada: consultar `evidencia/validacion_local.json`, los snapshots `targets_*.json`, `trafico_*.json` y `falla_*.json` que existan.

No existe consigna PDF de Hito 13 en esta copia; se implementa el alcance pedido en el mensaje del usuario. El PDF disponible es de Hito 12. `CONTEXTO_PARA_CODEX_HITO12.md` no se encontró. La raíz Git detectada es `C:/Users/Usuario`, no un repositorio independiente de esta carpeta: no atribuir su HEAD a esta implementación. Registrar commit propio como no disponible y usar huellas SHA256 de fuentes.

## Históricos de Hito 12

Se conservan en su ubicación original, sin duplicarlos como monitoreo nuevo. Por ejemplo, archivos `docs/evidencia/20261104T011554960995Z_baseline/trial_01/load.json` y `docs/evidencia/20261104T012248028457Z_pooled/trial_01/load.json`: ambos registran 319 operaciones y 240 en tramo estable, 8 éxitos/s y 0 errores; p95 de latencia estable 50.890 ms y 24.346 ms, respectivamente. Son dos repeticiones históricas del 4/11/2026; no prueban mejora causal global ni describen este entorno. Revisar las demás repeticiones, integridad y configuración antes de concluir. El dashboard NO importa estos valores como series actuales.

## Pendientes y límites

- No se levantan MongoDB, Neo4j, Cassandra, Redis ni IRIS. La defensa separa fundamentos y propuestas de implementaciones demostrables.
- No se verifica replicación, consistencia distribuida, failover de datos, integridad lógica ni durabilidad mediante la probe `/health`.
- Si el volumen nuevo está vacío, estadísticas devuelve 503 por base/tabla ausente; esto no demuestra regresión del contrato. No se creó dataset para ocultarlo.
- Volumen en dashboard significa requests, no tamaño ni cantidad de filas de bases.
- Captura visual del dashboard y evaluación humana de la defensa quedan pendientes si no se registran expresamente.
- La alerta de 5xx se observó en firing por consultas a base ausente; no se probó bajo carga pesada ni con un dataset operativo.
- Sin notificaciones externas, TLS ni autenticación InfluxDB: laboratorio exclusivamente local.
- Los scripts nuevos requieren nombre de carpeta esperado, daemon local y recursos con identidad propia. El perfil compacto es histórico retargeteado, no la demo monitoreada.
- Validar cada requisito contra salida concreta; no convertir configuración ni históricos en cumplimiento medido.


## Validaciones realizadas en esta sesión

- Compose estándar y compacto: sintaxis validada; el compacto no se arrancó.
- PowerShell: parseo de los siete scripts sin errores; inicio, targets, tráfico, falla y recuperación probados con Docker real. La detención se registra en `estado_final.json` cuando se ejecute.
- Python: 8 tests de contrato API/adaptador, métricas, cardinalidad, exclusión de scrapes, errores 503/500 y reutilización de conexiones pasaron. Son pruebas locales con dependencias simuladas; no demuestran consulta exitosa a la base real. Una advertencia de deprecación del TestClient/AnyIO quedó registrada.
- Promtool: configuración válida y tres reglas válidas. Dashboard provisionado y datasource encontrados por API Grafana; diez expresiones PromQL aceptadas (incluye dos en el panel de comparación). No se inspeccionó visualmente la interfaz.
- Tráfico: dos corridas separadas de 20 GET secuenciales, cada una con 10 salud 200 y 10 estadísticas 503. La segunda incluye percentiles nearest-rank y contexto. Son humo de monitoreo, no benchmark ni capacidad máxima.
- Una consulta SQL de conteo de solo lectura recibió HTTP 404: `database not found: hito12_g09`. Por eso no hay evidencia de respuestas estadísticas exitosas contra InfluxDB real. No se prepararon datos ni se usaron los del original.
- La prueba de falla observó probe API=0 e InfluxDB=1; alerta crítica firing; recuperación API=1 e identidad del volumen conservada. Los resultados están en los archivos falla y targets, sin capturas artificiales.
- Se verificó que `.runtime/hito13/grafana_admin_password` y `.venv` están ignorados por Git; no se publicaron secretos ni se hizo push.

Se conservó `validacion_intento1.json`: detectó un mock incompleto de la prueba exitosa (no asignaba el tiempo de dependencia en su thread) y un scrape transitorio tras recrear API. Se corrigió el mock y se agregó espera de targets. El primer snapshot de arranque también registró Grafana temporalmente down. No se borraron esos resultados ni se presentan como éxitos.

Las horas de evidencia son UTC; 2026-11-06 01:xx UTC corresponde al 5/11 por la noche en Argentina. `validacion_local.json` consolida entorno, versiones, imágenes y límites efectivos, fuentes SHA256, pruebas y archivos relacionados. Las primeras evidencias tienen menos metadatos; las corridas finales de scripts adjuntan contexto completo. No se atribuye un commit del perfil de usuario a este proyecto.

## Requisitos solicitados y alcance acreditado

| Pedido | Implementación / evidencia | Límite |
|---|---|---|
| Prometheus/Grafana aislados y con límites | Compose, inspect saneado en validacion_local | Tags explícitos, sin digest fijado |
| Requests, errores y latencia API | endpoint real /metrics, tests, dashboard_queries | Un worker, contadores se reinician |
| Al menos tres componentes | API, Prometheus, Grafana, blackbox; probes API/InfluxDB | Otros cinco motores ausentes |
| Disponibilidad, latencia, volumen, errores | JSON con nueve paneles, provisionado por API | Volumen de requests, no tamaño de datos; revisión visual pendiente |
| Comparar dos subsistemas | Probes reales API e InfluxDB | Salud HTTP, no rendimiento SQL equivalente |
| Dos PromQL explicadas | metricas_y_consultas y consultas aceptadas | Sin tráfico algunas series quedan vacías |
| Dos alertas/umbrales | Tres reglas, observaciones firing | Sin notificaciones externas ni SLO validado |
| Falla y recuperación | Archivos falla y snapshots de targets | Sin prueba de integridad lógica del dataset |
| Guion grupal hasta 20 min | defensa_final, 19 minutos | Requiere ensayo y reparto humano |
| Históricos Hito 12 separados | Referencias a archivos existentes | No son telemetría de Hito 13 |

No se declara cumplimiento de una rúbrica completa no disponible ni implementación de los seis motores. Lo pendiente es revisar el dashboard visualmente, ensayar la defensa. La consulta de negocio exitosa ya fue comprobada con el preparador nuevo descrito al inicio.

La suite histórica completa de Hito 12 no se ejecutó; sus pruebas operativas dependen de una CLI bloqueada deliberadamente en esta copia. La validación automatizada se limita a los tres archivos de tests enumerados en validacion_local.json.

Verificación final de esta ampliación: `evidencia/verificacion_dataset_hito13.json`. El tráfico nuevo completó 20/20 GET con HTTP 200 y cero errores; los cinco servicios quedaron activos y los seis targets UP. Las 10 pruebas locales pasaron (una advertencia de deprecación de AnyIO); integridad y consulta de negocio se comprobaron además con InfluxDB y API reales.
