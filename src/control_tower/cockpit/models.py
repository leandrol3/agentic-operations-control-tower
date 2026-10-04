from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, create_model, field_validator

from ..models import Contract

Key = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{2,79}$")]
Text = Annotated[str, Field(min_length=1, max_length=12000)]
Source = Literal["didactic", "durable"]
KnowledgeType = Literal["entity", "decision", "lesson", "pattern"]


class Fact(Contract):
    id: Text
    text: Text
    source: Text


class KnowledgeDraft(Contract):
    language: Literal["pt-BR"]
    type: KnowledgeType
    title: Text
    summary: Text
    selected_fact_ids: list[str] = Field(min_length=1, max_length=20)
    inference: Text
    related_items: list[Key] = Field(max_length=20)


class KnowledgeItem(Contract):
    id: Key
    type: KnowledgeType
    title: Text
    summary: Text
    content: Text
    tags: list[str]
    source_execution: Text
    source_incident: Text
    source: Source
    evidence: list[Fact] = Field(min_length=1)
    related: list[Key]
    validation_status: Literal[
        "draft", "pending_review", "approved", "rejected", "superseded"
    ]
    created_at: datetime
    updated_at: datetime
    generated_by: Text
    owner: Text
    provenance: Text
    evidence_level: Literal["didactic", "recorded", "inference"]
    reviewer: str | None = None
    review_note: str | None = None


class KnowledgeCandidate(KnowledgeItem):
    validation_status: Literal["pending_review"] = "pending_review"


class ReviewRequest(Contract):
    reviewer: Annotated[str, Field(min_length=3, max_length=100)]
    note: Annotated[str, Field(min_length=3, max_length=2000)]
    confirmed: Literal[True]

    @field_validator("reviewer", "note")
    @classmethod
    def meaningful(cls, value):
        if len(value.strip()) < 3:
            raise ValueError("Informe nome e justificativa da revisão")
        return value.strip()


class MaestroContext(Contract):
    context_type: Literal[
        "workforce",
        "agent",
        "execution",
        "recommendation",
        "knowledge",
        "lifecycle",
        "economics",
    ] = "workforce"
    agent_id: str | None = None
    execution_id: str | None = None
    recommendation_id: str | None = None
    knowledge_id: Key | None = None
    source: Source = "didactic"
    route: Annotated[str, Field(max_length=120)] = "overview"
    selected_filters: dict[str, str] = Field(default_factory=dict, max_length=5)


class MaestroUsage(Contract):
    model: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost: str | None = None
    currency: str | None = None
    pricing_version: str | None = None
    scope: str = "Consulta ao Maestro; estimativa, não fatura nem custo do workflow"


class MaestroRequest(Contract):
    question: Annotated[str, Field(min_length=3, max_length=2000)]
    session_id: Key | None = None
    context: MaestroContext | None = None
    agent_id: str = "supply"
    source: Source = "didactic"


class PlanDraft(Contract):
    hypothesis: Text | None = None
    language: Literal["pt-BR"]
    diagnosis: Text
    objective: Text
    steps: list[Text] = Field(min_length=1, max_length=8)
    evidence_refs: list[str] = Field(min_length=1)
    knowledge_ids: list[Key]
    expected_result: Text
    risks: Text


def grounded_plan_schema(facts):
    """Constrain provider references to this retrieval, without changing decision rules."""
    ids = tuple(dict.fromkeys(f.id for f in facts))
    if not ids:
        raise ValueError("Não há evidências para propor um plano")
    return create_model(
        "GroundedPlanDraft",
        __base__=PlanDraft,
        evidence_refs=(
            list[Literal[ids]],
            Field(
                min_length=1,
                description="IDs exatos das evidências recuperadas. Nunca descrições, títulos ou traduções.",
            ),
        ),
    )


class ImprovementPlan(Contract):
    hypothesis: str | None = None
    usage: MaestroUsage | None = None
    plan_id: Key
    agent_id: str
    source: Source
    diagnosis: str
    objective: str
    steps: list[str]
    staff_assignments: list[dict[str, str]]
    evidence: list[Fact]
    knowledge_ids: list[str]
    expected_result: str
    risk: str
    requires_human_approval: Literal[True] = True
    status: Literal["draft", "proposed", "approved", "rejected"] = "proposed"
    created_at: datetime
    generated_by: Text


class MaestroResponse(Contract):
    session_id: str | None = None
    context: MaestroContext | None = None
    language: Literal["pt-BR"]
    plan: ImprovementPlan
    sources_consulted: list[str]
    notice: str
