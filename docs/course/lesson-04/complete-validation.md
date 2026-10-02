# lesson-04-complete — relatório do candidato

Ensaio em 2026-10-02. Resultado: candidato implementado e validado; parar para revisão.
Escopo: **COLLECT → INTERPRET → RECOMMEND**, sem ACT.

## A. Baseline

- Branch inicial: `codex/lesson-04-start`.
- Commit inicial: `c00594e` (Git limpo antes de qualquer alteração).
- Suíte default anterior: **397 passed, 20 skipped em 14.01 s**.
- Toda a suíte anterior com integrações: **417 passed, 0 skipped em 17.96 s**.
- Branch de trabalho criada: `codex/lesson-04-complete`.
- Plano apresentado após baseline/inspeção: coleta limitada, interpretação determinística,
  máquina pura de lifecycle, recomendações read-only, APIs, fixtures e cinco demos.

## B. Arquitetura implementada

```text
Registry + Goals + Lifecycle             PostgreSQL (durable executions/events)
                    ↓                    ↓
                       COLLECT (snapshot)
                              ↓
          INTERPRET: goals/gaps, SLO, trends, value, triggers
                              ↓
             RECOMMEND: ordered deterministic rules
                              ↓
                   read-only API / textual cockpit
                              ↓
                    human review (no ACT)
```

Módulos novos em `src/control_tower/control_plane/`:

| Módulo | Responsabilidade |
|---|---|
| contracts.py | Contratos Pydantic públicos e enums |
| configuration.py | Thresholds didáticos explícitos e validados |
| collection.py | Eventos de etapa, qualidade contextual e custo atribuído ao papel |
| interpretation.py | GoalMeasurement, SLO, tendências, valor parcial e triggers |
| lifecycle.py | Allowed transitions, validação e autorização explícita; função pura |
| decision_engine.py | Precedência de regras, evidence, priority, ID determinístico |
| service.py | ControlPlane.evaluate: Collect → Interpret → Recommend |
| api.py | Três GETs, erros sanitizados, nenhuma mutação |
| demo_fixture.py | Sinais sintéticos para ensaio offline; nunca usado pela API |

Extensão pequena de `runtime/store.py`: últimas execuções terminais por modo, um snapshot
REPEATABLE READ READ ONLY, seleção limitada e ordenação creation DESC/UUID DESC.
Não altera o store da Aula 2. Não há migration nem tabela nova.

Runtime não chama Control Plane e Control Plane não chama LangGraph. Snapshot contém duas
janelas de três execuções; mínimo três amostras completas por dimensão. Custos são atribuídos
por agent_id nos eventos LLM, não por divisão do custo total. Modelos diferentes invalidam
comparação de custo. Registry atual e coorte histórica ficam separados; `cohort_model` explícito.

## C. Modelos e significado

- **GoalMeasurement:** target, actual, gap assinado, attainment, janela, status, evidence e measured_at.
  ON_TARGET/AT_RISK/OFF_TARGET/UNKNOWN. Mede conclusão técnica, não correção semântica.
- **AgentSLO / SLOEvaluation:** >= e <=, target, margem, unidade, severidade, evidência e
  PASS/WARN/VIOLATION/UNKNOWN. Thresholds em `config/lesson04-control-plane.json`.
- **BusinessValueAssessment:** proposta industrial (BRL), tempo de runtime até proposta (ms,
  proxy parcial), valor realizado UNKNOWN. Não usa avoided_penalty como dinheiro efetivamente salvo.
- **Lifecycle:** enum existente preservado; transições explícitas e RETIRED terminal.
  Função pura exige autorização humana; não grava Registry nem age sobre workers.
- **LifecycleTrigger:** goal miss, SLO violation, quality degradation contextual, cost increase,
  persistent underperformance. Sinal apenas.
- **ControlPlaneRecommendation:** ID estável, action, priority, summary, reason, evidence,
  current/suggested lifecycle, requires_human_approval=true e generated_at. Sem confidence inventado.
- **AgentControlPlaneView:** Registry, metas, SLOs, quality/economics/latency, tendências,
  valor parcial, triggers e recomendação opcional. Inclui configuração/pricing e data de referência.

Unknown não é zero: falta de evento, histórico truncado, janela insuficiente, usage parcial,
Finance/mock sem LLM ou preço/modelo desconhecido não são preenchidos artificialmente.
`workflow_degraded_rate` mede outcomes não normais dos workflows associados, não culpa individual.

## D. Decision Engine e thresholds

Config: `lesson04-didactic-v1`, source=didactic_configured_example.

| Sinal | Threshold inicial |
|---|---|
| Meta de conclusão | target do Registry=100%; warning gap=5 pontos |
| SLO de conclusão | >=90%; margem WARN=5 pontos |
| Stage latency p95 | <=2000 ms; margem WARN=200 ms |
| Mean recorded role LLM cost | <=USD 0.01; margem WARN=USD 0.002 |
| Workflow degraded rate | <=10%; margem WARN=5 pontos |
| Tendência estável | variação relativa até 5% |
| Persistência severa | conclusão <50% em ambas as janelas |
| Revisão de alta severidade | duas ou mais violações high/critical |

Precedência (primeira regra aplicável vence):

1. Persistência severa em ACTIVE → PAUSE / CRITICAL, sugere PAUSED.
2. Múltiplas violações high → REVIEW / HIGH, sugere REVIEW.
3. Workflow degradation acima do limite → INTERVENE / HIGH, sugere REVIEW.
4. Meta off target e custo crescente → OPTIMIZE / MEDIUM, sem mudança de lifecycle.
5. Outras violações/goal miss → REVIEW / MEDIUM.
6. Todas as dimensões aceitáveis, metas on target, tendências estáveis, evidência/modelo
   compatíveis → SCALE / LOW: avaliar experimento controlado, condicionado a demanda/capacidade/quota.
7. Sem suporte suficiente → recommendation=null e motivo explícito.

RETIRE está no enum, sem regra forçada. Agentes fora de ACTIVE não recebem proposta automática
de retomada/retirada. Business Value ainda não sustenta regra monetária de ROI/retirada.
IDs incluem evidência, configuração, estado e referência de pricing; generated_at não altera ID.
Toda recomendação acionável carrega evidence e aprovação humana. Nenhuma executa transition.

## E. APIs reais validadas

- GET `/control-plane/agents?mode=mock`: overview, sete agentes.
- GET `/control-plane/agents/{agent_id}?mode=mock`: projeção consolidada.
- GET `/control-plane/recommendations?mode=mock`: apenas recomendações suportadas.
- `mode=openai` apenas lê história existente; não chama provider.
- 404 agente desconhecido, 422 modo inválido, 503 store/config indisponível, 405 POST na rota GET.

Trecho real de Logistics após seis workflows mock:

```json
{
  "mode": "mock",
  "sample_count": 3,
  "pricing_version": "openai-public-pricing-2026-10-02",
  "pricing_reference_date": "2026-10-02",
  "recommendation": null
}
```

Metas ON_TARGET, Registry ACTIVE, custo UNKNOWN, lista de recomendações vazia.
Isso é resultado correto, não erro: mock não mede inference e não justifica SCALE.
A consulta histórica openai também respondeu (3 amostras atuais), sem nova inferência.

Endpoints anteriores conferidos ao vivo: /health alive; /ready ready com Redis/PostgreSQL ok;
GET /incidents; Finance deterministic; Quality approval pending; Economics mock_no_usage.
HTTP/MCP SDK executado em três rodadas: seis workflows mock concluídos, mesma identidade
reutilizada corretamente, resultado público igual, approval pending, actions=false.

## F. Demos reproduzidas

Na raiz do repositório, após instalar o extra lesson04:

```bash
uv run --extra lesson04 python scripts/demo_lesson04_complete.py --fixture stable --agent logistics --section goals
uv run --extra lesson04 python scripts/demo_lesson04_complete.py --fixture cost --agent logistics --section slo
uv run --extra lesson04 python scripts/demo_lesson04_complete.py --fixture review --agent logistics --section lifecycle
uv run --extra lesson04 python scripts/demo_lesson04_complete.py --fixture optimize --agent logistics --section recommendation
uv run --extra lesson04 python scripts/demo_lesson04_complete.py --fixture optimize --agent logistics --section pipeline
uv run --extra lesson04 python scripts/demo_lesson04_complete.py --live --mode mock
```

| Demonstração | Cálculo/CLI observado | Bloco didático |
|---|---:|---:|
| Goal Measurement | 0.196 s | 15 min |
| SLO Violation | 0.137 s | 15 min |
| Lifecycle | 0.145 s | 15 min |
| Recommendation | 0.134 s | 20 min |
| Pipeline | 0.142 s | 15 min |

Tempos locais indicativos, não benchmark ou SLO. Casos extras INTERVENE/PAUSE também ensaiados.
Fixtures totalmente offline; dados explicitamente sintéticos, sem escrita no banco.
Mesmos contratos/coleta/interpretação/regras usados no caminho durável.

Exemplo da fixture optimize (não medição real):

```text
SOURCE: DIDACTIC FIXTURE
COLLECT: 3 current + 3 previous executions, logistics, synthetic role usage
INTERPRET:
  target=100%; actual=66.666667%; gap=-33.333333%
  cost: USD 0.00056 -> USD 0.02016; trend=degrading
  latency p95=100 ms; workflow quality=unknown
RECOMMEND: OPTIMIZE / MEDIUM / approval=True
Lifecycle: ACTIVE (unchanged)
```

A UI distingue seções para revelar os conceitos progressivamente. O pipeline detalha reason,
evidence/unidades/escopo/IDs e pricing. Business context=BRL 12500 propostos; realized value UNKNOWN.
Runbook fecha 240 minutos incluindo start, com 75 minutos explícitos de teoria/contexto.

## G. Testes finais

| Execução | Resultado |
|---|---|
| Suíte default final | **480 passed, 21 skipped em 16.48 s** |
| Suíte completa final | **501 passed, 0 skipped em 21.03 s** |
| Casos novos | **84: 83 unitários/contratos + 1 integração PostgreSQL** |
| Aula 1 smoke mock | status ok; 13 checks |
| Demos de fixtures e cockpit live | passaram |
| HTTP/MCP distribuído | passou |
| Verificação sintática de comandos/runbook e diff | passou |

Cobertura nova: metas/gap/attainment/at risk/unknown, limites >=/<= com quatro estados SLO,
nearest-rank p95, tendências, custos sem usage, modelos diferentes, fontes, valor parcial,
36 combinações de lifecycle, autorização, cinco ações, precedence/persistência, evidence/priority,
ID estável, ausência de ACT/graph invocation, spans, API pública e erros sanitizados.

Integração nova: schema isolado, eventos gerados por workflow mock real, janelas limitadas,
idempotência, coortes, comparação de banco antes/depois da avaliação comprovando nenhuma escrita.
Todos os testes anteriores preservados; nenhum teste antigo alterado para acomodar o complete.
Regressões Aulas 2/3/4 e tracing habilitadas juntas. Nenhuma chamada OpenAI nos testes/ensaio.

## H. Limitações e decisões técnicas

- Núcleo pequeno rule-based; métricas atuais são metas técnicas observáveis, não qualidade semântica.
- Janelas de 3 são didáticas; p95 com 3 equivale ao máximo. Sem forecasting ou estatística robusta.
- Cost é estimativa de recorded role usage, não agent/workflow total, invoice ou Business Value.
- Business Value parcial: proposta e proxy de tempo não comprovam savings, aceite, impacto ou ROI.
- Lifecycle é state machine pura validada; não há persistência/histórico de transições nem API de ACT.
- Recomendações são projeções atuais, não workflow de aprovação persistido. Aprovação exigida não
  significa que uma autorização já aconteceu. Não resume agentes pausados nem força RETIRE.
- SCALE é elegibilidade para revisão humana de experimento, não prova de demanda/capacidade.
- Sem auto-remediation, auto-modify, model switching, prompt rewriting, judge sofisticado,
  enterprise governance/RBAC, dashboard SPA, Maestro, Second Brain ou Learning Loop implementados.
- Maestro, Second Brain e Learning Loop aparecem somente no fechamento conceitual.

## I. Git e arquivos

Branch `codex/lesson-04-complete`, novo commit local sobre c00594e (`git log -1 --oneline`).
Branch `codex/lesson-04-start` permanece exatamente em c00594e. Sem push, sem criação/movimento de tags.
Stack temporária encerrada sem remover volumes. Parar para revisão.

Arquivos novos:

```text
compose.lesson04-complete.yaml
config/lesson04-control-plane.json
fixtures/lesson04/control-plane.json
scripts/demo_lesson04_complete.py
src/control_tower/control_plane/
  api.py
  collection.py
  configuration.py
  contracts.py
  decision_engine.py
  demo_fixture.py
  interpretation.py
  lifecycle.py
  service.py
tests/test_lesson04_complete.py
tests/integration/test_lesson04_complete_store.py
docs/course/lesson-04-complete-runbook.md
docs/course/lesson-04/complete-validation.md
```

Arquivos existentes alterados: AGENTS.md, README.md, docs/course/PROJECT_CONTEXT.md (escopo/docs);
api/app.py (registro de rotas e versão); runtime/store.py (leitura snapshot).
Core, agents, tools, LangGraph, task/store da Aula 2, pricing e contratos do start preservados.
Dependências e lockfile intactos. Override Compose usa os mesmos serviços com nova imagem/config.
