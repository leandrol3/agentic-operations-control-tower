"""Explicit synthetic signals for offline teaching. Never used by API or persisted."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from ..distributed.durable import DurableExecution, DurableEvent, FinalResult, TaskOptions
from ..graph.state import Approval
from ..models import Recommendation
from .collection import ExecutionSample


def fixture_samples(name, path=Path('fixtures/lesson04/control-plane.json')):
    document = json.loads(path.read_text())
    if document['source'] != 'didactic_fixture':
        raise ValueError('Fixture provenance required')
    spec = document['scenarios'][name]
    rows = []
    for index in range(6):
        current = index >= 3
        failed = index % 3 < spec['current_failures' if current else 'previous_failures']
        tokens = spec['current_input_tokens' if current else 'previous_input_tokens']
        timestamp = datetime(2026,10,2,tzinfo=timezone.utc)+timedelta(minutes=index)
        uid = uuid5(NAMESPACE_URL, f'lesson04-fixture/{name}/{index}')
        events = []
        def event(kind, role='worker', **values):
            status = {'execution.queued':'queued','execution.completed':'completed','execution.failed':'failed'}.get(kind,'running')
            events.append(DurableEvent(execution_id=uid,incident_id='FIXTURE-ONLY',event_type=kind,agent_id=role,
                timestamp=timestamp+timedelta(milliseconds=len(events)),sequence=len(events)+1,attempt=1,status=status,**values))
        event('execution.queued','producer');event('execution.started')
        degraded = spec['degraded'] and current
        if degraded:
            event('llm.requested','supervisor')
            event('llm.failed','supervisor')
            event('llm.retry','supervisor')
            event('llm.requested','supervisor')
            event('llm.failed','supervisor')
            event('llm.fallback_activated','supervisor')
        for role in ('supervisor','supply','production','logistics','finance','challenger','recommendation'):
            event(role+'.started',role)
            if role != 'finance' and not degraded:
                event('llm.requested',role)
                event('llm.completed',role,input_tokens=tokens if role=='logistics' else 1000,output_tokens=100)
            event(role+('.failed' if role=='logistics' and failed else '.completed'),role,
                duration_ms=spec['latency_ms'] if role=='logistics' and current else 100)
            if role=='logistics' and failed:
                break
        result = None if failed else FinalResult(mode='degraded' if degraded else 'openai',
            outcome='degraded_recommendation' if degraded else 'recommendation',
            reason='synthetic_fixture' if degraded else None,
            recommendation=Recommendation(incident_id='FIXTURE-ONLY',severity='high',
                recommended_action='Synthetic proposal, not executed',estimated_cost_brl='12500.00',
                avoided_penalty_brl='0',customer_delay_days=0,confidence=0.65,risks=['Fixture only']),
            approval=Approval(authority='manager'))
        event('execution.failed' if failed else 'execution.completed')
        execution = DurableExecution(execution_id=uid,incident_id='FIXTURE-ONLY',idempotency_key=str(uid),
            llm_mode='openai',attempt=1,status='failed' if failed else 'completed',started_at=timestamp,
            completed_at=events[-1].timestamp,result=result,duration_ms=1000,worker_id='fixture-worker',
            current_step='failed' if failed else 'awaiting_approval',error='synthetic_stage_failure' if failed else None)
        rows.append(ExecutionSample(execution=execution,events=tuple(events),created_at=timestamp,
            options=TaskOptions(llm_mode='openai',llm_model='gpt-4.1-mini')))
    return rows
