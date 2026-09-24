# Entrega para revisão — candidato lesson-03-start

**Parecer técnico: APROVAR no escopo do start. Parecer pedagógico: APROVAR para ensaio do professor.**
Implementação e validação local concluídas; aprovação do checkpoint permanece com o professor.
Branch `codex/lesson-03-start`, base Aula 2 `d3a67ad`. Sem publicação e sem tag nova/movida.

## 1. Arquivos adicionados

```text
.dockerignore
Dockerfile
compose.override.yaml
compose.lesson03-failure.yaml
src/control_tower/
├── api/
│   ├── __init__.py
│   ├── app.py
│   ├── models.py
│   └── readiness.py
├── runtime/
│   ├── __init__.py
│   ├── __main__.py
│   ├── bootstrap.py
│   ├── settings.py
│   ├── signals.py
│   ├── store.py
│   └── worker_health.py
└── telemetry/
    ├── __init__.py
    ├── config.py
    ├── context.py
    ├── logging.py
    ├── tracing.py
    └── README.md
tests/
├── test_lesson03.py
├── integration/test_lesson03_context.py
└── fixtures/lesson02-frozen.json
scripts/validate_lesson03_start.py
docs/course/
├── lesson-03-runbook.md
└── lesson-03/
    ├── contracts.md
    ├── demo-outputs.md
    └── validation.md
labs/03_runtime_production/README.md
```

Alterados: pyproject/uv.lock (extra lesson03), .env.example, README, AGENTS e cabeçalho de escopo
PROJECT_CONTEXT. `docs/course/lesson-02-runbook.md` já tinha revisão local antes desta tarefa;
essa alteração foi preservada e não foi incorporada à implementação da Aula 3.

## 2–3. Arquitetura e endpoints

Client → **FastAPI** → producer Aula 2 → Redis → Celery A/B → **mesmo LangGraph** → agentes/tools → PostgreSQL.
OpenAI continua opcional nos pontos existentes. [Diagrama e decisões](contracts.md).

- POST `/incidents`: contrato público validado, 202 depois de publicar, sem executar grafo na API.
- GET `/executions/{id}`: status/attempt/worker/duration/context.
- GET `/executions/{id}/events`: projeção dos eventos duráveis, after/limit.
- GET `/executions/{id}/result`: resumo tipado; 202 pendente / 200 terminal; aprovação humana preservada.
- GET `/health`: processo vivo, sem dependências.
- GET `/ready`: Redis + PostgreSQL/schema; não chama OpenAI.

## 4–5. Comandos e requests/responses

[Runbook copiável completo](../lesson-03-runbook.md), com 23 blocos shell cuja sintaxe foi validada.
Setup: `uv sync --locked --extra lesson03`; `docker compose config --quiet`; `docker compose build`;
`docker compose up -d --wait`. Não há inicialização manual adicional de schema.

```bash
curl -i -X POST http://localhost:8000/incidents \
  -H 'Content-Type: application/json' \
  -d '{"incident_id":"HTTP-REVIEW-001","version":"review-v1"}'
```

Exemplo REAL do ensaio mock final (identidade própria, POST **0,046 s**):

```json
{
  "execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2",
  "status": "queued",
  "created": true,
  "trace_id": "e6ee4da3d0a44a278159751cbdcfb575",
  "correlation_id": "validation-84cb6784b07f"
}
```

Consulta subsequente: running e depois completed, worker-b, attempt=1, **3.240,39 ms**, incluindo
3.000 ms artificiais. Resultado mock recommendation, estimated_cost_brl=12500.00,
approval_status=pending, actions_executed=false. Reenvio conservou UUID e trace, created=false.
Resultado detalhado, todos os GETs e logs estão nas [transcrições](demo-outputs.md).

## 6. Health/readiness — observado

| Estado do Redis | /health | /ready |
|---|---:|---:|
| Disponível | 200 alive | 200 ready, redis/postgres ok |
| Parado | **200 alive** | **503 not_ready**, redis unavailable, postgres ok |
| Reiniciado | 200 | Primeiro 503; depois 200 com retry curto |

Sondas não dependem de OpenAI nem da qualidade do resultado. PostgreSQL down coberto por testes de
probe/HTTP; o ensaio operacional de stop/start foi feito com Redis. Ready não promete worker ativo,
quota, latência ou êxito end-to-end. Startup OpenAI sem chave tem regressão explícita e erro sanitizado.

## 7. Compose final

Cinco serviços **healthy** no ensaio: api, worker-a, worker-b, redis e postgres. Mesmo Dockerfile/tag
para três papéis; UID **10001** confirmado dentro do container API. Python3.12/uv0.7.6/lock.
API localhost:8000; portas localhost da infraestrutura mantidas para compatibilidade com a Aula 2.
Base Compose congelada; override automático acrescenta runtime. Sem Collector obrigatório.
API inicializa tabelas; workers dependem de sua saúde. Volumes anteriores conservados.
`docker compose down` executado ao final, sem `-v`; nenhum container do ensaio ficou ativo.

## 8. Configuração

RuntimeSettings agrupa campos por responsabilidade e aceita .env + ambiente, aliases antigos,
SecretStr e validações. `.env.example` documenta defaults. APP_ENV, LOG_LEVEL/FORMAT, endpoints,
LLM_MODE/modelo, concorrência, timeout e OTel são explícitos. [Tabela completa](contracts.md).
A CLI histórica mantém seu carregamento original. Mock não lê .keys nem solicita provider.

## 9–10. Correlação e logs

Associação persistida 1:1 `ct_execution_context` → Execution, sem modificar contrato JSONB antigo.
Primeira associação vence, inclusive em claims concorrentes. Contexto vai em headers Celery;
worker restaura ContextVar e acrescenta sua identidade. Cleanup após a tentativa evita vazamento.
API responde com o contexto canônico. Execution antiga sem associação aparece com IDs null.

Logs incluem timestamp/level/service/event/message e execution/incident/trace/correlation/worker.
Modos human e JSON exercitados. Falha artificial: **1.288,25 ms**, llm.failed → llm.retry →
llm.fallback_activated → llm.degraded, outcome=degraded_recommendation e aprovação pendente.
Nenhuma credencial real nem request OpenAI: placeholder público, interceptação antes da rede.

Snapshots de eventos são emitidos após a tentativa, não em tempo real por nó; duplicatas podem
repetir snapshot. Logs stdout não sobrevivem a down; runbook salva capturas antes de recriar containers.
ExecutionEvent preserva cronologia durável e não é substituído por OTel.

## 11. OpenTelemetry preparado

SDK/provider/resource opcionais, exporter OTLP/HTTP somente se configurado. Desabilitado não faz rede.
Sem spans gerados/autoinstrumentação no start. Seis contratos de métricas preparados; nenhuma coleta
ou dashboard alegados. Langfuse somente citado como destino especializado. OTel é o contrato central.

## 12–13. Testes e regressão

**333 testes passaram em 15,90 s**, com integração real em schemas isolados do PostgreSQL:

- 279 unitários/regressões anteriores;
- 14 integrações da Aula 2;
- 37 testes novos de API/settings/log/context/containers/freeze;
- 3 integrações novas de associação/contexto concorrente e colisão.

Smoke Aula 1: 12 checks OK. Smoke Aula 2 local: 10 completed/0 failed, 2 threads, capacidade2,
50ms artificiais, 0,353 s observado. Tasks reais e comportamento de retry/idempotência/fallback
anteriores cobertos nas 14 integrações. Ensaio HTTP completou o mesmo INCIDENT-001 em workers reais.
Não se repetiu SIGKILL nesta entrega de runtime; a demo congelada permanece intacta.

Proteção por hash: **60 arquivos Aula 1 + 18 Aula 2**, além das regressões já existentes.
Grafo, agentes, tools, datasets, models, producer/task/store antigos e compose.yaml sem alterações.
Dependências novas foram adicionadas ao extra; versões existentes do lock foram mantidas.
Nenhum teste unitário chama OpenAI. Ensaio OpenAI com provider real não foi necessário/executado aqui;
foi validada a continuidade artificial já existente, sem alegar inferência real.

Build real aprovado, up real aprovado, HTTP202/GETs reais, duplicata real, logs correlacionados,
Redis stop/start, recriação conservando resultado e shutdown foram executados. As transcrições
publicáveis estão em demo-outputs.md; artefatos brutos locais ficam em artifacts/lesson03-start.

## 14. Limitações e ajustes feitos durante a validação

- Corrigido campo da projeção HTTP: Recommendation usa estimated_cost_brl. Regressão usa grafo mock real.
- Corrigido coletor do ensaio para `Request.get_method()`, compatível com Python do macOS.
- Erros de contrato não ecoam payload; erros operacionais não mostram DSN/chaves em respostas/logs novos.
- Não é deploy de produção: sem auth/TLS/HA/migrations/pooling/outbox/autoscaling e sem garantia exactly-once.
- Claim, associação e publicação têm commits separados; recuperação é reenvio idempotente explícito.
- Uma única máquina: Apple Silicon host, containers Linux ARM64. Windows/x86 não ensaiados.
- Código operacional fica pré-preparado; o professor mostra só recortes, não dezenas de flags/configs.

## 15. Reservado ao complete

Spans distribuídos reais, propagação W3C/causalidade, instrumentação selecionada de workflow/provider,
instruments métricos e definição de destino/visualização. Não implementar o complete agora.
Aula 4 mantém routing avançado, custo/qualidade/SLO/governança e estratégias de fallback de portfólio.

## 16. Parecer pedagógico

Agenda exata **240 min**, com teoria/contexto protegido e alunos em observação. Demos API20,
runtime20, sondas20, correlação15; falha observável ocupa até8min do bloco de telemetria25.
Setup/downloads ficam fora da aula. O roteiro inclui comando/output/pergunta/fallback por bloco.

Riscos didáticos tratados: não confundir 202 com conclusão; completed com aprovação; correlação com
trace; container com produção; readiness com saúde end-to-end; evento durável com log transitório.
Demo 5 usa captura se consumir mais de2min de diagnóstico. A agenda foi planejada e os comandos
centrais ensaiados; não foi ministrada uma turma real de4h para medir exposição/discussão.

**APROVAR o candidato start para revisão do professor. Parar aqui, sem tags e sem complete.**
