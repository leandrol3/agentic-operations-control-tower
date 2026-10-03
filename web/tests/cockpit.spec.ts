import { test, expect } from "@playwright/test";

test("Visão Geral, Agent 360 e recomendação explicável", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Uma visão da sua força de trabalho." }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Abrir agente Suprimentos", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Abrir agente Suprimentos", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Suprimentos", level: 1 }),
  ).toBeVisible();
  await page
    .locator(".tabs")
    .getByRole("button", { name: "Metas", exact: true })
    .click();
  await expect(
    page.getByRole("cell", { name: "74 %", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "90 %", exact: true }),
  ).toBeVisible();
  await page
    .locator(".tabs")
    .getByRole("button", { name: "SLOs", exact: true })
    .click();
  await expect(
    page.getByRole("cell", { name: "Violação", exact: true }).first(),
  ).toBeVisible();
  await page
    .locator("nav")
    .getByRole("button", { name: "Decisões", exact: true })
    .click();
  await page.getByRole("button", { name: /Suprimentos · Intervir/ }).click();
  await expect(page.getByRole("dialog")).toContainText(
    "Recomendação não é autorização",
  );
  await expect(
    page.getByRole("button", { name: "Executar recomendação · indisponível" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Fechar recomendação" }).click();
  expect(errors).toEqual([]);
});

test("Navegação pelas 14 áreas, dimensões de projeção e estados conhecidos", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Abrir agente Suprimentos" }),
  ).toBeVisible();
  for (const title of [
    "Agentes",
    "Metas",
    "Operações",
    "Qualidade",
    "Economia & Valor",
    "Decisões",
    "Alertas 3",
    "Lifecycle",
    "Maestro IA",
    "Segundo Cérebro",
    "Learning Loop",
    "Configurações",
    "Relatórios",
  ]) {
    await page
      .locator("nav")
      .getByRole("button", { name: title, exact: true })
      .click();
    await expect(page.locator("h1")).not.toHaveText(
      "Uma visão da sua força de trabalho.",
    );
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
  }
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page
    .locator("nav")
    .getByRole("button", { name: "Visão Geral", exact: true })
    .click();
  await page.screenshot({
    path: "test-results/overview-1920.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("Maestro cita evidências e propõe staffs sem executar", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Conversar com o Maestro" }).click();
  await page
    .getByRole("button", { name: "Como posso melhorar o agente de Supply?" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Diagnóstico", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".assistant-message")).toContainText("74");
  await expect(page.locator(".assistant-message")).toContainText("90");
  await expect(page.locator(".assistant-message")).toContainText(
    "Fontes utilizadas",
  );
  await expect(
    page.getByRole("button", { name: "Executar plano · indisponível" }),
  ).toBeDisabled();
  await page.screenshot({
    path: "test-results/maestro-1440.png",
    fullPage: true,
  });
});

test("Extração, confirmação humana, persistência e grafo", async ({ page }) => {
  await page.goto("/");
  await page
    .locator("nav")
    .getByRole("button", { name: "Operações", exact: true })
    .click();
  await page
    .getByRole("button", { name: /Abrir execução/ })
    .first()
    .click();
  await page
    .getByRole("button", { name: "Extrair aprendizado", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Revisão humana do candidato" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Confirmar aprovação" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("heading", { name: "Proveniência", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("textbox", { name: "Nome do revisor" })
    .fill("Revisor de teste do LAB");
  await page
    .getByRole("textbox", { name: "Justificativa da revisão" })
    .fill(
      "Validação automatizada da interface, exclusivamente cenário sintético; não valida resultado de negócio.",
    );
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Confirmar aprovação" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Conhecimento aprovado e persistido.",
  );
  await expect(
    page.getByRole("heading", { name: "Revisão humana do candidato" }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "← Voltar ao Segundo Cérebro" })
    .click();
  await expect(
    page.getByRole("img", {
      name: "Grafo de relações entre documentos de conhecimento",
    }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/knowledge-1440.png",
    fullPage: true,
  });
});

test("Carregamento, erro recuperável e fonte vazia sem misturar fixtures", async ({
  page,
}) => {
  let release!: () => void;
  const gate = new Promise<void>((r) => (release = r));
  await page.route("**/api/cockpit/overview?source=didactic", async (route) => {
    await gate;
    await route.fulfill({
      status: 503,
      json: { detail: "API temporariamente indisponível." },
    });
  });
  await page.goto("/");
  await expect(page.getByText("Carregando a força de trabalho…")).toBeVisible();
  release();
  await expect(
    page
      .getByRole("alert")
      .filter({ hasText: "Não foi possível carregar o cockpit" }),
  ).toContainText("Não foi possível carregar o cockpit");
  await page.unroute("**/api/cockpit/overview?source=didactic");
  await page.getByRole("button", { name: "Tentar novamente" }).click();
  await expect(
    page.getByRole("button", { name: "Abrir agente Suprimentos" }),
  ).toBeVisible();
  await page.route("**/api/cockpit/overview?source=durable", async (route) => {
    const r = await route.fetch();
    const data = await r.json();
    data.operations = [];
    data.knowledge = {
      items: [],
      counts: { approved: 0, pending_review: 0, superseded: 0 },
      types: {},
      links: [],
    };
    await route.fulfill({ json: data });
  });
  await page.getByLabel("Fonte de dados").selectOption("durable");
  await page
    .locator("nav")
    .getByRole("button", { name: "Operações", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Nenhuma execução persistida" }),
  ).toBeVisible();
  await expect(page.getByText("DIDÁTICO · DADOS SINTÉTICOS")).toHaveCount(0);
  await page
    .locator("nav")
    .getByRole("button", { name: "Segundo Cérebro", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Ainda não há conhecimento nesta fonte",
    }),
  ).toBeVisible();
});
