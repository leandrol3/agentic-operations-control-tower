"""Cockpit boundaries: no provider/network in unit tests, no ACT, source isolation."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
import json
import socket
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("celery")
pytest.importorskip("psycopg")
pytest.importorskip("yaml")
from fastapi.testclient import TestClient
from pydantic import ValidationError
from control_tower.api.app import create_app
from control_tower.runtime.settings import RuntimeSettings
from control_tower.settings import Settings
from control_tower.cockpit.presentation import CockpitService
from control_tower.cockpit.knowledge import KnowledgeStore
from control_tower.cockpit.assistance import Maestro, MaestroTools, KnowledgeCompiler
from control_tower.cockpit.llm import StructuredProvider, ProviderConfigurationError
from control_tower.cockpit.models import (
    MaestroRequest,
    ReviewRequest,
    KnowledgeDraft,
    PlanDraft,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def service(tmp_path, monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_ROOT", str(tmp_path / "knowledge"))
    monkeypatch.setenv(
        "CONTROL_TOWER_PRICING_FILE", str(ROOT / "config/lesson04-pricing.json")
    )
    monkeypatch.setenv(
        "CONTROL_PLANE_CONFIG_FILE", str(ROOT / "config/lesson04-control-plane.json")
    )
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    store = MagicMock()
    store.control_plane_samples.return_value = []
    store.list_incidents.return_value = []
    return CockpitService(
        store,
        RuntimeSettings(_env_file=None, llm_mode="mock", otel_enabled=False),
        KnowledgeStore(),
    )


@pytest.fixture
def client(service):
    with TestClient(create_app(service.settings, service.store, MagicMock())) as c:
        yield c


def candidate(service):
    key = service.operations("didactic")[0]["execution_id"]
    return KnowledgeCompiler(service).extract(key, "didactic")


def approve(service, item):
    return service.knowledge.review(
        item.id,
        "approved",
        ReviewRequest(
            reviewer="Professor", note="Evidências e limites revisados.", confirmed=True
        ),
    )


def test_supply_fixture_is_derived_and_separate(service):
    view = service.snapshot("didactic")
    supply = next(a for a in view["agents"] if a["registry"]["agent_id"] == "supply")
    assert float(supply["goals"][0]["actual"]) == 74
    assert float(supply["goals"][0]["target"]) == 90
    assert float(supply["goals"][0]["gap"]) == -16
    assert supply["goals"][0]["status"] == "off_target"
    assert supply["recommendation"]["action"] == "intervene"
    assert supply["sample_count"] == 50 and len(view["operations"]) == 6
    assert any(a["goals"][0]["status"] == "on_target" for a in view["agents"])
    assert view["overview"]["degraded_executions"] > 0 and view["alerts"]
    service.store.assert_not_called()
    assert service.store.method_calls == []


def test_durable_empty_is_unknown_not_fixture(service):
    view = service.snapshot("durable")
    assert not view["operations"] and not view["recommendations"]
    assert view["overview"]["goals"]["unknown"] == 7
    assert view["overview"]["estimated_cost_usd"] is None
    assert all(a["goals"][0]["actual"] is None for a in view["agents"])


@pytest.mark.parametrize(
    "endpoint",
    ["/cockpit/overview", "/cockpit/reports/summary", "/cockpit/alerts", "/knowledge"],
)
def test_public_read_routes(client, endpoint):
    assert client.get(endpoint).status_code == 200
    assert client.get(endpoint + "?source=production").status_code == 422


def test_extract_persists_pending_markdown_provenance_and_raw(service):
    item = candidate(service)
    assert item.validation_status == "pending_review" and item.source == "didactic"
    saved = KnowledgeStore(service.knowledge.root).get(item.id)
    assert saved.model_dump() == item.model_dump()
    path = service.knowledge.root / "wiki" / "lessons" / f"{item.id}.md"
    assert path.read_text().startswith("---\n")
    assert (
        "## Observações fornecidas" in saved.content
        and "## Inferência proposta" in saved.content
    )
    assert saved.evidence and saved.generated_by == "mock-deterministic"
    raw = json.loads(
        (service.knowledge.root / "raw/executions" / f"{item.id}.json").read_text()
    )
    assert (
        raw["execution_id"] == item.source_execution
        and raw["business_outcome"] == "unknown"
    )
    assert not service.knowledge.list(status="approved")


def test_mock_offline_and_deterministic_content(service, monkeypatch):
    monkeypatch.setattr(
        socket,
        "create_connection",
        MagicMock(side_effect=AssertionError("network forbidden")),
    )
    a, b = candidate(service), candidate(service)
    assert a.id != b.id and a.content == b.content and a.evidence == b.evidence
    assert a.title == b.title
    p = Maestro(service).chat(MaestroRequest(question="Como melhorar Supply?"))["plan"]
    assert p.generated_by == "mock-deterministic"


@pytest.mark.parametrize("status", ["approved", "rejected"])
def test_review_explicit_persisted_once(service, status):
    item = candidate(service)
    req = ReviewRequest(
        reviewer="Professor", note="Revisão com limites didáticos.", confirmed=True
    )
    result = service.knowledge.review(item.id, status, req)
    assert result.validation_status == status and result.reviewer == "Professor"
    assert KnowledgeStore(service.knowledge.root).get(item.id).review_note == req.note
    with pytest.raises(ValueError):
        service.knowledge.review(item.id, "approved", req)
    with pytest.raises(ValueError):
        service.knowledge.create_candidate(result, {})


@pytest.mark.parametrize(
    "payload",
    [
        {"reviewer": "Professor", "note": "Revisado", "confirmed": False},
        {"reviewer": "   ", "note": "Revisado", "confirmed": True},
        {"reviewer": "Professor", "note": "   ", "confirmed": True},
    ],
)
def test_human_confirmation_and_meaningful_identity_required(payload):
    with pytest.raises(ValidationError):
        ReviewRequest.model_validate(payload)


def test_retrieval_excludes_pending_rejected_and_other_source(service):
    pending = candidate(service)
    approved = approve(service, candidate(service))
    rejected = candidate(service)
    service.knowledge.review(
        rejected.id,
        "rejected",
        ReviewRequest(reviewer="Professor", note="Não sustentado", confirmed=True),
    )
    tools = MaestroTools(service, "didactic", "supply")
    assert [i.id for i in tools.search_knowledge()] == [approved.id]
    with pytest.raises(ValueError):
        tools.get_knowledge_item(pending.id)
    assert not MaestroTools(service, "durable", "supply").search_knowledge()
    assert service.knowledge.list("estoque", status="approved") == [approved]


def test_maestro_consults_sources_evidence_no_act(service):
    approved = approve(service, candidate(service))
    pending = candidate(service)
    before = [v.registry for v in service.views("didactic")]
    response = Maestro(service).chat(
        MaestroRequest(question="Como posso melhorar o agente de Supply?")
    )
    plan = response["plan"]
    assert (
        response["language"] == "pt-BR"
        and "74" in plan.diagnosis
        and "90" in plan.diagnosis
    )
    assert {
        "get_agent",
        "get_agent_goals",
        "get_goal_measurements",
        "get_agent_quality",
        "get_agent_economics",
        "get_agent_business_value",
        "get_agent_lifecycle",
        "get_agent_slos",
        "get_agent_recommendations",
        "get_agent_executions",
        "search_knowledge",
        "get_knowledge_item",
    } <= set(response["sources_consulted"])
    assert approved.id in plan.knowledge_ids and pending.id not in plan.knowledge_ids
    assert plan.evidence and plan.status == "proposed" and plan.requires_human_approval
    assert len(plan.staff_assignments) == 7
    assert service.knowledge.get(pending.id).validation_status == "pending_review"
    assert before == [v.registry for v in service.views("didactic")]
    assert service.store.method_calls == []
    assert service.knowledge.plans("didactic")[0] == plan
    assert not service.knowledge.plans("durable")


class AlteringProvider:
    label = "structured-test-fixture"

    def __init__(self, **changes):
        self.changes = changes

    def generate(self, schema, prompt, context, mock):
        return schema.model_validate(mock | self.changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"selected_fact_ids": ["invented"]},
        {"related_items": ["unapproved-entity"]},
        {"language": "en-US"},
        {"summary": "Executei a transferência"},
    ],
)
def test_compiler_rejects_unsupported_generated_output(service, changes):
    key = service.operations("didactic")[0]["execution_id"]
    with pytest.raises((ValueError, ValidationError)):
        KnowledgeCompiler(service, AlteringProvider(**changes)).extract(key, "didactic")
    assert service.knowledge.list() == []


@pytest.mark.parametrize(
    "changes",
    [
        {"evidence_refs": ["invented"]},
        {"knowledge_ids": ["not-approved"]},
        {"diagnosis": "Implantei o novo agente"},
        {"language": "en-US"},
    ],
)
def test_maestro_rejects_unsupported_claims(service, changes):
    with pytest.raises((ValueError, ValidationError)):
        Maestro(service, AlteringProvider(**changes)).chat(
            MaestroRequest(question="Melhorar Supply")
        )
    assert not service.knowledge.plans()


@pytest.mark.parametrize("schema", [KnowledgeDraft, PlanDraft])
def test_real_mode_structured_parser_uses_schema_without_network(service, schema):
    client = MagicMock()
    recorder = AlteringProvider()

    def generate(s, p, c, m):
        client.responses.parse.return_value = SimpleNamespace(
            output_parsed=s.model_validate(m)
        )
        return StructuredProvider(
            Settings("openai", "test-model", "fixture-key"), client
        ).generate(s, p, c, m)

    recorder.generate = generate
    if schema is KnowledgeDraft:
        KnowledgeCompiler(service, recorder).extract(
            service.operations("didactic")[0]["execution_id"], "didactic"
        )
    else:
        Maestro(service, recorder).chat(MaestroRequest(question="Melhorar Supply"))
    assert client.responses.parse.call_args.kwargs["text_format"] is schema
    assert client.responses.parse.call_args.kwargs["model"] == "test-model"
    assert "português" in client.responses.parse.call_args.kwargs["input"][0]["content"]


def test_provider_refusal_and_missing_key_fail_clearly(service):
    with pytest.raises(ProviderConfigurationError, match="OPENAI_API_KEY"):
        StructuredProvider(Settings("openai")).generate(PlanDraft, "", {}, {})
    client = MagicMock()
    client.responses.parse.return_value = SimpleNamespace(output_parsed=None)
    with pytest.raises(ValueError, match="estruturada"):
        StructuredProvider(Settings("openai", "test", "fixture"), client).generate(
            PlanDraft, "", {}, {}
        )


def test_http_end_to_end_extract_review_then_retrieve(client, service):
    uid = service.operations("didactic")[0]["execution_id"]
    assert client.get("/cockpit/executions/" + uid).status_code == 200
    item = client.post("/knowledge/extract/" + uid).json()
    assert item["validation_status"] == "pending_review"
    assert client.get("/knowledge/" + item["id"]).json()["source_execution"] == uid
    assert (
        client.post("/knowledge/" + item["id"] + "/approve", json={}).status_code == 422
    )
    request = {
        "reviewer": "Professor",
        "note": "Evidências verificadas no LAB",
        "confirmed": True,
    }
    assert (
        client.post("/knowledge/" + item["id"] + "/approve", json=request).json()[
            "validation_status"
        ]
        == "approved"
    )
    assert (
        client.post("/knowledge/" + item["id"] + "/reject", json=request).status_code
        == 409
    )
    response = client.post(
        "/maestro/chat", json={"question": "O que aprendemos hoje?"}
    ).json()
    assert item["id"] in response["plan"]["knowledge_ids"]
    assert "Conhecimento validado" in response["plan"]["diagnosis"]


def test_http_missing_key_and_errors_do_not_leak(
    client, service, monkeypatch, tmp_path
):
    monkeypatch.setenv("LLM_MODE", "openai")
    monkeypatch.setenv("CONTROL_TOWER_ROOT", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(tmp_path / "absent"))
    response = client.post("/maestro/chat", json={"question": "Melhorar Supply"})
    assert response.status_code == 503 and "OPENAI_API_KEY" in response.json()["detail"]
    service.store.control_plane_samples.side_effect = RuntimeError(
        "secret DSN password"
    )
    response = client.get("/cockpit/overview?source=durable")
    assert response.status_code == 503 and "secret" not in response.text


def test_path_traversal_symlink_and_invalid_document(service, tmp_path):
    with pytest.raises(ValueError):
        service.knowledge._path("../escape")
    target = tmp_path / "external"
    target.mkdir()
    service.knowledge.root.mkdir()
    (service.knowledge.root / "wiki").symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError):
        candidate(service)


def test_related_graph_is_derived_from_approved_links(service):
    old = approve(service, candidate(service))
    new = candidate(service)
    assert new.related == [old.id]
    assert service.knowledge.overview("didactic")["links"] == [
        {"from": new.id, "to": old.id, "label": "relacionado a"}
    ]
    assert not service.knowledge.overview("durable")["items"]


def test_no_candidate_from_incomplete_execution(service, monkeypatch):
    monkeypatch.setattr(service, "execution", lambda *_: {"status": "running"})
    with pytest.raises(ValueError, match="concluídas"):
        KnowledgeCompiler(service).extract("any", "durable")
    assert not service.knowledge.list()
