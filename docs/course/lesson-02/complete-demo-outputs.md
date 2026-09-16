# Ensaio real — candidato lesson-02-complete

Ensaio em 2026-09-16 UTC, com Redis/PostgreSQL reais e dois workers Celery solo.
Workload mock de referência INCIDENT-001. Sem chamadas pagas. Tempos são observações locais, não benchmark.
UUIDs abaixo pertencem ao ensaio; na reprodução use os novos UUIDs impressos.

## Demos 1 e 2 — baseline preservado

```text
$ uv run control-tower batch --incidents 10 --workers 1 --demo-delay-ms 500
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 10
workers: 1
provider_limit: sem limite adicional | pico ativo: 1
completed: 10
failed: 0
duration: 5.238 s
throughput: 1.91 incidents/s (completed)
waited: 0 | pico esperando capacidade: 0
provider_wait_total: 0.000 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

```text
$ uv run control-tower batch --incidents 10 --workers 5 --demo-delay-ms 500
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 10
workers: 5
provider_limit: sem limite adicional | pico ativo: 5
completed: 10
failed: 0
duration: 1.066 s
throughput: 9.38 incidents/s (completed)
waited: 0 | pico esperando capacidade: 0
provider_wait_total: 0.000 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

```text
$ uv run control-tower batch --incidents 50 --workers 5 --provider-limit 5 --demo-delay-ms 500
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 50
workers: 5
provider_limit: 5 | pico ativo: 5
completed: 50
failed: 0
duration: 5.473 s
throughput: 9.14 incidents/s (completed)
waited: 0 | pico esperando capacidade: 0
provider_wait_total: 0.000 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

```text
$ uv run control-tower batch --incidents 50 --workers 20 --provider-limit 5 --demo-delay-ms 500
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 50
workers: 20
provider_limit: 5 | pico ativo: 5
completed: 50
failed: 0
duration: 5.580 s
throughput: 8.96 incidents/s (completed)
waited: 15 | pico esperando capacidade: 15
provider_wait_total: 67.003 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

```text
$ uv run control-tower batch --incidents 50 --workers 50 --provider-limit 5 --demo-delay-ms 500
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 50
workers: 50
provider_limit: 5 | pico ativo: 5
completed: 50
failed: 0
duration: 5.590 s
throughput: 8.94 incidents/s (completed)
waited: 45 | pico esperando capacidade: 45
provider_wait_total: 125.578 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

## Demo 3 — fila e dois workers

Lote de 20: todos completed, nenhum failed; worker_id confirmou A e B.
Os eventos abaixo são de uma das execuções. O ensaio automatizado usa version única para preservar histórico.

```text
$ control-tower enqueue --count 20 --version validation-f3360f7b-batch --demo-delay-ms 500
Publicadas: 20 | novas executions: 20 | existentes: 0
mock | referência INCIDENT-001 | aprovação humana obrigatória
d7cb1df5-2d2c-422d-b3b6-7958f4d65c55
ce307123-9111-4cec-9f6c-d3bd08c878ec
55bf2249-f868-4725-ae10-ba44139002b6
f4939747-ae0c-4862-a918-7c7c9d5ca47f
bca25970-25d5-47a1-85c9-6eaaf53f4b17
5aa1b57d-75fb-42b5-97d8-c36337ada8d4
6a4279dc-8ef5-4f67-acc2-b82cfae2d9ea
1d1cfeed-2306-4550-86d6-a2155c17392b
... mais 12; consulte executions
```

```text
$ control-tower enqueue --count 1 --version validation-f3360f7b-duplicate --demo-delay-ms 1500
Publicadas: 1 | novas executions: 1 | existentes: 0
mock | referência INCIDENT-001 | aprovação humana obrigatória
66517718-f700-4554-87fb-936b396320b9
```

```text
$ control-tower enqueue --count 1 --version validation-f3360f7b-duplicate --demo-delay-ms 1500
Publicadas: 1 | novas executions: 0 | existentes: 1
mock | referência INCIDENT-001 | aprovação humana obrigatória
66517718-f700-4554-87fb-936b396320b9
```

## Execução do lote

```text
$ uv run control-tower execution d7cb1df5-2d2c-422d-b3b6-7958f4d65c55
execution_id: d7cb1df5-2d2c-422d-b3b6-7958f4d65c55
incident_id: NC-S42-0001
status: completed
attempt: 1
worker_id: lesson02-A@Leandros-MacBook-Pro.local:3399
current_step: awaiting_approval
started_at: 2026-09-16 04:51:31.460667+00:00
completed_at: 2026-09-16 04:51:32.012139+00:00
error: None
result: approval pending; actions_executed=false
```

```text
$ uv run control-tower events d7cb1df5-2d2c-422d-b3b6-7958f4d65c55 --lifecycle
d7cb1df5-2d2c-422d-b3b6-7958f4d65c55 | eventos: 3 | últimos 12
  1 04:51:31 attempt=1 execution.queued
  2 04:51:31 attempt=1 execution.started
 21 04:51:32 attempt=1 execution.completed
```

## Demo 4A — retry controlado

```text
$ uv run control-tower execution d6e6148e-34b2-4c65-a061-3455fd306900
execution_id: d6e6148e-34b2-4c65-a061-3455fd306900
incident_id: NC-S42-0001
status: completed
attempt: 2
worker_id: lesson02-A@Leandros-MacBook-Pro.local:3399
current_step: awaiting_approval
started_at: 2026-09-16 04:51:43.966160+00:00
completed_at: 2026-09-16 04:51:44.060230+00:00
error: None
result: approval pending; actions_executed=false
```

```text
$ uv run control-tower events d6e6148e-34b2-4c65-a061-3455fd306900 --lifecycle
d6e6148e-34b2-4c65-a061-3455fd306900 | eventos: 7 | últimos 12
  1 04:51:41 attempt=1 execution.queued
  2 04:51:41 attempt=1 execution.started
  8 04:51:41 attempt=1 logistics.failed
 15 04:51:41 attempt=1 execution.failed
 16 04:51:41 attempt=1 execution.retry
 17 04:51:43 attempt=2 execution.started
 36 04:51:44 attempt=2 execution.completed
```

## Demo 4B — morte do worker

Worker encerrado por SIGKILL: `lesson02-B@Leandros-MacBook-Pro.local:3400`.
A mesma execution foi concluída por `lesson02-A@Leandros-MacBook-Pro.local:3399`, tentativa 2.
O registro interrupted é emitido na recuperação, não no instante exato da morte.

```text
$ uv run control-tower execution 212cd880-dbfe-4e43-a863-429ef5c54e61
execution_id: 212cd880-dbfe-4e43-a863-429ef5c54e61
incident_id: NC-S42-0001
status: completed
attempt: 2
worker_id: lesson02-A@Leandros-MacBook-Pro.local:3399
current_step: awaiting_approval
started_at: 2026-09-16 04:53:10.784883+00:00
completed_at: 2026-09-16 04:53:20.870008+00:00
error: None
result: approval pending; actions_executed=false
```

```text
$ uv run control-tower events 212cd880-dbfe-4e43-a863-429ef5c54e61 --lifecycle
212cd880-dbfe-4e43-a863-429ef5c54e61 | eventos: 5 | últimos 12
  1 04:51:45 attempt=1 execution.queued
  2 04:51:45 attempt=1 execution.started
  3 04:53:10 attempt=1 execution.interrupted
  4 04:53:10 attempt=2 execution.started
 23 04:53:20 attempt=2 execution.completed
```

## Demo 5 — duplicate delivery

```text
$ uv run control-tower execution 66517718-f700-4554-87fb-936b396320b9
execution_id: 66517718-f700-4554-87fb-936b396320b9
incident_id: NC-S42-0001
status: completed
attempt: 1
worker_id: lesson02-A@Leandros-MacBook-Pro.local:3399
current_step: awaiting_approval
started_at: 2026-09-16 04:51:39.044524+00:00
completed_at: 2026-09-16 04:51:40.663507+00:00
error: None
result: approval pending; actions_executed=false
```

```text
$ uv run control-tower events 66517718-f700-4554-87fb-936b396320b9 --lifecycle
66517718-f700-4554-87fb-936b396320b9 | eventos: 3 | últimos 12
  1 04:51:38 attempt=1 execution.queued
  2 04:51:39 attempt=1 execution.started
 21 04:51:40 attempt=1 execution.completed
```

## Demo 6 — consulta depois de parar os workers

Consultas reais realizadas sem workers ativos. PostgreSQL continuava disponível.

```text
$ uv run control-tower result 212cd880-dbfe-4e43-a863-429ef5c54e61
Workflow completed | approval pending | actions_executed=false
Caso de referência: INCIDENT-001 | modo: mock
Ação: Cenário D: Transferir até o piso de Campinas por rota padrão e replanejar; residual via Alpha
Custo: R$ 12500.00 | multa evitada: R$ 16000.00
Atraso: 3 dias | confiança: 0.65
Riscos: 3 | --json para contrato completo
```

```text
$ uv run control-tower executions
queued: 0 | running: 0 | completed: 23 | failed: 0
execution_id                         status     attempt worker
212cd880-dbfe-4e43-a863-429ef5c54e61 completed        2 lesson02-A:3399
d6e6148e-34b2-4c65-a061-3455fd306900 completed        2 lesson02-A:3399
66517718-f700-4554-87fb-936b396320b9 completed        1 lesson02-A:3399
a431dde0-f058-4b50-a62a-068f2bd0edde completed        1 lesson02-A:3399
c7ae28a4-e7c7-4e1b-9aaa-6630282a37bc completed        1 lesson02-B:3400
b25ad4f6-f4e1-46cb-b210-b22b2e629c36 completed        1 lesson02-B:3400
7849f496-dffd-4db1-943c-4ad83969f368 completed        1 lesson02-A:3399
a625bbd3-8fca-4f91-bc73-f70109c3c35c completed        1 lesson02-B:3400
```

## Contratos completos persistidos

[Execution com resultado](durable-execution-example.json) · [Eventos completos](durable-events-example.json).
Não projetar JSON completo por padrão; CLI execution/events/result é a view curta.
Events --lifecycle omite nós bem-sucedidos; a sequência tem lacunas porque preserva os números originais.
