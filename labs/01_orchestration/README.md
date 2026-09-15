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

**Depois, alvo da progressão da Aula 1 (ainda não implementado):**

```text
Incidente → Supervisor → estado compartilhado
                         ├─ Supply ──────┐
                         ├─ Production ──┼→ consolidação → Finance → Challenger
                         └─ Logistics ───┘                            ↓
                                             recomendação → aprovação humana
```

A introdução de LangGraph e seus nós será realizada pelo professor. O start já contém o boilerplate:
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

## O que observar na progressão posterior

Esta tabela descreve a demonstração futura, sem atribuir outputs inexistentes ao start.

| Conceito | Antes → depois | Evidência a observar | Pergunta | Aprendizado |
|---|---|---|---|---|
| Shared state e especialistas | Saídas isoladas → evidências por responsabilidade | Cada especialista escreve sua parte do estado | Quem pode sobrescrever qual informação? | Estado é contrato de coordenação. |
| Supervisor e LangGraph | Chamadas manuais → plano e transições explícitas | Especialistas selecionados e transições visíveis | Quem decide e como encerra? | Coordenação precisa de limites. |
| Paralelismo e consolidação | Investigação sequencial → ramos independentes e junção | Resultados reunidos antes de Finance | O que acontece se um ramo faltar? | Concorrência exige sincronização. |
| Finance | Evidências → comparação determinística de cenários | Custo com premissas de datas e alocação | Onde nasce o atraso do cliente? | LLM não substitui cálculo econômico. |
| Challenger | Plano candidato → premissas questionadas | Safety stock e evidência insuficiente destacados | O plano é barato porque ignorou um risco? | Questionar agrega uma função distinta. |
| Recomendação e aprovação | Prosa → contrato validado → decisão humana | Schema válido não implica ação autorizada | Quem assume a decisão? | Recomendação não é execução. |

## Comparação Git para revisão e reprodução

A tag original não foi movida. Nesta revisão local:

```bash
git status --short
git diff lesson-01-start -- src/control_tower labs docs/course
```

O comando inclui alterações em arquivos rastreados; arquivos novos aparecem no status e devem ser
abertos diretamente (como o runbook e smoke.py) até serem commitados.
Quando o professor aprovar e publicar `lesson-01-complete`, será possível comparar os dois estados:

```bash
git diff lesson-01-start..lesson-01-complete -- src/control_tower
```

Essa última comparação ainda não está disponível. Nenhuma implementação é solicitada ao aluno.
