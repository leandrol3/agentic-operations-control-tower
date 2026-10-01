# Guided Demo / Observation Guide — Runtime, Deployment & Production

Alunos não programam durante a aula. Observe decisões, formule hipóteses e compare resultados.
Reprodução posterior: siga a preparação e os comandos completos do
[runbook do professor](../../docs/course/lesson-03-runbook.md). Não é tutorial de implementação.

## Estado final

lesson-03-complete aprovado pelo professor. Demos 1–9 e rehearsal integral concluídos.
Tracing, Agent/Tool/LLM Spans, Collector/Jaeger e métricas reais implementados; sem novas demos.
[Validação final e proveniência do smoke OpenAI](../../docs/course/lesson-03/validation.md).

## Problema e transformação

Aula 2 executa de forma distribuída, mas alguém ainda precisa configurar/iniciar processos e saber
se podem receber tráfego. Um sistema operável precisa de contrato de serviço, empacotamento,
configuração e sinais verificáveis.

Antes: CLI → producer → Redis → Celery → LangGraph → PostgreSQL.
Depois: cliente HTTP → API → **mesmo producer/fila/workers/grafo**, com containers, settings, sondas
e associação trace_id/execution_id. [Diagrama](../../docs/course/lesson-03/contracts.md).

## Decisões que levaram ao runtime

Observe **problema → decisão → hipótese → demo → evidência → conclusão**, sem aprender sintaxe de
framework. As implementações ficam prontas; as perguntas explicam por que elas existem.

### 1. CLI → Service Boundary

Antes: CLI → producer → queue. Como outro sistema consome essa capacidade sem conhecer Celery,
Redis ou LangGraph? Decidimos criar Client → HTTP Contract → mesmo producer interno.
`POST /incidents` expõe uma capacidade; não exige que o consumidor escolha agente, task ou grafo.
**Pergunta:** trocar Redis deveria obrigar o cliente a mudar?
**Mensagem:** o cliente precisa de um contrato estável, não conhecer a implementação.

### 2. Internal State → Public API Contract

Uma investigação demora; aceitação e conclusão são momentos diferentes.
POST /incidents → 202 Accepted → execution_id → GET /executions/{id} → queued/running/completed.
O cliente consulta depois (polling); o POST não espera o workflow. Reenvio da mesma identidade/opções
preserva execução; execution_id e chave de idempotência têm funções diferentes.
IncidentSubmissionRequest e ExecutionAcceptedResponse são públicos; IncidentState permanece interno.
**Pergunta:** por que expor todos os campos do estado do LangGraph a um consumidor?
**Mensagem:** contratos públicos devem mudar mais lentamente que a implementação interna.
**Limites:** 202 ≠ incidente resolvido; completed ≠ business approved; Recommendation ≠ Authorization.
O case suportado continua sendo INCIDENT-001, sem cinco workflows novos ou ações automáticas.

### 3. Agentic Core → Operational Layer Around the Core

api/ recebe/responde HTTP; runtime/ configura processos e papéis; telemetry/ prepara contexto/sinais.
distributed/ mantém producer/fila/workers/store; graph/ coordena; agents/ e tools.py permanecem no core.
API Layer → Runtime Layer → Distributed Execution → LangGraph → Agents/Tools é um mapa de
responsabilidades, não uma exigência de reescrever chamadas internas.
**Pergunta:** para acrescentar outro protocolo de entrada, precisamos duplicar os agentes?
**Mensagem:** lógica de negócio/agentes não deve depender de HTTP.
Só depois dessa decisão discutimos uma imagem com múltiplos papéis: **Same artifact, different runtime roles**.

### 4. Shared IDs → Correlation → Distributed Tracing

Primeiro perguntar como seguir uma execução entre processos. execution_id identifica a execução;
correlation_id relaciona a sessão externa; trace_id permite localizar registros técnicos no start.
API log trace_id=ABC e worker log trace_id=ABC são exemplos abreviados de quadro, não headers válidos.
**Pergunta:** mesmo ID comprova relação pai/filho ou duração de cada chamada? Não.
**Mensagem:** correlation ajuda a encontrar; tracing ajuda a entender causalidade instrumentada.
No start não há árvore de spans. Tempos existentes nos eventos não equivalem a spans.
No complete, Agent Spans representam etapas relevantes e relacionam agentes, tools e LLM calls.
A mudança é observada nas Demos6–9, sem exercício de programação.

## Demonstrações do start preservadas

| Demo / conceito | Comandos observados | Output / pergunta | Aprendizado / fallback |
|---|---|---|---|
| 1 Service Boundary | curl POST /incidents; GET /executions/UUID e /result | 202 queued → running → completed. 202 significa decisão concluída? | API aceita trabalho; aprovação permanece pendente. Captura HTTP |
| 2 Reproducible Runtime | docker compose up -d; ps; logs api/worker-a/worker-b; down | Sete serviços no complete, mesma imagem para três papéis. O que persiste após down? | Containers não são produção completa; volumes conservam estado. Captura ps |
| 3 Alive vs Ready | curl /health; curl /ready; docker compose stop/start redis | health200, ready503 durante queda. Processo vivo pode estar inapto? | Sondas têm responsabilidades distintas. Matriz gravada |
| 4 Correlation Before Tracing | GET execution; filtrar logs por trace_id | Mesmo ID na API, store e worker. O que falta para entender causalidade? | IDs localizam; complete habilitado nas Demos6–9. Pares de logs gravados |
| 5 Observable Failure | Perfil failure + POST com llm_failure=timeout; GET result; logs | Falha + identidade + degraded_recommendation. Consigo relacionar falha e desfecho? | Falha observável; não repetir teoria de retry/fallback da Aula 2. Captura do timeout artificial |

Os comandos com UUID acima descrevem o que observar; blocos copiáveis com extração automática de IDs
estão no runbook. Os requests são envelopes do caso técnico INCIDENT-001, não novos workflows empresariais.
Sem compra/transferência/transporte automáticos. Demo failure não chama OpenAI: timeout ocorre antes da rede.

A ordem é Demos1–4 → captura da Demo5 → teoria Trace/Span → Demos6–9.
A falha é executada ao vivo somente na Demo9 para preservar a agenda de240min.

## Mensagens que devem ficar

- Produção começa quando podemos implantar, observar, reiniciar e operar com previsibilidade.
- O cliente consome uma capacidade por um contrato público estável.
- Aceitar trabalho não é concluir trabalho; recomendação não é autorização.
- A camada operacional envolve o core multiagente preservado.
- Correlation nos ajuda a encontrar. Tracing nos ajuda a entender causalidade.
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

Start tem correlação; complete tem spans reais, Collector/Jaeger e métricas exportadas ao debug exporter.
Logs stdout desaparecem ao remover containers; contexto/eventos no Postgres persistem. Há janelas entre
claim e publicação; reenvio idempotente é a recuperação didática. Não há HA, autenticação/TLS ou cloud deploy.
Consulte [evidências e limitações](../../docs/course/lesson-03/validation.md) para distinguir implementação,
ensaio real e limitações deliberadas.


## Correlation → Tracing → Agent Spans

Correlation → Trace → Span → Distributed Trace → Workflow Span → Agent Span → Tool / LLM Span.
Trace é a história distribuída observada. Span tem início/fim/duração/atributos/status/relações.
Agent Span representa uma etapa relevante da execução agêntica.

| Demo | Problema / hipótese | Comando (raiz; setup no runbook) | Evidência / discussão |
|---|---|---|---|
| 6 First Distributed Trace | Mesmo ID não mostra causa; W3C atravessa fila | uv run --extra lesson03 python scripts/trace_lesson03.py normal | URL direta; HTTP/publish/process/workflow; qual fronteira é assíncrona? |
| 7 Agent Spans | Worker oculta o trabalho interno | Reabrir URL da Demo6; nenhuma nova carga | Agentes irmãos, join posterior, Finance determinístico, Supply→tool/mock boundary |
| 8 Find the Bottleneck | Onde está o tempo? | DEMO_AGENT_DELAY_MS=1500 + recriar runtime; helper bottleneck | Logistics marcado com delay didático; join aguarda ramo mais lento |
| 9 Observable Failure as Trace | Onde falhou e como continuou? | Perfil failure + helper failure | Duas chamadas ERROR, retry, fallback/degraded, segunda invocação do mesmo grafo |

**Antes:** logs com identidade comum. **Depois:** spans com pais, duração, status e eventos.
Mock não executa LLM; seu span de completion é marcador explícito de substituto determinístico,
sem tokens e sem inferência. As tools e cálculos permanecem reais/determinísticos.
OpenAI opcional registra usage somente quando retornado, sem prompts/respostas completos.

**Perguntas:** árvore de spans é o LangGraph? A soma dos ramos paralelos é duração total?
Consumer pode iniciar após fim do HTTP? Completed pode conter uma recomendação degradada?
Se Jaeger cair, por que /ready continua200 quando banco/broker estão bons?

**Aprendizados:** workflow modela comportamento; trace registra uma execução observada.
ExecutionEvent é histórico durável; telemetria pode se perder. Observabilidade não deve vazar contexto.
OpenTelemetry é contrato; backend é substituível. Fallbacks: árvores/JSON/capturas reais salvas pelo professor.
Os cinco recortes de instrumentação somam no máximo10–12min, sem live coding.
