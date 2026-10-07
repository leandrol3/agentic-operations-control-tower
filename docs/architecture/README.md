# Arquitetura do projeto

## Arquitetura atual — até a Aula 4

[**C4: contexto, containers, componentes, implantação e fluxos**](c4/README.md)

O material inclui PDF, 11 diagramas em SVG/Mermaid e modelo editável, com leitura guiada para alunos e evolução resumida das quatro aulas. As relações foram conferidas no código e nas configurações do LAB.

## Modelo de dados

[PostgreSQL: diagrama ER, colunas, contratos JSONB e consultas para aula](data-model/README.md).

- [Diagrama editável Mermaid](data-model/model.mmd) e [SVG](data-model/model.svg).
- [DDL existente](data-model/schema.sql) e [contratos JSON Schema](data-model/contracts.schema.json).
- [Consultas de demonstração somente leitura](data-model/demo-readonly.sql).
- [PDF do modelo de dados](../../output/pdf/Modelo-de-Dados-PostgreSQL-NovaCore.pdf).

Para regenerar o PDF e o SVG a partir deste guia, na raiz do repositório:

```bash
uv run --with 'reportlab>=4,<5' python docs/architecture/data-model/build.py
```

O Markdown é a fonte do texto; o renderer contém o layout físico do ER. Se mudar o esquema, atualize também o Mermaid, o DDL e os contratos exportados. O renderer não consulta nem modifica o banco.

## Histórico didático

- [Arquitetura da Aula 1](lesson-01-architecture.md)
- [Grafo da Aula 1](lesson-01-graph.mmd)

As vistas atuais descrevem a implementação existente; o histórico preserva o recorte da primeira aula.
