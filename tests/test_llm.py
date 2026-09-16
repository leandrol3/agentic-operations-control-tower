"""Contratos e fronteiras LLM sem rede; a validação real é separada da suíte."""
import json
import os
from pathlib import Path
import subprocess
import sys
from threading import Barrier
from types import SimpleNamespace

import httpx
import pytest
from openai import AuthenticationError, APITimeoutError, RateLimitError
from pydantic import ValidationError

from control_tower.graph.workflow import build_graph, run_workflow
from control_tower.llm import (InvestigationPlan, SpecialistSynthesis, ChallengerJudgment,
                               RecommendationDecision, LLMRecommendation, OpenAIInterpreter)
from control_tower.settings import Settings
from control_tower.tools import Tools
from control_tower.views import show

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('supply', 'production', 'logistics')


class ScriptedInterpreter:
    model = 'test-double-not-a-real-llm'

    def __init__(self, change=None, barrier=None):
        self.change = change
        self.barrier = barrier
        self.calls = []

    def parse(self, role, schema, context):
        self.calls.append((role, context))
        if role == 'supervisor':
            value = dict(interpretation='Atraso de material exige investigação coordenada.',
                         tasks=[dict(specialist=n, question='Qual é a evidência disponível?') for n in NAMES])
        elif role in NAMES:
            if self.barrier:
                self.barrier.wait()
            value = dict(summary='Evidência sintetizada sem substituir dados.',
                         evidence_refs=context['allowed_evidence_refs'][:1], uncertainty='Confirmar disponibilidade.')
        elif role == 'challenger':
            value = dict(summary='Testar premissas antes de decidir.', findings=[dict(
                scenario_id='all', category='assumption', message='Confirmar capacidade produtiva.')])
        else:
            value = dict(scenario_id='D', rationale='Preserva piso e reduz custo; resta atraso residual.',
                         recommendation=context['templates']['D'])
        if self.change:
            self.change(role, value, context)
        return schema.model_validate(value)


@pytest.fixture
def demo():
    tools = Tools(ROOT)
    return tools, tools.load_incident(ROOT / 'incidents/incident_001.json')


def test_modes_share_graph_evidence_and_finance(demo):
    llm = ScriptedInterpreter()
    mock = run_workflow(*demo)
    real_mode = run_workflow(*demo, llm=llm)
    assert real_mode.llm_mode == 'openai'
    assert real_mode.investigation == mock.investigation
    assert real_mode.finance == mock.finance
    assert real_mode.recommendation.estimated_cost_brl == mock.recommendation.estimated_cost_brl
    assert real_mode.approval == mock.approval
    assert real_mode.status == 'awaiting_approval'
    assert sorted(n for n, _ in llm.calls) == sorted(['supervisor', *NAMES, 'challenger', 'recommendation'])
    assert build_graph(demo[0]).get_graph().to_json() == build_graph(demo[0], llm=llm).get_graph().to_json()
    assert any(f.blocking and f.scenario_id == 'C' for f in real_mode.review.findings)


def test_mock_preserves_previous_business_state(demo):
    previous = json.loads((ROOT/'docs/course/examples/incident-001-mock.json').read_text())
    current = run_workflow(*demo).model_dump(mode='json')
    assert {key: current[key] for key in previous} == previous


def test_syntheses_run_in_parallel_before_join(demo):
    events = []
    result = run_workflow(*demo, llm=ScriptedInterpreter(barrier=Barrier(3, timeout=5)),
                          observer=lambda n, p: events.append((n,p)))
    assert result.approval.actions_executed is False
    join = events.index(('consolidation','início'))
    assert all(events.index((n,'fim')) < join for n in NAMES)


@pytest.mark.parametrize('tasks', [[], ['supply'], ['supply', 'supply', 'logistics'], ['unknown']])
def test_invalid_supervisor_plan_fails_before_fanout(demo, tasks):
    def change(role, value, context):
        if role == 'supervisor':
            value['tasks'] = [dict(specialist=n, question='Investigar') for n in tasks]
    llm = ScriptedInterpreter(change)
    state = run_workflow(*demo, llm=llm)
    assert state.status == 'blocked' and state.finance is None
    assert [role for role, _ in llm.calls] == ['supervisor']


@pytest.mark.parametrize('field,value', [('estimated_cost_brl','1'), ('avoided_penalty_brl','0'),
                                       ('customer_delay_days',0), ('approval_required',False),
                                       ('confidence',0.99), ('incident_id','OTHER')])
def test_generated_recommendation_cannot_change_facts(demo, field, value):
    def change(role, data, context):
        if role == 'recommendation':
            data['recommendation'][field] = value
    state = run_workflow(*demo, llm=ScriptedInterpreter(change))
    assert state.status == 'blocked'
    assert state.recommendation is None and state.approval is None


def test_llm_cannot_select_ineligible_scenario(demo):
    def change(role, data, context):
        if role == 'recommendation':
            data['scenario_id'] = 'C'
    state = run_workflow(*demo, llm=ScriptedInterpreter(change))
    assert state.status == 'blocked' and state.approval is None


def test_llm_can_choose_different_eligible_tradeoff(demo):
    def change(role, data, context):
        if role == 'recommendation':
            data.update(scenario_id='B', recommendation=context['templates']['B'],
                        rationale='Custa mais, mas evita todos os atrasos.')
    state = run_workflow(*demo, llm=ScriptedInterpreter(change))
    assert state.status == 'awaiting_approval'
    assert state.review.selected_scenario == 'B'
    assert state.recommendation.customer_delay_days == 0
    assert state.recommendation.estimated_cost_brl == 20250


def test_llm_cannot_remove_risks_or_change_canonical_action(demo):
    def change(role, data, context):
        if role == 'recommendation':
            data['recommendation'].update(risks=[], recommended_action='Compra já executada')
    state = run_workflow(*demo, llm=ScriptedInterpreter(change))
    assert state.recommendation.risks
    assert state.recommendation.recommended_action.startswith('Cenário D:')
    assert state.approval.actions_executed is False


@pytest.mark.parametrize('failed_role', ['supervisor', *NAMES, 'challenger', 'recommendation'])
def test_api_failure_has_no_silent_mock_fallback(demo, failed_role):
    def change(role, value, context):
        if role == failed_role:
            raise ValueError('OpenAI: tempo limite')
    state = run_workflow(*demo, llm=ScriptedInterpreter(change))
    assert state.status == 'blocked' and state.approval is None
    assert state.llm_mode == 'openai'
    if failed_role in NAMES:
        assert state.finance is None
        assert getattr(state, failed_role).error


def test_bad_evidence_reference_blocks_join(demo):
    def change(role, data, context):
        if role == 'supply':
            data['evidence_refs'] = ['invented']
    state = run_workflow(*demo, llm=ScriptedInterpreter(change))
    assert state.investigation is None and state.status == 'blocked'


@pytest.mark.parametrize('mode', ['mock', 'openai'])
def test_compact_decisions_view(demo, mode):
    text, blocked = show(*demo, 'llm-decisions', llm=ScriptedInterpreter() if mode=='openai' else None)
    assert not blocked
    assert len(text.splitlines()) <= 20 and max(map(len,text.splitlines())) <= 96
    assert mode in text and 'actions_executed=false' in text
    assert 'LLMs interpretam e julgam.' in text


def test_key_file_and_env_precedence_without_secret_repr(tmp_path, monkeypatch):
    monkeypatch.setenv('LLM_MODE','openai')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('OPENAI_API_KEY_FILE', raising=False)
    (tmp_path/'.keys').write_text('OPENAI_API_KEY=sk-test-local\n')
    settings = Settings.load(tmp_path)
    assert settings.api_key == 'sk-test-local'
    assert 'sk-test-local' not in repr(settings)
    monkeypatch.setenv('OPENAI_API_KEY','sk-test-env')
    monkeypatch.setenv('OPENAI_MODEL','another-model')
    assert Settings.load(tmp_path).api_key == 'sk-test-env'
    assert Settings.load(tmp_path).model == 'another-model'


def test_mock_does_not_read_secret_file(tmp_path, monkeypatch):
    monkeypatch.setenv('LLM_MODE','mock')
    monkeypatch.setenv('OPENAI_API_KEY_FILE','/no-such-key')
    assert Settings.load(tmp_path).interpreter() is None


def test_missing_key_cli_is_clear_and_safe(tmp_path):
    env = dict(os.environ, LLM_MODE='openai', OPENAI_API_KEY='', OPENAI_API_KEY_FILE=str(tmp_path/'absent'))
    result = subprocess.run([sys.executable,'-m','control_tower.main','run','INCIDENT-001','--root',str(tmp_path)],
                            env=env, text=True,capture_output=True)
    assert result.returncode == 2 and 'requer OPENAI_API_KEY' in result.stderr
    assert 'Traceback' not in result.stderr and not result.stdout


@pytest.mark.parametrize('kind', ['401','429','timeout','refusal','incomplete','invalid'])
def test_adapter_sanitizes_errors_and_rejects_incomplete(kind):
    def parse(**kwargs):
        request = httpx.Request('POST','https://api.openai.com/v1/responses')
        if kind in ('401','429'):
            error = AuthenticationError if kind=='401' else RateLimitError
            raise error('secret-must-not-appear', response=httpx.Response(int(kind),request=request),body=None)
        if kind=='timeout':
            raise APITimeoutError(request=request)
        if kind=='invalid':
            return SimpleNamespace(status='completed',output_parsed=SimpleNamespace(model_dump=lambda: {'unexpected':'secret-must-not-appear'}))
        return SimpleNamespace(status='incomplete' if kind=='incomplete' else 'completed', output_parsed=None)
    client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    adapter = OpenAIInterpreter('sk-test-only','test-model',client=client)
    with pytest.raises(ValueError) as error:
        adapter.parse('supervisor',InvestigationPlan,{})
    assert 'secret-must-not-appear' not in str(error.value)


def test_adapter_uses_pydantic_no_storage_and_no_reasoning_output():
    captured = {}
    plan = InvestigationPlan(interpretation='Investigar', tasks=[dict(specialist='supply',question='Estoque?')])
    def parse(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(status='completed',output_parsed=plan)
    adapter = OpenAIInterpreter('sk-test','chosen-model',client=SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    assert adapter.parse('supervisor',InvestigationPlan,{'incident':'fixture'}) == plan
    assert captured['text_format'] is InvestigationPlan
    assert captured['store'] is False and captured['model'] == 'chosen-model'
    assert 'reasoning' not in captured and 'api_key' not in captured


def test_sdk_parse_contract_over_http_without_network():
    """Exercita o SDK real, incluindo schema strict e parse, com transporte local."""
    from openai import OpenAI
    from control_tower.models import Recommendation
    plan = InvestigationPlan(interpretation='Investigar',tasks=[dict(specialist=n,question='Evidência?') for n in NAMES])
    synthesis = SpecialistSynthesis(summary='Dados recebidos',evidence_refs=['local'],uncertainty='Confirmar prazo')
    judgment = ChallengerJudgment(summary='Há incerteza',findings=[dict(scenario_id='all',category='assumption',message='Prazo precisa de confirmação')])
    decision = RecommendationDecision(scenario_id='D',rationale='Custo menor, atraso residual',recommendation=LLMRecommendation(
        incident_id='INCIDENT-001',severity='high',recommended_action='Cenário D',estimated_cost_brl='12500',
        avoided_penalty_brl='16000',customer_delay_days=3,confidence=0.65,risks=['Confirmar prazo']))
    for role, value in [('supervisor',plan), ('supply',synthesis),('challenger',judgment),('recommendation',decision)]:
        def handle(request):
            body = json.loads(request.content)
            assert body['text']['format']['type'] == 'json_schema'
            assert body['text']['format']['strict'] is True
            assert body['text']['format']['schema']['additionalProperties'] is False
            assert body['store'] is False
            return httpx.Response(200, json={'id':'resp_test','object':'response','created_at':0,
                'status':'completed','model':'test', 'output':[{'id':'msg_test','type':'message','role':'assistant',
                'status':'completed','content':[{'type':'output_text','text':value.model_dump_json(),'annotations':[]}]}]})
        client = OpenAI(api_key='sk-test', http_client=httpx.Client(transport=httpx.MockTransport(handle)))
        try:
            assert OpenAIInterpreter('sk-test','test',client=client).parse(role,type(value),{}) == value
        finally:
            client.close()


def test_classroom_snippets_are_current_and_short():
    snippets=json.loads((ROOT/'docs/course/classroom/snippets.json').read_text())
    for snippet in snippets:
        assert 10 <= snippet['end']-snippet['start']+1 <= 30
        lines=(ROOT/snippet['path']).read_text().splitlines()
        assert snippet['code'] == '\n'.join(lines[snippet['start']-1:snippet['end']])


def test_runbook_keeps_240_minutes_with_comparison():
    import re
    text=(ROOT/'docs/course/lesson-01-runbook.md').read_text()
    assert sum(map(int,re.findall(r'\| (\d+) min \|',text))) == 240
    assert '10B. Mock vs OpenAI' in text


@pytest.mark.parametrize('view', ['summary','state','specialists','coordination'])
def test_openai_early_views_do_not_call_later_judgments(demo, view):
    llm=ScriptedInterpreter()
    text, blocked=show(*demo,view,llm=llm)
    assert not blocked
    assert {role for role, _ in llm.calls} == {'supervisor', *NAMES}
    assert 'awaiting_approval' not in text and '12.500' not in text


def test_openai_sequential_control_preserves_business_result(demo):
    assert run_workflow(*demo,llm=ScriptedInterpreter(),sequential=True) == run_workflow(*demo,llm=ScriptedInterpreter())


def test_raw_key_file_is_accepted_without_printing(tmp_path,monkeypatch):
    monkeypatch.setenv('LLM_MODE','openai')
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    monkeypatch.setenv('OPENAI_API_KEY_FILE','custom.keys')
    (tmp_path/'custom.keys').write_text('sk-test-placeholder')
    assert Settings.load(tmp_path).api_key == 'sk-test-placeholder'


@pytest.mark.parametrize('value', ['-1','1.001','not-money'])
def test_transport_schema_does_not_weaken_money_validation(value):
    with pytest.raises(ValidationError):
        LLMRecommendation(incident_id='INCIDENT-001',severity='high',recommended_action='Cenário D',
                          estimated_cost_brl=value,avoided_penalty_brl='0',customer_delay_days=0,
                          confidence=0.65,risks=[])
