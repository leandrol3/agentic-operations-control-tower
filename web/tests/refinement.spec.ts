import { test, expect } from "@playwright/test";
const nav = async (page: import("@playwright/test").Page, name: string) =>
  page.locator("nav").getByRole("button", { name, exact: true }).click();
test("Identidade oficial, exposição honesta, lifecycle e maturidade", async ({
  page,
}) => {
  await page.goto("/");
  const logo = page.getByAltText("Logo oficial L3");
  await expect(logo).toBeVisible();
  expect(await logo.evaluate((e: HTMLImageElement) => e.naturalWidth)).toBe(
    285,
  );
  expect(
    await page
      .locator(".sidebar")
      .evaluate((e) => getComputedStyle(e).backgroundColor),
  ).toBe("rgb(6, 36, 74)");
  await expect(
    page.getByRole("heading", { name: "Performance da workforce" }),
  ).toBeVisible();
  await expect(page.locator(".value-strip")).toContainText("140.000");
  await expect(page.locator(".value-strip")).toContainText("Não validado");
  await expect(page.locator(".value-strip")).toContainText(
    "não é economia realizada",
  );
  await nav(page, "Lifecycle");
  await expect(
    page.getByRole("img", { name: /Máquina de estados/ }),
  ).toBeVisible();
  await expect(page.locator('[data-state="active"]')).toHaveAttribute(
    "data-current",
    "true",
  );
  await expect(page.locator("[data-transition]")).toHaveCount(11);
  await expect(
    page.getByRole("heading", {
      name: "Transição recomendada · não executada",
    }),
  ).toBeVisible();
  await expect(page.locator(".content")).toContainText(
    "Aprovação humana: obrigatória",
  );
  await nav(page, "Economia & Valor");
  await expect(page.locator(".value-exposure").first()).toContainText(
    "140.000",
  );
  await expect(page.locator(".value-exposure").first()).toContainText("20.000");
  await nav(page, "Learning Loop");
  await expect(
    page.getByRole("heading", { name: "Maturidade da empresa agêntica" }),
  ).toBeVisible();
  await expect(page.locator(".lab-position")).toContainText(
    "ENTRE NÍVEIS 3 E 4",
  );
  await expect(page.getByText("O arco da disciplina")).toHaveCount(0);
});
test("CTA não chama provider; histórico compartilhado e contexto de execução", async ({
  page,
}) => {
  let calls = 0;
  page.on("request", (r) => {
    if (r.url().endsWith("/maestro/chat")) calls++;
  });
  await page.goto("/");
  await page.getByRole("button", { name: /1 agente requer atenção/ }).click();
  const drawer = page.locator(".maestro-drawer");
  await expect(drawer).toContainText("Agente: Suprimentos");
  expect(calls).toBe(0);
  await drawer.getByRole("button", { name: "Enviar ↗" }).click();
  await expect(drawer.locator(".assistant-message")).toHaveCount(1);
  await drawer
    .getByRole("textbox", { name: "Pergunta ao Maestro" })
    .fill("Qual evidência sustenta essa proposta?");
  await drawer.getByRole("button", { name: "Enviar ↗" }).click();
  await expect(drawer.locator(".assistant-message")).toHaveCount(2);
  await drawer.getByRole("button", { name: "Fechar Maestro" }).click();
  await nav(page, "Maestro IA");
  await expect(page.locator(".assistant-message")).toHaveCount(2);
  await nav(page, "Operações");
  await page.locator('.content tbody tr[role="button"]').first().click();
  await page
    .locator("header")
    .getByRole("button", { name: "Perguntar ao Maestro", exact: true })
    .click();
  await expect(drawer.locator(".context-chips")).toContainText("Execução:");
  await expect(drawer.locator(".context-notice").last()).toContainText(
    "Contexto alterado para Execução INCIDENT-001",
  );
  await expect(drawer.locator(".assistant-message")).toHaveCount(2);
  await drawer
    .getByRole("textbox", { name: "Pergunta ao Maestro" })
    .fill("Explique esta execução e seus limites.");
  await drawer.getByRole("button", { name: "Enviar ↗" }).click();
  await expect(drawer.locator(".assistant-message")).toHaveCount(3);
});
test("Agent 360, recomendação e conhecimento abrem contexto estruturado", async ({
  page,
}) => {
  const contexts: Record<string, string>[] = [];
  page.on("request", (r) => {
    if (r.url().endsWith("/maestro/chat"))
      contexts.push(r.postDataJSON().context);
  });
  await page.goto("/");
  await page
    .getByRole("button", { name: "Abrir agente Suprimentos", exact: true })
    .click();
  await page
    .locator("header")
    .getByRole("button", { name: "Perguntar ao Maestro", exact: true })
    .click();
  await page
    .locator(".maestro-drawer")
    .getByRole("button", { name: "Quem precisa de atenção?" })
    .click();
  await expect(page.locator(".assistant-message")).toHaveCount(1);
  expect(contexts[0].context_type).toBe("agent");
  await page.getByRole("button", { name: "Fechar Maestro" }).click();
  await nav(page, "Decisões");
  await page.getByRole("button", { name: /Suprimentos · Intervir/ }).click();
  await page
    .getByRole("button", {
      name: "Perguntar ao Maestro sobre esta recomendação",
    })
    .click();
  await page
    .locator(".maestro-drawer")
    .getByRole("button", { name: "Quem precisa de atenção?" })
    .click();
  await expect(page.locator(".assistant-message")).toHaveCount(2);
  expect(contexts[1].context_type).toBe("recommendation");
  expect(contexts[1].recommendation_id).toBeTruthy();
  await page.getByRole("button", { name: "Fechar Maestro" }).click();
  await nav(page, "Segundo Cérebro");
  await page.locator(".knowledge-row").first().click();
  await page
    .locator("header")
    .getByRole("button", { name: "Perguntar ao Maestro", exact: true })
    .click();
  await page
    .locator(".maestro-drawer")
    .getByRole("button", { name: "O que aprendemos hoje?" })
    .click();
  await expect(page.locator(".assistant-message")).toHaveCount(3);
  expect(contexts[2].context_type).toBe("knowledge");
  expect(contexts[2].knowledge_id).toBeTruthy();
});
test("Falha explícita preserva conversa e permite retry manual", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: /1 agente requer atenção/ }).click();
  await page.getByRole("button", { name: "Enviar ↗" }).click();
  await expect(page.locator(".assistant-message")).toHaveCount(1);
  await page.route("**/api/maestro/chat", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        detail: "Maestro indisponível: provider LLM não configurado.",
      }),
    }),
  );
  await page
    .getByRole("textbox", { name: "Pergunta ao Maestro" })
    .fill("Continue a análise anterior.");
  await page.getByRole("button", { name: "Enviar ↗" }).click();
  await expect(page.locator(".chat-error[role=alert]")).toContainText(
    "Os dados do Control Plane continuam disponíveis",
  );
  await expect(page.locator(".assistant-message")).toHaveCount(1);
  await page.unroute("**/api/maestro/chat");
  await page.getByRole("button", { name: "Tentar análise novamente" }).click();
  await expect(page.locator(".assistant-message")).toHaveCount(2);
  await expect(page.locator(".user-message")).toHaveCount(2);
});
