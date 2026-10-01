"""Baseline local da Aula 2: concorrência provada por sincronização, não por benchmark frágil."""
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from threading import Barrier, Lock
import time
from uuid import uuid4

from pydantic import ValidationError
import pytest
import yaml

from control_tower.distributed import batch
from control_tower.distributed.batch import BatchOptions, run_batch, render_batch
from control_tower.distributed.events import ExecutionEvent
from control_tower.distributed.idempotency import IdempotencyIdentity, idempotency_key
from control_tower.distributed.incidents import MIX, generate_incidents
from control_tower.distributed.models import Execution

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026,10,1,8,tzinfo=timezone.utc)


def test_generator_500_exact_mix_unique_ids_and_fixed_dates():
    incidents = generate_incidents()
    assert len(incidents) == 500
    assert len({i.incident_id for i in incidents}) == 500
    assert Counter(i.incident_type for i in incidents) == MIX
    assert incidents[0].created_at == NOW
    assert all(i.created_at.tzinfo is not None and i.payload['synthetic'] is True for i in incidents)
    assert all(i.payload['reference_case_id'] == 'INCIDENT-001' for i in incidents)
    assert all(i.model_dump().keys() == {'incident_id','incident_type','plant','severity',
                                       'created_at','business_priority','payload'} for i in incidents)


def test_generator_is_deterministic_and_does_not_mutate_global_rng():
    import random
    before = random.getstate()
    first = generate_incidents(500,42)
    assert first == generate_incidents(500,42)
    assert first != generate_incidents(500,43)
    assert random.getstate() == before


@pytest.mark.parametrize('count',[1,7,10,501,1000])
def test_generator_scales_counts(count):
    assert len(generate_incidents(count)) == count


@pytest.mark.parametrize('count',[0,-1,5001,True])
def test_generator_rejects_invalid_count(count):
    with pytest.raises(ValueError):
        generate_incidents(count)


def terminal(**changes):
    values=dict(execution_id=uuid4(),incident_id='NC-1',status='completed',started_at=NOW,
                completed_at=NOW+timedelta(seconds=1),current_step='awaiting_approval',
                worker_id='local:1',workflow_status='awaiting_approval')
    return Execution(**(values|changes))


def test_execution_lifecycle_contract_and_roundtrip():
    queued=Execution(execution_id=uuid4(),incident_id='NC-1')
    assert queued.status=='queued' and queued.attempt==1
    finished=terminal()
    assert Execution.model_validate_json(finished.model_dump_json())==finished
    assert finished.status=='completed' and finished.workflow_status=='awaiting_approval'


@pytest.mark.parametrize('changes',[
    {'status':'unknown'}, {'completed_at':None}, {'completed_at':NOW-timedelta(seconds=1)},
    {'started_at':None}, {'worker_id':None}, {'current_step':None}, {'attempt':0},
    {'status':'failed'}, {'error':'failure'}, {'status':'running'}, {'status':'queued'},
    {'started_at':NOW.replace(tzinfo=None)}, {'workflow_status':'blocked'},
])
def test_execution_rejects_incoherent_state(changes):
    with pytest.raises(ValidationError):
        terminal(**changes)


def test_execution_event_contract_future_fields_null():
    event=ExecutionEvent(execution_id=uuid4(),incident_id='NC-1',agent_id='supply',
                         event_type='step_completed',timestamp=NOW,status='running',duration_ms=2,sequence=1)
    assert all(getattr(event,key) is None for key in
               ('input_tokens','output_tokens','estimated_cost','quality_score','business_outcome'))
    assert ExecutionEvent.model_validate_json(event.model_dump_json()) == event


@pytest.mark.parametrize('changes',[
    {'duration_ms':-1}, {'duration_ms':float('nan')}, {'input_tokens':-1}, {'quality_score':1.1},
    {'quality_score':float('nan')}, {'estimated_cost':'-1'}, {'sequence':0},
    {'timestamp':NOW.replace(tzinfo=None)}, {'status':'completed'}, {'agent_id':' '},
])
def test_execution_event_rejects_invalid_metadata(changes):
    values=dict(execution_id=uuid4(),incident_id='NC-1',agent_id='supply',
                event_type='step_completed',timestamp=NOW,status='running',duration_ms=2,sequence=1)
    with pytest.raises(ValidationError):
        ExecutionEvent(**(values|changes))


def test_idempotency_same_logical_operation_same_key():
    assert idempotency_key('NC-1','analyze','v1') == idempotency_key('NC-1','analyze','v1')
    assert IdempotencyIdentity(incident_id='NC-1',operation='analyze').idempotency_key == idempotency_key('NC-1','analyze')


@pytest.mark.parametrize('other',[('NC-2','analyze','v1'),('NC-1','notify','v1'),('NC-1','analyze','v2')])
def test_idempotency_scope_includes_incident_operation_and_version(other):
    assert idempotency_key('NC-1','analyze','v1') != idempotency_key(*other)


def test_idempotency_no_separator_collision_and_stable_across_processes():
    assert idempotency_key('a:b','c') != idempotency_key('a','b:c')
    code="from control_tower.distributed.idempotency import idempotency_key; print(idempotency_key('NC-1'))"
    out=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,check=True)
    assert out.stdout.strip()==idempotency_key('NC-1')


@pytest.mark.parametrize('field',['incident_id','operation','version'])
def test_idempotency_empty_components_rejected(field):
    with pytest.raises(ValidationError):
        IdempotencyIdentity(**(dict(incident_id='NC-1',operation='analyze',version='v1')|{field:' '}))


def test_batch_e2e_matches_envelopes_preserves_pending_approval():
    incidents=generate_incidents(10)
    report=run_batch(ROOT,incidents,BatchOptions())
    assert report.completed==10 and report.failed==0 and report.max_active==1
    assert [e.incident_id for e in report.executions]==[i.incident_id for i in incidents]
    assert len({e.execution_id for e in report.executions})==10
    assert all(e.workflow_status=='awaiting_approval' and e.attempt==1 for e in report.executions)
    assert report.throughput == pytest.approx(report.completed/report.duration_s)
    assert len(render_batch(report).splitlines()) <=20
    assert max(map(len,render_batch(report).splitlines())) <=100
    for execution in report.executions:
        events=[event for event in report.events if event.execution_id==execution.execution_id]
        assert events[0].event_type=='execution_queued' and events[-1].event_type=='execution_completed'
        assert [e.sequence for e in events]==list(range(1,len(events)+1))
        join=next(e.sequence for e in events if e.agent_id=='consolidation' and e.event_type=='step_started')
        assert all(next(e.sequence for e in events if e.agent_id==n and e.event_type=='step_completed')<join
                   for n in ('supply','production','logistics'))


def test_five_local_workers_overlap_without_timing_assertion(monkeypatch):
    barrier=Barrier(5,timeout=10)
    original=batch.run_workflow
    def synchronized(*args,**kwargs):
        barrier.wait()
        return original(*args,**kwargs)
    monkeypatch.setattr(batch,'run_workflow',synchronized)
    report=run_batch(ROOT,generate_incidents(10),BatchOptions(workers=5))
    assert report.completed==10 and report.max_active==5
    assert len({e.worker_id for e in report.executions})==5


def test_provider_limit_bounds_work_and_exposes_contention(monkeypatch):
    barrier=Barrier(2,timeout=10)
    original=batch.run_workflow
    lock=Lock()
    active=peak=0
    def limited(*args,**kwargs):
        nonlocal active,peak
        with lock:
            active+=1
            peak=max(peak,active)
        barrier.wait()
        time.sleep(.02)
        try:
            return original(*args,**kwargs)
        finally:
            with lock:
                active-=1
    monkeypatch.setattr(batch,'run_workflow',limited)
    report=run_batch(ROOT,generate_incidents(10),BatchOptions(workers=10,provider_limit=2))
    assert report.completed==10 and report.max_active==peak==2
    assert report.waited>0 and report.max_waiting>0 and report.provider_wait_ms>0


def test_failure_releases_capacity_and_does_not_abort_remaining_incidents(monkeypatch):
    original=batch.run_workflow
    calls=0
    def fail_first(*args,**kwargs):
        nonlocal calls
        calls+=1
        if calls==1:
            raise ValueError('fixture failure')
        return original(*args,**kwargs)
    monkeypatch.setattr(batch,'run_workflow',fail_first)
    report=run_batch(ROOT,generate_incidents(3),BatchOptions(workers=1,provider_limit=1))
    assert report.completed==2 and report.failed==1
    assert report.executions[0].error=='ValueError: fixture failure'
    assert report.events[-1].event_type=='execution_completed'
    assert any(e.event_type=='execution_failed' for e in report.events)
    assert all(e.attempt==1 for e in report.executions)  # Nenhum retry escondido.


def test_duplicate_delivery_not_falsely_deduplicated_in_start():
    incident=generate_incidents(1)[0]
    report=run_batch(ROOT,(incident,incident),BatchOptions(workers=2))
    assert report.completed==2
    assert report.executions[0].incident_id==report.executions[1].incident_id
    assert report.executions[0].execution_id!=report.executions[1].execution_id


def test_batch_mock_cannot_call_network_even_if_environment_requests_openai(monkeypatch):
    monkeypatch.setenv('LLM_MODE','openai')
    monkeypatch.setenv('LANGSMITH_TRACING','true')
    def no_network(*args,**kwargs):
        pytest.fail('Baseline local tentou rede')
    monkeypatch.setattr(socket.socket,'connect',no_network)
    report=run_batch(ROOT,generate_incidents(2),BatchOptions(workers=2))
    assert report.completed==2 and report.mode=='mock'


@pytest.mark.parametrize('changes',[{'workers':0},{'workers':65},{'provider_limit':0},
                                    {'demo_delay_ms':-1},{'demo_delay_ms':2001}])
def test_batch_limits_are_explicit(changes):
    with pytest.raises(ValidationError):
        BatchOptions(**changes)


def test_compose_is_only_unconnected_local_infrastructure():
    config=yaml.safe_load((ROOT/'compose.yaml').read_text())
    assert set(config['services'])=={'redis','postgres'}
    for name,service in config['services'].items():
        assert service['healthcheck']['test']
        assert all(port.startswith('127.0.0.1:') for port in service['ports'])
        assert 'build' not in service and 'container_name' not in service
        assert service['volumes']
    assert config['services']['redis']['image']=='redis:7.4-alpine'
    assert config['services']['postgres']['image']=='postgres:16-alpine'


@pytest.mark.parametrize('args',[
    ['generate-incidents','--count','10'],['batch','--incidents','2','--workers','2'],['idempotency-demo'],
])
def test_new_cli_commands(args):
    result=subprocess.run([sys.executable,'-m','control_tower.main',*args],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==0,result.stderr
    assert len(result.stdout.splitlines())<=20


def test_generator_export_is_reproducible_and_refuses_overwrite(tmp_path):
    paths=[tmp_path/'a.jsonl',tmp_path/'b.jsonl']
    for path in paths:
        out=subprocess.run([sys.executable,'-m','control_tower.main','generate-incidents','--output',str(path)],
                           cwd=ROOT,text=True,capture_output=True)
        assert out.returncode==0
    assert paths[0].read_bytes()==paths[1].read_bytes()
    assert len(paths[0].read_text().splitlines())==500
    assert json.loads(paths[0].read_text().splitlines()[0])['incident_id']
    again=subprocess.run([sys.executable,'-m','control_tower.main','generate-incidents','--output',str(paths[0])],
                         cwd=ROOT,text=True,capture_output=True)
    assert again.returncode==2 and 'já existe' in again.stderr


def test_lesson01_frozen_files_unchanged():
    manifest=json.loads((ROOT/'tests/fixtures/lesson01-frozen.json').read_text())
    for name,expected in manifest.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
