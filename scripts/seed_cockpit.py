"""Prepare explicit didactic seeds only; never replace reviewed knowledge."""

from datetime import datetime, timezone
from control_tower.cockpit.knowledge import KnowledgeStore
from control_tower.cockpit.models import KnowledgeItem, Fact, MaestroRequest
from control_tower.cockpit.presentation import CockpitService
from control_tower.cockpit.assistance import Maestro, KnowledgeCompiler
from control_tower.cockpit.llm import StructuredProvider
from control_tower.settings import Settings
from control_tower.runtime.settings import RuntimeSettings


def seed():
    store = KnowledgeStore()
    now = datetime(2026, 10, 3, 12, tzinfo=timezone.utc)
    seeds = [
        (
            "entity-material-m42",
            "entity",
            "Material M42",
            "Material fictício do caso NovaCore; sem vínculo com clientes reais.",
            [],
        ),
        (
            "lesson-safety-stock",
            "lesson",
            "Estoque de segurança antes da transferência",
            "Avaliar estoque livre e preservar o piso de segurança antes de propor transferência entre plantas.",
            ["entity-material-m42"],
        ),
        (
            "pattern-evidence-review",
            "pattern",
            "Revisão conjunta de evidências alternativas",
            "Relacionar estoque, fornecedores, lead time e transporte; tratar dados ausentes como limites da análise.",
            ["lesson-safety-stock"],
        ),
    ]
    with store.lock():
        existing = {i.id for i in store.list()}
        for key, kind, title, summary, related in seeds:
            if key in existing:
                continue
            store._save(
                KnowledgeItem(
                    id=key,
                    type=kind,
                    title=title,
                    summary=summary,
                    content=(
                        "# "
                        + title
                        + "\n\n"
                        + summary
                        + "\n\nConteúdo didático pré-preparado, não aprendizado observado em produção.\n\n"
                        + "\n".join(
                            f"- [{r}](../"
                            + ("entities/" if r.startswith("entity") else "lessons/")
                            + r
                            + ".md)"
                            for r in related
                        )
                    ).strip(),
                    tags=["supply", "workforce"],
                    source_execution="didactic-curriculum",
                    source_incident="INCIDENT-001",
                    source="didactic",
                    evidence=[
                        Fact(
                            id="curriculum:" + key,
                            text=summary,
                            source="Curadoria didática do laboratório",
                        )
                    ],
                    related=related,
                    validation_status="approved",
                    created_at=now,
                    updated_at=now,
                    generated_by="didactic_seed",
                    owner="Curadoria didática",
                    provenance="Seed aprovado apenas para a demonstração; não representa revisão de resultado real.",
                    evidence_level="didactic",
                    reviewer="Curadoria didática pré-preparada",
                    review_note="Material de referência do LAB.",
                )
            )
    service = CockpitService(
        None,
        RuntimeSettings(_env_file=None, llm_mode="mock", otel_enabled=False),
        store,
    )
    provider = StructuredProvider(Settings())
    if not store.list(status="pending_review", source="didactic"):
        key = service.operations("didactic")[0]["execution_id"]
        KnowledgeCompiler(service, provider).extract(key, "didactic")
    if not store.plans("didactic"):
        Maestro(service, provider).chat(
            MaestroRequest(question="Como posso melhorar o agente de Supply?")
        )
    print(
        "Cenário didático preparado. Conhecimento existente preservado; nenhuma chamada LLM real."
    )


if __name__ == "__main__":
    seed()
