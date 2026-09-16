"""Recortes para projeção: mesmo grafo, execução interrompida antes de revelar a conclusão."""
from decimal import Decimal
import time

from langsmith import tracing_context

from .graph.state import WorkflowState
from .graph.workflow import build_graph
from .models import Incident
from .tools import Tools

VIEWS = ('summary', 'state', 'specialists', 'coordination', 'scenarios', 'challenger', 'recommendation', 'llm-decisions')
STOP_AFTER = {
    'summary': 'consolidation', 'state': 'consolidation', 'specialists': 'consolidation',
    'coordination': 'consolidation', 'scenarios': 'challenger', 'challenger': 'challenger',
    'recommendation': None, 'llm-decisions': None,
}


def money(value: Decimal) -> str:
    places = 0 if value == value.to_integral_value() else 2
    return f'{value:,.{places}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def load_view(tools: Tools, incident: Incident, view: str, **options) -> WorkflowState:
    if view not in VIEWS:
        raise ValueError('View desconhecida')
    stop = STOP_AFTER[view]
    with tracing_context(enabled=False):
        graph = build_graph(tools, **options)
        result = graph.invoke(WorkflowState(incident=incident), config={'recursion_limit': 20},
                              interrupt_after=[stop] if stop else None)
    return WorkflowState.model_validate(result)


def render_view(state: WorkflowState, view: str, tools: Tools) -> str:
    if state.blockers:
        return '\n'.join(['INVESTIGAÇÃO INCOMPLETA', *state.blockers,
                          'Ausência de evidência precisa aparecer como erro, não como conclusão.'])
    evidence = state.investigation
    if evidence is None:
        raise ValueError('Evidências ainda não consolidadas')
    supply, production, logistics = evidence.supply, evidence.production, evidence.logistics
    if view == 'llm-decisions':
        from textwrap import shorten, wrap
        def concise(label, value):
            return wrap(label + ': ' + shorten(' '.join(value.split()), width=160, placeholder='…'), width=94)
        findings = ([f.message for f in state.llm_challenger.findings] if state.llm_challenger else
                    [f.message for f in state.review.findings if not f.blocking])
        rationale = (state.llm_recommendation.rationale if state.llm_recommendation else
                     'Menor custo incremental entre cenários admissíveis; riscos exigem confirmação humana.')
        lines = [f'DECISÕES | {state.llm_mode} | ' + (state.llm_model or 'sem chamadas LLM'),
                 'Mesmas tools e cálculos; sínteses são consultivas, não novas evidências.']
        lines += concise('Supervisor', state.supervisor_reason)
        lines += ['Especialistas: ' + ', '.join(state.plan)]
        for name in ('supply', 'production', 'logistics'):
            synthesis = getattr(state, name + '_synthesis')
            value = synthesis.summary if synthesis else 'evidência tipada; síntese fixa/determinística'
            lines += [shorten(f'{name}: ' + ' '.join(value.split()), width=94, placeholder='…')]
        lines += ['Challenger (premissas / informação insuficiente):']
        lines += [shorten('  - ' + ' '.join(f.split()), width=94, placeholder='…') for f in findings[:3]]
        lines += concise('Justificativa', rationale)
        if state.recommendation:
            lines += [f'Cenário {state.review.selected_scenario} | custo R$ {money(state.recommendation.estimated_cost_brl)} | aprovação obrigatória',
                      f'{state.status} | actions_executed=false']
        lines += ['LLMs interpretam e julgam. Código determinístico mede e valida.']
        return '\n'.join(lines)
    if view == 'summary':
        demand = production.demand_units
        return '\n'.join([
            'EVIDÊNCIAS | INCIDENT-001 | unidades de M42; valores em BRL', '',
            f'São Paulo  disponível {supply.local.available_units} | demanda {demand} | déficit {max(0, demand-supply.local.available_units)}',
            f'Campinas   disponível {supply.origin.available_units} | safety stock {tools.get_safety_stock(state.incident.material, supply.origin.plant)}',
            f'           transferível sem romper o piso: {supply.origin.transferable_without_safety_stock_units}',
            f'Beta       capacidade {supply.alternative.capacity_units} | custo/un. {money(supply.alternative.unit_cost_brl)}',
            f'           prêmio/un. {money(supply.alternative.unit_cost_brl-supply.baseline.unit_cost_brl)} sobre Alpha',
            f'Logística  normal: {logistics.standard.lead_time_days} dias, {money(logistics.standard.cost_brl_per_trip)} / viagem',
            f'           expressa: {logistics.express.lead_time_days} dia, {money(logistics.express.cost_brl_per_trip)} / viagem', '',
            '3 ordens relacionadas; impacto por cliente ainda não avaliado.',
        ])
    if view == 'state':
        return '\n'.join([
            'SHARED STATE | retrato após a investigação', '',
            f'incident_id    {state.incident.incident_id}',
            f'plan           {" + ".join(state.plan)}',
            'canal          responsável       evidência',
            f'supply         Supply            SP {supply.local.available_units}; Campinas {supply.origin.available_units}',
            f'production     Production        {len(production.orders)} ordens; demanda {production.demand_units}',
            'logistics      Logistics         rotas normal e expressa',
            'investigation  Consolidação      3 resultados reunidos',
            f'status         {state.status}', '',
            'Cada especialista escreve somente em seu canal tipado.',
            'Mesmo incidente; responsabilidades distintas; nenhuma alocação executada.',
        ])
    if view == 'specialists':
        return '\n'.join([
            f'SPECIALISTS | {state.llm_mode} | evidências determinísticas', '',
            f'Supply      estoque + fornecedores: SP {supply.local.available_units}, Campinas {supply.origin.available_units}',
            f'            transferência preservando piso: {supply.origin.transferable_without_safety_stock_units}',
            f'Production  ordens + clientes: demanda {production.demand_units}',
            '            ' + ', '.join(o.order_id for o in production.orders),
            f'Logistics   rotas: normal {logistics.standard.lead_time_days} dias / expressa {logistics.express.lead_time_days} dia', '',
            'Tools controlam o acesso; agentes não leem CSV diretamente.',
            'Resultado = evidência tipada OU erro. Ainda não há avaliação de cenários.',
        ])
    if view == 'scenarios':
        if state.finance is None or state.review is None:
            raise ValueError('Comparação de cenários indisponível')
        actions = {'A': 'Esperar Alpha', 'B': 'Comprar Beta', 'C': 'Transferir expresso', 'D': 'Transferir/replanejar'}
        lines = ['CENÁRIOS | BRL incrementais | atrasos CO-001/002/003 (dias)', '',
                 f'{"ID":<2} {"Ação":<21} {"Custo":>7} {"Atrasos":>9} {"Multas":>7}  {"Restrição":<16} Admissível']
        for scenario in state.finance.scenarios:
            rejected = any(f.blocking and f.scenario_id in ('all', scenario.scenario_id) for f in state.review.findings)
            delays = '/'.join(str(d.delay_days) for d in scenario.deliveries)
            constraint = f'piso -{scenario.origin_safety_breach_units}' if scenario.origin_safety_breach_units else 'sem violação*'
            if rejected and not scenario.origin_safety_breach_units:
                constraint = 'revisar regras'
            lines.append(f'{scenario.scenario_id:<2} {actions[scenario.scenario_id]:<21} {money(scenario.total_cost_brl):>7} '
                         f'{delays:>9} {money(scenario.penalty_brl):>7}  {constraint:<16} {"não" if rejected else "sim*"}')
        lines += ['', '* Sob as regras do case; premissas ainda exigem confirmação.',
                  'Custo = prêmio de material + frete + multas; não é custo total do pedido.',
                  'customer_delay_days=3: maior atraso entre clientes, não o estratégico.',
                  'O cliente estratégico pode ter atraso zero (neste case: CO-001).',
                  'avoided_penalty é multa evitada; difere de economia líquida incremental.',
                  'confidence=0.65 é didático/fixo; não é probabilidade calibrada.']
        return '\n'.join(lines)
    if view == 'challenger':
        if state.finance is None or state.review is None:
            raise ValueError('Revisão indisponível')
        blocked = [f for f in state.review.findings if f.blocking]
        risks = [f for f in state.review.findings if not f.blocking]
        challenges = '; '.join(f'{f.scenario_id}: {f.message}' for f in blocked) or 'Sem violação detectada'
        from textwrap import wrap
        lines = ['CHALLENGER | revisão crítica', '',
                 f'Candidate Plan  Finance propõe cenário {state.finance.proposed_scenario}',
                 '      ↓', 'Assumptions     prazo Alpha; capacidade; custos de reposição/cancelamento',
                 '      ↓', 'Challenges']
        lines += ['  '+line for line in wrap(challenges, width=90)]
        lines += ['      ↓', f'Remaining Risks {len(risks)} pontos: prazo/capacidade, reposição e custos ausentes.',
                  '                Confirmações humanas continuam pendentes.', '',
                  'O Challenger não recalcula o cenário.',
                  'Ele testa se a conclusão ignora premissas, riscos ou evidências.',
                  'No código, também verifica consistência aritmética e temporal.',
                  'Revisar consistência não é construir uma nova simulação.']
        return '\n'.join(lines)
    if view == 'recommendation':
        recommendation = state.recommendation
        if recommendation is None or state.approval is None or state.finance is None:
            raise ValueError('Recomendação indisponível; requer revisão humana do problema')
        baseline = next(s for s in state.finance.scenarios if s.scenario_id == 'A')
        selected = next(s for s in state.finance.scenarios if s.scenario_id == state.review.selected_scenario)
        strategic = max((d.delay_days for d in selected.deliveries if d.strategic), default=0)
        return '\n'.join([
            'RECOMMENDATION → awaiting_approval', '',
            f'Cenário {selected.scenario_id} | custo incremental: R$ {money(recommendation.estimated_cost_brl)}',
            f'Multa evitada vs A: R$ {money(recommendation.avoided_penalty_brl)}',
            f'Economia líquida incremental vs A: R$ {money(baseline.total_cost_brl-selected.total_cost_brl)}',
            f'Maior atraso: {recommendation.customer_delay_days} dias | cliente estratégico: {strategic} dias',
            f'confidence = {recommendation.confidence} (didático/fixo, não calibrado)',
            f'Riscos pendentes: {len(recommendation.risks)}; confirmar premissas antes da decisão.', '',
            'approval_required = true', f'status = {state.status}',
            f'approval = {state.approval.status} | responsável: {state.approval.authority}',
            'actions_executed = false', '',
            'Uma recomendação válida não é uma decisão autorizada.',
        ])
    raise ValueError('View sem renderizador')


def show(tools: Tools, incident: Incident, view: str, **options) -> tuple[str, bool]:
    events = []
    started = time.perf_counter()
    if view == 'coordination':
        options['observer'] = lambda name, phase: events.append(f'{name:<14} {phase}')
    state = load_view(tools, incident, view, **options)
    if view == 'coordination' and not state.blockers:
        mode = 'sequencial' if options.get('sequential') else 'paralelo'
        delay = options.get('demo_delay_ms', 0)
        text = '\n'.join([f'COORDINATION | {mode} | espera artificial: {delay} ms/especialista', '',
                          *events, '', 'Join: só depois dos três resultados. Fluxo interrompido aqui.',
                          f'Tempo observado: {time.perf_counter()-started:.3f}s; não é benchmark.'])
    else:
        text = render_view(state, view, tools)
    return text, bool(state.blockers)
