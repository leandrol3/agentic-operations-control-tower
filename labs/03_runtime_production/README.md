# Guided Demo / Observation Guide — Runtime, Deployment & Production

Alunos não programam durante a aula. Observe decisões, formule hipóteses e compare resultados.
Reprodução posterior: siga a preparação e os comandos completos do
[runbook do professor](../../docs/course/lesson-03-runbook.md). Não é tutorial de implementação.

## Problema e transformação

Aula 2 executa de forma distribuída, mas alguém ainda precisa configurar/iniciar processos e saber
se podem receber tráfego. Um sistema operável precisa de contrato de serviço, empacotamento,
configuração e sinais verificáveis.

Antes: CLI → producer → Redis → Celery → LangGraph → PostgreSQL.
Depois: cliente HTTP → API → **mesmo producer/fila/workers/grafo**, com containers, settings, sondas
e associação trace_id/execution_id. [Diagrama](../../docs/course/lesson-03/contracts.md).

## Cinco demonstrações

| Demo / conceito | Comandos observados | Output / pergunta | Aprendizado / fallback |
|---|---|---|---|
| 1 Service Boundary | curl POST /incidents; GET /executions/UUID e /result | 202 queued → running → completed. 202 significa decisão concluída? | API aceita trabalho; aprovação permanece pendente. Captura HTTP |
| 2 Reproducible Runtime | docker compose up -d; ps; logs api/worker-a/worker-b; down | Cinco serviços, mesma imagem para três papéis. O que persiste após down? | Containers não são produção completa; volumes conservam estado. Captura ps |
| 3 Alive vs Ready | curl /health; curl /ready; docker compose stop/start redis | health200, ready503 durante queda. Processo vivo pode estar inapto? | Sondas têm responsabilidades distintas. Matriz gravada |
| 4 Correlation | GET execution; filtrar logs por trace_id | Mesmo ID na API, store e worker. Isso já é causalidade por spans? | Identidade atravessa processos; spans ficam para complete. Pares de logs gravados |
| 5 Observable Failure | Perfil failure + POST com llm_failure=timeout; GET result; logs | retry → fallback → degraded_recommendation. Por que marcar degradação? | Falha e continuidade explícitas. Captura do timeout artificial |

Os comandos com UUID acima descrevem o que observar; blocos copiáveis com extração automática de IDs
estão no runbook. Os requests são envelopes do caso técnico INCIDENT-001, não novos workflows empresariais.
Sem compra/transferência/transporte automáticos. Demo failure não chama OpenAI: timeout ocorre antes da rede.

## Mensagens que devem ficar

- Produção começa quando podemos implantar, observar, reiniciar e operar com previsibilidade.
- Container não é deploy; é uma unidade reproduzível de execução.
- Código permanece o mesmo. Configuração muda por ambiente.
- Alive não significa Ready. Ready não significa saudável end-to-end.
- Logs mostram eventos; traces mostram causalidade; métricas mostram comportamento no tempo.
- LangGraph coordena agentes. OpenTelemetry observa o caminho.
- ExecutionEvent é histórico durável; telemetria não o substitui.
- OpenTelemetry é o contrato de instrumentação. Langfuse é um possível destino especializado.

## Compare pelo Git depois da aula

A partir desta branch candidata, sem criar tags:

```bash
git diff d3a67ad -- src/control_tower/distributed src/control_tower/agents src/control_tower/graph
git status --short
```

O primeiro comando deve permanecer vazio: a camada operacional é aditiva. Enquanto a revisão não
estiver commitada, arquivos novos aparecem no status e não no diff. Não usar uma tag Aula 3 inexistente.

## Limites honestos

Start tem correlação e SDK preparado, não tracing end-to-end, dashboard ou métricas coletadas.
Logs stdout desaparecem ao remover containers; contexto/eventos no Postgres persistem. Há janelas entre
claim e publicação; reenvio idempotente é a recuperação didática. Não há HA, autenticação/TLS ou cloud deploy.
Consulte [evidências e limitações](../../docs/course/lesson-03/validation.md) para distinguir implementação,
ensaio real e itens que ainda ficam para o complete.
