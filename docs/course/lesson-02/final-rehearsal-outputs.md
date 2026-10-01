# Outputs do ensaio final da Aula 2

Execução real em 2026-09-16. Modos mock, Redis/PostgreSQL reais, dois workers locais independentes.
Tempos abaixo incluem início de processo CLI quando indicado; não são tempos de exposição do professor.
Datas dos eventos estão em UTC; a data sintética dos incidentes é um relógio de negócio distinto.

## Tempos medidos

| Experimento | Tempo |
|---|---:|
| queue_including_worker_start | 7.822 s |
| retry | 2.668 s |
| loss_kill_to_completed | 110.846 s |
| loss_full_sequence | 111.467 s |
| duplicate | 3.740 s |

Entre os inícios das tentativas após worker loss: **100.869 s**.
O tempo kill→completed inclui espera de redelivery e 10 s de delay da tentativa recuperada.
O ensaio anterior teve 85,410 s entre inícios; a variação confirma que 60 s de visibility timeout não é SLA.

## Outputs para projeção, na ordem executada

As versões reais abaixo são exclusivas deste ensaio. Na aula, escolher novas versões.
Os contadores incluem 23 execuções do ensaio anterior: não são contadores exclusivos do novo lote.
Repetição das consultas da perda ao final comprova que funcionam depois de encerrar os workers.

### uv run control-tower show INCIDENT-001 recommendation

CLI: 0.361 s.

```text
RECOMMENDATION → awaiting_approval

Cenário D | custo incremental: R$ 12.500
Multa evitada vs A: R$ 16.000
Economia líquida incremental vs A: R$ 11.000
Maior atraso: 3 dias | cliente estratégico: 0 dias
confidence = 0.65 (didático/fixo, não calibrado)
Riscos pendentes: 3; confirmar premissas antes da decisão.

approval_required = true
status = awaiting_approval
approval = pending | responsável: operations_manager
actions_executed = false

Uma recomendação válida não é uma decisão autorizada.
```

### uv run control-tower generate-incidents --count 500

CLI: 0.373 s.

```text
NovaCore | incidentes sintéticos
count: 500 | seed: 42
supplier_delay: 120
production_deviation: 85
logistics_delay: 140
sla_risk: 65
inventory_shortage: 90
5 categorias de chegada; batch usa replay do caso técnico INCIDENT-001.
Plantas/payloads sintéticos não são decisões de negócio já suportadas.
```

### uv run control-tower batch --incidents 10 --workers 1 --demo-delay-ms 500

CLI: 5.478 s.

```text
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 10
workers: 1
provider_limit: sem limite adicional | pico ativo: 1
completed: 10
failed: 0
duration: 5.106 s
throughput: 1.96 incidents/s (completed)
waited: 0 | pico esperando capacidade: 0
provider_wait_total: 0.000 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

### uv run control-tower batch --incidents 10 --workers 5 --demo-delay-ms 500

CLI: 1.417 s.

```text
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 10
workers: 5
provider_limit: sem limite adicional | pico ativo: 5
completed: 10
failed: 0
duration: 1.058 s
throughput: 9.45 incidents/s (completed)
waited: 0 | pico esperando capacidade: 0
provider_wait_total: 0.000 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

### uv run control-tower batch --incidents 50 --workers 5 --provider-limit 5 --demo-delay-ms 500

CLI: 5.620 s.

```text
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 50
workers: 5
provider_limit: 5 | pico ativo: 5
completed: 50
failed: 0
duration: 5.263 s
throughput: 9.50 incidents/s (completed)
waited: 0 | pico esperando capacidade: 0
provider_wait_total: 0.000 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

### uv run control-tower batch --incidents 50 --workers 20 --provider-limit 5 --demo-delay-ms 500

CLI: 5.918 s.

```text
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 50
workers: 20
provider_limit: 5 | pico ativo: 5
completed: 50
failed: 0
duration: 5.557 s
throughput: 9.00 incidents/s (completed)
waited: 15 | pico esperando capacidade: 15
provider_wait_total: 66.654 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

### uv run control-tower batch --incidents 50 --workers 50 --provider-limit 5 --demo-delay-ms 500

CLI: 5.916 s.

```text
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 50
workers: 50
provider_limit: 5 | pico ativo: 5
completed: 50
failed: 0
duration: 5.575 s
throughput: 8.97 incidents/s (completed)
waited: 45 | pico esperando capacidade: 45
provider_wait_total: 125.229 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

### uv run control-tower idempotency-demo

CLI: 0.337 s.

```text
Idempotency contract | NC-S42-0001 | analyze-reference | v1
idempotency_key: idem-v1-74fa8f63726e8644c2b41d5b2d5f8b16e2661c4138c78e3414c243c74a368685
Duas entregas, mesma chave: True
Helper não elimina duplicatas. Retry/reivindicação atômica ficam para o complete.
```

### uv run control-tower db-init

CLI: 0.162 s.

```text
PostgreSQL: tabelas de execução/eventos prontas. Nenhum dado removido.
```

### uv run control-tower enqueue --count 20 --version rehearsal-9dc2f378-queue --demo-delay-ms 500

CLI: 0.637 s.

```text
Publicadas: 20 | novas executions: 20 | existentes: 0
mock | referência INCIDENT-001 | aprovação humana obrigatória
ba797e70-c618-422a-8da7-c4265c59a3e0
71f528bb-e8d0-44fb-af0c-af9ab2bf517b
be7861ea-37a7-4465-a61c-02537c2791a6
b0ccb6fd-b22a-4f22-ae7c-a63d8263944b
ab5067a8-a3f8-48fa-8f98-0a25a23c4e01
a20c3249-f6be-4b01-9491-def74ee1724b
25aaca47-fd21-46c9-95ec-65964d245f8b
7994632c-1690-4648-9bd1-f51f6ff3ace3
... mais 12; consulte executions
```

### uv run control-tower executions

CLI: 0.156 s.

```text
queued: 20 | running: 0 | completed: 23 | failed: 0
execution_id                         status     attempt worker
ecf29b7a-6ad2-4486-9d75-9dfc076537e0 queued           1 —
4ff40777-42b9-4695-b8d5-4ac0e329f114 queued           1 —
3f3a84b2-f613-4696-bf94-ca86ee24d9ec queued           1 —
a6164137-a2b4-4503-ae92-8d81470cb058 queued           1 —
5ae47c0d-f52a-49fc-9b42-1f17b97acb3f queued           1 —
b3fc88e3-0407-40bf-aade-5b4b1c76162b queued           1 —
75768400-4e24-4102-bc4c-c81066b095a5 queued           1 —
7e181832-9f0f-4bcd-970c-ac93f7d7a4e4 queued           1 —
```

### uv run control-tower executions

CLI: 0.159 s.

```text
queued: 17 | running: 2 | completed: 24 | failed: 0
execution_id                         status     attempt worker
ecf29b7a-6ad2-4486-9d75-9dfc076537e0 queued           1 —
4ff40777-42b9-4695-b8d5-4ac0e329f114 queued           1 —
3f3a84b2-f613-4696-bf94-ca86ee24d9ec queued           1 —
a6164137-a2b4-4503-ae92-8d81470cb058 queued           1 —
5ae47c0d-f52a-49fc-9b42-1f17b97acb3f queued           1 —
b3fc88e3-0407-40bf-aade-5b4b1c76162b queued           1 —
75768400-4e24-4102-bc4c-c81066b095a5 queued           1 —
7e181832-9f0f-4bcd-970c-ac93f7d7a4e4 queued           1 —
```

### uv run control-tower execution ba797e70-c618-422a-8da7-c4265c59a3e0

CLI: 0.169 s.

```text
execution_id: ba797e70-c618-422a-8da7-c4265c59a3e0
incident_id: NC-S42-0001
status: completed
attempt: 1
worker_id: lesson02-A@Leandros-MacBook-Pro.local:87713
current_step: awaiting_approval
started_at: 2026-09-16 12:21:30.999618+00:00
completed_at: 2026-09-16 12:21:31.554006+00:00
error: None
result: approval pending; actions_executed=false
```

### uv run control-tower events ba797e70-c618-422a-8da7-c4265c59a3e0

CLI: 0.159 s.

```text
ba797e70-c618-422a-8da7-c4265c59a3e0 | eventos: 21 | últimos 12
 10 12:21:31 attempt=1 supply.completed
 11 12:21:31 attempt=1 consolidation.started
 12 12:21:31 attempt=1 consolidation.completed
 13 12:21:31 attempt=1 finance.started
 14 12:21:31 attempt=1 finance.completed
 15 12:21:31 attempt=1 challenger.started
 16 12:21:31 attempt=1 challenger.completed
 17 12:21:31 attempt=1 recommendation.started
 18 12:21:31 attempt=1 recommendation.completed
 19 12:21:31 attempt=1 human_approval.started
 20 12:21:31 attempt=1 human_approval.completed
 21 12:21:31 attempt=1 execution.completed
```

### uv run control-tower result ba797e70-c618-422a-8da7-c4265c59a3e0

CLI: 0.149 s.

```text
Workflow completed | approval pending | actions_executed=false
Caso de referência: INCIDENT-001 | modo: mock
Ação: Cenário D: Transferir até o piso de Campinas por rota padrão e replanejar; residual via Alpha
Custo: R$ 12500.00 | multa evitada: R$ 16000.00
Atraso: 3 dias | confiança: 0.65
Riscos: 3 | --json para contrato completo
```

### uv run control-tower events ba797e70-c618-422a-8da7-c4265c59a3e0 --lifecycle

CLI: 0.158 s.

```text
ba797e70-c618-422a-8da7-c4265c59a3e0 | eventos: 3 | últimos 12
  1 12:21:29 attempt=1 execution.queued
  2 12:21:31 attempt=1 execution.started
 21 12:21:31 attempt=1 execution.completed
```

### uv run control-tower enqueue --count 1 --version rehearsal-9dc2f378-retry --fail-specialist logistics

CLI: 0.486 s.

```text
Publicadas: 1 | novas executions: 1 | existentes: 0
mock | referência INCIDENT-001 | aprovação humana obrigatória
f077c8da-9408-4114-aab0-de87df57daf1
```

### uv run control-tower execution f077c8da-9408-4114-aab0-de87df57daf1

CLI: 0.182 s.

```text
execution_id: f077c8da-9408-4114-aab0-de87df57daf1
incident_id: NC-S42-0001
status: completed
attempt: 2
worker_id: lesson02-A@Leandros-MacBook-Pro.local:87713
current_step: awaiting_approval
started_at: 2026-09-16 12:21:40.943972+00:00
completed_at: 2026-09-16 12:21:41.033170+00:00
error: None
result: approval pending; actions_executed=false
```

### uv run control-tower events f077c8da-9408-4114-aab0-de87df57daf1

CLI: 0.158 s.

```text
f077c8da-9408-4114-aab0-de87df57daf1 | eventos: 36 | últimos 12
 25 12:21:41 attempt=2 supply.completed
 26 12:21:41 attempt=2 consolidation.started
 27 12:21:41 attempt=2 consolidation.completed
 28 12:21:41 attempt=2 finance.started
 29 12:21:41 attempt=2 finance.completed
 30 12:21:41 attempt=2 challenger.started
 31 12:21:41 attempt=2 challenger.completed
 32 12:21:41 attempt=2 recommendation.started
 33 12:21:41 attempt=2 recommendation.completed
 34 12:21:41 attempt=2 human_approval.started
 35 12:21:41 attempt=2 human_approval.completed
 36 12:21:41 attempt=2 execution.completed
```

### uv run control-tower result f077c8da-9408-4114-aab0-de87df57daf1

CLI: 0.146 s.

```text
Workflow completed | approval pending | actions_executed=false
Caso de referência: INCIDENT-001 | modo: mock
Ação: Cenário D: Transferir até o piso de Campinas por rota padrão e replanejar; residual via Alpha
Custo: R$ 12500.00 | multa evitada: R$ 16000.00
Atraso: 3 dias | confiança: 0.65
Riscos: 3 | --json para contrato completo
```

### uv run control-tower events f077c8da-9408-4114-aab0-de87df57daf1 --lifecycle

CLI: 0.159 s.

```text
f077c8da-9408-4114-aab0-de87df57daf1 | eventos: 7 | últimos 12
  1 12:21:38 attempt=1 execution.queued
  2 12:21:38 attempt=1 execution.started
  8 12:21:38 attempt=1 logistics.failed
 15 12:21:38 attempt=1 execution.failed
 16 12:21:38 attempt=1 execution.retry
 17 12:21:40 attempt=2 execution.started
 36 12:21:41 attempt=2 execution.completed
```

### uv run control-tower enqueue --count 1 --version rehearsal-9dc2f378-loss --demo-delay-ms 10000

CLI: 0.458 s.

```text
Publicadas: 1 | novas executions: 1 | existentes: 0
mock | referência INCIDENT-001 | aprovação humana obrigatória
d229700f-8165-4e3f-b349-4b9b6dd15fbf
```

### uv run control-tower execution d229700f-8165-4e3f-b349-4b9b6dd15fbf

CLI: 0.148 s.

```text
execution_id: d229700f-8165-4e3f-b349-4b9b6dd15fbf
incident_id: NC-S42-0001
status: running
attempt: 1
worker_id: lesson02-A@Leandros-MacBook-Pro.local:87713
current_step: workflow
started_at: 2026-09-16 12:21:42.617147+00:00
completed_at: None
error: None
result: —
```

### uv run control-tower execution d229700f-8165-4e3f-b349-4b9b6dd15fbf

CLI: 0.150 s.

```text
execution_id: d229700f-8165-4e3f-b349-4b9b6dd15fbf
incident_id: NC-S42-0001
status: running
attempt: 1
worker_id: lesson02-A@Leandros-MacBook-Pro.local:87713
current_step: workflow
started_at: 2026-09-16 12:21:42.617147+00:00
completed_at: None
error: None
result: —
```

### uv run control-tower execution d229700f-8165-4e3f-b349-4b9b6dd15fbf

CLI: 0.247 s.

```text
execution_id: d229700f-8165-4e3f-b349-4b9b6dd15fbf
incident_id: NC-S42-0001
status: completed
attempt: 2
worker_id: lesson02-B@Leandros-MacBook-Pro.local:87801
current_step: awaiting_approval
started_at: 2026-09-16 12:23:23.485242+00:00
completed_at: 2026-09-16 12:23:33.572698+00:00
error: None
result: approval pending; actions_executed=false
```

### uv run control-tower events d229700f-8165-4e3f-b349-4b9b6dd15fbf

CLI: 0.168 s.

```text
d229700f-8165-4e3f-b349-4b9b6dd15fbf | eventos: 23 | últimos 12
 12 12:23:33 attempt=2 supply.completed
 13 12:23:33 attempt=2 consolidation.started
 14 12:23:33 attempt=2 consolidation.completed
 15 12:23:33 attempt=2 finance.started
 16 12:23:33 attempt=2 finance.completed
 17 12:23:33 attempt=2 challenger.started
 18 12:23:33 attempt=2 challenger.completed
 19 12:23:33 attempt=2 recommendation.started
 20 12:23:33 attempt=2 recommendation.completed
 21 12:23:33 attempt=2 human_approval.started
 22 12:23:33 attempt=2 human_approval.completed
 23 12:23:33 attempt=2 execution.completed
```

### uv run control-tower result d229700f-8165-4e3f-b349-4b9b6dd15fbf

CLI: 0.156 s.

```text
Workflow completed | approval pending | actions_executed=false
Caso de referência: INCIDENT-001 | modo: mock
Ação: Cenário D: Transferir até o piso de Campinas por rota padrão e replanejar; residual via Alpha
Custo: R$ 12500.00 | multa evitada: R$ 16000.00
Atraso: 3 dias | confiança: 0.65
Riscos: 3 | --json para contrato completo
```

### uv run control-tower events d229700f-8165-4e3f-b349-4b9b6dd15fbf --lifecycle

CLI: 0.164 s.

```text
d229700f-8165-4e3f-b349-4b9b6dd15fbf | eventos: 5 | últimos 12
  1 12:21:42 attempt=1 execution.queued
  2 12:21:42 attempt=1 execution.started
  3 12:23:23 attempt=1 execution.interrupted
  4 12:23:23 attempt=2 execution.started
 23 12:23:33 attempt=2 execution.completed
```

### uv run control-tower enqueue --count 1 --version rehearsal-9dc2f378-duplicate --demo-delay-ms 3000

CLI: 0.498 s.

```text
Publicadas: 1 | novas executions: 1 | existentes: 0
mock | referência INCIDENT-001 | aprovação humana obrigatória
6cbf1fd3-332c-4851-9082-ccefbc235cfc
```

### uv run control-tower enqueue --count 1 --version rehearsal-9dc2f378-duplicate --demo-delay-ms 3000

CLI: 0.475 s.

```text
Publicadas: 1 | novas executions: 0 | existentes: 1
mock | referência INCIDENT-001 | aprovação humana obrigatória
6cbf1fd3-332c-4851-9082-ccefbc235cfc
```

### uv run control-tower execution 6cbf1fd3-332c-4851-9082-ccefbc235cfc

CLI: 0.191 s.

```text
execution_id: 6cbf1fd3-332c-4851-9082-ccefbc235cfc
incident_id: NC-S42-0001
status: completed
attempt: 1
worker_id: lesson02-A@Leandros-MacBook-Pro.local:88272
current_step: awaiting_approval
started_at: 2026-09-16 12:23:35.667731+00:00
completed_at: 2026-09-16 12:23:38.756385+00:00
error: None
result: approval pending; actions_executed=false
```

### uv run control-tower events 6cbf1fd3-332c-4851-9082-ccefbc235cfc

CLI: 0.152 s.

```text
6cbf1fd3-332c-4851-9082-ccefbc235cfc | eventos: 21 | últimos 12
 10 12:23:38 attempt=1 supply.completed
 11 12:23:38 attempt=1 consolidation.started
 12 12:23:38 attempt=1 consolidation.completed
 13 12:23:38 attempt=1 finance.started
 14 12:23:38 attempt=1 finance.completed
 15 12:23:38 attempt=1 challenger.started
 16 12:23:38 attempt=1 challenger.completed
 17 12:23:38 attempt=1 recommendation.started
 18 12:23:38 attempt=1 recommendation.completed
 19 12:23:38 attempt=1 human_approval.started
 20 12:23:38 attempt=1 human_approval.completed
 21 12:23:38 attempt=1 execution.completed
```

### uv run control-tower result 6cbf1fd3-332c-4851-9082-ccefbc235cfc

CLI: 0.149 s.

```text
Workflow completed | approval pending | actions_executed=false
Caso de referência: INCIDENT-001 | modo: mock
Ação: Cenário D: Transferir até o piso de Campinas por rota padrão e replanejar; residual via Alpha
Custo: R$ 12500.00 | multa evitada: R$ 16000.00
Atraso: 3 dias | confiança: 0.65
Riscos: 3 | --json para contrato completo
```

### uv run control-tower events 6cbf1fd3-332c-4851-9082-ccefbc235cfc --lifecycle

CLI: 0.155 s.

```text
6cbf1fd3-332c-4851-9082-ccefbc235cfc | eventos: 3 | últimos 12
  1 12:23:35 attempt=1 execution.queued
  2 12:23:35 attempt=1 execution.started
 21 12:23:38 attempt=1 execution.completed
```

### uv run control-tower execution d229700f-8165-4e3f-b349-4b9b6dd15fbf

CLI: 0.162 s.

```text
execution_id: d229700f-8165-4e3f-b349-4b9b6dd15fbf
incident_id: NC-S42-0001
status: completed
attempt: 2
worker_id: lesson02-B@Leandros-MacBook-Pro.local:87801
current_step: awaiting_approval
started_at: 2026-09-16 12:23:23.485242+00:00
completed_at: 2026-09-16 12:23:33.572698+00:00
error: None
result: approval pending; actions_executed=false
```

### uv run control-tower events d229700f-8165-4e3f-b349-4b9b6dd15fbf

CLI: 0.162 s.

```text
d229700f-8165-4e3f-b349-4b9b6dd15fbf | eventos: 23 | últimos 12
 12 12:23:33 attempt=2 supply.completed
 13 12:23:33 attempt=2 consolidation.started
 14 12:23:33 attempt=2 consolidation.completed
 15 12:23:33 attempt=2 finance.started
 16 12:23:33 attempt=2 finance.completed
 17 12:23:33 attempt=2 challenger.started
 18 12:23:33 attempt=2 challenger.completed
 19 12:23:33 attempt=2 recommendation.started
 20 12:23:33 attempt=2 recommendation.completed
 21 12:23:33 attempt=2 human_approval.started
 22 12:23:33 attempt=2 human_approval.completed
 23 12:23:33 attempt=2 execution.completed
```

### uv run control-tower result d229700f-8165-4e3f-b349-4b9b6dd15fbf

CLI: 0.149 s.

```text
Workflow completed | approval pending | actions_executed=false
Caso de referência: INCIDENT-001 | modo: mock
Ação: Cenário D: Transferir até o piso de Campinas por rota padrão e replanejar; residual via Alpha
Custo: R$ 12500.00 | multa evitada: R$ 16000.00
Atraso: 3 dias | confiança: 0.65
Riscos: 3 | --json para contrato completo
```

### uv run control-tower events d229700f-8165-4e3f-b349-4b9b6dd15fbf --lifecycle

CLI: 0.158 s.

```text
d229700f-8165-4e3f-b349-4b9b6dd15fbf | eventos: 5 | últimos 12
  1 12:21:42 attempt=1 execution.queued
  2 12:21:42 attempt=1 execution.started
  3 12:23:23 attempt=1 execution.interrupted
  4 12:23:23 attempt=2 execution.started
 23 12:23:33 attempt=2 execution.completed
```

### uv run control-tower executions

CLI: 0.158 s.

```text
queued: 0 | running: 0 | completed: 46 | failed: 0
execution_id                         status     attempt worker
6cbf1fd3-332c-4851-9082-ccefbc235cfc completed        1 lesson02-A:88272
d229700f-8165-4e3f-b349-4b9b6dd15fbf completed        2 lesson02-B:87801
f077c8da-9408-4114-aab0-de87df57daf1 completed        2 lesson02-A:87713
ecf29b7a-6ad2-4486-9d75-9dfc076537e0 completed        1 lesson02-B:87716
4ff40777-42b9-4695-b8d5-4ac0e329f114 completed        1 lesson02-B:87716
3f3a84b2-f613-4696-bf94-ca86ee24d9ec completed        1 lesson02-A:87713
a6164137-a2b4-4503-ae92-8d81470cb058 completed        1 lesson02-A:87713
5ae47c0d-f52a-49fc-9b42-1f17b97acb3f completed        1 lesson02-B:87716
```

## Resultado dos testes e limpeza

- Suíte local: 248 passed, 10 skipped (integração opt-in), 10,71 s.
- Integração PostgreSQL: 10 passed, 0,98 s.
- Idempotency do start: 8 passed (subconjunto, não somar ao total).
- Smoke: 12 checks OK. INCIDENT-001 mock: awaiting_approval.
- Total de testes distintos executados: **258 aprovados**.
- Workers próprios encerrados após o ensaio; Compose encerrado mantendo volumes.
- Nenhuma tag criada/movida. Sem alteração de código de aplicação ou arquitetura.
