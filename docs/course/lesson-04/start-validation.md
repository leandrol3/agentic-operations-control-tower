# lesson-04-start — relatório para revisão

Data local: 01/10/2026. Candidato implementado; aprovação do professor ainda pendente.

## A. Baseline

- Branch inicial: `codex/lesson-03-complete`.
- Commit inicial: `981d077fc4f3bd542971895dd11feb9a116f057d` (working tree limpo).
- `uv run --no-sync --extra lesson03 pytest`: **333 passed, 18 skipped, 13.10s**.
- As 18 integrações exigiam opt-in/infra. A baseline unitária estava verde; nenhum problema
  preexistente corrigido fora de escopo. O primeiro comando encontrou restrição de acesso ao
  cache uv do host; a repetição usou cache temporário e o ambiente já instalado, sem alterar código.
- Posteriormente TODAS as integrações antigas foram habilitadas e passaram na regressão final.

## B. Implementação

Criados:

```text
compose.lesson04.yaml
config/lesson04-pricing.json
docs/course/lesson-04-start-runbook.md
docs/course/lesson-04/start-validation.md
scripts/demo_lesson04.py
src/control_tower/application.py
src/control_tower/mcp/__init__.py
src/control_tower/mcp/server.py
src/control_tower/mcp/tools.py
src/control_tower/control_plane/__init__.py
src/control_tower/control_plane/registry.py
src/control_tower/control_plane/quality.py
src/control_tower/control_plane/economics.py
tests/test_lesson04.py
tests/integration/test_lesson04_store.py
```

Alterados: `AGENTS.md`, `README.md`, `docs/course/PROJECT_CONTEXT.md`, `pyproject.toml`,
`uv.lock`, `Dockerfile`, `src/control_tower/api/app.py`, `src/control_tower/runtime/store.py`.

Dependência direta nova: SDK oficial `mcp>=1.28,<2`, resolvido em **1.30.0**. Extra lesson04
inclui lesson03. Nenhuma versão preexistente no lockfile foi alterada. Transitivas novas:
attrs, cffi, cryptography, httpx-sse, jsonschema, jsonschema-specifications, pycparser, pyjwt,
python-multipart, pywin32 (Windows), referencing, rpds-py, sse-starlette.

**Migrações: nenhuma.** Consulta aditiva às opções JSONB existentes recupera o modelo persistido.
`distributed/store.py` permanece byte a byte congelado; nenhuma mudança em grafo, agents,
tools, modelos de negócio, dados, tasks, producer, idempotency, retry, fallback ou instrumentos OTel.
Nenhum teste anterior removido, editado ou enfraquecido. Runbooks das Aulas 1–3 intocados.

## C. Arquitetura

HTTP / MCP → **IncidentCapability** → producer existente → Redis/Celery → workers →
mesmo LangGraph → PostgreSQL. Resultado mantém aprovação humana e actions_executed=false.

- Submissão e consultas públicas extraídas da API; Pydantic público existente reutilizado.
- SDK MCP por stdio, processo da mesma imagem via `docker compose exec -T api ...`.
- Três tools; nenhum bypass da fila. HTTP→MCP com mesma identidade retorna mesmo UUID/created=false.
- Erros MCP de validação sanitizados; logs separados do stdout reservado ao protocolo.
- Registry estático tipado com sete agentes, owners e metas estruturadas explicitamente didáticas.
  Status registered não é liveness; model/execution_type refletem configuração atual.
  HTTP/MCP pertencem à capability; interface do agente é langgraph_node. Finance sem modelo.
- Quality deriva outcome/fallback/approval/confidence do histórico; evidence_complete e
  policy_compliant permanecem unknown. Confiança existente é didática, não calibrada.
- Economics agrega eventos duráveis, todas as tentativas. Não depende de Jaeger. Mock não tem
  tokens/custo. Pricing separado, Decimal, versão explícita; estimated_execution_cost desconhecido.
  Estimate cobre usage registrado, não cobrança nem custo total do workflow.
- O trace começa no MCP server, não no cliente stdio. Contexto real propaga pelo publisher
  já instrumentado; nenhum parent W3C remoto foi inventado.

## D. Demos e evidências observadas

Preparação/perfis/comandos completos: `../lesson-04-start-runbook.md`.

### Demo 1

```bash
uv run --extra lesson04 python scripts/demo_lesson04.py boundary
```

Ensaio com imagem final: HTTP `2e81af7e-296d-4ccc-8b49-674f7d30629c`, MCP
`ca065855-89dc-4864-a2ef-c690fecb0f48`; ambos completed, workers distintos,
**1328.9 ms / 1044.3 ms** (incluem delay artificial de 1000 ms; não benchmark).
Reenvio HTTP→MCP manteve UUID. Resultado público HTTP=MCP, approval=pending/actions=false.

Trace MCP: `ad37cc63c333f107fd881a2f924cb8f5`, **25 spans**. Relações parent/child verificadas:
`mcp tool submit_incident → messaging publish incident → messaging process incident → workflow`.

### Demo 2

```bash
uv run --extra lesson04 python scripts/demo_lesson04.py registry
uv run --extra lesson04 python scripts/demo_lesson04.py registry supply
```

7 registros, cada um com 1 meta; Supply mostra stock/supplier/alternative tools, owners,
meta configurada e interface interna. Finance deterministic/model=null. 404 coberto.

### Demo 3

Depois de ativar o perfil artificial documentado:

```bash
uv run --extra lesson04 python scripts/demo_lesson04.py degraded
uv run --extra lesson04 python scripts/demo_lesson04.py quality
```

Ensaio degraded `a0e9381c-ae45-48bd-aed5-92d4c273bd90`: **1319.6 ms**, completed,
outcome=degraded_recommendation, fallback=true. Normal: recommendation/fallback=false.
Ambos approval=pending, human_review_required=true, evidence/policy=null, confidence=0.65 existente.
Timeout artificial antes da rede, retry limitado e continuidade determinística do case; nenhuma
chamada OpenAI real. Depois, runtime retornou a mock.

### Demo 4

```bash
uv run --extra lesson04 python scripts/demo_lesson04.py economics
```

Mock: llm_calls=0, tokens=null, estimated_llm_cost=null, cost_source=mock_no_usage.
Execução histórica com usage já persistido, consultada sem nova inferência:

```bash
uv run --extra lesson04 python scripts/demo_lesson04.py economics 0693fd13-9590-45cd-8c37-ecdc2a870fb6
```

Resultado observado: **6 chamadas, 10117 input_tokens, 831 output_tokens**, zero retries,
fallback=false. Sem pricing configurado: custo indisponível, pricing_unconfigured.
O UUID é evidência deste banco, não fixture portátil. Em outra máquina use uma execução própria
ou o caminho mock. A aritmética monetária foi validada com pricing fixture explicitamente fictício:
300 input + 50 output, tarifas 2/8 por milhão → **0.001 USD** estimado sobre usage registrado.
Esse valor não representa preço real de provider.

## E. Validação final

Com todos os opt-ins:

```bash
LLM_MODE=mock LESSON02_INTEGRATION=1 LESSON03_INTEGRATION=1 \
LESSON03_TRACING_INTEGRATION=1 LESSON04_INTEGRATION=1 \
uv run --extra lesson04 pytest -q
```

**384 passed, 0 skipped, 18.81s.** Total anterior 351 + 33 novos (32 unit/protocol + 1 PostgreSQL).
No ambiente de execução foi usado `--no-sync` após sync locked e UV_CACHE_DIR temporário;
isso não modifica seleção/semântica dos testes. Nenhum teste chamou OpenAI real.

| Verificação | Resultado |
|---|---|
| Aula 1 smoke | OK, mock explícito |
| Aula 1 INCIDENT-001 | cenário D / 12500.00 BRL / approval pending |
| Aula 2 batch local | 20/20, 2 threads, 0.114s; referência repetida |
| Aula 2 fila/workers/store | 20/20, 2 workers, 0.837s; nenhuma ação |
| Aula 3 API/health/readiness | OK; Redis down → ready 503, health vivo; recuperação → ready 200 |
| Aula 3 trace distribuído | teste backend Jaeger passou |
| MCP protocolo/client stdio real | submit/status/result, identidade compartilhada e contratos equivalentes |
| MCP trace | 25 spans; parent/child corretos até worker |
| Registry/goals | contratos, unicidade, owners, Finance e endpoints |
| Quality | normal/degraded/escalation/unknown/404/503 |
| Economics | mock, usage parcial, zero observado, pricing, retries/fallback e persistência |
| OTel desligado | HTTP e MCP completed: ~1293 / 1302 ms, com delay artificial 1s |
| Collector indisponível | HTTP e MCP completed: ~1026 / 1063 ms; Collector restaurado |
| Dependências antigas | nenhuma versão alterada |
| Comandos do runbook | 17 blocos bash validados sintaticamente em zsh |
| Git diff --check | limpo |

Durações são observações locais; não representam capacidade de produção.
O teste PostgreSQL novo usa schema isolado e provider scripted: usage é persistido/reaberto,
modelo vem das opções do store e custo é calculado sem telemetria. Schema de teste removido.
Dados das demos preservados; sem purge/down -v. Runtime criado para ensaio encerrado ao final.

## F. Limitações deliberadas

Registry local, metas não avaliadas automaticamente, Quality sem juiz/score único, pricing configurável
sem preços inventados, custo apenas do usage registrado e sem atribuição por agente. Sem captura
integral de evidências de compliance nem business value. Historical missing usage continua unknown.
MCP stdio local sem propagação de parent remoto/auth remota. Nenhum decision engine, SLO, lifecycle,
routing, autoscaling, K8s, dashboard, learning loop, auto-modify ou lesson-04-complete.

## G. Git / revisão

Branch final: `codex/lesson-04-start`. Um commit lógico local agrupa implementação, testes e docs;
identifique-o por `git log -1 --oneline` e compare com `981d077`.
Nenhum push, nenhuma criação/movimentação de tag. Tags anteriores preservadas:

- lesson-01-start: objeto `3d880c9ed7f9b679980bc17dc91660d8d79b2f81`.
- lesson-01-complete: objeto `b306d3a5f4437df25a902b11a368e45efd30ec0c`.
- lesson-03-complete: objeto `87808e64976ef978fdf8e4ddf109167e8c301c83`.

**Parecer técnico: candidato pronto para revisão do professor.** Nenhuma aprovação inferida.

## Output curto capturado — imagem final

### Boundary

```text
HTTP accepted: 2e81af7e-296d-4ccc-8b49-674f7d30629c | queued | worker=- | duration_ms=None
MCP protocol/runtime logs: artifacts/lesson04-mcp.log
MCP tools: submit_incident, get_execution_status, get_execution_result
HTTP → MCP same identity: same execution_id, created=false (durable idempotency)
MCP accepted: ca065855-89dc-4864-a2ef-c690fecb0f48 | queued | worker=- | duration_ms=None
MCP reads HTTP execution: 2e81af7e-296d-4ccc-8b49-674f7d30629c | running | worker=worker-a@b20f03d41b8f:9 | duration_ms=None
HTTP status: 2e81af7e-296d-4ccc-8b49-674f7d30629c | running | worker=worker-a@b20f03d41b8f:9 | duration_ms=None
HTTP status: 2e81af7e-296d-4ccc-8b49-674f7d30629c | completed | worker=worker-a@b20f03d41b8f:9 | duration_ms=1328.9128750000145
HTTP status: ca065855-89dc-4864-a2ef-c690fecb0f48 | running | worker=worker-b@54196136ef2d:9 | duration_ms=None
HTTP status: ca065855-89dc-4864-a2ef-c690fecb0f48 | completed | worker=worker-b@54196136ef2d:9 | duration_ms=1044.329292000043
HTTP = MCP public result | outcome=recommendation | approval=pending | actions=false
Same capability, different boundary.
```

### Registry

```text
AGENT WORKFORCE (current configured runtime; status is registration, not health)
supervisor      registered deterministic                goals=1
  role: Coordinate the investigation
supply          registered deterministic                goals=1
  role: Collect inventory and supplier evidence
production      registered deterministic                goals=1
  role: Identify orders and material demand
logistics       registered deterministic                goals=1
  role: Identify reference transport routes
finance         registered deterministic                goals=1
  role: Calculate deterministic scenario costs
challenger      registered deterministic                goals=1
  role: Challenge assumptions and validate scenarios
recommendation  registered deterministic                goals=1
  role: Produce an actionable recommendation for human review
Ownership/goals: registry supply. HTTP/MCP expose the system capability, not each agent.
```

### Quality

```text
QUALITY: completed is runtime status, not a quality score
normal: 2e81af7e-296d-4ccc-8b49-674f7d30629c
  outcome_type: recommendation
  fallback_used: False
  human_review_required: True
  approval_status: pending
  confidence: 0.65
  evidence_complete: None
  policy_compliant: None
degraded: a0e9381c-ae45-48bd-aed5-92d4c273bd90
  outcome_type: degraded_recommendation
  fallback_used: True
  human_review_required: True
  approval_status: pending
  confidence: 0.65
  evidence_complete: None
  policy_compliant: None
confidence is copied from workflow, not calibrated. Unknown evidence/policy stay null.
```

### Economics mock

```text
Execution: 2e81af7e-296d-4ccc-8b49-674f7d30629c
llm_calls: 0
input_tokens: unavailable
output_tokens: unavailable
retry_count: 0
task_retry_count: 0
fallback_used: False
estimated_llm_cost: unavailable
estimated_execution_cost: unavailable
cost_currency: unavailable
cost_source: mock_no_usage
usage_source: mock_no_usage
usage_coverage: not_applicable
pricing_version: unavailable
cost_scope: recorded_usage_only_not_invoice
outcome: recommendation
Provider usage = measured | Pricing = configured | Cost = estimated
```
