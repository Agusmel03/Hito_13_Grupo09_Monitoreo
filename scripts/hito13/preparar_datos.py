"""Preparación acotada e idempotente, exclusivamente sobre el volumen Hito 13."""
import ast
import hashlib
import importlib.metadata
import json
import math
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import httpx
import psutil

ROOT = Path(__file__).resolve().parents[2]
PROJECT = 'hito13-g09'
DATABASE = 'hito12_g09'  # Nombre lógico requerido por la API; volumen físico propio.
VOLUME = 'hito13-g09_datos_hito13'
INFLUX = 'http://127.0.0.1:18183'
API = 'http://127.0.0.1:8013'
RUNTIME = ROOT / '.runtime/hito13'
GENERATED = RUNTIME / 'dataset'
EVIDENCE = ROOT / 'docs/hito13/evidencia'
COMPOSE = ['docker', 'compose', '-p', PROJECT, '-f', str(ROOT/'compose.yaml')]
EXPECTED = dict(schema_version=1, seed=1209, matches=24, minutes=90, step_seconds=5,
                start_utc='2030-06-08T19:00:00Z', database=DATABASE, measurement='estadisticas_equipo')


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def load_pure_module(name, replacements):
    """Reutiliza el código local sin importar common/CLI bloqueados ni alterar sys.modules.

    Solo sustituye imports de helpers declarados. Algoritmo, seed, line protocol,
    oráculo e integridad son los originales. No se ejecuta hito12.common.
    """
    path = ROOT / 'hito12' / (name+'.py')
    tree = ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    allowed = {'math', 'random', 'collections', 'datetime'}
    removed = set()
    body = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module in replacements:
            names = {alias.name for alias in node.names}
            if any(alias.asname for alias in node.names) or names != set(replacements[node.module]):
                raise RuntimeError('Cambió la dependencia del generador histórico; revisar adaptación Hito 13.')
            removed.add(node.module)
            continue
        if isinstance(node, ast.ImportFrom) and node.module not in allowed:
            raise RuntimeError('Import histórico no permitido por la adaptación.')
        if isinstance(node, ast.Import) and any(alias.name not in allowed for alias in node.names):
            raise RuntimeError('Import histórico no permitido por la adaptación.')
        body.append(node)
    if removed != set(replacements):
        raise RuntimeError('No se reconocieron las dependencias históricas esperadas.')
    tree.body = body
    namespace = {'__name__':'hito13_'+name, '__file__':str(path)}
    for values in replacements.values():
        namespace.update(values)
    exec(compile(tree, str(path), 'exec'), namespace)
    return SimpleNamespace(**namespace)


def dataset_module():
    return load_pure_module('dataset', {
        'hito12.common':dict(DATABASE=DATABASE, GENERATED=GENERATED, ROOT=ROOT,
                             digest=digest, read_json=read_json, write_json=write_json),
        'hito12.profiles':dict(DATASET_CONFIG='config/dataset.json')})


def command(args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=30)
    if result.returncode:
        raise RuntimeError('Comando local fallido: '+ ' '.join(args[:3]))
    return result.stdout.strip()


def check_service(item, service):
    labels = item['Config'].get('Labels', {})
    if (labels.get('com.docker.compose.project') != PROJECT or
        labels.get('com.docker.compose.service') != service or labels.get('edu.fixture.hito') != '13' or
        not item['State']['Running']):
        raise RuntimeError('Servicio sin identidad Hito 13 o detenido: '+service)
    port, internal = ('18183','8181/tcp') if service == 'influxdb' else ('8013','8000/tcp')
    bindings = item['HostConfig']['PortBindings'].get(internal, [])
    if bindings != [{'HostIp':'127.0.0.1', 'HostPort':port}]:
        raise RuntimeError('Puerto de servicio fuera de alcance: '+service)
    if set(item['NetworkSettings']['Networks']) != {PROJECT+'_laboratorio', PROJECT+'_acceso'}:
        raise RuntimeError('Redes inesperadas: '+service)
    limit = item['HostConfig']['Memory']
    if not 0 < limit <= (2*2**30 if service=='influxdb' else 512*2**20):
        raise RuntimeError('Límite de RAM ausente o superior al previsto.')
    cpu = item['HostConfig']['NanoCpus']
    if not 0 < cpu <= (2*10**9 if service=='influxdb' else 10**9):
        raise RuntimeError('Límite de CPU ausente o superior al previsto.')
    if service == 'influxdb':
        mounts = item['Mounts']
        if len(mounts)!=1 or not (mounts[0]['Type']=='volume' and mounts[0]['Name']==VOLUME
                and mounts[0]['Destination']=='/var/lib/influxdb3' and mounts[0]['RW']):
            raise RuntimeError('InfluxDB no monta exclusivamente el volumen Hito 13 esperado.')
        if '--node-id=hito13-g09' not in item['Config']['Cmd']:
            raise RuntimeError('Node ID inesperado.')
    else:
        env = dict(entry.split('=',1) for entry in item['Config']['Env'] if '=' in entry)
        if env.get('INFLUX_URL') != 'http://influxdb:8181':
            raise RuntimeError('API conectada a una dependencia inesperada.')


def check_environment():
    if ROOT.name != 'Hito_13_Grupo09_Monitoreo' or os.environ.get('DOCKER_HOST') or os.environ.get('DOCKER_CONTEXT'):
        raise RuntimeError('Se requiere la carpeta propia y el contexto Docker local.')
    endpoint = command(['docker','context','inspect','--format','{{.Endpoints.docker.Host}}'])
    if not endpoint.startswith(('npipe://','unix://')):
        raise RuntimeError('No se permite Docker remoto.')
    cfg = json.loads(command(COMPOSE+['config','--format','json']))
    if (cfg['name'] != PROJECT or cfg['volumes']['datos_hito13'].get('external') or
        cfg['volumes']['datos_hito13']['name'] != VOLUME):
        raise RuntimeError('Compose o volumen fuera de alcance.')
    info = json.loads(command(['docker','info','--format','{{json .}}']))
    if info['OSType']!='linux' or info['MemTotal'] < 4*2**30 or info['NCPU']<2:
        raise RuntimeError('Docker debe ser Linux con 4 GiB y 2 CPU como mínimo.')
    if psutil.virtual_memory().available < 768*2**20 or shutil.disk_usage(ROOT).free < 256*2**20:
        raise RuntimeError('Se requieren 768 MiB RAM host y 256 MiB disco libres.')
    services = {}
    for service in ('influxdb','api'):
        cid = command(COMPOSE+['ps','--quiet',service])
        if not cid or len(cid.splitlines())!=1:
            raise RuntimeError('Iniciar el laboratorio antes de preparar datos: '+service)
        item = json.loads(command(['docker','inspect',cid]))[0]
        check_service(item, service)
        services[service] = {'id':item['Id'], 'image':item['Config']['Image'], 'image_id':item['Image'],
                             'memory_bytes':item['HostConfig']['Memory'], 'nano_cpus':item['HostConfig']['NanoCpus']}
    volume = json.loads(command(['docker','volume','inspect',VOLUME]))[0]
    if volume.get('Labels',{}).get('com.docker.compose.project') != PROJECT:
        raise RuntimeError('Volumen sin identidad de proyecto esperada.')
    return {'docker':{k:info.get(k) for k in ('ServerVersion','OSType','NCPU','MemTotal')},
            'services':services, 'volume':{'name':volume['Name'],'created_at':volume['CreatedAt']},
            'host_available_memory_bytes':psutil.virtual_memory().available,
            'host_free_disk_bytes':shutil.disk_usage(ROOT).free}


class Database:
    def __init__(self, client, report):
        self.client, self.report = client, report

    def request(self, method, path, **kwargs):
        started = time.perf_counter()
        try:
            response = self.client.request(method, INFLUX+path, **kwargs)
        except httpx.HTTPError:
            self.report['operations'].append({'kind':path, 'method':method, 'status':None,
                                              'latency_ms':(time.perf_counter()-started)*1000})
            raise
        self.report['operations'].append({'kind':path,'method':method,'status':response.status_code,
                                          'latency_ms':(time.perf_counter()-started)*1000})
        return response

    def sql(self, query):
        response = self.request('GET','/api/v3/query_sql', params={'db':DATABASE,'q':query,'format':'json'})
        response.raise_for_status()
        rows = response.json()
        if not isinstance(rows,list):
            raise RuntimeError('Respuesta SQL inesperada.')
        return rows

    def existing_count(self):
        try:
            return int(self.sql('SELECT COUNT(*) AS total FROM estadisticas_equipo')[0]['total'])
        except httpx.HTTPStatusError as exc:
            text = exc.response.text.lower()
            if (exc.response.status_code in (400,404) and
                ('database not found: hito12_g09' in text or
                 ('estadisticas_equipo' in text and ('not found' in text or 'does not exist' in text)))):
                self.report['initial_state'] = 'expected_database_or_table_missing'
                return 0
            raise  # Red, autenticación y errores internos nunca significan base vacía.


def point_key(row):
    return tuple(row[k] for k in ('time','partido_id','equipo_codigo','sede_id'))


def missing_for_match(dataset, cfg, index, observed):
    expected = {point_key(row):row for row in dataset.canonical_rows(list(dataset.rows_for_match(cfg,index)),raw=True)}
    seen = set()
    for row in dataset.canonical_rows(observed,raw=True):
        key = point_key(row)
        if key in seen or key not in expected or row != expected[key]:
            raise RuntimeError('Datos ajenos, duplicados o alterados: no se sobrescriben ni se borran.')
        seen.add(key)
    return [dataset.line_protocol(row) for key,row in expected.items() if key not in seen]


def missing_lines(dataset, cfg, count, db):
    if not 0 <= count <= 51840:
        raise RuntimeError('Cantidad de datos incompatible: no se escribe.')
    lines, observed_count = [], 0
    for index, match in enumerate(dataset.match_ids(cfg),1):
        observed = db.sql("SELECT time, partido_id, equipo_codigo, sede_id, posesion_pct, "
                          "pases_completados_total, tiros_intervalo, recuperaciones_intervalo "
                          "FROM estadisticas_equipo WHERE partido_id = '"+match+"' ORDER BY time, equipo_codigo, sede_id") if count else []
        observed_count += len(observed)
        lines.extend(missing_for_match(dataset,cfg,index,observed))
    if observed_count != count or len(lines)+count != 51840:
        raise RuntimeError('Hay filas de otros partidos o cambios concurrentes; no se escribe.')
    return lines


def summarize(report, started):
    elapsed = time.perf_counter()-started
    latencies = sorted(op['latency_ms'] for op in report['operations'])
    report.update(finished_utc=now(), duration_seconds=elapsed, operations_total=len(latencies),
                  concurrency=1, rows_acknowledged_per_second_including_validation=report['acknowledged_records']/elapsed,
                  errors_http_4xx_5xx=sum(op['status'] is None or op['status']>=400 for op in report['operations']))
    report['latency_ms_all_operations'] = {f'p{p}':latencies[max(0,math.ceil(len(latencies)*p/100)-1)] for p in (50,95,99)} if latencies else {}
    report['latency_method']='nearest-rank; mezcla health, SQL y lotes; no es benchmark de estadísticas'


def prepare():
    report = {'start_utc':now(),'project':PROJECT,'database':DATABASE,'target':INFLUX,
              'commit':None,'commit_note':'No existe Git propio de esta copia; fuentes identificadas con SHA256.',
              'completed':False,'expected_records':51840,'batch_size':1000,'attempted_records':0,
              'acknowledged_records':0,'operations':[],'write_semantics':'Solo faltantes tras validar cada fila existente; claves deterministas, sin borrados ni reintentos automáticos.'}
    started = time.perf_counter()
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    evidence = EVIDENCE / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'_dataset.json')
    lock = None
    try:
        report['environment_before'] = check_environment()
        RUNTIME.mkdir(parents=True,exist_ok=True)
        lock_path = RUNTIME/'preparacion-dataset.lock'
        lock = lock_path.open('x',encoding='utf-8')
        lock.write(str(os.getpid())); lock.flush()
        cfg = read_json(ROOT/'config/dataset.json')
        if cfg != EXPECTED:
            raise RuntimeError('El preparador requiere el dataset estándar exacto de 51.840 filas.')
        dataset = dataset_module()
        manifest = dataset.generate(cfg, GENERATED)
        if manifest['rows'] != 51840:
            raise RuntimeError('Cantidad inesperada del generador.')
        report['manifest'] = manifest
        report['source_sha256'] = {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [
            ROOT/'hito12/dataset.py',ROOT/'hito12/integrity.py',ROOT/'config/dataset.json',
            Path(__file__),ROOT/'scripts/hito13/preparar_datos.ps1',ROOT/'compose.yaml',
            ROOT/'scripts/common.ps1',ROOT/'hito12/common.py']}
        report['versions']={name:importlib.metadata.version(name) for name in ('httpx','psutil')}
        report['python']=sys.version.split()[0]
        with httpx.Client(timeout=30,trust_env=False,follow_redirects=False) as client:
            identity = client.get(API+'/lab/identity');identity.raise_for_status()
            if identity.json().get('lab')!=PROJECT or identity.json().get('database')!=DATABASE:
                raise RuntimeError('Identidad HTTP de API inesperada.')
            report['api_identity']=identity.json()
            db = Database(client,report)
            db.request('GET','/health').raise_for_status()
            count = db.existing_count()
            report['existing_records']=count
            lines = missing_lines(dataset,cfg,count,db)
            report['missing_records']=len(lines)
            # Revalidar identidad tras generación/preflight y antes de cualquier escritura.
            checked = check_environment()
            if checked['volume']!=report['environment_before']['volume'] or checked['services']!=report['environment_before']['services']:
                raise RuntimeError('El destino cambió durante la preparación.')
            for offset in range(0,len(lines),1000):
                batch = lines[offset:offset+1000]
                if psutil.virtual_memory().available < 512*2**20:
                    raise RuntimeError('RAM host insuficiente; se puede reanudar sin duplicar.')
                report['attempted_records'] += len(batch)
                response = db.request('POST','/api/v3/write_lp',
                    params={'db':DATABASE,'precision':'second','accept_partial':'false','no_sync':'false'},
                    content=''.join(batch).encode(),headers={'Content-Type':'text/plain'})
                response.raise_for_status()
                report['acknowledged_records'] += len(batch)
                time.sleep(.05)
            integrity_module = load_pure_module('integrity',{
                'hito12.common':dict(digest=digest,now=now,sql=lambda _client,query:db.sql(query)),
                'hito12.dataset':dict(canonical_rows=dataset.canonical_rows)})
            report['integrity']=integrity_module.validate_source(client,manifest)
            if not report['integrity']['passed']:
                raise RuntimeError('Falló la lectura completa de integridad; no se borran ni reparan datos.')
            params = dict(desde=manifest['from'],hasta=manifest['to'],resolucion='5m')
            api_start=time.perf_counter()
            response=client.get(API+'/api/v1/partidos/P001/estadisticas',params=params)
            api_ms=(time.perf_counter()-api_start)*1000
            report['operations'].append({'kind':'statistics','method':'GET','status':response.status_code,'latency_ms':api_ms})
            report['api_statistics']={'status':response.status_code,'match':'P001','params':params,'latency_ms':api_ms}
            response.raise_for_status()
            passed = dataset.validate_response(response.json(),{'match':'P001','resolution':'5m'},manifest)
            report['api_statistics'].update(oracle_passed=passed,items=len(response.json()['data']['items']))
            if not passed:
                raise RuntimeError('API 200 pero su resultado no coincide con el oráculo determinista.')
        report['environment_after']=check_environment()
        if report['environment_before']['volume']!=report['environment_after']['volume']:
            raise RuntimeError('Cambió la identidad del volumen.')
        report['completed']=True
    except BaseException as exc:
        report['failure_type']=type(exc).__name__
        report['failure_note']=str(exc) if isinstance(exc,RuntimeError) else 'Fallo local/HTTP; consultar tipo y operaciones saneadas. Un lote sin confirmación puede haberse aplicado: reejecutar valida faltantes.'
        raise
    finally:
        if lock is not None:
            lock.close()
            (RUNTIME/'preparacion-dataset.lock').unlink()
        summarize(report,started)
        write_json(evidence,report)
        print('Evidencia:',evidence)
    print(json.dumps({'completed':report['completed'],'existing_records':count,'written_records':report['acknowledged_records'],
                      'actual_records':report['integrity']['actual_records'],'duplicates':report['integrity']['duplicates'],
                      'integrity_passed':report['integrity']['passed'],'statistics_http':report['api_statistics']['status'],
                      'statistics_oracle_passed':report['api_statistics']['oracle_passed']},indent=2))
    return report


if __name__=='__main__':
    prepare()
