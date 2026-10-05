"""Local, configured workforce. Goals are didactic targets, never observed KPIs."""
from enum import StrEnum
from typing import Annotated, Literal
from pydantic import Field, model_validator
from ..models import Contract

Text = Annotated[str, Field(min_length=1)]
AgentId = Literal['supervisor', 'supply', 'production', 'logistics', 'finance', 'challenger', 'recommendation']


class LifecycleState(StrEnum):
    """Administrative metadata only; no transitions or runtime execution policy."""
    DRAFT = 'draft'
    PILOT = 'pilot'
    ACTIVE = 'active'
    REVIEW = 'review'
    PAUSED = 'paused'
    RETIRED = 'retired'


class BusinessGoal(Contract):
    goal_id: Text
    name: Text
    metric: Text
    target: float = Field(ge=0, allow_inf_nan=False)
    unit: Literal['percent', 'seconds']
    measurement_window: Literal['per_execution'] = 'per_execution'
    target_source: Literal['didactic_configured_example'] = 'didactic_configured_example'
    description: Text


class AgentRecord(Contract):
    agent_id: AgentId
    name: Text
    role: Text
    business_owner: Text
    technical_owner: Text
    version: Text = 'lesson-01-complete'
    status: Literal['registered'] = 'registered'
    lifecycle_state: LifecycleState = Field(description=
        'Administrative lifecycle position; not runtime health or execution status')
    execution_type: Literal['deterministic', 'llm_with_deterministic_tools']
    model: Text | None
    tools: tuple[Text, ...]
    interfaces: tuple[Literal['langgraph_node'], ...] = ('langgraph_node',)
    criticality: Literal['high', 'medium'] = 'high'
    business_goals: tuple[BusinessGoal, ...] = Field(min_length=1)
    configuration_scope: Literal['current_runtime_not_execution_history'] = 'current_runtime_not_execution_history'

    @model_validator(mode='after')
    def consistent(self):
        if (self.execution_type == 'deterministic') != (self.model is None):
            raise ValueError('Deterministic agents have no model')
        if len({g.goal_id for g in self.business_goals}) != len(self.business_goals):
            raise ValueError('Duplicate goals')
        return self


# HTTP/MCP expose this system capability, not seven individual agents.
SYSTEM_CAPABILITY = {'capability_id': 'analyze-reference', 'interfaces': ('http', 'mcp'),
                     'reference_case_id': 'INCIDENT-001'}


def registry(mode='mock', model='gpt-4.1-mini') -> tuple[AgentRecord, ...]:
    rows = (
        ('supervisor', 'Operations Supervisor', 'Coordinate the investigation', 'Operations', (),
         'investigation_plan_completed', 'Plano válido que seleciona os especialistas necessários'),
        ('supply', 'Supply', 'Collect inventory and supplier evidence', 'Supply Chain',
         ('get_stock', 'get_supplier', 'get_alternative_suppliers'),
         'supply_evidence_completed', 'Evidência de estoque e fornecedores produzida sem falha'),
        ('production', 'Production', 'Identify orders and material demand', 'Production Planning',
         ('get_orders', 'get_customer_order'), 'production_evidence_completed',
         'Ordens, vínculos e demanda validados pelo contrato de evidência'),
        ('logistics', 'Logistics', 'Identify reference transport routes', 'Logistics',
         ('get_routes',), 'logistics_evidence_completed', 'Rotas standard e express disponíveis'),
        ('finance', 'Finance', 'Calculate deterministic scenario costs', 'Finance',
         ('calculate_penalty',), 'deterministic_calculation_completed',
         'Cálculo dos quatro cenários concluído; não mede custo de inferência'),
        ('challenger', 'Risk / Challenger', 'Challenge assumptions and validate scenarios', 'Operations Risk',
         ('calculate_penalty',), 'challenge_completed', 'Revisão concluída; não premiar quantidade de alertas'),
        ('recommendation', 'Recommendation', 'Produce an actionable recommendation for human review', 'Operations',
         (), 'recommendation_completed', 'Recomendação estruturada concluída; aprovação permanece humana'),
    )
    return tuple(AgentRecord(agent_id=aid, name=name, role=role, business_owner=owner,
        lifecycle_state=LifecycleState.ACTIVE,
        technical_owner='AI Engineering (didactic ownership)',
        execution_type='deterministic' if mode == 'mock' or aid == 'finance' else 'llm_with_deterministic_tools',
        model=None if mode == 'mock' or aid == 'finance' else model, tools=tools,
        business_goals=(BusinessGoal(goal_id=f'{aid}.completion', name=description, metric=metric,
            target=100, unit='percent', description='Meta ilustrativa por execução (sucesso=100%, falha=0%). '
            'Eventos de etapa são evidência candidata; avaliação automática de metas ainda não implementada.'),))
        for aid, name, role, owner, tools, metric, description in rows)
