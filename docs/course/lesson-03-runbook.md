# Aula 3 — Runtime, Deployment & Production

## Do sistema distribuído ao runtime operável em produção

**Candidato lesson-03-start**, sem tag. Este runbook será refinado depois do complete.
O professor demonstra; alunos observam arquitetura e trade-offs, sem programação durante a aula.
Comandos abaixo são para zsh/bash, na raiz do repositório. Setup/build/testes ficam antes das 4 horas.

> Produção não começa quando o código funciona. Produção começa quando o sistema pode ser
> implantado, observado, reiniciado e operado com previsibilidade.

O start entrega API, containers, settings, sondas e identidade entre processos. Ainda não há spans
end-to-end ou métricas coletadas. Não apresentar este laboratório como deployment de produção real.
[Arquitetura, contratos e limites](lesson-03/contracts.md) · [Evidências reais](lesson-03/validation.md).

## 0. Preparação do professor — fora da aula

### 0.1 Localizar o checkout e conferir o estado

```bash
cd '/Users/leandrolopes/Documents/ChatGPT/Disciplina Mult-Agents/agentic-operations-control-tower'
git branch --show-current
git status --short
git tag --list
```

Esperado nesta revisão: branch `codex/lesson-03-start`. Ela ainda não foi publicada; não usar
`git checkout lesson-03-start` como se existisse tag. Em outra máquina, usar o checkout que receber
esta revisão após aprovação. Não descartar alterações locais para trocar de branch.

### 0.2 Pré-requisitos e perfil

Docker Desktop aberto; Git, uv, curl e Python disponíveis. Primeiro download precisa de rede;
prepare imagens/dependências antes de entrar na sala. Não iniciar workers locais da Aula 2 em paralelo
com os containers. `compose.yaml` histórico está intacto; override automático acrescenta os três papéis.

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

Esperado: api, worker-a, worker-b, redis e postgres healthy. API inicializa schema aditivo no startup;
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
- Somente seis recortes de código da seção 9. Nada de escrever YAML/DDL/boilerplate em sala.
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
| 00:00–00:20 | Retomada Aula 2: distribuído ≠ produção | 20 |
| 00:20–00:45 | Service boundary / API | 25 |
| 00:45–01:05 | Demo 1 — API | 20 |
| 01:05–01:30 | Packaging / containers / runtime roles | 25 |
| 01:30–01:50 | Demo 2 — Compose completo | 20 |
| 01:50–02:05 | Intervalo | 15 |
| 02:05–02:30 | Configuração por ambiente | 25 |
| 02:30–02:55 | Health vs readiness | 25 |
| 02:55–03:15 | Demo 3 — health/readiness | 20 |
| 03:15–03:40 | Telemetria: 17 min teoria + até 8 min Demo 5 preparada | 25 |
| 03:40–03:55 | Demo 4 — correlação / trace context | 15 |
| 03:55–04:00 | Síntese e gancho | 5 |

Demo 5 é uma extensão preparada do bloco de telemetria, não mais um bloco de 20 minutos.
Se houver atraso, mostrar sua captura; não retirar teoria, intervalo ou síntese. Mais de 60–80 minutos
de contexto/teoria estão preservados. Tempos de aula são estimativas, não cronômetro de uma turma real.

## 2. Blocos conceituais — fala, pergunta, output e fallback

### 00:00–00:20 — retomada

**Objetivo:** distinguir execução distribuída de operação previsível. **Conceito:** o algoritmo pode
funcionar sem o sistema ser instalável/operável. **Fala:** “Na Aula 2 resolvemos quem recebe trabalho,
quem executa e onde guardar o histórico. Agora: como outra pessoa instala e opera esse conjunto?”
**Comando:** nenhum. **Output:** desenho CLI → Redis → workers → mesmo grafo → PostgreSQL.
**Pergunta:** “Se o processo responde, vocês entregariam tráfego a ele?”
**Fallback:** cinco caixas no quadro. Não reexecutar benchmark da Aula 2.

### 00:20–00:45 — service boundary

**Objetivo:** separar aceitação de execução. **Conceito:** contrato HTTP, 202, identidade e consulta.
**Fala:** “O cliente não precisa conhecer Celery. Precisa de um contrato para submeter e acompanhar.”
**Comando:** nenhum; abrir modelos públicos já localizados. **Output:** POST202 → GET estado/result.
**Pergunta:** “Se a resposta HTTP se perder, reenviar deve criar outra operação?”
**Fallback:** request/response gravados. Explicar 409 (identidade/opções), 422 (contrato) e 503 (dependência).

### 01:05–01:30 — packaging e papéis

**Objetivo:** separar software de papel operacional. **Conceito:** imagem é artefato, container é processo.
**Fala:** “O mesmo software pode assumir papéis de runtime diferentes.”
**Comando:** nenhum obrigatório; mostrar só CMD e command do Compose já prontos.
**Output:** uma imagem → API, worker-a, worker-b; volumes pertencem à infraestrutura.
**Pergunta:** “Precisamos duplicar o repositório para adicionar um worker?”
**Fallback:** diagrama de artefato/papéis. “Container não é deploy. Container é uma unidade reproduzível de execução.”

### 02:05–02:30 — configuração

**Objetivo:** distinguir código, configuração e segredo. **Conceito:** ambiente vence .env; config consistente
entre produtores/consumidores. **Fala:** “Código permanece o mesmo. Configuração muda por ambiente.”
**Comando seguro**, em vez de imprimir todo o ambiente:

```bash
docker compose exec -T api python -c 'from control_tower.runtime.settings import RuntimeSettings; s=RuntimeSettings(); print("env=",s.app_env,"mode=",s.llm_mode,"log=",s.log_format,"otel=",s.otel_enabled)'
```

**Output:** local, mock, human, False (ou json se selecionado). Não exibir DSN/chave.
**Pergunta:** “Editar uma variável no meu terminal altera um worker já em execução?”
**Fallback:** tabela de settings em contracts.md. Mudanças exigem recriação/reinício do processo.

### 02:30–02:55 — sondas

**Objetivo:** separar perguntas operacionais. **Conceito:** liveness do processo, readiness de dependências,
saúde do provider e sucesso end-to-end são verificações diferentes.
**Fala:** “Alive não significa Ready. Ready não significa saudável end-to-end.”
**Comando:** nenhum antes da Demo 3. **Output:** matriz vivo/pronto/resultado.
**Pergunta:** “Derrubar Redis deveria fazer o processo HTTP fingir que morreu?”
**Fallback:** prever a matriz health200/ready503 no quadro e depois conferir captura.

### 03:15–03:40 — telemetria

**Objetivo:** identificar sinais e seus limites. **Conceito:** logs, métricas, traces e eventos duráveis.
**Fala:** “Logs mostram eventos. Traces mostram causalidade. Métricas mostram comportamento ao longo do tempo.”
“LangGraph coordena agentes. OpenTelemetry observa o caminho.”
**Comando:** Demo 5 preparada abaixo (até 8 min); restante é discussão/diagrama.
**Output:** falha e outcome com mesma identidade; não há árvore de spans no start.
**Pergunta:** “Dois logs com o mesmo ID provam qual chamada causou a outra?”
**Fallback:** logs gravados. “ExecutionEvent e OpenTelemetry resolvem problemas diferentes.”
As seis métricas de config.py são contratos futuros. OTel é o contrato de instrumentação; Langfuse
pode ser um destino especializado, não uma dependência da aula.

## 3. DEMO 1 — Service Boundary / API — 20 min

**Objetivo:** comprovar 202 rápido e acompanhamento independente. **Conceito:** trabalho assíncrono.
**Antes:** runtime saudável, perfil mock; sem pendências. **Arquivos:** api/app.py, api/models.py,
distributed/producer.py (inalterado). **Condução:** 3 min hipótese, 8 min comandos, 9 min discussão.

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

## 4. DEMO 2 — Reproducible Runtime — 20 min

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

**Output:** mesmos cinco serviços; histórico D1 permanece. `down` não remove volumes; nunca usar -v.
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

## 5. DEMO 3 — Alive vs Ready — 20 min

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

## 6. DEMO 4 — Correlation / trace context — 15 min

**Objetivo:** localizar uma execução entre processos. **Conceito:** identidade comum, ainda sem causalidade por spans.
**Antes:** use a captura gravada da Demo 1, que permanece após remover containers. O GET lê o
contexto persistido ao vivo. Se a Demo 5 foi feita no bloco anterior, sua captura também está disponível.

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
**Pergunta:** “Com ID igual eu reconstruo parentesco/duração de cada chamada automaticamente?”
**Fallback:** pares API/worker gravados. **Código:** CorrelatedStore.claim e before_publish, até 3 min.
Distributed spans completos ficam para lesson-03-complete. Não mostrar dashboard inexistente.

## 7. DEMO 5 — Observable Failure preparada — até 8 min

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
**Código:** somente hooks de log e 1 ramo llm_workflow original já explicado na Aula 2.

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

## 8. Síntese — 5 min e encerramento

**Objetivo:** verbalizar o que mudou e o que falta. **Conceito:** coordenação cognitiva, operacional e runtime.
**Fala:** “O mesmo sistema ganhou uma fronteira de serviço, um artefato reproduzível, sondas e identidade.”
**Comando:** nenhum novo experimento. **Output:** arquitetura antes/depois.
**Pergunta:** “Que informações faltam para explicar a causalidade de uma execução lenta?”
**Fallback:** quadro. O gancho é tracing distribuído completo; não implementar Aula 4.

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
| api/models.py: IncidentSubmissionRequest | Fronteira pública pequena, workload honesto | 2 min |
| api/app.py: submit → enqueue | HTTP publica; não executa grafo | 2 min |
| Dockerfile USER/CMD + override command | Um artefato, papéis diferentes | 2 min |
| api/readiness.py e rota health | Dependências somente em readiness | 2 min |
| runtime/store.py: associação + signals.py: header | Identidade atravessa processos sem alterar domínio | 3 min |
| telemetry/config.py e tracing.py | Contrato preparado ≠ instrumentação concluída | 1 min |

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
| Nenhum span com OTEL_ENABLED=true | Esperado no start; SDK preparado não é tracing completo |

Todos os fallbacks gravados são identificados como ensaio anterior. Evitar consumir tempo da aula
com troubleshooting: dois minutos por problema, depois discussão com captura.
