"""Ensaio HTTP explícito; requer Compose já iniciado. Não chama OpenAI real.

mock: para/inicia apenas os dois workers; health: para/inicia Redis;
failure: exige perfil compose.lesson03-failure.yaml já iniciado.
Não faz purge/down -v, não muda tags nem publica.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from uuid import uuid4

BASE='http://127.0.0.1:8000'
parser=argparse.ArgumentParser()
parser.add_argument('demo',choices=['mock','health','failure'])
args=parser.parse_args()
lines=[]
workers_paused=False

def record(text):
    lines.append(text);print(text,flush=True)

def docker(*argv):
    result=subprocess.run(['docker','compose',*argv],text=True,capture_output=True,check=True)
    record('$ docker compose '+' '.join(argv)+'\n'+result.stdout.strip())
    return result.stdout

def http(path,body=None,headers=None):
    request=Request(BASE+path,data=json.dumps(body).encode() if body is not None else None,
                    headers={'Content-Type':'application/json'}| (headers or {}))
    started=time.perf_counter()
    try:
        response=urlopen(request,timeout=15)
    except HTTPError as error:
        response=error
    data=json.load(response)
    record(f'{request.get_method()} {path} → {response.status} ({time.perf_counter()-started:.3f}s)\n'+
           json.dumps(data,ensure_ascii=False))
    return response.status,data

try:
    if args.demo=='health':
        assert http('/health')[0]==200 and http('/ready')[0]==200
        docker('stop','redis')
        try:
            assert http('/health')[0]==200
            assert http('/ready')[0]==503
        finally:
            docker('start','redis')
        for _ in range(20):
            if http('/ready')[0]==200:break
            time.sleep(1)
        else:raise AssertionError('Readiness não recuperou')
    else:
        version='validation-'+uuid4().hex[:12]
        trace=uuid4().hex
        body={'incident_id':'HTTP-VALIDATION','version':version}
        if args.demo=='mock':
            body['demo_delay_ms']=3000
            docker('stop','worker-a','worker-b')
            workers_paused=True
        else:
            body.update(llm_failure='timeout',fallback='deterministic_reference')
        code,accepted=http('/incidents',body,{'X-Trace-ID':trace,'X-Correlation-ID':version})
        assert code==202 and accepted['created']
        uid=accepted['execution_id'];path='/executions/'+uid
        if args.demo=='mock':
            assert http(path)[1]['status']=='queued'
            assert http(path+'/result')[0]==202
            docker('start','worker-a','worker-b')
            workers_paused=False
        observed=set()
        for _ in range(60):
            code,state=http(path);observed.add(state['status'])
            assert state['trace_id']==trace
            if state['status'] in ('completed','failed'):break
            time.sleep(.5)
        assert state['status']=='completed'
        code,events=http(path+'/events?limit=100');assert code==200
        code,result=http(path+'/result');assert code==200 and not result['actions_executed']
        if args.demo=='mock':
            assert 'running' in observed
            assert result['mode']=='mock' and result['estimated_cost_brl']=='12500.00'
        else:
            assert result['outcome']=='degraded_recommendation'
            assert 'llm.fallback_activated' in {e['event_type'] for e in events['events']}
        code,duplicate=http('/incidents',body,{'X-Trace-ID':uuid4().hex})
        assert code==202 and duplicate['execution_id']==uid and not duplicate['created']
        assert duplicate['trace_id']==trace
        code,_=http('/incidents',body|{'reference_case_id':'unsupported'})
        assert code==422
        time.sleep(1)
        output=subprocess.run(['docker','compose','logs','--no-color','api','worker-a','worker-b'],
                              text=True,capture_output=True,check=True).stdout
        matching=[line for line in output.splitlines() if trace in line]
        record('LOGS CORRELACIONADOS\n'+'\n'.join(matching))
        assert any('worker.received' in line for line in matching)
        assert any('worker.finished' in line for line in matching)
        if args.demo=='failure':
            assert any('llm.fallback_activated' in line for line in matching)
    record('PASS: '+args.demo)
finally:
    if workers_paused:
        subprocess.run(['docker','compose','start','worker-a','worker-b'], check=False)
    target=Path('artifacts/lesson03-start');target.mkdir(parents=True,exist_ok=True)
    (target/(args.demo+'-http.txt')).write_text('\n\n'.join(lines)+'\n')
