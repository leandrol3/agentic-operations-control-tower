"""Ensaio real opt-in. Inicia só seus workers; mata apenas um desses processos.

Requer Compose saudável. Preserva banco, broker e logs; não usa purge/flush.
Executar da raiz: uv run python scripts/validate_lesson02_complete.py
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from uuid import uuid4
from control_tower.distributed.store import Store

ROOT=Path.cwd()
OUT=ROOT/'artifacts/lesson02-complete'
OUT.mkdir(parents=True,exist_ok=True)
RUN='validation-'+uuid4().hex[:8]
store=Store()
workers={}
logs=[]


def cli(*args):
    result=subprocess.run([sys.executable,'-m','control_tower.main',*args],text=True,capture_output=True,check=True)
    with (OUT/'commands.txt').open('a') as f:
        f.write('$ control-tower '+' '.join(args)+'\n'+result.stdout+'\n')
    return result.stdout


def wait_for(predicate, timeout=150):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        result=predicate()
        if result:
            return result
        time.sleep(.25)
    raise AssertionError('Prazo do ensaio excedido; ver logs em artifacts/lesson02-complete')


def executions(version):
    # Selecionar IDs registrados pelo producer evita interferir com ensaios anteriores.
    return [store.get(identity) for identity in IDS[version]]


def enqueue(version, count=1, **options):
    args=['enqueue','--count',str(count),'--version',version]
    for key,value in options.items():
        args.extend(['--'+key.replace('_','-'),str(value)])
    cli(*args)
    from control_tower.distributed.idempotency import idempotency_key
    from control_tower.distributed.incidents import generate_incidents
    identities=[]
    with store.connect() as conn:
        for incident in generate_incidents(count):
            row=conn.execute('SELECT execution_id FROM ct_executions WHERE idempotency_key=%s',
                            (idempotency_key(incident.incident_id,version=version),)).fetchone()
            identities.append(str(row['execution_id']))
    IDS[version]=identities
    return identities


def capture(version):
    for identity in IDS[version]:
        (OUT/f'{identity}.json').write_text(store.get(identity).model_dump_json(indent=2))
        (OUT/f'{identity}-events.json').write_text(json.dumps([e.model_dump(mode='json') for e in store.events(identity)],indent=2))
    identity=IDS[version][0]
    for command in ('execution','events','result'):
        cli(command,identity)
    cli('events',identity,'--lifecycle')


IDS={}
try:
    cli('db-init')
    for name in ('A','B'):
        log=(OUT/f'worker-{name}.log').open('w')
        logs.append(log)
        process=subprocess.Popen([sys.executable,'-m','celery','-A','control_tower.distributed.celery_app',
            'worker','--pool=solo','--concurrency=1','--hostname',f'lesson02-{name}@%h','--loglevel=INFO',
            '--without-gossip','--without-mingle'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        workers[name]=process
    wait_for(lambda: all(' ready.' in (OUT/f'worker-{n}.log').read_text() for n in workers),30)
    batch=RUN+'-batch'
    enqueue(batch,20,demo_delay_ms=500)
    cli('executions')
    wait_for(lambda: all(e.status=='completed' for e in executions(batch)),60)
    used={e.worker_id.split(':')[0] for e in executions(batch)}
    assert len(used)==2,used
    print('BATCH: 20 completed; dois workers distintos',flush=True)
    capture(batch)
    duplicate=RUN+'-duplicate'
    first=enqueue(duplicate,demo_delay_ms=1500)
    second=enqueue(duplicate,demo_delay_ms=1500)
    assert first==second
    wait_for(lambda: executions(duplicate)[0].status=='completed')
    assert executions(duplicate)[0].attempt==1
    capture(duplicate)
    print('DUPLICATE: mesma execution, attempt=1',flush=True)
    retry=RUN+'-retry'
    enqueue(retry,fail_specialist='logistics')
    wait_for(lambda: executions(retry)[0].status=='completed')
    assert executions(retry)[0].attempt==2
    capture(retry)
    print('RETRY: logistics falhou na tentativa 1; completed na 2',flush=True)
    lost=RUN+'-lost'
    enqueue(lost,demo_delay_ms=10000)
    running=wait_for(lambda: next((e for e in executions(lost) if e.status=='running'),None))
    name='A' if 'lesson02-A@' in running.worker_id else 'B'
    victim=workers[name]
    assert running.worker_id.endswith(':'+str(victim.pid))
    victim.kill()  # SIGKILL somente no subprocesso criado por este ensaio
    victim.wait(timeout=5)
    print(f'WORKER LOSS: {name} pid={victim.pid} encerrado; aguardando visibility timeout/redelivery',flush=True)
    wait_for(lambda: executions(lost)[0].status=='completed',150)
    recovered=executions(lost)[0]
    assert recovered.attempt==2 and recovered.worker_id!=running.worker_id
    capture(lost)
    cli('executions')
    summary={'run':RUN,'ids':IDS,'batch_workers':sorted(used),
             'lost_worker':running.worker_id,'recovered_worker':recovered.worker_id,'recovered_attempt':recovered.attempt}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2),flush=True)
finally:
    for process in workers.values():
        if process.poll() is None:
            process.terminate()
    for process in workers.values():
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    for log in logs:
        log.close()
