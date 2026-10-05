# lesson-04-start — validação dos três refinamentos

Data: 2026-10-02. Escopo fechado: cliente Codex MCP, população GET /incidents e pricing datado.
Este relatório complementa a baseline histórica em `start-validation.md`.

## A. Baseline antes das alterações

- Branch: `codex/lesson-04-start`; commit `7ecd4b3`; working tree limpo.
- Default: **365 passed, 19 skipped em 13.29 s**.
- Todas as integrações: **384 passed, 0 skipped em 18.06 s**.
- Não havia regressão preexistente. Nenhuma tag criada ou movida.

## B. MCP: launcher e Codex

Launcher: `scripts/start_lesson04_mcp.sh`, executável, independente do diretório corrente.
Inicia o mesmo servidor por stdio via Docker Compose exec -T. Não faz requests HTTP;
logs em stderr, protocolo em stdout. `DOCKER_BIN` opcional; fallback para Docker Desktop macOS.

Cliente real: Codex CLI **0.155.0-alpha.16.4**, instalado no aplicativo ChatGPT.
Conexão validada: **sim**, sessão `codex exec` efêmera, configuração temporária por `-c`:

```toml
[mcp_servers.novacore]
command = "/bin/bash"
args = ["/Users/leandrolopes/Documents/ChatGPT/Disciplina Mult-Agents/agentic-operations-control-tower/scripts/start_lesson04_mcp.sh"]
startup_timeout_sec = 30
```

Flags utilizadas: `--ephemeral --ignore-user-config --approve-for-me --json`.
Não foi alterada configuração global nem desabilitada aprovação. Uma primeira sessão read-only
conectou/descobriu tools, mas não permitiu aprovar chamadas (policy never). A sessão seguinte
usou a revisão automática normal e executou as três tools autorizadas.

Descoberta do catálogo MCP: submit_incident, get_execution_status, get_execution_result.
Chamadas efetivamente registradas como completed na sessão Codex:

| Tool | Evidência |
|---|---|
| submit_incident | created=true, queued, UUID 671c527e-35b1-4ccb-9ffc-482cabe48f0f |
| get_execution_status | completed, worker-b, 20.859 ms, awaiting_approval |
| get_execution_result | recommendation, mock, approval_required=true, pending, actions_executed=false |

O workflow não chamou OpenAI; o próprio cliente Codex utiliza seu serviço de modelo.
A UI Desktop e a sessão interativa `/mcp` não foram operadas neste ensaio:
**Codex interactive client not validated in this execution environment.**
O runbook inclui registro CLI, configuração equivalente, prompts e fallback SDK.

Demo 1A também validada com ClientSession real, tools/list e o novo launcher:
HTTP/MCP mesma identidade → mesmo UUID, created=false; segunda submissão MCP → outra execução.
Execuções concluídas em 1023.246 ms e 1279.836 ms, incluindo delay artificial de 1 s.
Resultado HTTP = MCP; recommendation/pending/actions=false.

## C. GET /incidents

Fluxo: API → IncidentCapability.list_incidents → CorrelatedStore.list_incidents.
Sem SQL no endpoint; sem alterar distributed/store.py, migrations ou idempotência.

Contrato público: incident_id, execution_id, version, status, outcome, approval_status,
created_at, completed_at. Um item por operação persistida, não por incident_id único.
`version=null`: valor original não disponível separadamente do hash; não reconstruído.
Timestamps reais; campos ainda não disponíveis ficam null. Sem IncidentState/payload/prompts.

Filtro status: queued/running/completed/failed. Limit padrão 20, faixa 1–100.
Ordenação: created_at DESC, execution_id DESC. Lista vazia [], inválido 422, store indisponível 503.
Sem filtro outcome, paginação ou nova tool MCP.

Resposta real a `GET /incidents?status=completed&limit=2` (primeiro item):

```json
{
  "incident_id": "L04-CODEX-VALIDATION",
  "execution_id": "671c527e-35b1-4ccb-9ffc-482cabe48f0f",
  "version": null,
  "status": "completed",
  "outcome": "recommendation",
  "approval_status": "pending",
  "created_at": "2026-10-02T20:10:53.046847Z",
  "completed_at": "2026-10-02T20:10:53.126666Z"
}
```

## D. Pricing

Versão `openai-public-pricing-2026-10-02`; reference_date `2026-10-02`.
Modelo gpt-4.1-mini; USD/milhão: input **0.40**, cached input **0.10**, output **1.60**.
Fonte: [OpenAI — gpt-4.1-mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini).
Configuração usa strings; cálculo usa Decimal. Sem cached_input_tokens persistidos,
nenhum desconto é aplicado: cached_input_discount_applied=false.
“Pricing capability is richer than current measurement capability.”

Histórico local ainda disponível: `0693fd13-9590-45cd-8c37-ecdc2a870fb6`.
6 chamadas registradas, 10117 input e 831 output, usage_coverage=recorded_calls:

```text
(10117 × 0.40 + 831 × 1.60) / 1000000 = USD 0.0053764
pricing_version: openai-public-pricing-2026-10-02
reference_date: 2026-10-02
cost_scope: recorded_usage_only_not_invoice
cached_input_discount_applied: false
```

Somente leitura histórica, sem nova chamada OpenAI. UUID não virou fixture obrigatória.
Sem histórico, demo mock e teste aritmético offline continuam reproduzíveis.
Mock confirmado: 0 calls, tokens/custo unavailable, cost_unavailable_reason=mock_no_usage.
Modelo desconhecido/ausente: sem custo inventado e motivo explícito (testes offline).
Provider usage = measured; Pricing = configured; Cost = estimated. Não é invoice,
agent cost, workflow cost, custo industrial ou Business Value.

## E. Testes e regressão

| Execução | Resultado |
|---|---|
| Testes focados antigos + novos | 48 passed em 1.31 s |
| Suíte default | **381 passed, 20 skipped em 13.89 s** |
| Integrações completas | **401 passed, 0 skipped em 17.96 s** |
| smoke mock | status ok; 13 checks |
| SDK boundary real | passou |
| Codex CLI MCP real | passou; limite interativo descrito acima |
| GET público e economics histórico/mock | passaram |

**17 novos casos**: 16 unitários/contrato/launcher, 1 integração PostgreSQL.
Cobre lista vazia, quatro estados, filtros inválidos, sanitização, limites, ordenação com empate,
idempotência, projeção pública, pricing Decimal, cached rate sem desconto, mock e modelo ausente.

Comandos de regressão (dependências lesson04 instaladas e stack ligada):

```bash
LLM_MODE=mock uv run pytest -q
LLM_MODE=mock LESSON02_INTEGRATION=1 LESSON03_INTEGRATION=1 LESSON03_TRACING_INTEGRATION=1 LESSON04_INTEGRATION=1 uv run pytest -q
LLM_MODE=mock uv run control-tower smoke
uv run --extra lesson04 python scripts/demo_lesson04.py boundary
```

No ensaio foi usado `--no-sync` após instalação, com cache temporário isolado.
Integrações cobrem Aulas 2/3/4 e tracing; preservam HTTP, MCP, Registry, Quality, Economics,
health/readiness, OTel, fallback, idempotência e human approval. Sem provider real nos testes.

## F. Arquivos alterados

- `scripts/start_lesson04_mcp.sh` (novo): launcher stdio.
- `scripts/demo_lesson04.py`: usa launcher e mostra metadata/razão de economics.
- `src/control_tower/api/models.py`: IncidentSummary.
- `src/control_tower/api/app.py`: GET /incidents.
- `src/control_tower/application.py`: método de listagem pública.
- `src/control_tower/runtime/store.py`: projeção SQL limitada/parametrizada.
- `src/control_tower/control_plane/economics.py`: metadata, tarifa cached e razões explícitas.
- `config/lesson04-pricing.json`: referência pública datada.
- `tests/test_lesson04_refinements.py` (novo): testes dos refinamentos.
- `tests/integration/test_lesson04_store.py`: integração real da listagem.
- `docs/course/lesson-04-start-runbook.md`: Demos 1A/1B, mini listagem, pricing e falas.
- `docs/course/lesson-04/refinement-validation.md` (novo): este relatório.

## G. Git e limites

Branch preservada: codex/lesson-04-start. Baseline 7ecd4b3 mantida; refinamento em novo commit
local, identificado por `git log -1 --oneline`. Sem push, sem criação/movimentação de tags.
Nenhuma mudança no grafo, agentes, tools determinísticas, tarefas/store congelados da Aula 2,
infraestrutura, migrations ou dependências. Sem expansão para Control Plane completo.
Stack temporária de validação encerrada sem remover volumes. Parar para revisão.
