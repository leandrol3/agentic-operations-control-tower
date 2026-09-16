# Snippets para projeção

Recortes do código real. Mostrar só quando esclarecem uma decisão;
não digitar nem navegar por diffs durante a aula. Números de linha referem-se à revisão atual.

## Shared state: canais de evidência

`src/control_tower/graph/state.py:122–131` — 10 linhas.

```python


class WorkflowState(Contract):
    incident: Incident
    plan: tuple[Specialist, ...] = ()
    supervisor_reason: str = ''
    supply: Result[SupplyEvidence] | None = None
    production: Result[ProductionEvidence] | None = None
    logistics: Result[LogisticsEvidence] | None = None
    investigation: Investigation | None = None
```

## Specialist output: Supply

`src/control_tower/agents/specialists.py:7–20` — 14 linhas.

```python
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
```

## Supervisor: plano explícito

`src/control_tower/agents/supervisor.py:6–17` — 12 linhas.

```python
    incident = state.incident
    if (incident.incident_id, incident.material, incident.plant, incident.supplier_id) != (
        'INCIDENT-001', 'M42', 'São Paulo', 'SUP-ALPHA'
    ):
        return {'blockers': ('Tipo de incidente fora do escopo desta demonstração',),
                'supervisor_reason': 'Sem plano conhecido; requer investigação humana'}
    return {'plan': ('supply', 'production', 'logistics'),
            'supervisor_reason': 'Investigar material, ordens/clientes e rotas; ramos independentes'}


def consolidate(state: WorkflowState) -> dict:
    """Join semântico após a barreira do grafo: ausência/erro impede Finance."""
```

## LangGraph: nós e transições

`src/control_tower/graph/workflow.py:113–134` — 22 linhas.

```python
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
```

## Paralelismo: esperar todos antes de consolidar

`src/control_tower/graph/workflow.py:123–137` — 15 linhas.

```python
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
```

## Finance: composição determinística de custo

`src/control_tower/scenarios.py:82–93` — 12 linhas.

```python
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
```

## Challenger: saldo, piso e política de frete

`src/control_tower/agents/challenger.py:55–70` — 16 linhas.

```python
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
```

## Recommendation: contrato existente

`src/control_tower/agents/interpretation.py:59–70` — 12 linhas.

```python
def template(state, scenario_id):
    selected = next(s for s in state.finance.scenarios if s.scenario_id == scenario_id)
    baseline = next(s for s in state.finance.scenarios if s.scenario_id == 'A')
    risks = [f.message for f in state.review.findings if f.scenario_id in ('all', scenario_id)]
    return Recommendation(
        incident_id=state.incident.incident_id, severity='high',
        recommended_action=f'Cenário {selected.scenario_id}: {selected.description}',
        estimated_cost_brl=selected.total_cost_brl,
        avoided_penalty_brl=max(0, baseline.penalty_brl - selected.penalty_brl),
        customer_delay_days=max(d.delay_days for d in selected.deliveries),
        confidence=0.65, risks=risks, approval_required=True,
    )
```
