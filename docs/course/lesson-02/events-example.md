# Execution Events — exemplo real em memória

Execução: `b0e3167d-78a6-4fcb-bf0b-7b258be3ee7b` · envelope `NC-S42-0001`.

| Seq | Etapa | Evento | Status externo | Duração (ms) |
|---:|---|---|---|---:|
| 1 | intake | execution_queued | queued | null |
| 2 | worker | execution_started | running | null |
| 3 | supervisor | step_started | running | null |
| 4 | supervisor | step_completed | running | 0.03 |
| 5 | logistics | step_started | running | null |
| 6 | logistics | step_completed | running | 0.06 |
| 7 | production | step_started | running | null |
| 8 | production | step_completed | running | 0.11 |
| 9 | supply | step_started | running | null |
| 10 | supply | step_completed | running | 0.04 |
| 11 | consolidation | step_started | running | null |
| 12 | consolidation | step_completed | running | 0.02 |
| 13 | finance | step_started | running | null |
| 14 | finance | step_completed | running | 0.22 |
| 15 | challenger | step_started | running | null |
| 16 | challenger | step_completed | running | 0.07 |
| 17 | recommendation | step_started | running | null |
| 18 | recommendation | step_completed | running | 0.04 |
| 19 | human_approval | step_started | running | null |
| 20 | human_approval | step_completed | running | 0.01 |
| 21 | worker | execution_completed | completed | 516.53 |

Timestamps completos estão no snapshot do ensaio. Esta é a ordem observada de uma execução;
os três especialistas podem intercalar eventos em outra ordem. Nenhum evento foi enviado a Redis/PostgreSQL.
Campos de tokens, custo estimado, qualidade e business_outcome permanecem null.
