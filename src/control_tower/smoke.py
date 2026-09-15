"""Verifica a prontidão do fixture didático INCIDENT-001, sem resolver o incidente."""
from datetime import date
from decimal import Decimal

from .models import Incident
from .tools import Tools


def check_demo(tools: Tools, incident: Incident) -> dict:
    checks = []

    def require(condition: bool, name: str):
        if not condition:
            raise ValueError(f"Smoke falhou: {name}. Confira o fixture do INCIDENT-001.")
        checks.append(name)

    require((incident.incident_id, incident.material, incident.plant, incident.supplier_id,
             incident.event_date, incident.delay_days) ==
            ("INCIDENT-001", "M42", "São Paulo", "SUP-ALPHA", date(2026, 10, 1), 7), "incident")
    orders = tools.get_orders(incident.material, incident.plant)
    require({o.order_id for o in orders} == {"PO-001", "PO-002", "PO-003"}, "related_orders")
    require(sum(o.quantity * o.material_units_per_product for o in orders) == 750, "demand")
    require([o.customer_order for o in orders if o.priority == "strategic"] == ["CO-001"], "strategic_customer")
    local = tools.get_stock("M42", "São Paulo")
    origin = tools.get_stock("M42", "Campinas")
    require((local.available_units, local.transferable_without_safety_stock_units) == (300, 200), "local_stock")
    require((origin.available_units, origin.transferable_without_safety_stock_units) == (500, 300), "transfer_stock")
    alternatives = tools.get_alternative_suppliers("M42", "SUP-ALPHA")
    require(any(s.supplier_id == "SUP-BETA" and s.capacity_units == 450 and s.lead_time_days == 2
                and s.unit_cost_brl == Decimal("145.00") for s in alternatives), "alternative_supplier")
    require(tools.get_supplier("SUP-ALPHA").unit_cost_brl == Decimal("100.00"), "baseline_cost")
    routes = tools.get_routes("Campinas", "São Paulo")
    require(any(r.service == "express" and r.lead_time_days == 1 and r.capacity_units == 500
                and r.cost_brl_per_trip == Decimal("18000.00") for r in routes), "express_route")
    require(any(r.service == "standard" and r.lead_time_days == 3 and r.capacity_units == 500
                and r.cost_brl_per_trip == Decimal("5000.00") for r in routes), "standard_route")
    require(tools.calculate_penalty("CO-001", 0) == 0 and
            tools.calculate_penalty("CO-001", 7) == Decimal("140000.00"), "hypothetical_penalty")
    policies = tools.policies
    require((policies.priority_customer_max_delay_days, policies.max_expedited_freight_brl,
             policies.manager_approval_threshold_brl) == (1, Decimal("50000"), Decimal("100000")), "policies")
    return {"checks_passed": checks, "demand_units": 750, "available_units": local.available_units,
            "shortfall_units": 450, "hypothetical_penalty_brl_7_days": "140000.00"}
