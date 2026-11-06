# Alertas y umbrales operativos

Reglas versionadas en `monitoring/prometheus/alerts.yml`; evaluación cada 10 s. Estado visible en Prometheus `/alerts`, sin Alertmanager ni notificaciones externas. Son umbrales iniciales del laboratorio, no SLO validados con producción.

| Alerta | Condición y duración | Severidad/responsable | Riesgo y acción |
|---|---|---|---|
| ComponenteHTTPNoDisponible | `probe_success{job="probes"} == 0` sostenido 30 s | critical / operaciones_g09 | HTTP inaccesible. Revisar `up` del exporter, logs acotados del servicio, ejecutar recuperación Hito 13; nunca borrar datos |
| ErroresServidorAPI | proporción de 5xx > 0.05 en rate de 2 min, sostenida 1 min | warning / backend_g09 | estadísticas indisponibles incluso con live OK. Revisar InfluxDB y errores SQL. Una base sin tabla puede causar 503; no cargar ni borrar automáticamente |
| ScrapeNoDisponible | `up == 0` sostenido 30 s | warning / operaciones_g09 | pérdida de observabilidad. Verificar endpoint y red; no deducir corrupción de la base |

Falla controlada: detener API durante 55 s; esperar probe=0 y alerta crítica firing, con InfluxDB aún disponible; recuperar en `finally` y verificar probe=1. Los 55 s permiten detección, 30 s de permanencia y un ciclo de evaluación. El script exige observar firing; genera evidencia y falla si no lo observa. Un cierre forzado de PowerShell puede impedir finally: usar `recuperar_servicios.ps1`.
La evidencia `falla_20261106T014713263Z.json` registra también ErroresServidorAPI y ScrapeNoDisponible en firing. La de 5xx se activó con el tráfico GET a estadísticas sobre una base inexistente, no por carga pesada. No acredita condiciones de producción. Ver los nombres exactos en evidencia/.
