# Contratos duráveis — candidato complete

O baseline local e seus contratos em `models.py`/`events.py` permanecem intactos.
`durable.py` estende Execution e ExecutionEvent; o vocabulário pontuado é exclusivo do fluxo distribuído.

## Execution

Todos os campos do start, mais `idempotency_key` e `result` tipados. `result` contém somente
Recommendation + Approval, modo efetivo (mock/openai/degraded), outcome, motivo/modelo quando aplicáveis e identificação do caso de referência. **Não armazena o estado
interno completo do LangGraph.** `execution_id` permanece o mesmo em todas as tentativas.
`attempt` começa em 1; a coluna interna `attempts` começa em 0 antes da primeira aquisição.

`queued → running → completed/failed`. Em falha recuperável: evento failed, estado queued + evento retry,
e depois running na tentativa seguinte. Os dois primeiros eventos são gravados na mesma transação;
portanto a CLI pode observar diretamente queued. Horários e worker refletem a tentativa atual/última;
o histórico preserva as tentativas anteriores. `current_step` é o último callback observado,
não a lista de todos os especialistas ativos em paralelo.

`completed` exige resultado validado. No outcome human_review_required, o resultado não contém
Recommendation: a decisão de encaminhamento terminou, mas o workflow não produziu recomendação.
Approval permanece pending, actions_executed=false. duration_ms mede a tentativa, sem espera em fila.
Nenhuma compra, transferência ou transporte é executado.

## ExecutionEvent

Mesmos campos do start, com `detail` opcional e nomes como `execution.queued`, `execution.started`,
`supervisor.completed`, `supply.completed`, `production.completed`, `logistics.completed`,
`finance.completed`, `challenger.completed`, `recommendation.completed`, `execution.completed`.
Há também `.started`, `.failed`, `execution.retry` e `execution.interrupted`.

Sequência crescente por execution, atualizada na mesma transação do INSERT do evento.
Callbacks concorrentes usam um lock local para serializar acesso à conexão do worker.
Eventos e alterações de estado associadas são atômicos. Timestamps têm fuso UTC; duração de nó
usa relógio monotônico. input_tokens/output_tokens são preenchidos somente em llm.completed quando a resposta OpenAI
contém usage. Permanecem null em mock/falha artificial. Custo, qualidade e business_outcome continuam null.
Eventos llm.requested/failed/retry/fallback_activated/degraded/escalated são aditivos; não há tracing.

## Claim e exclusão mútua

1. Producer calcula SHA-256 de `[incident_id, operation, version]`.
2. `UNIQUE(idempotency_key)` + `INSERT ... ON CONFLICT DO NOTHING` escolhem uma única Execution.
3. Mesmo envelope/opções retorna identidade existente; conteúdo diferente sob mesma chave é erro.
4. Cada entrega tenta um **advisory lock de sessão PostgreSQL** derivado da chave.
5. Outra entrega ativa não executa o grafo. Completed/failed terminal também não reexecuta.
6. Morte do processo fecha a conexão e libera o lock; redelivery pode iniciar outra tentativa.

Não há transação aberta durante o workflow: commits curtos tornam eventos visíveis ao professor.
O lock pertence à conexão, mantida por toda a task; PostgreSQL também precisa estar disponível.
Uma colisão improvável do hash do advisory lock pode serializar operações independentes; a constraint
usa a chave completa. Isso não é um protocolo de fencing para efeitos externos.

**At-least-once delivery + idempotent processing.** Não existe garantia de exactly-once.
Uma tentativa pode repetir cálculos. A proteção não autoriza efeitos de negócio irreversíveis.

## Entrega, ack e falha

- `acks_late=True`: ack após término da task.
- `task_reject_on_worker_lost=True`: perda de filho prefork pode ser requeued pelo processo pai.
- Demo portátil usa **solo**, um processo por worker. SIGKILL mata o worker inteiro; não há pai Celery
  vivo para rejeitar a entrega. Redis restaura a mensagem não confirmada após visibility timeout.
- Timeout didático 60 s; restauração é periódica, portanto 60 s não é SLA de recuperação.
- `worker_prefetch_multiplier=1`: com late ack reduz reserva antecipada. Slots de workers limitam
  processamento e o restante espera no broker. Não há admissão limitada no producer; backlog pode crescer.
- Falha didática de especialista na primeira tentativa usa `self.retry`, backoff 2/4 s, máximo 3 tentativas.
- Contagem durável limita também redeliveries por perda repetida de processos; a quarta aquisição
  marca failed sem executar o grafo. Não há DLQ sofisticada nem recuperação por nó.
- Falhas não classificadas como recuperáveis encerram em failed, sem retry genérico ilimitado.

## Janelas e limites honestos

Commit do claim e publicação Redis **não são uma transação única**. Se o producer cair entre eles,
a Execution pode ficar queued sem mensagem. Repetir `enqueue` com os mesmos parâmetros republica
a mesma identidade. Não implementamos transactional outbox nesta aula. O mesmo cuidado vale se a
publicação de um retry falhar. Erros de conectividade entre banco/broker/worker exigem diagnóstico;
esta aula valida queda de processo com Redis e PostgreSQL saudáveis, não todas as partições de rede.

60 s permanece no perfil mock/SIGKILL. O bloco OpenAI usa 900 s em producer e todos os workers,
reiniciados entre perfis. Requests reais podem demorar mais; 60 s poderia reentregar trabalho ainda ativo.
A CLI da Aula 1 permanece intacta. A task agora permite mock/OpenAI no mesmo grafo.
Ver [continuidade LLM](llm-continuity.md).
Redis AOF e volumes locais não substituem HA/backup; não usar `down -v` se quiser preservar dados.
O banco guarda documentos JSONB validados por Pydantic, constraints de identidade e tabelas de eventos.
Não há migrations framework, pooling nem backend de resultados Celery: PostgreSQL é a fonte consultada.

Referências: [Celery tasks/ack](https://docs.celeryq.dev/en/stable/userguide/tasks.html),
[Redis visibility timeout](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html),
[prefetch](https://docs.celeryq.dev/en/stable/userguide/optimizing.html),
[PostgreSQL advisory locks](https://www.postgresql.org/docs/16/explicit-locking.html#ADVISORY-LOCKS).
