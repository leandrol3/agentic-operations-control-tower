"""HTTP aceita/publica; workers executam. Nenhum grafo é executado no processo API."""
from contextlib import asynccontextmanager
from uuid import UUID
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from ..application import IncidentCapability, ApplicationError

from .models import (IncidentSummary, Status, IncidentSubmissionRequest, ExecutionAcceptedResponse, ExecutionStatusResponse,
    ExecutionEventsResponse, ExecutionResultResponse, HealthResponse, ReadinessResponse)
from .readiness import check_readiness
from ..runtime.settings import RuntimeSettings
from ..runtime.store import CorrelatedStore
from ..telemetry.logging import log_event
from ..telemetry.tracing import initialize_tracing
from ..telemetry import tracing
from ..telemetry.http import HTTPTracing


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
            tracing.shutdown()

    capability = IncidentCapability(settings, store, enqueue)
    app = FastAPI(title=settings.app_name, version='lesson-04-cockpit', lifespan=lifespan)

    @app.exception_handler(ApplicationError)
    async def application_error(request, error):
        return JSONResponse(status_code=error.code, content={'detail': error.detail})

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

    @app.get('/incidents', response_model=list[IncidentSummary])
    def incidents(status: Status | None = None, limit: int = Query(default=20, ge=1, le=100)):
        return capability.list_incidents(status=status, limit=limit)

    @app.post('/incidents', response_model=ExecutionAcceptedResponse, status_code=202)
    def submit(body: IncidentSubmissionRequest, response: Response,
               x_trace_id: str | None = Header(default=None),
               x_correlation_id: str | None = Header(default=None)):
        accepted = capability.submit_incident(body, x_trace_id=x_trace_id,
                                              x_correlation_id=x_correlation_id)
        response.headers['X-Trace-ID'] = accepted.trace_id
        response.headers['X-Correlation-ID'] = accepted.correlation_id
        response.headers['Location'] = f'/executions/{accepted.execution_id}'
        return accepted

    @app.get('/executions/{execution_id}', response_model=ExecutionStatusResponse)
    def execution_status(execution_id: UUID):
        return capability.execution_status(execution_id)

    @app.get('/executions/{execution_id}/events', response_model=ExecutionEventsResponse)
    def events(execution_id: UUID, after: int = Query(default=0, ge=0),
               limit: int = Query(default=30, ge=1, le=100)):
        return capability.events(execution_id, after, limit)

    @app.get('/executions/{execution_id}/result', response_model=ExecutionResultResponse)
    def result(execution_id: UUID, response: Response):
        result = capability.result(execution_id)
        if result.status in ('queued', 'running'):
            response.status_code = 202
        return result

    # Future Control Plane INPUTS only. No decision or automatic action.
    from ..control_plane.registry import registry, AgentRecord
    from ..control_plane.quality import assess_quality, QualityAssessment
    from ..control_plane.economics import assess_economics, load_pricing, ExecutionEconomics

    @app.get('/agents', response_model=list[AgentRecord])
    def agents():
        return registry(settings.llm_mode, settings.openai_model)

    @app.get('/agents/{agent_id}', response_model=AgentRecord)
    def agent(agent_id: str):
        for record in registry(settings.llm_mode, settings.openai_model):
            if record.agent_id == agent_id:
                return record
        raise HTTPException(404, 'Agent não encontrado')

    def signal_inputs(execution_id):
        execution = capability.load(execution_id)
        try:
            return execution, store.events(execution_id)
        except Exception:
            raise HTTPException(503, 'Histórico indisponível') from None

    @app.get('/executions/{execution_id}/quality', response_model=QualityAssessment)
    def quality(execution_id: UUID):
        return assess_quality(*signal_inputs(execution_id))

    @app.get('/executions/{execution_id}/economics', response_model=ExecutionEconomics)
    def economics(execution_id: UUID):
        execution, history = signal_inputs(execution_id)
        try:
            options = store.options_for(execution_id)
            pricing = load_pricing()
        except Exception:
            raise HTTPException(503, 'Configuração de economics indisponível') from None
        return assess_economics(execution, history, options.llm_model, pricing)

    from ..control_plane.api import register_routes
    register_routes(app, store, settings)

    from ..cockpit.api import register_cockpit
    register_cockpit(app, store, settings)

    app.add_middleware(HTTPTracing)  # Outer span also covers the existing HTTP log middleware.
    return app
