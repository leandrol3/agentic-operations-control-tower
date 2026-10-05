# L3 Control Plane — apresentação

Next.js + React + TypeScript, Tailwind v4, Radix Slot/CVA (primitiva local no estilo shadcn/ui), Recharts.
Regras de negócio ficam em Python. `app/api/[...path]` é um proxy de transporte; nenhuma chave é enviada ao browser.
Os 14 painéis usam um snapshot backend. O frontend formata números, faz busca visual e representa estados.

## Executar

Na raiz, siga `docs/course/lesson-04-cockpit-runbook.md` e `./scripts/cockpit.sh up -d --build --wait`.
Para desenvolvimento da UI com API já iniciada, dentro de `web`:

```bash
npm ci
API_INTERNAL_URL=http://127.0.0.1:8000 npm run dev
```

Se o serviço cockpit Compose já ocupa 3000, pare apenas esse serviço antes de usar o servidor local:
`../scripts/cockpit.sh stop cockpit`. Node 22 recomendado. Para voltar, `../scripts/cockpit.sh up -d cockpit`.

## Verificação

```bash
npm run typecheck
npm run build
npx playwright install chromium
npm test
```

Testes usam http://127.0.0.1:3000 (override `COCKPIT_URL`). O fluxo de aprovação grava um candidato
sintético com identificação explícita de teste; não valida semanticamente conhecimento real.
Cobertura: 14 áreas, 360, recomendação, Maestro, extração/revisão, grafo, loading, erro e vazio.

Busca e navegação não calculam attainment, SLO, custo ou ação. Aprovar/rejeitar chama a API, que valida
estado, confirmação, identidade declarada e nota. Lifecycle e plano permanecem sem execução.
