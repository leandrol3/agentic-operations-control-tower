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
    assert issubclass(client.responses.parse.call_args.kwargs["text_format"], schema)
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


# Final presentation refinement: identifiers, bounded conversation, honest value.
def test_exposure_reuses_capability_and_attention_is_backend_projection(service):
    snapshot = service.snapshot("didactic")
    assert snapshot["business_exposure"]["exposure_brl"] == "140000.00"
    assert snapshot["business_exposure"]["daily_penalty_brl"] == "20000.00"
    assert snapshot["business_exposure"]["realized"] is None
    assert snapshot["attention"]["agent_ids"] == ["supply"]
    assert snapshot["attention"]["count"] == snapshot["overview"]["attention_agents"]
    assert service.snapshot("durable")["business_exposure"]["exposure_brl"] is None


def test_chat_session_passes_bounded_history_and_changes_context(
    client, service, monkeypatch
):
    contexts = []
    original = StructuredProvider.generate

    def capture(self, schema, prompt, context, mock):
        contexts.append(context)
        return original(self, schema, prompt, context, mock)

    monkeypatch.setattr(StructuredProvider, "generate", capture)
    first = client.post(
        "/maestro/chat",
        json={
            "question": "Quem precisa de atenção?",
            "context": {
                "context_type": "agent",
                "agent_id": "supply",
                "source": "didactic",
            },
        },
    ).json()
    key = service.operations("didactic")[0]["execution_id"]
    for _ in range(8):
        response = client.post(
            "/maestro/chat",
            json={
                "question": "Explique as evidências anteriores",
                "session_id": first["session_id"],
                "context": {
                    "context_type": "execution",
                    "execution_id": key,
                    "source": "didactic",
                },
            },
        )
        assert response.status_code == 200
        assert response.json()["session_id"] == first["session_id"]
    assert contexts[0]["history"] == []
    assert contexts[1]["history"][0]["content"] == "Quem precisa de atenção?"
    assert len(contexts[-1]["history"]) == 12
    assert any(f["id"].startswith("context-execution:") for f in contexts[-1]["facts"])


@pytest.mark.parametrize(
    "kind,field,value",
    [
        ("execution", "execution_id", "00000000-0000-0000-0000-000000000000"),
        ("recommendation", "recommendation_id", "unknown"),
        ("knowledge", "knowledge_id", "unknown"),
    ],
)
def test_invalid_context_never_saves_plan(client, service, kind, field, value):
    before = len(service.knowledge.plans())
    response = client.post(
        "/maestro/chat",
        json={
            "question": "Explique este item",
            "context": {"context_type": kind, field: value},
        },
    )
    assert response.status_code in (404, 409)
    assert len(service.knowledge.plans()) == before


def test_recommendation_context_resolves_owner(client, service):
    rec = service.snapshot("didactic")["recommendations"][0]
    response = client.post(
        "/maestro/chat",
        json={
            "question": "Explique esta recomendação",
            "context": {
                "context_type": "recommendation",
                "recommendation_id": str(rec["recommendation_id"]),
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["plan"]["agent_id"] == rec["agent_id"]


def test_pending_context_content_excluded_from_facts(service):
    from control_tower.cockpit.conversation import resolve_context
    from control_tower.cockpit.models import MaestroContext

    item = candidate(service)
    facts, _ = resolve_context(
        service, MaestroContext(context_type="knowledge", knowledge_id=item.id)
    )
    assert "ainda não validado" in facts[0].text
    assert item.summary not in facts[0].text
    approve(service, item)
    facts, _ = resolve_context(
        service, MaestroContext(context_type="knowledge", knowledge_id=item.id)
    )
    assert item.summary in facts[0].text


def test_failed_provider_keeps_conversation_and_no_partial_plan(service, monkeypatch):
    from control_tower.cockpit.conversation import Conversations

    sessions = Conversations()
    req = MaestroRequest(question="Como melhorar Supply?")
    first = sessions.chat(service, req)
    before = len(service.knowledge.plans())
    history = list(sessions.sessions[first["session_id"]]["history"])

    def fail(*args, **kwargs):
        raise TimeoutError("provider")

    monkeypatch.setattr(StructuredProvider, "generate", fail)
    with pytest.raises(TimeoutError):
        sessions.chat(
            service, req.model_copy(update={"session_id": first["session_id"]})
        )
    assert sessions.sessions[first["session_id"]]["history"] == history
    assert len(service.knowledge.plans()) == before
    assert not sessions.sessions[first["session_id"]]["lock"].locked()


def test_session_capacity_and_duplicate_request_guard(service):
    from control_tower.cockpit.conversation import Conversations

    sessions = Conversations(capacity=1)
    req = MaestroRequest(question="Como melhorar Supply?")
    first = sessions.chat(service, req)
    entry = sessions.sessions[first["session_id"]]
    entry["lock"].acquire()
    try:
        with pytest.raises(ValueError):
            sessions.chat(
                service, req.model_copy(update={"session_id": first["session_id"]})
            )
        with pytest.raises(ValueError):
            sessions.chat(service, req)
    finally:
        entry["lock"].release()
    second = sessions.chat(service, req)
    assert list(sessions.sessions) == [second["session_id"]]


def test_usage_is_estimated_separately_from_workflow(service):
    from decimal import Decimal

    provider = StructuredProvider(
        Settings(mode="openai", api_key="unit-test"), client=MagicMock()
    )
    mock = Maestro(service).chat(MaestroRequest(question="Como melhorar Supply?"))[
        "plan"
    ]
    draft = PlanDraft(
        language="pt-BR",
        diagnosis=mock.diagnosis,
        objective=mock.objective,
        steps=mock.steps,
        evidence_refs=[e.id for e in mock.evidence],
        knowledge_ids=[],
        expected_result=mock.expected_result,
        risks=mock.risk,
    )
    provider.client.responses.parse.return_value = SimpleNamespace(
        output_parsed=draft.model_dump(),
        usage=SimpleNamespace(input_tokens=1000, output_tokens=200),
    )
    result = Maestro(service, provider).chat(
        MaestroRequest(question="Como melhorar Supply?")
    )
    usage = result["plan"].usage
    assert usage.input_tokens == 1000 and usage.output_tokens == 200
    assert Decimal(usage.estimated_cost) == Decimal("0.00072")
    assert usage.currency == "USD"
    assert service.snapshot("didactic")["overview"]["estimated_cost_usd"] is None


def test_missing_provider_does_not_break_control_plane(client, monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_MODE", "openai")
    monkeypatch.setenv("CONTROL_TOWER_ROOT", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(tmp_path / "missing"))
    response = client.post(
        "/maestro/chat", json={"question": "Quem precisa de atenção?"}
    )
    assert response.status_code == 503
    assert (
        "Maestro indisponível: provider LLM não configurado"
        in response.json()["detail"]
    )
    assert client.get("/cockpit/overview").status_code == 200


def test_read_only_cockpit_without_key_rejects_new_jobs(service, monkeypatch, tmp_path):
    monkeypatch.setenv("COCKPIT_READ_WITHOUT_LLM", "true")
    monkeypatch.setenv("LLM_MODE", "openai")
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(tmp_path / "missing"))
    enqueue = MagicMock()
    settings = service.settings.model_copy(
        update={"llm_mode": "openai", "control_tower_root": tmp_path}
    )
    with TestClient(create_app(settings, service.store, enqueue)) as c:
        response = c.post(
            "/incidents", json={"incident_id": "INCIDENT-001", "version": "test"}
        )
        assert response.status_code == 503
        enqueue.assert_not_called()
        assert c.get("/agents").status_code == 200


def test_maestro_provider_schema_limits_evidence_to_retrieved_ids():
    from control_tower.cockpit.models import Fact, grounded_plan_schema

    schema = grounded_plan_schema(
        [
            Fact(id="goal:supply", text="Meta de 90%", source="Registry"),
            Fact(id="slo:supply", text="Limite", source="SLO"),
        ]
    )
    assert schema.model_json_schema()["properties"]["evidence_refs"]["items"][
        "enum"
    ] == ["goal:supply", "slo:supply"]


def test_economics_context_resolves_displayed_exposure_without_savings(service):
    from control_tower.cockpit.conversation import resolve_context
    from control_tower.cockpit.models import MaestroContext

    facts, _ = resolve_context(service, MaestroContext(context_type="economics"))
    assert "140000.00" in facts[0].text and "Não é atraso confirmado" in facts[0].text
    facts, _ = resolve_context(
        service, MaestroContext(context_type="economics", source="durable")
    )
    assert "140000" not in facts[0].text and "indisponível" in facts[0].text
