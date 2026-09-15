"""Simulação determinística, sem efetivar compras/transferências. Datas em dias civis."""
from datetime import timedelta
from decimal import Decimal

from .graph.state import Allocation, Delivery, Investigation, Scenario
from .models import Incident
from .tools import Tools

ASSUMPTIONS = (
    'Alpha entrega o déficit residual em event_date + delay_days; quantidade da compra original não cadastrada.',
    'Capacidade produtiva sem limite horário; lotes indivisíveis, sem antecipação nem entregas parciais.',
    'Consumo do safety stock local permitido nesta simulação; reposição de SP requer revisão humana.',
    'Pedidos alternativos substituem quantidade de Alpha sem multa de cancelamento; confirmar comercialmente.',
)


def simulate(tools: Tools, incident: Incident, evidence: Investigation, scenario_id: str) -> Scenario:
    supply, production, logistics = evidence.supply, evidence.production, evidence.logistics
    shortfall = max(0, production.demand_units - supply.local.available_units)
    transferred = bought = 0
    carrier = None
    descriptions = {
        'A': 'Esperar Alpha; alocar estoque local ao cliente estratégico',
        'B': 'Comprar déficit de Beta, substituindo Alpha',
        'C': 'Transferir déficit por expresso de Campinas',
        'D': 'Transferir até o piso de Campinas por rota padrão e replanejar; residual via Alpha',
    }
    if scenario_id not in descriptions:
        raise ValueError('Cenário desconhecido')
    if scenario_id == 'B':
        bought = shortfall
        if bought > supply.alternative.capacity_units:
            raise ValueError('Capacidade de Beta insuficiente')
        if supply.alternative.unit_cost_brl < supply.baseline.unit_cost_brl:
            raise ValueError('Este case pressupõe fornecedor alternativo mais caro')
    if scenario_id in ('C', 'D'):
        transferred = shortfall if scenario_id == 'C' else min(
            shortfall, supply.origin.transferable_without_safety_stock_units)
        carrier = logistics.express if scenario_id == 'C' else logistics.standard
        if transferred > supply.origin.available_units or transferred > carrier.capacity_units:
            raise ValueError('Transferência excede estoque ou capacidade de uma viagem')
    alpha_units = shortfall - bought - transferred
    if alpha_units > supply.baseline.capacity_units:
        raise ValueError('Capacidade de Alpha insuficiente para o residual')
    # Lotes de material, por disponibilidade. Cada unidade só é alocada uma vez.
    lots = [{'source': 'local', 'units': supply.local.available_units, 'date': incident.event_date}]
    if bought:
        lots.append({'source': supply.alternative.supplier_id, 'units': bought,
                     'date': incident.event_date + timedelta(days=supply.alternative.lead_time_days)})
    if transferred:
        lots.append({'source': 'Campinas', 'units': transferred,
                     'date': incident.event_date + timedelta(days=carrier.lead_time_days)})
    if alpha_units:
        lots.append({'source': incident.supplier_id, 'units': alpha_units,
                     'date': incident.event_date + timedelta(days=incident.delay_days)})
    lots.sort(key=lambda lot: (lot['date'], lot['source']))
    customers = {c.order_id: c for c in production.customers}
    orders = sorted(production.orders, key=lambda o: (o.priority != 'strategic',
                    customers[o.customer_order].delivery_date, o.order_id))
    deliveries = []
    for order in orders:
        remaining = order.quantity * order.material_units_per_product
        allocations = []
        for lot in lots:
            quantity = min(remaining, lot['units'])
            if quantity:
                allocations.append(Allocation(source=lot['source'], units=quantity, available_date=lot['date']))
                lot['units'] -= quantity
                remaining -= quantity
        if remaining:
            raise ValueError(f'Material insuficiente para {order.order_id}')
        day = max(order.production_date, max(a.available_date for a in allocations))
        delivery_day = day + timedelta(days=1)
        customer = customers[order.customer_order]
        delay = max(0, (delivery_day - customer.delivery_date).days)
        deliveries.append(Delivery(
            order_id=order.order_id, customer_order=customer.order_id, strategic=order.priority == 'strategic',
            allocations=tuple(allocations), production_date=day, delivery_date=delivery_day,
            due_date=customer.delivery_date, delay_days=delay,
            penalty_brl=tools.calculate_penalty(customer.order_id, delay),
        ))
    premium = bought * (supply.alternative.unit_cost_brl - supply.baseline.unit_cost_brl)
    freight = carrier.cost_brl_per_trip if transferred else Decimal('0')
    penalty = sum((d.penalty_brl for d in deliveries), Decimal('0'))
    breach = max(0, transferred - supply.origin.transferable_without_safety_stock_units)
    return Scenario(
        scenario_id=scenario_id, description=descriptions[scenario_id], deliveries=tuple(deliveries),
        material_premium_brl=premium, freight_brl=freight, penalty_brl=penalty,
        total_cost_brl=premium + freight + penalty, transferred_units=transferred,
        origin_remaining_units=supply.origin.available_units-transferred,
        origin_safety_breach_units=breach, expedited=bool(transferred and carrier.service == 'express'),
        assumptions=ASSUMPTIONS,
    )
