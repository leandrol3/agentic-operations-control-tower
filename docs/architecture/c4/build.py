"""Render one editable C4 model into SVG, Mermaid and a student PDF. No application calls."""
from pathlib import Path
import argparse, json, math, html, textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE=Path(__file__).resolve().parent
COLORS={'person':('#17334f','#ffffff'),'system':('#075985','#ffffff'),'container':('#dceef9','#12334f'),'component':('#ddf3ed','#16463e'),'store':('#fff0cf','#624418'),'external':('#e5e7eb','#374151')}
TYPES={'person':'Pessoa / papel','system':'Sistema em foco','container':'Container lógico','component':'Componente','store':'Armazenamento','external':'Sistema externo'}
def font_setup():
 folder=Path('/System/Library/Fonts/Supplemental')
 if (folder/'Arial.ttf').exists():
  pdfmetrics.registerFont(TTFont('Regular',str(folder/'Arial.ttf')))
  pdfmetrics.registerFont(TTFont('Bold',str(folder/'Arial Bold.ttf')))
  return 'Regular','Bold'
 return 'Helvetica','Helvetica-Bold'
REG,BOLD=font_setup()
def wrap(txt,size,width,bold=False):
 out=[];font=BOLD if bold else REG
 for para in txt.split('\n'):
  line=''
  for word in para.split():
   proposed=(line+' '+word).strip()
   if line and pdfmetrics.stringWidth(proposed,font,size)>width:out.append(line);line=word
   else:line=proposed
  out.append(line)
 return out

def svg(d):
 out=['<svg xmlns="http://www.w3.org/2000/svg" width="1140" height="680" viewBox="0 0 1140 680">',
 '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#526574"/></marker></defs>',
 '<rect width="1140" height="680" fill="white"/>']
 if d.get('boundary'):
  out.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in d['boundary'])+'" fill="#f7fafc" stroke="#94a3b8" stroke-dasharray="7 5"/>')
 for e in d['edges']:
  pts=' '.join(f'{x},{y}' for x,y in e['points']);out.append(f'<polyline points="{pts}" fill="none" stroke="#526574" stroke-width="1.8" marker-end="url(#arrow)"/>')
 for n in d['nodes']:
  bg,fg=COLORS[n['kind']];x,y,w,h=n['x'],n['y'],n['w'],n['h']
  out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{bg}" stroke="{fg}" stroke-width="1.1"/>')
  specs=[(TYPES[n['kind']],10,False),(n['title'],15,True),(n['tech'],11.5,False),(n['desc'],12,False)]
  yy=y+15
  for txt,size,bold in specs:
   for line in wrap(txt,size,w-16,bold):
    out.append(f'<text x="{x+w/2}" y="{yy}" text-anchor="middle" font-family="Arial, sans-serif" font-size="{size}" font-weight="{"bold" if bold else "normal"}" fill="{fg}">{html.escape(line)}</text>');yy+=size+3
  assert yy<=y+h+5,(d['id'],n['id'],yy,y+h)
 for e in d['edges']:
  x,y=e['label_at'];ls=wrap(e['label'],12,180)
  ww=max(pdfmetrics.stringWidth(t,REG,12) for t in ls)+12
  out.append(f'<rect x="{x-ww/2}" y="{y-12}" width="{ww}" height="{len(ls)*15+4}" rx="3" fill="white"/>')
  for j,line in enumerate(ls):out.append(f'<text x="{x}" y="{y+j*15}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#334155">{html.escape(line)}</text>')
 out.append('</svg>');return '\n'.join(out)

def mermaid(d):
 ids={n['id'] for n in d['nodes']};assert len(ids)==len(d['nodes'])
 out=['flowchart TB',f'  %% {d["level"]} — {d["title"]}',f'  %% Escopo: {d["scope"]}']
 bounded=[]
 if d.get('boundary'):
  # Document explicit in-scope logical members; geometry is separate from semantics.
  bounded=d.get('inside',[n['id'] for n in d['nodes'] if n['kind']!='external'])
 def declare(n,indent='  '):
  parts=[TYPES[n['kind']],n['title'],n['tech'],n['desc']]
  label='<br/>'.join(html.escape(x,quote=True).replace('\n','<br/>') for x in parts)
  return f'{indent}{n["id"]}["{label}"]'
 if bounded:
  out.append('  subgraph scope["Escopo da vista"]')
  out.extend(declare(n,'    ') for n in d['nodes'] if n['id'] in bounded);out.append('  end')
 out.extend(declare(n) for n in d['nodes'] if n['id'] not in bounded)
 for e in d['edges']:
  assert e['source'] in ids and e['target'] in ids
  label=html.escape(e['label'].replace('\n',' / '),quote=True)
  out.append(f'  {e["source"]} -->|"{label}"| {e["target"]}')
 for kind,(bg,fg) in COLORS.items():out.append(f'  classDef {kind} fill:{bg},stroke:{fg},color:{fg};')
 for n in d['nodes']:out.append(f'  class {n["id"]} {n["kind"]};')
 return '\n'.join(out)+'\n'

WIDTH,HEIGHT=1190,842 # A3 landscape: vector diagrams readable in class and print.
def paragraph(c,text,x,y,width,size=15,leading=22,color='#17334f',bold=False):
 c.setFillColor(HexColor(color));c.setFont(BOLD if bold else REG,size)
 for line in wrap(text,size,width,bold):c.drawString(x,y,line);y-=leading
 return y-12

def header(c,title,subtitle,page):
 c.setFillColor(HexColor('#075985'));c.rect(0,HEIGHT-12,WIDTH,12,fill=1,stroke=0)
 paragraph(c,title,40,HEIGHT-56,1110,24,29,bold=True)
 paragraph(c,subtitle,40,HEIGHT-86,1110,12,17,color='#526574')
 c.setFont(REG,10);c.setFillColor(HexColor('#526574'));c.drawString(40,22,'L3 | NovaCore | Arquitetura atual até a Aula 4 | baseline c5ede1a | 05/10/2026');c.drawRightString(WIDTH-40,22,str(page))

def draw_diagram(c,d):
 # Same model and dimensions used by the editable SVG; no screenshot/rasterization.
 ox,oy=25,65
 def pos(p):return ox+p[0],oy+680-p[1]
 if d.get('boundary'):
  c.setDash(6,4);c.setStrokeColor(HexColor('#94a3b8'));c.setFillColor(HexColor('#f7fafc'))
  p=c.beginPath();p.moveTo(*pos(d['boundary'][0]));[p.lineTo(*pos(z)) for z in d['boundary'][1:]];p.close();c.drawPath(p,stroke=1,fill=1);c.setDash()
 for e in d['edges']:
  c.setStrokeColor(HexColor('#526574'));c.setLineWidth(1.8)
  ps=[pos(z) for z in e['points']]
  for a,b in zip(ps,ps[1:]):c.line(*a,*b)
  a,b=ps[-2:];ang=math.atan2(b[1]-a[1],b[0]-a[0]);p=c.beginPath();p.moveTo(*b)
  for sign in (-1,1):p.lineTo(b[0]-9*math.cos(ang)+sign*4*math.sin(ang),b[1]-9*math.sin(ang)-sign*4*math.cos(ang))
  p.close();c.setFillColor(HexColor('#526574'));c.drawPath(p,stroke=0,fill=1)
 for n in d['nodes']:
  bg,fg=COLORS[n['kind']];x,y=pos([n['x'],n['y']+n['h']]);w,h=n['w'],n['h']
  c.setStrokeColor(HexColor(fg));c.setFillColor(HexColor(bg));c.roundRect(x,y,w,h,8,fill=1,stroke=1)
  yy=y+h-15
  for txt,size,bold in [(TYPES[n['kind']],10,False),(n['title'],15,True),(n['tech'],11.5,False),(n['desc'],12,False)]:
   c.setFillColor(HexColor(fg));c.setFont(BOLD if bold else REG,size)
   for line in wrap(txt,size,w-16,bold):c.drawCentredString(x+w/2,yy,line);yy-=size+3
 for e in d['edges']:
  x,y=pos(e['label_at']);ls=wrap(e['label'],12,180);ww=max(pdfmetrics.stringWidth(t,REG,12) for t in ls)+12
  c.setFillColor(HexColor('#ffffff'));c.roundRect(x-ww/2,y-(len(ls)-1)*15-4,ww,len(ls)*15+4,3,fill=1,stroke=0)
  c.setFillColor(HexColor('#334155'));c.setFont(REG,12)
  for j,t in enumerate(ls):c.drawCentredString(x,y-j*15,t)

def build():
 model=json.loads((HERE/'model.json').read_text());dest=HERE/'diagrams';dest.mkdir(exist_ok=True)
 repo=HERE.parents[2]
 for d in model['diagrams']:
  for s in d['sources']:assert (repo/s).is_file(),s
  (dest/(d['id']+'.svg')).write_text(svg(d));(dest/(d['id']+'.mmd')).write_text(mermaid(d))
 pdf=HERE/'Arquitetura-C4-NovaCore-Aulas-1-a-4.pdf';c=canvas.Canvas(str(pdf),pagesize=(WIDTH,HEIGHT),pageCompression=1)
 c.setTitle('NovaCore | Arquitetura C4 atual e evolução nas quatro aulas');c.setAuthor('Leandro Lopes / L3');page=1
 header(c,'Arquitetura C4 do NovaCore','Guia visual para alunos | Arquitetura implementada + evolução resumida',page)
 y=HEIGHT-165
 for title,text in [
 ('Do processo à força de trabalho','Control Tower analisa o incidente. Control Plane mede os agentes. Maestro organiza propostas de melhoria. Segundo Cérebro preserva conhecimento revisado.'),
 ('Como ler este material','C1 apresenta pessoas e sistemas. C2 mostra aplicações, adaptadores e armazenamento. C3 abre componentes internos. Implantação e fluxos são vistas complementares, não novos níveis C4.'),
 ('O que esta edição representa','Código consolidado em main no commit c5ede1a75f41af8a01cdb0e9fd16d9a7836d0f3f. A documentação descreve o LAB local existente, sem inventar infraestrutura de produção ou ações autônomas.'),
 ('Formato de uso','Cada diagrama tem uma página de leitura guiada: ordem de explicação, limites e arquivos a consultar. As mesmas relações estão disponíveis em Mermaid, SVG e no modelo JSON editável.')]:
  y=paragraph(c,title,55,y,1060,21,28,bold=True);y=paragraph(c,text,55,y,1060,17,26)
 c.showPage();page+=1
 header(c,'Legenda e índice','Um container C4 é uma aplicação ou armazenamento; não é necessariamente um container Docker.',page)
 y=HEIGHT-130
 for kind,(bg,fg) in COLORS.items():
  c.setFillColor(HexColor(bg));c.setStrokeColor(HexColor(fg));c.roundRect(45,y-23,22,22,4,fill=1,stroke=1)
  y=paragraph(c,TYPES[kind],80,y-16,1030,14,20)-4
 y=paragraph(c,'Setas indicam chamadas, dependências ou passos explicitamente rotulados. Respostas de request retornam ao chamador e não exigem uma segunda seta. Contornos tracejados delimitam o escopo interno quando aplicável.',45,y-3,1080,13,19)
 for d in model['diagrams']:
  c.setFont(REG,13);c.setFillColor(HexColor('#075985'));c.drawString(45,y,d['id'][:2]+' | '+d['level']+' | '+d['title']);c.linkRect('',d['id'],(43,y-4,1140,y+16),relative=0);y-=23
 c.showPage();page+=1
 for d in model['diagrams']:
  c.bookmarkPage(d['id']);c.addOutlineEntry(d['level']+' | '+d['title'],d['id'])
  header(c,d['title'],d['level']+' | '+d['scope'],page);draw_diagram(c,d)
  c.showPage();page+=1
  header(c,'Leitura guiada | '+d['title'],'Use depois do diagrama: explicar o porquê, não apenas os nomes das tecnologias.',page);y=HEIGHT-130
  for label,items in [('COMO EXPLICAR',d['read']),('LIMITES IMPORTANTES',d['notes'])]:
   y=paragraph(c,label,45,y,1090,16,22,bold=True)
   for j,item in enumerate(items,1):y=paragraph(c,f'{j}. {item}',45,y,1090,16,24)
  y=paragraph(c,'ONDE ENCONTRAR NO CÓDIGO',45,y,1090,16,22,bold=True)
  for s in d['sources']:
   y=paragraph(c,s,45,y,1090,13,18,color='#075985')
  c.showPage();page+=1
 header(c,'As três fronteiras que não podem se confundir','Medir, interpretar e autorizar são responsabilidades diferentes.',page);y=HEIGHT-140
 for title,text in [
 ('Código determinístico','Inventory, suppliers, production, logistics, cenário/custos, políticas, Finance, validação e Decision Engine permanecem em código. O LLM não substitui o banco, a tool ou a regra.'),
 ('Interpretação por LLM','No workflow: Supervisor, sínteses dos especialistas, Challenger e Recommendation. Na gestão: Maestro e Knowledge Compiler. Outputs têm contratos Pydantic; referências válidas não garantem verdade semântica.'),
 ('Autorização humana','Human approval do incidente é um estado terminal pendente. Revisão do conhecimento é uma operação implementada na UI/API. Aprovar uma lição não aprova compra, transferência, plano ou mudança de lifecycle.'),
 ('O que ficou fora','Sem ACT, auto-deploy, automodificação, IAM empresarial, multi-tenancy, RAG vetorial, checkpoint por nó, transactional outbox ou garantia exactly-once de chamadas externas. A2A não foi implementado; MCP é local stdio.')]:
  y=paragraph(c,title,45,y,1090,20,27,bold=True);y=paragraph(c,text,45,y,1090,16,24)
 c.showPage();page+=1
 header(c,'Referências e manutenção','Arquitetura documentada a partir do código e da configuração, não de uma stack desejada.',page);y=HEIGHT-140
 for title,url in [('Modelo C4 - contexto','https://c4model.com/diagrams/system-context'),('Modelo C4 - containers','https://c4model.com/diagrams/container'),('Modelo C4 - componentes','https://c4model.com/diagrams/component')]:
  y=paragraph(c,title+' | '+url,45,y,1090,16,24);c.linkURL(url,(45,y+12,1140,y+38),relative=0)
 y=paragraph(c,'Convenção desta entrega',45,y-20,1090,20,27,bold=True)
 y=paragraph(c,'As vistas C1-C3 usam notação C4 simplificada com tipo, responsabilidade e tecnologia em cada caixa. Mermaid flowchart é usado por compatibilidade com a renderização do GitHub. SVG e PDF preservam um layout explícito; a disposição automática do Mermaid pode variar.',45,y,1090,16,24)
 y=paragraph(c,'Fontes e reprodução',45,y-10,1090,20,27,bold=True)
 y=paragraph(c,'docs/architecture/c4/model.json é a fonte editável. build.py gera diagramas .mmd, .svg e este PDF com ReportLab, sem executar o sistema ou chamar providers. README.md reúne o catálogo, o vínculo com os arquivos reais e as instruções de atualização.',45,y,1090,16,24)
 paragraph(c,'Não foi necessário reexecutar workloads nem alterar código do produto. As limitações operacionais foram conferidas nos módulos de execução, gestão e Compose. A arquitetura é do LAB local; sua promoção a produção requer outro projeto de implantação e segurança.',45,y-10,1090,16,24)
 c.save();print(pdf);print(f'{page} páginas / {len(model["diagrams"])} diagramas')
if __name__=='__main__':build()
