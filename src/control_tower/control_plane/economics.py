"""Provider usage is measured, pricing configured, cost estimated (never accounting).

No Jaeger queries. Aggregate durable events across all attempts, including retries.
Costs cover recorded usage only; failed calls may have unreported/billable usage.
"""
import os
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID
from pydantic import Field
from ..models import Contract
from .quality import fallback_signal

Rate = Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]


class ModelPricing(Contract):
    input_per_million: Rate
    output_per_million: Rate
    currency: str = Field(pattern=r'^[A-Z]{3}$')


class PricingConfig(Contract):
    version: str = Field(min_length=1)
    models: dict[str, ModelPricing] = Field(default_factory=dict)


def load_pricing() -> PricingConfig:
    path = os.environ.get('CONTROL_TOWER_PRICING_FILE')
    return PricingConfig.model_validate_json(Path(path).read_text()) if path else PricingConfig(version='unconfigured')


class ExecutionEconomics(Contract):
    execution_id: UUID
    llm_calls: int | None = Field(description="Recorded request attempts, including artificial timeout demos; not billed calls")
    input_tokens: int | None
    output_tokens: int | None
    retry_count: int
    task_retry_count: int
    fallback_used: bool | None
    estimated_llm_cost: Decimal | None
    estimated_execution_cost: None = None  # infrastructure/labor/business cost not measured
    cost_currency: str | None
    cost_source: Literal['mock_no_usage', 'usage_unavailable', 'pricing_unconfigured', 'configured_pricing_estimate']
    usage_source: Literal['durable_provider_events', 'mock_no_usage', 'unavailable']
    usage_coverage: Literal['recorded_calls', 'partial_or_unavailable', 'not_applicable']
    cost_scope: Literal['recorded_usage_only_not_invoice'] = 'recorded_usage_only_not_invoice'
    pricing_version: str | None
    model: str | None


def assess_economics(execution, events, model: str | None, pricing: PricingConfig) -> ExecutionEconomics:
    requested = [e for e in events if e.event_type == 'llm.requested']
    completed = [e for e in events if e.event_type == 'llm.completed']
    mock = execution.llm_mode == 'mock'
    inputs = [e.input_tokens for e in completed if e.input_tokens is not None]
    outputs = [e.output_tokens for e in completed if e.output_tokens is not None]
    input_tokens = sum(inputs) if inputs and not mock else None
    output_tokens = sum(outputs) if outputs and not mock else None
    rate = pricing.models.get(model) if model else None
    source = 'mock_no_usage' if mock else 'usage_unavailable'
    cost = None
    # Never multiply partial input coverage by a complete output sum.
    paired = bool(completed) and len(inputs) == len(outputs) == len(completed)
    if not mock and paired:
        source = 'pricing_unconfigured'
        if rate:
            source = 'configured_pricing_estimate'
            cost = (Decimal(input_tokens)*rate.input_per_million +
                    Decimal(output_tokens)*rate.output_per_million) / Decimal(1_000_000)
    full_recorded = paired and len(requested) == len(completed) and not any(
        e.event_type in ('llm.failed', 'execution.interrupted') for e in events)
    return ExecutionEconomics(execution_id=execution.execution_id,
        llm_calls=0 if mock else len(requested) if requested else None,
        input_tokens=input_tokens, output_tokens=output_tokens,
        retry_count=sum(e.event_type == 'llm.retry' for e in events),
        task_retry_count=sum(e.event_type == 'execution.retry' for e in events),
        fallback_used=fallback_signal(execution, events), estimated_llm_cost=cost,
        cost_currency=rate.currency if cost is not None else None, cost_source=source,
        usage_source='mock_no_usage' if mock else 'durable_provider_events' if inputs or outputs else 'unavailable',
        usage_coverage='not_applicable' if mock else 'recorded_calls' if full_recorded else 'partial_or_unavailable',
        pricing_version=pricing.version if cost is not None else None,
        model=None if mock else model)
