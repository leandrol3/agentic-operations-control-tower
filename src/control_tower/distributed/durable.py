"""Contratos aditivos: o baseline local continua usando os contratos do start."""
from typing import Annotated, Literal
from pydantic import Field, model_validator
from ..models import Contract, Recommendation
from ..graph.state import Approval
from .models import Execution, Text
from .events import ExecutionEvent


class FinalResult(Contract):
    reference_case_id: Literal['INCIDENT-001'] = 'INCIDENT-001'
    mode: Literal['mock', 'openai', 'degraded'] = 'mock'
    outcome: Literal['recommendation', 'degraded_recommendation', 'human_review_required'] = 'recommendation'
    model: Text | None = None
    reason: Text | None = None
    recommendation: Recommendation | None = None
    approval: Approval

    @model_validator(mode='after')
    def explicit_outcome(self):
        if (self.outcome == 'human_review_required') != (self.recommendation is None):
            raise ValueError('Human review não tem recomendação; demais resultados exigem recomendação')
        if self.outcome == 'degraded_recommendation' and (self.mode != 'degraded' or not self.reason):
            raise ValueError('Degradação exige modo explícito e motivo')
        if self.mode == 'degraded' and self.outcome != 'degraded_recommendation':
            raise ValueError('Modo degraded exige recomendação degradada')
        if self.outcome == 'human_review_required' and not self.reason:
            raise ValueError('Escalation exige motivo')
        return self


class DurableExecution(Execution):
    idempotency_key: Text
    result: FinalResult | None = None
    llm_mode: Literal['mock', 'openai'] = 'mock'
    duration_ms: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None = None

    @model_validator(mode='after')
    def result_matches_status(self):
        if (self.status == 'completed') != (self.result is not None):
            raise ValueError('Somente completed exige resultado final')
        return self


class DurableEvent(ExecutionEvent):
    event_type: Text
    detail: Text | None = None

    @model_validator(mode='after')
    def coherent_status(self):
        expected = {'execution.queued': 'queued', 'execution.started': 'running',
                    'execution.completed': 'completed', 'execution.failed': 'failed',
                    'execution.retry': 'queued', 'execution.interrupted': 'running'}
        llm_events = {'llm.requested', 'llm.failed', 'llm.retry', 'llm.completed',
                      'llm.fallback_activated', 'llm.degraded', 'llm.escalated'}
        if self.event_type not in expected and self.event_type not in llm_events and not self.event_type.endswith(('.started', '.completed', '.failed')):
            raise ValueError('Tipo de evento desconhecido')
        if self.status != expected.get(self.event_type, 'running'):
            raise ValueError('Evento e estado incompatíveis')
        return self


class TaskOptions(Contract):
    demo_delay_ms: Annotated[int, Field(ge=0, le=30000)] = 0
    fail_specialist: Literal['supply', 'production', 'logistics'] | None = None
    fail_always: bool = False

    llm_mode: Literal['mock', 'openai'] = 'mock'
    llm_model: Text = 'gpt-4.1-mini'
    llm_failure: Literal['none', 'timeout'] = 'none'
    fallback: Literal['human', 'deterministic_reference'] = 'human'

    @model_validator(mode='after')
    def separate_demos(self):
        if self.llm_mode == 'mock' and (self.llm_failure != 'none' or self.fallback != 'human'):
            raise ValueError('Demo LLM failure/fallback exige LLM_MODE=openai')
        if self.llm_mode == 'openai' and (self.fail_specialist or self.fail_always or self.demo_delay_ms):
            raise ValueError('Demos de falha de especialista/delay/worker loss ficam em mock')
        return self
