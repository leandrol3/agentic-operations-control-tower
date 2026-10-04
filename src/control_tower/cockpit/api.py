import os
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, Query
from fastapi.responses import JSONResponse

from ..settings import Settings
from .assistance import KnowledgeCompiler
from .conversation import Conversations
from .knowledge import KnowledgeStore
from .llm import ProviderConfigurationError
from .models import (
    KnowledgeCandidate,
    KnowledgeItem,
    MaestroRequest,
    MaestroResponse,
    ReviewRequest,
    Source,
)
from .presentation import CockpitService


def register_cockpit(app, store, settings):
    conversations = Conversations()

    @app.middleware("http")
    async def protect_submission_without_provider(request, call_next):
        # Read-only availability must not silently accept unserviceable jobs.
        if (
            os.getenv("COCKPIT_READ_WITHOUT_LLM") == "true"
            and settings.llm_mode == "openai"
            and request.method == "POST"
            and request.url.path == "/incidents"
        ):
            try:
                Settings.load(settings.control_tower_root)
            except ValueError:
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": "Provider LLM não configurado; consultas do Control Plane permanecem disponíveis."
                    },
                )
        return await call_next(request)

    def service():
        return CockpitService(store, settings, KnowledgeStore())

    def call(operation):
        try:
            return operation()
        except ProviderConfigurationError as error:
            raise HTTPException(503, str(error)) from None
        except LookupError:
            raise HTTPException(
                404, "Item não encontrado na fonte selecionada"
            ) from None
        except (ValueError, PermissionError):
            raise HTTPException(
                409, "Operação não validada. Confira evidências, estado e configuração."
            ) from None
        except Exception:
            raise HTTPException(
                503, "Serviço indisponível. Verifique a configuração e tente novamente."
            ) from None

    @app.get("/cockpit/overview")
    def overview(source: Source = "didactic"):
        return call(lambda: service().snapshot(source))

    @app.get("/cockpit/reports/summary")
    def reports(source: Source = "didactic"):
        return call(lambda: service().snapshot(source))

    @app.get("/cockpit/alerts")
    def alerts(source: Source = "didactic"):
        return call(lambda: service().snapshot(source)["alerts"])

    @app.get("/cockpit/executions/{execution_id}")
    def execution(execution_id: UUID, source: Source = "didactic"):
        return call(lambda: service().execution(str(execution_id), source))

    @app.post("/maestro/chat", response_model=MaestroResponse)
    def chat(request: MaestroRequest):
        return call(lambda: conversations.chat(service(), request))

    @app.get("/knowledge", response_model=list[KnowledgeItem])
    def knowledge(
        source: Source = "didactic",
        q: str = Query(default="", max_length=200),
        status: Literal["approved", "pending_review", "rejected", "superseded"]
        | None = None,
    ):
        return call(lambda: KnowledgeStore().list(q, status, source))

    @app.get("/knowledge/{key}", response_model=KnowledgeItem)
    def knowledge_item(key: str):
        return call(lambda: KnowledgeStore().get(key))

    @app.post("/knowledge/extract/{execution_id}", response_model=KnowledgeCandidate)
    def extract(execution_id: UUID, source: Source = "didactic"):
        return call(
            lambda: KnowledgeCompiler(service()).extract(str(execution_id), source)
        )

    @app.post("/knowledge/{key}/approve", response_model=KnowledgeItem)
    def approve(key: str, request: ReviewRequest):
        return call(lambda: KnowledgeStore().review(key, "approved", request))

    @app.post("/knowledge/{key}/reject", response_model=KnowledgeItem)
    def reject(key: str, request: ReviewRequest):
        return call(lambda: KnowledgeStore().review(key, "rejected", request))
