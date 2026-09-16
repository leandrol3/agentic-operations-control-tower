# Aula 1 — Runbook de contexto, teoria e demonstração

## Objetivo pedagógico

Compreender como um problema empresarial de coordenação pode ser decomposto e implementado como
um sistema multiagente com responsabilidades, estado, coordenação, paralelismo, crítica e aprovação humana.

Esta aula não é uma aula de sintaxe LangGraph nem live coding. Os alunos não programam.
O professor explica, pergunta e demonstra partes selecionadas da implementação já pronta.
Código aparece apenas quando esclarece uma decisão arquitetural; JSON integral e diffs ficam para estudo posterior.

**Revisão mock + OpenAI:** disponível na `main` (`git switch main` e `git pull --ff-only`).
O bloco 10B e llm-decisions fazem parte desta revisão.
As tags publicadas permanecem intactas e não incluem estes ajustes.

## Professor Setup — antes da aula

- Ambiente instalado previamente: nesta branch, executar `uv sync --locked` antes de entrar em sala.
- `.env` com `LLM_MODE=mock`; conferir que variável do terminal não aponta para outro modo.
- Para a comparação final, configurar OPENAI_API_KEY (ou OPENAI_API_KEY_FILE) e OPENAI_MODEL
  antes da aula. Executar `LLM_MODE=openai uv run python scripts/compare_modes.py` no ensaio.
  Guardar a saída como exemplo gravado; não depurar credenciais nem instalar SDK em sala.
- Testes e smoke executados; nenhum processo de instalação ou depuração durante a aula.
- Abrir `docs/course/classroom/index.html` em um navegador local, por duplo clique no arquivo.
  O documento não usa rede. Deixar selecionado **Contexto**, sem revelar as telas finais.
- Pelo seletor do documento, localizar antecipadamente **Arquitetura**, **Timeline**, **SP / Campinas**,
  **Cenários A–D** e os oito recortes de código. Mostrar uma tela por vez.
- Alternativas: `graph.svg` pronto, `snippets.md` e oito arquivos `.txt` de fallback na mesma pasta.
- Terminal em tela cheia com pelo menos **96 colunas × 24 linhas**, fonte grande e apenas um comando por vez.
  Views têm no máximo 20 linhas; reservar espaço para prompt. Limpar a tela entre conceitos.
- Se o ambiente falhar, usar arquivos gravados identificados como fallback. Não instalar dependências em aula.

```bash
uv run pytest -q
uv run control-tower smoke
uv run control-tower run INCIDENT-001
```

O comando completo acima é **checagem pré-aula**, não o roteiro das primeiras demonstrações.
Os materiais estáticos já estão no repositório. Para atualizá-los, somente antes da aula:

```bash
uv run python scripts/prepare_classroom.py
```

### O que o mock demonstra

`LLM_MODE=mock` demonstra a arquitetura REAL de coordenação usando especialistas determinísticos.
Não existe raciocínio de LLM nesse modo. O valor é explicar state, roles, graph, orchestration,
parallelism, consolidation e contracts. LLM real não é necessário para o objetivo desta aula.
OpenAI é a segunda demonstração, somente no bloco 10B após a recomendação.
Prepare chave e modelo antes da aula; os blocos anteriores continuam em mock.

## Agenda — 240 minutos

| Horário | Bloco | Tempo |
|---|---|---:|
| 00:00–00:25 | 1. Business context: NovaCore e coordenação | 25 min |
| 00:25–00:50 | 2. Teoria: Agent vs Multi-Agent System | 25 min |
| 00:50–01:10 | 3. INCIDENT-001, Time-to-Decision e investigação | 20 min |
| 01:10–01:30 | 4. Capabilities, tools determinísticas e contratos | 20 min |
| 01:30–01:45 | 5. Shared state e responsabilidades | 15 min |
| 01:45–02:00 | Intervalo | 15 min |
| 02:00–02:25 | 6. Supervisor + LangGraph | 25 min |
| 02:25–02:45 | 7. Parallel execution + join | 20 min |
| 02:45–03:15 | 8. Finance e cenários A–D | 30 min |
| 03:15–03:35 | 9. Challenger | 20 min |
| 03:35–03:42 | 10A. Structured Recommendation + Human Approval | 7 min |
| 03:42–03:50 | 10B. Mock vs OpenAI: interpretação e validação | 8 min |
| 03:50–04:00 | 11. Síntese e provocação para Aula 2 | 10 min |

Primeiros 70 minutos reservados a contexto e teoria, com no máximo dois minutos de comando no bloco 3:
cerca de 68 minutos de discussão conceitual antes de explorar código. Os tempos incluem perguntas.
Se houver atraso, reduzir navegação de código; não sacrificar contexto nem aprovação humana.

## 1. Business context — 25 minutos

- **Objetivo/conceito:** mostrar que a NovaCore tem um problema de coordenação, não apenas de informação.
- **Condução:** 10 min de contexto, 8 min percorrendo compras → produção → logística → comercial,
  7 min de discussão. Usar a tela **Contexto**; nenhum comando ou código.
- **Problema:** Alpha atrasa M42. Quem reúne informações? Quem verifica efeitos em outros departamentos?
- **Antes:** evento → pessoas → planilhas → reuniões → decisão.
- **Depois conceitual:** evento → investigação coordenada → decisão humana; não mostrar um plano vencedor.
- **Pergunta:** “Se cada área fizer uma boa análise isolada, a decisão da empresa necessariamente será boa?”
- **Mensagem-chave:** o custo de coordenação conecta as áreas e explica a necessidade de um sistema.
- **Fallback:** contar o fluxo de decisão com cinco caixas no quadro.

## 2. Agent vs Multi-Agent System — 25 minutos

- **Objetivo/conceito:** separar capacidade individual, organização de papéis e engenharia operacional.
- **Condução:** 10 min sobre a frase abaixo, 10 min nas seis perguntas e 5 min debatendo limites.
  Usar a tela **Teoria**. Nenhum código.

> Um agente é uma unidade de inteligência. Um sistema multiagente é uma organização.
> Colocar essa organização em produção é um problema de engenharia.

- **Who decides?** Quem define o plano e escolhe quem participa?
- **Where is the state?** Como cada papel sabe o que já foi apurado?
- **What happens when it fails?** Ausência de resultado não deve virar certeza.
- **Can I observe it?** Conseguimos explicar a sequência e as evidências?
- **What does it cost?** Onde cabem modelo, cálculo determinístico e coordenação?
- **Should this even be an agent?** Uma conta de multa precisa de LLM?
- **Pergunta:** “Qual dessas responsabilidades é inteligência e qual é engenharia?”
- **Mensagem-chave:** mais agentes não significa uma arquitetura melhor; responsabilidades precisam justificar-se.
- **Fallback:** usar a frase e as seis perguntas impressas; nenhuma dependência de software.

## 3. INCIDENT-001 e Time-to-Decision — 20 minutos

- **Objetivo/conceito:** distinguir evento, ordens relacionadas e impacto calculado por cenário.
- **Condução:** 8 min de incidente/timeline, até 2 min de comando, 10 min de discussão.
- **Material:** tela **Timeline**, `incidents/incident_001.json`, `docs/case/NOVACORE.md`.

```bash
uv run control-tower incident
```

- **Output:** data do evento 2026-10-01, atraso de Alpha sete dias, material M42 e planta São Paulo.
- **Timeline:** pedido Beta em 01/10 → chegada 03/10; Alpha → 08/10.
  Material no início de D → produção em D → entrega até fim de D+1. Dias corridos.
- **Time-to-Decision:** inclui decisão humana. A duração da CLI mede apenas o workflow até a recomendação.
  Horas para minutos é uma ilustração de valor, não benchmark.
- **Pergunta:** “Atraso de sete dias do fornecedor significa sete dias de atraso para todos os clientes?”
- **Mensagem-chave:** relações iniciam investigação; ainda não temos impacto confirmado.
- **Fallback:** ler o JSON de nove linhas e usar a timeline já aberta.

## 4. Capabilities, tools e contratos — 20 minutos

- **Objetivo/conceito:** capability controla o acesso e o significado dos dados; regras não dependem de LLM.
- **Condução:** 7 min de teoria, 5 min do quadro, 5 min de discussão e nota de falha de até 3 min.
- **Material:** tela **SP / Campinas**, `tools.py` apenas como referência; não abrir o arquivo integral.

```bash
uv run control-tower show INCIDENT-001 summary
```

- **Output:** SP disponível 300, demanda 750, déficit 450; Campinas disponível 500, piso 200,
  transferível 300; Beta capacidade 450, custo 145/un. e prêmio 45/un.; rotas 3 dias/5.000 e 1 dia/18.000.
- **Por que não ler todos os CSVs no agente?** Acesso direto mistura descoberta, interpretação e regra de
  negócio. A capability entrega um contrato pequeno, verificável e substituível por uma API empresarial.
- **Pergunta:** “500 disponíveis significa que podemos transferir 500 sem consequências?”
- **Mensagem-chave:** available, reservado e safety stock não são a mesma coisa.
- **Nota/fallback de 2–3 min, sem bloco próprio:** abrir `classroom/missing-evidence.txt` e dizer:
  “Ausência de evidência precisa aparecer como erro e não como conclusão.” Os testes de fixture permanecem;
  não percorrer todos em sala. Resiliência será aprofundada depois.
- **Fallback principal:** `classroom/summary.txt`. Não mostrar cenários ainda.

## 5. Shared state e especialistas — 15 minutos

- **Objetivo/conceito:** explicar canais de escrita, evidência tipada e responsabilidades.
- **Condução:** 5 min de teoria, 5 min das views e até 5 min dos snippets/perguntas.

```bash
uv run control-tower show INCIDENT-001 state
uv run control-tower show INCIDENT-001 specialists
```

- **Output:** plano Supply/Production/Logistics; cada canal contém só sua evidência; join reúne 3 resultados.
- **Recortes:** S1 Shared state e S2 Specialist output no [caderno de snippets](classroom/snippets.md).
  Não abrir o restante da classe ou imprimir o estado inteiro.
- **Pergunta:** “Quem pode escrever em cada campo? Por que não juntar tudo em um único texto?”
- **Mensagem-chave:** estado é contrato de coordenação, não histórico de conversa indiscriminado.
- **Sem revelação prematura:** estas views interrompem o grafo após consolidação, antes de Finance,
  Challenger, Recommendation e Approval; esses nós não executam.
- **Fallback:** `state.txt` e `specialists.txt`. Código previamente localizado, sem edição ao vivo.

## Intervalo — 15 minutos

Manter **Teoria** ou **Contexto** aberto; não deixar a tela de conclusão exposta.

## 6. Supervisor + LangGraph — 25 minutos

- **Objetivo/conceito:** quem decide o plano e como o fluxo é representado.
- **Condução:** 10 min de arquitetura, 5 min do Supervisor, 5 min das arestas e 5 min de perguntas.
- **Material:** tela **Arquitetura**, diagrama pronto `classroom/graph.svg`.
- **Recortes:** S3 Supervisor e S4 LangGraph edges. Explicar o significado das transições, não sintaxe.
- **Comando opcional, no máximo 30 segundos:** comprovar a origem do diagrama; não projetar Mermaid raw
  como visualização principal.

```bash
uv run control-tower graph
```

- **Output:** fonte Mermaid do grafo real; o SVG já está pronto para leitura.
- **Pergunta:** “Quem escolhe os especialistas? O que muda se não houver plano conhecido?”
- **Mensagem-chave:** o Supervisor usa um plano determinístico do case no mock; não existe seleção por LLM.
- **Fallback:** SVG estático e snippet S3; os caminhos de bloqueio estão descritos na legenda.

## 7. Parallel execution + join — 20 minutos

- **Objetivo/conceito:** executar em paralelo só o que é independente e esperar as dependências.
- **Condução:** 6 min conceituais, 4 min de comparação, 5 min do join e 5 min de discussão.

```bash
uv run control-tower show INCIDENT-001 coordination --demo-delay-ms 500
uv run control-tower show INCIDENT-001 coordination --sequential --demo-delay-ms 500
```

- **Output:** ordem real de início/fim e join após os três resultados. Nada de cenários ou conclusão.
- **Recorte:** S5 Parallel join. Mostrar a lista de origens como “aguardar todos”.
- **Pergunta:** “Podemos consolidar se uma das áreas ainda não respondeu?”
- **Mensagem-chave:** paralelismo exige independência; join garante que a consolidação não se antecipe.
- **Tempo:** espera artificial de 500 ms, explicitamente rotulada. Resultado é ilustrativo, não benchmark.
- **Fallback:** `coordination.txt` e diagrama; explicar que a ordem dos ramos pode variar.
  Não há retry/backoff/chaos nesta demonstração.

## 8. Finance e cenários A–D — 30 minutos

- **Objetivo/conceito:** construir custo incremental sob premissas, alocação e restrições explícitas.
- **Condução:** 8 min sobre premissas, 10 min da tabela, 5 min de cálculo e 7 min de discussão.

```bash
uv run control-tower show INCIDENT-001 scenarios
```

- **Output:** tabela A–D com ação, custo incremental, atrasos por cliente, multas, restrição e admissibilidade.
  A=23.500; B=20.250; C=18.000; D=12.500. A view não anuncia um vencedor nem produz Recommendation.
- **Recorte:** S6 Finance deterministic calculation: prêmio de material + frete + multas.
- **Admissibilidade:** usa a mesma revisão de regras existente no grafo. Essa view executa até Challenger
  para mostrar admissibilidade, mas oculta sua narrativa e seleção; não chama Recommendation/Approval.
  Não há uma cópia das regras na camada visual.
- **Quatro notas ficam junto da tabela:**
  1. `customer_delay_days=3` é o maior atraso entre clientes, não o atraso do cliente estratégico.
  2. O cliente estratégico pode ter atraso zero; neste case CO-001 tem zero.
  3. `avoided_penalty` difere de economia líquida incremental.
  4. `confidence=0.65` é didático/fixo, não probabilidade calibrada.
- **Pergunta:** “Você aceitaria atraso de um cliente não estratégico para reduzir custo?”
- **Mensagem-chave:** conta correta não elimina a necessidade de discutir premissas e objetivos.
- **Fallback:** `scenarios.txt` ou tela **Cenários A–D**; nunca derivar todas as fórmulas ao vivo.

## 9. Challenger — 20 minutos

- **Objetivo/conceito:** separar proposição de plano e crítica estruturada.
- **Condução:** 5 min de teoria, 5 min da view, até 3 min de código, 7 min de discussão.

```bash
uv run control-tower show INCIDENT-001 challenger
```

- **Output:** Candidate Plan → Assumptions → Challenges → Remaining Risks.
  Finance propõe D; C viola o piso em 150 unidades; informações comerciais e premissas seguem pendentes.
- **Recorte:** S7 Challenger. Não percorrer todas as verificações.
- **Mensagem principal:** “O Challenger não recalcula o cenário. Ele testa se a conclusão ignora
  premissas, riscos ou evidências.”
- **Precisão técnica:** o código também verifica consistência aritmética e temporal. Isso não reconstrói
  alocação nem simula outro plano. A revisão não é apenas uma segunda análise redundante.
- **Pergunta:** “Que evidência poderia nos fazer abandonar o plano aparentemente mais barato?”
- **Fallback:** `challenger.txt`; discutir confirmação do prazo de Alpha e reposição do estoque local.

## 10A. Structured Recommendation + Human Approval — 7 minutos

- **Objetivo/conceito:** separar contrato válido de autorização para agir.
- **Condução:** 2 min de contrato, 2 min de view/snippet, 3 min de decisão humana.

```bash
uv run control-tower show INCIDENT-001 recommendation
```

- **Recorte:** S8 Recommendation. O restante do contrato está no repositório para estudo posterior.
- **Output:** cenário D; custo 12.500; multa evitada 16.000; economia líquida incremental 11.000;
  atraso máximo 3 dias, estratégico 0; `Recommendation → awaiting_approval`; `actions_executed = false`.
- **Pergunta:** “Uma recomendação validada pode se tornar compra sem alguém autorizar?”
- **Mensagem-chave:** “Uma recomendação válida não é uma decisão autorizada.”
- **Limite real:** o nó cria solicitação pending e termina; não existe retomada, comando de aprovar
  nem integração operacional. Nenhuma compra, transporte ou transferência é executada.
- **Fallback:** `recommendation.txt`. Não projetar o estado integral.

## 10B. Mock vs OpenAI — 8 minutos

- **Objetivo:** distinguir interpretação/julgamento de medidas e validação.
- **Conceito:** mesmas fontes, tools, cálculos, nós e arestas; seis chamadas LLM em pontos definidos.
- **Condução:** 1 min retomando a fronteira; até 2 min de execução; 3 min comparando; 2 min de discussão.
- **Arquivos:** `llm.py`, `agents/interpretation.py`, `settings.py`, `scripts/compare_modes.py`.
- **Preparação:** chave/modelo testados; comando de comparação e saída gravada já abertos.
  Se não concluir em 2 min, interromper e usar fallback. Cada chamada tem timeout de 45 s, sem retry.

```bash
LLM_MODE=mock uv run control-tower show INCIDENT-001 llm-decisions
LLM_MODE=openai uv run control-tower show INCIDENT-001 llm-decisions
```

Para verificar a paridade automaticamente no ensaio, em duas execuções reais:

```bash
LLM_MODE=openai uv run python scripts/compare_modes.py
```

- **Alteração demonstrada:** Supervisor interpreta e gera perguntas; especialistas sintetizam suas
  evidências; Challenger aponta premissas/ausências; Recommendation explica trade-offs e escolhe
  entre cenários admissíveis. O mock preserva suas respostas determinísticas.
- **Output esperado:** view curta com modo/modelo, interpretação, especialistas, achados e justificativa;
  `awaiting_approval` e `actions_executed=false`. Cálculos A–D idênticos; textos e cenário escolhido
  podem variar. O script imprime `mesma evidência: True | mesmos cálculos A–D: True` quando ambos concluem.
- **O que o código decide:** quais dados existem, valores, multas, políticas, plano completo para este
  incidente, admissibilidade e conferência da Recommendation. C não se torna admissível por opinião LLM.
- **Pergunta:** “Se a explicação parece convincente mas muda o custo, qual camada deve rejeitá-la?”
- **Mensagem-chave:** **LLMs interpretam e julgam. Código determinístico mede e valida.**
- **Fallback:** executar mock; apresentar exemplo OpenAI gravado somente se validado e rotulado.
  Sem gravação de sucesso, mostrar o erro observado e declarar que a execução real não foi concluída.
  Não há troca automática de provider, cadeia de raciocínio, prompts extensos ou JSON gigante na tela.
- **Limite:** Challenger LLM é consultivo; riscos são preservados para decisão humana. Validação de
  estrutura e números não prova que todo texto gerado seja factualmente correto.

## 11. Síntese — 10 minutos

- **Condução:** 5 min retomando as seis perguntas e 5 min de discussão final.
- **Sequência consolidada:** Evidence → Coordination → Scenarios → Challenge → Recommendation.
- **Pergunta de ponte:** “Funcionou para um incidente. O que acontece quando chegam 500?”
- **Limite:** somente provocação; não iniciar Aula 2, instalar infraestrutura nem executar carga.
- **Após a aula:** alunos podem reproduzir as views e consultar código/JSON completo. Sem tarefa de programação.

## Recortes exatos — sem diffs em sala

Todos já estão no HTML e em `classroom/snippets.md`, extraídos do código real. Linhas desta revisão:

| ID | Conceito | Arquivo em src/control_tower/ | Linhas |
|---|---|---|---|
| S1 | Shared state (somente evidências) | graph/state.py | 122–131 |
| S2 | Specialist output | agents/specialists.py | 7–20 |
| S3 | Supervisor | agents/supervisor.py | 6–17 |
| S4 | LangGraph edges | graph/workflow.py | 113–134 |
| S5 | Parallel join | graph/workflow.py | 123–137 |
| S6 | Finance deterministic calculation | scenarios.py | 82–93 |
| S7 | Challenger | agents/challenger.py | 55–70 |
| S8 | Recommendation | agents/interpretation.py | 59–70 |

Os testes verificam que os trechos continuam idênticos ao código-fonte. O gerador não edita o grafo.
S1 contém oito linhas de código e duas de separação para não expor campos de etapas posteriores.

## Notas operacionais

- `show` não carrega um histórico salvo: cada comando executa novamente o mesmo fixture no modo escolhido até
  o ponto necessário. O estado de uma view não é retomado pela próxima. Em mock os resultados são
  determinísticos; OpenAI varia apenas interpretação, síntese e julgamento.
- Eventos da view coordination refletem execução real; HTML e arquivos de fallback são snapshots estáticos.
- Ausência/erro interrompe a apresentação e retorna saída 1; nunca inventar valores para completar um quadro.
- `run`, `--json`, testes de fixture e diffs continuam disponíveis para preparação/estudo. Não são a aula.
