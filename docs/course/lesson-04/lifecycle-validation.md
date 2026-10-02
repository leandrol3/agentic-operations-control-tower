# Refinamento final — lifecycle metadata no lesson-04-start

Ensaio: 2026-10-02. Escopo: metadata de lifecycle, demo Registry, documentação e regressão.

## A. Baseline

- Branch: `codex/lesson-04-start`.
- Commit inicial: `6a90a2f`; Git limpo antes das alterações.
- Default: **381 passed, 20 skipped em 14.22 s**.
- Integrações completas antes das alterações: **401 passed, 0 skipped em 18.51 s**.

## B. Mudanças

- `src/control_tower/control_plane/registry.py`: enum `LifecycleState`, campo obrigatório no
  `AgentRecord`, factory configura os sete agentes como `LifecycleState.ACTIVE`.
- `scripts/demo_lesson04.py`: view Registry com ID, ROLE, STATUS, LIFECYCLE, EXECUTION TYPE e GOALS.
- `tests/test_lesson04_lifecycle.py`: 16 novos casos, sem provider real.
- `docs/course/lesson-04-start-runbook.md`: separação das dimensões, fala, output, limitações e futuro.
- `docs/course/lesson-04/lifecycle-validation.md`: este relatório.

Enum: DRAFT, PILOT, ACTIVE, REVIEW, PAUSED, RETIRED; valores JSON em minúsculas, como os demais
contratos. Nenhuma string livre é aceita. View projeta maiúsculas para leitura em sala.

GET /agents e GET /agents/{agent_id} já usam AgentRecord: o campo aparece automaticamente,
inclusive no OpenAPI. Não foi necessário editar rotas ou application layer.
Nenhum campo antigo foi removido/renomeado; seus valores e semântica foram preservados.
Compatibilidade é aditiva nas respostas. Na construção Python/Pydantic, lifecycle_state é
obrigatório conforme solicitado: um dicionário antigo sem esse campo precisa fornecê-lo.
O Registry é local/configurado, portanto não há registros persistidos nem migration necessária.
Finance continua deterministic/model=null em ambos os modos. Business Goals não mudaram.

## C. Semântica

| Dimensão | O que responde | Exemplo |
|---|---|---|
| Registration status | Está cadastrado? | registered |
| Lifecycle state | Onde está no ciclo de vida administrativo/operacional? | active |
| Runtime health | O runtime consegue operar agora? | healthy/unknown, conforme observação |
| Execution status | Qual o estado desta execução específica? | queued/running/completed/failed |

ACTIVE não comprova health, disponibilidade instantânea, sucesso ou aprovação humana.
/health confirma processo API vivo; /ready consulta dependências configuradas. Não são health
checks individuais de todos os agentes/workers. Lifecycle metadata não muda o workflow.

## D. Demo ensaiada

Após a preparação Compose do runbook, na raiz do repositório:

```bash
uv run --extra lesson04 python scripts/demo_lesson04.py registry
uv run --extra lesson04 python scripts/demo_lesson04.py registry supply
curl --fail --silent --show-error http://localhost:8000/agents/finance | uv run python -m json.tool
```

Trecho da saída real (os sete agentes aparecem):

```text
ID              STATUS     LIFECYCLE  EXECUTION TYPE               GOALS
supply          registered ACTIVE     deterministic                goals=1
  ROLE: Collect inventory and supplier evidence
finance         registered ACTIVE     deterministic                goals=1
  ROLE: Calculate deterministic scenario costs
Registration status != Lifecycle state != Runtime health != Execution status
```

Fala: “Registered significa que o agente está cadastrado. Active significa que ele está ativo
no lifecycle. Nenhum dos dois diz se o runtime está saudável agora.”

Endpoints reais Supply e Finance retornaram registered/active/deterministic/model=null.
HTTP/MCP boundary real passou: mesma identidade reutiliza UUID, resultados públicos iguais,
outcome recommendation, approval pending, actions=false.
GET /incidents retornou população completed; /health alive; /ready ready com Redis/PostgreSQL ok.
Quality manteve approval pending/fallback false; Economics mock sem custo inventado.

## E. Testes finais

| Validação | Resultado |
|---|---|
| Novos testes focados | **16 passed em 0.55 s** |
| Default | **397 passed, 20 skipped em 15.15 s** |
| Todas as integrações | **417 passed, 0 skipped em 19.54 s** |
| smoke mock | ok; 13 checks |
| Demo Registry real | sete ACTIVE; registration separado |
| Demo boundary SDK MCP + HTTP | passou |
| GET /incidents, Quality, Economics, health/readiness reais | passaram |
| Sintaxe dos blocos shell do runbook e git diff --check | passou |

Casos novos: campo obrigatório, seis estados válidos, cinco valores inválidos (incluindo estados
de outras dimensões e null), sete agentes nos dois modos, API list/detail/OpenAPI e view curta.
Testes antigos preservados. Regressões Aulas 2/3/4 e tracing cobrem MCP/HTTP, Registry, pricing,
Quality, Economics, idempotência, fallback, human approval e OTel.

Comandos (dependências lesson04 instaladas e stack ligada):

```bash
LLM_MODE=mock uv run pytest -q
LLM_MODE=mock LESSON02_INTEGRATION=1 LESSON03_INTEGRATION=1 LESSON03_TRACING_INTEGRATION=1 LESSON04_INTEGRATION=1 uv run pytest -q
LLM_MODE=mock uv run control-tower smoke
```

No ensaio: `uv run --no-sync` após instalação, cache temporário isolado.
Nenhuma chamada OpenAI real foi feita. O modo OpenAI do Registry foi validado sem inferência.

## F. Limitações e fronteira

Lifecycle é metadata, não uma Lifecycle State Machine. Sem transitions, allowed transitions,
histórico, triggers, automação ou approval workflow para mudanças de lifecycle.
Sem Decision Engine, Recommendation Engine do Control Plane, Business Value, SLO evaluation,
auto-modify ou medição automática de metas. A recomendação operacional da Aula 1 permanece.

Futuro complete, apenas documentado: Business Goal Measurement; Business Value; SLOs/Thresholds;
Lifecycle State Machine/Triggers; Decision Engine; Collect → Interpret → Recommend;
Recommendation Model; Scale, Optimize, Intervene, Review, Pause, Retire; Control Plane Cockpit.

Resultado: **IDENTIFIED + MEASURABLE AGENTIC WORKFORCE** — IDENTITY + GOALS + LIFECYCLE METADATA
+ QUALITY + ECONOMICS. Ainda não há decisão sobre esses sinais. Quality preserva unknowns;
Economics continua estimativa de usage registrado, não custo total nem invoice.

## G. Git

Branch preservada: codex/lesson-04-start. Novo commit local sobre 6a90a2f, consultável por
`git log -1 --oneline`. Sem push, sem tag. Diff limitado aos cinco arquivos acima.
Nenhuma alteração de core, API routes, application, MCP, GET /incidents, Quality, Economics,
pricing, dependências ou infraestrutura. Stack de validação encerrada sem remover volumes.
Parar para revisão; não congelar via tag sem autorização.
