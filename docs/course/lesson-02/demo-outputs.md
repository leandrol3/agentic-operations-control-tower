# Aula 2 — outputs reais do ensaio

Ensaio local em 16/09/2026; espera artificial de 500 ms por workflow. Não é benchmark de produção.
O ensaio também salvou snapshots; o aviso de exportação foi omitido das saídas projetáveis.

## batch-10-w1

```bash
uv run control-tower batch --incidents 10 --workers 1 --demo-delay-ms 500
```

```text
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 10
workers: 1
provider_limit: sem limite adicional | pico ativo: 1
completed: 10
failed: 0
duration: 5.231 s
throughput: 1.91 incidents/s (completed)
waited: 0 | pico esperando capacidade: 0
provider_wait_total: 0.000 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

## batch-10-w5

```bash
uv run control-tower batch --incidents 10 --workers 5 --demo-delay-ms 500
```

```text
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 10
workers: 5
provider_limit: sem limite adicional | pico ativo: 5
completed: 10
failed: 0
duration: 1.111 s
throughput: 9.00 incidents/s (completed)
waited: 0 | pico esperando capacidade: 0
provider_wait_total: 0.000 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

## batch-50-w5-limit5

```bash
uv run control-tower batch --incidents 50 --workers 5 --provider-limit 5 --demo-delay-ms 500
```

```text
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 50
workers: 5
provider_limit: 5 | pico ativo: 5
completed: 50
failed: 0
duration: 5.536 s
throughput: 9.03 incidents/s (completed)
waited: 0 | pico esperando capacidade: 0
provider_wait_total: 0.000 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

## batch-50-w20-limit5

```bash
uv run control-tower batch --incidents 50 --workers 20 --provider-limit 5 --demo-delay-ms 500
```

```text
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 50
workers: 20
provider_limit: 5 | pico ativo: 5
completed: 50
failed: 0
duration: 5.583 s
throughput: 8.96 incidents/s (completed)
waited: 15 | pico esperando capacidade: 15
provider_wait_total: 66.975 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

## batch-50-w50-limit5

```bash
uv run control-tower batch --incidents 50 --workers 50 --provider-limit 5 --demo-delay-ms 500
```

```text
Batch execution | mock | threads locais, sem Celery
Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.
----------------
incidents: 50
workers: 50
provider_limit: 5 | pico ativo: 5
completed: 50
failed: 0
duration: 5.524 s
throughput: 9.05 incidents/s (completed)
waited: 45 | pico esperando capacidade: 45
provider_wait_total: 123.788 worker-s (somatório, não duração)
delay didático: 500 ms por execução; não é benchmark de produção.
completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.
Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.
```

## Generator — 500 envelopes

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

## Idempotency helper

```text
Idempotency contract | NC-S42-0001 | analyze-reference | v1
idempotency_key: idem-v1-74fa8f63726e8644c2b41d5b2d5f8b16e2661c4138c78e3414c243c74a368685
Duas entregas, mesma chave: True
Helper não elimina duplicatas. Retry/reivindicação atômica ficam para o complete.
```
