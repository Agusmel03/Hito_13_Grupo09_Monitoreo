"""Una sola variable experimental: cliente HTTP efímero versus persistente."""
from threading import local
from time import perf_counter
from types import SimpleNamespace

import httpx
from pydantic import SecretStr

from app.upstream_influx3 import Influx3Adapter
from app.monitoring import DEPENDENCY


class MeasuredAdapter(Influx3Adapter):
    def __init__(self, url: str, mode: str):
        super().__init__(SimpleNamespace(
            influx_url=url, influx_database="hito12_g09",
            # Marcador público sin privilegios: el laboratorio no usa autenticación.
            influx_token=SecretStr("hito12-local-no-secret"), timeout_seconds=4.0,
        ))
        if mode not in {"baseline", "pooled"}:
            raise ValueError("Modo desconocido")
        self.mode = mode
        self.timing = local()
        self.client = httpx.Client(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=16, max_keepalive_connections=16,
                                keepalive_expiry=5.0),
        ) if mode == "pooled" else None

    def query_sql(self, sql):
        start = perf_counter()
        result = "error"
        try:
            if self.client is None:
                rows = super().query_sql(sql)
                result = "ok"
                return rows
            response = self.client.get(
                f"{self.url}/api/v3/query_sql",
                params={"db": self.database, "q": sql, "format": "json"},
                headers={"Authorization": f"Bearer {self.token}"},
            )
            response.raise_for_status()
            rows = response.json()
            result = "ok"
            return rows
        finally:
            elapsed = perf_counter() - start
            self.timing.dependency_ms = elapsed * 1000
            DEPENDENCY.labels("influxdb", result).observe(elapsed)

    def close(self):
        if self.client is not None:
            self.client.close()
