"""Real in-memory MCP transport, shared Maestro and isolated filesystem; no paid calls."""
import asyncio
from unittest.mock import MagicMock

import pytest

pytest.importorskip('mcp')
pytest.importorskip('psycopg')
from mcp.shared.memory import create_connected_server_and_client_session
from control_tower.mcp.server import create_server
from control_tower.cockpit.models import MaestroResponse, ReviewRequest
from control_tower.cockpit.assistance import KnowledgeCompiler
from test_cockpit import service


def test_maestro_mcp_shared_service_history_and_approval_boundary(service):
    candidate = KnowledgeCompiler(service).extract(service.operations('didactic')[0]['execution_id'], 'didactic')
    async def run():
        async with create_connected_server_and_client_session(
            create_server(MagicMock(), maestro_service_factory=lambda: service)
        ) as client:
            tools = await client.list_tools()
            assert {t.name for t in tools.tools} == {
                'submit_incident', 'get_execution_status', 'get_execution_result', 'ask_maestro'
            }
            assert next(t for t in tools.tools if t.name == 'ask_maestro').outputSchema
            first = await client.call_tool('ask_maestro', {'request': {'question': 'Como melhorar Supply?'}})
            assert not first.isError
            response = MaestroResponse.model_validate(first.structuredContent)
            assert response.plan.generated_by == 'mock-deterministic'
            assert response.plan.requires_human_approval and response.plan.status == 'proposed'
            assert candidate.id not in response.plan.knowledge_ids
            assert service.knowledge.get(candidate.id).validation_status == 'pending_review'
            service.knowledge.review(candidate.id, 'approved', ReviewRequest(
                reviewer='Revisor sintético', note='Somente teste didático de retrieval.', confirmed=True))
            second = await client.call_tool('ask_maestro', {'request': {
                'question': 'Que conhecimento aprovado sustenta a proposta?', 'session_id': response.session_id}})
            followup = MaestroResponse.model_validate(second.structuredContent)
            assert followup.session_id == response.session_id
            assert candidate.id in followup.plan.knowledge_ids
            assert len(service.knowledge.plans('didactic')) == 2
            assert service.views('didactic')[0].registry.lifecycle_state == 'active'
    asyncio.run(run())


def test_maestro_mcp_invalid_request_and_provider_errors_are_sanitized(service, monkeypatch):
    from control_tower.cockpit.llm import StructuredProvider
    async def run():
        async with create_connected_server_and_client_session(
            create_server(MagicMock(), maestro_service_factory=lambda: service)
        ) as client:
            bad = await client.call_tool('ask_maestro', {'request': {'question': 'x'}})
            assert bad.isError
            monkeypatch.setattr(StructuredProvider, 'generate', MagicMock(side_effect=RuntimeError('secret-key-detail')))
            failed = await client.call_tool('ask_maestro', {'request': {'question': 'Como melhorar Supply?'}})
            assert failed.isError
            assert 'secret-key-detail' not in str(failed.content)
            assert not service.knowledge.plans('didactic')
    asyncio.run(run())


def test_maestro_mcp_durable_does_not_reuse_didactic_knowledge(service):
    candidate = KnowledgeCompiler(service).extract(service.operations('didactic')[0]['execution_id'], 'didactic')
    service.knowledge.review(candidate.id, 'approved', ReviewRequest(
        reviewer='Revisor sintético', note='Somente teste didático de isolamento.', confirmed=True))
    async def run():
        async with create_connected_server_and_client_session(
            create_server(MagicMock(), maestro_service_factory=lambda: service)
        ) as client:
            result = await client.call_tool('ask_maestro', {'request': {
                'question': 'Como melhorar Supply?', 'source': 'durable'}})
            response = MaestroResponse.model_validate(result.structuredContent)
            assert response.plan.source == 'durable'
            assert not response.plan.knowledge_ids
    asyncio.run(run())


def test_http_and_mcp_use_same_maestro_contract(service):
    from fastapi.testclient import TestClient
    from control_tower.api.app import create_app
    body = {'question': 'Como melhorar Supply?', 'agent_id': 'supply', 'source': 'didactic'}
    with TestClient(create_app(service.settings, service.store, MagicMock())) as http:
        expected = MaestroResponse.model_validate(http.post('/maestro/chat', json=body).json())
    async def run():
        async with create_connected_server_and_client_session(
            create_server(MagicMock(), maestro_service_factory=lambda: service)
        ) as client:
            result = await client.call_tool('ask_maestro', {'request': body})
            actual = MaestroResponse.model_validate(result.structuredContent)
            assert actual.plan.diagnosis == expected.plan.diagnosis
            assert actual.plan.steps == expected.plan.steps
            assert actual.sources_consulted == expected.sources_consulted
            assert actual.plan.evidence == expected.plan.evidence
            assert actual.plan.knowledge_ids == expected.plan.knowledge_ids
    asyncio.run(run())
