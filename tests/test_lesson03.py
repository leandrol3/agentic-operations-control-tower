"""HTTP/context/config offline: nenhuma infraestrutura ou chamada LLM real."""
import hashlib
import json
import logging
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4
import pytest

pytest.importorskip('fastapi', reason='uv sync --extra lesson03')
pytest.importorskip('pydantic_settings')
pytest.importorskip('celery')
pytest.importorskip('psycopg')
from fastapi.testclient import TestClient
from pydantic import ValidationError
from control_tower.api.app import create_app
from control_tower.api.models import IncidentSubmissionRequest
from control_tower.api import readiness
from control_tower.runtime.settings import RuntimeSettings
from control_tower.runtime import signals
from control_tower.telemetry.context import ExecutionContext, bind_context, current_context
from control_tower.telemetry.logging import ContextFormatter, log_event, LOGGER
from control_tower.telemetry.tracing import initialize_tracing
from control_tower.distributed.durable import DurableExecution, FinalResult
from control_tower.graph.state import Approval

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv('LLM_MODE', 'mock')
    return RuntimeSettings(_env_file=None, demo_controls_enabled=True, otel_enabled=False)


@pytest.fixture
def service(settings):
    store = MagicMock()
    execution = DurableExecution(execution_id=uuid4(), incident_id='HTTP-001', idempotency_key='k')
    store.get.return_value = execution
    store.context.return_value = None
    store.events.return_value = []
    enqueue = MagicMock(return_value=(execution, True))
    probe = MagicMock(return_value={'redis': 'ok', 'postgres': 'ok'})
    with TestClient(create_app(settings, store, enqueue, probe)) as client:
        yield client, store, enqueue, probe


def test_health_has_no_dependency_calls(service):
    client, store, enqueue, probe = service
    response = client.get('/health')
    assert response.status_code == 200 and response.json() == {'status': 'alive'}
    assert not store.mock_calls and not enqueue.called and not probe.called


@pytest.mark.parametrize('redis,postgres,status', [('ok','ok',200),('unavailable','ok',503),
    ('ok','unavailable',503),('unavailable','unavailable',503)])
def test_readiness_contract(service, redis, postgres, status):
    client, store, enqueue, probe = service
    probe.return_value = {'redis': redis, 'postgres': postgres}
    response = client.get('/ready')
    assert response.status_code == status
    assert response.json()['status'] == ('ready' if status == 200 else 'not_ready')
    assert not store.mock_calls and not enqueue.called


def test_submit_is_accepted_and_uses_producer_without_workflow(service, monkeypatch):
    from control_tower.graph import workflow
    monkeypatch.setattr(workflow, 'run_workflow', MagicMock(side_effect=AssertionError('HTTP cannot run graph')))
    client, store, enqueue, _ = service
    response = client.post('/incidents', json={'incident_id':'HTTP-001','version':'class-1'},
                           headers={'X-Trace-ID':'1'*32,'X-Correlation-ID':'class-1'})
    assert response.status_code == 202
    assert response.json()['status'] == 'queued'
    assert response.headers['x-trace-id'] == '1'*32
    assert response.headers['location'].endswith(response.json()['execution_id'])
    args, kwargs = enqueue.call_args
    assert args[0].payload['reference_case_id'] == 'INCIDENT-001'
    assert args[1].llm_mode == 'mock' and kwargs['store'] is store and kwargs['version']=='class-1'
    assert current_context.get() is None


@pytest.mark.parametrize('body', [{}, {'incident_id':' '}, {'incident_id':'a','secret':'dont-echo'},
    {'incident_id':'a','reference_case_id':'UNSUPPORTED'}, {'incident_id':'a','demo_delay_ms':30001}])
def test_invalid_payload_never_publishes(service, body):
    client, _, enqueue, _ = service
    response=client.post('/incidents',json=body)
    assert response.status_code==422 and 'dont-echo' not in response.text
    enqueue.assert_not_called()


@pytest.mark.parametrize('header,value', [('X-Trace-ID','abc'),('X-Trace-ID','0'*32),
    ('X-Correlation-ID','a b'),('X-Correlation-ID','a'*65)])
def test_invalid_context_rejected(service,header,value):
    client,_,enqueue,_=service
    assert client.post('/incidents',json={'incident_id':'x'},headers={header:value}).status_code==422
    enqueue.assert_not_called()


def test_conflict_and_publish_failure_are_honest(service):
    client,_,enqueue,_=service
    enqueue.side_effect=ValueError('secret DSN')
    response=client.post('/incidents',json={'incident_id':'x'})
    assert response.status_code==409 and 'secret' not in response.text
    enqueue.side_effect=ConnectionError('secret DSN')
    response=client.post('/incidents',json={'incident_id':'x'})
    assert response.status_code==503 and 'secret' not in response.text


def test_queries_project_public_fields_and_pending_result(service):
    client,store,_,_=service
    uid=str(store.get.return_value.execution_id)
    context=ExecutionContext(execution_id=uid)
    store.context.return_value=context
    response=client.get('/executions/'+uid)
    assert response.status_code==200 and response.json()['trace_id']==context.trace_id
    assert 'idempotency_key' not in response.json() and 'result' not in response.json()
    assert client.get(f'/executions/{uid}/events').json()=={'execution_id':uid,'events':[]}
    response=client.get(f'/executions/{uid}/result')
    assert response.status_code==202 and response.json()['outcome'] is None
    assert response.json()['actions_executed'] is False


def test_human_escalation_is_completed_but_not_approved(service):
    from datetime import datetime, timezone
    client,store,_,_=service
    e=store.get.return_value
    now=datetime.now(timezone.utc)
    store.get.return_value=DurableExecution(**(e.model_dump()|dict(status='completed',
        started_at=now,completed_at=now,worker_id='w',current_step='human_review_required',
        result=FinalResult(mode='openai',outcome='human_review_required',reason='simulated_timeout',
                           approval=Approval(authority='operations_manager')))))
    response=client.get(f'/executions/{e.execution_id}/result')
    assert response.status_code==200
    assert response.json()['outcome']=='human_review_required'
    assert response.json()['recommended_action'] is None
    assert response.json()['approval_status']=='pending'


@pytest.mark.parametrize('suffix',['','/events','/result'])
def test_unknown_or_unavailable_execution(service,suffix):
    client,store,_,_=service
    store.get.side_effect=ValueError('absent')
    assert client.get(f'/executions/{uuid4()}{suffix}').status_code==404
    store.get.side_effect=RuntimeError('postgresql://secret')
    response=client.get(f'/executions/{uuid4()}{suffix}')
    assert response.status_code==503 and 'secret' not in response.text


def test_demo_controls_are_explicit(settings):
    settings.demo_controls_enabled=False
    enqueue=MagicMock()
    with TestClient(create_app(settings,MagicMock(),enqueue,MagicMock())) as client:
        assert client.post('/incidents',json={'incident_id':'a','demo_delay_ms':1}).status_code==422
    enqueue.assert_not_called()


def test_settings_precedence_aliases_and_secrets(monkeypatch,tmp_path):
    path=tmp_path/'.env'
    path.write_text('LLM_MODE=mock\nLOG_FORMAT=json\nOTHER_OLD_FIELD=accepted\n')
    monkeypatch.setenv('LOG_FORMAT','human')
    monkeypatch.setenv('LESSON02_DATABASE_URL','postgresql://user:private@localhost/db')
    monkeypatch.setenv('OPENAI_API_KEY','test-secret')
    settings=RuntimeSettings(_env_file=path)
    assert settings.log_format=='human' and settings.llm_mode=='mock'
    assert 'private' in settings.database_url.get_secret_value()
    assert 'private' not in repr(settings) and 'test-secret' not in repr(settings)


@pytest.mark.parametrize('values',[{'request_timeout':0},{'worker_concurrency':0},
    {'llm_mode':'invalid'}, {'llm_mode':'openai','visibility_timeout':60},
    {'app_env':'production','demo_controls_enabled':True}])
def test_settings_reject_invalid(values):
    with pytest.raises(ValidationError):
        RuntimeSettings(_env_file=None, **values)


def test_context_isolated_and_log_json_is_structured(caplog):
    context=ExecutionContext(execution_id=uuid4(),incident_id='a',worker_id='worker-a')
    formatter=ContextFormatter('worker','json')
    with bind_context(context), caplog.at_level(logging.INFO,logger=LOGGER.name):
        log_event('worker.received','Mensagem curta')
    assert current_context.get() is None
    row=json.loads(formatter.format(caplog.records[-1]))
    assert row['trace_id']==context.trace_id and row['worker_id']=='worker-a'
    assert row['event']=='worker.received' and row['service']=='worker'
    with bind_context(ExecutionContext()):
        assert current_context.get().trace_id!=context.trace_id


def test_publish_context_header_matches_execution_only():
    uid=uuid4();headers={}
    with bind_context(ExecutionContext(execution_id=uid)):
        signals.before_publish(sender=signals.TASK,headers=headers,body=([],{'execution_id':str(uid)},{}))
        assert headers[signals.HEADER]['execution_id']==str(uid)
        empty={}
        signals.before_publish(sender=signals.TASK,headers=empty,body=([],{'execution_id':str(uuid4())},{}))
        assert not empty


def test_worker_context_from_header_and_cleanup(monkeypatch):
    context=ExecutionContext(execution_id=uuid4(),incident_id='a')
    task=MagicMock();task.name=signals.TASK;task.request.headers={signals.HEADER:context.model_dump(mode='json')}
    task.request.hostname='worker-a'
    store=MagicMock();store.get.side_effect=RuntimeError('secret')
    monkeypatch.setattr(signals,'CorrelatedStore',lambda:store)
    signals.task_started(sender=task,task=task,kwargs={'execution_id':str(context.execution_id)})
    assert current_context.get().trace_id==context.trace_id
    assert current_context.get().worker_id.startswith('worker-a:')
    signals.task_finished(sender=task,kwargs={'execution_id':str(context.execution_id)})
    assert current_context.get() is None


def test_readiness_actual_probes_handle_down(monkeypatch,settings):
    import psycopg,redis
    monkeypatch.setattr(psycopg,'connect',MagicMock(side_effect=psycopg.OperationalError('secret')))
    monkeypatch.setattr(redis.Redis,'from_url',MagicMock(side_effect=redis.ConnectionError('secret')))
    assert readiness.check_readiness(settings)=={'redis':'unavailable','postgres':'unavailable'}


def test_otel_disabled_no_network(settings,monkeypatch):
    import socket
    monkeypatch.setattr(socket,'create_connection',MagicMock(side_effect=AssertionError('network')))
    assert initialize_tracing(settings) is None
    settings.otel_enabled=True
    settings.otel_exporter_otlp_endpoint=None
    provider=initialize_tracing(settings)
    assert provider.resource.attributes['service.name']==settings.otel_service_name
    provider.shutdown()


def test_lesson02_frozen_and_container_contracts():
    import yaml
    for filename,digest in json.loads((ROOT/'tests/fixtures/lesson02-frozen.json').read_text()).items():
        assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==digest,filename
    config=yaml.safe_load((ROOT/'compose.override.yaml').read_text())
    roles=[config['services'][name] for name in ['api','worker-a','worker-b']]
    assert len({role['image'] for role in roles})==1
    assert all(role['healthcheck'] for role in roles)
    assert all(role['command'][-1]=='worker' for role in roles[1:])
    assert (ROOT/'Dockerfile').read_text().count('USER app')==1
    assert 'COPY . ' not in (ROOT/'Dockerfile').read_text()


def test_real_mock_recommendation_projects_finance_and_approval(service):
    from datetime import datetime,timezone
    from control_tower.tools import Tools
    from control_tower.graph.workflow import run_workflow
    tools=Tools(ROOT)
    state=run_workflow(tools,tools.load_incident(ROOT/'incidents/incident_001.json'),llm=None)
    client,store,_,_=service
    e=store.get.return_value;now=datetime.now(timezone.utc)
    store.get.return_value=DurableExecution(**(e.model_dump()|dict(status='completed',started_at=now,
        completed_at=now,worker_id='w',current_step='awaiting_approval',
        result=FinalResult(recommendation=state.recommendation,approval=state.approval))))
    response=client.get(f'/executions/{e.execution_id}/result')
    assert response.status_code==200 and response.json()['estimated_cost_brl']=='12500.00'
    assert response.json()['approval_status']=='pending' and not response.json()['actions_executed']


def test_openai_startup_without_key_fails_before_store(monkeypatch,tmp_path):
    import sys
    from control_tower.runtime import __main__ as runtime
    monkeypatch.setenv('LLM_MODE','openai')
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    monkeypatch.setenv('OPENAI_API_KEY_FILE',str(tmp_path/'missing'))
    monkeypatch.setattr(sys,'argv',['runtime','api'])
    s=RuntimeSettings(_env_file=None,llm_mode='openai',control_tower_root=tmp_path)
    monkeypatch.setattr(runtime,'RuntimeSettings',lambda:s)
    monkeypatch.setattr(runtime,'configure',lambda settings:MagicMock())
    store=MagicMock();monkeypatch.setattr(runtime,'CorrelatedStore',store)
    with pytest.raises(SystemExit,match='OPENAI_API_KEY'):
        runtime.main()
    store.assert_not_called()


def test_events_pagination_preserves_durable_sequence(service):
    from datetime import datetime,timezone
    from control_tower.distributed.durable import DurableEvent
    client,store,_,_=service;e=store.get.return_value
    store.events.return_value=[DurableEvent(execution_id=e.execution_id,incident_id=e.incident_id,
        agent_id='worker',event_type='llm.failed',status='running',sequence=i,
        timestamp=datetime.now(timezone.utc)) for i in range(1,6)]
    response=client.get(f'/executions/{e.execution_id}/events?after=2&limit=2')
    assert response.status_code==200
    assert [event['sequence'] for event in response.json()['events']]==[3,4]
    assert client.get(f'/executions/{e.execution_id}/events?limit=101').status_code==422
