# Validação técnica e pedagógica — candidato lesson-02-complete

## Parecer: APROVAR para revisão do checkpoint

Escopo restrito à Aula 2. Sem tag nova, sem mover tags, sem publicação. Branch local
`codex/lesson-02-complete`. Aula 1 e baseline local do start continuam disponíveis.

## Resultado técnico

- Suíte local completa: **248 passed** (230 anteriores + 18 novos); testes de integração são opt-in.
- Integração PostgreSQL: **10 passed**, com schemas isolados e removidos ao final.
- Total executado: **258 testes aprovados**. Os 28 novos cobrem contratos/configuração, task/producer,
  persistência, claim atômico concorrente, lock, retry, tentativas, eventos, resultado e falha terminal.
- Smoke Aula 1: 12 verificações OK. INCIDENT-001 mock ponta a ponta: awaiting_approval, ações=false.
- Batch local 10/1, 10/5 e 50/{5,20,50}/capacity5 executados novamente, sem falhas.
- Gerador 500 executado; mix determinístico preservado.
- Compose config válido; Redis PONG e PostgreSQL accepting connections.
- Dois workers Celery solo reais processaram o lote de 20; worker_id comprova A e B.
- Duas publicações da mesma operação retornaram uma Execution, attempt=1.
- Logistics falhou na tentativa 1; self.retry; tentativa 2 completed.
- SIGKILL do worker B durante processamento: redelivery para A, mesmo UUID, attempt=2, completed.
- **85,410 s** entre início da primeira e da segunda tentativa no ensaio de queda. A segunda executou
  o delay didático de 10 s. Visibility timeout de 60 s não implica recuperação exatamente em 60 s.
- Consultas após parar workers confirmaram durabilidade: 23 completed, queued/running/failed=0.
- Views curtas verificadas com até 100 colunas; variantes JSON de execution/events/result/executions válidas.
- Workers próprios encerrados. `docker compose down` removeu containers/rede; volumes preservados.

[Transcrições reais](complete-demo-outputs.md) · [Execution](durable-execution-example.json) ·
[Eventos completos](durable-events-example.json).
Logs brutos do ensaio ficam em artifacts/lesson02-complete (ignorados pelo Git).
O script `scripts/validate_lesson02_complete.py` reproduz o ensaio usando novas versões por rodada,
sem purge/flush. Requer broker/banco de laboratório sem outros consumidores da queue lesson02.

## Preservação

Nenhum agente, tool, grafo, dataset ou teste anterior da Aula 1 foi alterado. A CLI principal apenas
encaminha comandos novos; a regressão verifica 60 arquivos congelados. As dependências extras já
estavam no start aprovado. Batch/gerador/modelos/eventos/idempotency helper locais mantidos.

Tags verificadas, mesmos destinos:

- lesson-01-start: `5dc5fa09782c74dd61fe83b56a6c6dc8b0311afb`
- lesson-01-complete: `7bf48f68277a2414666773b200e679cee60b1f57`

A linha de base funcional da Aula 1 continua sendo 8fbc4fc, posterior à tag histórica complete.
Nenhuma tag da Aula 2 foi criada. Nenhuma chamada OpenAI foi feita nesta validação; a task distribuída
usa mock explícito e os modos da CLI da Aula 1 permanecem preservados por regressão.

## Decisões técnicas

- Celery padrão com Redis; não há framework próprio de filas ou wrapper de worker.
- PostgreSQL é fonte de Execution/Event/resultado; não há backend de resultado Celery duplicado.
- JSONB Pydantic mantém código curto; constraints relacionais garantem chave única e sequência por execução.
- Advisory lock de sessão impede duas entregas ativas da mesma chave em condições do laboratório.
- Retry controlado máximo 3 tentativas, backoff 2/4 s; contador durável também limita worker losses.
- State/event/result são persistidos; estado interno do grafo não. Recuperação repete a execução inteira.
- Solo facilita reprodução em macOS e torna PID/worker visíveis. Não é recomendação de pool para produção.

## Ensaio pedagógico

| Demo | Reserva em aula | Observação |
|---|---:|---|
| 1. Concorrência local | 25 min | Comandos levam segundos; priorizar hipóteses/comparação |
| 2. Limite de capacidade | 20 min | Mesma carga/capacidade nas três rodadas |
| 3. Queue + Workers | 25 min | Publicar antes de iniciar workers torna queued visível |
| 4. Retry + worker failure | 25 min | Reservar 2–3 min de recuperação; discutir estado running enquanto espera |
| 5. Duplicate delivery | 25 min | Repetir parâmetros idênticos; não confundir versão nova com duplicata |
| 6. Histórico durável | 20 min | Parar workers antes de consultar; JSON fica para reprodução posterior |

Agenda completa soma 240 min, com intervalo de 15 min e 65 min explícitos de contexto/teoria.
Snippets prontos de aproximadamente 10–30 linhas evitam digitação de boilerplate. Resultados e
trilhas gravados são fallbacks. Não há programação pelos alunos.

Pontos que exigem fala explícita:

1. completed não significa compra aprovada.
2. Envelopes de cinco categorias repetem um caso de referência, não cinco análises de negócio novas.
3. Counters da CLI são do banco e cumulativos; não medem diretamente tamanho exato do broker.
4. Backlog absorve picos; prefetch limita reserva, mas admissão do producer ainda não é limitada.
5. Retry tratado e redelivery após SIGKILL são mecanismos distintos.
6. `idempotency-demo` continua sendo o helper local do start; a proteção real está em enqueue/task/store.

## Limitações deliberadas

At-least-once delivery + idempotent processing; sem exactly-once. Não há checkpoint por nó,
transactional outbox, DLQ avançada, HA/backup, fencing de efeitos externos ou tratamento completo
de partições de rede. Claim e publicação não são atômicos: reenviar os mesmos parâmetros republica
uma operação queued sem mensagem. Banco/broker precisam permanecer saudáveis para a demo de worker loss.

Sem FastAPI, containers da aplicação, Kubernetes, autoscaling, telemetria, dashboards, Control Plane,
Harness/Hermes ou antecipação das Aulas 3/4. [Semântica detalhada](distributed-contracts.md).
