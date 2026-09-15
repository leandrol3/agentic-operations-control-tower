# Agentic Operations Control Tower

Laboratório oficial de **Multi-Agent Systems, Deployment, and Scaling**, MBA em AI Engineering &
Multi-Agents — professor Leandro Lopes. Disciplina de 16 horas, em quatro aulas de quatro horas.
O professor implementa e demonstra; alunos observam decisões, comportamento e trade-offs.
Os comandos permitem reprodução posterior, sem exercícios de programação durante a aula.

**Estado atual: candidato `lesson-01-complete`, em revisão local.** Não há tag complete.
A tag publicada `lesson-01-start` permanece intacta. O start revisado aprovado está em `171c324`;
o candidato está na branch local `codex/lesson-01-complete`, ainda não publicada.

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

Para esta revisão, use o checkout local existente:

```bash
cd "/Users/leandrolopes/Documents/ChatGPT/Disciplina Mult-Agents/agentic-operations-control-tower"
git switch codex/lesson-01-complete
uv python install 3.12
uv sync --locked
cp .env.example .env
uv run pytest -q
uv run control-tower smoke
uv run control-tower run INCIDENT-001
```

Copie `.env.example` apenas se ainda não tiver `.env`; preserve sua configuração existente.
PowerShell: `Copy-Item .env.example .env`. Não precisa ativar o ambiente virtual.
Para alunos em outra máquina, após publicação da branch candidata:

```bash
git clone https://github.com/leandrol3/agentic-operations-control-tower.git
cd agentic-operations-control-tower
git switch codex/lesson-01-complete
uv sync --locked
```

A branch não estará no clone remoto até ser publicada. Para a versão start já publicada, use
`git checkout lesson-01-start`; nessa versão ainda não existe `run`.

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
├── scenarios.py / presentation.py
├── agents/{specialists,supervisor,finance,challenger}.py
└── graph/{state,workflow}.py
data/ / incidents/ / tests/ / docs/ / labs/
```

## Configuração e recursos

`.env` usa `LLM_MODE=mock`; variável de ambiente tem precedência. `LLM_MODE=openai` é rejeitado
explicitamente: provider real foi adiado nesta etapa. Nenhuma chave é necessária.
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
| Start revisado (171c324) | Aprovado, commit local |
| lesson-01-complete | Candidato local em revisão, sem tag |
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
- OpenAI rejeitado: ajuste `.env` e variável de ambiente para `LLM_MODE=mock`.
- Erro de instalação: confira conexão/proxy; não desabilite TLS.
- Smoke falha: confira o fixture oficial. Doctor pode aceitar um subconjunto válido que não atende à demo.
- `run` bloqueia: leia o especialista/erro ou o relatório do Challenger; não existe fallback de decisão inventada.
- Mais lento no primeiro comando: importação de dependências também custa tempo; não comparar partida fria com quente.
- Branch/tag não encontrada: diferencie candidato local de versão publicada.
- Teste falha: preserve a saída completa, rode doctor e confira `git status`.

Nunca comite `.env`, tokens ou chaves.
