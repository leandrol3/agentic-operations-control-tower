"""Associação real no Postgres, schemas isolados; opt-in e nenhum provider real."""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4
import pytest
pytest.importorskip('pydantic_settings')
pytest.importorskip('psycopg')
pytest.importorskip('celery')
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from control_tower.distributed.config import database_url
from control_tower.distributed.incidents import generate_incidents
from control_tower.distributed.idempotency import idempotency_key
from control_tower.distributed.durable import TaskOptions
from control_tower.runtime.store import CorrelatedStore
from control_tower.telemetry.context import ExecutionContext, bind_context, current_context

pytestmark=pytest.mark.skipif(os.getenv('LESSON03_INTEGRATION')!='1',reason='Requer PostgreSQL e LESSON03_INTEGRATION=1')

@pytest.fixture
def store():
    dsn=database_url();schema='test_'+uuid4().hex
    with psycopg.connect(dsn,autocommit=True) as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    store=CorrelatedStore(make_conninfo(dsn,options=f'-c search_path={schema}'))
    store.initialize()
    try:yield store
    finally:
        with psycopg.connect(dsn,autocommit=True) as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def test_duplicate_preserves_original_context_and_domain(store):
    envelope=generate_incidents(1)[0];key=idempotency_key(envelope.incident_id)
    first=ExecutionContext()
    with bind_context(first):
        execution,new=store.claim(envelope,key,TaskOptions())
    with bind_context(ExecutionContext()):
        duplicate,new2=store.claim(envelope,key,TaskOptions())
        assert current_context.get().trace_id==first.trace_id
    assert new and not new2 and execution==duplicate
    assert store.context(execution.execution_id).trace_id==first.trace_id
    assert len(store.events(execution.execution_id))==1
    assert 'trace_id' not in store.get(execution.execution_id).model_dump()


def test_concurrent_context_has_one_winner(store):
    barrier=Barrier(4);envelope=generate_incidents(1)[0]
    def claim(_):
        with bind_context(ExecutionContext()):
            barrier.wait()
            execution,_=store.claim(envelope,idempotency_key(envelope.incident_id),TaskOptions())
            return execution.execution_id,current_context.get().trace_id
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(claim,range(4)))
    assert len(set(results))==1


def test_conflicting_options_do_not_replace_context(store):
    envelope=generate_incidents(1)[0];key=idempotency_key(envelope.incident_id)
    first=ExecutionContext()
    with bind_context(first):
        execution,_=store.claim(envelope,key,TaskOptions())
    with bind_context(ExecutionContext()),pytest.raises(ValueError):
        store.claim(envelope,key,TaskOptions(demo_delay_ms=10))
    assert store.context(execution.execution_id).trace_id==first.trace_id
