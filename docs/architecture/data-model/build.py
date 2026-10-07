"""Renderiza o guia Markdown e o ER sem conectar ao banco."""
from pathlib import Path
from html import escape
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderSVG
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
OUT=ROOT/'output/pdf/Modelo-de-Dados-PostgreSQL-NovaCore.pdf'
NAVY=colors.HexColor('#173650'); TEAL=colors.HexColor('#107c83')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyPT',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=7,textColor=NAVY))
styles.add(ParagraphStyle(name='CellPT',fontName='Helvetica',fontSize=8,leading=11,textColor=NAVY))
styles.add(ParagraphStyle(name='CodePT',fontName='Courier',fontSize=7,leading=10,backColor=colors.HexColor('#f1f5f9'),borderPadding=8,spaceAfter=10))
for name in ['Heading1','Heading2','Heading3']:
 styles[name].textColor=NAVY
 styles[name].spaceAfter=12

def diagram():
 d=Drawing(720,390)
 def box(x,y,w,title,fields):
  h=45+len(fields)*22
  d.add(Rect(x,y,w,h,fillColor=colors.HexColor('#f1f7fa'),strokeColor=TEAL,rx=7,ry=7))
  d.add(String(x+14,y+h-26,title,fontName='Helvetica-Bold',fontSize=14,fillColor=NAVY))
  for i,t in enumerate(fields):d.add(String(x+14,y+h-52-i*22,t,fontName='Helvetica',fontSize=11,fillColor=NAVY))
 box(15,85,300,'ct_executions',['PK execution_id : uuid','UK idempotency_key : text','document : jsonb','envelope : jsonb','options : jsonb','attempts : integer = 0','event_sequence : integer = 0','created_at : timestamptz = now()'])
 box(420,228,285,'ct_events',['PK, FK execution_id : uuid','PK sequence : integer','document : jsonb'])
 box(420,62,285,'ct_execution_context',['PK, FK execution_id : uuid','document : jsonb'])
 for y,label in [(270,'1 para 0..N'),(105,'1 para 0..1')]:
  d.add(Line(315,y,420,y,strokeColor=TEAL,strokeWidth=2));d.add(String(327,y+12,label,fontName='Helvetica-Bold',fontSize=10,fillColor=NAVY))
 d.add(String(15,25,'PK: chave primária | FK: chave estrangeira | UK: chave única',fontSize=10,fillColor=NAVY))
 return d

def footer(c,doc):
 c.setStrokeColor(TEAL);c.line(40,38,555,38);c.setFont('Helvetica',8);c.setFillColor(NAVY)
 c.drawString(40,25,'NovaCore LAB | Modelo PostgreSQL | Código + metadados locais | 05/10/2026')
 c.drawRightString(555,25,str(doc.page))

def build():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 draw=diagram();renderSVG.drawToFile(draw,str(BASE/'model.svg'))
 story=[];lines=(BASE/'README.md').read_text().splitlines();i=0
 while i<len(lines):
  line=lines[i];i+=1
  if not line:continue
  if line.startswith('```'):
   code=[]
   while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
   i+=1
   for chunk in '\n'.join(code).split('\n\n'): story.append(Preformatted(chunk,styles['CodePT'],maxLineLength=100))
   continue
  if line.startswith('|'):
   rows=[line]
   while i<len(lines) and lines[i].startswith('|'):rows.append(lines[i]);i+=1
   rows=[r for r in rows if not re.match(r'^\|[\s:|\-]+$',r)]
   data=[[Paragraph(escape(cell.strip()),styles['CellPT']) for cell in r.strip('|').split('|')] for r in rows]
   n=len(data[0]);widths={3:[145,180,190],2:[185,330]}.get(n)
   t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
   t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dceef0')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#cedde4'))]))
   story.extend([KeepTogether([t]),Spacer(1,12)]);continue
  if line.startswith('!['):draw.scale(.71,.71);draw.width=511.2;draw.height=276.9;story.append(draw);continue
  if line.startswith('# '):story.append(Paragraph(escape(line[2:]),styles['Title']));story.append(Spacer(1,16));continue
  if line.startswith('## '):
   if line.startswith(('## 2.', '## 3.', '## 5.', '## 6.', '## 9.')):story.append(PageBreak())
   story.append(Paragraph(escape(line[3:]),styles['Heading1']));continue
  if line.startswith('### '):story.append(Paragraph(escape(line[4:]),styles['Heading2']));continue
  story.append(Paragraph(escape(line),styles['BodyPT']))
 grouped=[]; j=0
 while j<len(story):
  item=story[j]
  if isinstance(item,Paragraph) and item.style.name in ('Heading1','Heading2'):
   end=j+1
   if end<len(story) and isinstance(story[end],Paragraph) and story[end].getPlainText().startswith('Localização:'): end+=1
   if end<len(story) and isinstance(story[end],KeepTogether):
    grouped.append(KeepTogether(story[j:end]+story[end]._content));j=end+1;continue
  grouped.append(item);j+=1
 story=grouped
 doc=SimpleDocTemplate(str(OUT),pagesize=(595,842),rightMargin=40,leftMargin=40,topMargin=36,bottomMargin=52,title='Modelo de Dados PostgreSQL - NovaCore',author='NovaCore LAB')
 doc.build(story,onFirstPage=footer,onLaterPages=footer)
 print(OUT)
if __name__=='__main__':build()
