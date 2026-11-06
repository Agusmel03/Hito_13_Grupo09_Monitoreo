# Archivos de la implementación

Dockerfile inspeccionado, sin cambios. El código y documentación originales de otros proyectos no se modificaron. No hay diff Git independiente porque la raíz detectada es el perfil del usuario.

Modificados en esta copia:

- `README.md`
- `.gitignore`
- `.dockerignore`
- `compose.yaml`
- `compose.compacto.yaml`
- `requirements.txt`
- `requirements-lock.txt`
- `app/main.py`
- `app/adapter.py`
- `hito12/common.py`
- `hito12/cli.py`
- `hito12/load.py`
- `hito12/profiles.py`
- `scripts/common.ps1`
- `tests/test_api.py`

Agregados:

- `app/monitoring.py`
- `monitoring/blackbox/blackbox.yml`
- `monitoring/grafana/dashboards/hito13.json`
- `monitoring/grafana/provisioning/dashboards/default.yml`
- `monitoring/grafana/provisioning/datasources/prometheus.yml`
- `monitoring/prometheus/alerts.yml`
- `monitoring/prometheus/prometheus.yml`
- `scripts/hito13/common.ps1`
- `scripts/hito13/detener_laboratorio.ps1`
- `scripts/hito13/generar_trafico.ps1`
- `scripts/hito13/iniciar_monitoreo.ps1`
- `scripts/hito13/prueba_falla_controlada.ps1`
- `scripts/hito13/recuperar_servicios.ps1`
- `scripts/hito13/validar_local.py`
- `scripts/hito13/verificar_targets.ps1`
- `tests/test_monitoring.py`

También se agregaron los siete documentos específicos en docs/hito13, README_hito12_historico.md y los JSON reales de docs/hito13/evidencia. Estado local ignorado: .venv y .runtime/hito13.

Los cuatro módulos hito12 modificados solo bloquean la CLI heredada o retargetean identidades/puertos; no se ejecutaron cargas. Los resultados y la documentación históricos se conservaron.


Ampliación de preparación del dataset: agregados `scripts/hito13/preparar_datos.ps1`, `scripts/hito13/preparar_datos.py` y `tests/test_hito13_dataset.py`. Actualizados `scripts/hito13/validar_local.py`, README y esta documentación de evidencias. Se conservan resultados previos y se agregan los JSON nuevos de preparación y tráfico. No se modificaron ni desbloquearon los scripts históricos ni `hito12/dataset.py` / `hito12/integrity.py` en esta ampliación.
