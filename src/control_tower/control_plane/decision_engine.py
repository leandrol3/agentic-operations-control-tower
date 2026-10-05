"""Ordered, evidence-driven rules. Recommend only; never invoke a transition."""
import json
from uuid import NAMESPACE_URL, uuid5
from ..telemetry import tracing
from .contracts import Action, Priority, GoalStatus, EvaluationStatus as S, Trend, ControlPlaneRecommendation
from .registry import LifecycleState
from .lifecycle import can_transition


def recommend(view, config):
    with tracing.operation('decision engine'):
        # Administrative states are not proof of performance; never resume paused/retired agents.
        if view.registry.lifecycle_state != LifecycleState.ACTIVE:
            return None, 'No automatic resume/retirement proposal for non-ACTIVE agents'
        goal = view.goals[0]
        violations = [s for s in view.slos if s.status == S.VIOLATION]
        high = [s for s in violations if s.severity in (Priority.HIGH, Priority.CRITICAL)]
        action = None
        suggested = None
        evidence = []
        if (goal.actual is not None and view.previous_goal.observed is not None
                and goal.actual < config.severe_completion_below
                and view.previous_goal.observed < config.severe_completion_below):
            action, priority, suggested = Action.PAUSE, Priority.CRITICAL, LifecycleState.PAUSED
            reason = 'Technical completion below configured severe threshold in two consecutive windows'
            evidence = [goal.evidence.model_copy(update={'target':config.severe_completion_below}),
                        view.previous_goal.model_copy(update={'target':config.severe_completion_below})]
        elif len(high) >= config.review_high_violations:
            action, priority, suggested = Action.REVIEW, Priority.HIGH, LifecycleState.REVIEW
            reason = 'Multiple high-severity SLO violations require administrative review'
            evidence = [s.evidence for s in high]
        elif any(s.evidence.metric == 'workflow_degraded_rate' for s in violations):
            action, priority, suggested = Action.INTERVENE, Priority.HIGH, LifecycleState.REVIEW
            reason = 'Associated workflow degradation exceeds threshold; investigate, do not blame this agent alone'
            evidence = [s.evidence for s in violations if s.evidence.metric == 'workflow_degraded_rate']
        elif goal.status == GoalStatus.OFF_TARGET and view.cost_trend == Trend.DEGRADING:
            action, priority = Action.OPTIMIZE, Priority.MEDIUM
            reason = 'Recorded role cost increased while technical completion remains off target'
            evidence = [goal.evidence, view.previous_cost, view.economics]
        elif violations or goal.status == GoalStatus.OFF_TARGET:
            action, priority, suggested = Action.REVIEW, Priority.MEDIUM, LifecycleState.REVIEW
            reason = 'Goal miss or SLO violation requires review of evidence'
            evidence = [goal.evidence] + [s.evidence for s in violations]
        elif (all(g.status == GoalStatus.ON_TARGET for g in view.goals)
                and view.goal_trend == Trend.STABLE and view.cost_trend == Trend.STABLE
                and view.quality.observed == 0 and view.slos
                and view.cohort_model is not None and view.registry.model == view.cohort_model
                and {'completion_rate','stage_latency_p95_ms','stage_llm_cost_usd','workflow_degraded_rate'}
                    <= {s.evidence.metric for s in view.slos}
                and all(s.status == S.PASS for s in view.slos)):
            action, priority = Action.SCALE, Priority.LOW
            reason = ('Eligible to evaluate a controlled scale experiment; capacity, demand and provider quota '
                      'must be checked by a human. This does not prove more workers are needed')
            evidence = [goal.evidence, view.previous_goal, view.previous_cost] + [s.evidence for s in view.slos]
        if action is None:
            return None, 'No supported action: insufficient evidence, warning only, or no rule matched'
        if suggested is not None and not can_transition(view.registry.lifecycle_state, suggested):
            raise ValueError('Recommendation proposes invalid lifecycle transition')
        # Stable identity for same evidence/config/agent/action. Timestamp is not part of identity.
        identity = json.dumps({'agent':view.registry.agent_id, 'action':action.value,
            'state':view.registry.lifecycle_state.value, 'config':config.model_dump(mode='json'),
            'pricing_version':view.pricing_version, 'pricing_reference_date':str(view.pricing_reference_date),
            'evidence':[e.model_dump(mode='json') for e in evidence]}, sort_keys=True)
        return ControlPlaneRecommendation(recommendation_id=uuid5(NAMESPACE_URL, identity),
            agent_id=view.registry.agent_id, action=action, priority=priority,
            summary=f'{action.value.upper()}: {view.registry.name}', reason=reason, evidence=tuple(evidence),
            current_lifecycle_state=view.registry.lifecycle_state, suggested_lifecycle_state=suggested,
            generated_at=view.measured_at), 'Recommendation is not authorization'
