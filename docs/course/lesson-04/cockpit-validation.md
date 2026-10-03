# Relatório de entrega — lesson-04-cockpit

Data: 03/10/2026. **Candidato implementado para revisão do professor. Sem ACT autônomo.**
[Runbook completo: preparação, 18 minutos de demonstração, comandos e fallbacks](../lesson-04-cockpit-runbook.md).

## A. Baseline

- Branch inicial: `codex/lesson-04-complete`.
- Commit inicial: `f8206ce5f1fb468bd8eed4b662db954d83e2778c`.
- Working tree inicialmente limpa; inspeção do core, API, Registry, economics/quality, store, Compose e materiais antes da implementação.
- Suíte padrão: **480 passed, 21 skipped em 14,62 s**.
- Suíte com integrações PostgreSQL/Redis/tracing habilitadas: **501 passed, 0 skipped em 19,52 s**.
- [Log do baseline completo](cockpit-captures/baseline.txt).

## B. Arquitetura entregue

- **Frontend:** Next.js 16.3.8, React 19, TypeScript, Tailwind, Radix/CVA e Recharts, separado em `web/`.
  A primitiva de botão segue o estilo shadcn/ui; não foi importado um catálogo inteiro de componentes.
- **Backend:** pacote aditivo `control_tower.cockpit`; usa ControlPlane, Registry, economics, quality e store existentes.
- **Maestro:** serviço de síntese estruturada; recebe fatos de tools internas e somente conhecimento aprovado da fonte selecionada.
- **Segundo Cérebro:** Markdown + YAML frontmatter + links; snapshots de proveniência e planos em arquivos; Git manual.
- **Learning Loop:** representação assistida de observação → medição → interpretação → proposta → revisão → memória.
- **Runtime empresarial:** mesmo LangGraph, tasks, tools determinísticas, Redis, workers, PostgreSQL e tracing das aulas anteriores.
- **Infra nova:** somente container `cockpit`. Nada de banco vetorial, banco de grafo ou serviço de routing.

Não há cálculo de attainment, custo, SLO, regras de decisão ou autorização no browser.
As condições de interface apenas apresentam estados e habilitam formulários; a API valida novamente cada ação.

## C. UI e experiência

14 áreas: Visão Geral, Agentes/360, Metas, Operações, Qualidade, Economia & Valor, Decisões,
Alertas, Lifecycle, Maestro, Segundo Cérebro, Learning Loop, Configurações e Relatórios.

Uma rota principal com painéis; proxy em `/api/[...path]`. Componentes compartilhados:
Button, Empty, Badge, Panel, Facts, Decision, KnowledgeGraph e Modal com foco/teclado.
Loading, erro recuperável e vazio são explícitos. Fonte e modo do serviço ficam visíveis.

Capturas verificadas:

- [Visão Geral 1440×900](cockpit-captures/overview-1440.png).
- [Visão Geral 1920×1080, página completa](cockpit-captures/overview-1920.png).
- [Supply: meta 90%, atual 74%, gap −16 p.p.](cockpit-captures/supply-goals-1440.png).
- [Maestro, evidências e staffs](cockpit-captures/maestro-1440.png).
- [Segundo Cérebro, grafo e feed após ensaio](cockpit-captures/knowledge-1440.png).
- [Learning Loop e arco das quatro aulas](cockpit-captures/learning-loop-1440.png).

As capturas de testes mostram registros sintéticos do ensaio. O estado inicial entregue foi recomposto:
3 referências curadas, 1 candidato pendente e 1 plano mock. O seed foi executado duas vezes sem duplicar esse estado.

## D. Maestro

### Fontes e tools

`get_agent`, `get_agent_goals`, `get_goal_measurements`, `get_agent_quality`, `get_agent_economics`,
`get_agent_business_value`, `get_agent_lifecycle`, `get_agent_slos`, `get_agent_recommendations`,
`get_agent_executions`, `get_workforce`, `search_knowledge`, `get_knowledge_item`.

O Maestro não chama SQL diretamente. O service layer prepara os fatos antes da chamada ao modelo.
Essas são tools internas determinísticas de consulta; não um agente que escolhe executar ações arbitrárias.
O modelo seleciona referências e sintetiza o plano, com whitelist de IDs.

### Contrato e limites

`PlanDraft` é o output Pydantic do provider; o backend constrói `ImprovementPlan` com identidade,
fontes, staffs, status `proposed` e `requires_human_approval=true`. O modelo não controla aprovação.
Prompt exige pt-BR, fatos versus hipóteses, fontes, justificativa curta, sem chain-of-thought.
Reforça que degradação não mede correção semântica, cobertura não comprova disponibilidade e custo não prova valor.

Exemplo mock:

> Suprimentos tem meta de 90% e resultado 74%. No cenário didático, 13 de 50 observações têm
> evidências alternativas incompletas. Isso exige investigação, não comprova causa raiz.

Plano: revisar evidências, considerar estoque de segurança/fornecedor/transporte, preparar avaliação,
comparar antes/depois e pedir revisão humana. Staffs são metadata conceitual.

### OpenAI real

Foram executadas chamadas reais com **gpt-4.1-mini**, em diretório temporário e com dados didáticos.
O cockpit permaneceu em mock. Chave não foi impressa nem versionada.

- Primeiro Maestro: 10,08 s, 8 referências, plano proposto com aprovação obrigatória.
- Knowledge Compiler: 5,66 s, 7 referências, candidato `pending_review`.
- A revisão humana do ensaio identificou uma hipótese semântica pouco delimitada no primeiro diagnóstico.
  O prompt foi reforçado. Uma resposta subsequente foi rejeitada pela validação, sem plano persistido
  ([registro da rejeição](cockpit-captures/openai-maestro-rejected.json)); o motivo detalhado dessa chamada não foi capturado.
  Uma nova solicitação manual produziu plano válido em **5,10 s**, com **7 referências**, observação e hipótese separadas,
  mantendo explícito que degradação não mede correção semântica. Veja [síntese final](cockpit-captures/openai-maestro-recheck.json).
  Não foi adicionado retry automático nem contorno da validação.
- [Primeiro smoke real](cockpit-captures/openai.json) preservado para transparência, sem apresentar schema válido como prova de verdade.

As durações são observações deste ensaio, não garantias de latência. Não foi criado sistema de contabilização
para essas chamadas; custos do Maestro/Compiler não entram nos totais históricos do workflow.

## E. Segundo Cérebro

```text
knowledge/
├── README.md
├── index.md
├── schema/knowledge-contract.md
├── raw/executions/*.json
├── plans/*.json
└── wiki/
    ├── index.md
    ├── entities/entity-material-m42.md
    ├── lessons/lesson-safety-stock.md
    ├── lessons/knowledge-<id>.md
    └── patterns/pattern-evidence-review.md
```

Tipos: entity, decision, lesson, pattern. Estados previstos: draft, pending_review, approved, rejected, superseded.
`decisions/` surge quando esse tipo é produzido; não há ontologia ou diretórios vazios artificiais.

Cada documento registra ID, título, resumo, tags, execução/incidente de origem, fonte, evidências,
relações, timestamps, gerador, owner, provenance, evidence_level e revisão humana.
A interface não executa HTML do Markdown. Conteúdo recebido é dado, não instrução.

Seeds aprovados são curadoria didática pré-preparada. O Compiler só cria pendentes; aprovação/rejeição
exige nome, nota e confirmação. Arquivos aprovados não são substituídos por novas extrações.
Escrita atômica por arquivo e lock local; sem commit automático. Retrieval usa apenas aprovados da mesma fonte.

## F. Knowledge Compiler

1. Lê execução concluída, resultado público, quality e eventos do service layer.
2. Compõe fatos identificados: proposta registrada, aprovação pendente, limites de outcome, capability de estoque e eventos.
3. Fornece ao provider fatos e relações aprovadas possíveis.
4. Valida `KnowledgeDraft`, idioma declarado pt-BR, referências existentes e relações permitidas.
5. Backend vincula execução, fonte, gerador, timestamps e status; reproduz observações literalmente.
6. Inferência permanece seção explícita, dependente de revisão.
7. Persiste candidato Markdown e snapshot bruto sanitizado; humano aprova ou rejeita.

Exemplo mock: **Considerar estoque de segurança antes de propor transferências**.
Não afirma transferência executada, savings ou benefício comprovado.
Output real pode sugerir outra lição sustentada pelo contexto; o título mock não é prometido para OpenAI.

## G. APIs

As APIs anteriores permanecem. Adições:

- GET `/cockpit/overview`, `/cockpit/reports/summary`, `/cockpit/alerts`.
- GET `/cockpit/executions/{uuid}`.
- POST `/maestro/chat`.
- GET `/knowledge`, `/knowledge/{id}`.
- POST `/knowledge/extract/{uuid}`.
- POST `/knowledge/{id}/approve`, `/knowledge/{id}/reject`.

Parâmetro `source=didactic|durable`. Busca de conhecimento aceita `q` e `status`.
Contratos Maestro/Knowledge aparecem no Swagger. Erros de infraestrutura são sanitizados.
Ausência de chave em OpenAI produz erro explícito `OPENAI_API_KEY`; não há fallback silencioso para mock.
Exemplos copiáveis no [runbook](../lesson-04-cockpit-runbook.md#7-apis-e-exemplos-pequenos).

## H. Demo e resultado operacional

```bash
uv sync --locked --extra lesson04
export LLM_MODE=mock
export CONTROL_TOWER_PRICING_FILE=config/lesson04-pricing.json
export CONTROL_PLANE_CONFIG_FILE=config/lesson04-control-plane.json
uv run --extra lesson04 python scripts/seed_cockpit.py
./scripts/cockpit.sh up -d --build --wait
uv run --extra lesson04 python scripts/demo_cockpit.py
```

Sequência de **18 minutos estimados de condução**, com build/instalação fora da aula:

| Bloco | Tempo |
|---|---:|
| Visão Geral e workforce | 2 min |
| Agent 360 e meta 90% × 74% | 3 min |
| Quality / Economics / SLO / Intervir | 2 min |
| Maestro e plano com staffs | 3 min |
| Execução → extrair → revisar → aprovar | 4 min |
| Reutilização e separação de fontes | 2 min |
| Learning Loop e encerramento | 2 min |

Distinguir: 50 observações sintéticas Supply; janelas técnicas dos demais papéis; 6 execuções ilustrativas.
Não foram fundidas artificialmente essas populações. Histórico persistido é outra fonte e não recebe seeds didáticos.

Além das fixtures, houve uma execução nova real nos serviços locais, **em mock**:

```text
execution_id: 030bd41a-396a-43ff-a91a-6aab383687d4
status: completed
worker: worker-b
duration_ms: 27.435
execution_events: 21
trace_id: b4d4473d259302f9c9511f3d09dee99d
outcome: recommendation
approval: pending
actions_executed: false
knowledge candidate: pending_review
usage/cost: indisponíveis, sem tokens inventados
```

Os artefatos de ensaio foram arquivados fora do conjunto de seed; a execução durável permanece no PostgreSQL.
A aprovação operacional não foi modificada. O cockpit ficou disponível localmente para revisão.

## I. Testes e evidências

| Verificação | Resultado |
|---|---|
| Regressão Python completa, com todas as integrações | **532 passed, 0 skipped, 20,80 s** |
| Novos testes Python do cockpit | **31** |
| Regressão anterior preservada | **501 testes** |
| Playwright: navegação, 360, recomendações, Maestro, extração/revisão, grafo, loading, erro e vazio | **5 passed, 3,7 s** |
| TypeScript | Sem erros |
| Build Next.js e Compose | Concluídos; serviços saudáveis |
| Smoke CLI mock | `status=ok`, 12 checks |
| Mock offline | Testes sem provider e seed sem dependência de banco/rede |
| OpenAI parser substituto | Contratos Pydantic para Maestro e Compiler, sem chamadas nos testes unitários |
| OpenAI real | Maestro e Compiler estruturados, sem aprovação automática |
| Validação visual | 1440×900 e 1920×1080, sem overflow horizontal |
| Git diff check | Sem erros de whitespace |

[Log da regressão](cockpit-captures/pytest.txt) · [Resultados Playwright](cockpit-captures/playwright.json).
O runbook contém todos os comandos para repetir as verificações. As capturas são evidência de ensaio,
não monitoramento contínuo. Os testes de UI aprovam apenas candidato sintético identificado como teste.

## J. Limitações e trade-offs

- LAB local, sem IAM/RBAC, isolamento multitenant ou auditoria inviolável. Nome do revisor é autodeclarado.
- Filesystem/Git atende legibilidade e ensino; não é storage distribuído. Revisão não faz commit/push.
- Sem vetor, banco de grafo, ontologia completa, engine de políticas ou roteamento sofisticado.
- “OKF” é perfil local Markdown/frontmatter/links, não certificação de uma especificação externa.
- Validação estrutural e de IDs não certifica toda inferência textual; por isso revisão semântica continua humana.
- Conhecimento recuperado melhora o contexto do Maestro. Não há injeção automática no próximo workflow nem treinamento de pesos.
- Staffs conceituais, planos não executáveis; estados futuros existem no contrato, sem motor de aprovação de planos.
- Horizonte operacional limitado a 30 registros e grafo visual a 12 itens; busca textual simples.
- Sem savings inventados, cached tokens não instrumentados, custos do Maestro/Compiler ainda fora da projeção histórica.
- Portas localhost; não foi preparada publicação pública. SDK chama OpenAI com timeout e sem retry oculto nessa nova camada.
- UI carrega snapshot único para simplicidade; não há tempo real/websocket nem paginação empresarial.

## K. Git e preservação

- Branch: `codex/lesson-04-cockpit`, baseada em `f8206ce`.
- Commit da entrega: consultar `git log -1 --oneline`; este relatório faz parte da entrega local.
- Sem push. Sem criação ou movimentação de tags. `main` e branches dos checkpoints não foram alteradas.
- Alterações no core limitadas ao registro aditivo das rotas, versão da API, dependência YAML
  e reconhecimento aditivo da métrica didática de cobertura. Grafo, tasks, tools e store empresarial preservados.
- Labels dos scripts da Aula 4 foram traduzidos na apresentação; IDs/enums/contratos permanecem compatíveis.
- `scripts/demo_lesson04.py:registry` mantém a assinatura/saída programática legada por compatibilidade com os testes anteriores;
  a CLI pública seleciona explicitamente a apresentação em português.
- Novos arquivos se concentram em `web/`, `src/control_tower/cockpit/`, `knowledge/`, fixture Supply,
  testes, launcher, seed, helper, runbook e evidências deste relatório.

**Parecer:** pronto para revisão pedagógica do professor. Nenhuma autorização de ACT, deploy ou publicação foi incorporada.
