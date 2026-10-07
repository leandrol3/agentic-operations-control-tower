# Branches e checkpoints

## Política

- `main`: versão consolidada, com alterações integradas por PR. Não há branch develop.
- Branches `codex/lesson-*`: estados didáticos preservados; não aplicar merges rotineiros de main nelas.
- Tags `lesson-*`: checkpoints imutáveis. Não mover nem recriar tags existentes. Uma correção futura pode receber uma nova tag com sufixo de revisão após validação.
- Trabalho novo: branch temporária `codex/<assunto>` criada da main atualizada, revisão e merge por PR.
- Remover branches temporárias somente após integração e conferência de trabalho exclusivo. Não remover branches das aulas.
- Nunca incluir credenciais ou conhecimento pessoal dos ensaios nas publicações.

## Referências conferidas em 06/10/2026

| Tag | Commit | Situação |
| --- | --- | --- |
| lesson-01-start | 5dc5fa0 | Existente; preservada, anterior à revisão guided-demo 171c324 |
| lesson-01-complete | 7bf48f6 | Existente; preservada |
| lesson-02-complete | ebf2060 | Snapshot da branch aprovada e runbook atualizado |
| lesson-03-start | ff3166d | Snapshot da etapa API/implantação, anterior ao complete |
| lesson-03-complete | a65b409 | Existente; preservada, anterior às correções documentais da branch |
| lesson-04-start | c00594e | Snapshot do Registry/MCP aprovado |
| lesson-04-complete | f8206ce | Snapshot do Control Plane antes do cockpit |
| lesson-04-cockpit | 17dcc25 | Snapshot publicado usado como base da aula final |

As novas tags registram estados já existentes, sem novo ensaio de runtime nesta organização documental. A correção posterior de localização do executável Codex está no runbook atual da main após integração do PR; a tag do cockpit permanece histórica.

## Lacuna deliberadamente não preenchida

A branch local codex/lesson-02-start aponta para 8fbc4fc, implementação OpenAI da Aula 1. Não publicar esse ponteiro como um start validado da Aula 2. Recuperar o commit correto e conferir o conteúdo antes de criar a tag correspondente.

## Limpeza

O PR C4 #4 já foi integrado. O commit local 3232e04 com modelo PostgreSQL foi reaplicado nesta branch de organização. Manter codex/architecture-c4 até este PR ser integrado, para preservar uma referência ao trabalho local. As branches locais de preparação da Aula 1 são mantidas como referências históricas nesta rodada; não precisam aparecer no GitHub.

## Antes de mudar de branch

Execute git status. Salve alterações em commit na branch de trabalho apropriada antes de git switch. Não use restauração forçada para contornar alterações pendentes. A documentação do modelo de dados já foi preservada em commit, evitando repetir o bloqueio observado durante a preparação da aula.
