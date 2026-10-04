"""Bounded, process-local LAB sessions. No provider memory or enterprise chat storage."""

from collections import OrderedDict
from threading import Lock
from uuid import uuid4

from .assistance import Maestro
from .models import Fact, MaestroContext


class Conversations:
    def __init__(self, capacity=128):
        self.capacity = capacity
        self.sessions = OrderedDict()
        self.lock = Lock()

    def chat(self, service, request):
        key = request.session_id or "session-" + uuid4().hex
        with self.lock:
            if key not in self.sessions:
                if len(self.sessions) >= self.capacity:
                    available = next(
                        (k for k, v in self.sessions.items() if not v["lock"].locked()),
                        None,
                    )
                    if available is None:
                        raise ValueError("Sessões ocupadas; tente novamente")
                    del self.sessions[available]
                self.sessions[key] = {"history": [], "lock": Lock()}
            entry = self.sessions[key]
            self.sessions.move_to_end(key)
            if not entry["lock"].acquire(blocking=False):
                raise ValueError("Já existe uma análise em andamento nesta sessão")
        try:
            context = request.context or MaestroContext(
                agent_id=request.agent_id, source=request.source
            )
            facts, agent_id = resolve_context(service, context)
            request = request.model_copy(
                update={
                    "source": context.source,
                    "agent_id": agent_id,
                    "context": context,
                }
            )
            result = Maestro(service).chat(
                request, history=entry["history"][-12:], context_facts=facts
            )
            # Only validated, saved plans enter memory. Failed requests leave the session untouched.
            entry["history"].extend(
                [
                    {
                        "role": "user",
                        "content": request.question,
                        "context": context.model_dump(),
                    },
                    {
                        "role": "assistant",
                        "content": result["plan"].diagnosis[:2500],
                        "proposal": result["plan"].objective[:1000],
                    },
                ]
            )
            entry["history"] = entry["history"][-12:]
            return dict(result, session_id=key, context=context)
        finally:
            entry["lock"].release()


def resolve_context(service, context):
    """Resolve identifiers server-side; never accept client facts/HTML as evidence."""
    agent_id = context.agent_id or "supply"
    facts = []
    if context.context_type == "execution" and not context.execution_id:
        raise ValueError("Execução obrigatória")
    if context.context_type == "recommendation" and not context.recommendation_id:
        raise ValueError("Recomendação obrigatória")
    if context.context_type == "knowledge" and not context.knowledge_id:
        raise ValueError("Conhecimento obrigatório")
    if context.context_type == "economics":
        exposure = service.snapshot(context.source)["business_exposure"]
        facts.append(
            Fact(
                id="context-business-exposure",
                source="Business Value / " + context.source,
                text=(
                    f"Exposição potencial {exposure['exposure_brl']} BRL: penalidade diária {exposure['daily_penalty_brl']} BRL × {exposure['hypothetical_days']} dias hipotéticos, pedido CO-001 / INCIDENT-001. Não é atraso confirmado, economia realizada ou valor individual por agente."
                    if exposure["exposure_brl"] is not None
                    else "Exposição potencial indisponível no histórico durável; não inferir valor a partir do cenário didático."
                ),
            )
        )
    if context.execution_id:
        item = service.execution(context.execution_id, context.source)
        facts.append(
            Fact(
                id="context-execution:" + item["execution_id"],
                source="Execução / " + context.source,
                text=f"Incidente {item['incident_id']}; estado {item['status']}; duração {item['duration_ms']} ms; nenhuma ação de negócio autorizada por esta consulta.",
            )
        )
    if context.recommendation_id:
        rec = next(
            (
                v.recommendation
                for v in service.views(context.source)
                if v.recommendation
                and str(v.recommendation.recommendation_id) == context.recommendation_id
            ),
            None,
        )
        if rec is None:
            raise LookupError("Recomendação não encontrada")
        agent_id = rec.agent_id
        facts.append(
            Fact(
                id="context-recommendation:" + str(rec.recommendation_id),
                source="Decision Engine",
                text=f"Proposta {rec.action}; aprovação humana obrigatória; transição sugerida {rec.suggested_lifecycle_state}; não executada.",
            )
        )
    if context.knowledge_id:
        item = service.knowledge.get(context.knowledge_id)
        if item.source != context.source:
            raise LookupError("Fonte diferente")
        facts.append(
            Fact(
                id="context-knowledge:" + item.id,
                source="Segundo Cérebro",
                text=(item.title + ": " + item.summary)
                if item.validation_status == "approved"
                else "Conhecimento ainda não validado; conteúdo excluído da síntese factual.",
            )
        )
    return facts, agent_id
