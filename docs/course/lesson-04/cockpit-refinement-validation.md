# L3 Control Plane — refinamento final da experiência

Data: 04/10/2026 · candidato `lesson-04-cockpit` · revisão local, sem publicação.

## A. Baseline

- Branch confirmada: `codex/lesson-04-cockpit`; commit inicial `6c1b168`.
- Nenhuma alteração rastreada no início. Havia **15 arquivos pessoais de planos/conhecimento não rastreados**;
  foram preservados e comparados por SHA-256. Não integram o commit deste refinamento.
- Antes de editar: **532 testes Python, todas as integrações habilitadas, em 21,98 s**;
  **5 Playwright em 3,7 s**; TypeScript aprovado; smoke com 12 checks aprovado.
- Build Next validado no Docker do curso. A tentativa local encontrou restrição do compilador
  ao abrir porta (`Operation not permitted`); não foi tratada como falha de código nem ocultada.
- Inspeção: CSS, 14 áreas, projeções Python, contratos, provider, conhecimento, testes e runbook.
  O problema do chat era confirmado: cada pergunta substituía a resposta anterior e não havia sessão.
- Integrações reutilizam a infraestrutura local, acrescentando registros sintéticos de teste ao banco.
  Escritas em conhecimento foram isoladas em volumes temporários, separados da pasta do professor.

## B. Identidade visual

- Asset oficial: **Logo L3.jpg**, copiado para `web/public/l3-logo.jpg`, sem conversão, recorte ou alteração.
  Igualdade binária verificada; proporção original 285 × 167 preservada. O Docker distribui `public/`.
- Marca: **L3 Control Plane · Agentic Workforce Operations · LAB NovaCore**.
- Tokens centralizados em `web/app/theme.css`: navy principal, cyan de destaque; verde positivo,
  âmbar atenção, vermelho crítico e tons neutros para informação desconhecida.
- Gráficos/SVG usam os mesmos tokens. Barras sem animação de entrada para evitar números visuais
  intermediários durante projeção e captura. Layout inspecionado em 1440×900 e 1920×1080.

## C. Lifecycle

- SVG leve em `web/components/lifecycle-graph.tsx`, sem nova biblioteca de grafos.
- Desenha **11 transições** recebidas da state machine existente; não recria regras em JavaScript.
- Cadastro atual destacado; Aposentado explicitamente terminal. Retornos possuem setas direcionais separadas.
- Proposta **Ativo → Em revisão** aparece separadamente, com razão/evidências,
  **não executada**, aprovação humana obrigatória e “Recomendação não é autorização”.
- Nenhum endpoint de transição foi criado; nenhum cadastro foi alterado.

## D. Business Value

| Informação | Valor / origem | Limite |
|---|---|---|
| Penalidade diária | R$ 20.000, pedido CO-001, capability `Tools.calculate_penalty` | Cadastro do case |
| Atraso hipotético | 7 dias | Hipótese didática, não atraso confirmado |
| Exposição potencial | **R$ 140.000** | Não é economia nem valor realizado; não somar entre agentes |
| Cenário recomendado | **R$ 12.500**, projeção existente `recommended_scenario_cost` | Proposta, não transação executada |
| Tempo até proposta | 1.000 ms, registro ilustrativo existente | Não confundir com latência da consulta ao Maestro |
| Valor realizado | **Ainda não validado** | Sem resultado empresarial comprovado |
| Custo total da execução | Não disponível | Infraestrutura/trabalho humano não medidos |

Custo LLM atribuído ao papel permanece separado; moedas não são convertidas e ROI não é inferido.
A fonte durável **não recebe** exposição sintética para preencher ausência de dados.
Overview e Relatórios incluem atenção, recomendações e valor sob gestão.

**LLM Cost ≠ Agent Cost ≠ Workflow Cost ≠ Business Decision ≠ Business Value.**

## E. Indicador de atenção

Backend projeta os IDs distintos dos agentes que já possuem triggers determinísticos.
Não há regra nova, cálculo de atenção em React ou classificação por LLM.
No cenário: **1 agente requer atenção**, Supply, a partir de 3 sinais existentes.
O contrato já suporta plural e lista de agentes. Com um único agente, o CTA prepara o contexto dele;
com vários, prepara a workforce e mostra a lista. Abrir o painel não faz request ao provider.

## F. Maestro

### Interface e contexto

Botão global no header e drawer lateral preservam a página de origem. Página Maestro e drawer
compartilham o mesmo estado da conversa. Context chips explicitam fonte, agente, lifecycle e execução
quando aplicáveis. Contexto muda sem apagar mensagens; uma indicação visual registra a troca.

`MaestroContext`: `context_type`, `agent_id`, `execution_id`, `recommendation_id`, `knowledge_id`,
`source`, `route`, `selected_filters`. Frontend envia identificadores; backend resolve objetos e fatos.
Não envia HTML, prompts extensos ou JSON de página ao provider. O contexto de Economia & Valor resolve também a exposição exibida, sem transplantar a fixture para a fonte durável. IDs inválidos ou fontes incompatíveis
são rejeitados. Conteúdo de conhecimento pendente não entra na síntese factual como verdade aprovada.

As tools existentes de cadastro, metas, medições, qualidade, economia, valor, lifecycle, SLOs,
recomendações, execuções, workforce e conhecimento permanecem. Sem SQL no Maestro.

### Sessão e falhas

- Sessão explícita: ID opaco; armazenamento **em memória no processo da API**, limite 128 sessões.
- Até 12 mensagens recentes (6 pares), com resumos curtos das respostas, entram em cada request.
  Histórico é continuidade, não evidência; fatos recuperados no contexto atual permanecem a referência.
- Trava por sessão e bloqueio imediato no frontend impedem solicitações simultâneas duplicadas.
- Usuário/assistente empilhados, autoscroll, loading textual, erro inline e retry manual.
- Falha mantém histórico; plano só é salvo depois de validar contrato, referências e limites existentes.
- O schema Pydantic do plano restringe `evidence_refs` aos IDs da recuperação atual, por enum; descrições não podem ocupar esse campo. A whitelist posterior continua como segunda validação.
- “Fontes utilizadas (N)” por resposta; detalhes de hipótese, plano, staffs e custo expansíveis.
- Staffs continuam sendo responsabilidades propostas, não novos agentes executando ações.

### Provider e consumo

`./scripts/cockpit.sh` assume **OpenAI** quando `LLM_MODE` não está definido; modelo padrão
`gpt-4.1-mini`. Runbook/README orientam chave somente no servidor. Mock é explícito para testes,
CI, desenvolvimento e fallback offline. Não existe fallback silencioso.

Ausência de chave foi verificada também no Compose real:

```text
GET /health             200
GET /cockpit/overview   200
POST /maestro/chat      503 — Maestro indisponível: provider LLM não configurado.
POST /incidents         503 — Provider LLM não configurado; consultas permanecem disponíveis.
```

A única adaptação fora do cockpit é uma condição de startup da API, habilitada apenas neste perfil,
para permitir leitura sem provider. Workers mantêm validação antecipada; novos jobs são rejeitados
quando falta chave. Os demais perfis preservam o comportamento anterior.

Usage real é persistido no plano: modelo, input/output tokens, custo estimado, moeda e versão do pricing.
Cálculo Decimal com pricing já configurado; não é fatura e não entra na economia do workflow.
Não atribui desconto de cache não instrumentado. Sem usage/pricing, o custo fica desconhecido.

### Ensaio OpenAI

Resultados finais do ensaio estão na tabela a seguir (atualizada após a validação final).
Nenhum conhecimento gerado pelo ensaio foi aprovado automaticamente.

| Turno | Duração | Entrada | Saída | Estimativa USD | Fontes |
|---|---:|---:|---:|---:|---:|
| 1 | 4.39 s | 2313 | 443 | 0.001634 | 6 |
| 2 | 4.71 s | 2512 | 389 | 0.0016272 | 7 |
| 3 | 4.48 s | 2702 | 394 | 0.0017112 | 5 |

Uma única sessão confirmada nos três turnos; todos exigem aprovação humana. Compiler: HTTP 200, 2.94 s, `pending_review`.

Antes do reforço do enum, duas respostas reais foram rejeitadas (ensaio e diagnóstico controlado):
o modelo escreveu descrições em `evidence_refs`. Nenhum plano inválido foi persistido.
O schema foi então limitado aos IDs recuperados e o ensaio de três turnos repetido com sucesso.
Não houve retry automático nem fallback silencioso. A validação é parte da experiência, não garantia
de verdade semântica. Os ensaios/candidatos ficaram exclusivamente no volume temporário.


## G. Agent 360 e navegação

- **Última análise do Maestro**: problema observado, hipótese a verificar, recomendação,
  staffs e status; planos antigos continuam legíveis.
- **Continuar conversa no Maestro** mantém a sessão ativa da aba; não reconstrói sessões antigas após reinício.
- Agent 360 abre contexto do agente; recomendação abre contexto de seu ID e resolve o agente no servidor;
  documento e execução abrem seus contextos próprios pelo botão global.
- Links existentes para execuções, decisões e conhecimento permanecem.

## H. Learning Loop / maturidade

Fluxo de 12 etapas preservado. O arco Aula 1–4 saiu da UI e permanece como narrativa dos slides.
Modelo organizacional: Automação → Observável → Gerenciada → Adaptativa → Learning Enterprise.
LAB indicado **entre níveis 3 e 4**, com medição, interpretação e propostas; sem mudança autônoma.
Autoridade de execução é outro eixo: não confundir maturidade organizacional com permissão de ACT.

“Learning Enterprise não significa auto-modificação sem controle.”
“Self-learning is not uncontrolled self-modification.” Nível 5 não é operacional no LAB.

## I. Capturas inspecionadas

Capturas de UI real, sem montagem ou redesenho; dados sintéticos identificados.

- [Overview 1440×900](cockpit-refinement-captures/overview-1440.png)
- [Overview 1920×1080](cockpit-refinement-captures/overview-1920.png)
- [Agent 360](cockpit-refinement-captures/agent-360.png)
- [Lifecycle e proposta](cockpit-refinement-captures/lifecycle.png)
- [Economia & Valor](cockpit-refinement-captures/economia-valor.png)
- [Conversa — três turnos em mock](cockpit-refinement-captures/maestro-conversa.png)
- [Maestro global em execução](cockpit-refinement-captures/maestro-execucao.png)
- [Segundo Cérebro](cockpit-refinement-captures/segundo-cerebro.png)
- [Learning Loop / Maturidade](cockpit-refinement-captures/learning-loop-maturity.png)
- [Maestro com OpenAI real](cockpit-refinement-captures/maestro-openai.png)

`node scripts/capture_cockpit_refinement.mjs` reproduz as nove capturas mock, com a stack
já iniciada em mock e volume de conhecimento de ensaio. Cria propostas, sem aprovações.
As conversas mantêm todos os turnos no scroll interno; a captura mostra uma janela do histórico.

## J. Testes

| Verificação | Resultado |
|---|---|
| Python + todas as integrações | **546 passed em 21,49 s**; zero skips |
| Playwright (5 anteriores + 4 novos cenários) | **9 passed em 6,4 s** |
| TypeScript | `tsc --noEmit` aprovado |
| Next production build | Aprovado no Docker Node 22 / Turbopack |
| Smoke mock | **12 checks**, status `ok`, offline |
| Compose | Todos os serviços saudáveis; helper `demo_cockpit.py` aprovado |
| OpenAI real | 3 turnos na mesma sessão + Compiler pendente; tabela acima |
| Ausência de chave real | Leituras HTTP 200; Maestro/jobs HTTP 503 explícitos |
| Integridade | Logo idêntico e 15 arquivos do professor preservados por hash |
| Diff | `git diff --check` sem erros |
| Higiene dos módulos alterados | Ruff imports/erros Python (I/F) aprovado; Prettier aprovado |

São **14 testes Python adicionais** sobre a baseline, sem chamadas OpenAI nos testes unitários.
O smoke e a regressão usaram mock explícito. Os ensaios reais foram separados e controlados.

Cobertura adicional: exposição e fonte durável, atenção determinística, histórico limitado,
contexto de execução/recomendação/conhecimento, pendente excluído como verdade, erro sem plano parcial,
limite de sessões, duplicidade concorrente, usage/custo separado, API legível sem chave e rejeição de jobs.
Browser cobre logo/navy, 11 arestas, estado atual/proposta, R$ 140 mil sem savings, CTA sem chamada,
três turnos, histórico entre página/drawer, mudança de contexto, Agent/Recommendation/Knowledge,
erro/retry, maturidade e remoção do arco da disciplina. As cinco demos de browser anteriores permanecem verdes.

## K. Limitações

- LAB local, sem autenticação empresarial ou histórico de chat durável/multiprocesso.
  Reload da página, reinício da API ou evicção da sessão pode perder continuidade; planos e knowledge persistem.
- Semântica do texto LLM exige revisão humana. Pydantic e referências válidas não comprovam causa ou benefício.
- Latência e disponibilidade OpenAI variam; tempos registrados são observações, não garantia.
- Conhecimento, exposição e execuções didáticos não comprovam resultado empresarial real.
- Nenhuma alteração em LangGraph, agents, tools, tasks, store, regras do Decision Engine ou lifecycle.
- Sem auto-code, auto-PR, auto-deploy, troca automática de modelo, transição automática ou novos staffs.
- Runtime/serviços permanecem os mesmos. Sem banco vetorial, graph database, tracing de chat ou analytics novo.

## L. Git

- Branch: `codex/lesson-04-cockpit`.
- Commit desta rodada: consultar `git log -1 --format='%h %s'` (o relatório integra o próprio commit).
- Arquivos do professor preservados: **15 não rastreados**, fora do commit.
- Checkpoints históricos preservados. **Sem push; nenhuma tag criada ou movida.**
- Material pronto para revisão visual/pedagógica do professor; nenhuma autorização de ACT é inferida.
