# Parecer — candidato lesson-02-start

Data do ensaio: 16/09/2026. Base congelada da Aula 1: `8fbc4fc`.
Branch: `codex/lesson-02-start`. Nenhuma tag criada/movida; nenhuma publicação desta revisão.

## Resultado técnico — APROVAR o start

- Suíte completa: **230 testes aprovados em 11,03 s**: 169 regressões existentes + 61 novos testes.
- Idempotência isolada: 8 testes aprovados. Identidade estável, mudança de escopo/versão e colisões
  de concatenação testadas; não há deduplicação distribuída implementada.
- 60 arquivos da Aula 1 protegidos por manifest de hashes em `tests/fixtures/lesson01-frozen.json`.
  Abrange agentes, grafo, dados, fixtures, contratos, testes e materiais específicos da Aula 1.
- Única mudança no código existente da Aula 1: import de sys e despacho de três comandos novos em main.py.
  O parser e os fluxos antigos permanecem intactos. Todas as 48 versões do lock anterior foram mantidas.
- Smoke Aula 1: 12 checks passaram. INCIDENT-001 em mock terminou awaiting_approval, sem ações.
- Generator: 500 envelopes, IDs únicos, seed 42 e mix exato 120/85/140/65/90; export JSONL válido.
  Testes verificam repetibilidade e ausência de alteração do gerador aleatório global.
- Batch: códigos 0, nenhum erro nos cinco ensaios; cada envelope recebe execution_id/estado/eventos próprios.
- Concorrência testada com barreiras entre threads; join da Aula 1 ainda exige os três especialistas.
  Limite de capacidade testado por pico real de ocupação, sem assert de tempo absoluto frágil.
- Teste de falha confirma isolamento por execução, liberação do slot, continuidade do lote e attempt=1.
- Teste de duplicate delivery confirma a limitação real: duas entregas ainda geram duas execuções.
- Rede bloqueada em teste mesmo com LLM_MODE=openai/LangSmith ativados: batch permanece mock offline.
- Contratos validam lifecycle, datas com fuso, ordem temporal, durations/tokens/custos e score; campos futuros null.
- Compose: `docker compose config --quiet` aprovado. Redis 7.4 / PostgreSQL 16 iniciados e healthy.
  `redis-cli ping` → PONG; `pg_isready` → accepting connections.
  Serviços encerrados com `docker compose down`; volumes didáticos preservados.
- Configuração limita portas a loopback e contém somente os dois serviços. Sem aplicação/worker containerizado.
- Celery/Redis e psycopg preparados no extra lesson02; não importados pelo runner local.
- O modo OpenAI da Aula 1 não foi alterado nem consumiu chamadas neste ensaio. Seus testes existentes passaram.

## Resultados observados — não são benchmark de produção

Espera artificial: 500 ms por workflow, dentro da capacidade simulada.

| Incidentes | Workers locais | Capacidade | Duração | Throughput | Entradas que esperaram |
|---:|---:|---:|---:|---:|---:|
| 10 | 1 | sem limite adicional | 5,231 s | 1,91/s | 0 |
| 10 | 5 | sem limite adicional | 1,111 s | 9,00/s | 0 |
| 50 | 5 | 5 | 5,536 s | 9,03/s | 0 |
| 50 | 20 | 5 | 5,583 s | 8,96/s | 15 |
| 50 | 50 | 5 | 5,524 s | 9,05/s | 45 |

Os três últimos ensaios atingiram pico ativo 5. A pequena variação de throughput é ruído/overhead local,
não ganho proporcional a workers. [Outputs completos](demo-outputs.md).

## Resultado pedagógico — APROVAR o start

- Agenda de 240 minutos. Runbook e observation guide orientam o professor; nenhum exercício de programação.
- Demo 1 executável: 10 incidentes com 1 vs 5 workers. Demo 2 executável: 50 com 5/20/50 e capacidade 5.
- Demo 3 deliberadamente conceitual: fila/Celery/store ainda não integrados. Docker healthy não é prova
  de execução distribuída, apenas de infraestrutura preparada.
- Demo 4: helper e testes executáveis, reentrega/atomicidade/retry discutidos conceitualmente.
- Saídas curtas projetáveis: até 16 linhas por batch (sem o aviso opcional de exportação).
- Discussão separa agentes dentro do grafo, threads entre workflows e futuros workers em outros processos.
- “Completed” distingue término computacional de aprovação/resolução de negócio.
- Exemplo de Execution e tabela de eventos prontos; instalação, exports extensos e pulls fora da aula.
- Segunda metade do roteiro permanece conceitual no start e precisa ser refinada com a implementação complete.

## Limitações preservadas para a revisão

- Os cinco tipos e quatro plantas são fixtures de chegada. O batch faz replay do mesmo INCIDENT-001
  por envelope, sem interpretar os payloads das novas categorias ou priorizar business_priority.
- Semáforo simula slots por workflow; não implementa rate limit de OpenAI ou backpressure distribuído.
  O intake materializa todo o lote em memória; há limite didático de 5.000 envelopes e 64 threads.
- Estado e eventos só existem em memória. Export após o lote não é state store, checkpoint ou resume.
- A chave de idempotência não reivindica execução atomicamente. Nenhum retry automático ou exactly-once.
- Tempos foram medidos uma vez em ambiente local; não representam capacidade de produção.
- Não foram testados Windows/Linux nesta rodada. Mock não requer Docker após dependências instaladas.

## Reservado ao lesson-02-complete

Integração Redis/Celery, consumidores reais, armazenamento PostgreSQL de Execution/eventos/resultados,
reentrega/retry e reivindicação atômica da identidade. Resume/checkpoint distribuído continua fora deste start.
Nenhuma implementação de FastAPI, OTel, Langfuse, Kubernetes, Control Plane, Agent Harness ou Hermes.

Referências de infraestrutura: [health checks em Compose](https://docs.docker.com/compose/how-tos/startup-order/)
e [dependências opcionais Celery/Redis](https://docs.celeryq.dev/en/stable/getting-started/introduction.html).
