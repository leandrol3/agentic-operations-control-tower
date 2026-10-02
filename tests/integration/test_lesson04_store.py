"""Durable usage -> economics with real PostgreSQL, scripted provider (no OpenAI)."""
import os
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4
import pytest
pytest.importorskip('psycopg')
pytest.importorskip('pydantic_settings')
pytest.importorskip('celery')
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from control_tower.runtime.store import CorrelatedStore
from control_tower.distributed.config import database_url
from control_tower.distributed.durable import TaskOptions, FinalResult
from control_tower.distributed.incidents import generate_incidents
from control_tower.distributed.llm_runtime import ResilientInterpreter
from control_tower.telemetry.context import ExecutionContext, bind_context
from control_tower.control_plane.economics import assess_economics, PricingConfig
from control_tower.control_plane.quality import assess_quality
from control_tower.graph.state import Approval
from control_tower.settings import Settings

pytestmark=pytest.mark.skipif(os.getenv('LESSON04_INTEGRATION')!='1',reason='Requires PostgreSQL and LESSON04_INTEGRATION=1')


def test_provider_usage_survives_new_store_and_model_configuration():
    dsn=database_url();schema='test_l04_'+uuid4().hex
    with psycopg.connect(dsn,autocommit=True) as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    isolated=make_conninfo(dsn,options=f'-c search_path={schema}')
    try:
        store=CorrelatedStore(isolated);store.initialize()
        envelope=generate_incidents(1)[0];key='fixture-'+uuid4().hex
        options=TaskOptions(llm_mode='openai',llm_model='fixture-model')
        with bind_context(ExecutionContext()): execution,_=store.claim(envelope,key,options)
        response=SimpleNamespace(usage=SimpleNamespace(input_tokens=300,output_tokens=50))
        client=SimpleNamespace(responses=SimpleNamespace(parse=MagicMock(return_value=response)))
        with store.acquire(execution.execution_id,key,envelope.model_dump(mode='json')) as session:
            assert session.begin('test-worker')
            interpreter=ResilientInterpreter(Settings('openai','fixture-model','test-only'),session,options,client=client)
            interpreter.request('supervisor',model='fixture-model')
            session.event('llm.escalated',detail='test-only human outcome')
            session.finish(FinalResult(mode='openai',model='fixture-model',outcome='human_review_required',
                reason='test-only',approval=Approval(authority='operations_manager')))
        # Reopen, no in-memory interpreter or telemetry dependency.
        reopened=CorrelatedStore(isolated)
        persisted=reopened.get(execution.execution_id)
        history=reopened.events(execution.execution_id)
        model=reopened.options_for(execution.execution_id).llm_model
        pricing=PricingConfig(version='fixture-not-real-price',models={'fixture-model':{
            'input_per_million':'2','output_per_million':'8','currency':'USD'}})
        result=assess_economics(persisted,history,model,pricing)
        assert result.input_tokens==300 and result.output_tokens==50
        assert result.estimated_llm_cost==Decimal('0.001')
        assert result.model=='fixture-model' and result.llm_calls==1
        assert assess_quality(persisted,history).approval_status=='pending'
        assert all('test-only' not in str(e.model_dump()) for e in history if e.event_type=='llm.completed')
    finally:
        with psycopg.connect(dsn,autocommit=True) as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
