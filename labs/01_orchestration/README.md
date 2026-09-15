# Aula 1 — Guided Demo / Observation Guide

Durante a aula, o professor implementa e demonstra. Os alunos acompanham, formulam hipóteses e
comparam comportamentos; não há programação pelos alunos. Após a aula, os comandos permitem
reproduzir o que já está disponível. O [runbook do professor](../../docs/course/lesson-01-runbook.md)
organiza a condução e os fallbacks.

## Arquitetura antes e depois

**Antes do start:** incidente → consultas dispersas → planilhas → discussão sem contrato comum.

**Start executável:**

```text
INCIDENT-001 → CLI → Tools → CSV/JSON
                     ↕
                 Pydantic
```

**Depois, complete aprovado executável em mock:**

```text
Incidente → Supervisor → estado compartilhado
                         ├─ Supply ──────┐
                         ├─ Production ──┼→ consolidação → Finance → Challenger
                         └─ Logistics ───┘                            ↓
                                             recomendação → aprovação humana
```

LangGraph e seus nós são demonstrados pelo professor. O start já contém o boilerplate:
dados, contratos, tools, CLI, configuração, fixtures, testes e modo offline.

## Demonstrações disponíveis no start

Na raiz do checkout revisado, com dependências instaladas conforme README:

| Conceito demonstrado | Comando | Output esperado | Pergunta para discussão | Aprendizado |
|---|---|---|---|---|
| Prontidão da base | `uv run control-tower doctor` | `status: ok`, `related_orders: 3`, `impact_status: not_assessed` | Carregar dados significa resolver um incidente? | Prontidão e resultado são coisas distintas. |
| Evento e tempo | `uv run control-tower incident` | `event_date: 2026-10-01`, `delay_days: 7` | Qual cliente atrasará e por quantos dias? | O evento não contém essa resposta. |
| Capabilities e restrições | `uv run control-tower tools` | SP: 300 disponíveis; três ordens; Beta: 450 unidades a 145 BRL; duas rotas | Transferência resolve tudo? | Estoque livre, safety stock, custo e prazo competem. |
| Evidência reproduzível | `uv run control-tower smoke` | 12 checks; demanda 750; déficit 450; multa hipotética `140000.00` | Essa multa foi realmente incorrida? | Smoke valida o case, não confirma impacto. |
| Falha explícita | `uv run pytest -q tests/test_lab.py -k incomplete` | Testes passam ao comprovar rejeição dos fixtures incompletos | Devemos mostrar sucesso se Beta sumiu? | Ausência de evidência deve ficar visível. |

Leia a [convenção temporal](../../docs/case/NOVACORE.md): material chega no início do dia, produção
ocorre nesse dia e entrega ao cliente pode ocorrer no dia seguinte. Ordens relacionadas não são
ordens com atraso confirmado. `not_assessed` não significa ausência de impacto.

## Demos 5–8 — o que observar no complete

No complete aprovado, execute `uv run control-tower run INCIDENT-001` e observe os papéis abaixo.
Use `--json` para inspecionar estado/evidências; `uv run control-tower graph` mostra o grafo real.
Compare `--demo-delay-ms 500` com `--sequential --demo-delay-ms 500`; a espera é artificial.
Use `--fail-specialist logistics` para observar o bloqueio no join (saída 1 esperada).

| Conceito | Antes → depois | Evidência a observar | Pergunta | Aprendizado |
|---|---|---|---|---|
| Shared state e especialistas | Saídas isoladas → evidências por responsabilidade | Cada especialista escreve sua parte do estado | Quem pode sobrescrever qual informação? | Estado é contrato de coordenação. |
| Supervisor e LangGraph | Chamadas manuais → plano e transições explícitas | Especialistas selecionados e transições visíveis | Quem decide e como encerra? | Coordenação precisa de limites. |
| Paralelismo e consolidação | Investigação sequencial → ramos independentes e junção | Resultados reunidos antes de Finance | O que acontece se um ramo faltar? | Concorrência exige sincronização. |
| Finance | Evidências → comparação determinística de cenários | Custo com premissas de datas e alocação | Onde nasce o atraso do cliente? | LLM não substitui cálculo econômico. |
| Challenger | Plano candidato → premissas questionadas | Safety stock e evidência insuficiente destacados | O plano é barato porque ignorou um risco? | Questionar agrega uma função distinta. |
| Recomendação e aprovação | Prosa → contrato validado → decisão humana | Schema válido não implica ação autorizada | Quem assume a decisão? | Recomendação não é execução. |

## Resultado e perguntas finais

Finance compara A=23.500, B=20.250, C=18.000 e D=12.500 BRL incrementais. Challenger rejeita C por
romper o piso de Campinas. D é recomendado com atraso de três dias para CO-003 e zero para Atlas.
A solicitação termina pendente de aprovação humana, sem ações. B elimina atrasos a custo maior:
“Se relacionamento com o cliente tiver outro peso, você escolheria D?”

O cálculo não afirma impacto real ocorrido. Premissas de capacidade, disponibilidade e custos
continuam exigindo confirmação. `confidence=0.65` não é probabilidade calibrada.

## Comparação Git para revisão e reprodução

A tag original não foi movida. O start revisado aprovado é o commit `171c324`.

```bash
git status --short
git diff 171c324..HEAD -- src/control_tower
git diff lesson-01-start..HEAD -- src/control_tower labs docs/course
```

O primeiro diff isola o complete commitado; o segundo inclui correções aprovadas do start.
Use a tag lesson-01-complete para reproduzir esta entrega. Alunos observam e reproduzem;
nenhuma implementação é solicitada durante a aula.
