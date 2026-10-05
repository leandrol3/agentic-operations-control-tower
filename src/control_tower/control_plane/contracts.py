"""Read-only Control Plane contracts. No runtime state or private content exported."""
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal
from uuid import UUID
from pydantic import Field
from ..models import Contract
from .registry import AgentRecord, AgentId, LifecycleState


class GoalStatus(StrEnum):
    UNKNOWN = 'unknown'
    ON_TARGET = 'on_target'
    AT_RISK = 'at_risk'
    OFF_TARGET = 'off_target'


class EvaluationStatus(StrEnum):
    PASS = 'pass'
    WARN = 'warn'
    VIOLATION = 'violation'
    UNKNOWN = 'unknown'


class Trend(StrEnum):
    IMPROVING = 'improving'
    STABLE = 'stable'
    DEGRADING = 'degrading'
    UNKNOWN = 'unknown'


class Priority(StrEnum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class Action(StrEnum):
    SCALE = 'scale'
    OPTIMIZE = 'optimize'
    INTERVENE = 'intervene'
    REVIEW = 'review'
    PAUSE = 'pause'
    RETIRE = 'retire'


class Evidence(Contract):
    metric: str
    observed: Decimal | None
    target: Decimal | None = None
    unit: str
    scope: Literal['agent_stage', 'workflow']
    source: Literal['durable_history', 'didactic_fixture']
    execution_ids: tuple[UUID, ...] = ()
    note: str


class GoalMeasurement(Contract):
    agent_id: str
    goal_id: str
    target: Decimal
    actual: Decimal | None
    unit: str
    measurement_window: str
    gap: Decimal | None
    attainment: Decimal | None
    status: GoalStatus
    evidence_source: str
    evidence: Evidence
    measured_at: datetime


class AgentSLO(Contract):
    slo_id: str
    agent_id: AgentId | Literal['*'] = '*'
    metric: Literal['completion_rate', 'stage_latency_p95_ms', 'stage_llm_cost_usd', 'workflow_degraded_rate']
    target: Decimal = Field(ge=0, allow_inf_nan=False)
    operator: Literal['>=', '<=']
    warning_margin: Decimal = Field(ge=0, allow_inf_nan=False)
    window: Literal['latest_terminal_executions'] = 'latest_terminal_executions'
    severity: Priority


class SLOEvaluation(Contract):
    slo_id: str
    agent_id: str
    observed: Decimal | None
    target: Decimal
    operator: str
    status: EvaluationStatus
    severity: Priority
    evidence: Evidence


class BusinessValueAssessment(Contract):
    execution_id: UUID
    value_metric: str
    value_amount: Decimal | None
    currency_or_unit: str
    value_source: str
    evidence_level: Literal['recorded_proposal', 'measured_runtime', 'unavailable']
    status: Literal['potential', 'observed', 'unknown']
    note: str


class LifecycleTrigger(Contract):
    agent_id: str
    trigger_type: str
    severity: Priority
    evidence: tuple[Evidence, ...]
    recommended_review: Literal[True] = True


class ControlPlaneRecommendation(Contract):
    recommendation_id: UUID
    agent_id: str
    action: Action
    priority: Priority
    summary: str
    reason: str
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    current_lifecycle_state: LifecycleState
    suggested_lifecycle_state: LifecycleState | None
    requires_human_approval: Literal[True] = True
    generated_at: datetime


class AgentControlPlaneView(Contract):
    registry: AgentRecord
    evidence_source: Literal['durable_history', 'didactic_fixture']
    configuration_version: str
    pricing_version: str
    pricing_reference_date: date | None
    mode: Literal['mock', 'openai']
    cohort_model: str | None
    measured_at: datetime
    window_size: int
    sample_count: int
    goals: tuple[GoalMeasurement, ...]
    slos: tuple[SLOEvaluation, ...]
    quality: Evidence
    economics: Evidence
    latency: Evidence
    cost_trend: Trend
    goal_trend: Trend
    previous_goal: Evidence
    previous_cost: Evidence
    business_value: tuple[BusinessValueAssessment, ...]
    triggers: tuple[LifecycleTrigger, ...]
    recommendation: ControlPlaneRecommendation | None
    decision_note: str
