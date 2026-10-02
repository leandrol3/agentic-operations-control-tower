"""Lifecycle metadata contract; no provider, transitions or runtime policy."""
import importlib.util
from pathlib import Path

import pytest
from pydantic import ValidationError

pytest.importorskip('mcp')
pytest.importorskip('celery')
pytest.importorskip('psycopg')
from fastapi.testclient import TestClient
from control_tower.api.app import create_app
from control_tower.control_plane.registry import AgentRecord, LifecycleState, registry
from test_lesson04 import settings, service, execution


def test_lifecycle_is_required():
    row = registry()[0].model_dump()
    del row['lifecycle_state']
    with pytest.raises(ValidationError) as error:
        AgentRecord.model_validate(row)
    assert error.value.errors()[0]['loc'] == ('lifecycle_state',)
    assert error.value.errors()[0]['type'] == 'missing'


@pytest.mark.parametrize('value', ['draft', 'pilot', 'active', 'review', 'paused', 'retired'])
def test_lifecycle_accepts_only_declared_states(value):
    row = AgentRecord.model_validate(registry()[0].model_dump() | {'lifecycle_state': value})
    assert isinstance(row.lifecycle_state, LifecycleState)
    assert row.model_dump(mode='json')['lifecycle_state'] == value
    assert row.status == 'registered'  # Registration is independent of lifecycle.


@pytest.mark.parametrize('value', ['registered', 'healthy', 'completed', 'pending', None])
def test_other_dimensions_are_not_lifecycle_states(value):
    with pytest.raises(ValidationError):
        AgentRecord.model_validate(registry()[0].model_dump() | {'lifecycle_state': value})


@pytest.mark.parametrize('mode', ['mock', 'openai'])
def test_all_agents_are_active_without_changing_existing_metadata(mode):
    records = registry(mode, 'configured-model')
    assert len(records) == 7
    for row in records:
        assert row.lifecycle_state is LifecycleState.ACTIVE
        assert row.status == 'registered'
        assert row.business_goals and row.business_owner and row.technical_owner
        assert row.version == 'lesson-01-complete' and row.interfaces == ('langgraph_node',)
        assert all(goal.target_source == 'didactic_configured_example' for goal in row.business_goals)
        if row.agent_id == 'finance' or mode == 'mock':
            assert row.execution_type == 'deterministic' and row.model is None
        else:
            assert row.execution_type == 'llm_with_deterministic_tools' and row.model == 'configured-model'


def test_api_exposes_required_enum_and_preserves_old_fields(settings, service):
    store, enqueue, _ = service
    old_fields = {'agent_id', 'name', 'role', 'business_owner', 'technical_owner', 'version',
        'status', 'execution_type', 'model', 'tools', 'interfaces', 'criticality',
        'business_goals', 'configuration_scope'}
    with TestClient(create_app(settings, store, enqueue)) as client:
        response = client.get('/agents')
        assert response.status_code == 200
        assert len(response.json()) == 7
        for row in response.json():
            assert set(row) == old_fields | {'lifecycle_state'}
            assert row['lifecycle_state'] == 'active' and row['status'] == 'registered'
            detail = client.get('/agents/' + row['agent_id'])
            assert detail.status_code == 200 and detail.json() == row
        schema = client.get('/openapi.json').json()['components']['schemas']
        assert 'lifecycle_state' in schema['AgentRecord']['required']
        assert schema['LifecycleState']['enum'] == ['draft', 'pilot', 'active', 'review', 'paused', 'retired']
    assert not store.mock_calls
    enqueue.assert_not_called()


def test_demo_projects_lifecycle_separately(monkeypatch, capsys):
    path = Path(__file__).resolve().parents[1] / 'scripts/demo_lesson04.py'
    spec = importlib.util.spec_from_file_location('lesson04_demo', path)
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    monkeypatch.setattr(demo, 'http', lambda path: [row.model_dump(mode='json') for row in registry()])
    demo.registry(None)
    output = capsys.readouterr().out
    assert all(label in output for label in ('ID', 'ROLE', 'STATUS', 'LIFECYCLE', 'EXECUTION TYPE', 'GOALS'))
    assert output.count('ACTIVE') == 7 and output.count('registered') == 7
    assert 'Registration status != Lifecycle state != Runtime health != Execution status' in output
