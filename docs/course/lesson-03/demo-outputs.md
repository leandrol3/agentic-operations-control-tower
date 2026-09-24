# Evidências reais — lesson-03-start

Ensaio em 24/09/2026 UTC, macOS ARM64 + containers Linux ARM64.
Mock e timeout artificial antes da rede; nenhum request pago. UUIDs são deste ensaio.
Tempos de máquina não são estimativas de exposição nem benchmark.

## Suíte completa com PostgreSQL real

```text
........................................................................ [ 21%]
........................................................................ [ 43%]
........................................................................ [ 64%]
........................................................................ [ 86%]
.............................................                            [100%]
333 passed in 15.90s
```

## Smoke Aula 1

```text
{
  "status": "ok",
  "mode": "mock",
  "incident_id": "INCIDENT-001",
  "related_orders": 3,
  "impact_status": "not_assessed",
  "checkpoint": "lesson-01-complete",
  "orchestration": "available_via_run",
  "checks_passed": [
    "incident",
    "related_orders",
    "demand",
    "strategic_customer",
    "local_stock",
    "transfer_stock",
    "alternative_supplier",
    "baseline_cost",
    "express_route",
    "standard_route",
    "hypothetical_penalty",
    "policies"
  ],
  "demand_units": 750,
  "available_units": 300,
  "shortfall_units": 450,
  "hypothetical_penalty_brl_7_days": "140000.00"
}
```

## Smoke Aula 2 local

```text
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 10
workers: 2
provider_limit: 2 | pico ativo: 2
completed: 10
failed: 0
duration: 0.353 s
throughput: 28.29 incidents/s (completed)
waited: 0 | pico esperando capacidade: 0
provider_wait_total: 0.000 worker-s (somatório, não duração)
delay didático: 50 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

## Compose saudável, após retorno ao mock

```text
NAME                           IMAGE                                   COMMAND                  SERVICE    CREATED          STATUS                        PORTS
novacore-lesson02-api-1        novacore-control-tower:lesson03-start   "python -m control_t…"   api        2 minutes ago    Up 2 minutes (healthy)        127.0.0.1:8000->8000/tcp
novacore-lesson02-postgres-1   postgres:16-alpine                      "docker-entrypoint.s…"   postgres   15 minutes ago   Up 15 minutes (healthy)       127.0.0.1:15432->5432/tcp
novacore-lesson02-redis-1      redis:7.4-alpine                        "docker-entrypoint.s…"   redis      15 minutes ago   Up 9 minutes (healthy)        127.0.0.1:16379->6379/tcp
novacore-lesson02-worker-a-1   novacore-control-tower:lesson03-start   "python -m control_t…"   worker-a   2 minutes ago    Up About a minute (healthy)   
novacore-lesson02-worker-b-1   novacore-control-tower:lesson03-start   "python -m control_t…"   worker-b   2 minutes ago    Up About a minute (healthy)
```

## HTTP mock, correlação e duplicata

```text
$ docker compose stop worker-a worker-b


POST /incidents → 202 (0.046s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "status": "queued", "created": true, "trace_id": "e6ee4da3d0a44a278159751cbdcfb575", "correlation_id": "validation-84cb6784b07f"}

GET /executions/16699a1c-db3b-4136-8f30-8a916cddbdf2 → 200 (0.010s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "incident_id": "HTTP-VALIDATION", "status": "queued", "attempt": 1, "current_step": null, "worker_id": null, "duration_ms": null, "trace_id": "e6ee4da3d0a44a278159751cbdcfb575", "correlation_id": "validation-84cb6784b07f"}

GET /executions/16699a1c-db3b-4136-8f30-8a916cddbdf2/result → 202 (0.006s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "status": "queued", "outcome": null, "mode": null, "recommended_action": null, "estimated_cost_brl": null, "approval_required": true, "approval_status": null, "actions_executed": false}

$ docker compose start worker-a worker-b


GET /executions/16699a1c-db3b-4136-8f30-8a916cddbdf2 → 200 (0.014s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "incident_id": "HTTP-VALIDATION", "status": "queued", "attempt": 1, "current_step": null, "worker_id": null, "duration_ms": null, "trace_id": "e6ee4da3d0a44a278159751cbdcfb575", "correlation_id": "validation-84cb6784b07f"}

GET /executions/16699a1c-db3b-4136-8f30-8a916cddbdf2 → 200 (0.011s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "incident_id": "HTTP-VALIDATION", "status": "queued", "attempt": 1, "current_step": null, "worker_id": null, "duration_ms": null, "trace_id": "e6ee4da3d0a44a278159751cbdcfb575", "correlation_id": "validation-84cb6784b07f"}

GET /executions/16699a1c-db3b-4136-8f30-8a916cddbdf2 → 200 (0.027s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "incident_id": "HTTP-VALIDATION", "status": "running", "attempt": 1, "current_step": "workflow", "worker_id": "worker-b@baa5a3380646:9", "duration_ms": null, "trace_id": "e6ee4da3d0a44a278159751cbdcfb575", "correlation_id": "validation-84cb6784b07f"}

GET /executions/16699a1c-db3b-4136-8f30-8a916cddbdf2 → 200 (0.026s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "incident_id": "HTTP-VALIDATION", "status": "running", "attempt": 1, "current_step": "workflow", "worker_id": "worker-b@baa5a3380646:9", "duration_ms": null, "trace_id": "e6ee4da3d0a44a278159751cbdcfb575", "correlation_id": "validation-84cb6784b07f"}

GET /executions/16699a1c-db3b-4136-8f30-8a916cddbdf2 → 200 (0.020s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "incident_id": "HTTP-VALIDATION", "status": "running", "attempt": 1, "current_step": "workflow", "worker_id": "worker-b@baa5a3380646:9", "duration_ms": null, "trace_id": "e6ee4da3d0a44a278159751cbdcfb575", "correlation_id": "validation-84cb6784b07f"}

GET /executions/16699a1c-db3b-4136-8f30-8a916cddbdf2 → 200 (0.018s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "incident_id": "HTTP-VALIDATION", "status": "running", "attempt": 1, "current_step": "workflow", "worker_id": "worker-b@baa5a3380646:9", "duration_ms": null, "trace_id": "e6ee4da3d0a44a278159751cbdcfb575", "correlation_id": "validation-84cb6784b07f"}

GET /executions/16699a1c-db3b-4136-8f30-8a916cddbdf2 → 200 (0.031s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "incident_id": "HTTP-VALIDATION", "status": "running", "attempt": 1, "current_step": "workflow", "worker_id": "worker-b@baa5a3380646:9", "duration_ms": null, "trace_id": "e6ee4da3d0a44a278159751cbdcfb575", "correlation_id": "validation-84cb6784b07f"}

GET /executions/16699a1c-db3b-4136-8f30-8a916cddbdf2 → 200 (0.029s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "incident_id": "HTTP-VALIDATION", "status": "running", "attempt": 1, "current_step": "workflow", "worker_id": "worker-b@baa5a3380646:9", "duration_ms": null, "trace_id": "e6ee4da3d0a44a278159751cbdcfb575", "correlation_id": "validation-84cb6784b07f"}

GET /executions/16699a1c-db3b-4136-8f30-8a916cddbdf2 → 200 (0.032s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "incident_id": "HTTP-VALIDATION", "status": "completed", "attempt": 1, "current_step": "awaiting_approval", "worker_id": "worker-b@baa5a3380646:9", "duration_ms": 3240.393460000064, "trace_id": "e6ee4da3d0a44a278159751cbdcfb575", "correlation_id": "validation-84cb6784b07f"}

GET /executions/16699a1c-db3b-4136-8f30-8a916cddbdf2/events?limit=100 → 200 (0.022s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "events": [{"sequence": 1, "timestamp": "2026-09-24T04:35:22.916022Z", "event_type": "execution.queued", "agent_id": "producer", "attempt": 1, "status": "queued"}, {"sequence": 2, "timestamp": "2026-09-24T04:35:24.865165Z", "event_type": "execution.started", "agent_id": "worker", "attempt": 1, "status": "running"}, {"sequence": 3, "timestamp": "2026-09-24T04:35:28.084953Z", "event_type": "supervisor.started", "agent_id": "supervisor", "attempt": 1, "status": "running"}, {"sequence": 4, "timestamp": "2026-09-24T04:35:28.087467Z", "event_type": "supervisor.completed", "agent_id": "supervisor", "attempt": 1, "status": "running"}, {"sequence": 5, "timestamp": "2026-09-24T04:35:28.091190Z", "event_type": "logistics.started", "agent_id": "logistics", "attempt": 1, "status": "running"}, {"sequence": 6, "timestamp": "2026-09-24T04:35:28.092644Z", "event_type": "production.started", "agent_id": "production", "attempt": 1, "status": "running"}, {"sequence": 7, "timestamp": "2026-09-24T04:35:28.093963Z", "event_type": "supply.started", "agent_id": "supply", "attempt": 1, "status": "running"}, {"sequence": 8, "timestamp": "2026-09-24T04:35:28.094931Z", "event_type": "logistics.completed", "agent_id": "logistics", "attempt": 1, "status": "running"}, {"sequence": 9, "timestamp": "2026-09-24T04:35:28.095899Z", "event_type": "production.completed", "agent_id": "production", "attempt": 1, "status": "running"}, {"sequence": 10, "timestamp": "2026-09-24T04:35:28.096716Z", "event_type": "supply.completed", "agent_id": "supply", "attempt": 1, "status": "running"}, {"sequence": 11, "timestamp": "2026-09-24T04:35:28.097932Z", "event_type": "consolidation.started", "agent_id": "consolidation", "attempt": 1, "status": "running"}, {"sequence": 12, "timestamp": "2026-09-24T04:35:28.098621Z", "event_type": "consolidation.completed", "agent_id": "consolidation", "attempt": 1, "status": "running"}, {"sequence": 13, "timestamp": "2026-09-24T04:35:28.099651Z", "event_type": "finance.started", "agent_id": "finance", "attempt": 1, "status": "running"}, {"sequence": 14, "timestamp": "2026-09-24T04:35:28.100546Z", "event_type": "finance.completed", "agent_id": "finance", "attempt": 1, "status": "running"}, {"sequence": 15, "timestamp": "2026-09-24T04:35:28.101663Z", "event_type": "challenger.started", "agent_id": "challenger", "attempt": 1, "status": "running"}, {"sequence": 16, "timestamp": "2026-09-24T04:35:28.102349Z", "event_type": "challenger.completed", "agent_id": "challenger", "attempt": 1, "status": "running"}, {"sequence": 17, "timestamp": "2026-09-24T04:35:28.103186Z", "event_type": "recommendation.started", "agent_id": "recommendation", "attempt": 1, "status": "running"}, {"sequence": 18, "timestamp": "2026-09-24T04:35:28.103762Z", "event_type": "recommendation.completed", "agent_id": "recommendation", "attempt": 1, "status": "running"}, {"sequence": 19, "timestamp": "2026-09-24T04:35:28.104591Z", "event_type": "human_approval.started", "agent_id": "human_approval", "attempt": 1, "status": "running"}, {"sequence": 20, "timestamp": "2026-09-24T04:35:28.105152Z", "event_type": "human_approval.completed", "agent_id": "human_approval", "attempt": 1, "status": "running"}, {"sequence": 21, "timestamp": "2026-09-24T04:35:28.106334Z", "event_type": "execution.completed", "agent_id": "worker", "attempt": 1, "status": "completed"}]}

GET /executions/16699a1c-db3b-4136-8f30-8a916cddbdf2/result → 200 (0.007s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "status": "completed", "outcome": "recommendation", "mode": "mock", "recommended_action": "Cenário D: Transferir até o piso de Campinas por rota padrão e replanejar; residual via Alpha", "estimated_cost_brl": "12500.00", "approval_required": true, "approval_status": "pending", "actions_executed": false}

POST /incidents → 202 (0.012s)
{"execution_id": "16699a1c-db3b-4136-8f30-8a916cddbdf2", "status": "completed", "created": false, "trace_id": "e6ee4da3d0a44a278159751cbdcfb575", "correlation_id": "validation-84cb6784b07f"}

POST /incidents → 422 (0.002s)
{"detail": "Request inválido; consulte /docs"}

LOGS CORRELACIONADOS
worker-b-1  | timestamp=2026-09-24T04:35:24.857107+00:00 | level=INFO | service=control-tower-worker-b | execution_id=16699a1c-db3b-4136-8f30-8a916cddbdf2 | incident_id=HTTP-VALIDATION | trace_id=e6ee4da3d0a44a278159751cbdcfb575 | correlation_id=validation-84cb6784b07f | worker_id=worker-b@baa5a3380646:9 | event=worker.received | message=Entrega recebida; domínio decide claim e execução
worker-b-1  | timestamp=2026-09-24T04:35:28.121875+00:00 | level=INFO | service=control-tower-worker-b | execution_id=16699a1c-db3b-4136-8f30-8a916cddbdf2 | incident_id=HTTP-VALIDATION | trace_id=e6ee4da3d0a44a278159751cbdcfb575 | correlation_id=validation-84cb6784b07f | worker_id=worker-b@baa5a3380646:9 | event=worker.finished | message=Snapshot da execução persistida | status=completed | attempt=1 | duration_ms=3240.393460000064 | outcome=recommendation
api-1       | timestamp=2026-09-24T04:35:22.939021+00:00 | level=INFO | service=control-tower-api | execution_id=16699a1c-db3b-4136-8f30-8a916cddbdf2 | incident_id=HTTP-VALIDATION | trace_id=e6ee4da3d0a44a278159751cbdcfb575 | correlation_id=validation-84cb6784b07f | event=queue.submitted | message=Producer confirmou publicação | created=True
api-1       | timestamp=2026-09-24T04:35:28.486239+00:00 | level=INFO | service=control-tower-api | execution_id=16699a1c-db3b-4136-8f30-8a916cddbdf2 | incident_id=HTTP-VALIDATION | trace_id=e6ee4da3d0a44a278159751cbdcfb575 | correlation_id=validation-84cb6784b07f | event=queue.submitted | message=Producer confirmou publicação | created=False
worker-a-1  | timestamp=2026-09-24T04:35:28.487794+00:00 | level=INFO | service=control-tower-worker-a | execution_id=16699a1c-db3b-4136-8f30-8a916cddbdf2 | incident_id=HTTP-VALIDATION | trace_id=e6ee4da3d0a44a278159751cbdcfb575 | correlation_id=validation-84cb6784b07f | worker_id=worker-a@3aa6af8f4eed:9 | event=worker.received | message=Entrega recebida; domínio decide claim e execução
worker-a-1  | timestamp=2026-09-24T04:35:28.509460+00:00 | level=INFO | service=control-tower-worker-a | execution_id=16699a1c-db3b-4136-8f30-8a916cddbdf2 | incident_id=HTTP-VALIDATION | trace_id=e6ee4da3d0a44a278159751cbdcfb575 | correlation_id=validation-84cb6784b07f | worker_id=worker-a@3aa6af8f4eed:9 | event=worker.finished | message=Snapshot da execução persistida | status=completed | attempt=1 | duration_ms=3240.393460000064 | outcome=recommendation

PASS: mock
```

## Health / readiness com Redis indisponível

```text
GET /health → 200 (0.014s)
{"status": "alive"}

GET /ready → 200 (0.021s)
{"status": "ready", "dependencies": {"redis": "ok", "postgres": "ok"}}

$ docker compose stop redis


GET /health → 200 (0.002s)
{"status": "alive"}

GET /ready → 503 (0.055s)
{"status": "not_ready", "dependencies": {"redis": "unavailable", "postgres": "ok"}}

$ docker compose start redis


GET /ready → 503 (0.009s)
{"status": "not_ready", "dependencies": {"redis": "unavailable", "postgres": "ok"}}

GET /ready → 200 (0.020s)
{"status": "ready", "dependencies": {"redis": "ok", "postgres": "ok"}}

PASS: health
```

## Timeout artificial / retry / fallback

```text
POST /incidents → 202 (0.278s)
{"execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "status": "queued", "created": true, "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023"}

GET /executions/1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a → 200 (0.010s)
{"execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "status": "queued", "attempt": 1, "current_step": null, "worker_id": null, "duration_ms": null, "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023"}

GET /executions/1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a → 200 (0.032s)
{"execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "status": "running", "attempt": 1, "current_step": "supervisor", "worker_id": "worker-a@8069a2caf625:9", "duration_ms": null, "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023"}

GET /executions/1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a → 200 (0.012s)
{"execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "status": "running", "attempt": 1, "current_step": "supervisor", "worker_id": "worker-a@8069a2caf625:9", "duration_ms": null, "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023"}

GET /executions/1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a → 200 (0.030s)
{"execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "status": "completed", "attempt": 1, "current_step": "degraded_recommendation", "worker_id": "worker-a@8069a2caf625:9", "duration_ms": 1288.2487919999903, "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023"}

GET /executions/1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a/events?limit=100 → 200 (0.022s)
{"execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "events": [{"sequence": 1, "timestamp": "2026-09-24T04:32:15.149925Z", "event_type": "execution.queued", "agent_id": "producer", "attempt": 1, "status": "queued"}, {"sequence": 2, "timestamp": "2026-09-24T04:32:15.180565Z", "event_type": "execution.started", "agent_id": "worker", "attempt": 1, "status": "running"}, {"sequence": 3, "timestamp": "2026-09-24T04:32:15.432766Z", "event_type": "supervisor.started", "agent_id": "supervisor", "attempt": 1, "status": "running"}, {"sequence": 4, "timestamp": "2026-09-24T04:32:15.433808Z", "event_type": "llm.requested", "agent_id": "supervisor", "attempt": 1, "status": "running"}, {"sequence": 5, "timestamp": "2026-09-24T04:32:15.434291Z", "event_type": "llm.failed", "agent_id": "supervisor", "attempt": 1, "status": "running"}, {"sequence": 6, "timestamp": "2026-09-24T04:32:15.434739Z", "event_type": "llm.retry", "agent_id": "supervisor", "attempt": 1, "status": "running"}, {"sequence": 7, "timestamp": "2026-09-24T04:32:16.436087Z", "event_type": "llm.requested", "agent_id": "supervisor", "attempt": 1, "status": "running"}, {"sequence": 8, "timestamp": "2026-09-24T04:32:16.437932Z", "event_type": "llm.failed", "agent_id": "supervisor", "attempt": 1, "status": "running"}, {"sequence": 9, "timestamp": "2026-09-24T04:32:16.439313Z", "event_type": "llm.fallback_activated", "agent_id": "worker", "attempt": 1, "status": "running"}, {"sequence": 10, "timestamp": "2026-09-24T04:32:16.452059Z", "event_type": "supervisor.started", "agent_id": "supervisor", "attempt": 1, "status": "running"}, {"sequence": 11, "timestamp": "2026-09-24T04:32:16.452984Z", "event_type": "supervisor.completed", "agent_id": "supervisor", "attempt": 1, "status": "running"}, {"sequence": 12, "timestamp": "2026-09-24T04:32:16.455181Z", "event_type": "logistics.started", "agent_id": "logistics", "attempt": 1, "status": "running"}, {"sequence": 13, "timestamp": "2026-09-24T04:32:16.456474Z", "event_type": "production.started", "agent_id": "production", "attempt": 1, "status": "running"}, {"sequence": 14, "timestamp": "2026-09-24T04:32:16.457445Z", "event_type": "supply.started", "agent_id": "supply", "attempt": 1, "status": "running"}, {"sequence": 15, "timestamp": "2026-09-24T04:32:16.458411Z", "event_type": "logistics.completed", "agent_id": "logistics", "attempt": 1, "status": "running"}, {"sequence": 16, "timestamp": "2026-09-24T04:32:16.459408Z", "event_type": "production.completed", "agent_id": "production", "attempt": 1, "status": "running"}, {"sequence": 17, "timestamp": "2026-09-24T04:32:16.460362Z", "event_type": "supply.completed", "agent_id": "supply", "attempt": 1, "status": "running"}, {"sequence": 18, "timestamp": "2026-09-24T04:32:16.461547Z", "event_type": "consolidation.started", "agent_id": "consolidation", "attempt": 1, "status": "running"}, {"sequence": 19, "timestamp": "2026-09-24T04:32:16.462217Z", "event_type": "consolidation.completed", "agent_id": "consolidation", "attempt": 1, "status": "running"}, {"sequence": 20, "timestamp": "2026-09-24T04:32:16.463161Z", "event_type": "finance.started", "agent_id": "finance", "attempt": 1, "status": "running"}, {"sequence": 21, "timestamp": "2026-09-24T04:32:16.464006Z", "event_type": "finance.completed", "agent_id": "finance", "attempt": 1, "status": "running"}, {"sequence": 22, "timestamp": "2026-09-24T04:32:16.464978Z", "event_type": "challenger.started", "agent_id": "challenger", "attempt": 1, "status": "running"}, {"sequence": 23, "timestamp": "2026-09-24T04:32:16.465931Z", "event_type": "challenger.completed", "agent_id": "challenger", "attempt": 1, "status": "running"}, {"sequence": 24, "timestamp": "2026-09-24T04:32:16.466857Z", "event_type": "recommendation.started", "agent_id": "recommendation", "attempt": 1, "status": "running"}, {"sequence": 25, "timestamp": "2026-09-24T04:32:16.467453Z", "event_type": "recommendation.completed", "agent_id": "recommendation", "attempt": 1, "status": "running"}, {"sequence": 26, "timestamp": "2026-09-24T04:32:16.468317Z", "event_type": "human_approval.started", "agent_id": "human_approval", "attempt": 1, "status": "running"}, {"sequence": 27, "timestamp": "2026-09-24T04:32:16.468847Z", "event_type": "human_approval.completed", "agent_id": "human_approval", "attempt": 1, "status": "running"}, {"sequence": 28, "timestamp": "2026-09-24T04:32:16.469547Z", "event_type": "llm.degraded", "agent_id": "worker", "attempt": 1, "status": "running"}, {"sequence": 29, "timestamp": "2026-09-24T04:32:16.470390Z", "event_type": "execution.completed", "agent_id": "worker", "attempt": 1, "status": "completed"}]}

GET /executions/1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a/result → 200 (0.007s)
{"execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "status": "completed", "outcome": "degraded_recommendation", "mode": "degraded", "recommended_action": "Cenário D: Transferir até o piso de Campinas por rota padrão e replanejar; residual via Alpha", "estimated_cost_brl": "12500.00", "approval_required": true, "approval_status": "pending", "actions_executed": false}

POST /incidents → 202 (0.012s)
{"execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "status": "completed", "created": false, "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023"}

POST /incidents → 422 (0.001s)
{"detail": "Request inválido; consulte /docs"}

LOGS CORRELACIONADOS
worker-b-1  | {"timestamp": "2026-09-24T04:32:16.823479+00:00", "level": "INFO", "service": "control-tower-worker-b", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-b@6d29f478cbf6:9", "event": "worker.received", "message": "Entrega recebida; domínio decide claim e execução"}
worker-b-1  | {"timestamp": "2026-09-24T04:32:16.844142+00:00", "level": "INFO", "service": "control-tower-worker-b", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-b@6d29f478cbf6:9", "event": "llm.requested", "message": "Evento durável observado após tentativa", "sequence": 4, "attempt": 1}
worker-b-1  | {"timestamp": "2026-09-24T04:32:16.844207+00:00", "level": "WARNING", "service": "control-tower-worker-b", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-b@6d29f478cbf6:9", "event": "llm.failed", "message": "Evento durável observado após tentativa", "sequence": 5, "attempt": 1}
worker-b-1  | {"timestamp": "2026-09-24T04:32:16.844234+00:00", "level": "INFO", "service": "control-tower-worker-b", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-b@6d29f478cbf6:9", "event": "llm.retry", "message": "Evento durável observado após tentativa", "sequence": 6, "attempt": 1}
worker-b-1  | {"timestamp": "2026-09-24T04:32:16.844258+00:00", "level": "INFO", "service": "control-tower-worker-b", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-b@6d29f478cbf6:9", "event": "llm.requested", "message": "Evento durável observado após tentativa", "sequence": 7, "attempt": 1}
worker-b-1  | {"timestamp": "2026-09-24T04:32:16.844274+00:00", "level": "WARNING", "service": "control-tower-worker-b", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-b@6d29f478cbf6:9", "event": "llm.failed", "message": "Evento durável observado após tentativa", "sequence": 8, "attempt": 1}
worker-b-1  | {"timestamp": "2026-09-24T04:32:16.844293+00:00", "level": "INFO", "service": "control-tower-worker-b", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-b@6d29f478cbf6:9", "event": "llm.fallback_activated", "message": "Evento durável observado após tentativa", "sequence": 9, "attempt": 1}
worker-b-1  | {"timestamp": "2026-09-24T04:32:16.844312+00:00", "level": "INFO", "service": "control-tower-worker-b", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-b@6d29f478cbf6:9", "event": "llm.degraded", "message": "Evento durável observado após tentativa", "sequence": 28, "attempt": 1}
worker-b-1  | {"timestamp": "2026-09-24T04:32:16.844342+00:00", "level": "INFO", "service": "control-tower-worker-b", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-b@6d29f478cbf6:9", "event": "worker.finished", "message": "Snapshot da execução persistida", "status": "completed", "attempt": 1, "duration_ms": 1288.2487919999903, "outcome": "degraded_recommendation"}
worker-a-1  | {"timestamp": "2026-09-24T04:32:15.171464+00:00", "level": "INFO", "service": "control-tower-worker-a", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-a@8069a2caf625:9", "event": "worker.received", "message": "Entrega recebida; domínio decide claim e execução"}
worker-a-1  | {"timestamp": "2026-09-24T04:32:16.485497+00:00", "level": "INFO", "service": "control-tower-worker-a", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-a@8069a2caf625:9", "event": "llm.requested", "message": "Evento durável observado após tentativa", "sequence": 4, "attempt": 1}
worker-a-1  | {"timestamp": "2026-09-24T04:32:16.485571+00:00", "level": "WARNING", "service": "control-tower-worker-a", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-a@8069a2caf625:9", "event": "llm.failed", "message": "Evento durável observado após tentativa", "sequence": 5, "attempt": 1}
worker-a-1  | {"timestamp": "2026-09-24T04:32:16.485598+00:00", "level": "INFO", "service": "control-tower-worker-a", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-a@8069a2caf625:9", "event": "llm.retry", "message": "Evento durável observado após tentativa", "sequence": 6, "attempt": 1}
worker-a-1  | {"timestamp": "2026-09-24T04:32:16.485622+00:00", "level": "INFO", "service": "control-tower-worker-a", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-a@8069a2caf625:9", "event": "llm.requested", "message": "Evento durável observado após tentativa", "sequence": 7, "attempt": 1}
worker-a-1  | {"timestamp": "2026-09-24T04:32:16.485639+00:00", "level": "WARNING", "service": "control-tower-worker-a", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-a@8069a2caf625:9", "event": "llm.failed", "message": "Evento durável observado após tentativa", "sequence": 8, "attempt": 1}
worker-a-1  | {"timestamp": "2026-09-24T04:32:16.485655+00:00", "level": "INFO", "service": "control-tower-worker-a", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-a@8069a2caf625:9", "event": "llm.fallback_activated", "message": "Evento durável observado após tentativa", "sequence": 9, "attempt": 1}
worker-a-1  | {"timestamp": "2026-09-24T04:32:16.485678+00:00", "level": "INFO", "service": "control-tower-worker-a", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-a@8069a2caf625:9", "event": "llm.degraded", "message": "Evento durável observado após tentativa", "sequence": 28, "attempt": 1}
worker-a-1  | {"timestamp": "2026-09-24T04:32:16.485704+00:00", "level": "INFO", "service": "control-tower-worker-a", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": "worker-a@8069a2caf625:9", "event": "worker.finished", "message": "Snapshot da execução persistida", "status": "completed", "attempt": 1, "duration_ms": 1288.2487919999903, "outcome": "degraded_recommendation"}
api-1       | {"timestamp": "2026-09-24T04:32:15.172309+00:00", "level": "INFO", "service": "control-tower-api", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": null, "event": "queue.submitted", "message": "Producer confirmou publicação", "created": true}
api-1       | {"timestamp": "2026-09-24T04:32:16.821617+00:00", "level": "INFO", "service": "control-tower-api", "execution_id": "1f85b0f6-eaa7-4c20-b43d-1b66dfeefe0a", "incident_id": "HTTP-VALIDATION", "trace_id": "fdcebc33ede44b01a118e7f662488632", "correlation_id": "validation-c1abbf8b0023", "worker_id": null, "event": "queue.submitted", "message": "Producer confirmou publicação", "created": false}

PASS: failure
```

## Resultado durável após recriar API e workers

```text
{"execution_id":"33c1d0b3-0c4b-400d-92f3-2d8933cdd902","status":"completed","outcome":"recommendation","mode":"mock","recommended_action":"Cenário D: Transferir até o piso de Campinas por rota padrão e replanejar; residual via Alpha","estimated_cost_brl":"12500.00","approval_required":true,"approval_status":"pending","actions_executed":false}
```

## Encerramento sem remover volumes

```text
 Container novacore-lesson02-worker-a-1 Stopping 
 Container novacore-lesson02-worker-b-1 Stopping 
 Container novacore-lesson02-worker-a-1 Stopped 
 Container novacore-lesson02-worker-a-1 Removing 
 Container novacore-lesson02-worker-a-1 Removed 
 Container novacore-lesson02-worker-b-1 Stopped 
 Container novacore-lesson02-worker-b-1 Removing 
 Container novacore-lesson02-worker-b-1 Removed 
 Container novacore-lesson02-api-1 Stopping 
 Container novacore-lesson02-api-1 Stopped 
 Container novacore-lesson02-api-1 Removing 
 Container novacore-lesson02-api-1 Removed 
 Container novacore-lesson02-postgres-1 Stopping 
 Container novacore-lesson02-redis-1 Stopping 
 Container novacore-lesson02-postgres-1 Stopped 
 Container novacore-lesson02-postgres-1 Removing 
 Container novacore-lesson02-postgres-1 Removed 
 Container novacore-lesson02-redis-1 Stopped 
 Container novacore-lesson02-redis-1 Removing 
 Container novacore-lesson02-redis-1 Removed 
 Network novacore-lesson02_default Removing 
 Network novacore-lesson02_default Removed 
NAME      IMAGE     COMMAND   SERVICE   CREATED   STATUS    PORTS
```
