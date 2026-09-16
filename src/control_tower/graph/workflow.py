"""Grafo finito: fan-out explícito, join de todos os ramos e parada humana obrigatória."""
from collections.abc import Callable
import time

from langgraph.graph import END, START, StateGraph
from langsmith import tracing_context

from ..agents import challenger, finance, specialists, supervisor, interpretation
from ..llm import Interpreter
from ..tools import Tools
from .state import Approval, LogisticsEvidence, ProductionEvidence, Result, SupplyEvidence, WorkflowState

SPECIALISTS = ('supply', 'production', 'logistics')


def route_supervisor(state: WorkflowState):
    return 'blocked' if state.blockers else list(state.plan)


def route_consolidation(state: WorkflowState):
    return 'blocked' if state.blockers else 'finance'


def route_finance(state: WorkflowState):
    return 'blocked' if state.blockers else 'challenger'


def route_review(state: WorkflowState):
    return 'recommendation' if not state.blockers and state.review and state.review.selected_scenario else 'blocked'


def build_graph(tools: Tools, *, sequential: bool = False, fail_specialist: str | None = None,
                demo_delay_ms: int = 0, observer: Callable[[str, str], None] | None = None,
                llm: Interpreter | None = None):
    if fail_specialist is not None and fail_specialist not in SPECIALISTS:
        raise ValueError('Especialista desconhecido para falha simulada')
    if not 0 <= demo_delay_ms <= 2000:
        raise ValueError('Latência didática deve estar entre 0 e 2000 ms')

    def notify(name, phase):
        if observer:
            observer(name, phase)

    def specialist_node(name):
        def node(state: WorkflowState):
            notify(name, 'início')
            try:
                if demo_delay_ms:
                    time.sleep(demo_delay_ms / 1000)
                if name == fail_specialist:
                    raise ValueError('Falha simulada pelo professor')
                data = getattr(specialists, name)(tools, state.incident)
                evidence_type = {'supply': SupplyEvidence, 'production': ProductionEvidence,
                                 'logistics': LogisticsEvidence}[name]
                result = Result[evidence_type](data=data)
                synthesis = interpretation.synthesize(llm, name, state.incident, result.data, state.llm_plan) if llm else None
            except (ValueError, OSError) as error:
                result = Result(error=str(error))
            notify(name, 'erro' if result.error else 'fim')
            update = {name: result}
            if llm and not result.error:
                update[name + '_synthesis'] = synthesis
            return update
        return node

    def finance_node(state: WorkflowState):
        try:
            return {'finance': finance.analyze(tools, state.incident, state.investigation)}
        except ValueError as error:
            return {'blockers': (f'Finance: {error}',)}

    def recommendation_node(state: WorkflowState):
        if llm:
            return interpretation.recommend(llm, state)
        return {'recommendation': interpretation.template(state, state.review.selected_scenario)}

    def supervisor_node(state: WorkflowState):
        update = interpretation.supervise(llm, state) if llm else supervisor.supervise(state)
        if llm:
            update.update(llm_mode='openai', llm_model=llm.model)
        return update

    def challenger_node(state: WorkflowState):
        review = challenger.challenge(tools, state.investigation, state.finance)
        if llm and review.selected_scenario:
            return interpretation.challenge(llm, state, review)
        return {'review': review}

    def human_approval(state: WorkflowState):
        if state.recommendation is None or not state.recommendation.approval_required:
            raise ValueError('Recomendação válida e aprovação humana obrigatórias')
        authority = 'manager' if state.recommendation.estimated_cost_brl > tools.policies.manager_approval_threshold_brl else 'operations_manager'
        return {'approval': Approval(authority=authority), 'status': 'awaiting_approval'}

    def blocked(state: WorkflowState):
        return {'status': 'blocked', 'blockers': state.blockers or ('Challenger não aprovou nenhum cenário para recomendação',)}

    def visible(name, function):
        def node(state: WorkflowState):
            notify(name, 'início')
            try:
                result = function(state)
            except ValueError as error:
                if not llm:
                    raise
                notify(name, 'erro')
                return {'blockers': (str(error),), 'status': 'blocked',
                        'llm_mode': 'openai', 'llm_model': llm.model}
            notify(name, 'fim')
            return result
        return node

    builder = StateGraph(WorkflowState)
    builder.add_node('supervisor', visible('supervisor', supervisor_node))
    for name in SPECIALISTS:
        builder.add_node(name, specialist_node(name))
    builder.add_node('consolidation', visible('consolidation', supervisor.consolidate))
    builder.add_node('finance', visible('finance', finance_node))
    builder.add_node('challenger', visible('challenger', challenger_node))
    builder.add_node('recommendation', visible('recommendation', recommendation_node))
    builder.add_node('human_approval', visible('human_approval', human_approval))
    builder.add_node('blocked', visible('blocked', blocked))
    builder.add_edge(START, 'supervisor')
    if sequential:
        builder.add_conditional_edges('supervisor', lambda s: 'blocked' if s.blockers else 'supply',
                                      {'blocked': 'blocked', 'supply': 'supply'})
        builder.add_edge('supply', 'production')
        builder.add_edge('production', 'logistics')
        builder.add_edge('logistics', 'consolidation')
    else:
        builder.add_conditional_edges('supervisor', route_supervisor,
                                      {n: n for n in (*SPECIALISTS, 'blocked')})
        # Lista significa esperar TODOS, não três arestas que podem disparar a junção separadamente.
        builder.add_edge(list(SPECIALISTS), 'consolidation')
    builder.add_conditional_edges('consolidation', route_consolidation, ['finance', 'blocked'])
    builder.add_conditional_edges('finance', route_finance, ['challenger', 'blocked'])
    builder.add_conditional_edges('challenger', route_review, ['recommendation', 'blocked'])
    builder.add_conditional_edges('recommendation', lambda s: 'blocked' if s.blockers else 'human_approval',
                                  ['blocked', 'human_approval'])
    builder.add_edge('human_approval', END)
    builder.add_edge('blocked', END)
    return builder.compile()


def run_workflow(tools: Tools, incident, **options) -> WorkflowState:
    initial = WorkflowState(incident=incident)
    # Mesmo com variáveis de tracing no ambiente do professor, mock continua offline.
    with tracing_context(enabled=False):
        result = build_graph(tools, **options).invoke(initial, config={'recursion_limit': 20})
    # O retorno do grafo é um dict; validar também o contrato terminal, não só as entradas dos nós.
    return WorkflowState.model_validate(result)
