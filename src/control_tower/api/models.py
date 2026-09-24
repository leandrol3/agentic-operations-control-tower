"""Contratos públicos pequenos; não exportam documentos internos do store."""
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from ..distributed.incidents import IncidentEnvelope

Identifier = Annotated[str, Field(min_length=1, max_length=80, pattern=r'^[A-Za-z0-9._:-]+$')]
Status = Literal['queued', 'running', 'completed', 'failed']


class APIModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class IncidentSubmissionRequest(APIModel):
    incident_id: Identifier
    version: Identifier = 'v1'
    # Este serviço expõe somente o workload de referência que já existe na Aula 2.
    reference_case_id: Literal['INCIDENT-001'] = 'INCIDENT-001'
    demo_delay_ms: int = Field(default=0, ge=0, le=30000)
    llm_failure: Literal['none', 'timeout'] = 'none'
    fallback: Literal['human', 'deterministic_reference'] = 'human'

    def envelope(self) -> IncidentEnvelope:
        return IncidentEnvelope(incident_id=self.incident_id, incident_type='supplier_delay',
            plant='São Paulo', severity='high', created_at='2026-10-01T08:00:00Z',
            business_priority=2, payload={'synthetic': True, 'workload': 'reference_replay',
                                         'reference_case_id': self.reference_case_id})


class ExecutionAcceptedResponse(APIModel):
    execution_id: UUID
    status: Status
    created: bool
    trace_id: str
    correlation_id: str


class ExecutionStatusResponse(APIModel):
    execution_id: UUID
    incident_id: str
    status: Status
    attempt: int
    current_step: str | None
    worker_id: str | None
    duration_ms: float | None
    trace_id: str | None
    correlation_id: str | None


class EventResponse(APIModel):
    sequence: int
    timestamp: datetime
    event_type: str
    agent_id: str
    attempt: int
    status: Status


class ExecutionEventsResponse(APIModel):
    execution_id: UUID
    events: list[EventResponse]


class ExecutionResultResponse(APIModel):
    execution_id: UUID
    status: Status
    outcome: str | None
    mode: str | None
    recommended_action: str | None
    estimated_cost_brl: str | None
    approval_required: Literal[True] = True
    approval_status: Literal['pending'] | None = None
    actions_executed: Literal[False] = False


class HealthResponse(APIModel):
    status: Literal['alive'] = 'alive'


class ReadinessResponse(APIModel):
    status: Literal['ready', 'not_ready']
    dependencies: dict[str, Literal['ok', 'unavailable']]
