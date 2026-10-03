"""Evidence-bound Maestro and Knowledge Compiler. No writes except proposed plans/candidates."""

from datetime import datetime, timezone
from uuid import uuid4
from .models import Fact, PlanDraft, ImprovementPlan, KnowledgeDraft, KnowledgeCandidate
from .llm import StructuredProvider, MAESTRO_PROMPT, COMPILER_PROMPT
from .presentation import NAMES
from .knowledge import FOLDERS
from .localization import pt


def validate_refs(ids, facts):
    known = {f.id for f in facts}
    if not ids or len(ids) != len(set(ids)) or not set(ids) <= known:
        raise ValueError("Referência de evidência inexistente ou duplicada")


def validate_proposal(text):
    # Structural/reference validation is strong; semantic truth still needs human review.
    forbidden = (
        "executei",
        "implantei",
        "alterei o agente",
        "aprovei o conhecimento",
        "lifecycle foi alterado",
    )
    if any(s in text.casefold() for s in forbidden):
        raise ValueError("Resposta afirma ação não autorizada")


class MaestroTools:
    def __init__(self, service, source, agent_id):
        self.service, self.source, self.agent_id = service, source, agent_id
        self.calls = []
        self.views = service.views(source)
        self.view = next(
            (v for v in self.views if v.registry.agent_id == agent_id), None
        )
        if self.view is None:
            raise LookupError("Agente não encontrado")

    def _read(self, name, value):
        self.calls.append(name)
        return value

    def get_workforce(self):
        return self._read("get_workforce", self.views)

    def get_agent(self):
        return self._read("get_agent", self.view.registry)

    def get_agent_goals(self):
        return self._read("get_agent_goals", self.view.registry.business_goals)

    def get_goal_measurements(self):
        return self._read("get_goal_measurements", self.view.goals)

    def get_agent_quality(self):
        return self._read("get_agent_quality", self.view.quality)

    def get_agent_economics(self):
        return self._read("get_agent_economics", self.view.economics)

    def get_agent_business_value(self):
        return self._read("get_agent_business_value", self.view.business_value)

    def get_agent_lifecycle(self):
        return self._read("get_agent_lifecycle", self.view.registry.lifecycle_state)

    def get_agent_slos(self):
        return self._read("get_agent_slos", self.view.slos)

    def get_agent_recommendations(self):
        return self._read("get_agent_recommendations", self.view.recommendation)

    def get_agent_executions(self):
        ids = {str(uid) for g in self.view.goals for uid in g.evidence.execution_ids}
        return self._read(
            "get_agent_executions",
            [
                i
                for i in self.service.operations(self.source)
                if i["execution_id"] in ids or self.source == "didactic"
            ],
        )

    def search_knowledge(self):
        return self._read(
            "search_knowledge",
            [
                i
                for i in self.service.knowledge.list(
                    status="approved", source=self.source
                )
                if self.agent_id in i.tags or "workforce" in i.tags
            ][:5],
        )

    def get_knowledge_item(self, key):
        item = self.service.knowledge.get(key)
        if item.validation_status != "approved" or item.source != self.source:
            raise ValueError("Conhecimento não validado para esta fonte")
        return self._read("get_knowledge_item", item)


class Maestro:
    def __init__(self, service, provider=None):
        self.service = service
        self.provider = provider or StructuredProvider()

    def chat(self, request):
        tools = MaestroTools(self.service, request.source, request.agent_id)
        agent = tools.get_agent()
        goals = tools.get_agent_goals()
        measurements = tools.get_goal_measurements()
        quality = tools.get_agent_quality()
        econ = tools.get_agent_economics()
        slos = tools.get_agent_slos()
        values = tools.get_agent_business_value()
        tools.get_agent_lifecycle()
        workforce = tools.get_workforce()
        rec = tools.get_agent_recommendations()
        executions = tools.get_agent_executions()
        knowledge = [tools.get_knowledge_item(i.id) for i in tools.search_knowledge()]
        g = measurements[0]
        actual = "desconhecido" if g.actual is None else str(round(g.actual, 2)) + "%"
        facts = [
            Fact(
                id="registry:" + agent.agent_id,
                text=f"Agente {NAMES[agent.agent_id]}; cadastro registrado; lifecycle {pt(agent.lifecycle_state)}.",
                source="Registry",
            ),
            Fact(
                id="goal:" + g.goal_id,
                text=f"Meta {g.target}%; atual {actual}; diferença {g.gap if g.gap is not None else 'desconhecida'} pontos percentuais; {tools.view.sample_count} amostras.",
                source=pt(request.source),
            ),
            Fact(
                id="quality:" + agent.agent_id,
                text=f"Resultados não normais no contexto do workflow: {quality.observed if quality.observed is not None else 'desconhecido'}%. Não mede correção semântica.",
                source=pt(request.source),
            ),
            Fact(
                id="economics:" + agent.agent_id,
                text=f"Custo estimado por papel: {econ.observed if econ.observed is not None else 'desconhecido'} USD. Não é custo total nem valor realizado.",
                source=pt(request.source),
            ),
            Fact(
                id="value:" + agent.agent_id,
                text="Valor de negócio realizado desconhecido; propostas não são economias obtidas.",
                source="BusinessValueAssessment",
            ),
            Fact(
                id="recommendation:" + agent.agent_id,
                text="Há proposta de " + pt(rec.action) + " sujeita à aprovação humana."
                if rec
                else "Não há recomendação sustentada pelas regras atuais.",
                source="Decision Engine",
            ),
        ]
        facts += [
            Fact(
                id="workforce:" + v.registry.agent_id,
                text=f"{NAMES[v.registry.agent_id]}: meta {pt(v.goals[0].status)}; proposta {pt(v.recommendation.action) if v.recommendation else 'ausente'}; lifecycle {pt(v.registry.lifecycle_state)}.",
                source=pt(request.source),
            )
            for v in workforce
        ]
        facts += [
            Fact(
                id="value-context:" + str(i),
                text=f"{pt(v.value_metric)}: {v.value_amount if v.value_amount is not None else 'desconhecido'} {v.currency_or_unit}; contexto, não resultado realizado.",
                source=pt(request.source),
            )
            for i, v in enumerate(values[:3])
        ]
        facts += [
            Fact(
                id="slo:" + s.slo_id,
                text=f"Limite {s.target}; observado {s.observed}; resultado {pt(s.status)}.",
                source="SLO",
            )
            for s in slos
        ]
        facts += [
            Fact(
                id="execution:" + i["execution_id"],
                text=f"Execução {i['execution_id']}: {pt(i['status'])}; fonte {pt(request.source)}.",
                source=pt(request.source),
            )
            for i in executions[:6]
        ]
        facts += [
            Fact(
                id="knowledge:" + i.id,
                text=i.title + ": " + i.summary,
                source="Segundo Cérebro / aprovado / " + pt(request.source),
            )
            for i in knowledge
        ]
        mock = {
            "language": "pt-BR",
            "diagnosis": f"{NAMES[agent.agent_id]} tem meta de {g.target}% e resultado {actual}. "
            + (
                "No cenário didático, 13 de 50 observações têm evidências alternativas incompletas. Isso exige investigação, não comprova a causa raiz."
                if request.source == "didactic" and agent.agent_id == "supply"
                else "A interpretação está limitada aos sinais disponíveis; desconhecido não significa sucesso."
            ),
            "objective": "Melhorar a cobertura e a confiabilidade das evidências sem alterar o agente automaticamente.",
            "steps": [
                "Revisar amostras fora da meta e distinguir observação de hipótese.",
                "Verificar estoque disponível, estoque de segurança, alternativas de fornecedor e transporte.",
                "Propor ajustes e um conjunto de avaliação com casos positivos e negativos.",
                "Comparar os resultados antes e depois e solicitar revisão humana.",
            ],
            "evidence_refs": [
                f.id
                for f in facts
                if not f.id.startswith(("execution:", "workforce:", "value-context:"))
            ]
            + [f.id for f in facts if f.id.startswith("execution:")][:2],
            "knowledge_ids": [i.id for i in knowledge],
            "expected_result": "Uma proposta de melhoria testável, com evidências e critérios de aceite.",
            "risks": "Dados didáticos não comprovam desempenho real. Não houve mudança de código, lifecycle ou permissões.",
        }
        question = request.question.casefold()
        if "aprendemos" in question:
            mock["diagnosis"] = (
                "Conhecimento validado disponível para este agente: "
                + (
                    "; ".join(i.title for i in knowledge)
                    or "nenhum item aprovado nesta fonte"
                )
                + ". Isso é memória validada, não prova de melhoria realizada."
            )
        elif "pendentes" in question:
            mock["diagnosis"] = (
                "Propostas pendentes na fonte selecionada: "
                + (
                    "; ".join(
                        NAMES[v.registry.agent_id] + " — " + pt(v.recommendation.action)
                        for v in workforce
                        if v.recommendation
                    )
                    or "nenhuma"
                )
                + ". Nenhuma mudança foi autorizada."
            )
        elif "atenção" in question or "revisão" in question:
            mock["diagnosis"] = (
                "Agentes com sinais de atenção: "
                + (
                    ", ".join(
                        NAMES[v.registry.agent_id] for v in workforce if v.triggers
                    )
                    or "nenhum sinal sustentado nesta janela"
                )
                + ". "
                + mock["diagnosis"]
            )
        if any(word in question for word in ("atenção", "pendentes", "revisão")):
            mock["evidence_refs"] += [
                f.id for f in facts if f.id.startswith("workforce:")
            ]
        draft = self.provider.generate(
            PlanDraft,
            MAESTRO_PROMPT,
            {
                "question": request.question,
                "facts": [f.model_dump() for f in facts],
                "knowledge_ids": [i.id for i in knowledge],
            },
            mock,
        )
        validate_refs(draft.evidence_refs, facts)
        if not set(draft.knowledge_ids) <= {i.id for i in knowledge}:
            raise ValueError("Conhecimento citado não está aprovado")
        validate_proposal(
            draft.diagnosis + " " + draft.expected_result + " " + " ".join(draft.steps)
        )
        plan = ImprovementPlan(
            plan_id="plan-" + uuid4().hex,
            agent_id=agent.agent_id,
            source=request.source,
            diagnosis=draft.diagnosis,
            objective=draft.objective,
            steps=draft.steps,
            staff_assignments=[
                {"name": n, "status": s}
                for n, s in [
                    ("Desenvolvimento", "Proposto"),
                    ("Dados", "Proposto"),
                    ("Arquitetura", "Consultivo"),
                    ("Avaliação / QA", "Proposto"),
                    ("Segurança", "Consultivo"),
                    ("Conhecimento", "Proposto"),
                    ("Revisor humano", "Obrigatório"),
                ]
            ],
            evidence=[f for f in facts if f.id in draft.evidence_refs],
            knowledge_ids=draft.knowledge_ids,
            expected_result=draft.expected_result,
            risk=draft.risks,
            created_at=datetime.now(timezone.utc),
            generated_by=self.provider.label,
        )
        self.service.knowledge.save_plan(plan)
        return {
            "language": "pt-BR",
            "plan": plan,
            "sources_consulted": tools.calls,
            "notice": "Plano proposto. Nenhuma ação executada. Aprovação humana obrigatória.",
        }


class KnowledgeCompiler:
    def __init__(self, service, provider=None):
        self.service = service
        self.provider = provider or StructuredProvider()

    def extract(self, key, source):
        execution = self.service.execution(key, source)
        if execution["status"] != "completed":
            raise ValueError("Somente execuções concluídas podem gerar candidatos")
        facts = [
            Fact(
                id="execution:" + key,
                text=f"Execução {key}; incidente {execution['incident_id']}; resultado {pt(execution['outcome'])}.",
                source=source,
            ),
            Fact(
                id="approval:" + key,
                text="Aprovação do incidente permanece pendente; nenhuma ação operacional foi executada.",
                source="resultado público",
            ),
            Fact(
                id="quality:" + key,
                text="Fallback: "
                + pt(execution["quality"]["fallback_used"])
                + ". Completude de evidências e conformidade podem ser desconhecidas.",
                source="QualityAssessment",
            ),
            Fact(
                id="capability:safety-stock",
                text="A capability de estoque calcula quantidade transferível preservando estoque de segurança; isso não comprova uma transferência realizada.",
                source="src/control_tower/tools.py:get_stock",
            ),
            Fact(
                id="business-outcome:" + key,
                text="Não há evidência persistida de economia realizada nem feedback humano de aceite.",
                source="limite da instrumentação",
            ),
        ]
        action = execution["result"]["action"]
        if action:
            facts.append(
                Fact(
                    id="proposal:" + key,
                    text="Proposta registrada (não executada): " + action[:2000],
                    source="resultado estruturado",
                )
            )
        facts.append(
            Fact(
                id="events:" + key,
                text=f"{len(execution['events'])} eventos disponíveis no histórico desta execução; não comprovam resultado de negócio.",
                source=pt(source),
            )
        )
        known = self.service.knowledge.list(status="approved", source=source)
        mock = {
            "language": "pt-BR",
            "type": "lesson",
            "title": "Considerar estoque de segurança antes de propor transferências",
            "summary": "A proposta de transferência deve preservar o estoque de segurança da planta de origem.",
            "selected_fact_ids": [f.id for f in facts],
            "inference": "Revisar estoque livre, limites de segurança e alternativas em conjunto pode melhorar a análise. A hipótese exige validação humana; nenhuma economia foi comprovada.",
            "related_items": [i.id for i in known[:3]],
        }
        draft = self.provider.generate(
            KnowledgeDraft,
            COMPILER_PROMPT,
            {
                "facts": [f.model_dump() for f in facts],
                "related_items": [{"id": i.id, "title": i.title} for i in known],
            },
            mock,
        )
        validate_refs(draft.selected_fact_ids, facts)
        if not set(draft.related_items) <= {i.id for i in known}:
            raise ValueError("Relação com conhecimento inexistente/não aprovado")
        validate_proposal(draft.summary + " " + draft.inference)
        selected = [f for f in facts if f.id in draft.selected_fact_ids]
        content = (
            "# "
            + draft.title
            + "\n\n## Observações fornecidas\n\n"
            + "\n".join("- " + f.text + " [" + f.id + "]" for f in selected)
            + "\n\n## Inferência proposta — requer revisão\n\n"
            + draft.inference
            + "\n\n## Conhecimento relacionado\n\n"
            + "\n".join(
                f"- [{i.title}](../{FOLDERS[i.type]}/{i.id}.md)"
                for i in known
                if i.id in draft.related_items
            )
        )
        now = datetime.now(timezone.utc)
        item = KnowledgeCandidate(
            id="knowledge-" + uuid4().hex,
            type=draft.type,
            title=draft.title,
            summary=draft.summary,
            content=content.strip(),
            tags=["supply", "workforce"],
            source_execution=key,
            source_incident=execution["incident_id"],
            source=source,
            evidence=selected,
            related=draft.related_items,
            validation_status="pending_review",
            created_at=now,
            updated_at=now,
            generated_by=self.provider.label,
            owner="Revisão humana do laboratório",
            provenance="Extração estruturada com referências validadas; sem aprovação automática.",
            evidence_level="didactic" if source == "didactic" else "inference",
        )
        return self.service.knowledge.create_candidate(
            item,
            {
                "source": source,
                "execution_id": key,
                "facts": [f.model_dump() for f in facts],
                "events": execution["events"],
                "business_outcome": "unknown",
                "human_feedback": "unavailable",
            },
        )
