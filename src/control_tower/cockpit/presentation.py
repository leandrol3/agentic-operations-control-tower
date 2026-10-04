"""Server-side presentation projections. Aggregation and alerts never live in JavaScript."""

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from ..control_plane.configuration import load_config
from ..control_plane.contracts import Evidence, Trend
from ..control_plane.decision_engine import recommend
from ..control_plane.demo_fixture import fixture_samples
from ..control_plane.economics import assess_economics, load_pricing
from ..control_plane.interpretation import (
    evaluate_slo,
    lifecycle_triggers,
    measure_goal,
)
from ..control_plane.lifecycle import ALLOWED_TRANSITIONS
from ..control_plane.quality import assess_quality
from ..control_plane.registry import BusinessGoal, registry
from ..control_plane.service import ControlPlane

NAMES = {
    "supervisor": "Supervisor de operações",
    "supply": "Suprimentos",
    "production": "Produção",
    "logistics": "Logística",
    "finance": "Finanças",
    "challenger": "Riscos e contestação",
    "recommendation": "Recomendação",
}
REASONS = {
    "scale": "Há evidências para avaliar um experimento controlado de escala. Demanda e capacidade ainda exigem análise humana.",
    "optimize": "A meta está abaixo do esperado e o custo registrado aumentou. Investigue o processo antes de alterar o agente.",
    "intervene": "A taxa de resultados degradados ultrapassou o limite configurado. Revise evidências e coordene uma intervenção humana.",
    "review": "Metas ou limites operacionais exigem revisão das evidências.",
    "pause": "Há subdesempenho severo em duas janelas. A pausa é uma proposta, não uma ação executada.",
    "retire": "Avaliar aposentadoria somente com evidência e autorização humana.",
}


def present(view):
    data = view.model_dump(mode="json")
    data["name_pt"] = NAMES[view.registry.agent_id]
    if view.recommendation:
        data["recommendation"]["reason_pt"] = REASONS[view.recommendation.action]
    return data


class CockpitService:
    def __init__(self, store, settings, knowledge):
        self.store, self.settings, self.knowledge = store, settings, knowledge

    def views(self, source):
        if source == "durable":
            return ControlPlane(
                self.store,
                records=registry(self.settings.llm_mode, self.settings.openai_model),
            ).evaluate(mode=self.settings.llm_mode)
        config = load_config()
        pricing = load_pricing()
        views = ControlPlane(None, config=config, pricing=pricing).evaluate(
            samples=fixture_samples("stable"),
            mode="openai",
            source="didactic_fixture",
            now=datetime(2026, 10, 3, 12, tzinfo=timezone.utc),
        )
        dataset = json.loads(Path("fixtures/cockpit/supply.json").read_text())
        rows = dataset["observations"]
        total = len(rows)
        if dataset["source"] != "didactic" or not total:
            raise ValueError("Amostra didática inválida")
        if any(
            type(r["alternative_evidence_complete"]) is not bool
            or type(r["degraded"]) is not bool
            for r in rows
        ):
            raise ValueError("Observações inválidas")
        ids = tuple(uuid5(NAMESPACE_URL, r["id"]) for r in rows)
        actual = (
            Decimal(sum(r["alternative_evidence_complete"] for r in rows)) * 100 / total
        )
        degraded = Decimal(sum(r["degraded"] for r in rows)) * 100 / total
        old = next(v for v in views if v.registry.agent_id == "supply")
        goal = BusinessGoal(
            goal_id="supply-alternative-evidence-coverage",
            name="Cobertura de evidências alternativas",
            metric="alternative_evidence_coverage",
            target=dataset["target"],
            unit="percent",
            description="Observações sintéticas com evidências alternativas completas; não prova disponibilidade de fornecedor.",
        )
        agent = old.registry.model_copy(update={"business_goals": (goal,)})
        evidence = Evidence(
            metric="completion_rate",
            observed=actual,
            unit="percent",
            scope="agent_stage",
            source="didactic_fixture",
            execution_ids=ids,
            note="37 de 50 observações didáticas com evidências alternativas completas; não são execuções reais.",
        )
        quality = old.quality.model_copy(
            update={
                "observed": degraded,
                "execution_ids": ids,
                "note": "Resultados degradados em 50 observações didáticas, separados da lista ilustrativa de execuções.",
            }
        )
        goal_config = config.model_copy(update={"window_size": 50, "min_samples": 50})
        goals = (measure_goal(agent, goal, evidence, goal_config, old.measured_at),)
        metrics = {
            "completion_rate": evidence,
            "workflow_degraded_rate": quality,
            "stage_llm_cost_usd": old.economics,
            "stage_latency_p95_ms": old.latency,
        }
        # Didactic profile: coverage is medium, degradation high. Existing rules stay intact.
        slos = tuple(
            evaluate_slo(
                s.model_copy(update={"severity": "medium"})
                if s.metric == "completion_rate"
                else s,
                metrics[s.metric],
                "supply",
            )
            for s in config.slos
        )
        current = old.model_copy(
            update={
                "registry": agent,
                "goals": goals,
                "slos": slos,
                "quality": quality,
                "sample_count": 50,
                "window_size": 50,
                "goal_trend": Trend.UNKNOWN,
                "configuration_version": "cockpit-supply-didactic-v1",
            }
        )
        triggers = lifecycle_triggers(
            agent,
            goals,
            slos,
            current.cost_trend,
            current.economics,
            current.previous_cost,
        )
        current = current.model_copy(update={"triggers": triggers})
        rec, note = recommend(current, config)
        current = current.model_copy(
            update={"recommendation": rec, "decision_note": note}
        )
        return [current if v.registry.agent_id == "supply" else v for v in views]

    def samples(self, source):
        return (
            fixture_samples("intervene")
            if source == "didactic"
            else self.store.control_plane_samples(limit=30, mode=self.settings.llm_mode)
        )

    def operations(self, source):
        if source == "didactic":
            return [
                dict(
                    incident_id="INCIDENT-001",
                    execution_id=str(s.execution.execution_id),
                    status=s.execution.status,
                    outcome=s.execution.result.outcome if s.execution.result else None,
                    approval_status="pending",
                    created_at=s.created_at.isoformat(),
                    completed_at=s.execution.completed_at.isoformat(),
                    duration_ms=s.execution.duration_ms,
                    source="didactic",
                )
                for s in reversed(self.samples(source))
            ]
        rows = self.store.list_incidents(limit=30)
        return [
            dict(
                r,
                execution_id=str(r["execution_id"]),
                duration_ms=self.store.get(r["execution_id"]).duration_ms,
                source="durable",
            )
            for r in rows
        ]

    def execution(self, key, source):
        if source == "didactic":
            sample = next(
                (
                    s
                    for s in self.samples(source)
                    if str(s.execution.execution_id) == key
                ),
                None,
            )
            if sample is None:
                raise LookupError("Execução não encontrada na fonte selecionada")
            e, events, options = sample.execution, sample.events, sample.options
            trace = None
        else:
            e = self.store.get(UUID(key))
            events = self.store.events(UUID(key))
            options = self.store.options_for(UUID(key))
            context = self.store.context(UUID(key))
            trace = context.trace_id if context else None
        result = e.result
        return {
            "execution_id": str(e.execution_id),
            "incident_id": "INCIDENT-001" if source == "didactic" else e.incident_id,
            "status": e.status,
            "outcome": result.outcome if result else None,
            "source": source,
            "duration_ms": e.duration_ms,
            "started_at": e.started_at,
            "completed_at": e.completed_at,
            "worker_id": e.worker_id,
            "trace_id": trace,
            "quality": assess_quality(e, events).model_dump(mode="json"),
            "economics": assess_economics(
                e, events, options.llm_model, load_pricing()
            ).model_dump(mode="json"),
            "result": {
                "action": result.recommendation.recommended_action
                if result and result.recommendation
                else None,
                "approval": "pending" if result else None,
                "actions_executed": False,
            },
            "events": [
                {
                    "id": x.sequence,
                    "agent": x.agent_id,
                    "type": x.event_type,
                    "timestamp": x.timestamp.isoformat(),
                }
                for x in events
            ],
        }

    def snapshot(self, source):
        views = self.views(source)
        items = self.operations(source)
        knowledge = self.knowledge.overview(source)
        recs = [present(v)["recommendation"] for v in views if v.recommendation]
        alerts = [
            {
                "id": v.registry.agent_id + "-" + str(i),
                "agent_id": v.registry.agent_id,
                "severity": t.severity,
                "message": {
                    "goal_miss": "Meta abaixo do esperado",
                    "slo_violation": "Limite operacional ultrapassado",
                    "quality_degradation": "Resultados degradados acima do limite",
                    "cost_increase": "Aumento de custo observado",
                    "persistent_underperformance": "Subdesempenho persistente",
                }.get(t.trigger_type, "Revisão recomendada"),
                "source": source,
                "timestamp": v.measured_at,
                "recommendation": v.recommendation.action if v.recommendation else None,
            }
            for v in views
            for i, t in enumerate(v.triggers)
        ]
        # No sum of role means. Execution-level cost summary is computed once per distinct execution.
        costs = []
        for sample in self.samples(source):
            econ = assess_economics(
                sample.execution,
                sample.events,
                sample.options.llm_model,
                load_pricing(),
            )
            costs.append(
                econ.estimated_llm_cost
                if econ.usage_coverage == "recorded_calls"
                else None
            )
        total_cost = (
            sum(costs, Decimal(0))
            if costs and all(c is not None for c in costs)
            else None
        )
        attention = sorted({a["agent_id"] for a in alerts})
        value = {
            "exposure_brl": None,
            "daily_penalty_brl": None,
            "hypothetical_days": None,
            "source": source,
            "realized": None,
            "note": "Valor realizado ainda não validado",
        }
        if source == "didactic":
            from ..tools import Tools

            tools = Tools(self.settings.control_tower_root)
            value.update(
                exposure_brl=str(tools.calculate_penalty("CO-001", 7)),
                daily_penalty_brl=str(tools.calculate_penalty("CO-001", 1)),
                hypothetical_days=7,
                order_id="CO-001",
                incident_id="INCIDENT-001",
                note="Exposição potencial para atraso hipotético; não é economia realizada",
            )
        goals = [g for v in views for g in v.goals]
        return {
            "source": source,
            "runtime_mode": self.settings.llm_mode,
            "updated_at": datetime.now(timezone.utc),
            "agents": [present(v) for v in views],
            "attention": {
                "agent_ids": attention,
                "count": len(attention),
                "label": f"{len(attention)} agente requer atenção"
                if len(attention) == 1
                else f"{len(attention)} agentes requerem atenção",
                "basis": "Agentes distintos com triggers determinísticos existentes",
            },
            "business_exposure": value,
            "overview": {
                "total_agents": len(views),
                "active_agents": sum(
                    v.registry.lifecycle_state == "active" for v in views
                ),
                "attention_agents": len({a["agent_id"] for a in alerts}),
                "goals": {
                    s: sum(g.status == s for g in goals)
                    for s in ("on_target", "at_risk", "off_target", "unknown")
                },
                "slo_violations": sum(
                    s.status == "violation" for v in views for s in v.slos
                ),
                "degraded_executions": sum(
                    i["outcome"] == "degraded_recommendation" for i in items
                ),
                "estimated_cost_usd": total_cost,
                "cost_window": f"Últimas execuções terminais {'sintéticas' if source == 'didactic' else 'do modo ' + self.settings.llm_mode}; até 30 registros, sem estimativa parcial",
                "cost_sample_count": len(costs),
                "realized_business_value": None,
                "pending_recommendations": len(recs),
                "alerts": len(alerts),
            },
            "alerts": alerts,
            "recommendations": recs,
            "operations": items,
            "knowledge": knowledge,
            "plans": self.knowledge.plans(source),
            "chart": [
                {
                    "agent": NAMES[v.registry.agent_id],
                    "target": v.goals[0].target,
                    "actual": v.goals[0].actual,
                }
                for v in views
            ],
            "settings": {
                "decision_rules": [
                    "Subdesempenho severo persistente em duas janelas: propor pausa.",
                    "Múltiplas violações de alta severidade ou meta não atingida: propor revisão conforme precedência do motor.",
                    "Degradação acima do limite: propor intervenção.",
                    "Custo crescente com meta não atingida: propor otimização.",
                    "Escala requer evidência suficiente e análise humana de demanda e capacidade. Nenhuma ação é executada.",
                ],
                "thresholds": load_config().model_dump(mode="json"),
                "pricing": load_pricing().model_dump(mode="json"),
                "demo_profile": "Supply: meta 90%, amostra 50; SLO conclusão medium e degradação high. Somente fonte didática.",
                "lifecycle_edges": [
                    {"from": k, "to": t}
                    for k, targets in ALLOWED_TRANSITIONS.items()
                    for t in sorted(targets)
                ],
            },
        }
