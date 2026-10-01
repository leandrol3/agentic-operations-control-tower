"""Eventos tipados e coletor volátil; nenhuma telemetria ou persistência integrada."""
from datetime import datetime, timezone
from threading import Lock
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from ..models import Contract, Money
from .models import Execution, Milliseconds, Status, Text

EventType = Literal['execution_queued', 'execution_started', 'step_started', 'step_completed',
                    'step_failed', 'execution_completed', 'execution_failed']


class ExecutionEvent(Contract):
    execution_id: UUID
    incident_id: Text
    agent_id: Text
    event_type: EventType
    timestamp: AwareDatetime
    status: Status
    duration_ms: Milliseconds | None = None
    sequence: Annotated[int, Field(ge=1)]
    attempt: Annotated[int, Field(ge=1)] = 1
    input_tokens: Annotated[int, Field(ge=0)] | None = None
    output_tokens: Annotated[int, Field(ge=0)] | None = None
    estimated_cost: Money | None = None
    quality_score: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)] | None = None
    business_outcome: Text | None = None

    @model_validator(mode='after')
    def coherent_status(self):
        expected = {'execution_queued': 'queued', 'execution_started': 'running',
                    'execution_completed': 'completed', 'execution_failed': 'failed'}
        if self.status != expected.get(self.event_type, 'running'):
            raise ValueError('Evento e status da execução são incompatíveis')
        return self


class InMemoryEvents:
    """Uma instância por execução; lock protege callbacks paralelos dos especialistas."""
    def __init__(self):
        self._events: list[ExecutionEvent] = []
        self._lock = Lock()

    def emit(self, execution: Execution, agent_id: str, event_type: EventType,
             duration_ms: float | None = None):
        with self._lock:
            event = ExecutionEvent(
                execution_id=execution.execution_id, incident_id=execution.incident_id,
                agent_id=agent_id, event_type=event_type, timestamp=datetime.now(timezone.utc),
                status=execution.status, duration_ms=duration_ms, sequence=len(self._events) + 1,
                attempt=execution.attempt,
            )
            self._events.append(event)

    def snapshot(self) -> tuple[ExecutionEvent, ...]:
        with self._lock:
            return tuple(self._events)
