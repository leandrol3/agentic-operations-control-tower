"""Estado compartilhado: cada especialista tem um canal exclusivo de escrita."""
from datetime import date
from typing import Generic, Literal, TypeVar

from pydantic import model_validator

from ..llm import ChallengerJudgment, InvestigationPlan, RecommendationDecision, SpecialistSynthesis

from ..models import (
    Carrier, Contract, CustomerOrder, Incident, Money, NonNegative, ProductionOrder,
    Recommendation, Stock, Supplier,
)

Specialist = Literal['supply', 'production', 'logistics']
T = TypeVar('T')


class Result(Contract, Generic[T]):
    data: T | None = None
    error: str | None = None

    @model_validator(mode='after')
    def exactly_one(self):
        if (self.data is None) == (self.error is None):
            raise ValueError('Resultado deve conter dados OU erro')
        if self.error is not None and not self.error.strip():
            raise ValueError('Erro deve explicar a falha')
        return self


class SupplyEvidence(Contract):
    local: Stock
    origin: Stock
    baseline: Supplier
    alternative: Supplier


class ProductionEvidence(Contract):
    orders: tuple[ProductionOrder, ...]
    customers: tuple[CustomerOrder, ...]
    demand_units: NonNegative

    @model_validator(mode='after')
    def consistent(self):
        if not self.orders or len({o.order_id for o in self.orders}) != len(self.orders):
            raise ValueError('Ordens ausentes ou duplicadas')
        if len({c.order_id for c in self.customers}) != len(self.customers):
            raise ValueError('Clientes duplicados')
        if {o.customer_order for o in self.orders} != {c.order_id for c in self.customers}:
            raise ValueError('Pedidos de clientes incompletos')
        if self.demand_units != sum(o.quantity * o.material_units_per_product for o in self.orders):
            raise ValueError('Demanda inconsistente')
        return self


class LogisticsEvidence(Contract):
    standard: Carrier
    express: Carrier


class Investigation(Contract):
    supply: SupplyEvidence
    production: ProductionEvidence
    logistics: LogisticsEvidence


class Allocation(Contract):
    source: str
    units: NonNegative
    available_date: date


class Delivery(Contract):
    order_id: str
    customer_order: str
    strategic: bool
    allocations: tuple[Allocation, ...]
    production_date: date
    delivery_date: date
    due_date: date
    delay_days: NonNegative
    penalty_brl: Money


class Scenario(Contract):
    scenario_id: Literal['A', 'B', 'C', 'D']
    description: str
    deliveries: tuple[Delivery, ...]
    material_premium_brl: Money
    freight_brl: Money
    penalty_brl: Money
    total_cost_brl: Money
    transferred_units: NonNegative
    origin_remaining_units: NonNegative
    origin_safety_breach_units: NonNegative
    expedited: bool
    assumptions: tuple[str, ...]


class FinanceReport(Contract):
    scenarios: tuple[Scenario, ...]
    proposed_scenario: Literal['A', 'B', 'C', 'D']


class Finding(Contract):
    scenario_id: str
    category: Literal['policy', 'inconsistency', 'missing_information', 'assumption']
    blocking: bool
    message: str


class Review(Contract):
    findings: tuple[Finding, ...]
    selected_scenario: Literal['A', 'B', 'C', 'D'] | None


class Approval(Contract):
    required: Literal[True] = True
    status: Literal['pending'] = 'pending'
    authority: Literal['operations_manager', 'manager']
    actions_executed: Literal[False] = False


class WorkflowState(Contract):
    incident: Incident
    plan: tuple[Specialist, ...] = ()
    supervisor_reason: str = ''
    supply: Result[SupplyEvidence] | None = None
    production: Result[ProductionEvidence] | None = None
    logistics: Result[LogisticsEvidence] | None = None
    investigation: Investigation | None = None
    finance: FinanceReport | None = None
    review: Review | None = None
    recommendation: Recommendation | None = None
    approval: Approval | None = None
    status: Literal['investigating', 'blocked', 'awaiting_approval'] = 'investigating'
    blockers: tuple[str, ...] = ()

    llm_mode: Literal['mock', 'openai'] = 'mock'
    llm_model: str | None = None
    llm_plan: InvestigationPlan | None = None
    supply_synthesis: SpecialistSynthesis | None = None
    production_synthesis: SpecialistSynthesis | None = None
    logistics_synthesis: SpecialistSynthesis | None = None
    llm_challenger: ChallengerJudgment | None = None
    llm_recommendation: RecommendationDecision | None = None

    @model_validator(mode='after')
    def terminal_contract(self):
        if self.status == 'awaiting_approval':
            if self.recommendation is None or self.approval is None:
                raise ValueError('Aguardando aprovação exige recomendação e solicitação humana')
        if self.status == 'blocked' and (self.recommendation is not None or self.approval is not None):
            raise ValueError('Fluxo bloqueado não pode recomendar ou solicitar aprovação de plano')
        return self
