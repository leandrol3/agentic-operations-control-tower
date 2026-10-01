"""Unitários offline. Integração PostgreSQL opt-in em arquivo separado."""
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4
import pytest
from pydantic import ValidationError

pytest.importorskip('celery', reason='uv sync --extra lesson02')
pytest.importorskip('psycopg', reason='uv sync --extra lesson02')
from control_tower.distributed import tasks, producer
from control_tower.distributed.celery_app import app
from control_tower.distributed.durable import DurableExecution, DurableEvent, TaskOptions
from control_tower.distributed.incidents import generate_incidents


def test_delivery_configuration():
    assert app.conf.task_acks_late and app.conf.task_reject_on_worker_lost
    assert app.conf.worker_prefetch_multiplier == 1
    assert app.conf.broker_transport_options['visibility_timeout'] == 60
    assert app.conf.task_ignore_result and app.conf.result_backend is None
    assert tasks.execute.max_retries == 2


@pytest.mark.parametrize('kind,status', [('execution.queued','queued'),('execution.started','running'),
    ('execution.retry','queued'),('execution.interrupted','running'),('execution.failed','failed'),
    ('execution.completed','completed'),('supply.completed','running')])
def test_durable_event(kind, status):
    event = DurableEvent(execution_id=uuid4(), incident_id='x',agent_id='worker',event_type=kind,
                         timestamp=datetime.now(timezone.utc),status=status,sequence=1)
    assert event.input_tokens is event.output_tokens is event.estimated_cost is event.quality_score is event.business_outcome is None
    assert DurableEvent.model_validate_json(event.model_dump_json()) == event


@pytest.mark.parametrize('kind,status', [('execution.retry','running'),('execution.completed','queued'),('unknown','running')])
def test_invalid_events(kind,status):
    with pytest.raises(ValidationError):
        DurableEvent(execution_id=uuid4(),incident_id='x',agent_id='worker',event_type=kind,
                     timestamp=datetime.now(timezone.utc),status=status,sequence=1)


@pytest.mark.parametrize('options',[{'demo_delay_ms':-1},{'demo_delay_ms':30001},{'fail_specialist':'finance'}])
def test_invalid_options(options):
    with pytest.raises(ValidationError):
        TaskOptions(**options)


def test_completed_requires_result():
    with pytest.raises(ValidationError):
        DurableExecution(execution_id=uuid4(),incident_id='x',idempotency_key='k',status='completed',
                         started_at=datetime.now(timezone.utc),completed_at=datetime.now(timezone.utc),
                         worker_id='w',current_step='done')


def test_duplicate_busy_never_runs_graph(monkeypatch):
    store = MagicMock()
    @contextmanager
    def busy(*args):
        yield None
    store.acquire = busy
    monkeypatch.setattr(tasks,'Store',lambda:store)
    graph = MagicMock()
    monkeypatch.setattr(tasks,'run_workflow',graph)
    result = tasks.execute.run(generate_incidents(1)[0].model_dump(mode='json'),'execution','key')
    assert result['duplicate'] is True
    graph.assert_not_called()


def test_producer_republishes_existing_identity(monkeypatch):
    store = MagicMock()
    execution = DurableExecution(execution_id=uuid4(),incident_id='x',idempotency_key='k')
    store.claim.return_value = execution,False
    publish = MagicMock()
    monkeypatch.setattr(producer.execute,'apply_async',publish)
    existing,new=producer.enqueue(generate_incidents(1)[0],TaskOptions(),store=store)
    assert existing==execution and not new
    assert publish.call_args.kwargs['task_id']==str(execution.execution_id)


def test_publish_failure_is_not_reported_as_success(monkeypatch):
    store=MagicMock()
    store.claim.return_value=DurableExecution(execution_id=uuid4(),incident_id='x',idempotency_key='k'),True
    monkeypatch.setattr(producer.execute,'apply_async',MagicMock(side_effect=ConnectionError('offline')))
    with pytest.raises(ConnectionError):
        producer.enqueue(generate_incidents(1)[0],TaskOptions(),store=store)
    store.claim.assert_called_once()
