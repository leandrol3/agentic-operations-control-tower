"""Views para projeção: recortes reais, sem antecipar a narrativa."""
from pathlib import Path
import os
import subprocess
import sys

import pytest

from control_tower.agents import challenger, finance
from control_tower.graph.workflow import run_workflow
from control_tower.tools import Tools
from control_tower.views import VIEWS, load_view, render_view, show

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def demo():
    tools = Tools(ROOT)
    return tools, tools.load_incident(ROOT / 'incidents/incident_001.json')


@pytest.mark.parametrize('view', VIEWS)
def test_view_fits_projector_terminal(demo, view):
    text, blocked = show(*demo, view)
    assert not blocked
    # Contrato explícito: reservar 4 linhas para prompt em uma tela de 96 x 24.
    assert len(text.splitlines()) <= 20
    assert max(map(len, text.splitlines())) <= 96


@pytest.mark.parametrize('view', ['summary', 'state', 'specialists', 'coordination'])
def test_early_views_do_not_execute_downstream(demo, view, monkeypatch):
    def forbidden(*args):
        pytest.fail('View inicial executou Finance/Challenger')
    monkeypatch.setattr(finance, 'analyze', forbidden)
    monkeypatch.setattr(challenger, 'challenge', forbidden)
    state = load_view(*demo, view)
    assert state.investigation is not None
    assert all(getattr(state, key) is None for key in ('finance', 'review', 'recommendation', 'approval'))
    text, _ = show(*demo, view)
    for word in ('12500', '12.500', 'recommendation', 'recomendação', 'challenger', 'approval', 'cenário D'):
        assert word.lower() not in text.lower()


def test_summary_exposes_registered_safety_stock(demo):
    text, _ = show(*demo, 'summary')
    for evidence in ('disponível 300 | demanda 750 | déficit 450', 'disponível 500 | safety stock 200',
                     'piso: 300', 'capacidade 450', 'custo/un. 145', 'prêmio/un. 45', '5.000', '18.000'):
        assert evidence in text
    assert demo[0].get_safety_stock('M42', 'Recife') == 20
    with pytest.raises(ValueError, match='Estoque não cadastrado'):
        demo[0].get_safety_stock('M42', 'unknown')


def test_scenarios_show_admissibility_without_recommendation(demo):
    state = load_view(*demo, 'scenarios')
    assert state.finance is not None and state.review is not None
    assert state.recommendation is None and state.approval is None
    text = render_view(state, 'scenarios', demo[0])
    assert 'piso -150' in text and 'não' in text
    assert all(value in text for value in ('23.500', '20.250', '18.000', '12.500', '0/4/3', '0/0/3'))
    assert 'Finance propõe' not in text and 'awaiting_approval' not in text
    assert 'customer_delay_days=3' in text and 'confidence=0.65' in text


def test_challenger_has_four_stages_and_no_final_recommendation(demo):
    text, _ = show(*demo, 'challenger')
    assert all(label in text for label in ('Candidate Plan', 'Assumptions', 'Challenges', 'Remaining Risks'))
    assert 'C: Transferência rompe safety stock' in text
    assert 'awaiting_approval' not in text and 'actions_executed' not in text


def test_final_view_is_same_workflow_and_human_boundary(demo):
    state = load_view(*demo, 'recommendation')
    assert state == run_workflow(*demo)
    text = render_view(state, 'recommendation', demo[0])
    assert 'actions_executed = false' in text
    assert 'awaiting_approval' in text and '12.500' in text and '16.000' in text and '11.000' in text


def test_coordination_retains_parallel_join_and_stops(demo):
    events = []
    state = load_view(*demo, 'coordination', observer=lambda n, p: events.append((n, p)))
    join = events.index(('consolidation', 'início'))
    assert all(events.index((n, 'fim')) < join for n in ('supply', 'production', 'logistics'))
    assert state.finance is None
    assert state == load_view(*demo, 'coordination', sequential=True)


def test_coordination_failure_does_not_invent_results(demo):
    text, blocked = show(*demo, 'coordination', fail_specialist='logistics')
    assert blocked and 'Falha simulada' in text
    assert 'evidência' in text and '12500' not in text


@pytest.mark.parametrize('view', VIEWS)
def test_cli_show(demo, view):
    result = subprocess.run([sys.executable, '-m', 'control_tower.main', 'show', 'INCIDENT-001', view],
                            cwd=ROOT, env=dict(os.environ, LLM_MODE='mock'), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert len(result.stdout.splitlines()) <= 20


@pytest.mark.parametrize('args', [
    ['show', 'INCIDENT-001'], ['show', 'INCIDENT-999', 'state'],
    ['show', 'INCIDENT-001', 'state', '--json'],
    ['show', 'INCIDENT-001', 'state', '--fail-specialist', 'logistics'],
    ['run', 'INCIDENT-001', 'state'],
])
def test_show_argument_errors_are_explicit(args):
    result = subprocess.run([sys.executable, '-m', 'control_tower.main', *args],
                            cwd=ROOT, env=dict(os.environ, LLM_MODE='mock'), capture_output=True, text=True)
    assert result.returncode == 2 and not result.stdout
