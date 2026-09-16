"""Provider substituído em todos os testes; qualquer conexão de rede é erro."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
import socket
import httpx
import pytest
from openai import APITimeoutError, AuthenticationError, RateLimitError
pytest.importorskip('celery', reason='Instale a Aula 2 com: uv sync --extra lesson02')
pytest.importorskip('psycopg', reason='Instale a Aula 2 com: uv sync --extra lesson02')

from control_tower.distributed import llm_runtime, tasks
from control_tower.distributed.config import visibility_timeout
from control_tower.distributed.durable import TaskOptions, FinalResult
from control_tower.graph.state import Approval
from control_tower.llm import SpecialistSynthesis
from control_tower.settings import Settings
from control_tower.tools import Tools
from control_tower.distributed.incidents import generate_incidents
from test_llm import ScriptedInterpreter

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a,**k):
        raise AssertionError('Testes unitários não podem acessar provider/rede')
    monkeypatch.setattr(socket.socket,'connect',forbidden)


def runtime(side_effect=None, failure='none'):
    parsed=SpecialistSynthesis(summary='Síntese',evidence_refs=['stock'],uncertainty='Confirmar')
    response=SimpleNamespace(status='completed',output_parsed=parsed,usage=SimpleNamespace(input_tokens=12,output_tokens=8))
    client=SimpleNamespace(responses=SimpleNamespace(parse=MagicMock(side_effect=side_effect,return_value=response)))
    session=MagicMock(); sleep=MagicMock()
    interpreter=llm_runtime.ResilientInterpreter(Settings('openai','gpt-4.1-mini','unit-test'),session,
        TaskOptions(llm_mode='openai',llm_failure=failure),client=client,sleep=sleep)
    return interpreter,client,session,sleep,response


def kinds(session):return [c.args[0] for c in session.event.call_args_list]


def test_provider_success_usage_without_prompts_in_events():
    interpreter,client,session,sleep,_=runtime()
    assert interpreter.parse('supply',SpecialistSynthesis,{'private_context':'not logged'}).summary=='Síntese'
    assert kinds(session)==['llm.requested','llm.completed']
    assert session.event.call_args.kwargs['input_tokens']==12
    assert 'private_context' not in str(session.event.call_args_list)
    sleep.assert_not_called()


def test_transient_retry_then_success():
    interpreter,client,session,sleep,response=runtime()
    client.responses.parse.side_effect=[APITimeoutError(request=httpx.Request('POST','https://example.test')),response]
    interpreter.parse('supply',SpecialistSynthesis,{})
    assert kinds(session)==['llm.requested','llm.failed','llm.retry','llm.requested','llm.completed']
    sleep.assert_called_once_with(1)


@pytest.mark.parametrize('status,error_cls,transient,calls',[(401,AuthenticationError,False,1),(429,RateLimitError,True,2)])
def test_status_classification(status,error_cls,transient,calls):
    response=httpx.Response(status,request=httpx.Request('POST','https://example.test'))
    error=error_cls('SECRET BODY NOT LOGGED',response=response,body=None)
    interpreter,client,session,sleep,_=runtime(side_effect=error)
    with pytest.raises(llm_runtime.ProviderUnavailable) as caught:
        interpreter.parse('supply',SpecialistSynthesis,{})
    assert caught.value.transient is transient and client.responses.parse.call_count==calls
    assert 'SECRET' not in str(session.event.call_args_list)


def test_simulated_timeout_never_calls_provider():
    interpreter,client,session,sleep,_=runtime(failure='timeout')
    with pytest.raises(llm_runtime.ProviderUnavailable,match='simulated_timeout'):
        interpreter.parse('supervisor',SpecialistSynthesis,{})
    client.responses.parse.assert_not_called()
    assert kinds(session).count('llm.requested')==2 and kinds(session).count('llm.retry')==1


def test_bad_structured_output_is_nontransient():
    interpreter,client,session,sleep,response=runtime()
    response.output_parsed=None
    with pytest.raises(llm_runtime.ProviderUnavailable) as caught:
        interpreter.parse('supply',SpecialistSynthesis,{})
    assert not caught.value.transient and 'llm.retry' not in kinds(session)


def test_missing_key_fails_clearly(monkeypatch,tmp_path):
    monkeypatch.setenv('LLM_MODE','openai');monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    monkeypatch.setenv('OPENAI_API_KEY_FILE',str(tmp_path/'absent'))
    monkeypatch.setattr(llm_runtime,'project_root',lambda:tmp_path)
    with pytest.raises(ValueError,match='OPENAI_API_KEY'):
        llm_runtime.settings_for(TaskOptions(llm_mode='openai'))


def test_mock_never_reads_key_or_constructs_provider(monkeypatch):
    monkeypatch.setattr(Settings,'load',MagicMock(side_effect=AssertionError('Não ler chave em mock')))
    assert llm_runtime.settings_for(TaskOptions()).mode=='mock'


@pytest.mark.parametrize('options',[{'llm_failure':'timeout'}, {'fallback':'deterministic_reference'},
 {'llm_mode':'openai','fail_specialist':'logistics'}, {'llm_mode':'openai','demo_delay_ms':10000}])
def test_demos_cannot_mix_paid_provider_and_mock_failures(options):
    with pytest.raises(ValueError):TaskOptions(**options)


def test_visibility_profiles(monkeypatch):
    monkeypatch.delenv('LESSON02_VISIBILITY_TIMEOUT',raising=False)
    monkeypatch.setenv('LLM_MODE','mock');assert visibility_timeout()==60
    monkeypatch.setenv('LLM_MODE','openai');assert visibility_timeout()==900


def execute_llm(monkeypatch, fallback, transient=True, safe=True, valid=True):
    tools=Tools(ROOT);incident=tools.load_incident(ROOT/'incidents/incident_001.json')
    session=MagicMock()
    class Broken:
        model='test'
        def parse(self,*args):raise llm_runtime.ProviderUnavailable('timeout' if transient else 'http_401',transient)
    monkeypatch.setattr(llm_runtime,'ResilientInterpreter',lambda *a,**k:Broken())
    envelope=generate_incidents(1)[0].model_dump(mode='json')
    if not safe:envelope['payload']['reference_case_id']='OTHER'
    if not valid:
        original=tasks.run_workflow
        def block(*a,**k):
            if k.get('llm') is None:return SimpleNamespace(status='blocked')
            return original(*a,**k)
        monkeypatch.setattr(tasks,'run_workflow',block)
    result=tasks.llm_workflow(tools,incident,None,Settings('openai','test','unit'),session,
                             TaskOptions(llm_mode='openai',fallback=fallback),envelope)
    return result,kinds(session)


def test_explicit_degraded_reuses_graph_and_preserves_approval(monkeypatch):
    result,events=execute_llm(monkeypatch,'deterministic_reference')
    assert result.mode=='degraded' and result.outcome=='degraded_recommendation'
    assert result.reason=='timeout' and result.recommendation.approval_required
    assert result.approval.actions_executed is False
    assert events==['llm.fallback_activated','llm.degraded']


@pytest.mark.parametrize('fallback,transient,safe,valid',[
 ('human',True,True,True),('deterministic_reference',False,True,True),
 ('deterministic_reference',True,False,True),('deterministic_reference',True,True,False)])
def test_unsafe_or_nontransient_escalates_without_recommendation(monkeypatch,fallback,transient,safe,valid):
    result,events=execute_llm(monkeypatch,fallback,transient,safe,valid)
    assert result.outcome=='human_review_required' and result.recommendation is None
    assert events[-1]=='llm.escalated' and 'llm.degraded' not in events


def test_openai_mode_same_graph_with_scripted_provider(monkeypatch):
    monkeypatch.setattr(llm_runtime,'ResilientInterpreter',lambda *a:ScriptedInterpreter())
    tools=Tools(ROOT);incident=tools.load_incident(ROOT/'incidents/incident_001.json')
    result=tasks.llm_workflow(tools,incident,None,Settings('openai','test','unit'),MagicMock(),
                             TaskOptions(llm_mode='openai'),generate_incidents(1)[0].model_dump(mode='json'))
    assert result.mode=='openai' and result.outcome=='recommendation'
    baseline=tasks.run_workflow(tools,incident)
    for field in ('estimated_cost_brl','avoided_penalty_brl','customer_delay_days','approval_required'):
        assert getattr(result.recommendation,field)==getattr(baseline.recommendation,field)
    assert result.approval==baseline.approval


def test_human_result_cannot_claim_recommendation():
    with pytest.raises(ValueError):FinalResult(mode='openai',approval=Approval(authority='operations_manager'))


def test_complete_mock_task_offline_without_provider_or_key(monkeypatch):
    from contextlib import contextmanager
    session=MagicMock();session.options=TaskOptions().model_dump();session.attempts=1
    store=MagicMock()
    @contextmanager
    def acquire(*args):yield session
    store.acquire=acquire
    monkeypatch.setattr(tasks,'Store',lambda:store)
    monkeypatch.setattr(Settings,'load',MagicMock(side_effect=AssertionError('Credencial não deve ser lida')))
    monkeypatch.setattr(llm_runtime,'ResilientInterpreter',MagicMock(side_effect=AssertionError('Provider não deve ser criado')))
    tasks.execute.run(generate_incidents(1)[0].model_dump(mode='json'),'offline-execution','key')
    result=session.finish.call_args.args[0]
    assert result.mode=='mock' and result.outcome=='recommendation'
    assert not result.approval.actions_executed


def test_openai_short_visibility_rejected_before_request(monkeypatch):
    monkeypatch.setattr(Settings,'load',lambda root:Settings('openai','gpt-4.1-mini','unit'))
    monkeypatch.setenv('LESSON02_VISIBILITY_TIMEOUT','60')
    with pytest.raises(ValueError,match='VISIBILITY_TIMEOUT'):
        llm_runtime.settings_for(TaskOptions(llm_mode='openai'))
