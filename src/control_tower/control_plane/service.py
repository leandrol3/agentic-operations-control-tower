"""Collect -> Interpret -> Recommend. A read-only facade, outside the business graph."""
from datetime import datetime, timezone
from ..telemetry import tracing
from .collection import collect_stage
from .configuration import load_config
from .economics import load_pricing
from .registry import registry
from .contracts import AgentControlPlaneView, LifecycleTrigger, Priority
from .interpretation import (METRICS, metric_evidence, measure_goal, evaluate_slo, trend,
    business_value, lifecycle_triggers)
from .decision_engine import recommend


class UnknownAgent(LookupError):
    pass


class ControlPlane:
    def __init__(self, store, *, config=None, pricing=None, records=None):
        self.store = store
        self.records = records
        self.config = config or load_config()
        self.pricing = pricing or load_pricing()

    def evaluate(self, *, mode='mock', agent_id=None, samples=None, source='durable_history', now=None):
        with tracing.operation('control_plane evaluate'):
            config = self.config
            if mode not in ('mock', 'openai'):
                raise ValueError('Invalid mode')
            records = self.records if self.records is not None else registry(mode)
            if agent_id is not None:
                records = tuple(r for r in records if r.agent_id == agent_id)
                if not records:
                    raise UnknownAgent('Agent not found')
            if samples is None:
                samples = self.store.control_plane_samples(limit=2*config.window_size, mode=mode)
            # Unique executions and deterministic ordering; fixture and store use the same pipeline.
            if len({s.execution.execution_id for s in samples}) != len(samples):
                raise ValueError('Duplicate execution in cohort')
            samples = sorted((s for s in samples if s.execution.llm_mode == mode),
                key=lambda s: (s.created_at, s.execution.execution_id), reverse=True)[:2*config.window_size]
            now = now or datetime.now(timezone.utc)
            current, previous = samples[:config.window_size], samples[config.window_size:]
            models = {s.options.llm_model for s in samples}
            cohort_model = next(iter(models)) if mode == 'openai' and len(models) == 1 else None
            output = []
            for agent in records:
                recent_signals = [collect_stage(s, agent.agent_id, self.pricing) for s in current]
                older_signals = [collect_stage(s, agent.agent_id, self.pricing) for s in previous]
                metrics = {m:metric_evidence(m,current,recent_signals,config,source) for m in METRICS}
                old = {m:metric_evidence(m,previous,older_signals,config,source) for m in ('completion_rate','stage_llm_cost_usd')}
                # Model changes invalidate cost comparisons, not historical costs themselves.
                comparable = len({s.options.llm_model for s in samples}) == 1
                ct = trend(metrics['stage_llm_cost_usd'].observed,
                    old['stage_llm_cost_usd'].observed if comparable else None, config.trend_relative_tolerance)
                gt = trend(metrics['completion_rate'].observed,old['completion_rate'].observed,
                    config.trend_relative_tolerance,higher_is_better=True)
                goals = tuple(measure_goal(agent,g,metrics['completion_rate'],config,now) for g in agent.business_goals)
                slos = tuple(evaluate_slo(s, metrics[s.metric], agent.agent_id) for s in config.slos
                             if s.agent_id in ('*',agent.agent_id))
                triggers = lifecycle_triggers(agent,goals,slos,ct,metrics['stage_llm_cost_usd'],old['stage_llm_cost_usd'])
                if (metrics['completion_rate'].observed is not None and old['completion_rate'].observed is not None
                        and metrics['completion_rate'].observed < config.severe_completion_below
                        and old['completion_rate'].observed < config.severe_completion_below):
                    triggers += (LifecycleTrigger(agent_id=agent.agent_id, trigger_type='persistent_underperformance',
                        severity=Priority.CRITICAL, evidence=(old['completion_rate'], metrics['completion_rate'])),)
                view = AgentControlPlaneView(registry=agent,evidence_source=source,configuration_version=config.version,
                    pricing_version=self.pricing.version,pricing_reference_date=self.pricing.reference_date,
                    mode=mode,cohort_model=cohort_model,measured_at=now,window_size=config.window_size,sample_count=len(current),
                    goals=goals,slos=slos,quality=metrics['workflow_degraded_rate'],economics=metrics['stage_llm_cost_usd'],
                    latency=metrics['stage_latency_p95_ms'],cost_trend=ct,goal_trend=gt,
                    previous_goal=old['completion_rate'],previous_cost=old['stage_llm_cost_usd'],
                    business_value=business_value(current,source),triggers=triggers,recommendation=None,decision_note='')
                rec,note = recommend(view,config)
                output.append(view.model_copy(update={'recommendation':rec,'decision_note':note}))
            return output
