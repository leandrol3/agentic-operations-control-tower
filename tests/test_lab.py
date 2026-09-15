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
    (tmp_path / '.env').write_text('LLM_MODE=openai\n')
    env = dict(os.environ)
    env.pop('LLM_MODE', None)
    result = subprocess.run([sys.executable, '-m', 'control_tower.main', 'doctor', '--root', str(tmp_path)],
                            env=env, text=True, capture_output=True)
    assert result.returncode == 2
    assert 'suporta LLM_MODE=mock' in result.stderr

def test_policy_values(tools):
    assert tools.policies.priority_customer_max_delay_days == 1
    assert tools.policies.max_expedited_freight_brl == Decimal('50000')
    assert tools.policies.manager_approval_threshold_brl == Decimal('100000')
