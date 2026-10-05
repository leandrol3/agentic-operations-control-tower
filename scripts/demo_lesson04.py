"""Small real clients, never a second workflow. Requires the lesson04 Compose stack.

HTTP uses urllib. MCP uses the official SDK and stdio through docker compose exec -T.
Artifacts keep IDs only so normal vs degraded survives a runtime profile change.
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
import time
from urllib.request import Request, urlopen
from uuid import uuid4
from control_tower.cockpit.localization import pt
from control_tower.cockpit.presentation import NAMES

FIELDS = {
    "outcome_type": "Tipo de resultado",
    "fallback_used": "Fallback usado",
    "human_review_required": "Revisão humana necessária",
    "approval_status": "Aprovação",
    "confidence": "Confiança não calibrada",
    "evidence_complete": "Evidências completas",
    "policy_compliant": "Conformidade com políticas",
    "llm_calls": "Chamadas LLM",
    "input_tokens": "Tokens de entrada",
    "output_tokens": "Tokens de saída",
    "retry_count": "Retries do LLM",
    "task_retry_count": "Retries da tarefa",
    "estimated_llm_cost": "Custo LLM estimado",
    "estimated_execution_cost": "Custo total da execução",
    "cost_currency": "Moeda",
    "cost_source": "Origem do custo",
    "usage_source": "Origem do consumo",
    "usage_coverage": "Cobertura do consumo",
    "pricing_version": "Versão do pricing",
    "reference_date": "Data de referência",
    "cached_input_discount_applied": "Desconto de cache aplicado",
    "cost_unavailable_reason": "Motivo de custo indisponível",
    "cost_scope": "Escopo do custo",
}

BASE = os.environ.get("AULA4_URL", "http://127.0.0.1:8000")
STATE = Path("artifacts/lesson04-demo.json")
LAUNCHER = Path(__file__).resolve().with_name("start_lesson04_mcp.sh")


def http(path, body=None):
    request = Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def remember(**values):
    old = json.loads(STATE.read_text()) if STATE.exists() else {}
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(old | values, indent=2) + "\n")


def saved(key):
    if not STATE.exists():
        raise SystemExit(
            "Execute primeiro: uv run --extra lesson04 python scripts/demo_lesson04.py boundary"
        )
    value = json.loads(STATE.read_text()).get(key)
    if not value:
        raise SystemExit(f"ID {key} ausente; execute a demo correspondente primeiro")
    return value


def status_line(label, data):
    print(
        f"{label}: {data['execution_id']} | {pt(data['status'])} | "
        f"worker={data.get('worker_id') or '-'} | duração_ms={data.get('duration_ms')}",
        flush=True,
    )


def wait(uid):
    previous = None
    for _ in range(120):
        state = http("/executions/" + uid)
        if state["status"] != previous:
            status_line("Status HTTP", state)
            previous = state["status"]
        if state["status"] == "completed":
            return state
        if state["status"] == "failed":
            raise RuntimeError("Execução falhou; consulte os eventos persistidos")
        time.sleep(0.5)
    raise TimeoutError("Execução não concluiu em 60 segundos; inspecione os workers")


async def boundary():
    from mcp import StdioServerParameters

    # No provider required. Both paths use the current container configuration.
    supply = http("/agents/supply")
    if supply["execution_type"] != "deterministic":
        raise SystemExit(
            "Demo boundary exige runtime mock. Volte ao perfil mock do runbook."
        )
    version = "boundary-" + uuid4().hex[:10]
    body = {"incident_id": "L04-HTTP", "version": version, "demo_delay_ms": 1000}
    accepted = http("/incidents", body)
    status_line("Aceito por HTTP", accepted)
    parameters = StdioServerParameters(command="/bin/bash", args=[str(LAUNCHER)])
    STATE.parent.mkdir(parents=True, exist_ok=True)
    print("Logs do protocolo MCP: artifacts/lesson04-mcp.log", flush=True)
    with Path("artifacts/lesson04-mcp.log").open("a") as logs:
        await boundary_session(parameters, accepted, body, logs)
    print("Mesma capacidade, fronteiras diferentes.")


async def boundary_session(parameters, accepted, body, logs):
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client

    async with stdio_client(parameters, errlog=logs) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            print(
                "Ferramentas MCP:",
                ", ".join(t.name for t in (await client.list_tools()).tools),
            )

            async def call(name, args):
                result = await client.call_tool(name, args)
                if result.isError:
                    raise RuntimeError("MCP tool failed: " + str(result.content))
                return result.structuredContent

            duplicate = await call("submit_incident", {"request": body})
            assert (
                duplicate["execution_id"] == accepted["execution_id"]
                and not duplicate["created"]
            )
            print(
                "HTTP → MCP: mesma identidade e execução, created=false (idempotência durável)"
            )
            other = await call(
                "submit_incident", {"request": body | {"incident_id": "L04-MCP"}}
            )
            status_line("Aceito por MCP", other)
            state = await call(
                "get_execution_status", {"execution_id": accepted["execution_id"]}
            )
            status_line("MCP consulta execução HTTP", state)
            # Poll asynchronously so MCP transport can keep processing.
            await asyncio.to_thread(wait, accepted["execution_id"])
            await asyncio.to_thread(wait, other["execution_id"])
            result = await call(
                "get_execution_result", {"execution_id": other["execution_id"]}
            )
            assert result == http(f"/executions/{other['execution_id']}/result")
            assert (
                result["approval_status"] == "pending"
                and not result["actions_executed"]
            )
            print(
                "HTTP = MCP resultado público | resultado="
                + pt(result["outcome"])
                + " | aprovação=pendente | ações=não executadas"
            )
            remember(normal=accepted["execution_id"], mcp=other["execution_id"])


def registry(agent, portuguese=False):
    # Default retained for callers of the earlier checkpoint's Python helper.
    # The CLI projects Portuguese without changing registry contracts.
    if portuguese:
        rows = [http("/agents/" + agent)] if agent else http("/agents")
        print("FORÇA DE TRABALHO IDENTIFICADA — metadata configurada, não saúde medida")
        print("Agente | Cadastro | Lifecycle | Tipo de execução | Metas")
        for row in rows:
            print(
                f"{NAMES[row['agent_id']]} | {pt(row['status'])} | {pt(row['lifecycle_state'])} | {pt(row['execution_type'])} | {len(row['business_goals'])}"
            )
            if agent:
                print(
                    "  ID:",
                    row["agent_id"],
                    "| versão:",
                    row["version"],
                    "| modelo:",
                    pt(row["model"]),
                )
                print(
                    "  Ferramentas:",
                    ", ".join(row["tools"]) or "Nenhuma ferramenta externa",
                )
                for goal in row["business_goals"]:
                    print(
                        "  Meta:", goal["name"], "| alvo:", goal["target"], goal["unit"]
                    )
        print("Cadastro ≠ Lifecycle ≠ Saúde do runtime ≠ Status da execução")
        print(
            "HTTP e MCP expõem a capability do sistema, não cada agente individualmente."
        )
        return
    if agent:
        print(json.dumps(http("/agents/" + agent), indent=2, ensure_ascii=False))
    else:
        print(
            "IDENTIFIED + MEASURABLE AGENTIC WORKFORCE (configured registry metadata)"
        )
        print(f"{'ID':15} {'STATUS':10} {'LIFECYCLE':10} {'EXECUTION TYPE':28} GOALS")
        for row in http("/agents"):
            print(
                f"{row['agent_id']:15} {row['status']:10} {row['lifecycle_state'].upper():10} {row['execution_type']:28} goals={len(row['business_goals'])}"
            )
            print("  ROLE: " + row["role"])
        print(
            "Registration status != Lifecycle state != Runtime health != Execution status"
        )
        print(
            "Ownership/goals: registry supply. HTTP/MCP expose the system capability, not each agent."
        )


def degraded():
    if http("/agents/supply")["execution_type"] == "deterministic":
        raise SystemExit(
            "Ative o perfil de falha artificial do runbook antes desta demo."
        )
    body = {
        "incident_id": "L04-DEGRADED",
        "version": "degraded-" + uuid4().hex[:10],
        "llm_failure": "timeout",
        "fallback": "deterministic_reference",
    }
    accepted = http("/incidents", body)
    status_line("Accepted", accepted)
    wait(accepted["execution_id"])
    remember(degraded=accepted["execution_id"])
    result = http("/executions/" + accepted["execution_id"] + "/result")
    assert result["outcome"] == "degraded_recommendation"
    print(
        "Timeout artificial antes da rede; continuidade determinística; sem chamada OpenAI real."
    )


def quality():
    print("QUALIDADE: concluída é status de runtime, não uma nota de qualidade")
    for key in ("normal", "degraded"):
        uid = saved(key)
        row = http(f"/executions/{uid}/quality")
        print(f"{key}: {uid}")
        for field in (
            "outcome_type",
            "fallback_used",
            "human_review_required",
            "approval_status",
            "confidence",
            "evidence_complete",
            "policy_compliant",
        ):
            print(f"  {FIELDS.get(field, field)}: {pt(row[field])}")
    print(
        "Confiança copiada do workflow, não calibrada. Evidências e conformidade desconhecidas permanecem nulas."
    )


def economics(uid):
    uid = uid or saved("normal")
    row = http(f"/executions/{uid}/economics")
    print("Execução:", uid)
    for key in (
        "llm_calls",
        "input_tokens",
        "output_tokens",
        "retry_count",
        "task_retry_count",
        "fallback_used",
        "estimated_llm_cost",
        "estimated_execution_cost",
        "cost_currency",
        "cost_source",
        "usage_source",
        "usage_coverage",
        "pricing_version",
        "reference_date",
        "cached_input_discount_applied",
        "cost_unavailable_reason",
        "cost_scope",
    ):
        missing = "Nenhum" if key == "cost_unavailable_reason" else "Não disponível"
        print(
            f"{FIELDS.get(key, key)}: {pt(row[key]) if row[key] is not None else missing}"
        )
    print("Resultado:", pt(http(f"/executions/{uid}/result")["outcome"]))
    print("Consumo do provider = medido | Pricing = configurado | Custo = estimado")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "demo", choices=["boundary", "registry", "degraded", "quality", "economics"]
    )
    parser.add_argument("id", nargs="?")
    args = parser.parse_args()
    if args.demo == "boundary":
        asyncio.run(boundary())
    elif args.demo == "registry":
        registry(args.id, portuguese=True)
    elif args.demo == "degraded":
        degraded()
    elif args.demo == "quality":
        quality()
    else:
        economics(args.id)


if __name__ == "__main__":
    main()
