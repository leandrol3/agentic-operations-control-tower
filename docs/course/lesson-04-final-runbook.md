# Aula 4 — Operating the Agentic Workforce
## Da observabilidade à decisão operacional

**Roteiro único do professor · 240 minutos · candidato `codex/lesson-04-cockpit`.**
Base pedagógica validada sobre `b3823b2`; extensão autorizada: Demo 6, Codex → MCP → Maestro. Este roteiro consolida start, complete e cockpit;
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
| 03:00–03:08 | 8 | Síntese visual das decisões já observadas | Qual decisão o cockpit permite tomar? |
| 03:08–03:15 | 7 | Maestro: conceito, fontes e limites | Quem coordena a melhoria? |
| 03:15–03:33 | 18 | Demo 5 — melhoria e conhecimento | Da atenção ao conhecimento reutilizado |
| 03:33–03:40 | 7 | Demo 6 — Codex → MCP → Maestro | A mesma gestão fora do cockpit |
| 03:40–03:50 | 10 | Segundo Cérebro: discussão e margem | Quando uma resposta vira conhecimento? |
| 03:50–04:00 | 10 | Learning Loop, maturidade e arco final | O que significa uma empresa aprender? |
| **Total** | **240** | **Sem instalação ou build ao vivo** | |

Há **105 min explícitos de contexto/teoria até a Demo 4**, além dos 15 min conceituais seguintes.
O cockpit entra na Demo 2 e permanece como interface principal.
Cada demo de 15 min reserva 2 min para transição/espera. A demo final tem 2 min internos de margem.
Dos 10 min após a Demo 6, preservar 6 min de reflexão e usar no máximo 4 para recuperação.
**Hard stop:** às 03:50 iniciar o fechamento, mesmo que alguma exploração opcional não tenha ocorrido.
Tempo de máquina não é tempo de fala: os números técnicos do relatório não simulam uma aula ministrada.

### Índice das demonstrações

1. **Demo 1 — Same Capability, Different Boundary:** HTTP e MCP acessam a mesma capability.
2. **Demo 2 — Registry, Goals e Lifecycle:** identidade, expectativa e estado administrativo.
3. **Demo 3 — Normal vs Degraded + Economics:** conclusão, qualidade e custo.
4. **Demo 4 — Collect → Interpret → Recommend:** sinais e decisão determinística.
5. **Demo 5 — Da recomendação ao conhecimento:** Maestro, extração, revisão e reutilização.
6. **Demo 6 — Codex → MCP → Maestro:** a mesma gestão e memória fora do cockpit.

### Orientação de condução: a interface acompanha o conceito

**Demo 1:** terminal para demonstrar a fronteira HTTP/MCP. **Demos 2–4:** cockpit para
identidade → evidências → decisão. **Demo 5:** partir da decisão já compreendida para
Maestro → revisão humana → memória. **Demo 6:** Codex acessa o Maestro via MCP.

O terminal fica preparado para contingência, não é um segundo roteiro obrigatório.
Mostre primeiro a evidência na tela, explique seu significado e só então abra um recorte de código,
quando indicado. Não percorra todos os menus nem repita o cadastro na Demo 5.
Use **Suprimentos (Supply)** como fio condutor. Mantenha **Fonte de dados → Cenário didático**
nas Demos 2–6. Diga: “Os dados são sintéticos; as regras e a navegação são as do sistema.
Mais adiante, o Maestro usará LLM real para interpretar esses mesmos dados.”
O modo do serviço (mock/OpenAI) e a fonte de dados (didática/durável) são escolhas diferentes.

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

### 2.4 Preparar execuções duráveis e outputs de contingência

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
No VS Code abra os arquivos da seção 10. Se o comando `code` já estiver instalado:

```bash
code src/control_tower/application.py src/control_tower/mcp/tools.py src/control_tower/control_plane/registry.py src/control_tower/control_plane/decision_engine.py src/control_tower/cockpit/assistance.py
```

Se não estiver, use Arquivo → Abrir arquivo no VS Code; não instalar a integração durante a aula.
Fonte de terminal 20–24; navegador 1440×900 ou 1920×1080, zoom 100%. Fechar abas de credenciais.

### Preparar a navegação visual antes de projetar

1. Abrir `http://localhost:3000`; usar janela ampla, preferencialmente 1440 × 900.
2. Selecionar **Fonte de dados → Cenário didático** e confirmar o aviso de dados sintéticos.
3. Ensaiar **Agentes → Suprimentos → Resumo / Metas / Lifecycle**.
4. Em **Operações**, testar o filtro `63cfd5c6` (normal) e depois substituí-lo por
   `5d04239c` (degradada). Abrir cada linha. Para voltar, clicar **Operações** no menu lateral.
5. Conferir **Agentes → Suprimentos → Economia / SLOs / Decisões** e a proposta **Intervir**.
6. Deixar a aba em **Visão Geral** para começar a Demo 2. Não abrir nem enviar pergunta ao Maestro ainda.
7. Manter os outputs da seção 2.4 salvos. Eles são execuções duráveis mock e fixtures técnicas;
   não são as seis linhas sintéticas da tela. Anunciar a troca de fonte se precisar usá-los.

Não há comando de terminal obrigatório nas Demos 2–4 quando a interface está funcionando.
Os comandos de contingência abaixo são completos e rodam no terminal preparado na seção 2.

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
- [ ] Codex autenticado; novacore-maestro conectado; fallback MCP mock salvo; terminal Codex aberto.
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
não prova execução distribuída atual. Reservar o cliente Codex para a Demo 6, quando ele consultará o Maestro e o conhecimento aprovado.
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

### 01:15–01:30 · Demo 2 — conhecer o agente pela interface

**Objetivo:** identificar responsabilidade, meta e estado administrativo sem ler um dump do cadastro.
**Entrada:** cockpit em Visão Geral, fonte Cenário didático. **Saída:** Suprimentos / Lifecycle.

| Minuto | Clique / gesto do professor | Fala e resultado esperado |
|---|---|---|
| 0–2 | Visão Geral: apontar 7 agentes e 1 em atenção | “Temos uma workforce registrada. Atenção é um convite para investigar.” Não abrir Maestro. |
| 2–5 | Menu **Agentes** → **Suprimentos** → **Resumo** | Apontar papel, responsáveis, versão e tools de estoque/fornecedores. “O cadastro define responsabilidade e capacidades.” Modelo configurado não prova chamada LLM nesta tela. |
| 5–8 | Aba **Metas** | Ler cobertura de evidências alternativas: alvo **90%**, atual **74%**, gap **−16 p.p.**, 50 observações. “37 de 50 observações têm cobertura completa.” Não apresentar como taxa de sucesso das seis execuções. |
| 8–10 | Aba **Lifecycle** | Apontar Ativo, seis estados e transições permitidas. “Ativo é estado administrativo. Não garante estar dentro da meta.” Sugestão de revisão não foi aplicada. |
| 10–11 | Abrir o recorte `BusinessGoal` / `AgentRecord` da seção 10 | “A tela apresenta um contrato explícito.” Mostrar campos, não implementação inteira. |
| 11–13 | Voltar a Lifecycle; perguntar aos alunos | “Um agente ativo pode estar fora da meta? Uma recomendação deveria mudar seu estado sozinha?” |
| 13–15 | Margem e transição | “Sabemos quem é e o que esperamos. Agora precisamos avaliar o que entregou.” |

Não clicar em transição inexistente. Finance continua determinístico; cadastro de agente não implica LLM.
A recomendação de intervenção será explicada na Demo 4; não antecipar a conversa com Maestro.

**Fallback se a UI falhar:** anunciar “Vou mostrar o contrato técnico do cadastro”.

```bash
uv run --extra lesson04 python scripts/demo_lesson04.py registry
uv run --extra lesson04 python scripts/demo_lesson04.py registry supply
```

O Registry técnico usa alvo de conclusão de etapa **100%**, diferente da cobertura didática **90%**
do cockpit. Não comparar os dois como se fossem a mesma métrica. Se o serviço também falhar,
abrir `src/control_tower/control_plane/registry.py` e mostrar os contratos já preparados.

## 5. Quality e Economics — teoria e Demo 3

### 01:30–01:50 · teoria

8 min status/qualidade; 6 min incerteza e evidência; 6 min usage/pricing/custo.
**Fala:** “Completed é status de runtime. Não é sinônimo de qualidade. Quality é um vetor antes
que seja uma nota. Não disponível não significa zero. Confiança declarada não é probabilidade calibrada.”
**Pergunta:** “Quanto custa um agente?” Distinguir consumo LLM, infraestrutura, pessoas, workflow e decisão.
Pricing é configuração datada; usage é medição; custo é estimativa. Não comparar USD com BRL por soma.

### 01:50–02:05 · Demo 3 — comparar resultados visualmente

**Objetivo:** separar conclusão, qualidade, fallback e custo. Fonte **Cenário didático**.
As execuções ilustrativas já existem; não submeter nova carga durante esta demo.

| Minuto | Clique / gesto do professor | Fala e resultado esperado |
|---|---|---|
| 0–2 | Menu **Operações**, ler colunas Status e Resultado | “Concluída é uma informação operacional. Vamos investigar o resultado.” |
| 2–4 | Em **Filtrar execuções**, digitar `63cfd5c6`; abrir a linha | Em **Resultado e revisão**, mostrar Recomendação e aprovação pendente. Em qualidade, distinguir confiança declarada de evidência validada. |
| 4–7 | Menu **Operações**; substituir filtro por `5d04239c`; abrir a linha | Mostrar Recomendação degradada, fallback e aprovação pendente. “As duas terminaram; não são resultados equivalentes.” Não clicar Extrair aprendizado ainda. |
| 7–10 | Menu **Agentes** → **Suprimentos** → **Economia** | Apontar estimativa **0,00056 USD** do papel no cenário e limites de cobertura. “Custo do papel, custo do workflow e valor de negócio têm escopos distintos.” |
| 10–13 | Perguntar e comparar verbalmente | “Uma execução concluída pode exigir intervenção? Não disponível significa custo zero?” Revisão humana também é obrigatória na normal. |
| 13–15 | Margem e transição | “Custo nos diz quanto consumimos. Valor exige evidência do que mudou no negócio.” |

O filtro aceita incidente, status ou UUID; **não pesquisar por ‘degraded’**.
Para voltar da execução, clicar **Operações** no menu lateral. Apagar/substituir o filtro anterior.

| Evidência das duas execuções sintéticas | Normal `63cfd5c6` | Degradada `5d04239c` |
|---|---|---|
| Status | Concluída | Concluída |
| Resultado | Recomendação | Recomendação degradada |
| Fallback | Não | Sim |
| Aprovação | Pendente | Pendente |
| Tokens de entrada | 6.000 sintéticos | Não disponível |
| Custo LLM estimado no dado da fixture | 0,00336 USD | Não disponível |

Os valores não são consumo real de provider. O custo pequeno no detalhe de execução pode aparecer
arredondado como zero; usar a aba **Economia** do agente para mostrar precisão, explicando o escopo
menor de **0,00056 USD**. Nunca dizer “gratuito”. Não confundir confiança declarada com probabilidade
calibrada nem campos de completude/conformidade indisponíveis com avaliação semântica positiva.
As seis execuções são ilustrações independentes das 50 observações da meta de Supply.

**Fallback preparado:** anunciar que as saídas abaixo são do ensaio durável em mock,
no qual tokens/custo são indisponíveis inclusive na execução normal.

```bash
cat "$AULA4_DIR/quality.txt"
cat "$AULA4_DIR/economics.txt"
```

Se precisar consultar novamente o ensaio com serviço disponível:

```bash
uv run --extra lesson04 python scripts/demo_lesson04.py quality
uv run --extra lesson04 python scripts/demo_lesson04.py economics
DEGRADED_ID="$(uv run python -c 'import json; print(json.load(open("artifacts/lesson04-demo.json"))["degraded"])')"
uv run --extra lesson04 python scripts/demo_lesson04.py economics "$DEGRADED_ID"
```

Tentativas na falha artificial não são chamadas faturadas. Não usar seu contador como fatura.

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

### 02:45–03:00 · Demo 4 — evidências e decisão no mesmo agente

**Objetivo:** explicar Collect → Interpret → Recommend usando Suprimentos.
**Entrada:** Agentes → Suprimentos, fonte Cenário didático. O serviço já pode estar OpenAI;
a decisão exibida continua sendo produzida por regras determinísticas.

| Minuto | Clique / gesto do professor | Fala e resultado esperado |
|---|---|---|
| 0–3 | Aba **Metas**, depois **Qualidade** | **Collect:** recuperar 90% / 74% / −16 p.p. e 28% de resultados degradados no contexto do workflow. “São sinais com fonte e escopo; não uma explicação causal.” |
| 3–5 | Aba **SLOs** | **Interpret:** comparar cobertura 74% com mínimo 90%; degradação 28% com limite 10%. Mostrar violação e unidade. Não ler todos os SLOs. |
| 5–7 | Aba **Decisões** | **Recommend:** apontar **Intervir**, evidências e aprovação obrigatória. “Uma regra transforma o sinal em proposta. Ainda não existe autorização para agir.” |
| 7–9 | Aba **Lifecycle**, depois **Economia** | Ativo → Em revisão é sugestão. Na área de valor, distinguir penalidade potencial **R$ 140.000**, cenário **R$ 12.500** e valor realizado desconhecido. |
| 9–10 | Código: `decision_engine.recommend` | Mostrar primeira regra aplicável e retorno. Não há chamada LLM nem execução da intervenção. |
| 10–13 | Menu **Decisões** → **Suprimentos · Intervir** | Ler uma evidência no detalhe; mostrar o botão de perguntar ao Maestro, sem enviar ainda. “A regra diz que há motivo para intervir. Quem ajuda a planejar a melhoria?” |
| 13–15 | Margem e transição | Deixar a recomendação pronta para a Demo 5. |

Collect, Interpret e Recommend descrevem a lógica já calculada; não são três botões a executar.
Degradação é contexto do workflow, não prova de culpa de Supply. A primeira regra aplicável tem
precedência: não atribuir a intervenção exclusivamente ao gap de cobertura. Nenhuma compra,
pausa de worker, troca de modelo ou transição de lifecycle é executada pela tela.

**Fallback:** o comando abaixo usa outra fixture, de **Logistics**, para explicar o mesmo pipeline.
Ela recomenda **Otimizar**, não Intervir. Anunciar a diferença de agente, métrica e fonte.

```bash
uv run --extra lesson04 python scripts/demo_lesson04_complete.py --fixture optimize --agent logistics --section pipeline
```

Esperado: alvo técnico 100%, atual 66,666667%, custo crescente, qualidade desconhecida,
Otimizar e aprovação necessária. Roda sem Docker. Se necessário usar a gravação:

```bash
cat "$AULA4_DIR/pipeline.txt"
```

Exploração opcional **fora dos 15 minutos**: fixture de custo acima do limite.

```bash
uv run --extra lesson04 python scripts/demo_lesson04_complete.py --fixture cost --agent logistics --section slo
```

Esperado: meta 100%, custo USD 0,02016 acima de 0,01. `modo=openai` nos eventos sintéticos
não significa chamada ao provider. Não trocar a narrativa principal para este segundo caso.

## 7. Das decisões observadas ao Maestro (03:00–03:15)

**03:00–03:08:** manter a recomendação de Suprimentos visível. Não reabrir Visão Geral nem
repetir o cadastro. Pedir que os alunos reconstruam: identidade → meta → evidências → limite → proposta.
Retomar as populações: 50 observações de cobertura Supply; janelas técnicas dos outros papéis;
6 execuções ilustrativas independentes. Não dividir as seis execuções para reproduzir os 74%.
**Pergunta:** “Qual evidência sustenta intervir? O que ainda precisamos investigar antes de mudar algo?”

**03:08–03:15:** “The Maestro is the Chief of Staff of the Agentic Workforce.”
Supervisor coordena **uma execução**. Maestro coordena **propostas de melhoria da workforce**.
Consulta fontes, sintetiza diagnóstico, propõe plano e responsabilidades. Staffs são papéis propostos,
não novos agentes executando. “LLMs interpretam e julgam. Código determinístico mede e valida.”
Anunciar: “Até aqui medimos e aplicamos regras. Agora vamos pedir uma interpretação e um plano.”
Não enviar a pergunta ainda; a espera do provider está prevista na Demo 5.

## 8. Demo 5 — da recomendação ao conhecimento em 18 minutos (03:15–03:33)

**Pré-condição:** OpenAI, gpt-4.1-mini, fonte Cenário didático, pasta de conhecimento isolada.
Texto do LLM varia; medidas, fontes, estado e autorização não. Cronometrar a partir da
recomendação **Suprimentos · Intervir**, já explicada na Demo 4. Não repetir Overview/Agent 360.
O LLM real interpreta dados sintéticos; isso não transforma o cenário em evidência de produção.

| Tempo da demo | Gestos e tela | Fala / evidência |
|---|---|---|
| 00:00–01:00 | Na recomendação, clicar **Perguntar ao Maestro sobre esta recomendação** | “Já sabemos por que investigar. Vamos planejar como melhorar.” Conferir contexto Suprimentos/recomendação. |
| 01:00–05:00 | Enviar **Como posso melhorar este agente?** | Ler diagnóstico curto, uma hipótese, um passo do plano, um staff e Fontes utilizadas. Distinguir evidência consultada de hipótese proposta. |
| 05:00–06:00 | Menu **Operações**; filtrar `63cfd5c6`, abrir execução e clicar **Extrair aprendizado** | “O plano não foi implantado. Vamos extrair uma lição da execução existente, não um suposto resultado da melhoria.” |
| 06:00–10:00 | Ler candidato, origem, observações e inferência; revisar usando formulário abaixo | Aprovar somente se sustentado. Caso contrário rejeitar e usar referência curada para demonstrar retrieval. |
| 10:00–12:00 | Menu **Segundo Cérebro**; abrir item aprovado, lista, grafo e feed | Apontar origem, revisor e limites. “A experiência agora tem memória persistida e revisão explícita.” |
| 12:00–14:00 | Voltar ao **Maestro**; perguntar **O que aprendemos hoje sobre Supply? Use o conhecimento aprovado.** | Conferir título do item nas fontes. Se não aparecer, declarar. Conhecimento pendente não vira verdade; retrieval não treina pesos. |
| 14:00–16:00 | Mostrar **Learning Loop** brevemente e guardar título da referência usada | “Propusemos, revisamos e reutilizamos conhecimento. Não demonstramos melhoria implantada.” Preparar a mesma referência para a Demo 6; maturidade fica para o fechamento. |
| 16:00–18:00 | Margem de provider, leitura e transições | Se disponível, perguntar: “O que foi aprovado: o conhecimento, o plano ou uma ação empresarial?” |

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
Se necessário reiniciar, usar a seção 12 e anunciar a mudança de modo. Não há fallback silencioso.
No minuto 10, se a revisão ainda não terminou, não aprovar às pressas: usar referência curada no Segundo Cérebro.
Na tabela SLO, um custo muito pequeno pode aparecer arredondado como `0`; a aba Economia mostra
`0,00056 USD` no cenário. Não interpretar o arredondamento como consumo gratuito.
Ao abrir execução/conhecimento a partir do Agent 360, o título principal pode continuar “Suprimentos”;
o breadcrumb e o título do documento indicam a área atual. Use o menu lateral para remover essa ambiguidade.
Até o minuto 16, concluir a passagem pelo Learning Loop e preparar a Demo 6. Máximo absoluto
20 min; recuperar até 2 min da discussão seguinte, preservando a revisão humana sem pressa.

## 9. Demo 6 — Codex → MCP → Maestro (03:33–03:40)

**Objetivo:** demonstrar acesso à mesma gestão por outro cliente, sem duplicar inteligência.
**Mensagem:** “A interface mudou. As capacidades, as evidências e os limites de autorização permaneceram.”

```text
Professor → Codex (cliente MCP) → ask_maestro
→ mesmo serviço Conversations/Maestro → Control Plane + conhecimento aprovado
→ proposta persistida na mesma memória do cockpit
```

Não afirmar “qualquer chatbox”. É um **cliente compatível com MCP e configurado para este transporte**.
Neste LAB, conexão local stdio por Docker exec; não é endpoint remoto público nem federação empresarial.
A tool usa o serviço Python diretamente, sem segundo grafo e sem fazer um POST HTTP interno.

### Preparação do Codex — antes da aula, depois de atualizar a imagem

O startup `up -d --build --wait` da seção 2.3 inclui o código novo na imagem da API.
O launcher usa o container API já iniciado, seu modo LLM, sua chave e seu volume de conhecimento.
**Não precisa carregar a chave OpenAI dentro do Codex.** Codex usa a autenticação própria;
Maestro usa a configuração do container. São duas camadas de inferência, com consumos distintos.

Em outro terminal, na raiz do repositório:

```bash
CODEX_BIN="$(command -v codex || true)"
if [ -z "$CODEX_BIN" ]; then
  for candidate in \
    /Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex \
    /Applications/Codex.app/Contents/Resources/codex \
    /Applications/ChatGPT.app/Contents/Resources/codex; do
    if [ -x "$candidate" ]; then
      CODEX_BIN="$candidate"
      break
    fi
  done
fi
if [ ! -x "$CODEX_BIN" ]; then
  printf '%s\n' 'Codex CLI não encontrado. Interrompa este bloco e confira a instalação.'
else
"$CODEX_BIN" --version
"$CODEX_BIN" login status
"$CODEX_BIN" mcp add novacore-maestro -- /bin/bash "$PWD/scripts/start_maestro_mcp.sh"
"$CODEX_BIN" mcp get novacore-maestro
"$CODEX_BIN" mcp list
"$CODEX_BIN"
fi
```

Se `login status` indicar ausência de autenticação, executar `"$CODEX_BIN" login` fora da projeção,
concluir no navegador e repetir o status. Não instalar/atualizar o cliente durante a aula.
O registro `novacore-maestro` é separado de `novacore`, preservando a Demo 1 histórica.
Não cadastrar novamente a cada pergunta. `mcp list` confirma configuração, não a execução da ferramenta.
No Codex interativo, digitar `/mcp` e conferir `novacore-maestro` conectado e `ask_maestro` disponível.
Se aparecer revisão de permissão, conferir servidor e argumentos, mantendo as aprovações normais.
Não desabilitar sandbox nem usar bypass. Deixar a sessão aberta antes de começar a aula.

**Catálogo:** três tools de incidente existentes + `ask_maestro` neste launcher opcional.
O launcher antigo continua expondo somente as três tools da Aula 4 start.
Nesta demo usar **somente ask_maestro**; não submeter incidentes OpenAI adicionais.

### Roteiro de sete minutos

| Minuto | Ação / fala |
|---|---|
| 0–1 | Mostrar conexão já pronta. “Saímos do cockpit; continuamos acessando a mesma organização.” |
| 1–3 | Enviar primeiro prompt; mostrar chamada `ask_maestro` e a síntese curta. |
| 3–5 | Enviar segundo prompt; apontar a lição aprovada na Demo 5 e suas fontes. |
| 5–6 | Voltar a Supply no cockpit, Atualizar dados, mostrar Última análise do Maestro. |
| 6–7 | Pergunta aos alunos e margem: “Mudar a interface deveria mudar as permissões?” |

**Prompt 1 — copiar no Codex:**

> Use somente a ferramenta ask_maestro do servidor MCP novacore-maestro. Não use shell,
> não altere arquivos e não submeta incidentes. Envie request com question="Como posso melhorar
> o agente de Supply?", agent_id="supply" e source="didactic". Resuma em português, em até
> cinco tópicos: diagnóstico, hipótese, proposta, fontes e aprovação necessária. Identifique
> o que veio do Maestro; não acrescente conclusões suas. Guarde o session_id para a próxima pergunta.

**Prompt 2 — copiar na mesma sessão:**

> Use novamente somente ask_maestro de novacore-maestro, reutilizando o session_id retornado.
> Envie question="Que conhecimento aprovado sustenta essa proposta?", agent_id="supply"
> e source="didactic". Mostre os títulos dos documentos aprovados citados nas evidências,
> incluindo a lição recém-aprovada se ela estiver presente. Se não estiver, diga isso explicitamente.
> Não invente fonte, não aprove conhecimento e não execute o plano. Responda em até cinco tópicos.

**Esperado:** gerador OpenAI/gpt-4.1-mini (ou mock explicitamente anunciado), Supply 74/90,
plano `proposed`, `requires_human_approval=true`, fontes verificáveis e conhecimento somente aprovado.
Copiar o `plan_id` apenas se necessário para comparar; não projetar o JSON inteiro.
No cockpit: menu Agentes → Suprimentos → Atualizar dados → Última análise do Maestro.
O plano MCP está no mesmo filesystem e fica visível. Histórico do chat é **local a cada processo**:
o chat MCP não é a sessão do browser. Reiniciar a conexão perde histórico; planos e conhecimento persistem.
As sínteses não precisam ter texto idêntico entre interfaces, porque o modelo pode variar.

**Fala:** “O Codex é o cliente. O Maestro continua sendo nosso Chief of Staff. As regras permanecem
no Control Plane. MCP não dá autorização para aprovar conhecimento, mudar lifecycle ou executar uma compra.”
**Pergunta:** “O que precisa ser compartilhado: a tela, o histórico inteiro do chat ou capacidades e memória validada?”
**Transição:** “A experiência aprovada pode informar outra interface. É assim que a memória começa a servir à organização.”

### Validação e reprodução não interativa

O ensaio desta extensão usou **Codex CLI real**, duas chamadas MCP reais e Maestro OpenAI real:
53,28 s no total; mesma sessão; planos visíveis no snapshot HTTP do cockpit. A sessão interativa
`/mcp` e a interface Desktop não foram operadas neste ensaio. Os comandos de registro acima são
para preparação do professor; a configuração de teste foi temporária, sem alterar seu cadastro global.

Para reproduzir a variante ensaiada, com Codex já autenticado, executar na raiz (substitui as duas
perguntas interativas; **não rodar ambas as variantes**):

```bash
"$CODEX_BIN" exec --ephemeral --ignore-user-config --approve-for-me \
  -c 'mcp_servers.novacore-maestro.command="/bin/bash"' \
  -c "mcp_servers.novacore-maestro.args=[\"$PWD/scripts/start_maestro_mcp.sh\"]" \
  -c 'mcp_servers.novacore-maestro.startup_timeout_sec=30' \
  -c 'mcp_servers.novacore-maestro.tool_timeout_sec=60' \
  'Use somente ask_maestro do servidor novacore-maestro. Não use shell, não leia ou altere arquivos e não submeta incidentes. Faça duas chamadas: primeiro question="Como posso melhorar o agente de Supply?", agent_id="supply", source="didactic"; depois reutilize o session_id e envie question="Que conhecimento aprovado sustenta essa proposta?" com o mesmo agente e fonte. Não repita em caso de falha. Resuma o retorno do Maestro em até oito tópicos, com fontes, plan_ids e aprovação necessária. Não invente conclusões nem execute ações.'
```

`--approve-for-me` usa revisão automática normal; não desativa sandbox ou aprovações.
A sessão efêmera não preserva o chat do cliente depois do comando. Os planos permanecem no serviço.

### Fallback da Demo 6

Se Codex/auth/conexão falhar, não gastar os sete minutos configurando. No terminal da raiz:

```bash
uv run --extra lesson04 python scripts/demo_maestro_mcp.py
```

Este cliente SDK faz **duas consultas reais via MCP**, sem Codex. Usa o modo atual do container;
em OpenAI faz duas chamadas pagas. Executar apenas se a conversa Codex não funcionou.
Preparar saída mock **antes da aula, enquanto a stack está mock**, para contingência total:

```bash
uv run --extra lesson04 python scripts/demo_maestro_mcp.py | tee "$AULA4_DIR/maestro-mcp-mock.txt"
```

Se provider ou Docker também falhar: `cat "$AULA4_DIR/maestro-mcp-mock.txt"`.
Anunciar gravação mock do ensaio. Não afirmar que Codex foi validado apenas porque o SDK funcionou.
Se as duas consultas ultrapassarem o orçamento, mostrar uma resposta e o conhecimento aprovado,
concluir a mensagem e avançar; hard stop 03:40, consumindo no máximo a margem da discussão seguinte.

## 10. Código: somente seis recortes, 30–60 segundos cada

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

Os três últimos recortes podem ficar para os 10 min de discussão após a Demo 6; não quebrar o fluxo integrado.
**Pronto antes:** Compose, Next.js, CSS, API, SQL, fixtures, schema, SDK, pricing, testes e seeds.
Nenhum boilerplate ao vivo. Não mostrar `.keys`, prompts extensos, dumps integrais ou código de infraestrutura.

## 11. Segundo Cérebro, Learning Loop e fechamento

### 03:40–03:50 · reflexão (10 min; até 4 de reserva)

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

## 12. Fallbacks copiáveis e troubleshooting

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

## 13. Regressão fora do horário de aula

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
