import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from decimal import Decimal

import pytest
from pydantic import ValidationError
from control_tower.models import Inventory, Recommendation
from control_tower.tools import Tools

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def tools():
    return Tools(ROOT)

def test_incident_and_demand(tools):
    incident = tools.load_incident(ROOT / 'incidents/incident_001.json')
    orders = tools.get_orders(incident.material, incident.plant)
    assert incident.incident_id == 'INCIDENT-001'
    assert len(orders) == 3
    assert sum(o.quantity * o.material_units_per_product for o in orders) == 750
    assert sum(o.priority == 'strategic' for o in orders) == 1

def test_stock_tradeoff(tools):
    assert tools.get_stock('M42', 'São Paulo').available_units == 300
    other = tools.get_stock('M42', 'Campinas')
    assert other.available_units == 500
    assert other.transferable_without_safety_stock_units == 300

def test_alternatives_and_routes(tools):
    beta, = tools.get_alternative_suppliers('M42', 'SUP-ALPHA')
    assert beta.capacity_units == 450
    assert beta.unit_cost_brl - tools.get_supplier('SUP-ALPHA').unit_cost_brl == Decimal('45.00')
    routes = tools.get_routes('Campinas', 'São Paulo')
    assert {r.service for r in routes} == {'standard', 'express'}
    assert tools.get_routes('São Paulo', 'Campinas') == ()

@pytest.mark.parametrize('days,expected', [(0, '0'), (1, '20000'), (7, '140000')])
def test_penalty(tools, days, expected):
    assert tools.calculate_penalty('CO-001', days) == Decimal(expected)

@pytest.mark.parametrize('days', [-1, 1.5, True, '2'])
def test_invalid_penalty_input(tools, days):
    with pytest.raises(ValueError):
        tools.calculate_penalty('CO-001', days)

def test_unknown_ids_are_not_zero_stock(tools):
    with pytest.raises(ValueError):
        tools.get_stock('missing', 'São Paulo')
    with pytest.raises(ValueError):
        tools.get_supplier('missing')
    with pytest.raises(ValueError):
        tools.calculate_penalty('missing', 1)

def test_bad_reservations():
    with pytest.raises(ValidationError):
        Inventory(plant='X', material='M42', quantity=10, reserved_quantity=11, safety_stock=2)

@pytest.mark.parametrize('override', [{'confidence': 1.2}, {'estimated_cost_brl': -1}, {'approval_required': False}, {'unexpected': 1}])
def test_invalid_recommendation(override):
    values = dict(incident_id='INCIDENT-001', severity='high', recommended_action='Investigar',
                  estimated_cost_brl='100.00', avoided_penalty_brl='0', customer_delay_days=0,
                  confidence=0.8, risks=[])
    with pytest.raises(ValidationError):
        Recommendation(**(values | override))

def test_broken_reference(tmp_path):
    shutil.copytree(ROOT / 'data', tmp_path / 'data')
    path = tmp_path / 'data/production_orders.csv'
    path.write_text(path.read_text().replace('CO-001', 'CO-MISSING'))
    with pytest.raises(ValueError, match='Identificador desconhecido'):
        Tools(tmp_path)

def test_duplicate_stock(tmp_path):
    shutil.copytree(ROOT / 'data', tmp_path / 'data')
    path = tmp_path / 'data/inventory.csv'
    path.write_text(path.read_text() + 'São Paulo,M42,1,0,0\n')
    with pytest.raises(ValueError, match='duplicado'):
        Tools(tmp_path)

@pytest.mark.parametrize('command', ['doctor', 'incident', 'tools', 'smoke'])
def test_cli_offline(command, tmp_path):
    env = dict(os.environ, LLM_MODE='mock')
    env.pop('OPENAI_API_KEY', None)
    result = subprocess.run([sys.executable, '-m', 'control_tower.main', command, '--root', str(ROOT)],
                            cwd=tmp_path, env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)

def test_env_file_rejects_unsupported_provider(tmp_path):
    (tmp_path / '.env').write_text('LLM_MODE=unsupported\n')
    env = dict(os.environ)
    env.pop('LLM_MODE', None)
    result = subprocess.run([sys.executable, '-m', 'control_tower.main', 'doctor', '--root', str(tmp_path)],
                            env=env, text=True, capture_output=True)
    assert result.returncode == 2
    assert 'LLM_MODE deve ser mock ou openai' in result.stderr

def test_policy_values(tools):
    assert tools.policies.priority_customer_max_delay_days == 1
    assert tools.policies.max_expedited_freight_brl == Decimal('50000')
    assert tools.policies.manager_approval_threshold_brl == Decimal('100000')

@pytest.fixture
def demo_copy(tmp_path):
    """Cópia descartável: falhas da demo nunca alteram o fixture oficial."""
    shutil.copytree(ROOT / 'data', tmp_path / 'data')
    shutil.copytree(ROOT / 'incidents', tmp_path / 'incidents')
    return tmp_path


def run_demo(command, root):
    return subprocess.run(
        [sys.executable, '-m', 'control_tower.main', command, '--root', str(root)],
        env=dict(os.environ, LLM_MODE='mock'), text=True, capture_output=True,
    )


def test_smoke_reports_evidence_not_confirmed_impact():
    result = run_demo('smoke', ROOT)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['related_orders'] == 3
    assert report['impact_status'] == 'not_assessed'
    assert 'affected_orders' not in report
    assert report['demand_units'] == 750
    assert report['shortfall_units'] == 450
    assert report['hypothetical_penalty_brl_7_days'] == '140000.00'
    assert len(report['checks_passed']) == 12
    assert {'express_route', 'alternative_supplier', 'transfer_stock', 'policies'} <= set(report['checks_passed'])


@pytest.mark.parametrize('table,marker', [
    ('suppliers', 'SUP-BETA'),
    ('inventory', 'Campinas'),
    ('carriers', 'ExpressCo'),
    ('carriers', 'RoadCo'),
    ('production_orders', 'PO-003'),
])
def test_incomplete_demo_rejected_by_smoke(demo_copy, table, marker):
    path = demo_copy / f'data/{table}.csv'
    lines = path.read_text(encoding='utf-8').splitlines()
    path.write_text('\n'.join(line for line in lines if marker not in line) + '\n', encoding='utf-8')
    # Estes subconjuntos ainda satisfazem schemas/referências, mas não a demo oficial.
    assert run_demo('doctor', demo_copy).returncode == 0
    result = run_demo('smoke', demo_copy)
    assert result.returncode == 2
    assert not result.stdout
    assert 'Smoke falhou' in result.stderr or 'Estoque não cadastrado' in result.stderr


@pytest.mark.parametrize('table', ['suppliers', 'inventory', 'production_orders', 'customer_orders', 'carriers'])
def test_incomplete_empty_table(demo_copy, table):
    path = demo_copy / f'data/{table}.csv'
    path.write_text(path.read_text(encoding='utf-8').splitlines()[0] + '\n', encoding='utf-8')
    result = run_demo('smoke', demo_copy)
    assert result.returncode == 2
    assert 'Fixture incompleto' in result.stderr
    assert not result.stdout


@pytest.mark.parametrize('file', [
    'data/suppliers.csv', 'data/inventory.csv', 'data/production_orders.csv',
    'data/customer_orders.csv', 'data/carriers.csv', 'data/policies.json',
    'incidents/incident_001.json',
])
def test_incomplete_missing_file(demo_copy, file):
    (demo_copy / file).unlink()
    result = run_demo('smoke', demo_copy)
    assert result.returncode == 2
    assert not result.stdout
    assert 'error:' in result.stderr


def test_incomplete_header(demo_copy):
    path = demo_copy / 'data/carriers.csv'
    path.write_text('carrier,origin\n', encoding='utf-8')
    result = run_demo('smoke', demo_copy)
    assert result.returncode == 2
    assert 'Cabeçalho inválido' in result.stderr


def test_temporal_convention_requires_day_after_production(demo_copy):
    path = demo_copy / 'data/customer_orders.csv'
    path.write_text(path.read_text(encoding='utf-8').replace('2026-10-03', '2026-10-02'), encoding='utf-8')
    with pytest.raises(ValueError, match='um dia de transporte'):
        Tools(demo_copy)


def test_tools_labels_related_orders():
    report = json.loads(run_demo('tools', ROOT).stdout)
    assert len(report['related_orders']) == 3
    assert report['impact_status'] == 'not_assessed'
    assert 'orders' not in report
