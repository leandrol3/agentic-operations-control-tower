# Aula 4 — Operating the Agentic Workforce
## Da observabilidade à decisão operacional

**Roteiro único do professor · 240 minutos · candidato `codex/lesson-04-cockpit`.**
Validado sobre o produto `b3823b2`. Este roteiro consolida start, complete e cockpit;
os documentos históricos continuam preservados. Não trocar de branch entre demos.
Alunos observam decisões, evidências e trade-offs. Não há exercício nem live coding.

> Observar não é operar. Operar é transformar sinais em decisões.
> Agents need goals, not just tasks.

Ao final, o aluno deve explicar como identidade, metas, qualidade, economics e valor
sustentam decisões sobre a workforce e como revisão humana transforma experiência em memória útil.

## 1. Mapa de navegação da aula

Cinco perguntas que devem permanecer visíveis na fala:

1. Como expor capabilities sem acoplar o core a um único protocolo?
2. Como identificar e organizar uma workforce agêntica?
3. Como saber se um agente está funcionando bem — e a que custo?
4. Como transformar sinais em decisões operacionais?
5. Como uma organização passa de operar agentes para aprender continuamente com eles?

| Horário relativo | Min | Bloco / ação | Pergunta condutora |
|---|---:|---|---|
| 00:00–00:15 | 15 | Retomada da Aula 3 e problema | Observar basta? |
| 00:15–00:35 | 20 | Service Boundary e MCP: teoria | Como expor capabilities sem acoplar o core? |
| 00:35–00:50 | 15 | Demo 1 — Same Capability, Different Boundary | O workflow mudou? |
| 00:50–01:15 | 25 | Registry, Goals, Lifecycle: teoria e discussão | Como identificar e organizar a workforce? |
| 01:15–01:30 | 15 | Demo 2 — Registry / Goals / Lifecycle | Quem é, para que existe e em que estado está? |
| 01:30–01:50 | 20 | Quality e Economics: teoria | Funciona bem e a que custo? |
| 01:50–02:05 | 15 | Demo 3 — normal/degraded e economics | Completed significa qualidade? |
| 02:05–02:20 | 15 | Pausa; professor prepara OpenAI | Sem nova carga empresarial |
| 02:20–02:45 | 25 | Business Value, SLO, Decision Engine | Como transformar sinais em decisões? |
| 02:45–03:00 | 15 | Demo 4 — Collect → Interpret → Recommend | O que sustenta a proposta? |
| 03:00–03:10 | 10 | Control Plane visual: enquadramento | Qual decisão o cockpit permite tomar? |
| 03:10–03:20 | 10 | Maestro: conceito, fontes e limites | Quem coordena a melhoria? |
| 03:20–03:38 | 18 | Demo 5 — narrativa integrada do cockpit | Da atenção ao conhecimento reutilizado |
| 03:38–03:50 | 12 | Segundo Cérebro: discussão e margem | Quando uma resposta vira conhecimento? |
| 03:50–04:00 | 10 | Learning Loop, maturidade e arco final | O que significa uma empresa aprender? |
| **Total** | **240** | **Sem instalação ou build ao vivo** | |

Há **105 min explícitos de contexto/teoria antes do cockpit**, além dos seus 20 min conceituais.
Cada demo de 15 min reserva 2 min para transição/espera. A demo final tem 2 min internos de margem.
Dos 12 min após o cockpit, preservar 6 min de reflexão e usar no máximo 6 para recuperação.
**Hard stop:** às 03:50 iniciar o fechamento, mesmo que alguma exploração opcional não tenha ocorrido.
Tempo de máquina não é tempo de fala: os números técnicos do relatório não simulam uma aula ministrada.

## 2. Preparação antes da aula (reservar 45–60 min)

### 2.1 Terminal, branch e dependências

Copiar no Terminal macOS/zsh. Execute um bloco por vez; se houver erro, pare nesse bloco.
Não apague histórico nem conhecimento para obter uma tela limpa.

```bash
cd '/Users/leandrolopes/Documents/ChatGPT/Disciplina Mult-Agents/agentic-operations-control-tower'
git branch --show-current
git log -1 --oneline
git status --short
open -a Docker
docker version
uv --version
uv sync --locked --extra lesson04
```

Esperado: `codex/lesson-04-cockpit`; Docker Client e Server respondem. Caso outra branch esteja
ativa, confira alterações próprias antes de `git switch codex/lesson-04-cockpit`.
Não é necessário fazer checkout dos checkpoints anteriores. Não mover tags.

### 2.2 Memória exclusiva da aula — preservar o conhecimento pessoal

Este bloco cria uma pasta nova **persistente em `artifacts/`**, copia apenas os seeds versionados
e prepara um overlay de volume. Execute uma vez por ensaio; não repetir no meio da aula.
O banco de execuções é preservado; apenas a memória do cockpit é isolada.

```bash
export AULA4_DIR="$PWD/artifacts/aula4-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$AULA4_DIR"
printf '%s\n' "$AULA4_DIR" > artifacts/aula4-current.txt
uv run python - <<'PY'
import json, os, subprocess
from pathlib import Path
root = Path.cwd()
out = Path(os.environ['AULA4_DIR'])
for name in subprocess.check_output(['git', 'ls-files', 'knowledge'], text=True).splitlines():
    target = out / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((root / name).read_bytes())
(out / 'knowledge').mkdir(exist_ok=True)
(out / 'isolation.yaml').write_text('services:\n  api:\n    volumes:\n      - type: bind\n        source: ' + json.dumps(str(out / 'knowledge')) + '\n        target: /app/knowledge\n')
print('Memória exclusiva preparada:', out / 'knowledge')
PY
export KNOWLEDGE_ROOT="$AULA4_DIR/knowledge"
export CONTROL_TOWER_PRICING_FILE=config/lesson04-pricing.json
export CONTROL_PLANE_CONFIG_FILE=config/lesson04-control-plane.json
export LLM_MODE=mock
export OTEL_ENABLED=true
export OTEL_CAPTURE_CONTENT=false
export DEMO_AGENT_DELAY_MS=0
export VISIBILITY_TIMEOUT=900
unset OPENAI_API_KEY
uv run --extra lesson04 python scripts/seed_cockpit.py
```

Esperado: três referências curadas, um candidato pendente e um plano mock. O seed é idempotente;
os três itens aprovados são material didático, não descobertas de produção.
**Novo terminal:** recuperar as variáveis antes de continuar:

```bash
cd '/Users/leandrolopes/Documents/ChatGPT/Disciplina Mult-Agents/agentic-operations-control-tower'
export AULA4_DIR="$(cat artifacts/aula4-current.txt)"
export KNOWLEDGE_ROOT="$AULA4_DIR/knowledge"
export CONTROL_TOWER_PRICING_FILE=config/lesson04-pricing.json
export CONTROL_PLANE_CONFIG_FILE=config/lesson04-control-plane.json
export VISIBILITY_TIMEOUT=900
```

### 2.3 Startup mock e verificação

```bash
export LLM_MODE=mock
./scripts/cockpit.sh -f "$AULA4_DIR/isolation.yaml" config --quiet
./scripts/cockpit.sh -f "$AULA4_DIR/isolation.yaml" up -d --build --wait
./scripts/cockpit.sh -f "$AULA4_DIR/isolation.yaml" ps
curl --fail --silent --show-error http://localhost:8000/health
curl --fail --silent --show-error http://localhost:8000/ready
uv run --extra lesson04 control-tower smoke
uv run --extra lesson04 python scripts/demo_cockpit.py
```

O launcher inclui os **cinco** arquivos Compose, configura UID/GID e mantém dois workers.
`health=alive`, `ready=ready`; serviços healthy. O smoke valida 12 condições do caso.
O helper visual confirma 7 agentes, 1 em atenção, Supply 90%/74%/−16 p.p. e 6 execuções ilustrativas.
`/ready` não prova sozinho que todos os workers funcionam: a Demo 1 completa essa verificação.
Build fica fora da aula. Nunca projetar `docker compose config` sem `--quiet` com chave carregada.

### 2.4 Preparar normal/degraded e salvar outputs de contingência

Este trabalho ocorre **antes da aula**. Primeiro HTTP/MCP real em mock:

```bash
uv run --extra lesson04 python scripts/demo_lesson04.py boundary | tee "$AULA4_DIR/boundary.txt"
uv run --extra lesson04 python scripts/demo_lesson04.py registry | tee "$AULA4_DIR/registry.txt"
```

Agora ativar somente o perfil existente de falha **artificial antes da rede**:

```bash
./scripts/cockpit.sh -f "$AULA4_DIR/isolation.yaml" -f compose.lesson03-failure.yaml up -d --wait
uv run --extra lesson04 python scripts/demo_lesson04.py degraded | tee "$AULA4_DIR/degraded.txt"
uv run --extra lesson04 python scripts/demo_lesson04.py quality | tee "$AULA4_DIR/quality.txt"
uv run --extra lesson04 python scripts/demo_lesson04.py economics | tee "$AULA4_DIR/economics.txt"
export LLM_MODE=mock
./scripts/cockpit.sh -f "$AULA4_DIR/isolation.yaml" up -d --wait
uv run --extra lesson04 python scripts/demo_lesson04_complete.py --fixture optimize --agent logistics --section pipeline | tee "$AULA4_DIR/pipeline.txt"
uv run --extra lesson04 python scripts/demo_cockpit.py | tee "$AULA4_DIR/cockpit.txt"
```

Guardar também uma síntese mock curta, antes de habilitar OpenAI:

```bash
curl --fail --silent --show-error http://localhost:8000/maestro/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Como posso melhorar o agente de Supply?","agent_id":"supply","source":"didactic"}' \
  > "$AULA4_DIR/maestro-mock.json"
uv run python - <<'PYMOCK'
import json, os
from pathlib import Path
root = Path(os.environ['AULA4_DIR'])
r = json.loads((root / 'maestro-mock.json').read_text())
p = r['plan']
assert p['generated_by'] == 'mock-deterministic', 'Volte a stack para mock antes de preparar este fallback'
text = 'FALLBACK DIDÁTICO MOCK — NÃO É INFERÊNCIA REAL\n' + p['diagnosis'] + '\n\n' + p['objective'] + '\n' + '\n'.join(p['steps'])
(root / 'maestro-mock.txt').write_text(text + '\n')
print(text)
PYMOCK
```

No perfil artificial **não enviar outros POSTs**, nem usar Maestro ou Compiler: a chave é um
placeholder e somente o incidente com `llm_failure=timeout` é seguro para essa demonstração.
O helper `degraded` envia exatamente esse campo. Não repetir SIGKILL, retry/redelivery da Aula 2.
Os IDs ficam em `artifacts/lesson04-demo.json`; rodar `boundary` novamente atualiza o normal,
preservando o degraded. PostgreSQL mantém os resultados após a troca de modo.

### 2.5 OpenAI real — carregar `.keys` sem mostrar a chave

A chave já autorizada pode estar em `.keys`; não usar `cat`, não enviar ao navegador e não executar
`source .keys` (o arquivo pode conter uma chave pura). O código abaixo usa o leitor existente,
passa a credencial apenas ao subprocesso Compose e não a imprime. Reutilize este mesmo bloco na pausa.

```bash
export LLM_MODE=openai
export OPENAI_MODEL=gpt-4.1-mini
uv run --extra lesson04 python - <<'PY'
import os, subprocess
from pathlib import Path
from control_tower.settings import Settings
settings = Settings.load(Path.cwd())
env = dict(os.environ, OPENAI_API_KEY=settings.api_key)
subprocess.run(['bash', 'scripts/cockpit.sh', '-f', str(Path(os.environ['AULA4_DIR']) / 'isolation.yaml'), 'up', '-d', '--wait'], env=env, check=True)
print('OpenAI configurado; chave não exibida.')
PY
```

Se chave ausente, o leitor falha claramente. Configure-a fora da projeção. Modelo sem permissão,
saldo, rede ou rate limit: ir ao fallback, não depurar credenciais em aula.
O runtime empresarial continua o mesmo; **não gerar nova carga OpenAI para demonstrar o cockpit**.
Somente as consultas do Maestro e a extração usam LLM real nesse percurso.

### 2.6 Pré-testar Maestro e Compiler uma vez

No cockpit: `Cenário didático` → Suprimentos → `Perguntar ao Maestro` →
“Como posso melhorar este agente?” → Enviar. Ler diagnóstico, fontes e plano.
Em `Operações`, abrir a primeira execução concluída e clicar `Extrair aprendizado`.
Conferir candidato pendente, origem e limites. Não aprovar sem ler. O candidato mock do seed
continua sendo a contingência. As instruções completas da revisão estão na Demo 5.
Não fazer chamadas pagas em loop para obter uma resposta mais bonita.

Ao finalizar a preparação, **voltar a mock para começar a aula**:

```bash
export LLM_MODE=mock
unset OPENAI_API_KEY
./scripts/cockpit.sh -f "$AULA4_DIR/isolation.yaml" up -d --wait
```

### 2.7 Telas e arquivos já abertos

```bash
open http://localhost:3000
open http://localhost:8000/docs
open http://localhost:16686
```

Abra a apresentação existente em Gamma/slides manualmente. Não há slides novos nesta entrega.
Deixe seis destinos acessíveis: slides, cockpit, Swagger, Jaeger, Terminal e VS Code.
Jaeger fica como reserva para perguntas, não passeio obrigatório da Aula 4.
No VS Code abra os arquivos da seção 9. Se o comando `code` já estiver instalado:

```bash
code src/control_tower/application.py src/control_tower/mcp/tools.py src/control_tower/control_plane/registry.py src/control_tower/control_plane/decision_engine.py src/control_tower/cockpit/assistance.py
```

Se não estiver, use Arquivo → Abrir arquivo no VS Code; não instalar a integração durante a aula.
Fonte de terminal 20–24; navegador 1440×900 ou 1920×1080, zoom 100%. Fechar abas de credenciais.

### Checklist imediatamente antes dos alunos entrarem

- [ ] Branch correta; working tree conhecido; conhecimento pessoal preservado.
- [ ] Docker funcionando; API ready; dois workers healthy; Demo 1 concluiu.
- [ ] Cockpit e Jaeger disponíveis.
- [ ] Chave OpenAI validada sem exposição; Maestro e Compiler ensaiados uma vez.
- [ ] Ambiente retornou a mock; bloco de troca para OpenAI pronto para a pausa.
- [ ] Seeds preparados na pasta isolada; candidato pendente e plano mock disponíveis.
- [ ] Supply meta 90%, atual 74%, gap −16; exatamente 1 agente requer atenção.
- [ ] Normal/degraded persistidos; outputs de fallback salvos.
- [ ] Navegador nas abas certas; terminal e seis trechos de código preparados; slides abertos.
- [ ] Cronômetro e hard stop de 03:50 definidos.

## 3. Abertura e Demo 1 — Same Capability, Different Boundary

### 00:00–00:15 · retomada

**Fala:** “Na aula passada aprendemos a observar a força de trabalho. Hoje a pergunta deixa de
ser ‘o que aconteceu?’ e passa a ser ‘o que devemos fazer com isso?’ Um trace explica uma execução.
Ele não decide se um agente deve continuar ativo, receber investimento ou passar por revisão.”
Reserve 3 min para recuperar uma pergunta da Aula 3; 7 min para o problema; 5 min para as cinco perguntas:
capabilities; identidade; qualidade/custo; decisão; aprendizado. Não reensinar Docker e tracing.

### 00:15–00:35 · teoria antes da demo

Desenhar verbalmente: cliente → adaptador → capability → fila → worker → mesmo LangGraph.
HTTP atende um cliente HTTP; MCP expõe ferramentas a clientes compatíveis. Nenhum exige outro core.
**Fala:** “Service Boundary é o princípio. HTTP e MCP são formas diferentes de expor capabilities.”
Explique contrato público, idempotência e separação entre submissão e execução. Não ensinar JSON-RPC.

### 00:35–00:50 · execução

Objetivo: provar mesmas identidade, capability e resultado. 2 min previsão, 4 min comando/leitura,
1 min código, 6 min discussão, 2 min margem. Ambiente **mock**.

```bash
uv run --extra lesson04 python scripts/demo_lesson04.py boundary
```

Output observado, com IDs/durações variáveis:

```text
Ferramentas MCP: submit_incident, get_execution_status, get_execution_result
HTTP → MCP: mesma identidade e execução, created=false (idempotência durável)
Status HTTP: <id> | Concluída | worker=worker-a@... | duração_ms=...
HTTP = MCP resultado público | resultado=Recomendação | aprovação=pendente | ações=não executadas
Mesma capacidade, fronteiras diferentes.
```

Queued/running podem passar entre consultas. Isso não invalida a execução distribuída.
Mostre `IncidentCapability.submit_incident` e um adaptador MCP, **30 s cada**.
**Pergunta:** “Workflow mudou quando trocamos HTTP por MCP?”
**Resposta-chave:** mudou o acesso; a inteligência, a fila, a validação e a aprovação permanecem.
**Fallback:** `cat "$AULA4_DIR/boundary.txt"`; declarar gravação do ensaio. Com runtime indisponível,
`LLM_MODE=mock uv run --extra lesson04 pytest tests/test_lesson04.py -k mcp -q` valida o contrato,
não prova execução distribuída atual. Não fazer também a demo Codex/MCP interativa no mesmo bloco.
**Transição:** “Expor uma capacidade não nos diz quem compõe a organização que a executa.”

## 4. Registry, Goals e Lifecycle — teoria e Demo 2

### 00:50–01:15 · teoria

10 min identidade/papel/owner; 8 min metas e unidades; 7 min lifecycle versus runtime.
**Fala:** “Você não consegue operar uma força de trabalho que não consegue identificar.
Identidade nos diz quem é o agente. Metas nos dizem por que ele existe.”

| Dimensão | Pergunta | Evidência |
|---|---|---|
| Cadastro | Está registrado? | `registered` |
| Lifecycle | Em que estágio administrativo está? | `active` |
| Runtime health | Pode servir agora? | dependências, workers, execução de verificação |
| Execução | O que aconteceu com um trabalho? | queued/running/completed/failed |

**Pergunta:** “Um agente Ativo pode participar de uma execução falha?” Sim.
Explique alvo, observado, gap, janela, unidade e desconhecido antes de abrir o cockpit.

### 01:15–01:30 · Demo 2

2 min pergunta, 4 min Registry, 3 min meta/lifecycle, 1 min código, 3 min discussão, 2 min margem.

```bash
uv run --extra lesson04 python scripts/demo_lesson04.py registry
uv run --extra lesson04 python scripts/demo_lesson04.py registry supply
uv run --extra lesson04 python scripts/demo_lesson04_complete.py --fixture stable --agent logistics --section goals
```

Esperado: sete papéis, Ativo, determinístico em mock; Supply usa tools de estoque/fornecedores;
Finance continua determinístico. Registry: alvo técnico 100%. Fixture Logistics: atual 100%, gap 0.
**Não confundir:** o cockpit Supply usa outra meta didática, **cobertura de evidência 90%**, calculada
sobre 50 observações. O alvo técnico de concluir uma etapa sem falhar não é essa cobertura.
Na UI abra `Lifecycle`: seis estados e 11 transições válidas. Estado atual Ativo; proposta não aplicada.
Não clicar em ações inexistentes nem afirmar que o motor grava transições.
**Código:** `BusinessGoal` e `AgentRecord`, no máximo 60 s.
**Pergunta:** “Recommendation deve mudar lifecycle automaticamente?” Não: recommendation is not authorization.
**Fallback:** Registry salvo no terminal, enum no arquivo; não alterar o cadastro para a demo.
**Transição:** “Agora sabemos quem é e o que esperamos. Precisamos medir o que entregou.”

## 5. Quality e Economics — teoria e Demo 3

### 01:30–01:50 · teoria

8 min status/qualidade; 6 min incerteza e evidência; 6 min usage/pricing/custo.
**Fala:** “Completed é status de runtime. Não é sinônimo de qualidade. Quality é um vetor antes
que seja uma nota. Não disponível não significa zero. Confiança declarada não é probabilidade calibrada.”
**Pergunta:** “Quanto custa um agente?” Distinguir consumo LLM, infraestrutura, pessoas, workflow e decisão.
Pricing é configuração datada; usage é medição; custo é estimativa. Não comparar USD com BRL por soma.

### 01:50–02:05 · Demo 3

2 min hipótese, 5 min comparação, 3 min economics, 3 min debate, 2 min margem.
Os dois resultados já foram produzidos na preparação; dizer isso explicitamente.

```bash
uv run --extra lesson04 python scripts/demo_lesson04.py quality
uv run --extra lesson04 python scripts/demo_lesson04.py economics
DEGRADED_ID="$(uv run python -c 'import json; print(json.load(open("artifacts/lesson04-demo.json"))["degraded"])')"
uv run --extra lesson04 python scripts/demo_lesson04.py economics "$DEGRADED_ID"
```

| Campo | Normal | Degraded artificial |
|---|---|---|
| Status do runtime | Concluída | Concluída |
| Resultado | Recomendação | Recomendação degradada |
| Fallback | Não | Sim |
| Revisão humana | Sim | Sim |
| Aprovação | Pendente | Pendente |
| Evidências completas / conformidade | Não disponível | Não disponível |
| Tokens / custo LLM | Não disponível | Não disponível |

Na falha artificial, tentativas registradas não são chamadas faturadas. Não usar seu contador como fatura.
**Pergunta:** “As duas completaram. São equivalentes?” Não. Revisão humana na normal é uma regra, não defeito.
**Fallback:** `cat "$AULA4_DIR/quality.txt"` e `cat "$AULA4_DIR/economics.txt"`.
**Transição:** “Custo nos diz quanto consumimos. Valor nos diz se valeu a pena.”

### 02:05–02:20 · pausa

Professor executa o bloco OpenAI da seção 2.5 e confere `demo_cockpit.py` (somente leitura, sem chamada LLM).
Não pedir que alunos esperem reconstrução de imagem. Manter candidato/plano mock pré-gerados.

## 6. Business Value, SLO e Decision Engine — teoria e Demo 4

### 02:20–02:45 · teoria

8 min valor; 8 min SLO/escopo; 9 min regras, precedência e autorização.
**Fala:** “Cost is not Value. Uma proposta barata pode ser ruim. Uma exposição evitável não é uma economia realizada.”

| Número didático | Significado | O que não prova |
|---|---|---|
| R$ 140.000 | Penalidade potencial: R$ 20 mil × 7 dias hipotéticos | Impacto confirmado ou savings |
| R$ 12.500 | Custo do cenário recomendado | Custo de tokens ou economia |
| Não validado | Valor realizado | Ausência de valor; falta comprovação |

SLO: limite de operação, unidade e janela; PASS/WARN/VIOLATION/UNKNOWN. As janelas técnicas são pequenas
(3 atuais/3 anteriores); p95 com 3 amostras é o máximo, não benchmark de produção.
Qualidade degradada é contexto do workflow, não prova de culpa individual de Supply.
**Perguntas:** “O que é valor: tokens baratos ou impacto de negócio?”
“Se o agente está fora da meta, devemos trocar o modelo imediatamente?” Investigar evidências primeiro.

### 02:45–03:00 · Demo 4

2 min hipótese; 3 min custo/SLO; 4 min pipeline; 1 min código; 3 min discussão; 2 min margem.

```bash
uv run --extra lesson04 python scripts/demo_lesson04_complete.py --fixture cost --agent logistics --section slo
uv run --extra lesson04 python scripts/demo_lesson04_complete.py --fixture optimize --agent logistics --section pipeline
```

Primeiro: meta 100%, custo USD 0,02016 acima de 0,01, proposta de revisão.
Segundo: atual 66,666667%, alvo 100%, custo crescente, qualidade desconhecida, **Otimizar**, aprovação Sim.
Ambos imprimem **FONTE: FIXTURE DIDÁTICA**. `modo=openai` no output caracteriza eventos sintéticos,
não requests ao provider. Mostrar uma evidência, sua unidade e escopo; não ler todas as linhas.
**Código:** primeira regra e retorno de `decision_engine.recommend`, 60 s. Primeira regra aplicável vence;
a regra não chama LLM, não altera modelo, não pausa worker, não autoriza plano.
**Fala:** “Control Plane não precisa controlar tudo. Ele precisa transformar sinais em decisões melhores.”
**Fallback:** `cat "$AULA4_DIR/pipeline.txt"`; a mesma fixture também roda sem Docker.
**Transição:** “O Control Plane identifica que devemos intervir. Mas quem coordena a melhoria?”

## 7. Control Plane visual e Maestro — preparar a narrativa (03:00–03:20)

**03:00–03:10:** explique a tela sem percorrer todos os menus. Coleção → interpretação → proposta.
Declare as três populações: 50 observações de cobertura Supply; janelas técnicas dos outros papéis;
6 execuções ilustrativas independentes. Não dividir as seis execuções para tentar reproduzir os 74%.
**03:10–03:20:** “The Maestro is the Chief of Staff of the Agentic Workforce.”
Supervisor coordena **uma execução**. Maestro coordena **propostas de melhoria da workforce**.
Consulta fontes, sintetiza diagnóstico, propõe plano e responsabilidades. Staffs são papéis propostos,
não novos agentes executando. “LLMs interpretam e julgam. Código determinístico mede e valida.”
**Pergunta:** “Quem deve melhorar um agente? Quais evidências a equipe precisaria antes de mudar seu modelo?”
Não mostrar a conversa completa ainda; preservar a surpresa e continuidade da demo.

## 8. Demo 5 — cockpit final em 18 minutos (03:20–03:38)

**Pré-condição:** OpenAI, gpt-4.1-mini, fonte Cenário didático, pasta de conhecimento isolada.
Texto do LLM varia; medidas, fontes, estado e autorização não. Cronometrar a partir de Visão Geral.

| Tempo da demo | Gestos e tela | Fala / evidência |
|---|---|---|
| 00:00–01:30 | Visão Geral; apontar 1 agente requer atenção; clicar CTA e fechar drawer sem enviar | “Estou vendo uma organização agêntica sendo gerenciada. O sinal pede investigação, não culpa.” |
| 01:30–04:00 | Abrir Suprimentos; Resumo → Metas → Qualidade → Economia → SLOs → Lifecycle | “Meta 90, atual 74, gap −16. São 37/50 observações completas. Ativo não significa dentro da meta.” |
| 04:00–05:00 | Decisões; abrir Suprimentos · Intervir | Mostrar evidências; Ativo → Em revisão é sugestão. “Recommendation is not authorization.” |
| 05:00–08:00 | Perguntar ao Maestro; enviar “Como posso melhorar este agente?” | Ler diagnóstico curto. Expandir Hipótese, plano de melhoria e staffs; Fontes utilizadas. Mostrar Registry, Goals, Quality, Economics, SLO, Control Plane e memória aprovada consultados. |
| 08:00–09:00 | Abrir Operações; primeira execução concluída relacionada; Extrair aprendizado | “Melhorar uma vez não significa aprender. A experiência precisa sobreviver à execução.” |
| 09:00–12:00 | Ler candidato, origem, observações e inferência; decidir revisão | Aprovar apenas se sustentado, com formulário abaixo. Caso contrário rejeitar e usar seed aprovado como exemplo de retrieval. |
| 12:00–13:30 | Voltar ao Segundo Cérebro; lista, grafo e feed | “Memória organizacional validada: execuções, decisões, evidências, feedback, outcomes, lessons e patterns. Não apenas vector database.” |
| 13:30–15:00 | Voltar ao Maestro; perguntar “O que aprendemos hoje sobre Supply? Use o conhecimento aprovado.” | Conferir título do item nas fontes. Conhecimento pendente não vira verdade. Melhora contexto do Maestro, não treina pesos. |
| 15:00–16:00 | Learning Loop; 12 etapas e régua de maturidade | LAB entre Gerenciada e Adaptativa, níveis 3 e 4. Nível 5 é visão futura. |
| 16:00–18:00 | Margem para provider, leitura e transições | Se não consumida, pedir ao aluno para distinguir recomendação, plano e aprovação. |

### Revisão humana — texto pronto, decisão consciente

Leia o candidato por inteiro antes de marcar a caixa. Verifique que observação não virou benefício realizado,
que inferência está rotulada e que execução de origem corresponde à tela.

- **Nome do revisor:** `Leandro Lopes`.
- **Justificativa:** `Revisei origem, evidências e limites. Aprovação restrita ao caso sintético do LAB; não comprova transferência realizada, melhoria implantada ou economia obtida.`
- Marcar: **Revisei o conteúdo, a origem e os limites desta proposta.**
- Clicar **Confirmar aprovação** somente se a leitura sustentar essa decisão; caso contrário **Rejeitar candidato**.

Esperado: `Conhecimento aprovado e persistido.`; status Aprovado e revisor/nota visíveis.
Isso **não** aprova incidente, compra, plano ou lifecycle. Candidato é sempre criado pending_review.
**Fala:** “O LLM propõe conhecimento. O sistema valida estrutura e proveniência. O humano autoriza conhecimento material.”

### O que mostrar e o que evitar

Mostrar uma hipótese, um passo do plano, um staff e uma fonte. Não ler todos os staffs.
No ensaio real, o LLM generalizou latência local como ausência de gargalo e atribuiu ao Supervisor
uma proposta produzida pelo Decision Engine. Corrigir verbalmente: “É síntese proposta, não fato novo;
a regra vem do motor e estes sinais não demonstram causalidade nem garantem atingir a meta.”
Se sugerir implementar algo que já existe, pedir validação do código/evidências antes de aceitar o plano.
O drawer conserva conversa ao navegar na mesma aba, mas reinício da API/reload perde a sessão;
planos e Markdown persistem. Ao mudar contexto, confira o chip (agente/recomendação/execução).
Não fazer as três perguntas adicionais do runbook histórico: duas consultas são suficientes aqui.
Tokens/custo da consulta ficam em detalhes opcionais e não se confundem com economics do workflow.
Se o novo documento não aparecer nas fontes, conferir fonte didática, status aprovado e busca;
o retrieval simples considera até cinco itens relevantes recentes. Não afirmar uso sem vê-lo.

### Regra de tempo e fallback dentro dos 18 minutos

Se uma chamada ultrapassar **15 s**, começar a explicação das fontes. O timeout do provider é 45 s.
Após falha, não fazer uma sequência de retries: mostrar plano mock/candidato preparados.
Reiniciar em mock pode levar dezenas de segundos; preferir conteúdo persistido para não interromper a história.
Se necessário reiniciar, usar a seção 11 e anunciar a mudança de modo. Não há fallback silencioso.
No minuto 12, se a revisão ainda não terminou, não aprovar às pressas: usar referência curada no Segundo Cérebro.
Na tabela SLO, um custo muito pequeno pode aparecer arredondado como `0`; a aba Economia mostra
`0,00056 USD` no cenário. Não interpretar o arredondamento como consumo gratuito.
Ao abrir execução/conhecimento a partir do Agent 360, o título principal pode continuar “Suprimentos”;
o breadcrumb e o título do documento indicam a área atual. Use o menu lateral para remover essa ambiguidade.
No minuto 16, abrir Learning Loop. Máximo absoluto 20 min; recuperar até 2 min da discussão seguinte.

## 9. Código: somente seis recortes, 30–60 segundos cada

Não percorrer arquivos inteiros. Abrir pela busca do VS Code (Cmd+F) nos símbolos abaixo.

| Arquivo | Símbolo/recorte | Mensagem |
|---|---|---|
| `src/control_tower/application.py` + `mcp/tools.py` | `submit_incident`, chamada da mesma capability | Adaptadores não duplicam inteligência |
| `src/control_tower/control_plane/registry.py` | `BusinessGoal`, `AgentRecord` | Identidade e expectativa explícitas |
| `src/control_tower/control_plane/decision_engine.py` | `recommend` | Regras transparentes, evidência e ausência de ACT |
| `src/control_tower/cockpit/assistance.py` | `MaestroTools` e início de `chat` | Consultar fontes antes de sintetizar |
| Mesmo arquivo | `KnowledgeCompiler.extract` | Observações, inferência e referências validadas |
| `$AULA4_DIR/knowledge/wiki/lessons/*.md` | Frontmatter + Inferência proposta | Proveniência e revisão sobrevivem à execução |

Para achar o Markdown sem copiar ID:

```bash
uv run python - <<'PY'
from control_tower.cockpit.knowledge import KnowledgeStore
for item in KnowledgeStore().list(source='didactic')[:5]:
    print(item.id, '|', item.validation_status, '|', item.title)
    print('Revisor:', item.reviewer or 'pendente')
PY
open "$AULA4_DIR/knowledge/wiki/lessons"
```

Os três últimos recortes podem ficar para os 12 min de discussão após a demo; não quebrar o fluxo integrado.
**Pronto antes:** Compose, Next.js, CSS, API, SQL, fixtures, schema, SDK, pricing, testes e seeds.
Nenhum boilerplate ao vivo. Não mostrar `.keys`, prompts extensos, dumps integrais ou código de infraestrutura.

## 10. Segundo Cérebro, Learning Loop e fechamento

### 03:38–03:50 · reflexão (12 min; até 6 de reserva)

Pergunte: “Quando uma resposta de um LLM vira conhecimento corporativo?”
Distinguir candidato, estrutura válida, evidência sustentada, autorização humana e utilidade posterior.
“Uma resposta pode ter formato correto e ainda estar errada. Proveniência permite revisar; não garante verdade.”
Mostrar o Markdown por 45 s. Relacionar execução, lição e pattern no grafo; arestas vêm de metadata,
não de inferência de causalidade. Segundo Cérebro guarda memória validada, não só embeddings.
“Quando o conhecimento melhora a próxima decisão, fechamos o loop.”
**Limite do LAB:** retrieval demonstrado no Maestro; o grafo empresarial não recebe automaticamente
esse conhecimento na próxima execução. Staffs e melhorias seguem propostas, não mudanças implantadas.

### 03:50–04:00 · fechamento protegido

3 min loop, 2 min maturidade, 3 min arco da disciplina, 2 min pergunta final.

```text
META → EXECUÇÃO → RESULTADO → MEDIÇÃO → CONTROL PLANE → MAESTRO
→ PLANO → STAFFS → VALIDAÇÃO → SEGUNDO CÉREBRO → MELHOR CONTEXTO
→ PRÓXIMA EXECUÇÃO ↺
```

**Fala:** “A organização não aprende porque executou mais. Ela aprende quando sua experiência melhora a próxima decisão.”

1. Automação — executa tarefas.
2. Observável — enxerga o que ocorreu.
3. Gerenciada — identifica, mede, interpreta e recomenda.
4. Adaptativa — coordena melhoria validada; LAB demonstra partes assistidas.
5. Learning Enterprise — visão organizacional futura; **não operacional neste LAB**.

“O LAB está entre 3 e 4. Aprendizado contínuo não significa automodificação irrestrita.”
A tela também mostra **autonomia 1/2 (recomendar/propor delegação)**. É outro eixo: autoridade para agir,
não a régua de maturidade organizacional. Aponte os títulos para evitar aparente contradição.

| Aula | Conquista |
|---|---|
| 1 | Agentes conseguem colaborar. |
| 2 | Conseguem executar em paralelo e sobreviver a falhas. |
| 3 | Conseguimos implantar e observar o runtime. |
| 4 | Conseguimos identificar, medir, interpretar e gerenciar a workforce. |
| Visão | A organização consegue coordenar, lembrar e aprender. |

**Falas finais:**
“Um agente é uma unidade de inteligência. Um sistema multiagente é uma organização.”
“Control Tower opera o processo. Control Plane opera a força de trabalho agêntica.”
“Agents need goals, not just tasks.”
“Recommendation is not authorization.”
“Operar agentes é uma disciplina de lifecycle, não apenas de runtime.”
**Pergunta de saída:** “Qual evidência precisaria existir para autorizar a próxima melhoria nesta organização?”

## 11. Fallbacks copiáveis e troubleshooting

### LLM indisponível: conteúdo preparado primeiro, mock explícito depois

No Agent 360, Última análise do Maestro mostra apenas o plano mais recente.
Para a síntese mock preparada, executar `cat "$AULA4_DIR/maestro-mock.txt"`; não depender de um seletor de planos antigos.
No Segundo Cérebro abrir candidato pendente pré-gerado. Ler antes de aprovar.
Dizer: “O provider está indisponível. A camada determinística continua medindo e recomendando.
Vou usar uma conversa mock preparada; não é uma inferência real.”

```bash
export LLM_MODE=mock
unset OPENAI_API_KEY
./scripts/cockpit.sh -f "$AULA4_DIR/isolation.yaml" up -d --wait
uv run --extra lesson04 python scripts/demo_cockpit.py
```

Recarregar a página; nova sessão, planos preservados. Para voltar a OpenAI repetir seção 2.5.
Não chamar mock de fallback de produção; é contingência explícita da aula.

### UI indisponível, API funcionando

```bash
uv run --extra lesson04 python scripts/demo_cockpit.py
curl --fail --silent --show-error 'http://localhost:8000/cockpit/overview?source=didactic' > "$AULA4_DIR/overview.json"
```

Somente se necessário fazer a consulta real via API (não duplicar a chamada que já funcionou na UI):

```bash
curl --fail --silent --show-error --max-time 55 http://localhost:8000/maestro/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Como posso melhorar o agente de Supply?","agent_id":"supply","source":"didactic"}' \
  > "$AULA4_DIR/maestro.json"
uv run python - <<'PY'
import json, os
from pathlib import Path
r=json.loads((Path(os.environ['AULA4_DIR'])/'maestro.json').read_text())
print(r['plan']['diagnosis'])
print('Status:', r['plan']['status'])
print('Fontes:', ', '.join(r['sources_consulted']))
PY
```

Extrair via API, se ainda não houver candidato disponível:

```bash
EXECUTION_ID="$(uv run python -c 'import json,os; from pathlib import Path; print(json.loads((Path(os.environ["AULA4_DIR"])/"overview.json").read_text())["operations"][0]["execution_id"])')"
curl --fail --silent --show-error --max-time 55 -X POST \
  "http://localhost:8000/knowledge/extract/$EXECUTION_ID?source=didactic" > "$AULA4_DIR/candidate.json"
uv run python - <<'PY'
import json, os
from pathlib import Path
r=json.loads((Path(os.environ['AULA4_DIR'])/'candidate.json').read_text())
print(r['id'], r['validation_status'], r['title'])
print(r['content'])
PY
```

Se a UI estiver indisponível, preservar candidato pendente e explicar a revisão usando Markdown;
não é necessário aprovar por terminal para concluir a mensagem pedagógica.

### Docker/API indisponíveis

```bash
cat "$AULA4_DIR/boundary.txt"
cat "$AULA4_DIR/quality.txt"
cat "$AULA4_DIR/pipeline.txt"
LLM_MODE=mock uv run --extra lesson04 python scripts/demo_lesson04_complete.py --fixture optimize --agent logistics --section pipeline
LLM_MODE=mock uv run --extra lesson04 python scripts/seed_cockpit.py
open "$AULA4_DIR/knowledge/wiki/lessons"
```

Anunciar quais outputs são gravações e quais cálculos são locais atuais. Não representar mock como provider real.

| Problema | Ação curta |
|---|---|
| ModuleNotFoundError | `uv sync --locked --extra lesson04` antes da aula |
| Boundary exige mock | `export LLM_MODE=mock`; startup com overlay isolado; não basta mudar só o shell |
| Chave ausente/modelo sem permissão | seção 2.5; se persistir, fallback; não projetar credenciais |
| Visão vazia ou Supply diferente | selecionar Cenário didático; `demo_cockpit.py`; não editar banco/thresholds |
| 100% Registry versus 90% cockpit | métricas/populações distintas; explicar seção 4 |
| JSON com 409/503 na síntese | resposta rejeitada/serviço indisponível; não salvo parcialmente; usar mock preparado |
| Candidato já aprovado | abrir pendente do seed ou extrair novo; não reaprovar item antigo |
| Histórico real unknown | fonte/coorte insuficiente; desconhecido é resultado válido |
| Memória parece vazia | conferir `$AULA4_DIR` e overlay; não substituir diretório pessoal |
| Página/API antiga | build pré-aula; `./scripts/cockpit.sh -f "$AULA4_DIR/isolation.yaml" logs --tail=40 cockpit api` |
| Em fila indefinidamente | conferir `ps`, workers e `/ready`; não culpar LLM sem evidência |
| Relógio apertado | cortar traces/tokens/configuração, nunca revisão humana e fechamento |

## 12. Regressão fora do horário de aula

Rodar em mock, com memória isolada. Playwright cria e aprova conteúdo **exclusivamente sintético**.

```bash
export LLM_MODE=mock
./scripts/cockpit.sh -f "$AULA4_DIR/isolation.yaml" up -d --wait
LESSON02_INTEGRATION=1 LESSON03_INTEGRATION=1 LESSON03_TRACING_INTEGRATION=1 LESSON04_INTEGRATION=1 \
  uv run --extra lesson04 pytest -q
uv run --extra lesson04 control-tower smoke
npm --prefix web ci
npm --prefix web run typecheck
./scripts/cockpit.sh -f "$AULA4_DIR/isolation.yaml" build cockpit
cd web
npx playwright install chromium
npm test
cd ..
uv run --extra lesson04 python scripts/demo_cockpit.py
```

Build de produção validado via Docker, que executa `next build`; não depender de build nativo durante a aula.
Instalação de pacotes/imagens requer rede; mock é offline depois de preparado.
Ao encerrar a aula, se quiser parar os serviços, aguardar trabalho terminar e executar:

```bash
./scripts/cockpit.sh -f "$AULA4_DIR/isolation.yaml" stop
```

Sem apagar volumes. Manter `artifacts/aula4-current.txt` e a pasta apontada para reprodução.
Não fazer push, tags ou mudanças de lifecycle como parte do ensaio.
