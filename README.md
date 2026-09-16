# Agentic Operations Control Tower

Laboratório oficial de **Multi-Agent Systems, Deployment, and Scaling**, MBA em AI Engineering &
Multi-Agents — professor Leandro Lopes. Disciplina de 16 horas, em quatro aulas de quatro horas.
O professor contextualiza, explica teoria e demonstra partes selecionadas; alunos observam decisões,
comportamento e trade-offs. Não há live coding nem aula de sintaxe LangGraph.
Os comandos permitem reprodução posterior, sem exercícios de programação durante a aula.

**Estado atual: `lesson-01-complete`, aprovado pelo professor.**
A tag `lesson-01-start` permanece intacta. O start revisado aprovado está em `171c324`;
a tag `lesson-01-complete` identifica a conclusão da Aula 1.
Revisão com mock + OpenAI disponível na `main`; tags anteriores preservadas.

## Para o professor — revisão de experiência de aula

**Novas views e materiais disponíveis na `main`.** As tags existentes permanecem intactas.
Os comandos de instalação na tag abaixo reproduzem a entrega técnica anterior;
para usar os materiais novos, atualize seu checkout da `main`.

```bash
git switch main
git pull --ff-only
uv sync --locked
uv run control-tower show INCIDENT-001 summary
uv run control-tower show INCIDENT-001 state
uv run control-tower show INCIDENT-001 specialists
uv run control-tower show INCIDENT-001 coordination --demo-delay-ms 500
uv run control-tower show INCIDENT-001 coordination --sequential --demo-delay-ms 500
uv run control-tower show INCIDENT-001 scenarios
uv run control-tower show INCIDENT-001 challenger
uv run control-tower show INCIDENT-001 recommendation
```

Abrir [o material visual offline](docs/course/classroom/index.html) por duplo clique no arquivo local.
Ele reúne contexto, teoria, timeline, [diagrama SVG pronto](docs/course/classroom/graph.svg), quadros e
[snippets de 10–23 linhas](docs/course/classroom/snippets.md). Uma tela por conceito, sem serviços novos.
As telas HTML são fallbacks gravados, não uma execução da aplicação. Use CLI para a demonstração ao vivo.

Views cabem em até 20 linhas × 96 colunas. Summary/state/specialists/coordination param antes de Finance;
scenarios/challenger param antes de Recommendation. Scenarios usa a revisão existente para mostrar
admissibilidade, sem revelar sua seleção. Cada view executa o fixture novamente; não há sessão persistente.
O [runbook de 240 minutos](docs/course/lesson-01-runbook.md) reserva os primeiros 70 minutos para contexto
e teoria. A nota de fixture incompleto dura até 3 minutos dentro de capabilities; não é bloco próprio.

`run`, JSON integral e Git diff permanecem disponíveis para preparação e estudo posterior.
Não projetar a saída completa nas primeiras demos. `mock` usa coordenação real e papéis determinísticos;
não existe raciocínio de LLM. Uma recomendação válida não é uma decisão autorizada.

## Proposta de valor e case

A NovaCore coordena fábricas, fornecedores e clientes B2B. Alpha atrasa M42 sete dias; três ordens
estão relacionadas ao material/planta. O sistema reúne evidências, compara cenários e prepara uma
recomendação rastreável para decisão humana. Relação não confirma atraso de cliente.

Antes: evento → pessoas → emails/planilhas → reuniões → decisão.
Depois: evento → investigação paralela → cenários → Challenger → recomendação → decisão humana.
A métrica de negócio é **Time-to-Decision**. Horas para minutos é objetivo ilustrativo, não benchmark.
A CLI mede apenas execução até a recomendação; a decisão humana permanece pendente.

## Arquitetura

```text
                       ┌─ Supply ──────┐
Incidente → Supervisor ├─ Production ──┼→ Consolidação → Finance → Challenger
                       └─ Logistics ───┘                             ↓
                                       Aprovação pendente ← Recommendation
```

Estado Pydantic compartilhado, canais separados por especialista, join explícito no LangGraph.
Tools acessam CSV/JSON; Finance usa cálculos determinísticos. Mock executa o grafo real sem LLM,
chave ou rede. Human Approval encerra em `awaiting_approval`; não há execução de ações.
Veja [arquitetura e diagrama](docs/architecture/README.md) e [premissas do case](docs/case/NOVACORE.md).

## Pré-requisitos e instalação

Git, Python 3.12 e [uv](https://docs.astral.sh/uv/getting-started/installation/).
Primeira instalação requer internet; depois o workflow mock funciona offline.

Para instalar e reproduzir o checkpoint aprovado:

```bash
git clone https://github.com/leandrol3/agentic-operations-control-tower.git
cd agentic-operations-control-tower
git checkout lesson-01-complete
uv python install 3.12
uv sync --locked
cp .env.example .env
uv run pytest -q
uv run control-tower smoke
uv run control-tower run INCIDENT-001
```

Em um clone existente, salve suas alterações e execute `git fetch --tags` antes do checkout.
Copie `.env.example` apenas se ainda não tiver `.env`; preserve sua configuração existente.
PowerShell: `Copy-Item .env.example .env`. Não precisa ativar o ambiente virtual.
Para reproduzir o início original da aula, use `git checkout lesson-01-start`; nessa versão não existe `run`.

## Demonstração — comandos prontos

```bash
uv run control-tower doctor
uv run control-tower incident
uv run control-tower tools
uv run control-tower smoke
uv run control-tower graph
uv run control-tower run INCIDENT-001
uv run control-tower run INCIDENT-001 --json
uv run control-tower run INCIDENT-001 --demo-delay-ms 500
uv run control-tower run INCIDENT-001 --sequential --demo-delay-ms 500
uv run control-tower run INCIDENT-001 --fail-specialist logistics
```

- `doctor`: carregamento, schemas e referências; três `related_orders`, `impact_status: not_assessed`.
- `tools`: evidencia relações e restrições; não simula cronograma.
- `smoke`: 12 verificações do fixture oficial; demanda 750, disponível 300, déficit 450;
  multa **hipotética** de CO-001 com sete dias de atraso = 140.000 BRL. Não é a multa do cenário A.
- `graph`: Mermaid derivado do grafo real, sem renderização ou rede.
- `run`: eventos de início/fim reais (ordem dos especialistas pode variar), resumo estável por papel,
  comparação A–D, Challenger, JSON de Recommendation e solicitação humana.
- `--json`: todo o estado validado em JSON, sem eventos ou tempos; resultado determinístico.
- `--demo-delay-ms`: espera artificial limitada a 0–2000 ms por especialista. Não simula desempenho real de LLM.
- `--sequential`: as mesmas funções com arestas sequenciais; mesma recomendação.
- `--fail-specialist`: Supply/Production/Logistics podem falhar deliberadamente; a junção bloqueia Finance.
  Saída **1** é esperada nessa demo. Erro de configuração/fixture: saída **2**. Sucesso: saída **0**.

### Resultado esperado de `run INCIDENT-001`

| Cenário | Total incremental BRL | Atrasos CO-001/002/003 | Revisão |
|---|---:|---|---|
| A — esperar Alpha | 23.500 | 0 / 4 / 3 | Admissível |
| B — Beta | 20.250 | 0 / 0 / 0 | Admissível |
| C — transferência expressa | 18.000 | 0 / 0 / 0 | Bloqueado: safety stock Campinas |
| D — transferência padrão + replanejamento | 12.500 | 0 / 0 / 3 | Menor custo admissível |

D é recomendado sob as premissas documentadas. Multa evitada versus A: 16.000 BRL; economia total:
11.000 BRL. `customer_delay_days=3` é o máximo entre clientes; Atlas tem atraso zero.
Challenger pede confirmação de disponibilidade, capacidade e custos ausentes. `confidence=0.65`
é marcador didático, não probabilidade calibrada. `approval_required=true`, status `pending`,
`actions_executed=false`. Não existe comando para aprovar ou executar compra/transferência.

[Exemplo completo gravado](docs/course/examples/incident-001-mock.txt) ·
[Estado JSON](docs/course/examples/incident-001-mock.json) ·
[Exemplo com falha](docs/course/examples/incident-001-failure.txt).

## Guias e organização

[Observation Guide](labs/01_orchestration/README.md) para alunos e
[runbook de quatro horas](docs/course/lesson-01-runbook.md) para o professor.
[Contexto permanente](docs/course/PROJECT_CONTEXT.md) e [validação](docs/course/VALIDATION.md).

```text
src/control_tower/
├── main.py / models.py / tools.py / smoke.py
├── scenarios.py / presentation.py / views.py / settings.py / llm.py
├── agents/{specialists,supervisor,finance,challenger,interpretation}.py
└── graph/{state,workflow}.py
data/ / incidents/ / tests/ / docs/ / labs/
```

## Configuração e recursos

.env usa `LLM_MODE=mock`; variável de ambiente tem precedência. Mock não exige chave.
A revisão na `main` adiciona `LLM_MODE=openai` ao mesmo grafo:

```bash
LLM_MODE=mock uv run control-tower show INCIDENT-001 llm-decisions
LLM_MODE=openai OPENAI_MODEL=gpt-4.1-mini uv run control-tower show INCIDENT-001 llm-decisions
LLM_MODE=openai uv run python scripts/compare_modes.py
```

Forneça `OPENAI_API_KEY` no ambiente ou `.env` ignorado; `.keys` na raiz do checkout também é aceito.
Para arquivo externo ao checkout, use `OPENAI_API_KEY_FILE=../.keys` (não há busca automática em pastas pais).
O arquivo aceita valor simples ou `OPENAI_API_KEY=...`; nunca o inclua no Git.
Modelo configurável por `OPENAI_MODEL`; padrão `gpt-4.1-mini`. Falta de chave é erro explícito.
**LLMs interpretam e julgam. Código determinístico mede e valida.**
Seis chamadas no fluxo OpenAI: Supervisor, três sínteses, Challenger e Recommendation.
Finance, evidências, políticas e aprovação obrigatória continuam determinísticos.
O LLM pode preferir outro cenário admissível; os valores de cada cenário são conferidos pelo código.
Falha/recusa da API bloqueia o fluxo; retorne explicitamente ao mock para o fallback.
Veja [fronteiras e comparação](docs/course/llm-modes.md) e o
[exemplo real gravado](docs/course/examples/incident-001-modes-comparison.txt). Esta revisão não altera as tags.
Python local, sem GPU, modelo local ou Docker. Planejamento conservador: 4 GB de RAM na máquina e
1 GB de disco livre; não são mínimos medidos. Testado em macOS ARM64/Apple Silicon; Windows/Linux
seguem comandos equivalentes, mas ainda não foram testados nesta entrega.

As dependências transitivas de LangGraph não ativam serviços. Tracing é desabilitado no workflow mock.
Estado só em memória; não há checkpoints persistentes ou retomada. Cada comando termina sozinho;
Ctrl+C interrompe. Eventos e erros ficam no terminal. Para guardar a execução: acrescente `> demo.txt`.

Para reinstalar, remova apenas o ambiente gerado na raiz do checkout:

```bash
rm -rf .venv
uv sync --locked
```

PowerShell: `Remove-Item -Recurse -Force .venv`. Não use `git clean -fdx` para evitar apagar `.env`.
Full Lab com Docker Desktop, API, Redis, PostgreSQL e workers chega nas aulas seguintes. Observabilidade,
load test k6 e simulador de falhas da Aula 4 ainda não existem. Não há endpoints para acessar agora.

## Comparar estados com Git

```bash
git status --short
git diff lesson-01-start..HEAD
git diff 171c324..HEAD -- src/control_tower
```

A primeira comparação inclui a correção pedagógica do start; a segunda isola a progressão complete.
Salve suas alterações antes de trocar de checkout. Tags deixam o Git em detached HEAD; use uma branch
própria caso queira experimentar depois. Não movemos tags aprovadas.

| Checkpoint | Estado |
|---|---|
| lesson-01-start | Tag original publicada e preservada |
| Start revisado (171c324) | Aprovado, incluído no histórico |
| lesson-01-complete | Aprovado, checkpoint de conclusão da Aula 1 |
| lesson-02-start / complete | Redis/Celery: futuro |
| lesson-03-start / complete | FastAPI/PostgreSQL/Docker: futuro |
| lesson-04-start / complete | Observabilidade/chaos/escala/FinOps: futuro |

Após criação/publicação das tags futuras: `git fetch --tags`, `git checkout lesson-02-start`,
`git diff lesson-02-start..lesson-02-complete`. Essas tags ainda não existem.

## Seis perguntas de engenharia

1. Who decides? Quem decide qual agente executa?
2. Where is the state? Onde está o estado?
3. What happens when it fails? O que ocorre quando algo falha?
4. Can I observe it? Conseguimos explicar a execução?
5. What does it cost? Quanto custa cada incidente?
6. Should this even be an agent? Deveria ser código determinístico?

## Troubleshooting

- `uv` não encontrado: reinicie o terminal e confira PATH após instalar.
- Python incompatível: `uv python install 3.12`, depois `uv sync --locked`.
- Dados ausentes: execute na raiz ou use `--root CAMINHO`.
- OpenAI indisponível: confira chave/modelo e acesso à API; `LLM_MODE=mock` é o fallback offline.
- Erro de instalação: confira conexão/proxy; não desabilite TLS.
- Smoke falha: confira o fixture oficial. Doctor pode aceitar um subconjunto válido que não atende à demo.
- `run` bloqueia: leia o especialista/erro ou o relatório do Challenger; não existe fallback de decisão inventada.
- Mais lento no primeiro comando: importação de dependências também custa tempo; não comparar partida fria com quente.
- Branch/tag não encontrada: execute `git fetch --tags` e confira `git tag --list`.
- Teste falha: preserve a saída completa, rode doctor e confira `git status`.

Nunca comite `.env`, tokens ou chaves.
