"""Local exporters; no real OpenAI or infrastructure calls."""
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
pytest.importorskip('opentelemetry.sdk')
pytest.importorskip('fastapi')
pytest.importorskip('celery')
pytest.importorskip('psycopg')
from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from control_tower.telemetry import tracing, propagation, instrumentation
from control_tower.runtime.settings import RuntimeSettings
from control_tower.telemetry.context import ExecutionContext, bind_context

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def telemetry(monkeypatch):
    monkeypatch.setenv('LLM_MODE', 'mock')
    monkeypatch.setenv('DEMO_AGENT_DELAY_MS', '0')
    exporter, reader = InMemorySpanExporter(), InMemoryMetricReader()
    tracing.initialize_tracing(RuntimeSettings(_env_file=None, otel_enabled=True),
                               span_exporter=exporter, metric_reader=reader)
    yield exporter, reader
    tracing.shutdown()
    instrumentation._degraded.set(False)


def spans(telemetry):
    return telemetry[0].get_finished_spans()


def test_w3c_valid_parent_and_tracestate(telemetry):
    parent = '00-'+'1'*32+'-'+'2'*16+'-01'
    with tracing.operation('HTTP', context=propagation.extract({'traceparent':parent, 'tracestate':'vendor=value'})):
        headers={};propagation.inject(headers)
        with tracing.operation('worker', context=propagation.extract(headers)):
            pass
    first,second=spans(telemetry)
    assert first.parent.span_id==second.context.span_id
    assert second.parent.span_id==int('2'*16,16)
    assert headers['tracestate']=='vendor=value'
    assert headers['traceparent'].split('-')[1]=='1'*32


@pytest.mark.parametrize('parent',['bad','00-'+'0'*32+'-'+'2'*16+'-01',None])
def test_invalid_parent_creates_new_trace(telemetry,parent):
    with tracing.operation('new',context=propagation.extract({'traceparent':parent} if parent else {})):
        pass
    assert spans(telemetry)[0].parent is None


def test_http_server_real_trace_and_sanitized_failure(telemetry):
    from fastapi.testclient import TestClient
    from control_tower.api.app import create_app
    from control_tower.distributed.durable import DurableExecution
    execution=DurableExecution(execution_id=uuid4(),incident_id='x',idempotency_key='k')
    enqueue=MagicMock(return_value=(execution,True))
    settings=RuntimeSettings(_env_file=None,otel_enabled=True)
    # No lifespan: the test owns the in-memory providers.
    client=TestClient(create_app(settings,MagicMock(),enqueue,MagicMock()))
    r=client.post('/incidents',json={'incident_id':'x'},headers={'traceparent':'00-'+'1'*32+'-'+'2'*16+'-01'})
    assert r.status_code==202 and r.json()['trace_id']=='1'*32
    s=spans(telemetry)[0]
    assert s.name=='http POST /incidents' and s.kind==trace.SpanKind.SERVER
    assert s.attributes['http.response.status_code']==202
    enqueue.side_effect=ConnectionError('postgresql://secret:key@db/company-data')
    assert client.post('/incidents',json={'incident_id':'x'}).status_code==503
    assert spans(telemetry)[-1].status.status_code==trace.StatusCode.ERROR
    assert 'secret' not in str([(s.attributes,s.events,s.status) for s in spans(telemetry)])


def test_workflow_agents_tools_parallel_join_and_no_business_change(telemetry, monkeypatch):
    from threading import Barrier
    from control_tower.tools import Tools
    from control_tower.graph import workflow
    from control_tower.agents import specialists
    instrumentation.install()
    barrier=Barrier(3)
    for name in workflow.SPECIALISTS:
        original=getattr(specialists,name)
        def run(*args,_original=original,**kwargs):
            barrier.wait(timeout=5)
            return _original(*args,**kwargs)
        monkeypatch.setattr(specialists,name,run)
    tools=Tools(ROOT)
    with bind_context(ExecutionContext(execution_id=uuid4(),incident_id='test')):
        state=workflow.run_workflow(tools,tools.load_incident(ROOT/'incidents/incident_001.json'))
    assert state.approval.actions_executed is False
    assert str(state.recommendation.estimated_cost_brl)=='12500.00'
    records=spans(telemetry);names={s.name for s in records}
    assert {'workflow incident-investigation','agent supervisor','agent supply','agent production',
        'agent logistics','deterministic finance','agent challenger','agent recommendation',
        'workflow consolidation','workflow human_approval','tool inventory.lookup',
        'tool supplier.lookup','llm completion'} <= names
    byname={s.name:s for s in records}
    specialist=[byname['agent '+n] for n in workflow.SPECIALISTS]
    assert max(s.start_time for s in specialist) < min(s.end_time for s in specialist)
    assert byname['workflow consolidation'].start_time >= max(s.end_time for s in specialist)
    assert all(s.parent.span_id==byname['workflow incident-investigation'].context.span_id for s in specialist)
    llms=[s for s in records if s.name=='llm completion']
    assert len(llms)==6 and all(s.attributes['gen_ai.provider.name']=='mock' for s in llms)
    assert all(not any('tokens' in k for k in s.attributes) for s in llms)
    assert not tracing.identifiers()  # no context leak


def test_failure_retry_fallback_events_and_usage(telemetry):
    from control_tower.distributed.llm_runtime import ResilientInterpreter, ProviderUnavailable
    from control_tower.distributed.durable import TaskOptions
    from control_tower.settings import Settings
    options=TaskOptions(llm_mode='openai',llm_failure='timeout',fallback='deterministic_reference')
    session=SimpleNamespace(execution=SimpleNamespace(attempt=1), options=options.model_dump())
    session.event=lambda kind,agent='worker',**kw:instrumentation.observe_event(session,kind,agent,**kw)
    interpreter=ResilientInterpreter(Settings(mode='openai',api_key='unit-secret',model=options.llm_model),
                                    session,options,client=MagicMock(),sleep=lambda _:None)
    with tracing.operation('agent supervisor'):
        with pytest.raises(ProviderUnavailable):
            interpreter.request('supervisor')
        session.event('llm.fallback_activated')
        session.event('llm.degraded')
    calls=[s for s in spans(telemetry) if s.name=='llm completion']
    assert len(calls)==2 and all(s.status.status_code==trace.StatusCode.ERROR for s in calls)
    assert calls[0].context.span_id != calls[1].context.span_id
    events={e.name for s in spans(telemetry) for e in s.events}
    assert {'llm.retry','llm.fallback_activated','llm.degraded'}<=events
    assert 'unit-secret' not in str(spans(telemetry))
    assert instrumentation._llm_scope.get() is None


def test_successful_usage_only_when_reported_and_metrics(telemetry):
    session=SimpleNamespace(execution=SimpleNamespace(attempt=1,result=None), options={'llm_model':'unit-model'})
    with tracing.operation('worker'):
        instrumentation.observe_event(session,'execution.started')
        instrumentation.observe_event(session,'llm.requested','supply')
        instrumentation.observe_event(session,'llm.completed','supply',input_tokens=13,output_tokens=7)
        instrumentation.observe_event(session,'execution.completed')
    call=next(s for s in spans(telemetry) if s.name=='llm completion')
    assert call.attributes['gen_ai.usage.input_tokens']==13
    data=telemetry[1].get_metrics_data()
    metrics={m.name:m for r in data.resource_metrics for s in r.scope_metrics for m in s.metrics}
    assert {'llm.calls','llm.tokens.input','llm.tokens.output','executions.started','executions.completed','execution.duration'}<=metrics.keys()
    assert metrics['llm.tokens.input'].data.data_points[0].value==13
    assert not any('execution_id' in str(p.attributes) for m in metrics.values() for p in m.data.data_points)


def test_log_has_real_ids_and_no_payload(telemetry,caplog):
    from control_tower.telemetry.logging import log_event,ContextFormatter,LOGGER
    with bind_context(ExecutionContext(execution_id=uuid4(),incident_id='a')):
        with tracing.operation('work'),caplog.at_level(logging.INFO,logger=LOGGER.name):
            expected=tracing.identifiers()
            log_event('safe','message')
    row=json.loads(ContextFormatter('service','json').format(caplog.records[-1]))
    assert row['trace_id']==expected['trace_id'] and row['span_id']==expected['span_id']
    assert row['execution_id'] and row['incident_id']=='a'


def test_privacy_error_type_only_and_content_rejected(telemetry):
    secret='key-dsn-prompt-customer-secret'
    with pytest.raises(ValueError):
        with tracing.operation('work'):
            raise ValueError(secret)
    s=spans(telemetry)[0]
    assert secret not in str(s.attributes)+str(s.events)+str(s.status)
    assert s.events[0].attributes=={'exception.type':'ValueError'}
    with pytest.raises(ValueError):
        RuntimeSettings(_env_file=None,otel_capture_content=True)


def test_disabled_workflow_no_network(monkeypatch):
    import socket
    tracing.shutdown()
    monkeypatch.setattr(socket.socket,'connect',MagicMock(side_effect=AssertionError('network forbidden')))
    assert tracing.initialize_tracing(RuntimeSettings(_env_file=None,otel_enabled=False)) is None
    from control_tower.graph.workflow import run_workflow
    from control_tower.tools import Tools
    tools=Tools(ROOT)
    assert run_workflow(tools,tools.load_incident(ROOT/'incidents/incident_001.json')).status=='awaiting_approval'


def test_producer_injects_and_worker_continues_each_delivery(telemetry, monkeypatch):
    from control_tower.runtime import signals
    from control_tower.distributed import tasks
    from celery.app.task import Task
    # Existing installed wrapper delegates to the bound original; patch its send path.
    headers_seen=[]
    monkeypatch.setattr(tasks.app, 'send_task', lambda *a,**kw: headers_seen.append(kw.get('headers')))
    instrumentation.install()
    uid=str(uuid4())
    with bind_context(ExecutionContext(execution_id=uid,incident_id='case')):
        with tracing.operation('http POST /incidents'):
            tasks.execute.apply_async(kwargs={'execution_id':uid,'envelope':{},'idempotency_key':'k'})
    assert headers_seen and headers_seen[0]['traceparent']
    context=ExecutionContext(execution_id=uid,incident_id='case')
    task=SimpleNamespace(name=signals.TASK, request=SimpleNamespace(
        headers=headers_seen[0]|{signals.HEADER:context.model_dump(mode='json')},
        hostname='unit-worker',retries=0,delivery_info={'redelivered':False}))
    store=MagicMock();store.get.side_effect=RuntimeError('unit-secret')
    monkeypatch.setattr(signals,'CorrelatedStore',lambda:store)
    for redelivered in (False,True):
        task.request.delivery_info['redelivered']=redelivered
        signals.task_started(sender=task,task=task,kwargs={'execution_id':uid})
        with tracing.operation('workflow incident-investigation'):pass
        signals.task_finished(sender=task,kwargs={'execution_id':uid},state='SUCCESS')
    processing=[s for s in spans(telemetry) if s.name=='messaging process incident']
    publish=next(s for s in spans(telemetry) if s.name=='messaging publish incident')
    assert len(processing)==2 and processing[0].context.span_id!=processing[1].context.span_id
    assert all(s.parent.span_id==publish.context.span_id for s in processing)
    assert processing[1].attributes['messaging.message.redelivered']
    assert not tracing.identifiers()


def test_failed_workflow_closes_nodes_and_restores_parent(telemetry):
    from control_tower.tools import Tools
    from control_tower.graph import workflow
    from control_tower.distributed.llm_runtime import ProviderUnavailable
    instrumentation.install()
    tools=Tools(ROOT);incident=tools.load_incident(ROOT/'incidents/incident_001.json')
    llm=MagicMock();llm.parse.side_effect=ProviderUnavailable('private-message',True)
    with tracing.operation('outer'):
        before=tracing.identifiers()
        with pytest.raises(ProviderUnavailable):workflow.run_workflow(tools,incident,llm=llm)
        assert tracing.identifiers()==before
    node=next(s for s in spans(telemetry) if s.name=='agent supervisor')
    assert node.end_time and node.status.status_code==trace.StatusCode.ERROR
    assert 'private-message' not in str(node.events)


def test_http_completion_log_is_inside_server_span(telemetry,monkeypatch):
    from fastapi.testclient import TestClient
    from control_tower.api import app as api_module
    from control_tower.distributed.durable import DurableExecution
    execution=DurableExecution(execution_id=uuid4(),incident_id='x',idempotency_key='k')
    seen=[]
    monkeypatch.setattr(api_module,'log_event',lambda event,*a,**kw:seen.append((event,tracing.identifiers())))
    client=TestClient(api_module.create_app(RuntimeSettings(_env_file=None,otel_enabled=True),MagicMock(),
                                           MagicMock(return_value=(execution,True)),MagicMock()))
    assert client.post('/incidents',json={'incident_id':'x'}).status_code==202
    ids=next(value for name,value in seen if name=='http.completed')
    assert ids['trace_id'] and ids['span_id']


def test_request_retry_injects_new_publish_context(telemetry,monkeypatch):
    from control_tower.distributed import tasks
    headers=[]
    monkeypatch.setattr(tasks.app,'send_task',lambda *a,**kw:headers.append(kw['headers']))
    instrumentation.install()
    original={'traceparent':'00-'+'1'*32+'-'+'2'*16+'-01','tracestate':'vendor=one'}
    with tracing.operation('messaging process incident',context=propagation.extract(original)):
        tasks.execute.apply_async(kwargs={'execution_id':str(uuid4()),'envelope':{},'idempotency_key':'k'},headers=original)
    publish=next(s for s in spans(telemetry) if s.name=='messaging publish incident')
    process=next(s for s in spans(telemetry) if s.name=='messaging process incident')
    assert publish.parent.span_id==process.context.span_id
    assert headers[0]['traceparent'].split('-')[2]==format(publish.context.span_id,'016x')
    assert headers[0]['tracestate']=='vendor=one'
    assert original['traceparent'].split('-')[2]=='2'*16 # input not mutated


def test_degraded_boundary_is_not_reported_as_production_mock(telemetry):
    from control_tower.tools import Tools
    from control_tower.graph import workflow
    instrumentation.install()
    session=SimpleNamespace(execution=SimpleNamespace(attempt=1),options={'fallback':'deterministic_reference'})
    tools=Tools(ROOT)
    with tracing.operation('processing'):
        instrumentation.observe_event(session,'llm.fallback_activated')
        state=workflow.run_workflow(tools,tools.load_incident(ROOT/'incidents/incident_001.json'))
    calls=[s for s in spans(telemetry) if s.name=='llm completion']
    assert state.status=='awaiting_approval' and len(calls)==6
    assert all(s.attributes['control_tower.llm.mode']=='degraded' for s in calls)
    assert all(s.attributes['gen_ai.provider.name']=='deterministic' for s in calls)


def test_failed_attempt_counter_and_duration_are_exported(telemetry):
    session=SimpleNamespace(execution=SimpleNamespace(attempt=2,result=None),options={})
    with tracing.operation('messaging process incident'):
        instrumentation.observe_event(session,'execution.started')
        instrumentation.observe_event(session,'execution.failed')
        instrumentation.observe_event(session,'execution.retry')
    records=telemetry[1].get_metrics_data()
    metrics={m.name:m for r in records.resource_metrics for s in r.scope_metrics for m in s.metrics}
    assert metrics['executions.failed'].data.data_points[0].value==1
    histogram=metrics['execution.duration'].data.data_points[0]
    assert histogram.count==1 and histogram.attributes['outcome']=='failed'
    span=spans(telemetry)[0]
    assert span.status.status_code==trace.StatusCode.ERROR
    assert span.attributes['control_tower.attempt']==2
    assert span.events[-1].name=='execution.retry'
