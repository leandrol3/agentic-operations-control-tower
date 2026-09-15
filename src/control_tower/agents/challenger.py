"""Revisão independente: consistência, políticas, premissas e evidência ausente."""
from datetime import timedelta
from decimal import Decimal

from ..graph.state import FinanceReport, Finding, Investigation, Review
from ..tools import Tools


def challenge(tools: Tools, evidence: Investigation, report: FinanceReport) -> Review:
    findings = []
    eligible = []
    if len(report.scenarios) != 4 or {s.scenario_id for s in report.scenarios} != {'A', 'B', 'C', 'D'}:
        return Review(selected_scenario=None, findings=(Finding(
            scenario_id='all', category='missing_information', blocking=True,
            message='Comparação A–D incompleta ou duplicada'),))
    orders = {o.order_id: o for o in evidence.production.orders}
    customers = {c.order_id: c for c in evidence.production.customers}
    for scenario in report.scenarios:
        rejected = False

        def flag(category, message, blocking=True):
            nonlocal rejected
            rejected = rejected or blocking
            findings.append(Finding(scenario_id=scenario.scenario_id, category=category,
                                    blocking=blocking, message=message))

        if scenario.total_cost_brl != scenario.material_premium_brl + scenario.freight_brl + scenario.penalty_brl:
            flag('inconsistency', 'Custo total não corresponde aos componentes')
        if scenario.penalty_brl != sum((d.penalty_brl for d in scenario.deliveries), Decimal('0')):
            flag('inconsistency', 'Multas agregadas inconsistentes')
        if len(scenario.deliveries) != len(orders) or {d.order_id for d in scenario.deliveries} != set(orders):
            flag('missing_information', 'Ordens sem avaliação de entrega ou duplicadas')
        for delivery in scenario.deliveries:
            order = orders.get(delivery.order_id)
            if order is None:
                flag('inconsistency', 'Ordem desconhecida')
                continue
            customer = customers[order.customer_order]
            expected_delay = max(0, (delivery.delivery_date - customer.delivery_date).days)
            if (delivery.customer_order != order.customer_order or delivery.due_date != customer.delivery_date
                    or delivery.strategic != (order.priority == 'strategic')):
                flag('inconsistency', f'{order.order_id}: vínculo ou prioridade divergente')
            if (not delivery.allocations or sum(a.units for a in delivery.allocations) !=
                    order.quantity * order.material_units_per_product):
                flag('inconsistency', f'{order.order_id}: alocação incompleta')
            elif delivery.production_date != max(order.production_date,
                                                 max(a.available_date for a in delivery.allocations)):
                flag('inconsistency', f'{order.order_id}: produção não respeita disponibilidade')
            if (delivery.delivery_date != delivery.production_date + timedelta(days=1)
                    or delivery.delay_days != expected_delay
                    or delivery.penalty_brl != tools.calculate_penalty(order.customer_order, expected_delay)):
                flag('inconsistency', f'{order.order_id}: datas ou multa inconsistentes')
            if order.priority == 'strategic' and expected_delay > tools.policies.priority_customer_max_delay_days:
                flag('policy', 'Atraso do cliente estratégico excede a política')
        local_used = sum(a.units for d in scenario.deliveries for a in d.allocations if a.source == 'local')
        origin_used = sum(a.units for d in scenario.deliveries for a in d.allocations if a.source == 'Campinas')
        if local_used > evidence.supply.local.available_units or origin_used != scenario.transferred_units:
            flag('inconsistency', 'Material contado em duplicidade ou transferência inconsistente')
        breach = max(0, scenario.transferred_units - evidence.supply.origin.transferable_without_safety_stock_units)
        if (scenario.origin_remaining_units != evidence.supply.origin.available_units - scenario.transferred_units
                or scenario.origin_safety_breach_units != breach):
            flag('inconsistency', 'Saldo de Campinas inconsistente')
        if breach:
            flag('policy', f'Transferência rompe safety stock de Campinas em {breach} unidades')
        if scenario.expedited and scenario.freight_brl > tools.policies.max_expedited_freight_brl:
            flag('policy', 'Frete expresso excede o limite')
        if scenario.total_cost_brl > tools.policies.manager_approval_threshold_brl:
            flag('policy', 'Custo requer escalonamento ao gerente', blocking=False)
        if not rejected:
            eligible.append(scenario)
    findings.extend([
        Finding(scenario_id='all', category='missing_information', blocking=False,
                message='Confirmar quantidade/prazo de Alpha e disponibilidade comercial de Beta/transportadora antes da decisão.'),
        Finding(scenario_id='all', category='assumption', blocking=False,
                message='Capacidade produtiva simplificada e reposição do safety stock local precisam de validação humana.'),
        Finding(scenario_id='all', category='assumption', blocking=False,
                message='Custos incrementais excluem material base, reposição de Campinas e eventual cancelamento de Alpha.'),
    ])
    selected = min(eligible, key=lambda s: (s.total_cost_brl, s.scenario_id)) if eligible else None
    return Review(findings=tuple(findings), selected_scenario=selected.scenario_id if selected else None)
