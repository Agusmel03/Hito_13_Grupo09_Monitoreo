"""Validación acotada, solo laboratorio local; guarda evidencia saneada, no credenciales."""
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[2]
assert ROOT.name == 'Hito_13_Grupo09_Monitoreo'
OUT = ROOT / 'docs/hito13/evidencia/validacion_local.json'
COMPOSE = ['docker', 'compose', '-p', 'hito13-g09', '-f', str(ROOT/'compose.yaml')]

def command(args):
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
    return {'command':args, 'exit_code':p.returncode, 'stdout':p.stdout.strip(), 'stderr':p.stderr.strip()}

def get(url):
    try:
        with urlopen(url, timeout=8) as response:
            text = response.read().decode()
            return {'status':response.status, 'body':json.loads(text)}
    except HTTPError as e:
        return {'status':e.code, 'body':e.read().decode()[:500]}

record = {'start_utc':datetime.now(timezone.utc).isoformat(), 'project':'hito13-g09',
          'commit':None, 'commit_note':'Git raíz es perfil del usuario, no commit propio de esta copia; usar SHA256.',
          'host':{'system':platform.system(),'release':platform.release(),'python':platform.python_version()},
          'scope':'Validación de observabilidad; sin inserciones, carga pesada ni integridad lógica de datos.',
          'commands':[]}
assert not os.environ.get('DOCKER_HOST') and not os.environ.get('DOCKER_CONTEXT'), 'Se requiere contexto local'
endpoint = command(['docker','context','inspect','--format','{{.Endpoints.docker.Host}}'])
assert endpoint['exit_code']==0 and endpoint['stdout'].startswith(('npipe://','unix://')), 'Daemon no local'
info = command(['docker','info','--format','{{json .}}'])
assert info['exit_code']==0
raw = json.loads(info['stdout'])
record['docker']={k:raw.get(k) for k in ['ServerVersion','NCPU','MemTotal','OSType','Architecture']}
record['commands'].append(command(COMPOSE+['config','--quiet']))
record['commands'].append(command(['git','check-ignore','.runtime/hito13/grafana_admin_password','.venv/Scripts/python.exe']))
record['commands'].append(command(['powershell','-NoProfile','-Command', '$allErrors = @(); Get-ChildItem scripts/hito13/*.ps1 | ForEach-Object { $tokens=$null; $errs=$null; $null=[System.Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$tokens,[ref]$errs); $allErrors += $errs }; if ($allErrors.Count) { $allErrors; exit 1 }; Write-Output "PowerShell syntax OK"']))
record['commands'].append(command(['docker','compose','-p','hito13-g09','-f',str(ROOT/'compose.compacto.yaml'),'config','--quiet']))
record['commands'].append(command(COMPOSE+['exec','-T','prometheus','promtool','check','config','/etc/prometheus/prometheus.yml']))
record['commands'].append(command(COMPOSE+['exec','-T','prometheus','promtool','check','rules','/etc/prometheus/alerts.yml']))
record['commands'].append(command([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider','--basetemp','.runtime/hito13/pytest-validacion-dataset','tests/test_hito13_dataset.py','tests/test_api.py','tests/test_monitoring.py','tests/test_connections.py']))
config=json.loads(command(COMPOSE+['config','--format','json'])['stdout'])
assert config['name']=='hito13-g09'
record['config']={n:{k:v.get(k) for k in ['image','cpus','mem_limit','ports']} for n,v in config['services'].items()}
ids=command(COMPOSE+['ps','--all','--quiet'])['stdout'].splitlines()
record['containers']=[]
for cid in ids:
    item=json.loads(command(['docker','inspect',cid])['stdout'])[0]
    assert item['Config']['Labels']['com.docker.compose.project']=='hito13-g09'
    record['containers'].append({'service':item['Config']['Labels']['com.docker.compose.service'],
      'image':item['Config']['Image'],'image_id':item['Image'],'state':item['State']['Status'],
      'memory_bytes':item['HostConfig']['Memory'],'nano_cpus':item['HostConfig']['NanoCpus'],
      'networks':list(item['NetworkSettings']['Networks']),
      'mounts':[{'type':m['Type'],'name':m.get('Name'),'destination':m['Destination']} for m in item['Mounts']]})
record['resources_snapshot']=command(COMPOSE+['stats','--no-stream','--format','json'])
record['grafana_health']=get('http://127.0.0.1:13013/api/health')
record['grafana_dashboard']=get('http://127.0.0.1:13013/api/dashboards/uid/fixture2030-hito13')
record['grafana_datasource']=get('http://127.0.0.1:13013/api/datasources/uid/prometheus-hito13')
for attempt in range(30):
    record['targets']=get('http://127.0.0.1:19013/api/v1/targets')['body']['data']['activeTargets']
    if len(record['targets'])==6 and all(t['health']=='up' for t in record['targets']):
        break
    time.sleep(2)
# Targets are static local addresses. Do not collect container env or raw logs.
record['targets']=[{k:t[k] for k in ['labels','health','lastScrape','lastError']} for t in record['targets']]
record['probes']=get('http://127.0.0.1:19013/api/v1/query?'+urlencode({'query':'probe_success{job="probes"}'}))
record['api_identity']=get('http://127.0.0.1:8013/lab/identity')
record['influx_readonly_query']=get('http://127.0.0.1:18183/api/v3/query_sql?'+urlencode({'db':'hito12_g09','q':'SELECT COUNT(*) AS total FROM estadisticas_equipo','format':'json'}))
record['dashboard_queries']=[]
dashboard=json.loads((ROOT/'monitoring/grafana/dashboards/hito13.json').read_text(encoding='utf-8'))
for panel in dashboard['panels']:
    for target in panel['targets']:
        result=get('http://127.0.0.1:19013/api/v1/query?'+urlencode({'query':target['expr']}))
        record['dashboard_queries'].append({'panel':panel['id'],'expression':target['expr'],'http_status':result['status'],'result':result['body']})
paths=[ROOT/'compose.yaml',ROOT/'compose.compacto.yaml',ROOT/'Dockerfile',ROOT/'requirements-lock.txt']
for folder in ['app','monitoring','scripts/hito13','tests']:
    paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
record['source_sha256']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
record['evidence_files']=[p.name for p in OUT.parent.glob('*.json') if p!=OUT]
record['end_utc']=datetime.now(timezone.utc).isoformat()
record['checks']={
 'commands_pass':all(c['exit_code']==0 for c in record['commands']),
 'six_targets_up':len(record['targets'])==6 and all(t['health']=='up' for t in record['targets']),
 'two_probes_success':len(record['probes']['body']['data']['result'])==2 and all(p['value'][1]=='1' for p in record['probes']['body']['data']['result']),
 'dashboard_provisioned':record['grafana_dashboard']['status']==200,
 'datasource_provisioned':record['grafana_datasource']['status']==200,
 'all_dashboard_promql_valid':all(q['http_status']==200 and q['result'].get('status')=='success' for q in record['dashboard_queries'])}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record['checks'],indent=2))
print('Evidencia:',OUT)
sys.exit(0 if all(record['checks'].values()) else 1)
