// Local visual evidence. Use only an isolated mock fixture profile: creates proposed plans, no approvals.
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { mkdir } from "node:fs/promises";
const require = createRequire(new URL("../web/package.json", import.meta.url));
const { chromium } = require("@playwright/test");
const output = fileURLToPath(
  new URL(
    "../docs/course/lesson-04/cockpit-refinement-captures/",
    import.meta.url,
  ),
);
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const url = process.env.COCKPIT_URL || "http://localhost:3000";
const mode = await (
  await page.request.get(url + "/api/cockpit/overview")
).json();
if (mode.runtime_mode !== "mock") {
  await browser.close();
  throw new Error(
    "Capturas automatizadas exigem mock explícito e dados isolados.",
  );
}
const nav = async (name) => {
  await page.locator("nav").getByRole("button", { name, exact: true }).click();
};
const capture = async (name) => {
  await page.screenshot({
    path: output + name + ".png",
    fullPage: name === "lifecycle",
  });
};
try {
  await page.goto(url);
  await page.getByRole("button", { name: /1 agente requer atenção/ }).waitFor();
  await capture("overview-1440");
  await page.setViewportSize({ width: 1920, height: 1080 });
  await capture("overview-1920");
  await page.setViewportSize({ width: 1440, height: 900 });
  await page
    .getByRole("button", { name: "Abrir agente Suprimentos", exact: true })
    .click();
  await capture("agent-360");
  await nav("Lifecycle");
  await capture("lifecycle");
  await nav("Economia & Valor");
  await capture("economia-valor");
  await nav("Segundo Cérebro");
  await capture("segundo-cerebro");
  await nav("Learning Loop");
  await page
    .getByRole("heading", { name: "Maturidade da empresa agêntica" })
    .scrollIntoViewIfNeeded();
  await capture("learning-loop-maturity");
  await nav("Maestro IA");
  for (const [i, q] of [
    "Como posso melhorar o agente de Supply?",
    "Qual evidência ainda falta validar?",
    "O que aprendemos hoje?",
  ].entries()) {
    await page.getByRole("textbox", { name: "Pergunta ao Maestro" }).fill(q);
    await page.getByRole("button", { name: "Enviar ↗" }).click();
    await page.locator(".assistant-message").nth(i).waitFor();
  }
  await page.locator(".conversation-history").evaluate((e) => {
    e.scrollTop = 0;
  });
  await capture("maestro-conversa");
  await nav("Operações");
  await page.locator('.content tbody tr[role="button"]').first().click();
  await page
    .locator("header")
    .getByRole("button", { name: "Perguntar ao Maestro", exact: true })
    .click();
  await page.locator(".maestro-drawer").waitFor();
  await page.locator(".context-notice").last().waitFor();
  await page.locator(".conversation-history").evaluate((e) => {
    e.scrollTop = e.scrollHeight;
  });
  await capture("maestro-execucao");
  if (errors.length) throw new Error(errors.join("\n"));
  console.log("9 capturas; 3 turnos na mesma sessão; nenhum erro de página.");
} finally {
  await browser.close();
}
