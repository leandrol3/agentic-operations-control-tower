"""Shared application capability: public contracts, existing producer and durable store.

No transport, graph execution or agent logic here. HTTP/MCP map ApplicationError.
"""
from uuid import UUID
from pydantic import ValidationError
from opentelemetry import trace
from .api.models import (IncidentSubmissionRequest, ExecutionAcceptedResponse,
    ExecutionStatusResponse, ExecutionEventsResponse, EventResponse, ExecutionResultResponse)
from .telemetry.context import ExecutionContext, bind_context, current_context
from .telemetry.logging import log_event
from .telemetry import tracing


class ApplicationError(Exception):
    def __init__(self, code: int, detail: str):
        super().__init__(detail)
        self.code, self.detail = code, detail


class IncidentCapability:
    def __init__(self, settings, store, enqueue):
        self.settings, self.store, self.enqueue = settings, store, enqueue

    def submit_incident(self, body: IncidentSubmissionRequest, *,
                        x_trace_id: str | None = None,
                        x_correlation_id: str | None = None) -> ExecutionAcceptedResponse:
        from .distributed.durable import TaskOptions
        try:
            context = ExecutionContext(**({'trace_id': x_trace_id} if x_trace_id else {}),
                **({'correlation_id': x_correlation_id} if x_correlation_id else {}))
            options = TaskOptions(llm_mode=self.settings.llm_mode, llm_model=self.settings.openai_model,
                demo_delay_ms=body.demo_delay_ms, llm_failure=body.llm_failure, fallback=body.fallback)
        except ValidationError:
            raise ApplicationError(422, 'Contexto/opções incompatíveis com o modo do runtime') from None
        if (body.demo_delay_ms or body.llm_failure != 'none' or body.fallback != 'human') and not self.settings.demo_controls_enabled:
            raise ApplicationError(422, 'Demo controls desabilitados neste runtime')
        real = tracing.identifiers()
        if real:
            context = context.model_copy(update={'trace_id': real['trace_id']})
        with bind_context(context):
            trace.get_current_span().set_attributes({
                'control_tower.operation': 'analyze-reference',
                'control_tower.version': body.version})
            try:
                execution, created = self.enqueue(body.envelope(), options, version=body.version, store=self.store)
            except ValueError:
                raise ApplicationError(409, 'Identidade/opções conflitantes ou configuração inválida; '
                                    'confira configuração e use nova version para nova operação') from None
            except Exception:
                log_event('queue.submission_failed', 'Publicação não confirmada; reenviar mesma identidade')
                raise ApplicationError(503, 'Publicação não confirmada. Reenvie o mesmo request/version; '
                                    'pode haver claim persistido.') from None
            context = current_context.get()
            trace.get_current_span().set_attributes(tracing.attributes())
            log_event('queue.submitted', 'Producer confirmou publicação', created=created)
            return ExecutionAcceptedResponse(execution_id=execution.execution_id, status=execution.status,
                created=created, trace_id=context.trace_id, correlation_id=context.correlation_id)

    def load(self, execution_id):
        try:
            return self.store.get(execution_id)
        except ValueError:
            raise ApplicationError(404, 'Execution não encontrada') from None
        except Exception:
            raise ApplicationError(503, 'Store indisponível') from None

    def execution_status(self, execution_id: UUID) -> ExecutionStatusResponse:
        execution = self.load(execution_id)
        try:
            context = self.store.context(execution_id)
        except Exception:
            raise ApplicationError(503, 'Contexto indisponível') from None
        return ExecutionStatusResponse(**{key: getattr(execution, key) for key in
            ('execution_id', 'incident_id', 'status', 'attempt', 'current_step', 'worker_id', 'duration_ms')},
            trace_id=context.trace_id if context else None,
            correlation_id=context.correlation_id if context else None)

    def events(self, execution_id: UUID, after: int = 0, limit: int = 30) -> ExecutionEventsResponse:
        self.load(execution_id)
        try:
            items = self.store.events(execution_id)
        except Exception:
            raise ApplicationError(503, 'Histórico indisponível') from None
        return ExecutionEventsResponse(execution_id=execution_id, events=[
            EventResponse(**{key: getattr(item, key) for key in EventResponse.model_fields})
            for item in items if item.sequence > after][:limit])

    def result(self, execution_id: UUID) -> ExecutionResultResponse:
        execution = self.load(execution_id)
        final = execution.result
        recommendation = final.recommendation if final else None
        return ExecutionResultResponse(execution_id=execution_id, status=execution.status,
            outcome=final.outcome if final else None, mode=final.mode if final else None,
            recommended_action=recommendation.recommended_action if recommendation else None,
            estimated_cost_brl=str(recommendation.estimated_cost_brl) if recommendation else None,
            approval_status='pending' if final else None)
