"""Deterministic measurements and thresholds. Unknown is not zero or success."""
from decimal import Decimal
from math import ceil
from ..telemetry import tracing
from .contracts import (Evidence, GoalMeasurement, GoalStatus, SLOEvaluation,
    EvaluationStatus as S, Trend, BusinessValueAssessment, LifecycleTrigger, Priority)

METRICS = {
    'completion_rate': ('percent', 'agent_stage', 'Technical node completion; not semantic correctness or acceptance'),
    'stage_latency_p95_ms': ('ms', 'agent_stage', 'Nearest-rank p95 of terminal node duration; no queue time'),
    'stage_llm_cost_usd': ('USD', 'agent_stage', 'Mean estimated recorded role usage; not full agent/workflow cost'),
    'workflow_degraded_rate': ('percent', 'workflow', 'Non-normal outcomes in associated workflows; not individual agent blame'),
}


def metric_evidence(metric, samples, signals, config, source):
    values = [r[{'completion_rate':'success','stage_latency_p95_ms':'latency',
                 'stage_llm_cost_usd':'cost','workflow_degraded_rate':'degraded'}[metric]] for r in signals]
    enough = len(values) >= config.min_samples and all(v is not None for v in values)
    observed = None
    if enough:
        numbers = [Decimal(str(v)) if not isinstance(v, bool) else Decimal(int(v)) for v in values]
        if metric == 'stage_latency_p95_ms':
            observed = sorted(numbers)[ceil(Decimal('0.95') * len(numbers))-1]
        else:
            observed = sum(numbers) / len(numbers)
            if metric.endswith('_rate'):
                observed *= 100
    unit, scope, note = METRICS[metric]
    return Evidence(metric=metric, observed=observed, unit=unit, scope=scope, source=source,
        execution_ids=tuple(s.execution.execution_id for s in samples),
        note=note + ('' if enough else '; unknown: insufficient samples or missing evidence'))


def measure_goal(agent, goal, evidence, config, now):
    with tracing.operation('goal evaluate'):
        actual = evidence.observed
        # Current registry's seven technical completion goals, not arbitrary future metrics.
        supported = goal.metric in {'alternative_evidence_coverage', 'investigation_plan_completed','supply_evidence_completed',
            'production_evidence_completed','logistics_evidence_completed',
            'deterministic_calculation_completed','challenge_completed','recommendation_completed'}
        if not supported or goal.unit != 'percent':
            actual = None
            evidence = evidence.model_copy(update={'observed': None, 'note': 'Unsupported goal metric; no measurement invented'})
        target = Decimal(str(goal.target))
        gap = actual-target if actual is not None else None
        status = GoalStatus.UNKNOWN if gap is None else (GoalStatus.ON_TARGET if gap >= 0 else
            GoalStatus.AT_RISK if gap >= -config.goal_warning_gap else GoalStatus.OFF_TARGET)
        return GoalMeasurement(agent_id=agent.agent_id, goal_id=goal.goal_id, target=target,
            actual=actual, gap=gap, attainment=actual/target if actual is not None and target else None,
            unit=goal.unit, measurement_window=f'latest_{config.window_size}_terminal_executions; per_execution aggregated',
            status=status, evidence_source=evidence.source, evidence=evidence.model_copy(update={'target':target}), measured_at=now)


def evaluate_slo(slo, evidence, agent_id):
    with tracing.operation('slo evaluate'):
        actual = evidence.observed
        status = S.UNKNOWN
        if actual is not None:
            distance = actual-slo.target if slo.operator == '>=' else slo.target-actual
            status = S.VIOLATION if distance < 0 else S.WARN if distance < slo.warning_margin else S.PASS
        return SLOEvaluation(slo_id=slo.slo_id, agent_id=agent_id, observed=actual, target=slo.target,
            operator=slo.operator, status=status, severity=slo.severity,
            evidence=evidence.model_copy(update={'target':slo.target}))


def trend(current, previous, tolerance, *, higher_is_better=False):
    if current is None or previous is None:
        return Trend.UNKNOWN
    delta = current-previous
    if abs(delta) <= abs(previous)*tolerance:
        return Trend.STABLE
    improving = delta > 0 if higher_is_better else delta < 0
    return Trend.IMPROVING if improving else Trend.DEGRADING


def business_value(samples, source):
    values = []
    for sample in samples:
        result = sample.execution.result
        rec = result.recommendation if result else None
        values.append(BusinessValueAssessment(execution_id=sample.execution.execution_id,
            value_metric='recommended_scenario_cost', value_amount=rec.estimated_cost_brl if rec else None,
            currency_or_unit='BRL', value_source=source+'.result.recommendation',
            evidence_level='recorded_proposal' if rec else 'unavailable', status='potential' if rec else 'unknown',
            note='Industrial scenario proposal contextualizes value; this is neither LLM cost nor realized savings'))
        duration = sample.execution.duration_ms if rec else None
        values.append(BusinessValueAssessment(execution_id=sample.execution.execution_id,
            value_metric='workflow_time_to_proposal_ms', value_amount=Decimal(str(duration)) if duration is not None else None,
            currency_or_unit='ms', value_source=source+'.execution.duration_ms',
            evidence_level='measured_runtime' if duration is not None else 'unavailable',
            status='observed' if duration is not None else 'unknown',
            note='Value proxy only: final attempt runtime to proposal; excludes queue/human decision and proves no improvement'))
        values.append(BusinessValueAssessment(execution_id=sample.execution.execution_id,
            value_metric='realized_business_value', value_amount=None, currency_or_unit='unknown',
            value_source='no_persisted_business_outcome', evidence_level='unavailable', status='unknown',
            note='Human acceptance, implementation and avoided exposure are not measured; no ROI or savings claim'))
    return tuple(values)


def lifecycle_triggers(agent, goals, slos, cost_trend, cost, previous_cost):
    result = []
    for goal in goals:
        if goal.status == GoalStatus.OFF_TARGET:
            result.append(LifecycleTrigger(agent_id=agent.agent_id, trigger_type='goal_miss',
                severity=Priority.MEDIUM, evidence=(goal.evidence,)))
    for slo in slos:
        if slo.status == S.VIOLATION:
            result.append(LifecycleTrigger(agent_id=agent.agent_id,
                trigger_type='quality_degradation' if slo.evidence.metric == 'workflow_degraded_rate' else 'slo_violation',
                severity=slo.severity, evidence=(slo.evidence,)))
    if cost_trend == Trend.DEGRADING:
        result.append(LifecycleTrigger(agent_id=agent.agent_id, trigger_type='cost_increase',
            severity=Priority.MEDIUM, evidence=(previous_cost, cost)))
    return tuple(result)
