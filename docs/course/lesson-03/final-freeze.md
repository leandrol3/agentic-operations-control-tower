# Fechamento formal — 30/09/2026

## Regressão final

Suíte com as três integrações habilitadas: **351 passed in 17.73s**.
Smoke Aula 1 OK; Aula 2 batch mock 10 completed, 0 failed, 0,346 s.
Aula 3 start: PASS mock (incluindo idempotência), PASS health/readiness.
Compose config e up passaram. Imagem já construída e validada no ensaio anterior foi reutilizada:
nenhuma alteração funcional da aplicação ocorreu neste fechamento. Build não precisou ser repetido.

Encontrada e corrigida uma inconsistência de isolamento: fixture dos testes do start herdava
OTEL_ENABLED do shell. Agora declara otel_enabled=False, correspondente ao comportamento que testa.
Primeira execução: 2 falhas/349 sucessos; após correção, 351 sucessos. Sem alteração da aplicação.

## Traces desta rodada

| Caso | Execution ID | Trace ID | Spans | Tentativa persistida | Helper | Outcome |
|---|---|---|---:|---:|---:|---|
| normal | `17d40f9c-8809-420c-9ecb-89ae9c06ec5b` | `d4e9cc5e945c76afcf20cd9a54807aac` | 25 | 30.30 ms | 1.356 s | recommendation |
| bottleneck | `c61d8f7c-bf62-451f-a3c6-da71139b2b7a` | `7ee0e7ee8db73faf6a0ec94191c1d8c8` | 25 | 1772.02 ms | 2.573 s | recommendation |
| failure | `5cd0e67e-8776-47c0-bcd6-4916fe4646bc` | `1284ab80f2ecabc6bde1226fe58217f8` | 29 | 1289.06 ms | 3.212 s | degraded_recommendation |

[Artefatos desta rodada](captures/final-2026-09-30/normal-summary.json). Os demais arquivos estão na
mesma pasta: JSON integral do backend, árvores, summaries e saída da suíte/smokes.
As capturas anteriores e o overhead didático permanecem preservados. Os tempos são observações locais,
não benchmark científico, nem overhead universal. Falha artificial não chama OpenAI.

## Validações do professor

Smoke OpenAI real e full pedagogical rehearsal aprovados pelo professor. Data/hora, modelo,
execution_id, trace_id, latência, spans e usage desse smoke não foram fornecidos: ver campos
explicitamente não informados em [validation.md](validation.md). Nenhum valor inferido ou chamada paga
repetida. Todas as demos aprovadas; aula considerada ministrável em 4h. Setup/build/pull fora da agenda.

## Checkpoints e Git

Tags existentes preservadas, incluindo objetos anotados e commits:

- lesson-01-start: objeto 3d880c9ed7f9b679980bc17dc91660d8d79b2f81; commit 5dc5fa09782c74dd61fe83b56a6c6dc8b0311afb.
- lesson-01-complete: objeto b306d3a5f4437df25a902b11a368e45efd30ec0c; commit 7bf48f68277a2414666773b200e679cee60b1f57.

As tags lesson-02-start, lesson-02-complete e lesson-03-start não existem localmente nem no remoto
consultado. Não foram criadas retroativamente. Branches anteriores preservadas:

- codex/lesson-02-start: 8fbc4fc2ca4a744ee89d2b2e9d54a326c801baf5.
- codex/lesson-02-complete: d3a67ad9ce71fd3a67e3e67ec29bf682f4eca70d.
- codex/lesson-03-start: ff3166dde434f1b68954580bc33d7ab906e12e4f.

A alteração preexistente em docs/course/lesson-02-runbook.md fica fora do commit do checkpoint.
Branch final: codex/lesson-03-complete. Tag anotada local; push não autorizado nesta tarefa.

## Limites preservados

Jaeger em memória e telemetria best effort; capturas são fallback. Mock não é inferência real.
Approval permanece obrigatório. Sem novos agentes, grafo, contratos, demos ou instrumentação.
Aula 4: qualidade, economia, valor, SLO, routing avançado e Control Plane permanecem fora de escopo.

## Collector indisponível e encerramento

Collector parado: health 200, ready 200, POST 202, execução completed.
[Evidência desta rodada](captures/final-2026-09-30/collector-down.json).
Collector reiniciado; `docker compose down` concluído com sucesso, sem remover volumes.

**Status final: APPROVED.** lesson-03-complete concluído e congelado após commit/tag local.
