# Aula 1 — Runbook do professor

**Duração:** 4 horas de uma disciplina de 16 horas. Professor implementa/demonstra; alunos observam
e discutem. Não reservar tempo para alunos digitarem código, instalarem dependências ou completarem TODOs.

**Estado deste documento:** demos 1–4 executáveis no start revisado. Demos 5–8 são o roteiro conceitual
da progressão a preparar somente após aprovação de `lesson-01-complete`; não há implementação nem
comando de execução de grafo nesta entrega. Não apresentar esse roteiro como aula completa já executável.

## Preparação antes da aula (fora das 4 horas)

- Use o checkout revisado na branch `codex/lesson-01-start-guided-demo`; a tag publicada ainda é a anterior.
- Rode `uv sync --locked`, configure `.env` com `LLM_MODE=mock` e execute os comandos abaixo.
- Deixe abertos este runbook, o guia de observação, o case, main.py, models.py e tools.py.
- Instalação, parsing, fixtures e boilerplate já vêm prontos. Concentre futuras edições em estado,
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
Não mova tags aprovadas. Na revisão local, `git diff lesson-01-start -- src/control_tower` compara
arquivos rastreados; abra os arquivos novos diretamente. Após publicação dos checkpoints, compare
`git diff lesson-01-start..lesson-01-complete -- src/control_tower` (ainda indisponível).

## Agenda de 240 minutos

| Janela | Atividade | Minutos |
|---|---|---:|
| 00:00–00:15 | Abertura: coordenação e Time-to-Decision | 15 |
| 00:15–00:30 | Demo 1 — base pronta | 15 |
| 00:30–00:50 | Demo 2 — evento, relação e tempo | 20 |
| 00:50–01:15 | Demo 3 — restrições e capabilities | 25 |
| 01:15–01:30 | Demo 4 — smoke e falha de fixture | 15 |
| 01:30–01:45 | Intervalo | 15 |
| 01:45–02:15 | Demo 5 — estado e especialistas (planejada) | 30 |
| 02:15–02:45 | Demo 6 — Supervisor, LangGraph e paralelismo (planejada) | 30 |
| 02:45–03:15 | Demo 7 — consolidação, Finance e Challenger (planejada) | 30 |
| 03:15–03:40 | Demo 8 — recomendação e aprovação (planejada) | 25 |
| 03:40–04:00 | Síntese, comparação de estados e perguntas | 20 |

Os tempos incluem explicação, observação e discussão. Na revisão atual, use as demos planejadas
apenas para validar a sequência conceitual; a segunda metade depende da entrega complete aprovada.

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
  O boilerplate já está presente; apontar onde a futura orquestração será conectada.
- **Resultado esperado:** `status: ok`, `mode: mock`, `related_orders: 3`,
  `impact_status: not_assessed`, `orchestration: TODO`.
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

- **Alteração relevante a demonstrar:** nenhuma implementação; destacar a fronteira que os futuros
  especialistas consumirão. Não reescrever leitores de CSV nem fórmulas durante a aula.
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

## Demo 5 — Estado compartilhado e especialistas (planejada)

- **Objetivo:** tornar visível quem produz e quem consome cada evidência.
- **Conceito:** shared state e specialist agents.
- **Tempo estimado:** 30 min.
- **Arquivos envolvidos:** src/control_tower/models.py, tools.py, agents/ e graph/ (implementação futura).
- **Comandos disponíveis para preparar a discussão:**

  ```bash
  uv run control-tower tools
  ```

  Comando de execução dos especialistas: pendente da implementação/revisão de complete.
- **Alteração relevante a demonstrar depois:** professor acrescenta estado e saídas de Supply,
  Production e Logistics, reutilizando as capabilities prontas; mostrar só o contrato e a escrita no estado.
- **Resultado esperado futuro:** evidências separadas por especialista, com campos e responsabilidades
  claros. Neste start o comando mostra apenas dados das tools, não agentes executados.
- **Pergunta:** “Se dois especialistas escrevem no mesmo campo, qual resultado prevalece?”
- **Mensagem-chave:** estado compartilhado precisa de regras de escrita e consolidação.
- **Fallback:** desenhar o estado no quadro com três áreas, usando os dados reais da demo 3.

## Demo 6 — Supervisor, LangGraph e investigação paralela (planejada)

- **Objetivo:** revelar as decisões de coordenação e dependência.
- **Conceito:** Supervisor, LangGraph, parallel execution e junção.
- **Tempo estimado:** 30 min.
- **Arquivos envolvidos:** src/control_tower/graph/ e agents/ (futuros nós/arestas).
- **Comandos:** nesta revisão, apenas `git status --short` para situar o checkpoint;
  execução do grafo e comparação start..complete ficam pendentes até existir complete.
- **Alteração relevante a demonstrar depois:** professor conecta Supervisor ao estado e aos ramos
  independentes, mostra passagem sequencial → paralela e a barreira anterior à consolidação.
- **Resultado esperado futuro:** três ramos com evidências reunidas antes do passo seguinte.
  Comparar tempos observados quando houver implementação; não prometer ganho de 3×.
- **Pergunta:** “Finance pode começar se Logistics ainda não respondeu?”
- **Mensagem-chave:** paralelismo reduz espera quando as dependências permitem, mas exige coordenação.
- **Fallback:** usar o diagrama do guia e percorrer cartões de estado em sequência/paralelo,
  explicitando que é simulação conceitual, não trace real.

## Demo 7 — Consolidar, calcular e desafiar (planejada)

- **Objetivo:** distinguir evidências, custo de cenário e crítica do plano.
- **Conceito:** consolidation, Finance e Challenger.
- **Tempo estimado:** 30 min.
- **Arquivos envolvidos:** tools.py, models.py, data/policies.json e agents/ (futuros Finance/Risk).
- **Comandos de apoio existentes:**

  ```bash
  uv run control-tower smoke
  ```

  Execução de comparação de cenários/Challenger: pendente de complete.
- **Alteração relevante a demonstrar depois:** professor liga consolidação à avaliação determinística
  de cenários e à crítica de premissas. Mostrar alocação e datas que sustentam cada custo.
- **Resultado esperado futuro:** comparação A–D com evidências e Challenger apontando safety stock,
  restrições ou informação insuficiente. Hoje smoke só valida dados e multa hipotética.
- **Pergunta:** “O plano é melhor ou apenas deixou uma restrição de fora?”
- **Mensagem-chave:** Finance calcula sob premissas; Challenger testa essas premissas.
- **Fallback:** comparar verbalmente transferir 300 versus 450 de Campinas e destacar o piso de 200;
  não inventar ranking nem output de agente.

## Demo 8 — Recomendação estruturada e aprovação (planejada)

- **Objetivo:** separar saída válida de decisão autorizada.
- **Conceito:** structured recommendation e human approval.
- **Tempo estimado:** 25 min.
- **Arquivos envolvidos:** src/control_tower/models.py (Recommendation), tests/test_lab.py,
  graph/ (futura transição para aprovação).
- **Comandos de apoio existentes:**

  ```bash
  uv run pytest -q tests/test_lab.py -k invalid_recommendation
  ```

  Execução do fluxo com pausa para aprovação: pendente de complete.
- **Alteração relevante a demonstrar depois:** conectar resultado do grafo ao contrato existente e
  explicitar a parada para decisão humana. Schema e testes já estão preparados, não serão reescritos.
- **Resultado esperado atual:** quatro casos inválidos rejeitados, incluindo `approval_required=False`.
  Resultado futuro: recomendação validada aguardando decisão; nenhuma compra/transferência automática.
- **Pergunta:** “Passar no Pydantic significa que o plano está correto e autorizado?”
- **Mensagem-chave:** validação estrutural, qualidade da decisão e autorização são responsabilidades distintas.
- **Fallback:** abrir Recommendation e os quatro testes; discutir o limite do schema usando o plano do quadro.

## Encerramento — 20 minutos

Retomar quem decide, onde está o estado, como falha, como observar, custo e quando usar código
em vez de agente. Mostrar quais módulos foram acrescentados pelo professor e quais capabilities
permaneceram estáveis. Orientar reprodução pelo guia, sem tarefa de programação.
A comparação Git entre start e complete só será realizada após os dois estados existirem e serem validados.
