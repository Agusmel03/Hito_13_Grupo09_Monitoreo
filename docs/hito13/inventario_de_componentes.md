# Inventario Hito 13

| Componente | Versión/puerto loopback | Medición real configurada | Límite CPU/RAM |
|---|---|---|---|
| API FastAPI | imagen propia, Python 3.13.3; 8013 | `/metrics`: requests, errores 4xx/5xx, histograma duración; duración SQL desde adaptador. Probe `/health/live` solo proceso HTTP | 1 / 512 MiB |
| InfluxDB 3 Core | 3.12.2-core; 18183 | blackbox GET `/health`: 2xx, duración, código. Llamadas SQL desde API solo cuando hay requests. No exporter de almacenamiento ni replicación | 2 / 2048 MiB |
| Prometheus | 3.3.0; 19013 | `/metrics`, TSDB/scrapes; evalúa reglas | 0.5 / 256 MiB |
| Grafana | 11.6.0; 13013 | `/metrics` propio, `up` indica que el scrape funciona; dashboard provisionado | 0.5 / 256 MiB |
| Blackbox exporter | 0.26.0; sin puerto host | `/metrics` del exporter y `/probe` con dos destinos HTTP | 0.2 / 64 MiB |

Seis targets: cuatro scrapes directos (API, Prometheus, Grafana, blackbox) y dos probes (API e InfluxDB). Hay cinco componentes y dos subsistemas de aplicación observados: API e InfluxDB.
`up{job="probes"}=1` significa que se obtuvo la respuesta del exporter, incluso si el destino está caído. `probe_success=1` indica respuesta HTTP 2xx del destino; no asegura SQL, persistencia ni integridad. `up{job="blackbox"}` mide el exporter mismo.

Volúmenes Compose propios: `hito13-g09_datos_hito13`, `hito13-g09_prometheus_hito13`, `hito13-g09_grafana_hito13`. Redes `hito13-g09_laboratorio` y `hito13-g09_acceso`; no montajes de datos externos ni socket Docker.
MongoDB, Neo4j, Cassandra, Redis e IRIS: no desplegados, no conectados y no monitoreados por este Compose. No se deduce su salud a partir de la API de estadísticas.
