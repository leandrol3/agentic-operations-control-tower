# Ensaio final — Aula 2 / candidato lesson-02-complete

## Parecer: AJUSTAR a condução pedagógica; arquitetura aprovada no escopo do laboratório

Ensaio executado com comandos reais, Redis/PostgreSQL e dois processos Celery. Tempos de máquina
foram medidos; tempos de exposição/discussão abaixo são estimativas de condução, **não uma aula de
quatro horas ministrada a uma turma**. O conteúdo cabe em quatro horas com preparação prévia,
65 min de teoria/contexto protegidos e 10 min de margem. Sem live coding.

Não foram alterados código de aplicação, arquitetura, runbook atual ou tags. Este relatório propõe
ajustes de roteiro para revisão. Nenhum conteúdo da Aula 3 foi implementado.

## Evidência do ensaio executado

- 258 testes distintos aprovados: 248 locais + 10 de integração. Smoke e INCIDENT-001 OK.
- Lote de 20 ficou queued antes de iniciar os consumidores; A e B processaram o lote.
- Publicação + início dos dois workers + conclusão do lote: **7,82 s**.
- Retry tratado de Logistics até completed na tentativa 2: **2,67 s**.
- Queda de A, início de B e recuperação até completed: **111,47 s** para a sequência completa;
  **110,85 s** do kill até completed. Mesmo UUID, attempt=2.
- Duas publicações até conclusão da execução única: **3,74 s**; attempt=1. Log do segundo worker
  retornou duplicate=True, confirmando que a segunda entrega chegou durante o processamento.
- Consultas após parar ambos os workers continuaram funcionando.
- CLI batch: 15 linhas/81 colunas; execution: 10/54; events: até 13/63; result: 6/99.
- Os contadores finais incluem histórico anterior: 46 completed = 23 anteriores + 23 deste ensaio.

Máquina é uma pequena parte do bloco: operação dos três terminais, formulação de hipótese e interpretação
ocupam o restante. Não confundir os 111 s de recuperação medidos com os 25 min pedagógicos de falhas.

## Ajustes necessários antes da aula

1. **Sequência:** o bloco 5 atual antecipa idempotência antes da fila. Substituir por “por que precisamos
   de fila?”. Depois demonstrar workers → retry/redelivery → idempotência → estado → eventos.
   A identidade pode ser mencionada antes; prova e implementação ficam após a falha.
2. **Margem:** a agenda atual soma exatamente 240 min. Reservar 10 min explícitos, sem consumir teoria.
3. **Worker loss:** preparar comandos/UUID/PID sem improviso. Os 10 s atuais são uma janela curta para
   copiar dois identificadores e explicar ao mesmo tempo. Explicar o slide antes; executar em silêncio;
   só depois discutir durante a espera. Caso o professor precise ampliar o delay para 30 s, ensaiar
   essa variante antes da aula; o ensaio registrado aqui usa exatamente os 10 s atuais.
4. **Código projetado:** trecho atual de task termina antes da chamada ao LangGraph; trecho de claim
   não inclui o advisory lock. Mostrar os recortes relevantes descritos abaixo, não o módulo completo.
5. **Histórico existente:** contadores são cumulativos. Registrar a contagem inicial e trabalhar com
   os UUIDs do novo lote. Não dizer “há 20 completed” se o banco também contém ensaios anteriores.

## Agenda recomendada — 240 min

| Horário | Bloco | Estimativa de condução | Teoria/contexto protegido |
|---|---|---:|---:|
| 00:00–00:20 | Problema de escala e retomada | 20 min | 15 min |
| 00:20–00:45 | Concorrência local e duas camadas de coordenação | 25 min | 20 min |
| 00:45–01:05 | Demo 1: 1 versus 5 threads | 20 min | — |
| 01:05–01:25 | Demo 2: gargalo e capacidade | 20 min | 10 min |
| 01:25–01:40 | Necessidade de fila | 15 min | 10 min |
| 01:40–01:55 | Intervalo | 15 min | — |
| 01:55–02:20 | Demo 3: workers independentes | 25 min | 10 min |
| 02:20–02:45 | Demo 4: retry e redelivery | 25 min | — |
| 02:45–03:05 | Demo 5: idempotência no store | 20 min | — |
| 03:05–03:30 | Demo 6: estado durável (12 min), eventos (13 min) | 25 min | — |
| 03:30–03:40 | Garantias e limites | 10 min | — |
| 03:40–03:50 | Margem para recuperação/perguntas acumuladas | 10 min | — |
| 03:50–04:00 | Síntese e perguntas de saída | 10 min | — |
| **Total** | | **240 min** | **65 min** |

Sem imprevistos, usar a margem para discussão do cenário “commit aconteceu, ack não”. Não preencher
com configuração adicional de Celery/PostgreSQL. Limitar inspeção de código a 10–12 min somados.
Instalação, downloads e testes completos ficam fora dos 240 min; reservar 15–20 min de preparação
com dependências já disponíveis e mais tempo se houver primeiro download.

## Validação dos oito pontos solicitados

| Ponto | Resultado | Fala necessária |
|---|---|---|
| Concorrência local × distribuição | Arquiteturas distintas verificadas | Batch: threads no mesmo processo. Celery: processos independentes coordenados externamente; ensaio usa uma máquina, não um cluster de máquinas |
| Retry × redelivery | Ambos executados separadamente | Retry é uma decisão tratada pela task; redelivery recupera uma entrega sem ack após desaparecimento do processo |
| At-least-once | Coerente com ensaio e configuração | Pode haver entrega repetida; não significa execução única nem garantia incondicional diante de toda falha |
| Idempotência no store | Claim/lock reais, testes concorrentes e duas publicações | UNIQUE escolhe identidade; lock impede duas tentativas ativas; terminal concluído não reexecuta |
| Worker failure | Reproduzível; ritmo exige preparação | Não prometer recuperação aos 60 s exatos; não usar a espera para depurar configuração |
| Views | Resumos projetáveis | UUID correlaciona; attempt não é número de mensagens; counters incluem histórico |
| Excesso de detalhes de infraestrutura | Risco moderado nos snippets | Explicar responsabilidades, não SQL/serializers/pools/redes Docker |
| Teoria mínima | Runbook atual e proposta reservam 65 min | Não consumir esse tempo com setup ou troubleshooting |

## Slides antes das demos

1. **500 chegadas, capacidade finita:** taxa de chegada, trabalho em execução, espera. As cinco categorias
   são envelopes sintéticos; a análise técnica continua sendo o caso de referência INCIDENT-001.
2. **Duas dimensões:** especialistas em paralelo dentro de um LangGraph; vários LangGraphs em execução
   em threads locais ou workers independentes. Três especialistas não significam três workers Celery.
3. **Gargalo:** mais concorrência só ajuda até saturar a capacidade. Prefetch/slots controlam consumo;
   fila armazena espera, mas não limita automaticamente a admissão nem elimina backlog ilimitado.
4. **Por que fila:** produtores e consumidores podem existir em momentos diferentes. Mostrar o lote
   queued antes de iniciar workers. Nomear Redis/Celery somente após explicar as responsabilidades.
5. **Duas linhas do tempo:** erro tratado → retry com backoff; processo desaparece → ausência de ack →
   visibility timeout/varredura → redelivery. Em solo não existe pai Celery vivo para rejeitar o filho.
6. **Entrega versus execução:** at-least-once, execution_id estável, attempt crescente. Claim único +
   exclusão mútua; hash sozinho não resolve. Não prometer exactly-once nem efeitos externos seguros.
7. **Estado versus eventos:** uma fotografia atual versus trilha ordenada. `running` não prova vida;
   interrupted é registrado na recuperação. Completed ainda exige aprovação humana; não autoriza compra.
8. **Limites:** o workflow reinicia inteiro. Não há checkpoint por nó; commit no Postgres e publicação
   no Redis não são transação única. Reenviar mesmos parâmetros recupera publicação ausente.

## Comandos exatos para o professor

Executar todos na raiz do repositório. Os UUIDs/PIDs abaixo são placeholders a substituir por valores
impressos. Usar versões novas em cada ensaio; repetir exatamente a mesma versão somente na Demo 5.

### Preparação fora da aula

```bash
uv sync --locked --extra lesson02
uv run pytest -q
LLM_MODE=mock uv run control-tower smoke
docker compose config --quiet
docker compose up -d --wait
docker compose ps
uv run control-tower db-init
LESSON02_INTEGRATION=1 uv run pytest tests/integration -q
```

### Abertura e demos locais — Terminal 3

```bash
LLM_MODE=mock uv run control-tower show INCIDENT-001 recommendation
uv run control-tower generate-incidents --count 500
uv run control-tower batch --incidents 10 --workers 1 --demo-delay-ms 500
uv run control-tower batch --incidents 10 --workers 5 --demo-delay-ms 500
uv run control-tower batch --incidents 50 --workers 5 --provider-limit 5 --demo-delay-ms 500
uv run control-tower batch --incidents 50 --workers 20 --provider-limit 5 --demo-delay-ms 500
uv run control-tower batch --incidents 50 --workers 50 --provider-limit 5 --demo-delay-ms 500
```

### Fila — Terminal 3, antes de iniciar workers

```bash
uv run control-tower executions
uv run control-tower enqueue --count 20 --version aula2-final-fila-v1 --demo-delay-ms 500
uv run control-tower executions
```

### Terminal 1 — worker A

```bash
uv run celery -A control_tower.distributed.celery_app worker --pool=solo --concurrency=1 --hostname='lesson02-A@%h' --loglevel=INFO --without-gossip --without-mingle
```

### Terminal 2 — worker B

```bash
uv run celery -A control_tower.distributed.celery_app worker --pool=solo --concurrency=1 --hostname='lesson02-B@%h' --loglevel=INFO --without-gossip --without-mingle
```

Executar `uv run control-tower executions` no Terminal 3 enquanto processam. Não abrir com logs
Celery projetados: deixar A/B como prova visual de consumidores; projetar a CLI resumida.

### Retry tratado — Terminal 3

```bash
uv run control-tower enqueue --count 1 --version aula2-final-retry-v1 --fail-specialist logistics
uv run control-tower execution <UUID_RETRY>
uv run control-tower events <UUID_RETRY> --lifecycle
```

Aguardar conclusão. Mesmo UUID, attempt=2, events mostram logistics.failed / execution.retry.

### Worker loss — sequência operacional

Parar B com Ctrl-C no Terminal 2 depois de concluir os trabalhos anteriores. A permanece pronto.

```bash
uv run control-tower enqueue --count 1 --version aula2-final-loss-v1 --demo-delay-ms 10000
uv run control-tower execution <UUID_LOSS>
kill -KILL <PID_DE_A_CONFIRMADO_NO_WORKER_ID>
uv run control-tower execution <UUID_LOSS>
```

Confirmar running antes do kill. Matar somente o PID do worker A desta demo. Reiniciar B no Terminal 2
com o comando acima; A permanece parado. Consultar depois, sem rolagem contínua de logs:

```bash
uv run control-tower execution <UUID_LOSS>
uv run control-tower events <UUID_LOSS> --lifecycle
```

### Idempotência — reiniciar A, Terminal 3

```bash
uv run control-tower enqueue --count 1 --version aula2-final-duplicate-v1 --demo-delay-ms 3000
uv run control-tower enqueue --count 1 --version aula2-final-duplicate-v1 --demo-delay-ms 3000
uv run control-tower execution <UUID_DUPLICATE>
uv run control-tower events <UUID_DUPLICATE> --lifecycle
```

### Estado e eventos — parar ambos os workers, manter banco disponível

```bash
uv run control-tower execution <UUID_LOSS>
uv run control-tower result <UUID_LOSS>
uv run control-tower events <UUID_LOSS> --lifecycle
uv run control-tower events <UUID_LOSS>
```

Explicar estado/resultado antes da trilha. A view padrão events mostra os últimos 12 eventos; para
Supervisor/Supply usar trilha gravada ou `--json` fora da projeção, sem insinuar que os anteriores sumiram.
Ao encerrar: `docker compose down`, sem `-v`.

## Código que vale mostrar — 10–12 min no total

| Momento | Recorte | Conceito | Evitar |
|---|---|---|---|
| Workers | `tasks.py`: chamada `run_workflow(...)`, validação do término e persistência | Celery envolve o grafo original | Task inteira com callbacks/temporização |
| Retry | `tasks.py`: ramo WorkflowFailure + `self.retry` | Backoff e orçamento limitados | Catálogo de opções Celery |
| Idempotência | `store.py`: UNIQUE/ON CONFLICT + `acquire` com pg_try_advisory_lock | Identidade e exclusão são proteções distintas | Explicar sintaxe SQL/JSONB |
| Estado | `models.py`/`durable.py`: IDs, status, attempt, result | Execução durável e resultado validado | Todos os validadores Pydantic |
| Eventos | Campos de correlação + `finish` | Resultado e evento no mesmo commit | Loop de inserts/sequence e conexões |

O snippet de task existente não mostra a chamada ao grafo e o snippet de claim não mostra o lock.
Preparar recortes/slides antes da aula. As linhas longas de SQL não são adequadas à projeção de 100
colunas; usar diagrama de responsabilidade e destacar apenas a constraint e a aquisição do lock.
Campos futuros de tokens/custo/qualidade podem ser citados como null; não abrir assunto de observabilidade.

## Tudo que deve ficar pronto

Compose, dependências, schema, generator, fixtures, autenticação local, configuração Celery, workers
com nomes únicos, versão de cada experimento, trechos curtos, UUIDs dos fallbacks e outputs gravados.
Não escrever Docker/YAML, SQL, boilerplate de task, serializers, conexões ou testes em sala.
Não demonstrar criação de usuários do banco nem instalação de Redis.

## Fallbacks e regras de tempo

- **Local/capacidade:** uma tentativa; depois tabela gravada se houver erro. Não ajustar benchmark ao vivo.
- **Fila:** se banco/broker indisponível, usar captura queued → running → completed. Não gastar mais
  de 2 min diagnosticando infraestrutura em sala; explicar que captura não é execução ao vivo.
- **Retry:** o evento persistido comprova o retry mesmo se a CLI não capturou a janela curta de queued.
- **Worker loss:** explicar antes de executar; esperar até 3 min após kill. Nesse intervalo, discutir
  ausência de ack e significado de running. Ao exceder 3 min, mostrar trilha gravada, preservar UUID
  para diagnóstico posterior e seguir. Se terminou antes do kill, não alegar perda recuperada.
- **Duplicata:** usar os dois outputs com mesmo UUID e event log com um started. Testes de concorrência
  são evidência adicional; não substituir exclusão mútua por explicação apenas do hash.
- **Durabilidade:** parar workers, consultar banco. Se banco estiver indisponível, mostrar export
  persistido e identificar explicitamente como captura de ensaio anterior.

## Critério de saída dos alunos

O aluno deve explicar onde o trabalho espera, quem limita processamento, por que uma mensagem pode
voltar, como a mesma operação evita concorrência duplicada e onde permanece o histórico quando o
worker morre. Saber escrever configurações Celery/Redis/PostgreSQL não é objetivo de avaliação.

Resultados e tempos medidos do ensaio: [outputs finais](final-rehearsal-outputs.md).
