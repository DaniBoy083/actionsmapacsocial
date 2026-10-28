import { test, expect, type Page, type BrowserContext } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

let cookies: Awaited<ReturnType<BrowserContext["cookies"]>> | undefined;
async function login(page: Page) {
  if (cookies) {
    await page.context().addCookies(cookies);
    await page.goto("/dashboard");
    return;
  }
  await page.goto("/login");
  await page.getByLabel("E-mail", { exact: true }).fill("test@example.invalid");
  await page.getByLabel("Senha", { exact: true }).fill("Somente-teste-2026");
  await page.getByRole("button", { name: "Acessar plataforma" }).click();
  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByRole("heading", { name: /Olá/ })).toBeVisible();
  cookies = await page.context().cookies();
}

test("cadastro completo, correção, ficha privada e segunda via imprimível", async ({
  page,
}, info) => {
  await login(page);
  const id = await page.evaluate(async () => {
    const session = await (await fetch("/api/backend/auth/me")).json();
    const response = await fetch("/api/backend/acoes", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": session.csrf_token,
      },
      body: JSON.stringify({
        nome: "Ação para segunda via sintética",
        locais: [{ municipio_ibge: "2508901" }],
      }),
    });
    return (await response.json()).id;
  });
  await page.goto(`/acoes/${id}`);
  await page
    .getByRole("button", { name: "Registrar beneficiário", exact: true })
    .click();
  let dialog = page.getByRole("dialog");
  await dialog
    .getByLabel("Nome", { exact: false })
    .fill("Pessoa da ficha sintética");
  await dialog.getByLabel("CPF", { exact: true }).fill("52998224725");
  await dialog.getByLabel("Telefone", { exact: true }).fill("83999990000");
  await dialog
    .getByLabel("Data de nascimento", { exact: true })
    .fill("2000-01-02");
  await dialog.getByLabel("Data da ficha", { exact: true }).fill("2026-09-17");
  await dialog
    .getByLabel("Responsável indicado na ficha", { exact: true })
    .fill("Responsável sintético");
  await dialog
    .getByLabel("Observações gerais (sem dados oculares)", { exact: true })
    .fill("Cadastro sintético.");
  await dialog
    .getByRole("combobox", { name: "Município indicado na ficha", exact: true })
    .click();
  await page.getByRole("option", { name: "Mamanguape", exact: true }).click();
  await expect(page.getByRole("listbox")).toHaveCount(0);
  await dialog
    .getByRole("combobox", { name: "Declaração de recebimento no documento" })
    .click();
  await page
    .getByRole("option", { name: "Recebimento confirmado", exact: true })
    .click();
  await expect(page.getByRole("listbox")).toHaveCount(0);
  await dialog
    .getByRole("button", { name: "Salvar beneficiário", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await page
    .getByRole("button", {
      name: "Ver ficha de Pessoa da ficha sintética",
      exact: true,
    })
    .click();
  dialog = page.getByRole("dialog");
  await expect(
    dialog.getByText("529.982.247-25", { exact: true }),
  ).toBeVisible();
  await expect(dialog.getByText("02/01/2000", { exact: true })).toBeVisible();
  await expect(
    dialog.getByText("Responsável sintético", { exact: true }),
  ).toBeVisible();
  await dialog.getByRole("button", { name: "Fechar", exact: true }).click();
  await page
    .getByRole("button", {
      name: "Editar cadastro de Pessoa da ficha sintética",
      exact: true,
    })
    .click();
  dialog = page.getByRole("dialog");
  await expect(dialog.getByLabel("CPF", { exact: true })).toHaveValue(
    "52998224725",
  );
  await dialog.getByLabel("Telefone", { exact: true }).fill("12345678");
  await dialog
    .getByRole("button", { name: "Salvar beneficiário", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await page
    .getByRole("button", {
      name: "Emitir segunda via de Pessoa da ficha sintética",
      exact: true,
    })
    .click();
  const sheet = page.locator("[data-beneficiary-print]");
  await expect(
    sheet.getByRole("heading", {
      name: "Segunda via da ficha de cadastro",
      exact: true,
    }),
  ).toBeVisible();
  await expect(sheet.getByText("12345678", { exact: true })).toBeVisible();
  await expect(sheet).not.toContainText("Esférico");
  await expect(sheet).not.toContainText("Cilíndrico");
  await expect(sheet).toContainText(
    "Assinatura do beneficiário ou responsável nesta via",
  );
  await page.evaluate(async () => {
    await Promise.all(
      document
        .getAnimations()
        .filter((a) => a.effect?.getTiming().iterations !== Infinity)
        .map((a) => a.finished.catch(() => {})),
    );
  });
  const content = page.getByRole("region", {
    name: "Conteúdo da ficha de cadastro",
    exact: true,
  });
  await content.focus();
  await expect(content).toBeFocused();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.evaluate(() => {
    window.print = () =>
      document.documentElement.setAttribute("data-print-requested", "true");
  });
  await page
    .getByRole("button", { name: "Imprimir segunda via", exact: true })
    .click();
  await expect(page.locator("html")).toHaveAttribute(
    "data-print-requested",
    "true",
  );
  await page.setViewportSize({ width: 794, height: 1123 });
  await page.emulateMedia({ media: "print" });
  await expect(sheet).toBeVisible();
  await expect(page.locator("body")).toHaveCSS(
    "background-color",
    "rgb(255, 255, 255)",
  );
  await expect(page.locator(".sidebar")).not.toBeVisible();
  await expect(
    page.getByRole("button", { name: "Imprimir segunda via", exact: true }),
  ).not.toBeVisible();
  await page.screenshot({
    path: `artifacts/beneficiary-second-copy-${info.project.name}.png`,
    fullPage: true,
  });
  await page.pdf({
    path: `artifacts/beneficiary-second-copy-${info.project.name}.pdf`,
    preferCSSPageSize: true,
    printBackground: true,
  });
});

test("mapa de ações removido da navegação, página e BFF", async ({ page }) => {
  await login(page);
  await expect(
    page.getByRole("link", { name: "Mapa de ações", exact: true }),
  ).toHaveCount(0);
  expect((await page.request.get("/api/backend/mapa-acoes")).status()).toBe(
    404,
  );
  await page.goto("/mapa-acoes");
  await expect(
    page.getByRole("heading", { name: "Página não encontrada", exact: true }),
  ).toBeVisible();
});
