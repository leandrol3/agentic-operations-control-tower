"""Contratos explícitos; dinheiro em BRL e quantidades em unidades de M42."""
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

NonNegative = Annotated[int, Field(ge=0)]
Money = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2)]

class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

class Supplier(Contract):
    supplier_id: str
    name: str
    material: str
    lead_time_days: NonNegative
    reliability_score: Annotated[float, Field(ge=0, le=1)]
    unit_cost_brl: Money
    capacity_units: NonNegative
    region: str

class Inventory(Contract):
    plant: str
    material: str
    quantity: NonNegative
    reserved_quantity: NonNegative
    safety_stock: NonNegative

    @model_validator(mode="after")
    def reservations_fit(self):
        if self.reserved_quantity > self.quantity:
            raise ValueError("Reserva não pode exceder estoque físico")
        return self

class ProductionOrder(Contract):
    order_id: str
    plant: str
    product: str
    quantity: Annotated[int, Field(gt=0)]
    material: str
    material_units_per_product: Annotated[int, Field(gt=0)]
    production_date: date
    customer_order: str
    priority: Literal["standard", "strategic"]

class CustomerOrder(Contract):
    order_id: str
    customer: str
    product: str
    quantity: Annotated[int, Field(gt=0)]
    delivery_date: date
    sla_penalty_brl_per_day: Money
    priority: Literal["standard", "strategic"]
    margin_brl: Money

class Carrier(Contract):
    carrier: str
    origin: str
    destination: str
    service: Literal["standard", "express"]
    lead_time_days: NonNegative
    capacity_units: Annotated[int, Field(gt=0)]
    cost_brl_per_trip: Money
    reliability: Annotated[float, Field(ge=0, le=1)]

class Policies(Contract):
    priority_customer_max_delay_days: NonNegative
    max_expedited_freight_brl: Money
    manager_approval_threshold_brl: Money

class Incident(Contract):
    incident_id: str
    event_date: date
    supplier_id: str
    material: str
    plant: str
    delay_days: Annotated[int, Field(gt=0)]
    description: str

class Stock(Contract):
    plant: str
    material: str
    available_units: NonNegative
    transferable_without_safety_stock_units: NonNegative

class Recommendation(Contract):
    incident_id: str
    severity: Literal["low", "medium", "high"]
    recommended_action: Annotated[str, Field(min_length=1)]
    estimated_cost_brl: Money
    avoided_penalty_brl: Money
    customer_delay_days: NonNegative
    confidence: Annotated[float, Field(ge=0, le=1)]
    risks: list[str]
    approval_required: Literal[True] = True
