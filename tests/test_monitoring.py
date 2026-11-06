import httpx
from fastapi.testclient import TestClient
from prometheus_client.parser import text_string_to_metric_families
from app.main import app
from app.adapter import MeasuredAdapter

def samples(client):
    response = client.get('/metrics')
    assert response.status_code == 200
    assert 'text/plain' in response.headers['content-type']
    return [s for f in text_string_to_metric_families(response.text) for s in f.samples]

def test_metrics_count_errors_without_cardinality_or_scrape_noise(monkeypatch):
    with TestClient(app, raise_server_exceptions=False) as client:
        before = sum(s.value for s in samples(client) if s.name == 'hito13_http_requests_total')
        client.get('/health/live')
        client.get('/no-existe-id-privado')
        def fail(*args):
            raise httpx.ConnectError('no exponer')
        monkeypatch.setattr(app.state.adapter, 'statistics', fail)
        assert client.get('/api/v1/partidos/P001/estadisticas', params={'desde':'2030-06-08T19:00:00Z','hasta':'2030-06-08T20:30:00Z'}).status_code == 503
        values = samples(client)
        assert sum(s.value for s in values if s.name == 'hito13_http_requests_total') == before + 3
        assert any(s.name == 'hito13_http_errors_total' and s.labels['status'] == '503' and s.value >= 1 for s in values)
        assert any(s.name == 'hito13_http_request_duration_seconds_count' and s.value >= 1 for s in values)
        assert 'no-existe-id-privado' not in str(values)
        assert not any(s.labels.get('route') == '/metrics' for s in values)

def test_dependency_errors_are_observed(monkeypatch):
    adapter = MeasuredAdapter('http://influxdb:8181', 'baseline')
    def fail(*args, **kwargs):
        raise httpx.ConnectError('unavailable')
    monkeypatch.setattr(httpx, 'get', fail)
    try:
        adapter.query_sql('SELECT 1')
    except httpx.ConnectError:
        pass
    assert adapter.timing.dependency_ms >= 0
    with TestClient(app) as client:
        assert any(s.name == 'hito13_dependency_duration_seconds_count' and s.labels == {'component':'influxdb','result':'error'} and s.value >= 1 for s in samples(client))


def test_success_contract_and_unhandled_exception_are_instrumented(monkeypatch):
    with TestClient(app, raise_server_exceptions=False) as client:
        def success(*args):
            app.state.adapter.timing.dependency_ms = 0.0
            return []
        monkeypatch.setattr(app.state.adapter, 'statistics', success)
        params = {'desde':'2030-06-08T19:00:00Z', 'hasta':'2030-06-08T20:30:00Z'}
        response = client.get('/api/v1/partidos/P001/estadisticas', params=params)
        assert response.status_code == 200
        assert response.json()['data']['items'] == []
        assert response.headers['X-Hito12-Lab'] == 'hito13-g09'
        def unexpected(*args):
            raise RuntimeError('private diagnostic')
        monkeypatch.setattr(app.state.adapter, 'statistics', unexpected)
        assert client.get('/api/v1/partidos/P001/estadisticas', params=params).status_code == 500
        assert any(s.name == 'hito13_http_errors_total' and s.labels['status'] == '500' and s.value >= 1 for s in samples(client))
