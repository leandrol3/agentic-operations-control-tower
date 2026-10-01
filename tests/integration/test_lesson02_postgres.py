"""Banco real em schema isolado; sem apagar dados de demonstração."""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4
import pytest

pytest.importorskip('psycopg')
pytest.importorskip('celery')
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from celery.exceptions import Retry
from control_tower.distributed import tasks
from control_tower.distributed.config import database_url
from control_tower.distributed.durable import TaskOptions
from control_tower.distributed.idempotency import idempotency_key
from control_tower.distributed.incidents import generate_incidents
from control_tower.distributed.store import Store

pytestmark = pytest.mark.skipif(os.getenv('LESSON02_INTEGRATION')!='1',reason='Requer Compose e LESSON02_INTEGRATION=1')


@pytest.fixture
def store(monkeypatch):
    dsn=database_url()
    schema='test_'+uuid4().hex
    with psycopg.connect(dsn,autocommit=True) as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    isolated=make_conninfo(dsn,options=f'-c search_path={schema}')
    monkeypatch.setenv('LESSON02_DATABASE_URL',isolated)
    store=Store()
    store.initialize()
    try:
        yield store
    finally:
        with psycopg.connect(dsn,autocommit=True) as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def claim(store,**options):
    envelope=generate_incidents(1)[0]
    key=idempotency_key(envelope.incident_id)
    execution,_=store.claim(envelope,key,TaskOptions(**options))
    return execution,envelope,key


def test_atomic_concurrent_claim(store):
    envelope=generate_incidents(1)[0]
    barrier=Barrier(8)
    def submit(_):
        barrier.wait()
        return store.claim(envelope,idempotency_key(envelope.incident_id),TaskOptions())
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(submit,range(8)))
    assert sum(created for _,created in results)==1
    assert len({e.execution_id for e,_ in results})==1
    assert len(store.events(results[0][0].execution_id))==1


def test_conflicting_payload_rejected(store):
    execution,envelope,key=claim(store)
    with pytest.raises(ValueError,match='payload'):
        store.claim(envelope,key,TaskOptions(demo_delay_ms=10))


def test_session_lock_excludes_second_delivery_and_releases(store):
    e,envelope,key=claim(store)
    with store.acquire(e.execution_id,key,envelope.model_dump(mode='json')) as first:
        assert first.begin('A')
        with store.acquire(e.execution_id,key,envelope.model_dump(mode='json')) as second:
            assert second is None
    with store.acquire(e.execution_id,key,envelope.model_dump(mode='json')) as recovered:
        assert recovered.begin('B')
        assert recovered.execution.attempt==2
    assert 'execution.interrupted' in [e.event_type for e in store.events(e.execution_id)]


def test_full_workflow_persisted_and_duplicate_terminal_noop(store):
    e,envelope,key=claim(store)
    kwargs=dict(envelope=envelope.model_dump(mode='json'),execution_id=str(e.execution_id),idempotency_key=key)
    tasks.execute.run(**kwargs)
    final=store.get(e.execution_id)
    assert final.status=='completed' and final.attempt==1
    assert final.result.approval.required and not final.result.approval.actions_executed
    assert final.result.recommendation.incident_id=='INCIDENT-001'
    events=store.events(e.execution_id)
    expected={'execution.queued','execution.started','supervisor.completed','supply.completed','production.completed',
              'logistics.completed','finance.completed','challenger.completed','recommendation.completed','execution.completed'}
    assert expected <= {event.event_type for event in events}
    assert [event.sequence for event in events]==list(range(1,len(events)+1))
    tasks.execute.run(**kwargs)
    assert store.get(e.execution_id)==final and store.events(e.execution_id)==events


def test_retry_attempt_and_events(store,monkeypatch):
    e,envelope,key=claim(store,fail_specialist='logistics')
    countdowns=[]
    def retry(**kwargs):
        countdowns.append(kwargs['countdown'])
        raise Retry()
    monkeypatch.setattr(tasks.execute,'retry',retry)
    kwargs=dict(envelope=envelope.model_dump(mode='json'),execution_id=str(e.execution_id),idempotency_key=key)
    with pytest.raises(Retry):
        tasks.execute.run(**kwargs)
    assert store.get(e.execution_id).status=='queued'
    tasks.execute.run(**kwargs)
    final=store.get(e.execution_id)
    assert final.status=='completed' and final.attempt==2 and countdowns==[2]
    events=store.events(e.execution_id)
    assert {'logistics.failed','execution.retry'} <= {e.event_type for e in events}


def test_retry_budget_terminal_failure(store,monkeypatch):
    e,envelope,key=claim(store,fail_specialist='logistics',fail_always=True)
    def retry(**kwargs):
        raise Retry()
    monkeypatch.setattr(tasks.execute,'retry',retry)
    kwargs=dict(envelope=envelope.model_dump(mode='json'),execution_id=str(e.execution_id),idempotency_key=key)
    for _ in range(2):
        with pytest.raises(Retry):
            tasks.execute.run(**kwargs)
    with pytest.raises(tasks.WorkflowFailure):
        tasks.execute.run(**kwargs)
    final=store.get(e.execution_id)
    assert final.status=='failed' and final.attempt==3 and final.result is None
    tasks.execute.run(**kwargs)
    assert store.get(e.execution_id)==final


def test_redelivery_budget_after_repeated_worker_loss(store):
    e,envelope,key=claim(store)
    for i in range(3):
        with store.acquire(e.execution_id,key,envelope.model_dump(mode='json')) as session:
            assert session.begin(f'worker-{i}')
    with store.acquire(e.execution_id,key,envelope.model_dump(mode='json')) as session:
        assert not session.begin('worker-4')
    assert store.get(e.execution_id).status=='failed'


def test_message_mismatch_cannot_run(store):
    e,envelope,key=claim(store)
    with pytest.raises(ValueError,match='Mensagem'):
        with store.acquire(uuid4(),key,envelope.model_dump(mode='json')):
            pass


@pytest.mark.parametrize('error_type',[ValueError,RuntimeError])
def test_nonretryable_error_persisted(store,monkeypatch,error_type):
    e,envelope,key=claim(store)
    def fail(*a,**k):
        raise error_type('falha não recuperável')
    monkeypatch.setattr(tasks,'run_workflow',fail)
    with pytest.raises(error_type):
        tasks.execute.run(envelope.model_dump(mode='json'),str(e.execution_id),key)
    assert store.get(e.execution_id).status=='failed'
    assert store.events(e.execution_id)[-1].event_type=='execution.failed'


@pytest.mark.parametrize('fallback,outcome',[('deterministic_reference','degraded_recommendation'),('human','human_review_required')])
def test_llm_failure_events_and_result_persisted(store,monkeypatch,fallback,outcome):
    from control_tower.distributed import llm_runtime
    from control_tower.settings import Settings
    monkeypatch.setattr(llm_runtime,'settings_for',lambda options:Settings('openai','gpt-4.1-mini','test-placeholder'))
    # Falha simulada ocorre antes de qualquer request SDK. Nenhuma chamada paga.
    e,envelope,key=claim(store,llm_mode='openai',llm_failure='timeout',fallback=fallback)
    tasks.execute.run(envelope.model_dump(mode='json'),str(e.execution_id),key)
    final=store.get(e.execution_id)
    assert final.status=='completed' and final.result.outcome==outcome
    assert final.attempt==1 and final.duration_ms>0
    events=store.events(e.execution_id)
    kinds=[e.event_type for e in events]
    assert kinds.count('llm.requested')==2 and kinds.count('llm.retry')==1
    assert 'llm.fallback_activated' in kinds
    assert ('llm.degraded' if fallback=='deterministic_reference' else 'llm.escalated') in kinds
    assert all(e.input_tokens is None for e in events)
    if fallback=='human':assert final.current_step=='human_review_required' and final.result.recommendation is None


def test_usage_fields_persist_without_cost_estimate(store):
    e,envelope,key=claim(store)
    with store.acquire(e.execution_id,key,envelope.model_dump(mode='json')) as session:
        session.begin('worker')
        session.event('llm.completed','supervisor',input_tokens=123,output_tokens=45)
    event=store.events(e.execution_id)[-1]
    assert event.input_tokens==123 and event.output_tokens==45 and event.estimated_cost is None


def test_worker_missing_key_is_persisted_as_clear_failure(store,monkeypatch,tmp_path):
    from control_tower.distributed import llm_runtime
    monkeypatch.setenv('LLM_MODE','openai');monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    monkeypatch.setenv('OPENAI_API_KEY_FILE',str(tmp_path/'absent'))
    monkeypatch.setattr(llm_runtime,'project_root',lambda:tmp_path)
    e,envelope,key=claim(store,llm_mode='openai')
    with pytest.raises(ValueError,match='OPENAI_API_KEY'):
        tasks.execute.run(envelope.model_dump(mode='json'),str(e.execution_id),key)
    final=store.get(e.execution_id)
    assert final.status=='failed' and 'OPENAI_API_KEY' in final.error
    assert not any(e.event_type=='llm.requested' for e in store.events(e.execution_id))
