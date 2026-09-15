"""Resumo de demonstração: ordem pedagógica estável; eventos ao vivo mostram a ordem real."""
from .graph.state import WorkflowState


def render(state: WorkflowState) -> str:
    lines = [f'\n=== {state.incident.incident_id} | mock | resumo ===',
             f'Supervisor: {state.supervisor_reason}', f'Plano: {", ".join(state.plan)}']
    for name in ('supply', 'production', 'logistics'):
        result = getattr(state, name)
        if result is None:
            lines.append(f'{name.title()}: não executado')
        elif result.error:
            lines.append(f'{name.title()}: ERRO — {result.error}')
        else:
            lines.append(f'{name.title()}: OK')
            if name == 'supply':
                lines.append(f'  SP={result.data.local.available_units}; Campinas={result.data.origin.available_units}; '
                             f'transferível sem romper piso={result.data.origin.transferable_without_safety_stock_units}; '
                             f'Beta={result.data.alternative.unit_cost_brl} BRL/unidade')
            elif name == 'production':
                lines.append(f'  {len(result.data.orders)} ordens relacionadas; demanda={result.data.demand_units}; impacto ainda não avaliado')
            else:
                lines.append(f'  padrão={result.data.standard.lead_time_days} dias/{result.data.standard.cost_brl_per_trip} BRL; '
                             f'expresso={result.data.express.lead_time_days} dia/{result.data.express.cost_brl_per_trip} BRL')
    lines.append('Consolidação: ' + ('3/3 evidências reunidas' if state.investigation else 'não concluída'))
    if state.finance:
        lines.append('Finance: cenário | material extra | frete | multa | total incremental BRL')
        for scenario in state.finance.scenarios:
            lines.append(f'  {scenario.scenario_id} | {scenario.material_premium_brl:.2f} | {scenario.freight_brl:.2f} | '
                         f'{scenario.penalty_brl:.2f} | {scenario.total_cost_brl:.2f}')
            for delivery in scenario.deliveries:
                lines.append(f'    {delivery.order_id}: entrega {delivery.delivery_date}, atraso {delivery.delay_days} dia(s), '
                             f'multa {delivery.penalty_brl:.2f} BRL')
        lines.append(f'Finance propõe: {state.finance.proposed_scenario}')
    if state.review:
        lines.append('Challenger:')
        for finding in state.review.findings:
            lines.append(f'  [{finding.scenario_id}] {"BLOQUEIA" if finding.blocking else "REVISAR"}: {finding.message}')
        lines.append(f'Cenário admissível selecionado: {state.review.selected_scenario}')
    if state.recommendation:
        lines.extend(['Recomendação estruturada:', state.recommendation.model_dump_json(indent=2)])
        lines.append('Confiança 0.65: valor didático conservador, não probabilidade calibrada.')
    if state.approval:
        lines.append(f'APROVAÇÃO HUMANA NECESSÁRIA | pending | responsável={state.approval.authority}')
    if state.blockers:
        lines.extend(f'BLOQUEADO: {message}' for message in state.blockers)
    lines.append(f'Estado final: {state.status}. Nenhuma ação operacional executada.')
    return '\n'.join(lines)
