# Aula 1 — Guided Demo / Observation Guide

## O que vamos compreender

Como um problema empresarial de coordenação pode ser decomposto em responsabilidades, estado,
coordenação, paralelismo, crítica e aprovação humana. O professor explica e demonstra; alunos
observam e discutem. Não há programação durante a aula.

> Um agente é uma unidade de inteligência. Um sistema multiagente é uma organização.
> Colocar essa organização em produção é um problema de engenharia.

As seis perguntas: Who decides? Where is the state? What happens when it fails? Can I observe it?
What does it cost? Should this even be an agent?

## Antes e depois

Antes: evento → pessoas → planilhas → reuniões → decisão.
Depois: evento → evidências → coordenação → cenários → crítica → recomendação → decisão humana.

Veja o [material visual](../../docs/course/classroom/index.html), que abre localmente sem rede.
O professor seleciona a tela correspondente ao conceito. Mock executa o grafo real com especialistas
determinísticos: não há raciocínio de LLM nem ação operacional automática.

## O que observar — e como reproduzir depois

Na revisão atual, após instalação indicada no README:

| Conceito | Comando | Output esperado | Discussão / aprendizado |
|---|---|---|---|
| Evento e tempo | `uv run control-tower incident` | Alpha atrasa 7 dias; data fixa | Atraso do fornecedor não é atraso de todos os clientes |
| Capabilities | `uv run control-tower show INCIDENT-001 summary` | SP 300/750/450; Campinas 500/piso 200/transferível 300 | Disponível não significa transferível sem risco |
| Estado | `uv run control-tower show INCIDENT-001 state` | Canais separados por responsável | Quem escreve qual evidência? |
| Especialistas | `uv run control-tower show INCIDENT-001 specialists` | Supply, Production e Logistics | Papéis se justificam por responsabilidade |
| Coordenação | `uv run control-tower show INCIDENT-001 coordination --demo-delay-ms 500` | Ramos independentes e join após todos | Espera artificial serve para visualizar, não medir LLM |
| Controle sequencial | `uv run control-tower show INCIDENT-001 coordination --sequential --demo-delay-ms 500` | Mesmos papéis, em sequência | O que é dependência e o que pode ser paralelo? |
| Finance | `uv run control-tower show INCIDENT-001 scenarios` | Tabela A–D e restrições | Conta correta depende de premissas |
| Crítica | `uv run control-tower show INCIDENT-001 challenger` | Plano → premissas → desafios → riscos | Crítica é distinta de gerar outra análise |
| Recomendação | `uv run control-tower show INCIDENT-001 recommendation` | awaiting_approval, actions_executed=false | Validação não autoriza execução |

As primeiras views não executam Finance, Challenger ou recomendação. A tabela de cenários usa a
revisão de regras existente para admissibilidade, mas não anuncia a escolha final. Cada comando
reexecuta o case até a etapa necessária; não retoma uma sessão anterior.

## Quatro distinções para levar da aula

- `customer_delay_days=3` é o maior atraso entre clientes, não o atraso do cliente estratégico.
- O cliente estratégico pode ter atraso zero.
- `avoided_penalty` é diferente de economia líquida incremental.
- `confidence=0.65` é didático/fixo neste estágio, não probabilidade calibrada.

Leia as [premissas completas](../../docs/case/NOVACORE.md) depois da aula. Capacidade, prazo de Alpha,
reposição de estoque e custos de cancelamento ainda exigem confirmação humana.

Ausência de evidência precisa aparecer como erro e não como conclusão. Os testes continuam no
repositório; a aula usa apenas uma nota curta, sem antecipar resiliência operacional.

Para estudo posterior: `uv run control-tower run INCIDENT-001 --json` e comparação Git entre versões.
O professor usa [o runbook](../../docs/course/lesson-01-runbook.md); não precisa percorrer grandes diffs.
Tags existentes permanecem intactas e ainda não contêm estas novas views.

## Observar a fronteira mock vs OpenAI

Após a recomendação, compare `LLM_MODE=mock` e `LLM_MODE=openai` usando
`uv run control-tower show INCIDENT-001 llm-decisions`.
O modo real usa a credencial previamente configurada pelo professor. Ninguém programa em sala.

- Observe interpretação do Supervisor, três sínteses, achados do Challenger e justificativa final.
- Mesmas fontes e cálculos A–D; narrativas e preferência entre alternativas admissíveis podem variar.
- Pergunta: se o modelo sugerir outro valor ou ignorar uma política, quem impede a recomendação?
- Aprendizado: **LLMs interpretam e julgam. Código determinístico mede e valida.**
- Fallback: mock ao vivo e exemplo gravado identificado pelo modo, nunca simular sucesso da API.

Roteiro detalhado em [llm-modes.md](../../docs/course/llm-modes.md).
