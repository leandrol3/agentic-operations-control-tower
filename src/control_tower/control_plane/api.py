"""Read-only transport adapter. No fixture loading and no mutation endpoints."""
from typing import Literal
from fastapi import HTTPException
from .contracts import AgentControlPlaneView, ControlPlaneRecommendation
from .service import ControlPlane, UnknownAgent
from .registry import registry


def register_routes(app, store, settings):
    def evaluate(mode, agent_id=None):
        try:
            return ControlPlane(store, records=registry(settings.llm_mode, settings.openai_model)).evaluate(mode=mode, agent_id=agent_id)
        except UnknownAgent:
            raise HTTPException(404, 'Agent not found') from None
        except Exception:
            raise HTTPException(503, 'Control Plane evidence/configuration unavailable') from None

    @app.get('/control-plane/agents', response_model=list[AgentControlPlaneView])
    def overview(mode: Literal['mock','openai'] = 'mock'):
        return evaluate(mode)

    @app.get('/control-plane/agents/{agent_id}', response_model=AgentControlPlaneView)
    def agent(agent_id: str, mode: Literal['mock','openai'] = 'mock'):
        return evaluate(mode, agent_id)[0]

    @app.get('/control-plane/recommendations', response_model=list[ControlPlaneRecommendation])
    def recommendations(mode: Literal['mock','openai'] = 'mock'):
        return [v.recommendation for v in evaluate(mode) if v.recommendation is not None]
