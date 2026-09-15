# Agentic Operations Control Tower

Laboratório oficial da disciplina **Multi-Agent Systems, Deployment, and Scaling**, MBA em
AI Engineering & Multi-Agents — professor Leandro Lopes.

**Checkpoint atual: `lesson-01-start`.** Base executável para construir a orquestração durante a aula.
O objetivo da disciplina é arquitetar, fazer deploy e escalar sistemas multiagente com robustez
operacional e eficiência de custo. Um único sistema evolui ao longo das quatro aulas.

## O case

A NovaCore Industries coordena fábricas, fornecedores e clientes B2B. Alpha atrasou M42 em sete dias;
três ordens estão afetadas, incluindo um cliente estratégico. Investigue estoque, alternativas e multas.

Antes: evento → pessoas → emails/planilhas → reuniões → decisão.
Depois: evento → especialistas em paralelo → cenários → revisão de risco → recomendação → decisão humana.
Proposta de valor: decisões coordenadas, contextualizadas e rastreáveis, com capacidade operacional ampliada.
**Time-to-Decision** é a métrica central. Horas para minutos é uma ilustração pedagógica, não benchmark.

## Arquitetura deste checkpoint

```text
CLI → Tools determinísticas → dados CSV/JSON
             ↓
       contratos Pydantic
```

Mock aqui significa execução offline determinística das capabilities. Ainda não há agentes, chamadas
LLM, escolha automática do plano ou ações operacionais. Os exercícios de agentes e grafo estão em
`src/control_tower/agents/` e `graph/`. A aprovação humana é obrigatória no contrato de recomendação.

```text
├── AGENTS.md
├── README.md
├── pyproject.toml / uv.lock / .python-version / .env.example
├── docs/
│   ├── architecture/README.md
│   ├── case/NOVACORE.md
│   └── course/PROJECT_CONTEXT.md
├── data/                 # cinco CSVs e políticas
├── incidents/incident_001.json
├── src/control_tower/
│   ├── main.py / models.py / tools.py
│   ├── agents/README.md   # TODOs didáticos
│   └── graph/README.md    # TODOs didáticos
├── labs/01_orchestration/README.md
└── tests/test_lab.py
```

## Pré-requisitos e instalação

Git, Python 3.12 e uv. Instale uv pelas instruções oficiais:
[instalação do uv](https://docs.astral.sh/uv/getting-started/installation/).
A instalação inicial precisa de internet; os comandos do laboratório depois funcionam offline.

```bash
git clone https://github.com/leandrol3/agentic-operations-control-tower.git
cd agentic-operations-control-tower
git checkout lesson-01-start
uv python install 3.12
uv sync --locked
cp .env.example .env
uv run pytest
uv run control-tower doctor
uv run control-tower incident
uv run control-tower tools
uv run control-tower smoke
```

No Windows PowerShell, substitua `cp .env.example .env` por `Copy-Item .env.example .env`.
Execute tudo na raiz do checkout; não precisa ativar ambiente virtual.
Doctor e smoke devem informar `status: ok`, `affected_orders: 3`, `mode: mock` e `orchestration: TODO`.
O comando tools exibe estoque, ordens, fornecedores alternativos e rotas, sem recomendar um cenário.

`.env.example` usa `LLM_MODE=mock`. A CLI lê `.env`; variável do ambiente tem precedência.
`LLM_MODE=openai` é rejeitado explicitamente neste checkpoint. Não precisa fornecer chave.

## Primeiro laboratório

Leia [o case e as premissas](docs/case/NOVACORE.md), depois siga
[o roteiro da Aula 1](labs/01_orchestration/README.md).
Para explorar uma capability em Python:

```bash
uv run python -c "from pathlib import Path; from control_tower.tools import Tools; t=Tools(Path('.')); print(t.get_stock('M42', 'Campinas')); print(t.calculate_penalty('CO-001', 7))"
```

Esperado: 500 unidades disponíveis, 300 transferíveis preservando safety stock, multa de R$140.000.
Isso é multa hipotética de sete dias do cliente, não uma conclusão sobre o impacto do incidente.
Money usa Decimal; multas não usam LLM. Dados completos e premissas ficam documentados no case.

## Recursos, iniciar, parar e limpar

Start/Lite: Python local, sem Docker, sem GPU, sem modelo local. Planejamento conservador: 4 GB RAM
na máquina e 1 GB de disco livre; não são mínimos medidos. Validado em macOS ARM64/Apple Silicon.
Windows e Linux usam o mesmo fluxo, mas ainda não foram testados nesta entrega.
Cada comando termina sozinho; Ctrl+C interrompe. Saídas e erros aparecem no terminal.
Não há serviços persistentes, banco, API ou logs distribuídos neste checkpoint.

Para reinstalar, remova **somente o ambiente gerado**, na raiz do projeto:

```bash
rm -rf .venv
uv sync --locked
```

PowerShell: `Remove-Item -Recurse -Force .venv`, depois `uv sync --locked`.
Não use `git clean -fdx`: isso apagaria também sua configuração local.

Full Lab é a evolução da Aula 3: Docker Desktop, API, Redis, PostgreSQL e workers;
observabilidade chega na Aula 4. Quantidade de workers e memória serão documentadas e medidas nessas etapas.
Compose, endpoints de API, habilitação Langfuse, load test k6 e simulador de falhas **ainda não existem**.
Não é necessário instalar Docker Desktop agora. A evolução deve usar imagens multiarch para Apple Silicon.

## Checkpoints e progressão

| Checkpoint | Conteúdo | Situação |
|---|---|---|
| lesson-01-start | Dados, contratos, tools e exercícios | Esta entrega |
| lesson-01-complete | LangGraph, especialistas, Supervisor, Challenger, aprovação | Após validação do professor |
| lesson-02-start / complete | Execução distribuída, Redis/Celery | Planejado |
| lesson-03-start / complete | FastAPI, PostgreSQL, Docker Compose | Planejado |
| lesson-04-start / complete | OpenTelemetry, Langfuse, chaos, k6, FinOps | Planejado |

`git tag --list 'lesson-*'` mostra somente checkpoints existentes.
Trocar para uma tag deixa o Git em detached HEAD; para trabalhar: `git switch -c minha-aula-01`.
Salve suas alterações antes de mudar de checkpoint. Após publicar checkpoints futuros, será possível:

```bash
git fetch --tags
git checkout lesson-02-start
git diff lesson-02-start..lesson-02-complete
uv sync --locked
```

Esses comandos da Aula 2 não funcionam enquanto as tags não existirem.
Veja [a estrutura final proposta](docs/architecture/README.md) e [o contexto completo](docs/course/PROJECT_CONTEXT.md).

## Seis perguntas de engenharia

1. Who decides? Quem decide qual agente executa?
2. Where is the state? Onde está o estado?
3. What happens when it fails? O que ocorre quando algo falha?
4. Can I observe it? Conseguimos explicar a execução?
5. What does it cost? Quanto custa cada incidente?
6. Should this even be an agent? Deveria ser código determinístico?

## Troubleshooting

- `uv` não encontrado: reinicie o terminal após instalar e confira o PATH.
- Python incompatível: execute `uv python install 3.12` e `uv sync --locked`.
- Arquivo data ausente: execute na raiz do checkout ou use `control-tower doctor --root CAMINHO` via uv.
- Erro de provider: ajuste `.env` e a variável de ambiente para `LLM_MODE=mock`.
- Erro de rede ao instalar: confira proxy e conectividade com o índice de pacotes; não desabilite TLS.
- Erro de validação: restaure o dado editado ou confira tipos, IDs, reservas e datas no case.
- Tag não encontrada após clone: o responsável ainda precisa publicar o commit e a tag no GitHub.
- Teste falhou: preserve a mensagem completa, rode `uv run control-tower doctor` e confira `git status`.

Não comite `.env`, tokens ou chaves. Aprovação de gerente e recomendação são exercícios futuros;
o start não aplica políticas nem executa compras ou transferências.
