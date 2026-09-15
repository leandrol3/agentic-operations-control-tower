"""Especialistas mock: mesmas responsabilidades do desenho, sem LLM nem acesso direto a CSV."""
from ..graph.state import LogisticsEvidence, ProductionEvidence, SupplyEvidence
from ..models import Incident
from ..tools import Tools


def supply(tools: Tools, incident: Incident) -> SupplyEvidence:
    alternatives = tools.get_alternative_suppliers(incident.material, incident.supplier_id)
    beta = next((s for s in alternatives if s.supplier_id == 'SUP-BETA'), None)
    if beta is None:
        raise ValueError('Fornecedor alternativo SUP-BETA ausente; investigação incompleta')
    return SupplyEvidence(
        local=tools.get_stock(incident.material, incident.plant),
        origin=tools.get_stock(incident.material, 'Campinas'),
        baseline=tools.get_supplier(incident.supplier_id), alternative=beta,
    )


def production(tools: Tools, incident: Incident) -> ProductionEvidence:
    orders = tools.get_orders(incident.material, incident.plant)
    return ProductionEvidence(
        orders=orders, customers=tuple(tools.get_customer_order(o.customer_order) for o in orders),
        demand_units=sum(o.quantity * o.material_units_per_product for o in orders),
    )


def logistics(tools: Tools, incident: Incident) -> LogisticsEvidence:
    routes = tools.get_routes('Campinas', incident.plant)
    standard = next((r for r in routes if r.service == 'standard'), None)
    express = next((r for r in routes if r.service == 'express'), None)
    if standard is None or express is None:
        raise ValueError('Rotas standard/express ausentes; investigação incompleta')
    return LogisticsEvidence(standard=standard, express=express)
