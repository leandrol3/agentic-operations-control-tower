# Distribuição — Aula 2

O baseline do start (`incidents`, `batch`, `models`, `events`, `idempotency`, `cli`) permanece local e
preservado. O complete acrescenta `celery_app`, `tasks`, `producer`, `store`, `durable`, `config` e
`remote_cli`. Não há scheduler/queue próprios, API, telemetria ou checkpoint LangGraph.

- Producer persiste claim único e publica mensagem Celery no Redis.
- Task adquire lock PostgreSQL e chama o workflow original da Aula 1 em mock ou openai.
- Estado/eventos/resultado validado são duráveis; consultas não dependem do worker.
- Retry e redelivery repetem o workflow inteiro; não executam ações de negócio.
- Credenciais locais públicas do Compose são apenas para laboratório. Mock não lê chave; openai
  usa Settings da Aula 1, sem enviar credenciais para broker/store.

[Runbook](../../../docs/course/lesson-02-runbook.md) ·
[Contratos, janelas de falha e limites](../../../docs/course/lesson-02/distributed-contracts.md)

O batch local preserva as métricas: duration exclui geração/export, throughput=completed/duration,
provider_wait soma worker-segundos; limite simulado não é rate limit real nem admissão de produtores.
No fluxo distribuído, a CLI mostra contadores do banco, não métrica exata do tamanho da fila Redis.

`llm_runtime.py` acrescenta retry de request e eventos mínimos; tasks.py decide degradação explícita
ou encaminhamento humano. Sem outro grafo/provider/router. Ver llm-continuity.md no material da Aula 2.
