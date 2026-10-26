import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

declare global {
  interface Window {
    copiedIntegrationText: string;
  }
}

test("Tecnologia cria, copia, rotaciona e revoga token de leitura", async ({
  page,
}, testInfo) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async (value: string) => {
          Object.assign(window, { copiedIntegrationText: value });
        },
      },
    });
  });
  await page.goto("/login");
  await page.getByLabel("E-mail", { exact: true }).fill("test@example.invalid");
  await page.getByLabel("Senha", { exact: true }).fill("Somente-teste-2026");
  await page.getByRole("button", { name: "Acessar plataforma" }).click();
  await expect(page).toHaveURL(/dashboard/);
  await page.goto("/tecnologia/conexao");
  const name = `Agenda E2E ${testInfo.project.name} ${Date.now()}`;
  await page
    .getByRole("button", {
      name: "Copiar endpoint — Resumos de ações",
      exact: true,
    })
    .click();
  expect(
    await page.evaluate(
      () =>
        (window as Window & { copiedIntegrationText: string })
          .copiedIntegrationText,
    ),
  ).toBe("http://localhost:3100/api/integracoes/v1/acoes/resumos");
  await page
    .getByRole("button", {
      name: "Copiar cURL — Resumos de ações",
      exact: true,
    })
    .click();
  expect(
    await page.evaluate(
      () =>
        (window as Window & { copiedIntegrationText: string })
          .copiedIntegrationText,
    ),
  ).toContain("Authorization: Bearer <TOKEN_DA_AGENDA>");
  await page.getByRole("button", { name: "Criar token", exact: true }).click();
  let dialog = page.getByRole("dialog");
  await dialog.getByLabel("Nome do token", { exact: false }).fill(name);
  await dialog.getByRole("combobox", { name: "Validade do token" }).click();
  await page
    .getByRole("option", { name: "Nunca expirar", exact: true })
    .click();
  await dialog
    .getByLabel("Confirme sua senha institucional", { exact: false })
    .fill("Somente-teste-2026");
  await dialog
    .getByRole("button", { name: "Gerar token", exact: true })
    .click();
  dialog = page.getByRole("dialog");
  const raw = await dialog
    .getByLabel("Token de integração", { exact: true })
    .inputValue();
  expect(raw).toMatch(/^acm_/);
  await expect(dialog.getByText(/Validade: Nunca expira/)).toBeVisible();
  await dialog
    .getByRole("button", { name: "Copiar token", exact: true })
    .click();
  expect(
    await page.evaluate(
      () =>
        (window as Window & { copiedIntegrationText: string })
          .copiedIntegrationText,
    ),
  ).toBe(raw);
  await dialog
    .getByRole("button", { name: "Copiar cURL com token", exact: true })
    .click();
  const command = await page.evaluate(
    () =>
      (window as Window & { copiedIntegrationText: string })
        .copiedIntegrationText,
  );
  expect(command).toContain(
    "http://localhost:3100/api/integracoes/v1/acoes/resumos",
  );
  expect(command).toContain(`Authorization: Bearer ${raw}`);
  expect(
    await page.evaluate(() => JSON.stringify([localStorage, sessionStorage])),
  ).not.toContain(raw);
  expect((await page.request.get("/api/integracoes/v1/health")).status()).toBe(
    401,
  );
  expect(
    (
      await page.request.get("/api/integracoes/v1/health", {
        headers: { Authorization: `Bearer ${raw}` },
      })
    ).status(),
  ).toBe(200);
  const result = await page.request.get("/api/integracoes/v1/acoes/resumos", {
    headers: { Authorization: `Bearer ${raw}` },
  });
  expect(result.status()).toBe(200);
  expect(await result.json()).toHaveProperty("exportacao_id");
  await dialog
    .getByRole("button", { name: "Concluir e ocultar token", exact: true })
    .click();
  await page.reload();
  await expect(
    page.getByLabel("Token de integração", { exact: true }),
  ).toHaveCount(0);
  const listing = await page.request.get("/api/backend/tecnologia/tokens");
  expect(await listing.text()).not.toContain(raw);
  expect(
    (await listing.json()).find((row: { nome: string }) => row.nome === name)
      .expira_em,
  ).toBeNull();
  await page
    .getByRole("button", { name: `Rotacionar token ${name}`, exact: true })
    .click();
  dialog = page.getByRole("dialog");
  await expect(
    dialog.getByRole("combobox", { name: "Validade do token" }),
  ).toHaveText("Nunca expirar");
  await dialog
    .getByLabel("Confirme sua senha institucional", { exact: false })
    .fill("Somente-teste-2026");
  await dialog
    .getByRole("button", { name: "Gerar token", exact: true })
    .click();
  const replacement = await page
    .getByRole("dialog")
    .getByLabel("Token de integração", { exact: true })
    .inputValue();
  expect(replacement).not.toBe(raw);
  expect(
    (
      await page.request.get("/api/integracoes/v1/health", {
        headers: { Authorization: `Bearer ${raw}` },
      })
    ).status(),
  ).toBe(401);
  await page
    .getByRole("button", { name: "Concluir e ocultar token", exact: true })
    .click();
  await page
    .getByRole("button", { name: `Revogar token ${name}`, exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByLabel("Confirme sua senha institucional", { exact: false })
    .fill("Somente-teste-2026");
  await page
    .getByRole("button", { name: "Confirmar revogação", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  expect(
    (
      await page.request.get("/api/integracoes/v1/health", {
        headers: { Authorization: `Bearer ${replacement}` },
      })
    ).status(),
  ).toBe(401);
  const accessibility = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await page.screenshot({
    path: `artifacts/integrations-${testInfo.project.name}.png`,
    fullPage: true,
  });
});
