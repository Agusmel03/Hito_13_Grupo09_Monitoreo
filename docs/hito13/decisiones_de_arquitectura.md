# Decisiones de arquitectura

1. Ampliar solo esta copia: proyecto, puertos, redes e identidades Hito 13. El nombre lógico de base `hito12_g09` se conserva para compatibilidad en volumen independiente. No montar ni migrar Hito 12. El código heredado de cargas queda bloqueado tanto desde PowerShell como desde CLI Python; sus documentos se conservan como históricos.
2. Prometheus recoge métricas internas y blackbox prueba HTTP. Esto agrega monitoreo real de InfluxDB sin instalar seis motores ni afirmar métricas que no existen. La disponibilidad HTTP y la integridad lógica son propiedades diferentes.
3. Cliente Prometheus Python 0.22.1, rutas normalizadas, contadores y buckets acotados. Un proceso como en Dockerfile original. Sin cambios SQL ni esquema ni inserciones de datos para la demo.
4. Provisioning de fuente y dashboard por archivos, fuente UID estable. Grafana Viewer anónimo solo loopback, admin con secreto aleatorio ignorado por Git, login web deshabilitado. Las imágenes tienen tags explícitos; no se fijan digests, por lo que no se garantiza inmutabilidad del registro.
5. Retención Prometheus 3 días y tamaño de bloques 256 MB; WAL/head pueden superar ese tamaño en disco. RAM agregada máxima aproximada 3.06 GiB; revisar consumo real con `docker compose -p hito13-g09 -f compose.yaml stats --no-stream`. La infraestructura nueva suma 576 MiB de límites de RAM y 1.2 CPU. No es una reserva ni una medición de uso.
6. Reglas evaluadas localmente, sin Alertmanager ni envío a personas. No agregar cAdvisor/socket Docker ni exporters para motores ausentes.
7. Las probes no generan carga SQL ni cambian datos. Tráfico de demo limitado a 60 GET secuenciales con pausa de 1 s. La prueba detiene solo API y conserva los volúmenes. No se ejecutan benchmarks Hito 12.
