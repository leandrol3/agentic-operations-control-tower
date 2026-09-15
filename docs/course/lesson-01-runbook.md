# Aula 1 — Runbook do professor

**Duração:** 4 horas de uma disciplina de 16 horas. Professor implementa/demonstra; alunos observam
e discutem. Não reservar tempo para alunos digitarem código, instalarem dependências ou completarem TODOs.

**Estado deste documento:** Demos 1–8 executáveis no candidato local `lesson-01-complete`,
branch `codex/lesson-01-complete`, em modo mock. O start revisado aprovado está em `171c324`.
A tag `lesson-01-start` permanece intacta; a tag complete ainda não existe.

## Preparação antes da aula (fora das 4 horas)

- Use o checkout candidato na branch `codex/lesson-01-complete`; não faça checkout da tag start para estas demos.
- Rode `uv sync --locked`, configure `.env` com `LLM_MODE=mock` e execute os comandos abaixo.
- Deixe abertos este runbook, o guia de observação, o case, main.py, models.py e tools.py.
- Instalação, parsing, fixtures e boilerplate já vêm prontos. Concentre a comparação entre os estados em estado,
  responsabilidades, arestas, junção de resultados e limite de aprovação.
- Para reproduzir depois, alunos seguem README e guia; não precisam reconstruir os agentes.

```bash
uv run pytest -q
uv run control-tower doctor
uv run control-tower incident
uv run control-tower tools
uv run control-tower smoke
```

Antes de mudar de checkpoint, confira `git status --short` e preserve alterações em uma branch.
Não mova tags aprovadas. Use `git diff 171c324..HEAD -- src/control_tower` para comparar start revisado e candidato commitado.
Use `git diff lesson-01-start..HEAD` para incluir também os ajustes pedagógicos aprovados.
Para revisão antes de commit, `git diff 171c324 -- src/control_tower` inclui edições rastreadas locais.
A comparação entre as duas tags só estará disponível após aprovação e criação de complete.

## Agenda de 240 minutos

| Janela | Atividade | Minutos |
|---|---|---:|
| 00:00–00:15 | Abertura: coordenação e Time-to-Decision | 15 |
| 00:15–00:30 | Demo 1 — base pronta | 15 |
| 00:30–00:50 | Demo 2 — evento, relação e tempo | 20 |
| 00:50–01:15 | Demo 3 — restrições e capabilities | 25 |
| 01:15–01:30 | Demo 4 — smoke e falha de fixture | 15 |
| 01:30–01:45 | Intervalo | 15 |
| 01:45–02:15 | Demo 5 — estado e especialistas | 30 |
| 02:15–02:45 | Demo 6 — Supervisor, LangGraph e paralelismo | 30 |
| 02:45–03:15 | Demo 7 — consolidação, Finance e Challenger | 30 |
| 03:15–03:40 | Demo 8 — recomendação e aprovação | 25 |
| 03:40–04:00 | Síntese, comparação de estados e perguntas | 20 |

Os tempos incluem explicação, observação e discussão. Não reescrever boilerplate ao vivo;
mostrar pequenas alterações conceituais via Git e executar o candidato já preparado.

## Demo 1 — A base está pronta para investigar

- **Objetivo:** abrir a aula com execução reproduzível, sem escrever infraestrutura ao vivo.
- **Conceito:** ambiente pronto é diferente de decisão produzida.
- **Tempo estimado:** 15 min.
- **Arquivos envolvidos:** README.md, pyproject.toml, .env.example, src/control_tower/main.py.
- **Comandos:**

  ```bash
  uv run control-tower doctor
  ```

- **Alteração relevante a demonstrar:** nenhuma edição; mostrar o caminho CLI → Tools → contratos/dados.
  O boilerplate já está presente; apontar onde a orquestração do complete se conecta.
- **Resultado esperado:** `status: ok`, `mode: mock`, `related_orders: 3`,
  `impact_status: not_assessed`, `orchestration: available_via_run`.
- **Pergunta:** “O que ainda falta para essa aplicação poder recomendar uma decisão?”
- **Mensagem-chave:** base determinística reduz ruído para discutir coordenação.
- **Fallback:** mostrar o output esperado acima e o diagrama do guia; se uv falhar mas o ambiente já
  estiver instalado, usar `.venv/bin/python -m control_tower.main doctor` no Mac. Não reinstalar em aula.

## Demo 2 — O evento não confirma impacto no cliente

- **Objetivo:** impedir que relação entre dados seja interpretada como conclusão operacional.
- **Conceito:** `related_orders` versus impacto confirmado; calendário explícito.
- **Tempo estimado:** 20 min.
- **Arquivos envolvidos:** incidents/incident_001.json, data/production_orders.csv,
  data/customer_orders.csv, docs/case/NOVACORE.md, src/control_tower/tools.py.
- **Comandos:**

  ```bash
  uv run control-tower incident
  uv run control-tower tools
  ```

- **Alteração relevante a demonstrar:** mostrar a mudança de `affected_orders` para `related_orders`
  e a inclusão de `impact_status`; apontar que get_orders só filtra material/planta.
- **Resultado esperado:** evento em 01/10/2026, atraso de Alpha de 7 dias e três ordens relacionadas.
  Na linha do tempo: Alpha chega em 08/10; Beta comprado em 01/10 chega em 03/10.
  Produzir em 02/10 permite entregar em 03/10. Nenhum atraso por cliente está calculado.
- **Pergunta:** “Se SP dispõe de 300 unidades, Atlas necessariamente vai atrasar?”
- **Mensagem-chave:** um vínculo inicia investigação; confirmar impacto exige alocação e cronograma.
- **Fallback:** abrir os JSON/CSVs no editor e desenhar as três datas usando a convenção do case.

## Demo 3 — Tools expõem o trade-off

- **Objetivo:** comparar restrições sem antecipar um plano vencedor.
- **Conceito:** capabilities, disponibilidade, safety stock e cálculo determinístico.
- **Tempo estimado:** 25 min.
- **Arquivos envolvidos:** src/control_tower/tools.py, data/inventory.csv, data/suppliers.csv,
  data/carriers.csv, data/policies.json.
- **Comandos:**

  ```bash
  uv run control-tower tools
  uv run control-tower smoke
  ```

- **Alteração relevante a demonstrar:** nenhuma implementação; destacar a fronteira que os
  especialistas consomem. Não reescrever leitores de CSV nem fórmulas durante a aula.
- **Resultado esperado:** demanda 750, disponível SP 300, déficit 450; Campinas tem 500 disponíveis,
  mas apenas 300 preservam safety stock. Beta custa 145 por unidade e oferece 450; expresso custa
  18.000 por viagem. Multa de 140.000 é hipotética para sete dias de atraso de CO-001.
- **Pergunta:** “Transferir 450 resolve a falta de material: qual risco essa frase esconde?”
- **Mensagem-chave:** melhor plano depende de critérios explícitos, não só de disponibilidade física.
- **Fallback:** fazer no quadro 750 − 300 = 450 e 500 − 450 = 50 versus piso 200;
  usar valores do case. Não apresentar a multa hipotética como custo confirmado do incidente.

## Demo 4 — Não mostrar verde com fixture incompleto

- **Objetivo:** comprovar que a demonstração detecta perda de dados necessários.
- **Conceito:** smoke semântico além de carregamento e validação de schema.
- **Tempo estimado:** 15 min.
- **Arquivos envolvidos:** src/control_tower/smoke.py, src/control_tower/tools.py, tests/test_lab.py.
- **Comandos:**

  ```bash
  uv run control-tower smoke
  uv run pytest -q tests/test_lab.py -k incomplete
  ```

- **Alteração relevante a demonstrar:** abrir os testes que removem Beta, estoque de Campinas,
  rota expressa ou uma ordem em cópias temporárias; destacar a verificação correspondente no smoke.
  O fixture oficial permanece intacto. Mostrar também rejeição de tabela vazia/cabeçalho incompleto.
- **Resultado esperado:** fixture oficial passa 12 checks. Testes passam porque demonstram que cada
  fixture danificado retorna erro (saída 2, sem JSON de sucesso). Doctor pode aceitar um subconjunto
  válido; smoke exige a configuração didática oficial.
- **Pergunta:** “Uma lista vazia de alternativas significa ausência real ou fixture quebrado?”
- **Mensagem-chave:** prontidão para esta demo precisa das evidências que sustentam a discussão.
- **Fallback:** ler os casos de teste e o erro esperado `Smoke falhou`/`Fixture incompleto` no editor.
  Não gastar a aula depurando ambiente; registrar o problema para depois.

## Demo 5 — Estado compartilhado e especialistas

- **Objetivo:** tornar visível quem produz e quem consome cada evidência.
- **Conceito:** shared state e specialist agents.
- **Tempo estimado:** 30 min.
- **Arquivos envolvidos:** src/control_tower/graph/state.py, agents/specialists.py, tools.py.
- **Comandos:**

  ```bash
  uv run control-tower run INCIDENT-001
  uv run control-tower run INCIDENT-001 --json
  git diff 171c324..HEAD -- src/control_tower/graph/state.py src/control_tower/agents/specialists.py
  ```

- **Alteração relevante:** Supply, Production e Logistics recebem o mesmo incidente e escrevem
  somente seu canal no estado. Pydantic valida evidência ou erro; não misturar dados em um texto global.
- **Resultado esperado:** Supply mostra 300 locais/500 Campinas; Production retorna três ordens e
  demanda 750; Logistics mostra rotas de 3 e 1 dia. No JSON, `supply`, `production` e `logistics`
  contêm `data` e `error: null`; `investigation` contém a junção validada.
- **Pergunta:** “Se dois especialistas escrevessem no mesmo campo, quem prevaleceria?”
- **Mensagem-chave:** estado compartilhado tem responsabilidade de escrita explícita.
- **Fallback:** abrir docs/course/examples/incident-001-mock.json e percorrer os três canais;
  marcar como resultado gravado. Não atribuir raciocínio de LLM às funções mock.

## Demo 6 — Supervisor, LangGraph e investigação paralela

- **Objetivo:** revelar coordenação, independência e barreira de sincronização.
- **Conceito:** Supervisor, LangGraph, parallel execution e join.
- **Tempo estimado:** 30 min.
- **Arquivos envolvidos:** agents/supervisor.py, graph/workflow.py, tests/test_workflow.py.
- **Comandos:**

  ```bash
  uv run control-tower graph
  uv run control-tower run INCIDENT-001 --demo-delay-ms 500
  uv run control-tower run INCIDENT-001 --sequential --demo-delay-ms 500
  uv run pytest -q tests/test_workflow.py -k parallel_branches
  ```

- **Alteração relevante:** mostrar fan-out após Supervisor e
  `add_edge(list(SPECIALISTS), 'consolidation')`. O modo sequencial muda apenas as arestas.
- **Resultado esperado:** no paralelo, três inícios antes dos finais graças à espera didática;
  consolidação inicia após todos terminarem. No sequencial, cada início segue o final anterior.
  Ambas execuções produzem a mesma recomendação. A espera de 500 ms é artificial e explicitamente
  rotulada; os tempos observados não são benchmark de LLM ou promessa de aceleração.
- **Pergunta:** “Finance pode começar se Logistics não respondeu?”
- **Mensagem-chave:** paralelismo exige independência e um ponto explícito de junção.
- **Fallback:** abrir docs/architecture/lesson-01-graph.mmd e o teste com Barrier, que comprova
  sobreposição dos três ramos sem comparar tempos frágeis. Mostrar o trace gravado como exemplo.

## Demo 7 — Consolidação, Finance e Challenger

- **Objetivo:** distinguir evidências, custo de cenário e crítica do plano.
- **Conceito:** consolidation, Finance e Challenger com funções distintas.
- **Tempo estimado:** 30 min.
- **Arquivos envolvidos:** scenarios.py, agents/finance.py, agents/challenger.py,
  data/policies.json, docs/case/NOVACORE.md.
- **Comandos:**

  ```bash
  uv run control-tower run INCIDENT-001
  uv run control-tower run INCIDENT-001 --fail-specialist logistics
  uv run pytest -q tests/test_workflow.py -k challenger
  ```

- **Alteração relevante:** consolidar antes de simular alocação/datas/custos; Finance propõe menor
  custo e Challenger revisa consistência, políticas, premissas e informação insuficiente.
- **Resultado esperado normal:** A=23.500; B=20.250; C=18.000; D=12.500 BRL de custo incremental.
  D preserva Campinas e aceita atraso de 3 dias em CO-003; B evita todos os atrasos por custo maior.
  Challenger bloqueia C (piso rompido em 150 unidades) e pede confirmação de capacidades/prazos.
- **Resultado esperado com falha:** saída 1, Logistics com erro, Supply/Production preservados;
  consolidação bloqueia; Finance, Challenger e Recommendation não executam. É demonstração de
  dependência/resultado ausente, sem retry, circuit breaker ou mecanismo de caos da Aula 4.
- **Pergunta:** “O plano é melhor ou apenas deixou um custo/risco de fora?”
- **Mensagem-chave:** cálculos são determinísticos sob premissas; Challenger expõe os limites.
- **Fallback:** abrir examples/incident-001-failure.txt e a tabela A–D do case; não afirmar que houve
  execução ao vivo. Mostrar que a multa evitada (16.000) difere da economia total (11.000).

## Demo 8 — Recomendação estruturada e aprovação humana

- **Objetivo:** separar saída válida de decisão autorizada.
- **Conceito:** structured recommendation e human approval.
- **Tempo estimado:** 25 min.
- **Arquivos envolvidos:** models.py (Recommendation), graph/state.py (Approval),
  graph/workflow.py (recommendation/human_approval), tests/test_workflow.py.
- **Comandos:**

  ```bash
  uv run control-tower run INCIDENT-001 --json
  uv run pytest -q tests/test_workflow.py -k approval
  uv run pytest -q tests/test_lab.py -k invalid_recommendation
  ```

- **Alteração relevante:** conectar resultado a Recommendation existente e terminar em
  `awaiting_approval`. O nó human_approval cria uma solicitação pendente; não aprova automaticamente.
- **Resultado esperado:** cenário D, `estimated_cost_brl: "12500.00"`,
  `avoided_penalty_brl: "16000.00"`, `customer_delay_days: 3`, `approval_required: true`;
  `approval.status: pending`, `actions_executed: false`, responsável `operations_manager`.
  Confiança 0.65 é marcador didático, não probabilidade calibrada. Dados do JSON são determinísticos.
- **Pergunta:** “Passar no Pydantic significa que o plano está correto e autorizado?”
- **Mensagem-chave:** estrutura, qualidade e autorização são responsabilidades distintas.
- **Fallback:** abrir examples/incident-001-mock.json e os testes. Esta aula termina na solicitação:
  não há comando de aprovar, persistência/retomada, compra, transporte ou transferência automática.

## Encerramento — 20 minutos

Retomar quem decide, onde está o estado, como falha, como observar, custo e quando usar código
em vez de agente. Comparar `git diff 171c324..HEAD -- src/control_tower` e apontar capabilities preservadas.
Alunos reproduzem com o guia; não há tarefa de programação. O workflow termina antes da decisão humana:
a duração da CLI não mede Time-to-Decision completo. A aprovação do candidato e criação da tag
lesson-01-complete continuam pendentes da revisão do professor.
