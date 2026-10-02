"""Control Plane: deterministic interpretation, boundaries and no ACT/provider calls."""
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

import pytest
pytest.importorskip('mcp')
pytest.importorskip('psycopg')
pytest.importorskip('celery')
from fastapi.testclient import TestClient
from control_tower.api.app import create_app
from control_tower.control_plane.configuration import load_config, ControlPlaneConfig
from control_tower.control_plane.contracts import AgentSLO, Evidence, EvaluationStatus, Trend
from control_tower.control_plane.economics import PricingConfig
from control_tower.control_plane.demo_fixture import fixture_samples
from control_tower.control_plane.registry import registry, LifecycleState as State
from control_tower.control_plane.lifecycle import ALLOWED_TRANSITIONS, transition, can_transition
from control_tower.control_plane.interpretation import evaluate_slo, trend
from control_tower.control_plane.collection import collect_stage
from control_tower.control_plane.service import ControlPlane
from test_lesson04 import settings, service, execution

ROOT=Path(__file__).resolve().parents[1]
NOW=datetime(2026,10,2,12,tzinfo=timezone.utc)


@pytest.fixture
def plane(monkeypatch):
    monkeypatch.setenv('CONTROL_PLANE_CONFIG_FILE',str(ROOT/'config/lesson04-control-plane.json'))
    monkeypatch.setenv('CONTROL_TOWER_PRICING_FILE',str(ROOT/'config/lesson04-pricing.json'))
    return ControlPlane(None)


def evaluate(plane, scenario='stable', agent='logistics', samples=None):
    return plane.evaluate(samples=fixture_samples(scenario) if samples is None else samples,
        mode='openai',source='didactic_fixture',agent_id=agent,now=NOW)[0]


def test_goal_measurement_gap_and_evidence(plane):
    v=evaluate(plane,'optimize');g=v.goals[0]
    assert g.target==100 and g.actual==Decimal(200)/3
    assert g.gap==g.actual-100 and g.attainment==g.actual/100
    assert g.status=='off_target' and g.evidence_source=='didactic_fixture'
    assert len(g.evidence.execution_ids)==3
    assert g.measured_at==NOW and 'not semantic correctness' in g.evidence.note


def test_empty_history_is_unknown_no_recommendation(plane):
    v=evaluate(plane,samples=[])
    assert v.goals[0].actual is v.goals[0].gap is v.goals[0].attainment is None
    assert v.goals[0].status=='unknown' and v.recommendation is None
    assert all(s.status=='unknown' for s in v.slos)
    assert v.cost_trend==v.goal_trend=='unknown'


@pytest.mark.parametrize('count',[1,2])
def test_minimum_samples_prevents_conclusions(plane,count):
    v=evaluate(plane,samples=fixture_samples('stable')[-count:])
    assert v.goals[0].status=='unknown' and v.recommendation is None


def test_truncated_history_never_becomes_success_or_zero_cost(plane):
    rows=fixture_samples('stable')
    rows[-1]=rows[-1].model_copy(update={'events':rows[-1].events[1:]})
    v=evaluate(plane,samples=rows)
    assert v.goals[0].actual is None and v.economics.observed is None
    assert v.recommendation is None


def test_missing_stage_not_inferred_from_completed_execution(plane):
    rows=fixture_samples('stable');r=rows[-1]
    events=[e for e in r.events if e.agent_id!='logistics']
    rows[-1]=r.model_copy(update={'events':tuple(e.model_copy(update={'sequence':i}) for i,e in enumerate(events,1))})
    v=evaluate(plane,samples=rows)
    assert v.goals[0].actual is None and v.latency.observed is None


def test_retry_last_attempt_wins_and_role_cost_is_not_workflow_cost(plane):
    sample=fixture_samples('stable')[0]
    # Earlier attempt's terminal must never override the final attempt's stage.
    events=list(sample.events)
    idx=next(i for i,e in enumerate(events) if e.event_type=='logistics.completed')
    events[idx]=events[idx].model_copy(update={'attempt':2,'event_type':'logistics.failed'})
    sample=sample.model_copy(update={'execution':sample.execution.model_copy(update={'attempt':2}), 'events':tuple(events)})
    signal=collect_stage(sample,'logistics',plane.pricing)
    assert signal['success'] is False
    assert signal['cost']==Decimal('0.00056')  # one role, not six times this amount


@pytest.mark.parametrize('mutate',['missing_usage','failed_request'])
def test_incomplete_role_usage_stays_unknown(plane,mutate):
    rows=fixture_samples('stable');r=rows[-1];events=list(r.events)
    index=next(i for i,e in enumerate(events) if e.event_type=='llm.completed' and e.agent_id=='logistics')
    events[index]=events[index].model_copy(update={'input_tokens':None} if mutate=='missing_usage'
        else {'event_type':'llm.failed','input_tokens':None,'output_tokens':None})
    rows[-1]=r.model_copy(update={'events':tuple(events)})
    assert evaluate(plane,samples=rows).economics.observed is None


def test_mock_and_finance_have_no_invented_cost(plane):
    rows=[r.model_copy(update={'execution':r.execution.model_copy(update={'llm_mode':'mock'}),
        'options':r.options.model_copy(update={'llm_mode':'mock'})}) for r in fixture_samples('stable')]
    views=plane.evaluate(samples=rows,mode='mock',source='didactic_fixture')
    assert all(v.economics.observed is None and v.recommendation is None for v in views)
    assert evaluate(plane,agent='finance').economics.observed is None


@pytest.mark.parametrize('operator,observed,status',[
    ('>=',100,'pass'),('>=',92,'warn'),('>=',90,'warn'),('>=',89,'violation'),('>=',None,'unknown'),
    ('<=',80,'pass'),('<=',88,'warn'),('<=',90,'warn'),('<=',91,'violation'),('<=',None,'unknown')])
def test_slo_operators_thresholds_and_unknown(operator,observed,status):
    s=AgentSLO(slo_id='fixture',metric='completion_rate',target=90,operator=operator,warning_margin=5,severity='high')
    e=Evidence(metric='completion_rate',observed=observed,unit='percent',scope='agent_stage',source='didactic_fixture',note='fixture')
    assert evaluate_slo(s,e,'supply').status==status


@pytest.mark.parametrize('current,previous,expected',[(10,10,'stable'),(11,10,'degrading'),(9,10,'improving'),(None,10,'unknown'),(1,0,'degrading'),(0,0,'stable')])
def test_trend(current,previous,expected):
    assert trend(Decimal(current) if current is not None else None,Decimal(previous),Decimal('.05'))==expected


@pytest.mark.parametrize('current',list(State))
@pytest.mark.parametrize('target',list(State))
def test_explicit_lifecycle_machine(current,target):
    allowed=target in ALLOWED_TRANSITIONS[current]
    assert can_transition(current,target)==allowed
    if allowed:
        with pytest.raises(PermissionError): transition(current,target)
        assert transition(current,target,human_authorized=True)==target
    else:
        with pytest.raises(ValueError): transition(current,target,human_authorized=True)


@pytest.mark.parametrize('scenario,action,priority',[
    ('stable','scale','low'),('optimize','optimize','medium'),('intervene','intervene','high'),
    ('review','review','high'),('pause','pause','critical')])
def test_decisions_have_evidence_and_never_act(plane,scenario,action,priority,monkeypatch):
    import control_tower.control_plane.lifecycle as lifecycle
    monkeypatch.setattr(lifecycle,'transition',MagicMock(side_effect=AssertionError('No ACT')))
    v=evaluate(plane,scenario);r=v.recommendation
    assert r.action==action and r.priority==priority
    assert r.requires_human_approval and r.evidence and r.reason and r.generated_at==NOW
    assert all(e.observed is not None and e.execution_ids for e in r.evidence)
    assert v.registry.lifecycle_state==r.current_lifecycle_state==State.ACTIVE
    assert r.recommendation_id==evaluate(plane,scenario).recommendation.recommendation_id
    assert all(a.lifecycle_state==State.ACTIVE for a in registry())
    assert not lifecycle.transition.called


def test_persistent_rule_requires_two_bad_windows(plane):
    assert evaluate(plane,'review').recommendation.action!='pause'
    assert evaluate(plane,'pause').recommendation.action=='pause'


def test_no_automatic_resume_of_paused_or_retired(plane):
    for state in (State.PAUSED,State.RETIRED):
        plane.records=tuple(r.model_copy(update={'lifecycle_state':state}) for r in registry())
        assert evaluate(plane).recommendation is None


def test_model_change_invalidates_cost_trend(plane):
    rows=fixture_samples('stable')
    rows[0]=rows[0].model_copy(update={'options':rows[0].options.model_copy(update={'llm_model':'other'})})
    assert evaluate(plane,samples=rows).cost_trend=='unknown'


def test_value_is_not_cost_or_savings(plane):
    v=evaluate(plane)
    items=v.business_value
    assert {x.value_metric for x in items}=={'recommended_scenario_cost','workflow_time_to_proposal_ms','realized_business_value'}
    realized=[x for x in items if x.value_metric=='realized_business_value']
    assert all(x.value_amount is None and x.status=='unknown' for x in realized)
    proposal=items[0]
    assert proposal.value_amount==Decimal('12500') and proposal.currency_or_unit=='BRL'
    assert v.economics.unit=='USD' and v.economics.observed==Decimal('.00056')


def test_duplicate_cohort_is_rejected(plane):
    rows=fixture_samples('stable')
    with pytest.raises(ValueError): evaluate(plane,samples=rows+[rows[0]])


def test_api_read_only_public_views_and_errors(plane,settings,service):
    store,enqueue,_=service
    store.control_plane_samples.return_value=fixture_samples('optimize')
    with TestClient(create_app(settings,store,enqueue)) as client:
        response=client.get('/control-plane/agents/logistics?mode=openai')
        assert response.status_code==200
        body=response.json()
        assert body['recommendation']['action']=='optimize'
        assert body['registry']['execution_type']=='deterministic'  # Current mock registry != historical openai cohort.
        assert body['evidence_source']=='durable_history'
        assert len(client.get('/control-plane/agents?mode=openai').json())==7
        assert client.get('/control-plane/recommendations?mode=openai').json()
        assert client.get('/control-plane/agents/no-agent').status_code==404
        assert client.get('/control-plane/agents?mode=invalid').status_code==422
        assert client.post('/control-plane/agents/logistics',json={'lifecycle_state':'paused'}).status_code==405
        assert not any(secret in response.text for secret in ('idempotency_key','input_tokens','synthetic_stage_failure'))
        store.control_plane_samples.side_effect=RuntimeError('SECRET DSN')
        response=client.get('/control-plane/agents')
        assert response.status_code==503 and 'SECRET' not in response.text
    enqueue.assert_not_called()


def test_spans_and_no_graph_execution(plane,settings,monkeypatch):
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    from control_tower.telemetry import tracing
    from control_tower.graph import workflow
    monkeypatch.setattr(workflow,'run_workflow',MagicMock(side_effect=AssertionError('Runtime called')))
    exporter=InMemorySpanExporter()
    tracing.initialize_tracing(settings.model_copy(update={'otel_enabled':True}),span_exporter=exporter)
    try:
        evaluate(plane)
        names={s.name for s in exporter.get_finished_spans()}
        assert {'control_plane evaluate','goal evaluate','slo evaluate','decision engine'} <= names
        assert not workflow.run_workflow.called
    finally:
        tracing.shutdown()


def test_config_invalid_minimum_and_duplicates(plane):
    data=plane.config.model_dump()
    with pytest.raises(ValueError): ControlPlaneConfig.model_validate(data|{'min_samples':50})
    with pytest.raises(ValueError): ControlPlaneConfig.model_validate(data|{'slos':data['slos']*2})


def test_goal_at_risk_and_unsupported_metric(plane):
    from control_tower.control_plane.interpretation import measure_goal
    agent=registry()[0];goal=agent.business_goals[0]
    e=Evidence(metric='completion_rate',observed=97,unit='percent',scope='agent_stage',source='didactic_fixture',note='fixture')
    assert measure_goal(agent,goal,e,plane.config,NOW).status=='at_risk'
    unsupported=goal.model_copy(update={'metric':'human_acceptance'})
    g=measure_goal(agent,unsupported,e,plane.config,NOW)
    assert g.actual is None and g.status=='unknown'


def test_p95_uses_nearest_rank_and_requires_coverage(plane):
    from control_tower.control_plane.interpretation import metric_evidence
    rows=fixture_samples('stable')[:3]
    e=metric_evidence('stage_latency_p95_ms',rows,[{'latency':v} for v in (20,100,50)],plane.config,'didactic_fixture')
    assert e.observed==100
    e=metric_evidence('stage_latency_p95_ms',rows,[{'latency':v} for v in (20,None,50)],plane.config,'didactic_fixture')
    assert e.observed is None


def test_slo_unknown_and_warning_do_not_trigger_actions(plane):
    from control_tower.control_plane.interpretation import lifecycle_triggers
    v=evaluate(plane)
    warnings=tuple(s.model_copy(update={'status':EvaluationStatus.WARN}) for s in v.slos)
    assert not lifecycle_triggers(v.registry,v.goals,warnings,v.cost_trend,v.economics,v.previous_cost)


def test_persistent_trigger_is_explicit(plane):
    v=evaluate(plane,'pause')
    t=next(t for t in v.triggers if t.trigger_type=='persistent_underperformance')
    assert t.severity=='critical' and len(t.evidence)==2
    assert t.recommended_review


def test_changed_config_changes_recommendation_identity(plane):
    first=evaluate(plane).recommendation
    plane.config=plane.config.model_copy(update={'version':'another-config'})
    second=evaluate(plane).recommendation
    assert first.recommendation_id!=second.recommendation_id


def test_filtered_cohort_and_unknown_agent(plane):
    assert plane.evaluate(samples=fixture_samples('stable'),mode='mock')[0].sample_count==0
    with pytest.raises(LookupError): plane.evaluate(samples=[],agent_id='invalid')
    with pytest.raises(ValueError): plane.evaluate(samples=[],mode='invalid')


def test_scale_needs_all_dimensions(plane):
    plane.config=plane.config.model_copy(update={'slos':plane.config.slos[:1]})
    assert evaluate(plane).recommendation is None


def test_scale_does_not_transfer_historical_success_to_different_configuration(plane):
    plane.records=registry('mock')
    v=evaluate(plane)
    assert v.cohort_model=='gpt-4.1-mini'
    assert v.registry.model is None and v.recommendation is None
