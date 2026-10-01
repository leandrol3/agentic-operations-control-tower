# Aula 3 — Runtime, Deployment & Production

## Do sistema distribuído ao runtime operável em produção

**Full pedagogical rehearsal completed by professor.** Registro em 30/09/2026: todas as demos
executadas com sucesso, progressão aprovada e aula considerada ministrável em 4h. Tempos reais
por bloco não informados; a agenda abaixo é estimada. Smoke OpenAI também aprovado pelo professor;
[proveniência e campos não informados](lesson-03/validation.md).
Setup/build/pull ficam fora das 4h; ambiente preparado e capturas disponíveis antes de começar.
Preservar discussão de contratos, Correlation → Trace → Span e destaque visual dos Agent Spans.
Evitar explicação prolongada de Compose. Identificar o gargalo artificial, não reensinar fallback
na Demo 9 e reservar a síntese final para o gancho da Aula 4.


**lesson-03-complete — aprovado pelo professor.** Start aprovado preservado; complete acrescenta tracing.
O professor demonstra; alunos observam arquitetura e trade-offs, sem programação durante a aula.
Comandos abaixo são para zsh/bash, na raiz do repositório. Setup/build/testes ficam antes das 4 horas.

> Produção não começa quando o código funciona. Produção começa quando o sistema pode ser
> implantado, observado, reiniciado e operado com previsibilidade.

O start entrega API, containers, settings, sondas e identidade entre processos. O complete acrescenta
spans end-to-end, métricas reais e Collector + Jaeger, sem mudar o core. Não apresentar este laboratório como deployment de produção real.
[Arquitetura, contratos e limites](lesson-03/contracts.md) · [Evidências reais](lesson-03/validation.md).

## 0. Preparação do professor — fora da aula

### 0.1 Localizar o checkout e conferir o estado

```bash
cd '/Users/leandrolopes/Documents/ChatGPT/Disciplina Mult-Agents/agentic-operations-control-tower'
git branch --show-current
git status --short
git tag --list
```

Esperado nesta revisão: branch `codex/lesson-03-complete`. Ela ainda não foi publicada; não usar
`git checkout lesson-03-start` como se existisse tag. Em outra máquina, usar o checkout que receber
esta revisão após aprovação. Não descartar alterações locais para trocar de branch.

### 0.2 Pré-requisitos e perfil

Docker Desktop aberto; Git, uv, curl e Python disponíveis. Primeiro download precisa de rede;
prepare imagens/dependências antes de entrar na sala. Não iniciar workers locais da Aula 2 em paralelo
com os containers. `compose.yaml` histórico está intacto; override automático acrescenta os três papéis, Collector e Jaeger.

```bash
docker version
docker compose version
uv sync --locked --extra lesson03
export LLM_MODE=mock
export OTEL_ENABLED=false
export LOG_FORMAT=human
```

Não substituir `--extra lesson03` por `--extra lesson02` ao testar API. Não sobrescrever .env existente.
O mock dispensa chave. O build não lê nem copia .keys/.env do host. API e workers compartilham imagem.

### 0.3 Preparar sessão, pasta e URL — colar todo o bloco

```bash
export AULA3_RUN="aula3-$(date +%Y%m%d-%H%M%S)"
export AULA3_DIR="$PWD/artifacts/$AULA3_RUN"
export AULA3_URL="http://127.0.0.1:8000"
mkdir -p "$AULA3_DIR"
printf 'export AULA3_RUN=%q\nexport AULA3_DIR=%q\nexport AULA3_URL=%q\n' \
  "$AULA3_RUN" "$AULA3_DIR" "$AULA3_URL" > artifacts/aula3-session.env
```

API_PORT customizada exige ajustar AULA3_URL. Uma sessão nova evita colisões entre versões de ensaios.
Para recuperar terminal fechado: volte à raiz e execute `source artifacts/aula3-session.env`.

### 0.4 Instalar, construir e subir

```bash
uv run --extra lesson03 pytest -q
LLM_MODE=mock uv run --extra lesson03 control-tower smoke
LLM_MODE=mock uv run --extra lesson03 control-tower batch \
  --incidents 10 --workers 2 --provider-limit 2 --demo-delay-ms 50
docker compose config --quiet
docker compose build
docker compose up -d --wait
docker compose ps
curl --fail --silent --show-error "$AULA3_URL/health"
curl --fail --silent --show-error "$AULA3_URL/ready"
```

Esperado: api, worker-a, worker-b, redis e postgres healthy; Collector e Jaeger running.
A verificação ponta a ponta do backend será feita pela Demo 6; running sozinho não comprova ingestão. API inicializa schema aditivo no startup;
não precisa db-init manual. Build/primeiro pull não contam como tempo da demo. Não projetar `compose
config` sem --quiet quando usar segredo real: ele pode expandir variáveis privadas.

Para a regressão com banco real, antes da aula:

```bash
LESSON02_INTEGRATION=1 LESSON03_INTEGRATION=1 LLM_MODE=mock \
  uv run --extra lesson03 pytest -q
```

Integração usa schemas temporários isolados e remove só esses schemas. Nenhuma chamada OpenAI paga.
Redis/Postgres mantêm portas localhost históricas para CLI/testes; containers usam rede interna.
Volumes anteriores são preservados. Se API não subir, não apagar volumes: confira senha/portas do
ambiente existente. Consulta de logs, sem mostrar .env:

```bash
docker compose logs --tail 30 api
docker compose logs --tail 30 worker-a
docker compose logs --tail 30 worker-b
```

### 0.5 Materiais já abertos

- Este roteiro; [arquitetura](lesson-03/contracts.md); [guia de observação](../../labs/03_runtime_production/README.md).
- Capturas da [validação](lesson-03/validation.md), para fallback claramente identificado.
- Recortes selecionados da seção 9; na discussão dos contratos, somente os dois recortes da Ponte 2. Nada de escrever YAML/DDL/boilerplate em sala.
- Terminal em fonte grande. Não imprimir todos os eventos/JSON interno por padrão.
- Execute primeiro todo o ensaio fora da aula. O script auxiliar pode automatizar três verificações:

```bash
uv run --extra lesson03 python scripts/validate_lesson03_start.py mock
uv run --extra lesson03 python scripts/validate_lesson03_start.py health
```

O primeiro para/inicia os dois workers; o segundo para/inicia Redis. Use somente no laboratório sem
outra carga ativa. São ensaios, não comandos de observabilidade de produção. Failure exige perfil da Demo 5.

## 1. Agenda — 240 minutos

| Horário | Bloco | Minutos |
|---|---|---:|
| 00:00–00:20 | Distributed ≠ Production | 20 |
| 00:20–00:45 | Pontes 1/2: Service Boundary + API Contract | 25 |
| 00:45–01:00 | Demo 1 — API | 15 |
| 01:00–01:20 | Ponte 3 + Runtime Roles | 20 |
| 01:20–01:35 | Demo 2 — Compose | 15 |
| 01:35–01:50 | Configuração | 15 |
| 01:50–02:05 | Intervalo | 15 |
| 02:05–02:25 | Health / Readiness | 20 |
| 02:25–02:40 | Demo 3 — Health | 15 |
| 02:40–02:55 | Demo 4 — Correlation Before Tracing; Demo 5 em captura | 15 |
| 02:55–03:10 | Correlation → Trace → Span → Distributed Trace | 15 |
| 03:10–03:25 | Demo 6 — First Distributed Trace | 15 |
| 03:25–03:40 | Demo 7 — Agent Spans | 15 |
| 03:40–03:50 | Demo 8 — Find the Bottleneck | 10 |
| 03:50–03:57 | Demo 9 — Observable Failure as a Trace | 7 |
| 03:57–04:00 | Síntese / gancho Aula 4 | 3 |

Total **240 minutos**. Teoria protegida: retomada20 + pontes25 + camada/papéis20 +
configuração15 = **80 minutos**, além de sondas e teoria de tracing. Setup fora da aula.
A Demo 5 mantém os comandos como reprodução/ensaio; nesta agenda usar sua captura em até2min
no bloco de correlação. A mesma falha será executada ao vivo na Demo 9; não repetir recriações.
Demos 1–3 foram compactadas na exposição, sem remover comandos. Se houver atraso, reduzir navegação
em código e usar capturas; não sacrificar conceitos. Tempos de aula são estimativas, não turma medida.

### Narrativa em 13 passos

1. Distributed ≠ Production: retomar o que a Aula 2 resolveu e o que falta operar.
2. Perguntar como outro sistema acessa o runtime sem conhecer suas ferramentas internas.
3. Introduzir Service Boundary como contrato estável de acesso à capacidade.
4. Desenhar aceitação assíncrona: POST, 202, execution_id e consulta posterior.
5. Separar contrato público de estado interno; comprovar na Demo 1.
6. Localizar a camada operacional ao redor do core multiagente preservado.
7. Distinguir artefato e processo: uma imagem, diferentes papéis; comprovar na Demo 2.
8. Mostrar como configuração muda o ambiente sem reescrever o software.
9. Separar processo vivo, prontidão e saúde end-to-end; comprovar na Demo 3.
10. Seguir execution_id/trace_id/correlation_id entre processos na Demo 4.
11. Usar a captura da Demo 5 para localizar falha/desfecho; executar a falha na Demo 9.
12. Reconhecer o limite: correlação relaciona registros; tracing explicita causalidade instrumentada.
13. Abrir o trace real e explorar Agent/Tool/LLM Spans, gargalo e falha nas Demos 6–9.

Regra de condução: **problema → decisão arquitetural → implementação → demo**.
A tecnologia aparece depois que a turma entende a necessidade que ela atende.

## 2. Blocos conceituais — fala, pergunta, output e fallback

### 00:00–00:20 — retomada

**Objetivo:** distinguir execução distribuída de operação previsível. **Conceito:** o algoritmo pode
funcionar sem o sistema ser instalável/operável. **Fala:** “Na Aula 2 resolvemos quem recebe trabalho,
quem executa e onde guardar o histórico. Agora: como outra pessoa instala e opera esse conjunto?”
**Comando:** nenhum. **Output:** desenho CLI → Redis → workers → mesmo grafo → PostgreSQL.
**Pergunta:** “Se o processo responde, vocês entregariam tráfego a ele?”
**Fallback:** cinco caixas no quadro. Não reexecutar benchmark da Aula 2.

### 00:20–00:30 — Ponte 1: From CLI to Service Boundary

**Problema:** na Aula 2 o professor conhece a CLI e a infraestrutura. Um frontend, ERP ou outro
serviço precisa consumir a capacidade sem aprender os detalhes desse runtime.
**Pergunta de abertura:** “Como outro sistema, frontend ou aplicação corporativa utiliza esse runtime
sem conhecer Celery, Redis ou LangGraph?”

```text
Antes: CLI → producer interno → queue
Depois: Client → Service Boundary → mesmo producer interno → queue

Client → HTTP Contract → Application Runtime → Queue / Workers / LangGraph
```

**Decisão:** criar uma fronteira estável, com entrada e resposta explícitas. HTTP é o protocolo dessa
fronteira; FastAPI materializa a decisão. Não justificar a API apenas pela conveniência do framework.
**Fala:** “O cliente não deve conhecer a implementação interna do sistema. Ele precisa de um contrato estável.”

A rota `POST /incidents` expressa a capacidade de submeter um incidente para análise. Rotas como
`POST /run-agent`, `POST /execute-langgraph` ou `POST /celery-task` acoplariam o consumidor a mecanismos
internos. São contraexemplos conceituais, **não endpoints existentes**.
O laboratório continua limitado ao replay técnico de INCIDENT-001, não a qualquer caso empresarial.

**Mensagem:** “A API expõe uma capacidade do sistema, não sua implementação interna.”
**Perguntas:** o consumidor precisa saber que usamos Celery? Que existe LangGraph? Se trocarmos Redis
ou o orchestrator, o contrato HTTP deveria mudar? Espere respostas antes de mostrar arquivos.
**Implementação a localizar:** api/app.py recebe HTTP e delega ao producer já existente.
**Comando:** nenhum. **Evidência futura:** Demo 1 submete sem expor task/fila/grafo ao cliente.
**Fallback:** desenhar as duas linhas no quadro; não abrir documentação de FastAPI.

### 00:30–00:45 — Ponte 2: Designing the API Contract

Reservar 8 minutos para aceitação assíncrona e 7 para contrato público versus modelo interno.
**Problema:** tempo de fila, execução e provider variam. Manter o cliente esperando prende a conversa
HTTP ao tempo do workflow e torna timeout/desconexão ambíguos: o processamento pode continuar.
**Decisão:** separar submissão de acompanhamento, sem alterar o core.

```text
POST /incidents → 202 Accepted → execution_id → GET /executions/{id}
                                                   ↓
                                     queued → running → completed
```

| Decisão | Por quê | O que a Demo 1 comprova |
|---|---|---|
| POST /incidents | Solicitar processamento de uma capacidade do sistema | Request pequeno, sem escolher agente/task |
| 202 Accepted | Publicação aceita para processamento assíncrono | Retorna enquanto consumidores estão parados |
| execution_id | Endereço estável para acompanhar a execução e seu histórico | Mesmo UUID no status, eventos e resultado |
| GET posterior / polling | Cliente decide quando consultar; não mantém o POST aberto | Loop consulta sem reexecutar o grafo |
| Não aguardar workflow | Tempo da conversa HTTP fica separado da fila/investigação | Resposta precede running/completed |
| Identidade idempotente | Resposta perdida não deve criar outra operação lógica | Mesmo request/version reutiliza execução |

**Precisão:** o POST espera claim/publicação; não é um retorno sem trabalho algum. Não garante que a
investigação terá sucesso. Se a publicação não for confirmada, pode retornar 503 com claim já persistido.
execution_id identifica a execução; a identidade idempotente deriva de incident_id + operação + version.
Não usar trace_id como chave de idempotência. Mesma identidade exige mesmas opções; outra experiência
usa nova version. Uma duplicata pode retornar 202 com status já completed e created=false.

**Fala:** “Aceitar trabalho não é o mesmo que concluir trabalho.”
**Escrever no quadro:** `202 Accepted ≠ incidente resolvido`; `completed ≠ business approved`;
`Recommendation ≠ Authorization`. Completed também pode indicar encaminhamento humano concluído,
sem recomendação automática. Nenhuma compra, transporte ou transferência é autorizada por esses status.

#### Public Contract ≠ Internal Model

```text
CLIENT → API Contract → Application / Runtime → Domain Models → LangGraph
```

**Pergunta antes do código:** “Por que não devolver diretamente o IncidentState da Aula 1?”
O estado interno contém detalhes de coordenação, evidências e evolução do grafo. Exportá-lo inteiro
obriga consumidores a acompanhar mudanças internas e expõe campos que não precisam conhecer.
IncidentSubmissionRequest e ExecutionAcceptedResponse são contratos públicos; IncidentState e os
modelos de domínio/runtime têm outra responsabilidade. A camada HTTP traduz e projeta, não duplica
regras de negócio. **Contratos públicos devem mudar mais lentamente que a implementação interna.**

Mostrar **somente estes dois recortes** de [api/models.py](../../src/control_tower/api/models.py),
sem explicar sintaxe de Pydantic. O primeiro é um recorte inicial: campos didáticos/método foram omitidos
somente na projeção, sem alterar o contrato implementado.

```python
class IncidentSubmissionRequest(APIModel):
    incident_id: Identifier
    version: Identifier = 'v1'
    # Este serviço expõe somente o workload de referência que já existe na Aula 2.
    reference_case_id: Literal['INCIDENT-001'] = 'INCIDENT-001'
```

```python
class ExecutionAcceptedResponse(APIModel):
    execution_id: UUID
    status: Status
    created: bool
    trace_id: str
    correlation_id: str
```

Aponte a identidade de negócio/version na entrada e o endereço de acompanhamento na saída.
Não abrir IncidentState integral nem os validadores. Os IDs de telemetria serão retomados no bloco final.
**Pergunta:** “Se acrescentarmos um campo interno de investigação, o cliente precisa mudar?”
**Comando:** nenhum; a Demo 1 comprova o desenho. **Fallback:** sequência e dois contratos impressos.
**Checagem antes da demo:** peça à turma que explique 202, execution_id, consulta posterior e por que
não retornar todo o estado. Corrija a interpretação antes de executar o primeiro curl.

### 01:00–01:10 — Ponte 3: Operational Layer Around the Agentic Core

**Problema:** adicionar HTTP não deveria exigir outra implementação dos agentes ou do grafo.
**Decisão:** envolver o core com responsabilidades operacionais, preservando a execução já aprovada.

```text
API Layer → Runtime Layer → Distributed Execution → LangGraph → Agents / Tools
                contexto e sinais acompanham as fronteiras
```

O desenho representa responsabilidades, não uma cadeia de chamadas rígida: a rota usa o producer
original, e o bootstrap prepara o processo antes de receber trabalho.

| Estrutura real em src/control_tower/ | Responsabilidade |
|---|---|
| api/ | Recebe/valida contratos HTTP e projeta respostas |
| runtime/ | Settings, bootstrap, papéis operacionais e associação de contexto |
| telemetry/ | Contexto, logs e spans/exporters do complete; desabilitados no primeiro bloco |
| distributed/ | Producer, fila/tasks/workers e persistência existentes |
| graph/ | LangGraph continua coordenando a execução |
| agents/ e tools.py | Mesmas responsabilidades e capabilities; não conhecem FastAPI |

Neste repositório as tools estão em **tools.py**, não em uma nova pasta tools/.
**Fala:** “A Aula 3 adicionou uma camada operacional ao redor do sistema. Não reescreveu o sistema multiagente.”
“Business logic e agent logic não devem depender do protocolo de entrada.”
**Perguntas:** precisamos duplicar agentes para adicionar API? O LangGraph deve saber se a origem é
HTTP ou CLI? Um futuro consumer Kafka exigiria alterar agentes? Kafka é apenas hipótese, não implementação.
**Comando:** nenhum; mostrar árvore de responsabilidades, sem percorrer todos os módulos.
**Fallback:** quadro com core no centro e camadas operacionais em volta.

### 01:10–01:20 — do artefato aos papéis de runtime

**Problema:** o mesmo software precisa atender clientes e consumir trabalho em processos independentes.
**Decisão:** uma imagem, comandos diferentes para cada papel; API e worker têm ciclos de vida próprios.
**Conceito:** imagem é artefato, container é processo. Um processo worker não é um agente do LangGraph.
**Fala:** “Same artifact, different runtime roles.”
**Implementação:** Dockerfile comum; command api/worker no override, preparados previamente.
**Comando:** nenhum obrigatório; mostrar só CMD e command, sem leitura linha a linha do YAML.
**Output previsto:** uma imagem → API, worker-a, worker-b; volumes pertencem à infraestrutura.
**Pergunta:** “Precisamos duplicar o repositório para adicionar um worker?”
**Fallback:** diagrama artefato/papéis. “Container não é deploy. Container é uma unidade reproduzível de execução.”

### 01:35–01:50 — configuração

**Objetivo:** distinguir código, configuração e segredo. **Conceito:** ambiente vence .env; config consistente
entre produtores/consumidores. **Fala:** “Código permanece o mesmo. Configuração muda por ambiente.”
**Comando seguro**, em vez de imprimir todo o ambiente:

```bash
docker compose exec -T api python -c 'from control_tower.runtime.settings import RuntimeSettings; s=RuntimeSettings(); print("env=",s.app_env,"mode=",s.llm_mode,"log=",s.log_format,"otel=",s.otel_enabled)'
```

**Output:** local, mock, human, False (ou json se selecionado). Não exibir DSN/chave.
**Pergunta:** “Editar uma variável no meu terminal altera um worker já em execução?”
**Fallback:** tabela de settings em contracts.md. Mudanças exigem recriação/reinício do processo.

### 02:05–02:25 — sondas

**Objetivo:** separar perguntas operacionais. **Conceito:** liveness do processo, readiness de dependências,
saúde do provider e sucesso end-to-end são verificações diferentes.
**Fala:** “Alive não significa Ready. Ready não significa saudável end-to-end.”
**Comando:** nenhum antes da Demo 3. **Output:** matriz vivo/pronto/resultado.
**Pergunta:** “Derrubar Redis deveria fazer o processo HTTP fingir que morreu?”
**Fallback:** prever a matriz health200/ready503 no quadro e depois conferir captura.

### 02:40–02:45 — antes dos sinais: como sigo a execução?

**Problema de abertura:** “Como localizo uma mesma execução atravessando processos diferentes?”
Não começar por um catálogo de logs, métricas e traces. Primeiro, nomear as identidades:

| Identidade | Pergunta que ajuda a responder |
|---|---|
| execution_id | Qual execução durável estou acompanhando? |
| correlation_id | Qual identificador externo/da sessão relaciona esses registros? |
| trace_id | Qual identidade técnica compartilhada permite localizar registros entre processos? |

No start, trace_id é identidade de correlação; o nome do campo não comprova existência de trace.
Idempotência conserva o contexto canônico da primeira associação. worker_id pode mudar entre entregas.

```text
API log:    trace_id=ABC  execution_id=123
Worker log: trace_id=ABC  execution_id=123
```

ABC/123 são abreviações de quadro; a API real valida trace_id hexadecimal de 32 caracteres e UUID.
**Decisão:** persistir a associação e levá-la nos headers da task; restaurá-la no contexto do worker.
**Implementação:** runtime/store.py, runtime/signals.py e telemetry/context.py já preparados.
**Pergunta:** “Ter o mesmo ID em dois logs prova que uma chamada causou a outra?” **Resposta: não.**
**Demo seguinte:** primeiro comprovar que conseguimos encontrar a execução; depois discutir o que falta.
**Comando:** somente os da Demo 4. **Fallback:** dois registros gravados com o mesmo ID.

### 02:55–03:10 — Correlation → Tracing → Agent Spans

**Problema:** o mesmo ID localiza registros, mas não descreve causalidade e tempo por operação.
**Decisão:** modelar operações semanticamente relevantes como spans e propagar seu contexto.
**Trace:** história distribuída de uma operação observada.
**Span:** operação com início, fim, duração, atributos, status e relação com outras operações.
**Agent Span:** representação observável de uma etapa relevante da execução agêntica.

```text
Correlation → Trace → Span → Distributed Trace → Workflow Span → Agent Span → Tool / LLM Span
```

Fala: “Correlation nos ajuda a encontrar. Tracing nos ajuda a entender causalidade.”
Spans HTTP, publish e process têm identidades diferentes e relações causais. Nesta aplicação,
consumo de **uma mensagem** continua como filho do publish, mesmo se HTTP já terminou. Uma nova
entrega recebe outro span. Não confundir árvore hierárquica com ordenação sequencial.
Os três especialistas são irmãos concorrentes; join aparece depois dos três, não como pai deles.

**Trace não é o LangGraph.** Workflow modela o comportamento. Trace registra uma execução observada:
infraestrutura, waits, chamadas externas e tentativas podem aparecer além dos nós lógicos.
“Observabilidade também exige modelagem. Nem toda função merece virar um span.”

ExecutionEvent é histórico durável; OTel é telemetria técnica, sujeita a perdas/exportação assíncrona.
**Domain history != observability telemetry.** Não usar Jaeger como store de resultado.
**OpenTelemetry é o contrato. O backend é substituível.** Aplicação → OTLP → Collector → Jaeger.
Langfuse é possível destino especializado, não dependência desta aula.

Pergunta: “Qual evidência me diria se o tempo foi gasto na fila, em coordenação ou no provider?”
Antecipe que mock não é inferência: seus spans LLM são marcadores da fronteira determinística,
sem tokens. O atraso didático da Demo 8 é rotulado, não latência real de provider.
Fallback: árvore impressa das [capturas reais](lesson-03/complete-demo-outputs.md).

## 3. DEMO 1 — Service Boundary / API — 15 min

**Problema →** outro sistema precisa submeter e acompanhar uma investigação de duração variável.
**Decisão →** boundary estável e contrato assíncrono público, separado dos modelos internos.
**Hipótese →** podemos aceitar o trabalho sem consumidor ativo e acompanhá-lo pelo mesmo UUID.
**Demo →** comandos 3.1–3.3, após as Pontes 1/2; implementação em api/ + producer original.
**Evidência →** 202/queued antes de ligar workers; GET acompanha até resultado; duplicata conserva identidade.
**Conclusão →** aceitar trabalho não é concluí-lo; Recommendation ≠ Authorization.

**Objetivo:** comprovar 202 rápido e acompanhamento independente. **Conceito:** trabalho assíncrono.
**Antes:** runtime saudável, perfil mock; sem pendências. **Arquivos:** api/app.py, api/models.py,
distributed/producer.py (inalterado). **Condução:** 3 min hipótese, 6 min comandos, 6 min discussão.

### 3.1 Parar apenas consumidores para tornar queued visível

```bash
docker compose stop worker-a worker-b
export D1_VERSION="$AULA3_RUN-api"
export D1_TRACE="$(uv run --extra lesson03 python -c 'from uuid import uuid4; print(uuid4().hex)')"
cat > "$AULA3_DIR/demo1-request.json" <<JSON
{"incident_id":"HTTP-DEMO-001","version":"$D1_VERSION","demo_delay_ms":5000}
JSON
curl --fail-with-body --silent --show-error \
  -D "$AULA3_DIR/demo1-headers.txt" \
  -o "$AULA3_DIR/demo1-accepted.json" \
  -X POST "$AULA3_URL/incidents" \
  -H 'Content-Type: application/json' \
  -H "X-Trace-ID: $D1_TRACE" \
  -H "X-Correlation-ID: $D1_VERSION" \
  --data-binary @"$AULA3_DIR/demo1-request.json"
cat "$AULA3_DIR/demo1-headers.txt"
cat "$AULA3_DIR/demo1-accepted.json"
export D1_ID="$(uv run --extra lesson03 python -c 'import json,sys; print(json.load(open(sys.argv[1]))["execution_id"])' "$AULA3_DIR/demo1-accepted.json")"
curl --fail --silent --show-error "$AULA3_URL/executions/$D1_ID"
```

**Output esperado:** HTTP202, created=true, queued, execution_id, trace/correlation e Location.
GET mostra queued, worker/duration null. Delay de 5 s é didático, não latência real do grafo/LLM.
Se curl falhar, não continuar com UUID vazio. 409: não apagar banco, crie versão `-r2` para nova operação.

### 3.2 Iniciar consumidores e consultar até terminal

```bash
docker compose start worker-a worker-b
for AULA3_TRY in {1..30}; do
  curl --fail --silent --show-error "$AULA3_URL/executions/$D1_ID" \
    -o "$AULA3_DIR/demo1-state.json" || break
  uv run --extra lesson03 python -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["status"],"worker=",d["worker_id"],"duration_ms=",d["duration_ms"])' "$AULA3_DIR/demo1-state.json"
  D1_STATUS="$(uv run --extra lesson03 python -c 'import json,sys; print(json.load(open(sys.argv[1]))["status"])' "$AULA3_DIR/demo1-state.json")"
  if [ "$D1_STATUS" = completed ] || [ "$D1_STATUS" = failed ]; then break; fi
  sleep 1
done
curl --fail --silent --show-error "$AULA3_URL/executions/$D1_ID/result"
curl --fail --silent --show-error "$AULA3_URL/executions/$D1_ID/events?limit=3"
docker compose logs --no-color api worker-a worker-b > "$AULA3_DIR/demo1-logs.txt"
```

**Output:** queued → running → completed, worker-a ou b; duration_ms inclui 5 s artificiais, sem fila.
Resultado recommendation/mock, custo BRL12500.00, approval pending, actions_executed=false.
Events mostra início do histórico. `after=3&limit=3` consulta próximos; não imprimir 100 eventos na projeção.
**Fala-chave:** “O sistema agora possui uma fronteira de serviço.”
**Pergunta:** “O 202 significa incidente resolvido ou pedido de processamento aceito?”
**Fallback:** máximo 2 min de diagnóstico, usar mock-http gravado. Não depurar FastAPI ao vivo.

### 3.3 Repetir identidade, sem nova operação (opcional, 1 min)

```bash
curl --fail-with-body --silent --show-error -X POST "$AULA3_URL/incidents" \
  -H 'Content-Type: application/json' --data-binary @"$AULA3_DIR/demo1-request.json"
```

Mesmo UUID, created=false, correlação original. O status pode já ser completed. Isso republica a entrega;
o store impede nova execução efetiva. Não alterar delay/version para alegar que foi a mesma operação.

## 4. DEMO 2 — Reproducible Runtime — 15 min

**Problema →** reproduzir processos e infraestrutura não pode depender de comandos improvisados.
**Decisão →** mesmo artefato com papéis API/worker, materializado por Dockerfile + Compose.
**Hipótese →** recriar os processos conserva a capacidade e o histórico persistido.
**Demo →** comandos abaixo, após a Ponte 3 e a distinção artefato/processo.
**Evidência →** sete serviços, nova submissão funcionando e resultado anterior ainda consultável.
**Conclusão →** Same artifact, different runtime roles; reproduzibilidade local não é produção completa.

**Objetivo:** instalação operacional reproduzível. **Conceito:** mesmo artefato, três papéis; estado em volumes.
**Antes:** D1 concluída. **Arquivos:** Dockerfile, compose.yaml + override. **Fala:** “O runtime inteiro
agora é reproduzível.” Não chamar isso de production deployment.

```bash
docker compose down
docker compose up -d --wait
docker compose ps
curl --fail --silent --show-error "$AULA3_URL/executions/$D1_ID/result"
docker compose logs --tail 5 api
docker compose logs --tail 5 worker-a
docker compose logs --tail 5 worker-b
```

**Output:** mesmos sete serviços; histórico D1 permanece. `down` não remove volumes; nunca usar -v.
Para nova submissão após recriar o runtime, copie:

```bash
curl --fail-with-body --silent --show-error -X POST "$AULA3_URL/incidents" \
  -H 'Content-Type: application/json' \
  -d "{\"incident_id\":\"HTTP-RUNTIME-001\",\"version\":\"$AULA3_RUN-runtime\"}" \
  -o "$AULA3_DIR/demo2-accepted.json"
export D2_ID="$(uv run --extra lesson03 python -c 'import json,sys; print(json.load(open(sys.argv[1]))["execution_id"])' "$AULA3_DIR/demo2-accepted.json")"
for AULA3_TRY in {1..20}; do
  curl --fail --silent --show-error "$AULA3_URL/executions/$D2_ID" -o "$AULA3_DIR/demo2-state.json" || break
  D2_STATUS="$(uv run --extra lesson03 python -c 'import json,sys; print(json.load(open(sys.argv[1]))["status"])' "$AULA3_DIR/demo2-state.json")"
  printf 'status=%s\n' "$D2_STATUS"
  if [ "$D2_STATUS" = completed ] || [ "$D2_STATUS" = failed ]; then break; fi
  sleep 1
done
curl --fail --silent --show-error "$AULA3_URL/executions/$D2_ID/result"
```

Não é necessário novo build se código/dependências não mudaram. Sem delay, a execução pode estar
concluída já na primeira consulta; eventos preservam as transições.

**Pergunta:** “O que sobreviveu à remoção dos containers? E por quê?”
**Código que vale mostrar:** COPY explícito, USER e dois comandos runtime; não cada dependência uv.
**Fallback:** ps/resultado gravados. Se partida ultrapassar 2 min, usar captura e preservar discussão.
**Encerramento do bloco:** esperar nova execução terminar; serviços ficam ligados no intervalo.

## 5. DEMO 3 — Alive vs Ready — 15 min

**Problema →** um processo HTTP vivo pode estar incapaz de aceitar trabalho útil.
**Decisão →** separar liveness do processo e readiness de dependências, em api/app.py/readiness.py.
**Hipótese →** sem Redis a API permanece viva, mas perde prontidão.
**Demo →** os mesmos comandos stop/start e consultas abaixo.
**Evidência →** health200/ready503 na queda; ready200 após recuperação.
**Conclusão →** Alive ≠ Ready; **Ready ≠ Healthy End-to-End**. Não ampliar para provider health complexo.

**Objetivo:** sonda responde à pergunta certa. **Antes:** nenhuma execução ativa. **Arquivo:** api/readiness.py.
**Conceito:** disponibilidade da fila não é liveness da API; provider real não participa destas sondas.

```bash
curl --silent --show-error -i "$AULA3_URL/health"
curl --silent --show-error -i "$AULA3_URL/ready"
docker compose stop redis
curl --silent --show-error -i "$AULA3_URL/health"
curl --silent --show-error -i "$AULA3_URL/ready"
```

**Output:** antes 200/200; depois health200 alive e ready503 not_ready, redis unavailable/postgres ok.
Não usar --fail no comando da falha esperada. API ainda pode ler resultados antigos do PostgreSQL;
não submeter novos incidentes nesta demonstração. Worker health poderá acusar falha porque depende de Redis.

```bash
docker compose start redis
for AULA3_TRY in {1..20}; do
  if curl --fail --silent --show-error "$AULA3_URL/ready"; then
    printf '\nReadiness recuperada.\n'
    break
  fi
  sleep 1
done
curl --silent --show-error -i "$AULA3_URL/ready"
```

**Output:** ready200, ambas ok. O loop tem limite; não presume recuperação instantânea.
**Fala:** “Alive não significa Ready.” **Pergunta:** “Readiness200 garante que existe worker ou quota OpenAI?”
**Resposta:** não. Ela verifica somente dependências essenciais definidas para o start.
**Fallback:** captura health-http; se não recuperar, preservar estado, não apagar volumes nem reiniciar tudo.
No ensaio automatizado Redis é reiniciado em finally mesmo se uma asserção falhar.

## 6. DEMO 4 — Correlation Before Tracing — 15 min

**Problema →** precisamos localizar a mesma execução em processos distintos.
**Decisão →** associação persistida e contexto na task/logs, sem reescrever o core.
**Hipótese →** API, execução consultada e worker compartilham a identidade.
**Demo →** mesmos comandos de consulta/filtro abaixo; runtime/store.py/signals.py materializam a passagem.
**Evidência →** IDs coincidentes em registros da API e do worker.
**Conclusão →** correlação permite encontrar; com OTEL_ENABLED=false, ainda não coletamos árvore de spans, parent-child observável
ou duração por etapa **em spans**. Tempos de eventos existentes não substituem essa estrutura.

**Objetivo:** localizar uma execução entre processos. **Conceito:** identidade comum, ainda sem causalidade por spans.
**Antes:** use a captura gravada da Demo 1, que permanece após remover containers. O GET lê o
contexto persistido ao vivo. A Demo 5 virá depois, usando o conceito de correlação já observado.

```bash
export D1_ID="$(uv run --extra lesson03 python -c 'import json,sys; print(json.load(open(sys.argv[1]))["execution_id"])' "$AULA3_DIR/demo1-accepted.json")"
export D1_TRACE="$(uv run --extra lesson03 python -c 'import json,sys; print(json.load(open(sys.argv[1]))["trace_id"])' "$AULA3_DIR/demo1-accepted.json")"
curl --fail --silent --show-error "$AULA3_URL/executions/$D1_ID"
grep -F "$D1_TRACE" "$AULA3_DIR/demo1-logs.txt"
```

**Explique:** o GET é ao vivo; os logs são a captura desta sessão, feita ao final da Demo 1.
`down`/recriação remove logs locais, mas conserva contexto/eventos PostgreSQL. Isso motiva um destino
de telemetria no complete. Para observar logs sem captura, faça nova submissão (bloco 3) depois do
último `up`, e filtre antes de recriar containers:

```bash
docker compose logs --no-color api worker-a worker-b | grep -F "$D1_TRACE"
```

**Output:** queue.submitted na API e worker.received/finished no consumidor, mesmo trace/execution.
O worker_id de uma entrega duplicada pode ser diferente do worker que executou o grafo; o log finished
é snapshot, não afirma que a duplicata recalculou. Resultado GET mostra o dono real da tentativa.
**Fala:** “A identidade da execução atravessa processos.”
**Pergunta de fechamento:** “O que está faltando para transformar correlação em causalidade?”
**Resposta:** distributed tracing. A árvore e os Agent Spans serão introduzidos às 02:55 e abertos nas Demos 6/7.
**Fallback:** pares API/worker gravados. **Código:** CorrelatedStore.claim e before_publish, até 3 min.
Mantenha OTEL_ENABLED=false até a Demo 6: a passagem de correlação para tracing deve ser explícita.

## 7. DEMO 5 — Observable Failure — captura de até 2 min / ensaio opcional

**Problema →** um resultado terminal isolado não identifica a falha que levou ao desfecho.
**Decisão →** usar o contexto comum nos registros da falha conhecida e consultar o resultado durável.
**Hipótese →** podemos localizar a falha, associá-la à execução e reconhecer o outcome explícito.
**Demo →** mesmos comandos do perfil artificial abaixo; hooks operacionais projetam os eventos existentes.
**Evidência →** llm.failed, contexto comum e worker.finished com degraded_recommendation.
**Conclusão →** a falha tem identidade e desfecho verificáveis; isso ainda não é causalidade por spans.

**Foco da fala:** “Consigo identificar a falha, associá-la à execução e entender o desfecho?”
Retry/fallback já foram tratados na Aula 2. Nomear os eventos apenas para localizar evidências;
não reensinar políticas, percorrer llm_workflow ou repetir a discussão de resiliência.

**Objetivo:** tornar visíveis falha e decisão de continuidade conhecidas da Aula 2.
**Conceito:** mesmos eventos, acrescidos de identidade operacional. Sem novo provider/grafo/routing.
**Fala:** “A falha não desapareceu; ficou identificada e associada a um desfecho explícito.”
**Antes:** execuções normais terminais. Salvar logs anteriores antes de recriar processos:

```bash
docker compose logs --no-color api worker-a worker-b > "$AULA3_DIR/runtime-logs.txt"
docker compose stop api worker-a worker-b
docker compose -f compose.yaml -f compose.override.yaml \
  -f compose.lesson03-failure.yaml up -d --wait
```

Esse perfil usa **placeholder público**, modo openai e timeout artificial antes da rede, como na Aula 2.
Não demonstra OpenAI funcionando e não usa a chave real do professor. Envie obrigatoriamente
llm_failure=timeout conforme abaixo; não use este perfil para chamadas reais.

```bash
export F_VERSION="$AULA3_RUN-observable-failure"
export F_TRACE="$(uv run --extra lesson03 python -c 'from uuid import uuid4; print(uuid4().hex)')"
cat > "$AULA3_DIR/failure-request.json" <<JSON
{"incident_id":"HTTP-FAILURE-001","version":"$F_VERSION","llm_failure":"timeout","fallback":"deterministic_reference"}
JSON
curl --fail-with-body --silent --show-error -X POST "$AULA3_URL/incidents" \
  -H 'Content-Type: application/json' -H "X-Trace-ID: $F_TRACE" \
  -H "X-Correlation-ID: $F_VERSION" --data-binary @"$AULA3_DIR/failure-request.json" \
  -o "$AULA3_DIR/failure-accepted.json"
cat "$AULA3_DIR/failure-accepted.json"
export F_ID="$(uv run --extra lesson03 python -c 'import json,sys; print(json.load(open(sys.argv[1]))["execution_id"])' "$AULA3_DIR/failure-accepted.json")"
for AULA3_TRY in {1..20}; do
  curl --fail --silent --show-error "$AULA3_URL/executions/$F_ID" -o "$AULA3_DIR/failure-state.json" || break
  F_STATUS="$(uv run --extra lesson03 python -c 'import json,sys; print(json.load(open(sys.argv[1]))["status"])' "$AULA3_DIR/failure-state.json")"
  printf 'status=%s\n' "$F_STATUS"
  if [ "$F_STATUS" = completed ] || [ "$F_STATUS" = failed ]; then break; fi
  sleep 1
done
curl --fail --silent --show-error "$AULA3_URL/executions/$F_ID/result"
docker compose logs --no-color api worker-a worker-b > "$AULA3_DIR/failure-logs.txt"
grep -F "$F_TRACE" "$AULA3_DIR/failure-logs.txt"
```

**Output:** llm.requested → llm.failed → llm.retry → llm.failed → llm.fallback_activated → llm.degraded;
worker.finished outcome=degraded_recommendation, mode=degraded, aprovação pending/actions=false.
Logs são snapshots emitidos depois da tentativa; timestamp do log não é timestamp original de cada falha.
Os eventos de negócio mantêm a cronologia original; API events os consulta. Não há tokens inventados.

**Pergunta:** “Se completed, por que a recomendação ainda precisa ser distinguida como degradada?”
**Mensagem:** fallback é continuidade explícita e limitada ao case; não é mock como fallback universal de produção.
**Fallback pedagógico:** após 2 min de erro, usar failure-http gravado. Não depurar provider/secret em sala.
**Código:** no máximo o hook de log para apontar contexto e outcome; não reabrir o algoritmo de fallback da Aula 2.

Opcional no ensaio, fora do limite de 8 min: mudar fallback para human e version para `-human`, criando
outro request. Outcome será human_review_required, sem recomendação automática; não alegar revisão já feita.
O script de validação do perfil atual usa timeout determinístico:

```bash
uv run --extra lesson03 python scripts/validate_lesson03_start.py failure
```

### Voltar obrigatoriamente ao perfil mock

Somente após F_ID terminal e logs salvos:

```bash
export LLM_MODE=mock
export OTEL_ENABLED=false
docker compose stop api worker-a worker-b
docker compose up -d --wait
curl --fail --silent --show-error "$AULA3_URL/ready"
```

O override failure só entra com os três `-f`; não modifica .env. `up` normal recria os papéis mock.
Para correlacionar depois dessa recriação, use arquivo failure-logs.txt ou nova submissão mock.

## 8. Síntese — 3 min, somente depois das Demos 6–9

**Objetivo:** verbalizar o que mudou e o que falta. **Conceito:** coordenação cognitiva, operacional e runtime.
**Fala:** “O mesmo sistema ganhou uma fronteira de serviço, um artefato reproduzível, sondas e identidade.”
**Comando:** nenhum novo experimento. **Output:** arquitetura antes/depois.
**Pergunta final:** “Agora conseguimos observar uma força de trabalho agêntica. Mas como decidimos
se ela está boa, cara, lenta ou gerando valor?”
**Fallback:** quadro: Traces / Metrics / Tokens / Latency / Errors / Agent activity → ???
Gancho Aula 4 — Operating the Agentic Workforce: quality, economics, value, SLOs, optimization,
Control Plane. Apenas a pergunta, nenhuma implementação.

Encerrar somente o laboratório desta sessão, depois de concluir carga e capturar evidências:

```bash
docker compose down
```

Sem `-v`. Histórico fica nos volumes. Para retomar só a Aula 2 nesta branch:

```bash
docker compose -f compose.yaml up -d --wait
```

Esse comando não inicia os containers API/worker; os comandos originais da Aula 2 continuam disponíveis.

## 9. O que mostrar e o que deixar pronto

| Recorte | Mostrar por quê | Limite de leitura |
|---|---|---:|
| api/models.py: IncidentSubmissionRequest e ExecutionAcceptedResponse | Somente os dois recortes da Ponte 2; entrada e acompanhamento | 3 min |
| api/app.py: submit → enqueue | HTTP publica; não executa grafo | 2 min |
| Dockerfile USER/CMD + override command | Um artefato, papéis diferentes | 2 min |
| api/readiness.py e rota health | Dependências somente em readiness | 2 min |
| runtime/store.py: associação + signals.py: header | Identidade atravessa processos sem alterar domínio | 3 min |
| telemetry/tracing.py, propagation.py, instrumentation.py | Ver recortes do complete abaixo | 10 min no total de código novo |

Prontos: dependências, contratos, DDL, Docker, Pydantic settings, uv lock, fixtures, testes, bootstrap,
JSONs de request, comandos de captura, variáveis de sessão. Nada disso é exercício dos alunos.
Não percorrer todo o store, YAML, classes de exceção ou código interno de Celery/SDK OTel.

## 10. Recuperação rápida

| Sintoma | Ação concreta |
|---|---|
| ModuleNotFoundError | `uv sync --locked --extra lesson03`; mantenha --extra nos comandos |
| API não aparece | `docker compose config --services`: verificar override presente e raiz correta |
| 409 | Mesmo incident/version com opções diferentes: nova version; não limpar banco |
| 422 | Conferir modelo em /docs, modo e controles; só INCIDENT-001 é workload suportado |
| 503 no POST | Dependência/publicação não confirmada; corrigir e reenviar request idêntico |
| queued eterno | `docker compose ps` e logs worker; conferir modo/modelo/fila e consumidores |
| health200 ready503 | Esperado se Redis/Postgres indisponível; ler dependencies |
| trace não aparece em logs atuais | Container foi recriado? Use captura salva, não invente trace retroativo |
| OpenAI sem chave | Startup acusa OPENAI_API_KEY; configurar antes de subir, não imprimir chave |
| Porta ocupada | Encerrar seu ensaio anterior ou ajustar API_PORT e AULA3_URL; não matar processos arbitrários |
| Duração “alta” em mock | demo_delay_ms está no request; inclui atraso artificial explícito |
| Nenhum span com OTEL_ENABLED=true | Conferir exporter endpoint, Collector, Jaeger e recreação dos três processos; executar o helper da Demo 6 |

Todos os fallbacks gravados são identificados como ensaio anterior. Evitar consumir tempo da aula
com troubleshooting: dois minutos por problema, depois discussão com captura.

## 11. Storyboard conceitual

Service Boundary → contrato público → camada operacional → artefato/papéis → configuração → sondas
→ correlação → Trace/Span/W3C → agentes/tools/LLMs → tempo/falha → perguntas da Aula 4.
Nenhum slide novo é gerado automaticamente; este é o roteiro conceitual para projeção.

## 12. Demos do complete — preparar antes da aula

Preserve Demos1–4 com OTEL_ENABLED=false para tornar a fronteira explícita.
Os comandos abaixo partem da raiz e das variáveis AULA3_DIR/AULA3_URL da preparação.
Não iniciar outra stack ou workers locais em paralelo. Concluir carga antes de recriar API/workers.
O helper imprime URL direta e grava JSON do backend e árvore curta para fallback; não gera traces fictícios.
No macOS, abrir a URL impressa com `open`; outros sistemas podem colá-la no navegador.

### Demo 6 — First Distributed Trace — 15 min

**Problema →** IDs encontram registros, mas não mostram a relação entre operações.
**Hipótese →** W3C preserva contexto HTTP → publicação → processamento → grafo.
**Execução →** habilitar o runtime já preparado e publicar um único replay do mesmo INCIDENT-001.
**Trace →** abrir URL impressa e localizar os quatro níveis.
**Evidência →** mesmo trace, span IDs diferentes, serviços API e worker; resultado ainda exige aprovação.
**Conclusão →** identidade virou causalidade observável.

Preparar a recriação no intervalo se o ensaio local mostrar demora; a mudança pode ser apresentada
com captura comparativa. Não construir/downloadar imagens em sala.

```bash
export LLM_MODE=mock
export OTEL_ENABLED=true
export OTEL_CAPTURE_CONTENT=false
export DEMO_AGENT_DELAY_MS=0
export LOG_FORMAT=json
docker compose up -d --wait
curl --fail --silent --show-error "$AULA3_URL/ready"
uv run --extra lesson03 python scripts/trace_lesson03.py normal --output "$AULA3_DIR/traces"
export D6_TRACE="$(uv run --extra lesson03 python -c 'import json,sys; print(json.load(open(sys.argv[1]))["trace_id"])' "$AULA3_DIR/traces/normal-summary.json")"
open "http://localhost:16686/trace/$D6_TRACE"
```

Esperado: POST202, completed, aproximadamente duas dezenas de spans (confirmar captura, não fixar
quantidade como contrato), árvore API → publish → process → workflow. A UI pode levar alguns segundos
por causa do batch; helper espera até30s e verifica backend. Não repetir POST só porque a UI demorou.
Pergunta: “Agora conseguimos apenas correlacionar ou conseguimos reconstruir o caminho?”
Recorte1: initialize_tracing em telemetry/tracing.py (2min). Recorte2: inject e extract nos headers
em propagation.py/runtime/signals.py (2min). Nenhum boilerplate ao vivo.
Fallback: normal-tree.txt/normal-trace.json da sessão ou capturas da validação, declaradas como gravadas.

### Demo 7 — Agent Spans — 15 min

**Problema →** worker não revela qual etapa agêntica foi executada.
**Hipótese →** operações semânticas tornam trabalho e coordenação distinguíveis.
**Execução →** reutilizar o trace da Demo6, sem nova carga.
**Trace →** expandir workflow; Supply; tool inventory.lookup; llm completion.
**Evidência →** Supervisor, três especialistas irmãos, consolidation, deterministic finance,
Challenger, Recommendation, human_approval. Barra temporal mostra sobreposição quando mensurável.
**Conclusão →** Agent Span torna uma etapa da força de trabalho observável.

```bash
open "http://localhost:16686/trace/$D6_TRACE"
cat "$AULA3_DIR/traces/normal-tree.txt"
```

Na UI: expandir `workflow incident-investigation`, depois `agent supply`; clicar em uma barra
para ver tags e parent. `gen_ai.provider.name=mock` e `deterministic_substitute` significam que o
marcador não mede inferência. Não há tokens de mock. Tool spans medem as consultas reais locais.
Finance aparece explicitamente determinístico; aprovação continua pending.
Pergunta: “Qual parte pertence à coordenação e qual pertence ao trabalho do agente?”
Recortes3/4: workflow operation e início/fim do observer em telemetry/instrumentation.py (4min).
Não apresentar soma das durações paralelas como duração total. Se as barras mock forem pequenas,
usar zoom e a Demo8; testes com barreira também comprovam paralelismo, sem fingir latência real.
Fallback: árvore gravada e diagrama; não afirmar ordenação total entre Supply/Production/Logistics.

### Demo 8 — Find the Bottleneck — 10 min

**Problema →** mesma arquitetura pode esconder espera numa operação.
**Hipótese →** uma espera explícita em Logistics será localizada pelo trace.
**Execução →** somente DEMO_AGENT_DELAY_MS muda; mesmo grafo, fixture e cálculos.
**Trace →** abrir novo trace e comparar barra Logistics com irmãos e join.
**Evidência →** atributo demo_delay_ms=1500; join inicia depois do ramo mais lento.
**Conclusão →** trace localiza onde o tempo foi gasto.

```bash
export DEMO_AGENT_DELAY_MS=1500
docker compose up -d --wait
uv run --extra lesson03 python scripts/trace_lesson03.py bottleneck --output "$AULA3_DIR/traces"
export D8_TRACE="$(uv run --extra lesson03 python -c 'import json,sys; print(json.load(open(sys.argv[1]))["trace_id"])' "$AULA3_DIR/traces/bottleneck-summary.json")"
open "http://localhost:16686/trace/$D8_TRACE"
```

Perguntar **antes de abrir:** “Onde vocês acham que está a latência?”
Delay é artificial no início de Logistics, não tempo real de OpenAI nem alteração de dados.
Limite de2s/configuração local: não é mecanismo de produção. A mudança exige recriação dos processos.
Nenhum código novo projetado nesta demo. Fallback: bottleneck-tree.txt e atributo rotulado.

### Demo 9 — Observable Failure as a Trace — 7 min

**Problema →** saber que houve falha não mostra onde nem o que ocorreu depois.
**Hipótese →** duas falhas do provider e a decisão de fallback estarão no caminho observado.
**Execução →** perfil artificial já aprovado na Aula2; nenhuma chave real, nenhuma chamada externa.
**Trace →** expandir primeiro workflow/Supervisor: duas chamadas ERROR; evento retry;
processamento: fallback_activated; segundo workflow determinístico; degraded.
**Evidência →** duas tentativas de request dentro da mesma tentativa durável; novo workflow de
continuidade, resultado degraded_recommendation, aprovação pending.
**Conclusão →** a falha passou de registro isolado para parte do caminho observável.

```bash
export DEMO_AGENT_DELAY_MS=0
docker compose -f compose.yaml -f compose.override.yaml -f compose.lesson03-failure.yaml up -d --wait
uv run --extra lesson03 python scripts/trace_lesson03.py failure --output "$AULA3_DIR/traces"
export D9_TRACE="$(uv run --extra lesson03 python -c 'import json,sys; print(json.load(open(sys.argv[1]))["trace_id"])' "$AULA3_DIR/traces/failure-summary.json")"
open "http://localhost:16686/trace/$D9_TRACE"
```

Clique no span `messaging process incident` para seus eventos fallback/degraded e no Supervisor
para retry. Events OTel têm tempo observado; ExecutionEvent continua com sequência durável no banco.
Recorte5: observe_event, caso llm.requested/failed/completed (2min). Total de código novo:10min.
Pergunta: “Agora só sei que houve falha ou localizo onde ocorreu e o que aconteceu depois?”
Não reensinar retry/redelivery nem implementar routing. Fallback: failure-tree.txt/JSON e captura UI.
Se precisar investigar mais de2min, usar captura. Restaurar mock após a demo:

```bash
export LLM_MODE=mock
export DEMO_AGENT_DELAY_MS=0
docker compose up -d --wait
curl --fail --silent --show-error "$AULA3_URL/ready"
```

### OpenAI real — opcional, fora da sequência obrigatória

Uma execução apenas, antes da aula ou substituindo a execução mock da Demo6, nunca adicionando
um bloco além de240min. Exige chave/modelo previamente configurados e perfil failure removido.
Não usar chave em argumento de comando, não exibir `.keys`, `.env` ou `compose config` expandido.
No terminal privado, solicite a chave sem eco; depois restaure mock:

```bash
read -rs 'OPENAI_API_KEY?OPENAI_API_KEY (entrada oculta): '
export OPENAI_API_KEY
export OPENAI_MODEL=gpt-4.1-mini
export LLM_MODE=openai
export OTEL_ENABLED=true
docker compose up -d --wait
uv run --extra lesson03 python scripts/trace_lesson03.py normal --output "$AULA3_DIR/openai"
unset OPENAI_API_KEY
export LLM_MODE=mock
docker compose up -d --wait
```

O `read` acima é zsh/macOS; bash usa `read -rsp 'OPENAI_API_KEY: ' OPENAI_API_KEY`.
Span real: provider=openai, modelo solicitado, latência e tokens somente quando usage veio na resposta.
Saída/custo não são prometidos. Captura de conteúdo continua desligada. Não depurar quota em sala.

### Falha do Collector — ensaio pré-aula / discussão

Não é uma quinta demo nova. Confirmar que sondas não dependem de telemetria:

```bash
docker compose stop otel-collector
curl --fail --silent --show-error "$AULA3_URL/health"
curl --fail --silent --show-error "$AULA3_URL/ready"
curl --fail-with-body --silent --show-error -X POST "$AULA3_URL/incidents"   -H 'Content-Type: application/json'   -d "{\"incident_id\":\"HTTP-NO-COLLECTOR\",\"version\":\"$AULA3_RUN-collector-down\"}"   -o "$AULA3_DIR/no-collector.json"
export NC_ID="$(uv run --extra lesson03 python -c 'import json,sys; print(json.load(open(sys.argv[1]))["execution_id"])' "$AULA3_DIR/no-collector.json")"
for AULA3_TRY in {1..30}; do
  curl --fail --silent --show-error "$AULA3_URL/executions/$NC_ID"
  sleep 1
done
curl --fail --silent --show-error "$AULA3_URL/executions/$NC_ID/result"
docker compose start otel-collector
```

Esperado: health/ready200 e completed, mesmo com falha de exportação. Telemetria pode ser perdida:
exporter tem buffer finito/retry limitado; não é auditoria durável. Não prometer recuperar todos os spans.
Observability failure != Business runtime failure. Ao terminar todas as capturas, executar o down da seção8.


### Medição simples de overhead — somente ensaio pré-aula

Duas execuções de aquecimento e cinco amostras sequenciais em cada perfil. Sem provider pago,
sem delay artificial. Não rodar suíte/carga paralela durante a coleta. Não é benchmark científico.

```bash
export LLM_MODE=mock
export LOG_FORMAT=json
export DEMO_AGENT_DELAY_MS=0
export OTEL_ENABLED=false
docker compose up -d --wait
uv run --extra lesson03 python scripts/measure_lesson03_overhead.py disabled
export OTEL_ENABLED=true
docker compose up -d --wait
uv run --extra lesson03 python scripts/measure_lesson03_overhead.py enabled
```

Compare median_execution_ms nos arquivos artifacts/lesson03-complete/overhead-*.json.
Mede tempo de tentativa persistido, não custo total do Collector nem SLA. Host, banco, scheduling,
conexões e variabilidade influenciam uma amostra tão pequena. Não prometer overhead universal.

### Teste opcional ponta a ponta do complete

Com perfil mock/OTel ativo:

```bash
LESSON02_INTEGRATION=1 LESSON03_INTEGRATION=1 LESSON03_TRACING_INTEGRATION=1 \
  LLM_MODE=mock uv run --extra lesson03 pytest -q
```

Com perfil de falha artificial da Demo9 ativo:

```bash
LESSON03_TRACING_INTEGRATION=1 LESSON03_TRACE_DEMO=failure \
  uv run --extra lesson03 pytest tests/integration/test_lesson03_traces.py -q
```

Essas integrações consultam o backend, não dependem só de screenshots. Testes unitários usam
exporters em memória e provider controlado; não chamam OpenAI real.
