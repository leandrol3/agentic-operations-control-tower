"""Small refinement contracts: no provider calls."""
from datetime import date, datetime, timezone
from decimal import Decimal
import os
from pathlib import Path
import subprocess
from uuid import uuid4
import pytest
pytest.importorskip('mcp')
pytest.importorskip('celery')
pytest.importorskip('psycopg')
from fastapi.testclient import TestClient
from control_tower.api.app import create_app
from control_tower.control_plane.economics import load_pricing, assess_economics
from test_lesson04 import settings, service, execution, final, events

ROOT=Path(__file__).resolve().parents[1]


def test_empty_incident_list(settings,service):
    store,enqueue,_=service;store.list_incidents.return_value=[]
    with TestClient(create_app(settings,store,enqueue)) as client:
        response=client.get('/incidents')
    assert response.status_code==200 and response.json()==[]
    store.list_incidents.assert_called_once_with(status=None,limit=20)
    enqueue.assert_not_called()


@pytest.mark.parametrize('status',['queued','running','completed','failed'])
def test_incident_summary_contract_and_filter(settings,service,status):
    store,enqueue,_=service
    now=datetime.now(timezone.utc)
    row=dict(incident_id='I-001',execution_id=uuid4(),status=status,
        outcome='human_review_required' if status=='completed' else None,
        approval_status='pending' if status=='completed' else None,
        created_at=now,completed_at=now if status in ('completed','failed') else None)
    store.list_incidents.return_value=[row]
    with TestClient(create_app(settings,store,enqueue)) as client:
        response=client.get('/incidents',params={'status':status,'limit':10})
    assert response.status_code==200
    item=response.json()[0]
    assert set(item)==set(row)|{'version'}
    assert item['version'] is None and item['status']==status
    assert item['outcome']==row['outcome'] and item['approval_status']==row['approval_status']
    store.list_incidents.assert_called_once_with(status=status,limit=10)


@pytest.mark.parametrize('query',['limit=0','limit=101','limit=abc','status=invalid'])
def test_incident_invalid_filter_never_reads_store(settings,service,query):
    store,enqueue,_=service
    with TestClient(create_app(settings,store,enqueue)) as client:
        assert client.get('/incidents?'+query).status_code==422
    store.list_incidents.assert_not_called()


def test_incident_store_failure_is_sanitized(settings,service):
    store,enqueue,_=service;store.list_incidents.side_effect=RuntimeError('SECRET DSN')
    with TestClient(create_app(settings,store,enqueue)) as client:
        response=client.get('/incidents')
    assert response.status_code==503 and 'SECRET' not in response.text


@pytest.fixture
def dated_pricing(monkeypatch):
    monkeypatch.setenv('CONTROL_TOWER_PRICING_FILE',str(ROOT/'config/lesson04-pricing.json'))
    return load_pricing()


def test_dated_public_pricing(dated_pricing):
    p=dated_pricing
    assert p.version=='openai-public-pricing-2026-10-02'
    assert p.source=='OpenAI public API pricing' and p.reference_date==date(2026,10,2)
    rate=p.models['gpt-4.1-mini']
    assert rate.input_per_million==Decimal('0.40')
    assert rate.cached_input_per_million==Decimal('0.10')
    assert rate.output_per_million==Decimal('1.60') and rate.currency=='USD'
    assert all(isinstance(v,Decimal) for v in (rate.input_per_million,rate.cached_input_per_million,rate.output_per_million))


def test_estimate_uses_standard_input_when_cached_usage_absent(execution,dated_pricing):
    e=execution.model_copy(update={'llm_mode':'openai'})
    history=events(e,'llm.requested','llm.completed')
    history[1]=history[1].model_copy(update={'input_tokens':10117,'output_tokens':831})
    result=assess_economics(e,history,'gpt-4.1-mini',dated_pricing)
    assert result.estimated_llm_cost==Decimal('0.0053764')
    assert isinstance(result.estimated_llm_cost,Decimal)
    assert result.reference_date==date(2026,10,2)
    assert result.pricing_version==dated_pricing.version
    assert not result.cached_input_discount_applied and result.cost_unavailable_reason is None
    assert result.estimated_execution_cost is None


@pytest.mark.parametrize('mode,model,reason',[('mock','gpt-4.1-mini','mock_no_usage'),
    ('openai','unknown-model','model_not_priced'),('openai',None,'model_unavailable')])
def test_no_invented_cost_with_dated_table(execution,dated_pricing,mode,model,reason):
    e=execution.model_copy(update={'llm_mode':mode})
    history=events(e,'llm.requested','llm.completed')
    history[1]=history[1].model_copy(update={'input_tokens':100,'output_tokens':20})
    result=assess_economics(e,history,model,dated_pricing)
    assert result.estimated_llm_cost is None and result.cost_unavailable_reason==reason
    if mode=='mock': assert result.input_tokens is None and result.output_tokens is None


def test_launcher_is_independent_of_cwd_and_preserves_stdio(tmp_path):
    fake=tmp_path/'docker';fake.write_text('#!/bin/sh\nprintf "%s\\n" "$PWD" "$@"\n')
    fake.chmod(0o755)
    result=subprocess.run(['/bin/bash',str(ROOT/'scripts/start_lesson04_mcp.sh')],
        cwd=tmp_path,env=os.environ|{'DOCKER_BIN':str(fake)},capture_output=True,text=True,check=True)
    lines=result.stdout.splitlines()
    assert lines[0]==str(ROOT)
    assert '-T' in lines and '-t' not in lines
    assert lines[-3:]==['python','-m','control_tower.mcp.server']
    assert result.stderr==''
