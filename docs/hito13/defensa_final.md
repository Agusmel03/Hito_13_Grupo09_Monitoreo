# Defensa final grupal — 19 minutos

Distribuir los roles entre integrantes disponibles. Cada exposición debe mostrar archivos o resultados reales; los conceptos de motores ausentes se presentan como diseño y límites. No afirmar que los seis motores están integrados en esta copia.

| Tiempo | Responsable/tema | Guion y evidencia |
|---|---|---|
| 0:00–2:00 | Integrante A: alcance | Fixture 2030, copia aislada de Hito 12; Compose Hito 13 y volúmenes propios. API e InfluxDB son el flujo real. Mostrar inventario; los otros cinco motores no están desplegados aquí |
| 2:00–4:00 | A: MongoDB | Explicar modelo documental adecuado para catálogos/equipos como propuesta. Validación, índices según consulta y costo de duplicación. No mostrar réplica, shard ni política write concern como configurados: no existe configuración local |
| 4:00–6:00 | Integrante B: Neo4j | Proponer relaciones equipo–partido–sede y recorridos de grafos; explicar consultas por relaciones frente a documentos. No atribuir constraints, índices, cluster ni pruebas Cypher a este laboratorio |
| 6:00–8:00 | B: Cassandra | Explicar partición elegida según patrón de lectura y evitar particiones sin límite. Consistencia por operación y replicación son decisiones de diseño a fundamentar; no afirmar RF, quorum, nodos o disponibilidad probados aquí |
| 8:00–10:00 | Integrante C: Redis | Presentar caché, TTL e invalidación como propuesta para lecturas; no hay caché implementada en esta API. Recordar que un servicio activo no prueba hits/misses ni integración. No afirmar Sentinel, cluster ni mejora medida |
| 10:00–13:00 | C: InfluxDB real | Mostrar `app/adapter.py`, `app/upstream_influx3.py`, ventana temporal, resolución, SQL y `HITO12_MODE`. Base lógica heredada en volumen propio. Distinguir probe HTTP, llamada SQL y datos. Mostrar p95 histórico Hito 12 con archivo/fecha, separado de Prometheus actual; no extrapolar causalidad |
| 13:00–15:00 | Integrante D: IRIS | Propuesta de integración/Data Mart a partir de documentos heredados. No afirmar ETL ejecutado, warehouse, interoperabilidad, mirror ni resultados transaccionales. Qué claves y validaciones requeriría antes de implementar |
| 15:00–18:00 | D y A: monitoreo y falla | Abrir Grafana y Prometheus targets. Explicar rate [2m] en req/s y p95 [2m] en segundos. Comparar probes API/InfluxDB. Ejecutar falla 55 s, observar probe=0 y alerta firing, recuperación probe=1. Mostrar evidencia JSON; no borrar ni sembrar datos |
| 18:00–19:00 | Equipo: límites | Tres componentes instrumentados más probes; falta validación de salud lógica y motores externos. Alertas locales sin envío. Resolver preguntas con hechos; lo no ejecutado se dice pendiente |

Preparación previa: iniciar laboratorio, esperar dos scrapes, generar 20 requests y abrir dashboard. La falla ocupa aproximadamente 85 s contando recuperación. Si el entorno falla, mostrar evidencia previa fechada como previa, sin simular una demo en vivo. Reservar un minuto del máximo de 20 para contingencias.

Preguntas frecuentes: ¿`up=1` prueba que InfluxDB funciona? No: en probes indica scrape del exporter; `probe_success` solo 2xx. ¿La latencia SQL es tiempo interno del motor? No: incluye transporte y cliente. ¿Dónde está la réplica? No existe en este Compose. ¿Se midió Redis? No. ¿Por qué conservar HITO12_MODE? Selecciona baseline/pooled del cliente conservando contrato y datos.
