"""Quality is a vector before it becomes a score. Read-only durable evidence."""
from typing import Literal
from uuid import UUID
from pydantic import Field
from ..models import Contract


class QualityAssessment(Contract):
    execution_id: UUID
    outcome_type: Literal['recommendation', 'degraded_recommendation', 'human_review_required'] | None
    fallback_used: bool | None
    human_review_required: bool | None
    approval_status: Literal['pending'] | None
    confidence: float | None = Field(default=None, ge=0, le=1)
    confidence_source: Literal['workflow_result_not_calibrated'] | None = None
    evidence_complete: bool | None = None
    policy_compliant: bool | None = None
    source: Literal['durable_result_and_events'] = 'durable_result_and_events'


def fallback_signal(execution, events):
    if (execution.result and execution.result.outcome == 'degraded_recommendation') or any(
            e.event_type == 'llm.fallback_activated' for e in events):
        return True
    # Missing/truncated legacy history must not turn absence into proof.
    contiguous = bool(events) and [e.sequence for e in events] == list(range(1, len(events)+1))
    if contiguous and events[0].event_type == 'execution.queued' and any(
            e.event_type in ('execution.completed', 'execution.failed') for e in events):
        return False
    return None


def assess_quality(execution, events) -> QualityAssessment:
    final = execution.result
    recommendation = final.recommendation if final else None
    return QualityAssessment(execution_id=execution.execution_id,
        outcome_type=final.outcome if final else None, fallback_used=fallback_signal(execution, events),
        human_review_required=final.approval.required if final else None,
        approval_status=final.approval.status if final else None,
        confidence=recommendation.confidence if recommendation else None,
        confidence_source='workflow_result_not_calibrated' if recommendation else None)
