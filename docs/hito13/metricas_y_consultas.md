# Métricas y consultas

Scrape y evaluación cada 10 segundos; timeout 5 s, probes 3 s. Histogramas en segundos, contadores se reinician al reiniciar la API. Un worker de uvicorn; múltiples workers requieren rediseñar agregación. No se instrumenta el tiempo de envío completo de cuerpos streaming. No se guardan SQL, tokens, ID de partido ni parámetros como etiquetas.

| Métrica | Unidad y alcance |
|---|---|
| `hito13_http_requests_total{method,route,status}` | requests completadas desde inicio del proceso; excluye `/metrics`, incluye health y 4xx |
| `hito13_http_errors_total{method,route,status}` | respuestas 4xx/5xx; 4xx no implica fallo del servidor |
| `hito13_http_request_duration_seconds` | histograma de duración de middleware hasta respuesta; incluye validación y dependencia |
| `hito13_dependency_duration_seconds{component="influxdb",result}` | histograma de llamada SQL desde cliente API, incluye transporte, motor y parseo; incluye errores; no tiempo interno puro de InfluxDB |
| `probe_success`, `probe_duration_seconds` | disponibilidad binaria y segundos de la probe HTTP sintética |
| `up` | disponibilidad del scrape, binaria |

## Consultas para la defensa

1. Throughput: `sum by (route) (rate(hito13_http_requests_total{job="api"}[2m]))`. Unidad requests/s, ventana móvil 2 minutos. Los health checks se distinguen por ruta; para negocio filtrar `route="/api/v1/partidos/{partido_id}/estadisticas"`. Necesita dos scrapes como mínimo.
2. p95: `histogram_quantile(0.95, sum by (le) (rate(hito13_http_request_duration_seconds_bucket{job="api"}[2m])))`. Unidad segundos, ventana 2 minutos; aproximación por buckets. No hay p95 válido sin observaciones; No data/NaN no significa cero.
3. Disponibilidad: `probe_success{job="probes"}`. Sin ventana, último scrape. Comparación equivalente de API `/health/live` e InfluxDB `/health`, ambas GET HTTP. No comparar esta latencia con una consulta SQL como si fuera la misma operación.
4. Latencia media de probes últimos 2 min: `avg_over_time(probe_duration_seconds{job="probes"}[2m])`. Segundos por componente; incluye las probes fallidas.
5. Errores: `sum(rate(hito13_http_requests_total{job="api",status=~"5.."}[2m])) / clamp_min(sum(rate(hito13_http_requests_total{job="api"}[2m])), 0.001)`. Proporción 0..1, ventana 2 minutos; dashboard porcentaje. Sin 5xx observados puede ser No data. No se rellena como éxito artificial.
6. Volumen de operaciones: `sum(hito13_http_requests_total{job="api"})`. Requests desde reinicio; no es volumen de datos almacenados ni número de partidos.

El panel API vs SQL muestra medias con ventana de 2 minutos, ambas en segundos; API es extremo a extremo y la dependencia está contenida en esa duración. No son servicios independientes ni evidencia de rendimiento equivalente. La comparación principal entre componentes es la de probes HTTP.

Fuentes: [patrón exporter multi-target](https://prometheus.io/docs/guides/multi-target-exporter/), [provisioning Grafana](https://grafana.com/docs/grafana/latest/administration/provisioning/), [información del servidor InfluxDB](https://docs.influxdata.com/influxdb3/core/api/server-information/).
