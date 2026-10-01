"""Eventos NovaCore sintéticos: seed/data fixas, cinco categorias, nenhuma consulta externa."""
from collections import Counter
from datetime import datetime, timedelta, timezone
import random
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field

from ..models import Contract
from .models import Text

IncidentType = Literal['supplier_delay', 'production_deviation', 'logistics_delay', 'sla_risk', 'inventory_shortage']
MIX = dict(supplier_delay=120, production_deviation=85, logistics_delay=140, sla_risk=65, inventory_shortage=90)
SEED = 42
CREATED_AT = datetime(2026, 10, 1, 8, tzinfo=timezone.utc)
PLANTS = ('São Paulo', 'Campinas', 'Curitiba', 'Recife')


class IncidentEnvelope(Contract):
    incident_id: Text
    incident_type: IncidentType
    plant: Text
    severity: Literal['low', 'medium', 'high', 'critical']
    created_at: AwareDatetime
    business_priority: Annotated[int, Field(ge=1, le=5)]
    payload: dict[str, str | int | bool]


def generate_incidents(count: int = 500, seed: int = SEED) -> tuple[IncidentEnvelope, ...]:
    if isinstance(count, bool) or not 1 <= count <= 5000:
        raise ValueError('count deve estar entre 1 e 5000')
    rng = random.Random(seed)
    # Maiores restos: preserva o mix exato de 500 e distribui lotes menores proporcionalmente.
    sizes = {kind: count * weight // 500 for kind, weight in MIX.items()}
    ranked = sorted(MIX, key=lambda kind: -(count * MIX[kind] % 500))
    for kind in ranked[:count-sum(sizes.values())]:
        sizes[kind] += 1
    categories = [kind for kind, size in sizes.items() for _ in range(size)]
    rng.shuffle(categories)
    events = []
    for index, kind in enumerate(categories, 1):
        severity = rng.choice(('low', 'medium', 'high', 'critical'))
        payload = {
            'supplier_delay': {'supplier_id': 'SUP-ALPHA', 'material': 'M42', 'delay_days': rng.randint(1, 7)},
            'production_deviation': {'line_id': f'LINE-{rng.randint(1,4):02}', 'deviation_units': rng.randint(10,100)},
            'logistics_delay': {'shipment_id': f'SHIP-{index:04}', 'delay_hours': rng.randint(2,48)},
            'sla_risk': {'customer_order': f'CO-SYN-{index:04}', 'hours_to_sla': rng.randint(1,24)},
            'inventory_shortage': {'material': 'M42', 'missing_units': rng.randint(10,200)},
        }[kind]
        payload.update(synthetic=True, workload='reference_replay', reference_case_id='INCIDENT-001')
        events.append(IncidentEnvelope(
            incident_id=f'NC-S{seed}-{index:04}', incident_type=kind, plant=rng.choice(PLANTS),
            severity=severity, created_at=CREATED_AT + timedelta(seconds=(index-1)*5),
            business_priority={'critical': 1, 'high': 2, 'medium': 3, 'low': 5}[severity], payload=payload,
        ))
    return tuple(events)


def summarize(incidents: tuple[IncidentEnvelope, ...], seed: int) -> str:
    counts = Counter(i.incident_type for i in incidents)
    return '\n'.join(['NovaCore | incidentes sintéticos', f'count: {len(incidents)} | seed: {seed}',
                      *[f'{kind}: {counts[kind]}' for kind in MIX],
                      '5 categorias de chegada; batch usa replay do caso técnico INCIDENT-001.',
                      'Plantas/payloads sintéticos não são decisões de negócio já suportadas.'])
