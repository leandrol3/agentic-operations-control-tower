"""Plano explícito para o único tipo de incidente suportado nesta aula."""
from ..graph.state import Investigation, WorkflowState


def supervise(state: WorkflowState) -> dict:
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
    failures = []
    if state.plan != ('supply', 'production', 'logistics'):
        failures.append('Plano não contém os três especialistas necessários')
    for name in ('supply', 'production', 'logistics'):
        result = getattr(state, name)
        if result is None:
            failures.append(f'{name}: resultado ausente')
        elif result.error is not None:
            failures.append(f'{name}: {result.error}')
    if failures:
        return {'blockers': tuple(failures)}
    evidence = Investigation(supply=state.supply.data, production=state.production.data,
                             logistics=state.logistics.data)
    return {'investigation': evidence}
