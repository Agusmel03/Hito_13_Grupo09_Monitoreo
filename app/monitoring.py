"""Metricas por proceso; un worker. Sin IDs, SQL, parametros ni datos personales."""
from prometheus_client import Counter, Histogram

REQUESTS = Counter('hito13_http_requests_total', 'Requests HTTP completadas, excluye metrics', ['method', 'route', 'status'])
ERRORS = Counter('hito13_http_errors_total', 'Respuestas HTTP 4xx y 5xx', ['method', 'route', 'status'])
LATENCY = Histogram('hito13_http_request_duration_seconds', 'Tiempo hasta respuesta del middleware', ['method', 'route'], buckets=(.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10))
DEPENDENCY = Histogram('hito13_dependency_duration_seconds', 'Duracion de llamada SQL a InfluxDB, incluye fallos', ['component', 'result'], buckets=(.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10))
