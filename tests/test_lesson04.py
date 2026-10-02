"""Inputs for future operations: no external provider calls in these tests."""
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4
import pytest

pytest.importorskip('mcp', reason='uv sync --extra lesson04')
pytest.importorskip('celery')
pytest.importorskip('psycopg')
from fastapi.testclient import TestClient
from mcp.shared.memory import create_connected_server_and_client_session
from control_tower.api.app import create_app
from control_tower.api.models import IncidentSubmissionRequest
from control_tower.application import IncidentCapability
from control_tower.mcp.server import create_server
from control_tower.runtime.settings import RuntimeSettings
from control_tower.distributed.durable import DurableExecution, DurableEvent, FinalResult, TaskOptions
from control_tower.control_plane.registry import registry, AgentRecord, SYSTEM_CAPABILITY
from control_tower.control_plane.quality import assess_quality
from control_tower.control_plane.economics import assess_economics, PricingConfig, load_pricing
from control_tower.graph.state import Approval

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def settings():
    return RuntimeSettings(_env_file=None, llm_mode='mock', demo_controls_enabled=True, otel_enabled=False)


@pytest.fixture
def execution():
    return DurableExecution(execution_id=uuid4(), incident_id='L04-001', idempotency_key='test')


def events(execution, *kinds):
    terminal={'execution.queued':'queued','execution.completed':'completed','execution.failed':'failed',
              'execution.retry':'queued'}
    return [DurableEvent(execution_id=execution.execution_id, incident_id=execution.incident_id,
        event_type=kind, agent_id='supervisor', timestamp=datetime.now(timezone.utc), sequence=i,
        status=terminal.get(kind,'running')) for i,kind in enumerate(kinds,1)]


@pytest.fixture
def service(settings, execution):
    store=MagicMock()
    store.get.return_value=execution
    store.context.return_value=None
    store.events.return_value=[]
    store.options_for.return_value=TaskOptions()
    enqueue=MagicMock(return_value=(execution,True))
    return store, enqueue, IncidentCapability(settings,store,enqueue)


@pytest.fixture
def final(execution):
    from control_tower.tools import Tools
    from control_tower.graph.workflow import run_workflow
    tools=Tools(ROOT)
    state=run_workflow(tools,tools.load_incident(ROOT/'incidents/incident_001.json'),llm=None)
    now=datetime.now(timezone.utc)
    return execution.model_copy(update=dict(status='completed',started_at=now,completed_at=now,
        worker_id='worker-a',current_step='awaiting_approval',
        result=FinalResult(recommendation=state.recommendation,approval=state.approval)))


def test_mcp_real_protocol_shares_capability_and_public_contracts(settings,service,execution,monkeypatch):
    store, enqueue, capability=service
    from control_tower.graph import workflow
    monkeypatch.setattr(workflow,'run_workflow',MagicMock(side_effect=AssertionError('Boundary bypassed queue')))
    original=IncidentCapability.submit_incident
    calls=[]
    def observed(self,*args,**kwargs):
        calls.append(self);return original(self,*args,**kwargs)
    monkeypatch.setattr(IncidentCapability,'submit_incident',observed)
    with TestClient(create_app(settings,store,enqueue)) as http:
        accepted=http.post('/incidents',json={'incident_id':'L04-001'}).json()
        expected_status=http.get(f'/executions/{execution.execution_id}').json()
        expected_result=http.get(f'/executions/{execution.execution_id}/result').json()
    async def check():
        async with create_connected_server_and_client_session(create_server(capability)) as client:
            listing=await client.list_tools()
            assert {t.name for t in listing.tools}=={'submit_incident','get_execution_status','get_execution_result'}
            assert all(t.outputSchema for t in listing.tools)
            result=await client.call_tool('submit_incident',{'request':{'incident_id':'L04-001'}})
            assert not result.isError and result.structuredContent['execution_id']==accepted['execution_id']
            for name,expected in [('get_execution_status',expected_status),('get_execution_result',expected_result)]:
                result=await client.call_tool(name,{'execution_id':str(execution.execution_id)})
                assert not result.isError and result.structuredContent==expected
    asyncio.run(check())
    assert len(calls)==2 and enqueue.call_count==2
    assert enqueue.call_args.kwargs['store'] is store


@pytest.mark.parametrize('tool', ['get_execution_status','get_execution_result'])
def test_mcp_unknown_execution_and_store_error_sanitized(service,tool):
    store,_,capability=service
    async def check():
        async with create_connected_server_and_client_session(create_server(capability)) as client:
            for exception,code in [(ValueError('secret'),404),(RuntimeError('secret DSN'),503)]:
                store.get.side_effect=exception
                result=await client.call_tool(tool,{'execution_id':str(uuid4())})
                text=' '.join(c.text for c in result.content)
                assert result.isError and str(code) in text and 'secret' not in text
    asyncio.run(check())


def test_mcp_completed_result_is_public(service, final):
    store,_,capability=service;store.get.return_value=final
    async def check():
        async with create_connected_server_and_client_session(create_server(capability)) as client:
            result=await client.call_tool('get_execution_result',{'execution_id':str(final.execution_id)})
            assert result.structuredContent==capability.result(final.execution_id).model_dump(mode='json')
            assert result.structuredContent['approval_status']=='pending'
            assert result.structuredContent['actions_executed'] is False
            assert 'risks' not in result.structuredContent
    asyncio.run(check())


@pytest.mark.parametrize('mode',['mock','openai'])
def test_registry_represents_real_workforce(mode):
    records=registry(mode,'configured-model')
    expected={'supervisor','supply','production','logistics','finance','challenger','recommendation'}
    assert {r.agent_id for r in records}==expected and len(records)==7
    goals=[]
    from control_tower.tools import Tools
    for r in records:
        assert r.business_owner and r.technical_owner and r.version and r.status=='registered'
        assert r.interfaces==('langgraph_node',)
        assert all(hasattr(Tools,t) for t in r.tools)
        assert r.business_goals and all(g.target_source=='didactic_configured_example' for g in r.business_goals)
        goals.extend(g.goal_id for g in r.business_goals)
        if r.agent_id=='finance' or mode=='mock':
            assert r.execution_type=='deterministic' and r.model is None
        else:
            assert r.model=='configured-model'
    assert len(set(goals))==len(goals)
    assert SYSTEM_CAPABILITY['interfaces']==('http','mcp')


def test_registry_rejects_incoherent_model_and_duplicate_goals():
    row=registry()[0].model_dump()
    with pytest.raises(ValueError): AgentRecord.model_validate(row|{'model':'fake'})
    with pytest.raises(ValueError): AgentRecord.model_validate(row|{'business_goals':row['business_goals']*2})


def test_registry_endpoints_do_not_need_store(settings, service):
    store,enqueue,_=service
    with TestClient(create_app(settings,store,enqueue)) as client:
        assert len(client.get('/agents').json())==7
        assert client.get('/agents/supply').json()['agent_id']=='supply'
        assert client.get('/agents/unknown').status_code==404
        assert client.get('/agents/finance').json()['model'] is None
    assert not store.mock_calls


@pytest.mark.parametrize('outcome',['recommendation','degraded_recommendation','human_review_required'])
def test_quality_outcomes_preserve_human_approval(final,outcome):
    result=final.result
    history=events(final,'execution.queued','execution.completed')
    if outcome=='degraded_recommendation':
        final=final.model_copy(update={'result':result.model_copy(update={
            'mode':'degraded','outcome':outcome,'reason':'simulated_timeout'})})
    elif outcome=='human_review_required':
        final=final.model_copy(update={'result':FinalResult(mode='openai',outcome=outcome,
            reason='provider_failure',approval=Approval(authority='operations_manager'))})
        history=events(final,'execution.queued','llm.fallback_activated','execution.completed')
    q=assess_quality(final,history)
    assert q.outcome_type==outcome and q.fallback_used==(outcome!='recommendation')
    assert q.human_review_required and q.approval_status=='pending'
    assert q.evidence_complete is None and q.policy_compliant is None
    assert q.confidence==(None if outcome=='human_review_required' else final.result.recommendation.confidence)


def test_quality_unknowns_for_incomplete_legacy_history(execution,final):
    q=assess_quality(execution,[])
    assert q.fallback_used is q.confidence is q.approval_status is q.human_review_required is None
    assert assess_quality(final,[]).fallback_used is None


@pytest.mark.parametrize('suffix',['quality','economics'])
def test_signal_endpoints_missing_or_unavailable(settings,service,suffix):
    store,enqueue,_=service
    with TestClient(create_app(settings,store,enqueue)) as client:
        store.get.side_effect=ValueError('absent')
        assert client.get(f'/executions/{uuid4()}/{suffix}').status_code==404
        store.get.side_effect=RuntimeError('secret DSN')
        response=client.get(f'/executions/{uuid4()}/{suffix}')
        assert response.status_code==503 and 'secret' not in response.text


def test_signal_endpoints_normal(settings,service,final):
    store,enqueue,_=service;store.get.return_value=final
    store.events.return_value=events(final,'execution.queued','execution.completed')
    with TestClient(create_app(settings,store,enqueue)) as client:
        path=f'/executions/{final.execution_id}'
        assert client.get(path+'/quality').json()['fallback_used'] is False
        assert client.get(path+'/economics').json()['cost_source']=='mock_no_usage'


@pytest.fixture
def pricing():
    # Controlled arithmetic fixture, NOT provider prices.
    return PricingConfig(version='test-fixture-only',models={'fixture-model':{
        'input_per_million':'2','output_per_million':'8','currency':'USD'}})


def test_economics_mock_never_invents_usage(final,pricing):
    e=assess_economics(final,events(final,'execution.queued','execution.completed'),'fixture-model',pricing)
    assert e.llm_calls==0
    assert e.input_tokens is e.output_tokens is e.estimated_llm_cost is e.estimated_execution_cost is None
    assert e.cost_source=='mock_no_usage' and e.model is None


def test_economics_aggregates_durable_provider_usage_and_retry(execution,pricing):
    execution=execution.model_copy(update={'llm_mode':'openai'})
    history=events(execution,'execution.queued','llm.requested','llm.failed','llm.retry',
        'llm.requested','llm.completed','llm.requested','llm.completed','llm.fallback_activated',
        'execution.retry','execution.completed')
    history[5]=history[5].model_copy(update={'input_tokens':100,'output_tokens':20})
    history[7]=history[7].model_copy(update={'input_tokens':200,'output_tokens':30,'attempt':2})
    e=assess_economics(execution,history,'fixture-model',pricing)
    assert e.llm_calls==3 and e.input_tokens==300 and e.output_tokens==50
    assert e.retry_count==1 and e.task_retry_count==1 and e.fallback_used
    assert e.estimated_llm_cost==Decimal('0.001') and e.cost_currency=='USD'
    assert e.pricing_version=='test-fixture-only' and e.usage_coverage=='partial_or_unavailable'
    assert e.estimated_execution_cost is None


@pytest.mark.parametrize('input_tokens,output_tokens',[(0,0),(100,20),(None,20),(100,None),(None,None)])
def test_economics_usage_availability(execution,pricing,input_tokens,output_tokens):
    execution=execution.model_copy(update={'llm_mode':'openai'})
    history=events(execution,'llm.requested','llm.completed')
    history[1]=history[1].model_copy(update={'input_tokens':input_tokens,'output_tokens':output_tokens})
    e=assess_economics(execution,history,'fixture-model',pricing)
    if input_tokens is not None and output_tokens is not None:
        assert e.estimated_llm_cost is not None and e.usage_coverage=='recorded_calls'
    else:
        assert e.estimated_llm_cost is None and e.usage_coverage=='partial_or_unavailable'


def test_usage_without_pricing_and_missing_history(execution,pricing):
    execution=execution.model_copy(update={'llm_mode':'openai'})
    history=events(execution,'llm.requested','llm.completed')
    history[1]=history[1].model_copy(update={'input_tokens':100,'output_tokens':20})
    e=assess_economics(execution,history,'unknown-model',pricing)
    assert e.cost_source=='pricing_unconfigured' and e.input_tokens==100 and e.estimated_llm_cost is None
    e=assess_economics(execution,[],'fixture-model',pricing)
    assert e.llm_calls is None and e.input_tokens is None and e.estimated_llm_cost is None


def test_pricing_is_explicit_config(monkeypatch,tmp_path,pricing):
    monkeypatch.delenv('CONTROL_TOWER_PRICING_FILE',raising=False)
    assert load_pricing().models=={}
    path=tmp_path/'pricing.json';path.write_text(pricing.model_dump_json())
    monkeypatch.setenv('CONTROL_TOWER_PRICING_FILE',str(path))
    assert load_pricing()==pricing
    with pytest.raises(ValueError):
        PricingConfig(version='bad',models={'x':{'input_per_million':-1,'output_per_million':0,'currency':'USD'}})


def test_quality_history_gap_does_not_prove_no_fallback(final):
    history=events(final,'execution.queued','execution.completed')
    history[-1]=history[-1].model_copy(update={'sequence':99})
    assert assess_quality(final,history).fallback_used is None


def test_economics_partial_completed_response_does_not_estimate_total(execution,pricing):
    execution=execution.model_copy(update={'llm_mode':'openai'})
    history=events(execution,'llm.requested','llm.completed','llm.requested','llm.completed')
    history[1]=history[1].model_copy(update={'input_tokens':100,'output_tokens':20})
    history[3]=history[3].model_copy(update={'output_tokens':30})
    result=assess_economics(execution,history,'fixture-model',pricing)
    assert result.input_tokens==100 and result.output_tokens==50
    assert result.estimated_llm_cost is None


def test_mcp_span_uses_sdk_context_and_can_parent_publish(settings,service):
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    from control_tower.telemetry import tracing
    store,enqueue,capability=service
    exporter=InMemorySpanExporter()
    tracing.initialize_tracing(settings.model_copy(update={'otel_enabled':True}),span_exporter=exporter)
    async def check():
        async with create_connected_server_and_client_session(create_server(capability)) as client:
            result=await client.call_tool('submit_incident',{'request':{'incident_id':'MCP-SPAN'}})
            assert not result.isError
            return result.structuredContent
    try:
        result=asyncio.run(check())
        spans=exporter.get_finished_spans()
        span=next(s for s in spans if s.name=='mcp tool submit_incident')
        assert result['trace_id']==format(span.context.trace_id,'032x')
        assert span.context.is_valid
    finally: tracing.shutdown()


def test_economics_bad_pricing_and_history_fail_safely(settings,service,monkeypatch,tmp_path):
    store,enqueue,_=service
    path=tmp_path/'pricing.json';path.write_text('invalid-secret')
    monkeypatch.setenv('CONTROL_TOWER_PRICING_FILE',str(path))
    with TestClient(create_app(settings,store,enqueue)) as client:
        uid=store.get.return_value.execution_id
        response=client.get(f'/executions/{uid}/economics')
        assert response.status_code==503 and 'secret' not in response.text
        store.events.side_effect=RuntimeError('secret DSN')
        response=client.get(f'/executions/{uid}/quality')
        assert response.status_code==503 and 'secret' not in response.text


@pytest.mark.parametrize('body',[{}, {'incident_id':'SECRET INVALID INPUT'},
                                {'incident_id':'ok','secret':'PRIVATE'},
                                {'incident_id':'ok','reference_case_id':'SECRET'}])
def test_mcp_invalid_payload_is_sanitized_and_never_enqueues(service,body):
    _,enqueue,capability=service
    async def check():
        async with create_connected_server_and_client_session(create_server(capability)) as client:
            result=await client.call_tool('submit_incident',{'request':body})
            text=' '.join(c.text for c in result.content)
            assert result.isError and '422' in text
            assert 'SECRET' not in text and 'PRIVATE' not in text
    asyncio.run(check())
    enqueue.assert_not_called()
