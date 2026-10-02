"""Bounded durable snapshots. No graph invocation, telemetry backend or provider calls."""
from datetime import datetime
from pydantic import model_validator
from ..models import Contract
from ..distributed.durable import DurableExecution, DurableEvent, TaskOptions
from .quality import assess_quality
from .economics import assess_economics


class ExecutionSample(Contract):
    execution: DurableExecution
    events: tuple[DurableEvent, ...]
    options: TaskOptions
    created_at: datetime

    @model_validator(mode='after')
    def consistent(self):
        if self.execution.status not in ('completed', 'failed'):
            raise ValueError('Only terminal executions are comparable')
        if any(e.execution_id != self.execution.execution_id for e in self.events):
            raise ValueError('Event belongs to a different execution')
        if self.options.llm_mode != self.execution.llm_mode:
            raise ValueError('Execution mode differs from persisted options')
        return self


def complete_history(sample):
    events = sample.events
    return (bool(events) and [e.sequence for e in events] == list(range(1, len(events)+1))
            and events[0].event_type == 'execution.queued'
            and events[-1].event_type == 'execution.' + sample.execution.status)


def collect_stage(sample, agent_id, pricing):
    """Last attempt's last stage outcome, never infer success from workflow completed.

    Node completed proves technical completion only. Failed provider calls can leave no
    node terminal event; absence remains unknown, even when the workflow terminates.
    """
    events = sample.events
    history_ok = complete_history(sample)
    terminals = [e for e in events if e.agent_id == agent_id and e.attempt == sample.execution.attempt
                 and e.event_type in (agent_id+'.completed', agent_id+'.failed')]
    last = terminals[-1] if terminals and history_ok else None
    success = None if last is None else last.event_type.endswith('.completed')
    duration = last.duration_ms if last else None
    quality = assess_quality(sample.execution, events)
    # Only usage explicitly tagged with this role; do not allocate whole workflow cost to agents.
    role_events = [e for e in events if e.agent_id == agent_id and e.event_type.startswith('llm.')]
    economics = assess_economics(sample.execution, role_events, sample.options.llm_model, pricing)
    cost = economics.estimated_llm_cost if (
        history_ok and economics.usage_coverage == 'recorded_calls' and economics.cost_currency == 'USD') else None
    return {'success': success, 'latency': duration, 'cost': cost,
            'degraded': (sample.execution.result.outcome != 'recommendation')
                if history_ok and sample.execution.result else None,
            'quality': quality, 'economics': economics}
