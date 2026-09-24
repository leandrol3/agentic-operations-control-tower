"""Identidade explícita, sem fingir que há spans ou traceparent W3C."""
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExecutionContext(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    trace_id: str = Field(default_factory=lambda: uuid4().hex, pattern=r'^[0-9a-f]{32}$')
    correlation_id: str = Field(default_factory=lambda: uuid4().hex,
                                pattern=r'^[a-zA-Z0-9._:-]{1,64}$')
    execution_id: UUID | None = None
    incident_id: str | None = None
    worker_id: str | None = None

    @field_validator('trace_id')
    @classmethod
    def nonzero_trace(cls, value):
        if int(value, 16) == 0:
            raise ValueError('trace_id deve ser não nulo')
        return value


current_context: ContextVar[ExecutionContext | None] = ContextVar('execution_context', default=None)


@contextmanager
def bind_context(context: ExecutionContext):
    token = current_context.set(context)
    try:
        yield
    finally:
        current_context.reset(token)
