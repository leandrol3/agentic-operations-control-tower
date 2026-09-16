# Demo distribuída OpenAI e continuidade — outputs reais

Ensaio em 2026-09-16, gpt-4.1-mini, três envelopes sintéticos, dois workers locais.
Mesmo workflow LangGraph/dados/tools da Aula 1. Sem prompts ou respostas extensas nesta view.
Tempos medem processamento por tentativa; não incluem espera na fila.

## Execuções

| execution_id | worker | modo | outcome | duração |
|---|---|---|---|---:|
| 72e2030c-efdd-41d7-9821-2e23db777849 | llm-A | openai | recommendation | 13.27 s |
| 5b746d9e-e021-4a1e-81d4-18389fcfb64e | llm-B | openai | recommendation | 19.31 s |
| fc3e9650-4308-4d30-aea7-8c18c2d4535b | llm-A | openai | recommendation | 11.74 s |
| 0d899179-c498-4ead-9a75-7c1c590fb25b | llm-A | degraded | degraded_recommendation | 1.12 s |
| 814f0f53-7b51-4e3f-af13-556a404ceaf0 | llm-B | openai | human_review_required | 1.04 s |

## Estados projetados durante a carga real

Contadores são cumulativos e incluem ensaios anteriores. As três linhas recentes identificam este lote.

```text
queued: 3 | running: 0 | completed: 46 | failed: 0
execution_id                         status     attempt worker            duration
fc3e9650-4308-4d30-aea7-8c18c2d4535b queued           1 —                 —
5b746d9e-e021-4a1e-81d4-18389fcfb64e queued           1 —                 —
72e2030c-efdd-41d7-9821-2e23db777849 queued           1 —                 —
```

```text
queued: 1 | running: 2 | completed: 46 | failed: 0
execution_id                         status     attempt worker            duration
fc3e9650-4308-4d30-aea7-8c18c2d4535b queued           1 —                 —
5b746d9e-e021-4a1e-81d4-18389fcfb64e running          1 llm-B:98727       —
72e2030c-efdd-41d7-9821-2e23db777849 running          1 llm-A:98726       —
```

```text
queued: 0 | running: 0 | completed: 49 | failed: 0
execution_id                         status     attempt worker            duration
fc3e9650-4308-4d30-aea7-8c18c2d4535b completed        1 llm-A:98726       11.74s
5b746d9e-e021-4a1e-81d4-18389fcfb64e completed        1 llm-B:98727       19.31s
72e2030c-efdd-41d7-9821-2e23db777849 completed        1 llm-A:98726       13.27s
```

## Degradação explícita e revisão humana

A falha artificial aconteceu antes da rede; nenhum request OpenAI foi enviado nesses dois casos.
`attempt=1` abaixo é a tentativa da task. O retry do provider é registrado em llm.retry e request_attempt
no detalhe persistido; não é redelivery nem retry Celery.

### control-tower events 0d899179-c498-4ead-9a75-7c1c590fb25b --llm

```text
0d899179-c498-4ead-9a75-7c1c590fb25b | eventos: 7 | últimos 12
  4 13:07:26 attempt=1 llm.requested
  5 13:07:26 attempt=1 llm.failed
  6 13:07:26 attempt=1 llm.retry
  7 13:07:27 attempt=1 llm.requested
  8 13:07:27 attempt=1 llm.failed
  9 13:07:27 attempt=1 llm.fallback_activated
 28 13:07:27 attempt=1 llm.degraded
```

### control-tower result 0d899179-c498-4ead-9a75-7c1c590fb25b

```text
Workflow completed | approval pending | actions_executed=false
Caso de referência: INCIDENT-001 | modo: degraded
outcome: degraded_recommendation | reason: simulated_timeout
Ação: Cenário D: Transferir até o piso de Campinas por rota padrão e replanejar; residual via Alpha
Custo: R$ 12500.00 | multa evitada: R$ 16000.00
Atraso: 3 dias | confiança: 0.65
Riscos: 3 | --json para contrato completo
```

### control-tower events 814f0f53-7b51-4e3f-af13-556a404ceaf0 --llm

```text
814f0f53-7b51-4e3f-af13-556a404ceaf0 | eventos: 7 | últimos 12
  4 13:07:28 attempt=1 llm.requested
  5 13:07:28 attempt=1 llm.failed
  6 13:07:28 attempt=1 llm.retry
  7 13:07:29 attempt=1 llm.requested
  8 13:07:29 attempt=1 llm.failed
  9 13:07:29 attempt=1 llm.fallback_activated
 10 13:07:29 attempt=1 llm.escalated
```

### control-tower result 814f0f53-7b51-4e3f-af13-556a404ceaf0

```text
Execution completed | human_review_required | actions_executed=false
Caso de referência: INCIDENT-001 | modo: openai
outcome: human_review_required | reason: simulated_timeout
Revisão humana necessária; nenhuma recomendação automática.
```

## Usage recebido naturalmente

| Execution | input_tokens | output_tokens | Respostas do provider |
|---|---:|---:|---:|
| 72e2030c-efdd-41d7-9821-2e23db777849 | 10097 | 827 | 6 |
| 5b746d9e-e021-4a1e-81d4-18389fcfb64e | 10084 | 796 | 6 |
| fc3e9650-4308-4d30-aea7-8c18c2d4535b | 10010 | 776 | 6 |

São contagens retornadas pelo provider e persistidas em llm.completed. Nenhuma estimativa de custo.
Nos cenários simulados os campos permanecem null, não se inventam medições de tokens.

## Regressão

- 270 testes locais aprovados; 14 de integração aprovados: **284 no total**.
- 22 novos testes locais bloqueiam rede e substituem provider; 4 novos testes de integração cobrem
  resultados/eventos/usage/chave ausente, sem chamadas pagas.
- Task mock completa verificada com socket bloqueado e leitura de chave/provider proibida.
- Smoke Aula 1: 12 checks OK. Os 60 arquivos congelados da Aula 1 continuam preservados.
- Ensaio original distribuído repetido em mock: 20 execuções com A/B, duplicate attempt=1,
  retry de especialista attempt=2, SIGKILL de A e recuperação por B attempt=2.
- OpenAI não foi usado em SIGKILL/retry de especialista/idempotência.
- Workers encerrados; Redis/PostgreSQL saudáveis e encerrados, volumes mantidos.
- Tags existentes preservadas; nenhuma tag Aula 2 criada ou movida. Sem publicação.
