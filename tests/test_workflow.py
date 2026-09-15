"""Regressões comportamentais das Demos 5–8; sem API, relógio ou dados externos."""
from datetime import date
from decimal import Decimal
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from threading import Barrier

import pytest
from pydantic import ValidationError

from control_tower.agents import challenger, finance, specialists, supervisor
from control_tower.graph.state import Approval, Investigation, Result, WorkflowState
from control_tower.graph.workflow import build_graph, run_workflow, route_supervisor
from control_tower.scenarios import simulate
from control_tower.tools import Tools

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def tools():
    return Tools(ROOT)


@pytest.fixture
def incident(tools):
    return tools.load_incident(ROOT / 'incidents/incident_001.json')


@pytest.fixture
def evidence(tools, incident):
    return Investigation(supply=specialists.supply(tools, incident),
                         production=specialists.production(tools, incident),
                         logistics=specialists.logistics(tools, incident))


@pytest.mark.parametrize('values', [{}, {'data': 'ok', 'error': 'bad'}, {'error': ''}])
def test_result_requires_evidence_or_error(values):
    with pytest.raises(ValidationError):
        Result(**values)


@pytest.mark.parametrize('change', [
    {'plan': ('unknown',)}, {'status': 'approved'}, {'status': 'awaiting_approval'},
    {'unexpected': True}, {'supply': {'data': {'local': 'not a stock'}}},
])
def test_typed_state_rejects_invalid_values(incident, change):
    with pytest.raises(ValidationError):
        WorkflowState(incident=incident, **change)


def test_supervisor_selects_three_independent_specialists(incident):
    state = WorkflowState(incident=incident)
    update = supervisor.supervise(state)
    state = WorkflowState.model_validate(state.model_dump() | update)
    assert route_supervisor(state) == ['supply', 'production', 'logistics']


def test_unknown_incident_routes_to_blocked(tools, incident):
    state = run_workflow(tools, incident.model_copy(update={'material': 'M99'}))
    assert state.status == 'blocked'
    assert state.plan == ()
    assert state.supply is None and state.finance is None and state.recommendation is None


def test_specialists_return_evidence_not_decisions(evidence):
    assert evidence.supply.local.available_units == 300
    assert evidence.supply.alternative.supplier_id == 'SUP-BETA'
    assert evidence.production.demand_units == 750
    assert len(evidence.production.customers) == 3
    assert evidence.logistics.standard.lead_time_days == 3
    assert evidence.logistics.express.lead_time_days == 1


def test_join_rejects_missing_result(incident, evidence):
    state = WorkflowState(incident=incident, plan=('supply', 'production', 'logistics'),
                          supply=Result(data=evidence.supply), production=Result(data=evidence.production))
    update = supervisor.consolidate(state)
    assert update['blockers'] == ('logistics: resultado ausente',)
    assert 'investigation' not in update


def test_parallel_branches_overlap_and_join_runs_once(monkeypatch, tools, incident):
    # Nenhum ramo termina até os três iniciarem: prova concorrência sem benchmark frágil.
    barrier = Barrier(3, timeout=5)
    for name in ('supply', 'production', 'logistics'):
        original = getattr(specialists, name)
        def synchronized(t, i, function=original):
            barrier.wait()
            return function(t, i)
        monkeypatch.setattr(specialists, name, synchronized)
    events = []
    state = run_workflow(tools, incident, observer=lambda n, p: events.append((n, p)))
    assert state.status == 'awaiting_approval'
    assert events.count(('consolidation', 'início')) == 1
    join = events.index(('consolidation', 'início'))
    assert all(events.index((name, 'fim')) < join for name in ('supply', 'production', 'logistics'))
    assert events.index(('finance', 'início')) > events.index(('consolidation', 'fim'))


def test_sequential_control_same_result_and_order(tools, incident):
    events = []
    sequential = run_workflow(tools, incident, sequential=True, observer=lambda n, p: events.append((n, p)))
    parallel = run_workflow(tools, incident)
    assert sequential == parallel
    assert events.index(('supply', 'fim')) < events.index(('production', 'início'))
    assert events.index(('production', 'fim')) < events.index(('logistics', 'início'))


@pytest.mark.parametrize('name', ['supply', 'production', 'logistics'])
def test_failed_specialist_blocks_finance_and_recommendation(tools, incident, name):
    state = run_workflow(tools, incident, fail_specialist=name)
    assert state.status == 'blocked'
    assert getattr(state, name).error == 'Falha simulada pelo professor'
    assert all(getattr(state, n).data is not None for n in ('supply', 'production', 'logistics') if n != name)
    assert state.investigation is None and state.finance is None
    assert state.review is None and state.recommendation is None and state.approval is None


def test_invalid_specialist_schema_blocks_flow(monkeypatch, tools, incident):
    def bad_evidence(t, i):
        from control_tower.graph.state import ProductionEvidence
        return ProductionEvidence(orders=(), customers=(), demand_units=0)
    monkeypatch.setattr(specialists, 'production', bad_evidence)
    state = run_workflow(tools, incident)
    assert state.status == 'blocked' and state.finance is None
    assert 'Ordens ausentes' in state.production.error


@pytest.mark.parametrize('scenario_id,total,penalty,delays', [
    ('A', '23500.00', '23500.00', [0, 4, 3]),
    ('B', '20250.00', '0', [0, 0, 0]),
    ('C', '18000.00', '0', [0, 0, 0]),
    ('D', '12500.00', '7500.00', [0, 0, 3]),
])
def test_finance_scenarios_calculate_customer_delays(tools, incident, evidence, scenario_id, total, penalty, delays):
    scenario = simulate(tools, incident, evidence, scenario_id)
    assert scenario.total_cost_brl == Decimal(total)
    assert scenario.penalty_brl == Decimal(penalty)
    assert [d.delay_days for d in scenario.deliveries] == delays
    assert sum(a.units for d in scenario.deliveries for a in d.allocations) == 750
    assert sum(a.units for d in scenario.deliveries for a in d.allocations if a.source == 'local') == 300


def test_d_preserves_origin_safety_stock_and_uses_residual_alpha(tools, incident, evidence):
    scenario = simulate(tools, incident, evidence, 'D')
    assert scenario.transferred_units == 300
    assert scenario.origin_remaining_units == 200
    assert scenario.origin_safety_breach_units == 0
    assert scenario.deliveries[1].production_date == date(2026, 10, 4)
    assert scenario.deliveries[2].delivery_date == date(2026, 10, 9)
    assert sum(a.units for d in scenario.deliveries for a in d.allocations if a.source == 'SUP-ALPHA') == 150


def test_allocation_independent_of_input_row_order(tools, incident, evidence):
    reordered = evidence.model_copy(update={'production': evidence.production.model_copy(update={
        'orders': tuple(reversed(evidence.production.orders))})})
    assert finance.analyze(tools, incident, evidence) == finance.analyze(tools, incident, reordered)


def test_insufficient_capacity_blocks_finance(tools, incident, monkeypatch):
    original = specialists.supply
    def low_capacity(t, i):
        supply = original(t, i)
        return supply.model_copy(update={'alternative': supply.alternative.model_copy(update={'capacity_units': 1})})
    monkeypatch.setattr(specialists, 'supply', low_capacity)
    state = run_workflow(tools, incident)
    assert state.status == 'blocked'
    assert 'Capacidade de Beta insuficiente' in state.blockers[0]
    assert state.recommendation is None


def test_challenger_distinguishes_policy_and_missing_information(tools, incident, evidence):
    report = finance.analyze(tools, incident, evidence)
    review = challenger.challenge(tools, evidence, report)
    assert review.selected_scenario == 'D'
    assert any(f.scenario_id == 'C' and f.blocking and '150 unidades' in f.message for f in review.findings)
    assert any(f.category == 'missing_information' and not f.blocking for f in review.findings)


def test_challenger_rejects_inconsistent_cost_and_selects_alternative(tools, incident, evidence):
    report = finance.analyze(tools, incident, evidence)
    modified = report.model_copy(update={'scenarios': tuple(
        s.model_copy(update={'total_cost_brl': Decimal('1')}) if s.scenario_id == 'D' else s
        for s in report.scenarios)})
    review = challenger.challenge(tools, evidence, modified)
    assert review.selected_scenario == 'B'  # C é mais barato, mas viola safety stock.
    assert any(f.category == 'inconsistency' and f.scenario_id == 'D' for f in review.findings)


def test_challenger_blocks_missing_scenario(tools, incident, evidence):
    report = finance.analyze(tools, incident, evidence)
    review = challenger.challenge(tools, evidence, report.model_copy(update={'scenarios': report.scenarios[:3]}))
    assert review.selected_scenario is None
    assert review.findings[0].blocking


def test_challenger_blocks_strategic_delay(tools, incident, evidence):
    # Reduz o prazo do cliente estratégico para tornar TODOS os cenários inadmissíveis.
    customers = tuple(c.model_copy(update={'delivery_date': date(2026, 10, 1)})
                      if c.priority == 'strategic' else c for c in evidence.production.customers)
    evidence = evidence.model_copy(update={'production': evidence.production.model_copy(update={'customers': customers})})
    review = challenger.challenge(tools, evidence, finance.analyze(tools, incident, evidence))
    assert review.selected_scenario is None
    assert any('estratégico' in f.message for f in review.findings)


def test_recommendation_and_human_approval_end_to_end(tools, incident):
    state = run_workflow(tools, incident)
    assert state.status == 'awaiting_approval'
    assert state.recommendation.estimated_cost_brl == Decimal('12500')
    assert state.recommendation.avoided_penalty_brl == Decimal('16000')
    assert state.recommendation.customer_delay_days == 3
    assert state.recommendation.approval_required is True
    assert state.approval.status == 'pending'
    assert state.approval.actions_executed is False
    assert state.approval.authority == 'operations_manager'
    assert WorkflowState.model_validate_json(state.model_dump_json()) == state


@pytest.mark.parametrize('threshold,authority', [('12500', 'operations_manager'), ('12499', 'manager')])
def test_approval_threshold_boundary(tools, incident, threshold, authority):
    tools.policies = tools.policies.model_copy(update={'manager_approval_threshold_brl': Decimal(threshold)})
    state = run_workflow(tools, incident)
    assert state.approval.authority == authority
    assert state.approval.required is True


@pytest.mark.parametrize('change', [{'required': False}, {'status': 'approved'}, {'actions_executed': True}])
def test_human_approval_cannot_be_bypassed(change):
    with pytest.raises(ValidationError):
        Approval(authority='operations_manager', **change)


def test_mock_is_offline_and_deterministic(monkeypatch, tools, incident):
    def no_network(*args, **kwargs):
        pytest.fail('Mock tentou acessar a rede')
    monkeypatch.setattr(socket.socket, 'connect', no_network)
    monkeypatch.setattr(socket, 'create_connection', no_network)
    monkeypatch.setenv('LANGSMITH_TRACING', 'true')
    first = run_workflow(tools, incident)
    assert first == run_workflow(tools, incident)


def test_graph_contains_explicit_join_and_no_action_nodes(tools):
    graph = build_graph(tools).get_graph()
    edges = {(e.source, e.target) for e in graph.edges}
    assert all((name, 'consolidation') in edges for name in ('supply', 'production', 'logistics'))
    assert ('human_approval', '__end__') in edges
    assert set(graph.nodes) == {'__start__', '__end__', 'supervisor', 'supply', 'production', 'logistics',
                               'consolidation', 'finance', 'challenger', 'recommendation', 'human_approval', 'blocked'}


@pytest.mark.parametrize('options,expected', [([], 0), (['--fail-specialist', 'logistics'], 1),
                                           (['--demo-delay-ms', '-1'], 2)])
def test_run_cli(tools, options, expected):
    result = subprocess.run([sys.executable, '-m', 'control_tower.main', 'run', 'INCIDENT-001', '--json', *options],
                            cwd=ROOT, env=dict(os.environ, LLM_MODE='mock'), text=True, capture_output=True)
    assert result.returncode == expected, result.stderr
    if expected in (0, 1):
        state = WorkflowState.model_validate_json(result.stdout)
        assert state.status == ('awaiting_approval' if expected == 0 else 'blocked')


def test_cli_unknown_incident_not_silently_replaced():
    result = subprocess.run([sys.executable, '-m', 'control_tower.main', 'run', 'INCIDENT-999'],
                            cwd=ROOT, env=dict(os.environ, LLM_MODE='mock'), text=True, capture_output=True)
    assert result.returncode == 2
    assert not result.stdout


def test_invalid_return_at_agent_boundary_becomes_error(monkeypatch, tools, incident):
    monkeypatch.setattr(specialists, 'supply', lambda t, i: {'invented': 'not evidence'})
    state = run_workflow(tools, incident)
    assert state.supply.error is not None
    assert state.status == 'blocked' and state.finance is None


def test_graph_stops_when_challenger_has_no_admissible_scenario(monkeypatch, tools, incident):
    from control_tower.graph.state import Review
    monkeypatch.setattr(challenger, 'challenge', lambda *args: Review(findings=(), selected_scenario=None))
    state = run_workflow(tools, incident)
    assert state.status == 'blocked'
    assert state.finance is not None and state.recommendation is None and state.approval is None


def test_workflow_never_mutates_operational_data(tools, incident):
    paths = list((ROOT / 'data').glob('*')) + list((ROOT / 'incidents').glob('*'))
    before = {p: p.read_bytes() for p in paths}
    run_workflow(tools, incident)
    run_workflow(tools, incident, fail_specialist='supply')
    assert {p: p.read_bytes() for p in paths} == before


@pytest.mark.parametrize('limit,blocked', [('18000', False), ('17999', True)])
def test_expedited_freight_policy_boundary(tools, incident, evidence, limit, blocked):
    # Isola política de frete: neste experimento, piso da origem permite transferir 450.
    origin = evidence.supply.origin.model_copy(update={'transferable_without_safety_stock_units': 500})
    evidence = evidence.model_copy(update={'supply': evidence.supply.model_copy(update={'origin': origin})})
    tools.policies = tools.policies.model_copy(update={'max_expedited_freight_brl': Decimal(limit)})
    review = challenger.challenge(tools, evidence, finance.analyze(tools, incident, evidence))
    assert any(f.scenario_id == 'C' and f.blocking and 'Frete expresso' in f.message
               for f in review.findings) == blocked
