"""Real durable events -> read-only Control Plane, isolated PostgreSQL schema."""
import os
from pathlib import Path
from decimal import Decimal
from uuid import uuid4
import pytest
pytest.importorskip('psycopg')
pytest.importorskip('celery')
pytest.importorskip('mcp')
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from control_tower.runtime.store import CorrelatedStore
from control_tower.distributed.config import database_url
from control_tower.distributed.incidents import generate_incidents
from control_tower.distributed.durable import TaskOptions, FinalResult
from control_tower.telemetry.context import ExecutionContext, bind_context
from control_tower.tools import Tools
from control_tower.graph.workflow import run_workflow
from control_tower.control_plane.configuration import ControlPlaneConfig
from control_tower.control_plane.economics import PricingConfig
from control_tower.control_plane.service import ControlPlane

pytestmark=pytest.mark.skipif(os.getenv('LESSON04_INTEGRATION')!='1',reason='Requires PostgreSQL and LESSON04_INTEGRATION=1')
ROOT=Path(__file__).resolve().parents[2]


def test_durable_control_plane_is_bounded_and_read_only():
    dsn=database_url();schema='test_l04_cp_'+uuid4().hex
    with psycopg.connect(dsn,autocommit=True) as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    try:
        store=CorrelatedStore(make_conninfo(dsn,options=f'-c search_path={schema}'));store.initialize()
        config=ControlPlaneConfig.model_validate_json((ROOT/'config/lesson04-control-plane.json').read_text())
        pricing=PricingConfig.model_validate_json((ROOT/'config/lesson04-pricing.json').read_text())
        plane=ControlPlane(store,config=config,pricing=pricing)
        assert plane.evaluate(agent_id='logistics')[0].goals[0].status=='unknown'
        tools=Tools(ROOT);incident=tools.load_incident(ROOT/'incidents/incident_001.json')
        for index in range(4):
            envelope=generate_incidents(1)[0];key='cp-'+str(index)
            with bind_context(ExecutionContext()):
                execution,new=store.claim(envelope,key,TaskOptions());assert new
                duplicate,new=store.claim(envelope,key,TaskOptions());assert not new
                assert duplicate.execution_id==execution.execution_id
            with store.acquire(execution.execution_id,key,envelope.model_dump(mode='json')) as session:
                session.begin('integration-worker')
                state=run_workflow(tools,incident,observer=session.step,fail_specialist='logistics' if index==3 else None)
                if index==3: session.fail('controlled specialist failure',retry=False)
                else: session.finish(FinalResult(recommendation=state.recommendation,approval=state.approval),duration_ms=100)
        assert len(store.control_plane_samples(limit=2))==2
        assert store.control_plane_samples(mode='openai')==[]
        with store.connect() as conn:
            before=conn.execute('SELECT document,options FROM ct_executions ORDER BY execution_id').fetchall()
            event_count=conn.execute('SELECT count(*) AS n FROM ct_events').fetchone()['n']
        v=plane.evaluate(agent_id='logistics')[0]
        assert v.sample_count==3 and v.goals[0].status=='off_target'
        assert round(v.goals[0].actual,2)==Decimal('66.67')
        assert v.economics.observed is None
        assert v.recommendation.action=='review' and v.recommendation.requires_human_approval
        assert v.registry.lifecycle_state=='active' and v.evidence_source=='durable_history'
        assert len({e for e in v.goals[0].evidence.execution_ids})==3
        with store.connect() as conn:
            assert conn.execute('SELECT document,options FROM ct_executions ORDER BY execution_id').fetchall()==before
            assert conn.execute('SELECT count(*) AS n FROM ct_events').fetchone()['n']==event_count
    finally:
        with psycopg.connect(dsn,autocommit=True) as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
