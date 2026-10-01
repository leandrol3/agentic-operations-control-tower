"""Contratos de execução; não são um banco de dados nem um scheduler."""
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, StringConstraints, model_validator

from ..models import Contract, Money

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Status = Literal['queued', 'running', 'completed', 'failed']
Milliseconds = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class Execution(Contract):
    execution_id: UUID
    incident_id: Text
    status: Status = 'queued'
    started_at: AwareDatetime | None = None
    completed_at: AwareDatetime | None = None
    current_step: Text | None = None
    attempt: Annotated[int, Field(ge=1)] = 1
    worker_id: Text | None = None
    error: Text | None = None
    workflow_status: Literal['awaiting_approval', 'blocked'] | None = None

    @model_validator(mode='after')
    def lifecycle(self):
        if self.status == 'queued':
            if any(v is not None for v in (self.started_at, self.completed_at, self.worker_id, self.current_step)):
                raise ValueError('queued ainda não tem início, fim, worker ou etapa')
        else:
            if self.started_at is None or self.worker_id is None or self.current_step is None:
                raise ValueError('Execução iniciada exige started_at, worker_id e current_step')
            if self.status == 'running' and self.completed_at is not None:
                raise ValueError('running não pode ter completed_at')
            if self.status in ('completed', 'failed'):
                if self.completed_at is None or self.completed_at < self.started_at:
                    raise ValueError('Execução terminal exige fim igual ou posterior ao início')
        if (self.status == 'failed') != (self.error is not None):
            raise ValueError('Somente failed exige descrição de erro')
        if self.status in ('queued', 'running') and self.workflow_status is not None:
            raise ValueError('Workflow ainda não terminou')
        if self.status == 'completed' and self.workflow_status == 'blocked':
            raise ValueError('Workflow bloqueado não é execução completed')
        return self
