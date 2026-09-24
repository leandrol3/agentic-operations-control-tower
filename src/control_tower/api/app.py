"""HTTP aceita/publica; workers executam. Nenhum grafo é executado no processo API."""
from contextlib import asynccontextmanager
from uuid import UUID
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .models import (IncidentSubmissionRequest, ExecutionAcceptedResponse, ExecutionStatusResponse,
    ExecutionEventsResponse, EventResponse, ExecutionResultResponse, HealthResponse, ReadinessResponse)
from .readiness import check_readiness
from ..runtime.settings import RuntimeSettings
from ..runtime.store import CorrelatedStore
from ..telemetry.context import ExecutionContext, bind_context, current_context
from ..telemetry.logging import log_event
from ..telemetry.tracing import initialize_tracing


def create_app(settings=None, store=None, enqueue=None, readiness=None):
    settings = settings or RuntimeSettings()
    # Injection explicita permite testar HTTP sem infraestrutura ou provider.
    if enqueue is None:
        from ..runtime.bootstrap import configure
        configure(settings)
        from ..distributed.producer import enqueue
    store = store if store is not None else CorrelatedStore(settings.database_url.get_secret_value())
    readiness = readiness if readiness is not None else check_readiness

    @asynccontextmanager
    async def lifespan(app):
        provider = initialize_tracing(settings)
        yield
        if provider:
            provider.shutdown()

    app = FastAPI(title=settings.app_name, version='lesson-03-start', lifespan=lifespan)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, error):
        # Não ecoar payload arbitrário ou input sensível na resposta.
        return JSONResponse(status_code=422, content={'detail': 'Request inválido; consulte /docs'})

    @app.middleware('http')
    async def request_log(request: Request, call_next):
        response = await call_next(request)
        if request.url.path not in ('/health', '/ready'):
            log_event('http.completed', 'Resposta HTTP', method=request.method,
                      status_code=response.status_code)
        return response

    @app.get('/health', response_model=HealthResponse)
    def health():
        return HealthResponse()

    @app.get('/ready', response_model=ReadinessResponse)
    def ready(response: Response):
        dependencies = readiness(settings)
        ok = all(value == 'ok' for value in dependencies.values())
        response.status_code = 200 if ok else 503
        return ReadinessResponse(status='ready' if ok else 'not_ready', dependencies=dependencies)

    @app.post('/incidents', response_model=ExecutionAcceptedResponse, status_code=202)
    def submit(body: IncidentSubmissionRequest, response: Response,
               x_trace_id: str | None = Header(default=None),
               x_correlation_id: str | None = Header(default=None)):
        from ..distributed.durable import TaskOptions
        try:
            context = ExecutionContext(**({'trace_id': x_trace_id} if x_trace_id else {}),
                **({'correlation_id': x_correlation_id} if x_correlation_id else {}))
            options = TaskOptions(llm_mode=settings.llm_mode, llm_model=settings.openai_model,
                demo_delay_ms=body.demo_delay_ms, llm_failure=body.llm_failure, fallback=body.fallback)
        except ValidationError:
            raise HTTPException(422, 'Contexto/opções incompatíveis com o modo do runtime') from None
        if (body.demo_delay_ms or body.llm_failure != 'none' or body.fallback != 'human') and not settings.demo_controls_enabled:
            raise HTTPException(422, 'Demo controls desabilitados neste runtime')
        with bind_context(context):
            try:
                execution, created = enqueue(body.envelope(), options, version=body.version, store=store)
            except ValueError:
                raise HTTPException(409, 'Identidade/opções conflitantes ou configuração inválida; '
                                    'confira configuração e use nova version para nova operação') from None
            except Exception:
                log_event('queue.submission_failed', 'Publicação não confirmada; reenviar mesma identidade')
                raise HTTPException(503, 'Publicação não confirmada. Reenvie o mesmo request/version; '
                                    'pode haver claim persistido.') from None
            context = current_context.get()
            response.headers['X-Trace-ID'] = context.trace_id
            response.headers['X-Correlation-ID'] = context.correlation_id
            response.headers['Location'] = f'/executions/{execution.execution_id}'
            log_event('queue.submitted', 'Producer confirmou publicação', created=created)
            return ExecutionAcceptedResponse(execution_id=execution.execution_id, status=execution.status,
                created=created, trace_id=context.trace_id, correlation_id=context.correlation_id)

    def load(execution_id):
        try:
            return store.get(execution_id)
        except ValueError:
            raise HTTPException(404, 'Execution não encontrada') from None
        except Exception:
            raise HTTPException(503, 'Store indisponível') from None

    @app.get('/executions/{execution_id}', response_model=ExecutionStatusResponse)
    def execution_status(execution_id: UUID):
        execution = load(execution_id)
        try:
            context = store.context(execution_id)
        except Exception:
            raise HTTPException(503, 'Contexto indisponível') from None
        return ExecutionStatusResponse(**{key: getattr(execution, key) for key in
            ('execution_id', 'incident_id', 'status', 'attempt', 'current_step', 'worker_id', 'duration_ms')},
            trace_id=context.trace_id if context else None,
            correlation_id=context.correlation_id if context else None)

    @app.get('/executions/{execution_id}/events', response_model=ExecutionEventsResponse)
    def events(execution_id: UUID, after: int = Query(default=0, ge=0),
               limit: int = Query(default=30, ge=1, le=100)):
        load(execution_id)
        try:
            items = store.events(execution_id)
        except Exception:
            raise HTTPException(503, 'Histórico indisponível') from None
        return ExecutionEventsResponse(execution_id=execution_id, events=[
            EventResponse(**{key: getattr(item, key) for key in EventResponse.model_fields})
            for item in items if item.sequence > after][:limit])

    @app.get('/executions/{execution_id}/result', response_model=ExecutionResultResponse)
    def result(execution_id: UUID, response: Response):
        execution = load(execution_id)
        if execution.status in ('queued', 'running'):
            response.status_code = 202
        final = execution.result
        recommendation = final.recommendation if final else None
        return ExecutionResultResponse(execution_id=execution_id, status=execution.status,
            outcome=final.outcome if final else None, mode=final.mode if final else None,
            recommended_action=recommendation.recommended_action if recommendation else None,
            estimated_cost_brl=str(recommendation.estimated_cost_brl) if recommendation else None,
            approval_status='pending' if final else None)

    return app
