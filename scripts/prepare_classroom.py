"""Gera materiais estáticos da aula a partir do código e das views reais; sem rede."""
from pathlib import Path
from html import escape
import json

from control_tower.graph.workflow import build_graph
from control_tower.tools import Tools
from control_tower.views import VIEWS, show

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/course/classroom'
OUT.mkdir(parents=True, exist_ok=True)
tools = Tools(ROOT)
incident = tools.load_incident(ROOT / 'incidents/incident_001.json')

SNIPPETS = [
    ('shared-state', 'Shared state: canais de evidência', 'graph/state.py', 120, 129),
    ('specialist-output', 'Specialist output: Supply', 'agents/specialists.py', 7, 20),
    ('supervisor', 'Supervisor: plano explícito', 'agents/supervisor.py', 6, 17),
    ('langgraph-edges', 'LangGraph: nós e transições', 'graph/workflow.py', 98, 120),
    ('parallel-join', 'Paralelismo: esperar todos antes de consolidar', 'graph/workflow.py', 109, 123),
    ('finance', 'Finance: composição determinística de custo', 'scenarios.py', 82, 93),
    ('challenger', 'Challenger: saldo, piso e política de frete', 'agents/challenger.py', 55, 70),
    ('recommendation', 'Recommendation: contrato existente', 'graph/workflow.py', 67, 79),
]
manifest = []
md = ['# Snippets para projeção', '', 'Recortes do código real. Mostrar só quando esclarecem uma decisão;',
      'não digitar nem navegar por diffs durante a aula. Números de linha referem-se à revisão atual.', '']
for key, title, name, first, last in SNIPPETS:
    path = ROOT / 'src/control_tower' / name
    snippet = '\n'.join(path.read_text().splitlines()[first-1:last])
    entry = dict(id=key, title=title, path=f'src/control_tower/{name}', start=first, end=last, code=snippet)
    manifest.append(entry)
    md += [f'## {title}', '', f'`{entry["path"]}:{first}–{last}` — {last-first+1} linhas.', '',
           '```python', snippet, '```', '']
(OUT/'snippets.md').write_text('\n'.join(md), encoding='utf-8')
(OUT/'snippets.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

views = {}
for view in VIEWS:
    text, blocked = show(tools, incident, view)
    if blocked:
        raise RuntimeError(text)
    if view == 'coordination':
        # Snapshot sem tempo de máquina e sem ordenação de threads apresentada como determinística.
        text = '\n'.join(text.splitlines()[:-1])+'\nOrdem dos ramos pode variar; compare ao vivo com espera artificial.'
    views[view] = text
    (OUT/f'{view}.txt').write_text(text+'\n',encoding='utf-8')
text, blocked = show(tools, incident, 'coordination', fail_specialist='logistics')
assert blocked
(OUT/'missing-evidence.txt').write_text(text+'\n',encoding='utf-8')

# Layout previamente renderizado do caminho principal; os caminhos de bloqueio são uma legenda explícita.
positions = {
    '__start__': (55,135,145,'Incidente'), 'supervisor': (265,135,210,'Supervisor'),
    'supply': (595,35,200,'Supply'), 'production': (595,135,200,'Production'),
    'logistics': (595,235,200,'Logistics'), 'consolidation': (1000,135,250,'Join / consolidação'),
    'finance': (1000,390,250,'Finance'), 'challenger': (660,390,220,'Challenger'),
    'recommendation': (310,390,230,'Recommendation'), 'human_approval': (310,590,230,'Aprovação pendente'),
    '__end__': (660,590,220,'Fim: sem ações'),
}
graph = build_graph(tools).get_graph()
edges = [(e.source,e.target) for e in graph.edges]
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="810" viewBox="0 0 1440 810" role="img" aria-labelledby="title desc">',
       '<title id="title">Coordenação NovaCore — LangGraph</title>',
       '<desc id="desc">Supervisor distribui três especialistas; join aguarda todos; Finance, Challenger, Recommendation e aprovação humana. Erros podem bloquear.</desc>',
       '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="none" stroke="#526880"/></marker></defs>',
       '<rect width="1440" height="810" fill="#f5f7fb"/>',
       '<text x="55" y="62" font-family="sans-serif" font-size="30" fill="#17314b">Uma organização de responsabilidades explícitas</text>']
for source, target in edges:
    if source not in positions or target not in positions:
        continue
    x,y,w,_=positions[source]; a,b,v,_=positions[target]
    if b==y:
        if a>x: sx,sy,tx,ty=x+w,y+30,a,b+30
        else: sx,sy,tx,ty=x,y+30,a+v,b+30
    elif abs(a-x)<20:
        sx,sy,tx,ty=x+w/2,y+60,a+v/2,b
    else:
        sx,sy,tx,ty=x+w,y+30,a,b+30
    if source=='recommendation': sx,sy,tx,ty=x+w/2,y+60,a+v/2,b
    if source in ('supply','production','logistics'):
        sx,sy,tx,ty=x+w,y+30,a,b+30
    svg.append(f'<path data-source="{source}" data-target="{target}" d="M{sx} {sy} C{(sx+tx)/2} {sy}, {(sx+tx)/2} {ty}, {tx} {ty}" fill="none" stroke="#526880" stroke-width="3" marker-end="url(#arrow)"/>')
for name,(x,y,w,label) in positions.items():
    fill='#dcefeb' if name=='human_approval' else '#ffffff'
    svg += [f'<rect x="{x}" y="{y}" width="{w}" height="60" rx="12" fill="{fill}" stroke="#c8d4df" stroke-width="2"/>',
            f'<text x="{x+w/2}" y="{y+37}" text-anchor="middle" font-family="sans-serif" font-size="21" fill="#17314b">{escape(label)}</text>']
svg += ['<text x="870" y="276" font-family="sans-serif" font-size="20" fill="#526880">aguarda os 3</text>',
        '<rect x="55" y="712" width="1330" height="58" rx="10" fill="#f8e9dc"/>',
        '<text x="77" y="748" font-family="sans-serif" font-size="21" fill="#703c20">Saídas de bloqueio: Supervisor, Join, Finance ou Challenger → blocked → fim.</text>',
        '<text x="55" y="797" font-family="sans-serif" font-size="17" fill="#526880">Caminho principal extraído do grafo real. Mock: coordenação real, especialistas determinísticos; sem raciocínio de LLM.</text>', '</svg>']
(OUT/'graph.svg').write_text('\n'.join(svg)+'\n',encoding='utf-8')
(OUT/'graph-edges.json').write_text(json.dumps(edges,indent=2)+'\n')

# HTML local: uma tela por conceito; sem rede, build de frontend ou navegação por resultados extensos.
css='''body{margin:0;background:#f5f7fb;color:#17314b;font-family:Arial,sans-serif}header{padding:16px 32px;border-bottom:1px solid #c8d4df;display:flex;gap:22px;align-items:center}select,button{font:inherit;padding:8px;background:white;border:1px solid #b9c9d8;border-radius:6px}main{padding:24px 38px}section{display:none}section.active{display:block}h1{font-size:32px;margin:0 0 20px}p,li{font-size:25px;line-height:1.45}pre{font-family:ui-monospace,Menlo,monospace;font-size:clamp(14px,1.55vw,22px);line-height:1.55;white-space:pre-wrap;margin:0}code{font-family:inherit}.subtitle{font-size:17px;color:#53667b;margin-top:16px}.timeline{display:grid;grid-template-columns:repeat(4,1fr);gap:22px;margin-top:50px}.card{background:white;padding:26px;border:1px solid #c8d4df;border-radius:16px}.date{font-size:32px;font-weight:bold;color:#197c70}.code pre{font-size:clamp(13px,1.16vw,18px);line-height:1.4}.code h1{font-size:26px}.code p{font-size:16px}img{width:100%;max-height:calc(100vh - 130px)}'''
sections=[('context','Contexto', '''<h1>NovaCore: o problema é coordenação</h1><p>Um atraso de M42 conecta fornecedores, estoque, produção, logística e clientes.</p><p>Antes: evento → pessoas → planilhas → reuniões → decisão.</p><p>Objetivo: reduzir o tempo entre evento, investigação e decisão humana.</p><p><strong>Quem precisa saber o quê — e em que momento?</strong></p><p class="subtitle">Empresa e números fictícios; horas para minutos é ilustração, não benchmark.</p>'''),
('theory','Teoria', '''<h1>Do agente à organização</h1><p>Um agente é uma unidade de inteligência.<br>Um sistema multiagente é uma organização.<br>Colocar essa organização em produção é um problema de engenharia.</p><ul><li>Who decides? · Where is the state?</li><li>What happens when it fails? · Can I observe it?</li><li>What does it cost? · Should this even be an agent?</li></ul><p class="subtitle">Mock demonstra state, roles, graph, orchestration, parallelism, consolidation e contracts — sem raciocínio de LLM.</p>'''),
('timeline','Timeline', '''<h1>O evento não confirma atraso do cliente</h1><div class="timeline"><div class="card"><div class="date">01/10</div><p>Evento; estoque inicial.<br>Alpha era esperado.</p></div><div class="card"><div class="date">02/10</div><p>Expresso chega se sair dia 1.<br>Produção usa material de manhã.</p></div><div class="card"><div class="date">03/10</div><p>Beta chega se pedido dia 1.<br>Prazo de CO-001.</p></div><div class="card"><div class="date">08/10</div><p>Novo prazo Alpha.<br>Produzir dia 8 permite entregar dia 9.</p></div></div><p>Produção durante D → entrega até o fim de D+1. Dias corridos, datas fixas.</p><p class="subtitle">Time-to-Decision inclui a decisão humana, ainda pendente; a duração da CLI mede só o workflow.</p>'''),
('graph','Arquitetura','<img src="graph.svg" alt="Grafo real de coordenação com join e aprovação humana"/>')]
labels={'summary':'SP / Campinas','state':'Shared state','specialists':'Especialistas','coordination':'Coordenação','scenarios':'Cenários A–D','challenger':'Challenger','recommendation':'Recomendação'}
for view in VIEWS:
    sections.append((view,labels[view],'<pre>'+escape(views[view])+'</pre><p class="subtitle">Fallback gravado do fixture oficial. Para execução ao vivo: uv run control-tower show INCIDENT-001 '+view+'</p>'))
for item in manifest:
    sections.append((item['id'],'Código · '+item['title'], f'<div class="code"><h1>{escape(item["title"])}</h1><p>{item["path"]}:{item["start"]}–{item["end"]}</p><pre>{escape(item["code"])}</pre></div>'))
html=['<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>NovaCore · Aula 1</title><style>'+css+'</style>',
      '<header><strong>NovaCore · Aula 1</strong><label>Conceito <select id="choose">']
html += [f'<option value="{key}">{escape(title)}</option>' for key,title,_ in sections]
html += ['</select></label><button id="back">←</button><button id="next">→</button></header><main>']
html += [f'<section id="{key}" class="{"active" if n==0 else ""}">{body}</section>' for n,(key,_,body) in enumerate(sections)]
html += ['</main><script>const s=document.querySelector("select");function show(){document.querySelectorAll("section").forEach(x=>x.classList.toggle("active",x.id===s.value));}s.onchange=show;document.querySelector("#next").onclick=()=>{s.selectedIndex=Math.min(s.length-1,s.selectedIndex+1);show()};document.querySelector("#back").onclick=()=>{s.selectedIndex=Math.max(0,s.selectedIndex-1);show()};</script></html>']
(OUT/'index.html').write_text('\n'.join(html)+'\n',encoding='utf-8')
print(f'Materiais gerados em {OUT}')
