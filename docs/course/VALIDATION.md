# Validação de lesson-01-start

- Ambiente observado: macOS ARM64, Python 3.12.3, uv 0.7.6.
- `uv sync` gerou uv.lock e instalou as dependências.
- `uv run pytest`: 24 testes passaram.
- `uv run control-tower smoke`: status ok, INCIDENT-001, três ordens afetadas.
- Cópia limpa sem .venv e sem .env: `uv sync --locked --offline` instalou a partir do cache;
  `.env.example` foi copiado para `.env`, pytest e doctor/incident/tools/smoke passaram.
- Instalação inicial com rede foi validada no checkout de trabalho; instalação limpa usou cache.
- Testes cobrem demanda, estoque/reservas, alternativas, rotas, multas, entradas inválidas,
  referências quebradas, duplicação de estoque, contrato de aprovação e configuração da CLI.
- O modo mock não importa SDK de LLM nem necessita de chave.
- Windows/Linux, Docker, API e execução com LLM real não foram testados: infraestrutura e
  provider real estão fora do escopo deste checkpoint.
- README diferencia recursos existentes de roadmap e documenta premissas do dataset.
- Routing, retries e transições do grafo serão testados quando forem implementados no complete.

A inspeção inicial encontrou repositório remoto vazio. Commit e tag de entrega devem ser conferidos
em `git log --oneline` e `git tag --list`, respectivamente; este documento não atesta publicação remota.
