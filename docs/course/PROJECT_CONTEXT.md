# Contexto permanente do projeto

## Correção pedagógica vigente — prevalece sobre o briefing histórico

A disciplina tem 16 horas, em quatro aulas de quatro horas. Os alunos NÃO programam durante
as aulas. O professor implementa e demonstra; alunos acompanham decisões, comportamento e trade-offs.
O repositório prioriza demonstração ao vivo, progressão visual/conceitual, reprodução posterior,
comparação Git e redução de boilerplate. Labs são Guided Demo / Observation Guides.
Método vigente: teoria → problema → demonstração pelo professor → observação → discussão → reflexão.
Menções abaixo a “codificação conjunta”, exercícios de implementação pelo aluno ou construção durante
a aula são históricas e substituídas por esta correção. Reprodução posterior é opcional e não requer
implementar o sistema. O professor usa `lesson-01-runbook.md`.

Start preserva datasets, models, tools determinísticas, CLI, fixtures, configuração, testes e mock.
A progressão posterior demonstra shared state, especialistas, Supervisor, LangGraph, paralelismo,
consolidação, Finance, Challenger, recomendação estruturada e aprovação humana.
Start revisado aprovado pelo professor, registrado em 171c324. Agora está autorizada a implementação
do candidato lesson-01-complete para Demos 5–8, na branch codex/lesson-01-complete.
A tag publicada lesson-01-start permanece intacta. Não criar/mover lesson-01-complete antes da revisão.
Mock é o modo desta entrega; OpenAI opcional foi adiado. Não avançar à Aula 2 nem adicionar infraestrutura
prevista para aulas seguintes. Os contratos e cálculos são determinísticos, a orquestração usa LangGraph.

## Status e limite de escopo
Fase atual: candidato `lesson-01-complete`. Na inspeção inicial, o repositório estava vazio, sem histórico,
tags, código ou documentos de curso anteriores. Abaixo está o briefing integral do professor,
preservado como fonte de requisitos e organizado pelas 49 seções originais.
Somente após validação do professor implementar `lesson-01-complete`; não avançar à Aula 2.

## Mapa de consulta
- Seções 1–5: objetivo, pré-requisitos e método didático.
- Seções 6–18: NovaCore, agentes, dados e contratos.
- Seções 19–24: stack, portabilidade e repositório único.
- Seções 25–33: progressão das quatro aulas e experimentos.
- Seções 34–43: perguntas de engenharia, qualidade e Git.
- Seções 44–49: limites, primeira entrega e critérios de aceite.

## Briefing integral
# Agentic Operations Control Tower — Project Master Brief

Você será o principal engenheiro de software responsável por construir o laboratório oficial da disciplina **Multi-Agent Systems, Deployment, and Scaling**, parte de um MBA em **AI Engineering & Multi-Agents**.

Trabalhe diretamente no repositório:

`leandrol3/agentic-operations-control-tower`

Este projeto não é apenas uma demonstração de agentes. Ele deve ser um laboratório tecnicamente sólido, didaticamente progressivo e executável pelos alunos em suas próprias máquinas.

Antes de alterar código, leia completamente este documento e os demais documentos existentes em `docs/course/`.

---

# 1. CONTEXTO DA DISCIPLINA

A disciplina faz parte de uma formação mais ampla em AI Engineering.

Os alunos já terão cursado anteriormente uma disciplina chamada aproximadamente:

**Agent Orchestration with LangChain and CrewAI**

Na disciplina anterior eles já terão aprendido conceitos como:

* o que é um agente;
* tools;
* chains;
* LangChain;
* CrewAI;
* memória;
* agentes colaborativos;
* padrões sequenciais;
* execução paralela;
* arquitetura hierárquica;
* event-driven;
* observabilidade introdutória;
* LangSmith;
* logs estruturados.

Portanto, esta disciplina NÃO deve repetir extensivamente:

* introdução básica a agentes;
* criação de agentes simples;
* prompt engineering básico;
* CrewAI básico;
* LangChain básico;
* RAG;
* arquitetura cognitiva avançada;
* segurança e governança de IA;
* plataformas enterprise específicas.

Esses temas são cobertos em outras disciplinas do MBA.

---

# 2. OBJETIVO FORMAL DA DISCIPLINA

Objetivo definido na ementa:

> Ao final desta disciplina, o aluno saberá arquitetar, fazer deploy e escalar sistemas multi-agente em ambientes de produção, garantindo robustez operacional e eficiência de custo.

Essa frase deve orientar todas as decisões técnicas e pedagógicas.

Não basta fazer agentes colaborarem.

O aluno deve compreender a diferença entre:

**Multi-Agent Demo**

e

**Production Multi-Agent System**

---

# 3. POSICIONAMENTO PEDAGÓGICO

A disciplina deve responder:

> Como transformar um sistema multiagente funcional em um sistema de software real, distribuído, resiliente, observável, escalável e economicamente sustentável?

A mensagem central da disciplina é:

> Um agente é uma unidade de inteligência.
> Um sistema multiagente é uma organização.
> Colocar essa organização em produção é um problema de engenharia.

Outra mensagem essencial:

> O desafio não é apenas criar agentes inteligentes. É construir uma força de trabalho agêntica confiável, observável, resiliente e economicamente sustentável.

---

# 4. MÉTODO DE ENSINO DO PROFESSOR

O professor é Leandro Lopes.

Seu método de ensino segue deliberadamente:

**teoria didática → problema → demonstração → codificação conjunta → experimento → reflexão**

A prática deve ser o ponto alto de cada aula.

Não queremos apresentar tecnologias de forma isolada.

Exemplo ruim:

> “Hoje vamos aprender Redis.”

Exemplo desejado:

> “Agora temos vários workers. Onde colocamos o estado compartilhado?”

Somente depois que o problema estiver claro, introduzir Redis.

O mesmo vale para:

* queues;
* workers;
* PostgreSQL;
* Docker;
* tracing;
* retry;
* circuit breaker;
* autoscaling;
* observability.

O aluno deve entender primeiro **por que** determinada tecnologia existe.

---

# 5. PRINCÍPIO PEDAGÓGICO

Sempre que possível, usar a sequência:

**necessidade → problema → tecnologia → implementação → experimento**

Exemplo:

1. Um incidente funciona corretamente.
2. Agora chegam 200 incidentes.
3. A arquitetura atual começa a falhar.
4. Surge a necessidade de fila e workers.
5. Implementamos fila + workers.
6. Realizamos teste.
7. Observamos a diferença.

Evitar apresentar tecnologias apenas porque fazem parte da stack.

---

# 6. O CASE LONGITUDINAL

Toda a disciplina utilizará UM ÚNICO SISTEMA que evolui aula após aula.

Nome do case:

# Enterprise Operations Control Tower

Empresa fictícia:

# NovaCore Industries

A NovaCore é uma empresa industrial B2B com aproximadamente:

* 4 fábricas;
* 3 centros de distribuição;
* dezenas de fornecedores;
* carteira de clientes enterprise;
* contratos com SLA;
* transportadoras terceirizadas;
* planejamento produtivo;
* estoque distribuído;
* pedidos de diferentes prioridades.

Não precisamos representar uma empresa gigantesca.

Os dados devem ser pequenos o suficiente para os alunos entenderem, mas ricos o suficiente para gerar interdependências.

---

# 7. PROBLEMA DE NEGÓCIO

Hoje a NovaCore reage a incidentes operacionais de forma fragmentada.

Exemplo:

Um fornecedor comunica atraso de uma matéria-prima crítica.

O processo atual pode ser:

1. comprador percebe a ocorrência;
2. informa planejamento;
3. planejamento identifica ordens afetadas;
4. produção verifica capacidade;
5. logística procura alternativas;
6. comercial identifica clientes afetados;
7. financeiro calcula impacto;
8. alguém consolida planilhas;
9. ocorre uma reunião;
10. finalmente é tomada uma decisão.

O maior problema não é falta de conhecimento.

O problema é:

# COORDENAÇÃO

---

# 8. SITUAÇÃO ANTES

Fluxo conceitual:

Event
→ Person notices
→ Email / Teams / spreadsheets
→ consultas a sistemas
→ reuniões
→ informações divergentes
→ nova análise
→ decisão
→ execução manual

Características:

* informação fragmentada;
* dependência de pessoas-chave;
* análise sequencial;
* alto tempo de resposta;
* difícil rastreabilidade;
* retrabalho;
* baixa capacidade de processar múltiplos incidentes;
* pouca memória operacional;
* alto custo de coordenação.

---

# 9. MÉTRICA DE NEGÓCIO PRINCIPAL

A métrica principal do case será:

# Time-to-Decision

Exemplo antes:

08:00 — incidente detectado
13:30 — informações consolidadas
15:00 — reunião
16:00 — decisão

Time-to-Decision:

~8 horas

Depois da força de trabalho agêntica:

08:00:00 — evento
08:00:03 — investigação iniciada
08:00:45 — dados coletados
08:01:10 — cenários calculados
08:01:30 — riscos analisados
08:01:45 — recomendação preparada
08:03:00 — aprovação humana

Objetivo:

reduzir horas para minutos.

Não tratar esses números como métricas reais de benchmark; são valores pedagógicos ilustrativos.

---

# 10. PROPOSTA DE VALOR

Definição:

> O Enterprise Operations Control Tower utiliza uma força de trabalho agêntica para transformar eventos operacionais em decisões coordenadas, contextualizadas e rastreáveis, reduzindo o tempo entre detecção, análise e ação.

Quatro dimensões principais:

## Velocidade

Event → Understanding → Decision → Action

## Qualidade

Mais perspectivas e variáveis analisadas simultaneamente.

## Escala

A mesma equipe humana consegue supervisionar muito mais eventos.

## Consistência

Critérios e políticas são aplicados de forma padronizada.

---

# 11. O MODELO “DEPOIS”

Arquitetura conceitual:

Event
→ Event Intake
→ Operations Supervisor
→ especialistas em paralelo
→ Shared State
→ Finance
→ Risk / Challenger
→ Decision
→ Recommendation
→ Human Approval
→ Action
→ Monitoring

Human Approval deve permanecer.

O objetivo do laboratório NÃO é promover autonomia irrestrita.

Mensagem:

> A força de trabalho agêntica não substitui a organização. Ela cria uma nova camada operacional entre dados, sistemas e pessoas.

---

# 12. AGENTES INICIAIS

O sistema terá inicialmente os seguintes agentes.

## Operations Supervisor

Responsabilidades:

* receber incidente;
* interpretar o problema;
* definir plano de investigação;
* escolher especialistas;
* coordenar execução;
* acompanhar estado;
* consolidar resultados;
* produzir material para decisão.

O Supervisor não precisa dominar todos os assuntos.

Ele precisa saber quem deve trabalhar em cada problema.

---

## Supply Agent

Responsabilidades:

* estoque;
* fornecedores;
* lead time;
* compras;
* materiais alternativos;
* disponibilidade.

Possíveis tools:

* `get_inventory()`
* `get_supplier()`
* `get_purchase_orders()`
* `get_alternative_suppliers()`

---

## Production Agent

Responsabilidades:

* capacidade;
* ordens;
* sequenciamento;
* dependências produtivas;
* replanejamento.

Possíveis tools:

* `get_production_orders()`
* `get_capacity()`
* `simulate_reschedule()`

---

## Logistics Agent

Responsabilidades:

* transportadoras;
* rotas;
* custos;
* prazos;
* alternativas de transporte.

Possíveis tools:

* `get_shipping_options()`
* `get_carriers()`
* `calculate_expedited_shipping()`

---

## Finance Agent

Responsabilidades:

* comparar impacto econômico;
* custo das alternativas;
* penalidades;
* margem;
* benefício econômico.

Possíveis tools:

* `calculate_penalty()`
* `calculate_margin_impact()`
* `calculate_scenario_cost()`

---

## Risk / Challenger Agent

Responsabilidade especial:

NÃO produzir simplesmente outra análise.

Seu papel é desafiar o plano.

Perguntas que deverá fazer:

* qual premissa pode estar errada?
* falta informação?
* há riscos não considerados?
* alguma conclusão não é suportada por dados?
* alguma política foi violada?
* há excesso de confiança?
* existe alternativa melhor?

Esse agente é importante pedagogicamente.

---

# 13. AGENTES FUTUROS OPCIONAIS

Podem ser introduzidos conforme a evolução:

* Customer Agent;
* Procurement Agent;
* Compliance Agent;
* Forecast Agent;
* Communication Agent;
* Execution Agent.

Mas sempre ensinar:

> Mais agentes não significa necessariamente uma arquitetura melhor.

Uma atividade futura poderá inclusive pedir que alunos reduzam o número de agentes mantendo a qualidade da decisão.

---

# 14. DIGITAL TWIN SIMPLIFICADO

Criar dados fictícios que representem a NovaCore.

Arquivos iniciais sugeridos:

`data/suppliers.csv`

Campos aproximados:

* supplier_id
* name
* material
* lead_time
* reliability_score
* unit_cost
* capacity
* region

---

`data/inventory.csv`

Campos:

* plant
* material
* quantity
* reserved_quantity
* safety_stock

---

`data/production_orders.csv`

Campos:

* order_id
* plant
* product
* quantity
* material
* production_date
* customer_order
* priority

---

`data/customer_orders.csv`

Campos:

* customer
* order
* product
* quantity
* delivery_date
* sla_penalty
* priority
* margin

---

`data/carriers.csv`

Campos:

* carrier
* route
* lead_time
* capacity
* cost
* reliability

---

`data/policies.json`

Exemplo conceitual:

```json
{
  "priority_customer_max_delay": 1,
  "max_expedited_freight": 50000,
  "manager_approval_threshold": 100000
}
```

Essas políticas ajudam a ensinar que:

> Nem toda decisão deve ser delegada a um LLM.

Código determinístico continua sendo essencial.

---

# 15. TOOLS COMO CAMADA DE CAPABILITY

Agentes não devem ler todos os CSVs diretamente.

Devemos abstrair o acesso aos dados através de tools.

Exemplo:

```python
inventory.get_stock(material, plant)

production.get_orders(material)

supplier.get_status(supplier_id)

logistics.get_routes(origin, destination)

finance.calculate_scenario(actions)
```

Isso simula uma realidade enterprise:

* ERP;
* WMS;
* CRM;
* TMS;
* APIs;
* sistemas legados.

Mensagem:

> O agente não “entra no SAP”. Ele consome uma capability controlada.

---

# 16. PRIMEIRO INCIDENTE

Arquivo:

`incidents/incident_001.json`

Situação:

> O fornecedor Alpha informou atraso de sete dias na entrega do material M42 para a planta São Paulo.

O dataset deve ser construído de forma que:

* três ordens dependam de M42;
* uma pertença a cliente estratégico;
* estoque local cubra apenas parte da demanda;
* exista outra planta com estoque;
* exista fornecedor alternativo;
* fornecedor alternativo tenha custo maior;
* exista frete expresso;
* cliente estratégico possua penalidade relevante.

Pergunta:

> Qual é o melhor plano operacional?

Não deve existir uma resposta trivial.

---

# 17. CENÁRIOS POSSÍVEIS

O sistema pode comparar alternativas como:

## A — esperar o fornecedor

Baixo custo incremental, grande atraso e penalidade.

## B — fornecedor alternativo

Maior custo de material, menor atraso.

## C — transferência entre plantas

Custo logístico e possível impacto em safety stock da planta origem.

## D — transferência + replanejamento

Custo intermediário, pouco ou nenhum atraso.

Os números devem ser fictícios, consistentes e deterministicamente calculáveis pelas tools.

---

# 18. OUTPUT ESTRUTURADO

Nunca depender apenas de prosa solta.

Usar Pydantic.

Exemplo conceitual:

```python
class Recommendation(BaseModel):
    incident_id: str
    severity: str
    recommended_action: str
    estimated_cost: float
    avoided_penalty: float
    customer_delay_days: int
    confidence: float
    risks: list[str]
    approval_required: bool
```

Mensagem pedagógica:

> LLMs podem ser probabilísticos. A arquitetura ao redor deles não precisa ser.

---

# 19. STACK TÉCNICA INICIAL

Stack aprovada para o laboratório:

## Linguagem

Python 3.12

## Dependency / project management

uv

## Agent orchestration

LangGraph

## LLM

OpenAI API inicialmente.

Manter abstração suficiente para permitir Azure OpenAI ou outro provider posteriormente sem reescrever o sistema.

Os modelos NÃO precisam rodar localmente.

## Validation / contracts

Pydantic

## API

FastAPI

## Queue / Cache / state operacional

Redis

## Async / distributed workers

Celery

## Durable storage

PostgreSQL

## Containers

Docker

## Local orchestration

Docker Compose

## Telemetry standard

OpenTelemetry

## Agent observability

Langfuse

## Load testing

k6

## Chaos / fault injection

Começar com fault simulator próprio e didático.

Toxiproxy poderá ser adicionado posteriormente se agregar valor.

## Production scaling concept

Kubernetes

Kubernetes deve ser majoritariamente conceitual/demonstrativo, não o laboratório principal.

---

# 20. AMBIENTE DO PROFESSOR

Professor utilizará:

MacBook Pro
Apple M3 Pro
36 GB RAM

Docker Desktop será o principal ambiente local.

O ambiente deve funcionar bem em Apple Silicon.

---

# 21. AMBIENTE DOS ALUNOS

Não assumir hardware potente.

Alunos poderão ter:

* macOS;
* Windows;
* eventualmente Linux;
* máquinas com menos memória.

O README deverá indicar:

## Full Lab

* Docker Desktop
* API
* Redis
* PostgreSQL
* workers
* observability

## Lite Lab

Se necessário:

* menos workers;
* menor quantidade de serviços;
* observabilidade cloud;
* configuração de memória reduzida.

Evitar dependências específicas de arquitetura x86 quando houver equivalente multiarch.

---

# 22. ESTRUTURA DE ALTO NÍVEL DO REPOSITÓRIO

Estrutura esperada aproximadamente:

```text
agentic-operations-control-tower/
│
├── README.md
├── AGENTS.md
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── compose.yaml
│
├── docs/
│   ├── architecture/
│   ├── case/
│   └── course/
│       └── PROJECT_CONTEXT.md
│
├── data/
│   ├── suppliers.csv
│   ├── inventory.csv
│   ├── production_orders.csv
│   ├── customer_orders.csv
│   ├── carriers.csv
│   └── policies.json
│
├── incidents/
│   ├── incident_001.json
│   └── ...
│
├── src/
│   └── control_tower/
│       ├── main.py
│       ├── agents/
│       ├── graph/
│       ├── tools/
│       ├── models/
│       ├── api/
│       ├── workers/
│       ├── persistence/
│       ├── telemetry/
│       └── config/
│
├── labs/
│   ├── 01_orchestration/
│   ├── 02_distributed_execution/
│   ├── 03_deployment/
│   └── 04_observability_chaos/
│
├── tests/
│
├── docker/
│
└── scripts/
```

Pode melhorar essa estrutura se houver justificativa clara, mas preserve a progressão pedagógica.

---

# 23. PRINCÍPIO DO REPOSITÓRIO

Existe UM ÚNICO SISTEMA.

Não criar quatro projetos independentes.

O mesmo sistema evolui durante as aulas.

Isso é essencial.

---

# 24. CHECKPOINTS DA DISCIPLINA

Devemos manter estes checkpoints Git:

* `lesson-01-start`

* `lesson-01-complete`

* `lesson-02-start`

* `lesson-02-complete`

* `lesson-03-start`

* `lesson-03-complete`

* `lesson-04-start`

* `lesson-04-complete`

Cada checkpoint deve representar um estado executável e pedagogicamente coerente.

Quando possível, usar Git tags para esses checkpoints.

O README deve ensinar o aluno a fazer:

```bash
git checkout lesson-02-start
```

e comparar:

```bash
git diff lesson-02-start..lesson-02-complete
```

---

# 25. AULA 1 — ARCHITECTURE & ORCHESTRATION

Pergunta:

> Como estruturamos um sistema multiagente para resolver um problema real?

Objetivos:

* conhecer o case;
* compreender a proposta de valor;
* entender o “antes e depois”;
* compreender o problema operacional;
* decompor responsabilidades;
* implementar estado;
* tools;
* especialistas;
* supervisor;
* execução paralela;
* output estruturado;
* challenger;
* human approval.

Não gastar muito tempo ensinando agente básico.

Foco:

**design de sistema multiagente.**

Estado inicial:

`lesson-01-start`

Deve conter:

* projeto configurado;
* dados;
* models;
* incidente;
* algumas tools;
* scaffolding;
* TODOs didáticos.

Estado final:

`lesson-01-complete`

Deve executar o `INCIDENT-001` de ponta a ponta.

---

# 26. AULA 2 — DISTRIBUTED EXECUTION

Provocação:

> Funcionou para um incidente. O que acontece quando chegam 100 ou 500?

Introduzir progressivamente:

* sync x async;
* jobs;
* queues;
* producer / consumer;
* workers;
* parallelism;
* concurrency;
* shared state;
* Redis;
* Celery;
* checkpoint;
* resume;
* idempotency;
* timeout;
* retry;
* dead-letter concepts;
* rate limits;
* backpressure;
* eventual consistency.

Estado inicial:

`lesson-02-start`

Estado final:

`lesson-02-complete`

O sistema deve conseguir processar múltiplos incidentes de maneira assíncrona/distribuída.

---

# 27. AULA 3 — DEPLOYMENT & RUNTIME

Provocação:

> Agora isso precisa ser entregue e operado como uma aplicação real.

Introduzir:

* FastAPI;
* endpoints;
* configuration;
* environment variables;
* secrets;
* Dockerfile;
* images;
* containers;
* Docker Compose;
* Redis;
* PostgreSQL;
* workers;
* health checks;
* liveness;
* readiness;
* graceful shutdown;
* stateless vs stateful;
* replicas;
* deployment;
* rollback como conceito.

Kubernetes deve aparecer como evolução natural.

Não fazer da aula um curso de administração Kubernetes.

Estado inicial:

`lesson-03-start`

Estado final:

`lesson-03-complete`

O comando ideal deverá ser próximo de:

```bash
docker compose up
```

e levantar o ambiente completo.

---

# 28. AULA 4 — OBSERVABILITY, RESILIENCE, SCALE & FINOPS

Pergunta:

> Como sabemos se esse sistema realmente funciona bem quando está em produção?

Introduzir:

## Observability

* logs estruturados;
* metrics;
* traces;
* trace_id;
* incident_id;
* execution_id;
* spans;
* distributed tracing;
* OpenTelemetry;
* Langfuse;
* model calls;
* tool calls;
* handoffs;
* latency;
* errors;
* tokens;
* cost.

## Resilience

* timeout;
* retry;
* exponential backoff;
* circuit breaker;
* fallback;
* model fallback;
* tool fallback;
* execution limits;
* partial results;
* graceful degradation.

## Scale

* horizontal scaling;
* workers;
* queue depth;
* throughput;
* bottlenecks;
* quotas;
* rate limits;
* caching;
* model capacity;
* SLO / SLA.

## Agent FinOps

* cost per incident;
* cost per agent;
* cost per model;
* token budget;
* model routing;
* cheaper model selection;
* context reduction;
* cache;
* deterministic code instead of LLM where appropriate;
* tradeoff quality x latency x cost.

Estado inicial:

`lesson-04-start`

Estado final:

`lesson-04-complete`

---

# 29. CHAOS LAB

A parte final da Aula 4 deve ser memorável.

Nome:

# Multi-Agent Chaos Day

O professor deverá conseguir injetar falhas controladas.

Exemplos:

## Latency

Logistics API demora 10 ou 30 segundos.

## Failure rate

Finance API falha em 40% das chamadas.

## Invalid output

Agente retorna valor absurdo ou schema inválido.

## Infinite / excessive loop

Supervisor excede número normal de iterações.

## Worker failure

Container de worker cai.

## LLM failure

Rate limit ou erro simulado.

## Load spike

Chegam 100, 500 ou 1.000 incidentes.

## Cost explosion

Um agente utiliza modelo caro e contexto excessivo.

Os alunos deverão observar, diagnosticar e melhorar o sistema.

---

# 30. FAULT SIMULATOR

Preferimos inicialmente um componente próprio simples e legível.

Exemplo conceitual:

```http
POST /chaos/logistics

{
  "latency_ms": 10000,
  "failure_rate": 0.3
}
```

Isso é mais didático que começar imediatamente com tooling complexo.

Toxiproxy poderá ser incorporado posteriormente.

---

# 31. OBSERVABILITY

A arquitetura deve usar OpenTelemetry como padrão de instrumentação.

Princípio:

> Observabilidade deve ser uma propriedade do sistema, não uma dependência de uma ferramenta específica.

Langfuse será a primeira interface para visualização de:

* traces;
* latency;
* generations;
* tools;
* tokens;
* costs;
* failures;
* datasets/evals futuramente.

Não acoplar toda a aplicação a APIs proprietárias desnecessariamente.

---

# 32. DASHBOARD CONCEITUAL

Desejamos chegar a métricas como:

* incidents open;
* incidents resolved;
* failed executions;
* average time-to-decision;
* cost per incident;
* token cost;
* agent failure rate;
* queue depth;
* throughput;
* p95 latency.

Trace desejável:

```text
INC-847
│
├── Supervisor
├── Supply
│   └── Inventory Tool
├── Production
├── Logistics
│   └── Carrier Tool
├── Finance
└── Risk
```

Idealmente mostrar duração e custo por span/agente.

---

# 33. LOAD TEST

Usar k6.

A Aula 4 deve poder aumentar carga progressivamente:

* 1 usuário;
* 10;
* 50;
* 100;
* 500.

Observar:

* throughput;
* latency;
* queue;
* workers;
* errors;
* tokens;
* cost.

---

# 34. CINCO PERGUNTAS CENTRAIS DE ENGENHARIA

Toda a disciplina deverá retornar a estas perguntas:

## 1. Who decides?

Quem decide qual agente deve executar?

## 2. Where is the state?

Onde está o estado do sistema?

## 3. What happens when it fails?

O que acontece quando alguma coisa quebra?

## 4. Can I observe it?

Conseguimos explicar o que aconteceu?

## 5. What does it cost?

Quanto custa realizar a tarefa?

Adicionar uma sexta provocação:

## 6. Should this even be an agent?

Talvez aquilo devesse ser código determinístico.

Essas perguntas devem aparecer no README/material da disciplina.

---

# 35. BEFORE / AFTER

O aluno precisa compreender explicitamente a transformação.

## BEFORE

Event
→ people
→ emails
→ spreadsheets
→ meetings
→ analysis
→ decision

Características:

* hours;
* limited scale;
* low traceability.

## AFTER

Event
→ Agentic Workforce
→ Parallel Investigation
→ Scenario Analysis
→ Risk Review
→ Recommendation
→ Human Decision

Características:

* minutes;
* higher scale;
* high traceability.

Não vender autonomia total.

Vender:

> capacidade operacional amplificada.

---

# 36. FRAMEWORK GENERALIZÁVEL

O case deve ensinar um padrão aplicável além de operações industriais:

Event
→ Understand
→ Investigate
→ Specialists
→ Simulate
→ Challenge
→ Decide
→ Approve
→ Act
→ Observe

Esse mesmo padrão deve poder ser adaptado para:

* crédito;
* incidentes de TI;
* supply chain;
* logística;
* saúde;
* atendimento B2B;
* operações;
* compliance;
* manutenção;
* gestão de crises.

---

# 37. QUALIDADE DO README

O README é parte do produto educacional.

Ele deve permitir que um aluno que perdeu parte da aula consiga recuperar o ambiente.

Incluir obrigatoriamente:

* objetivo do projeto;
* proposta de valor do case;
* arquitetura;
* pré-requisitos;
* instalação;
* configuração;
* `.env`;
* comandos;
* troubleshooting;
* Docker Desktop;
* como iniciar;
* como parar;
* como limpar;
* como executar testes;
* como acessar API;
* como observar logs;
* como mudar de checkpoint;
* diferença entre checkpoints;
* como executar incidentes;
* como rodar load test;
* como habilitar observabilidade;
* como simular falhas;
* recursos mínimos;
* notas específicas para Apple Silicon quando necessário;
* notas Windows quando necessário.

Comandos devem ser copy/paste friendly.

---

# 38. MODE MOCK

Sempre que razoável, permitir execução em modo mock sem necessidade de consumir API paga.

Exemplo:

```env
LLM_MODE=mock
```

E:

```env
LLM_MODE=openai
OPENAI_API_KEY=...
```

O modo mock deve preservar a arquitetura e produzir resultados determinísticos úteis para aprendizado.

Isso permitirá:

* onboarding;
* testes;
* CI;
* laboratório sem custos;
* debugging.

Depois os alunos poderão ativar LLM real.

---

# 39. TESTES

Não criar apenas uma demonstração.

Adicionar testes para:

* tools;
* schemas;
* deterministic calculations;
* policies;
* incident loading;
* routing;
* invalid output;
* retries;
* state transitions;
* API;
* basic integration flow.

Manter os testes legíveis para alunos.

---

# 40. PRINCÍPIOS DE ENGENHARIA

Priorizar:

* clarity over cleverness;
* explicit architecture;
* typed contracts;
* deterministic business calculations;
* small cohesive modules;
* reproducibility;
* observability;
* failure handling;
* idempotency;
* portability;
* teaching value.

Evitar:

* abstrações excessivas;
* meta-frameworks desnecessários;
* magia;
* dependências sem valor didático;
* código excessivamente sofisticado para o objetivo.

---

# 41. SEGURANÇA

Nunca commitar:

* API keys;
* tokens;
* credentials;
* secrets.

Usar:

`.env.example`

e `.gitignore`.

Se algum segredo for encontrado, interromper e informar antes de publicar.

---

# 42. GIT

O repositório deve manter histórico claro.

Preferir commits pequenos e semanticamente significativos.

Não misturar várias aulas em um único commit gigantesco.

Exemplos:

`feat: add NovaCore digital twin`

`feat: add deterministic inventory tools`

`feat: implement supply agent`

`feat: implement lesson 01 orchestration graph`

`feat: add distributed task queue`

`feat: containerize control tower`

`feat: add OpenTelemetry tracing`

`feat: add chaos fault simulator`

---

# 43. CHECKPOINTS

Nunca mover silenciosamente um checkpoint já aprovado pelo professor.

Antes de criar ou atualizar os tags:

* executar testes;
* executar smoke test;
* validar README;
* confirmar que o estado corresponde à aula.

---

# 44. O QUE NÃO FAZER AGORA

Não implementar tudo de uma vez.

Não construir todas as quatro aulas imediatamente.

Não criar Kubernetes completo agora.

Não self-hostar todos os componentes de observabilidade imediatamente.

Não criar UI sofisticada.

Não adicionar centenas de incidentes.

Não introduzir Kafka sem necessidade.

Não introduzir cloud deployment agora.

Não introduzir RAG.

Não adicionar recursos apenas por parecerem modernos.

---

# 45. ORDEM DE IMPLEMENTAÇÃO

## Fase atual

Construir somente a base do projeto e a experiência da Aula 1.

Primeiro objetivo:

# `lesson-01-start`

Esse checkpoint deve proporcionar ao aluno:

1. clonar;
2. instalar;
3. verificar ambiente;
4. compreender o case;
5. explorar dados;
6. executar algumas tools;
7. visualizar o INCIDENT-001;
8. começar a construir a arquitetura multiagente durante a aula.

Não entregar toda a solução no checkpoint start.

---

# 46. DEPOIS

Após validação do professor:

implementar:

# `lesson-01-complete`

Esse checkpoint deve conter:

* orquestração multiagente funcionando;
* INCIDENT-001 resolvido;
* execução visível;
* structured outputs;
* specialist agents;
* supervisor;
* challenger/risk;
* human approval indication;
* testes básicos;
* documentação.

Somente depois da revisão do professor avançaremos para Aula 2.

---

# 47. PRIMEIRA TAREFA

Agora faça o seguinte:

1. Inspecione completamente o repositório existente.
2. Não apague decisões anteriores sem necessidade.
3. Crie `docs/course/PROJECT_CONTEXT.md` contendo este contexto de forma organizada.
4. Crie um `AGENTS.md` na raiz com instruções de engenharia para futuros agentes/Codex.
5. Proponha a estrutura final do repositório.
6. Crie ou refine o `README.md`.
7. Implemente somente os artefatos necessários para `lesson-01-start`.
8. Crie datasets fictícios pequenos, porém coerentes.
9. Crie `INCIDENT-001`.
10. Crie Pydantic models básicos.
11. Crie tools determinísticas básicas.
12. Adicione testes das tools.
13. Adicione `.env.example`.
14. Garanta execução em `LLM_MODE=mock`.
15. Garanta compatibilidade com macOS Apple Silicon.
16. Execute testes.
17. Execute smoke test.
18. Revise a experiência de um aluno seguindo apenas o README.
19. Faça commit das alterações.
20. Crie o tag `lesson-01-start` somente quando o estado estiver validado.

Antes de implementar `lesson-01-complete`, pare e apresente:

* resumo da arquitetura;
* árvore de arquivos;
* comandos de execução;
* resultados dos testes;
* decisões técnicas;
* tradeoffs;
* perguntas ou riscos relevantes.

Não avance para Aula 2.

---

# 48. CRITÉRIO DE SUCESSO DO PRIMEIRO CHECKPOINT

Um aluno deve ser capaz de fazer algo equivalente a:

```bash
git clone https://github.com/leandrol3/agentic-operations-control-tower.git

cd agentic-operations-control-tower

git checkout lesson-01-start

uv sync

cp .env.example .env

uv run pytest
```

e depois executar o primeiro laboratório seguindo apenas o README.

O processo deve ser simples, reproduzível e didático.

---

# 49. REGRA PERMANENTE

Sempre que houver conflito entre:

* usar tecnologia sofisticada;
* e tornar o conceito compreensível;

prefira tornar o conceito compreensível.

Mas mantenha padrões reais de engenharia.

Este é um laboratório de MBA em AI Engineering, não um tutorial infantil e não um sistema enterprise de produção real.

O equilíbrio desejado é:

**realistic enough to teach production engineering
simple enough to understand completely.**

Comece agora pela inspeção do repositório e pelo planejamento/implementação do `lesson-01-start`.
