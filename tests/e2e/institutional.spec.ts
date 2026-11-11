import { test, expect, type Page } from "@playwright/test";
import path from "node:path";

async function login(page: Page) {
  await page.goto("/login");
  await page
    .getByLabel("E-mail", { exact: true })
    .fill("admin@example.invalid");
  await page.getByLabel("Senha", { exact: true }).fill("Somente-teste-2026");
  await page.getByRole("button", { name: "Acessar plataforma" }).click();
  await expect(page).toHaveURL(/dashboard/);
}

for (const support of ["Total", "Parcial"]) {
  test(`metadados e duas marcas opcionais em apoio ${support}, com segunda via preservada`, async ({
    page,
  }, info) => {
    await login(page);
    await page.goto("/acoes");
    const name = `Ação sintética ${support} ${info.project.name} ${Date.now()}`;
    await page
      .getByRole("button", { name: "Cadastrar nova ação", exact: true })
      .first()
      .click();
    const form = page.getByRole("dialog");
    await form.getByLabel("Nome da ação", { exact: false }).fill(name);
    await form.getByLabel("Município do local 1").click();
    await page
      .getByRole("option", { name: "João Pessoa", exact: true })
      .click();
    await form.getByLabel("Modalidade de apoio").click();
    await page.getByRole("option", { name: support, exact: true }).click();
    await form.getByLabel("Tipo de instrumento").click();
    await page.getByRole("option", { name: "Emenda", exact: true }).click();
    await form
      .getByLabel("Nome/título da emenda ou convênio")
      .fill("Instrumento sintético de impressão");
    await form.getByLabel("Número da emenda/convênio").fill("0007/2026");
    await form
      .getByLabel("Autor da emenda (quando aplicável)")
      .fill("Autoria sintética");
    for (const brand of ["órgão governamental", "clínica parceira"]) {
      await form.getByLabel(`Nome: ${brand}`).fill(`${brand} sintético`);
      await form.getByLabel(`Uso da marca de ${brand} autorizado`).check();
      await form
        .getByLabel(`Logo de ${brand}`, { exact: true })
        .setInputFiles(path.resolve("public/logo-ac-social.png"));
      await expect(
        form.getByAltText(`Prévia da marca: ${brand} sintético`),
      ).toBeVisible();
    }
    await form
      .getByRole("button", { name: "Salvar ação", exact: true })
      .click();
    await expect(form).not.toBeVisible();
    await page.getByLabel("Buscar por nome").fill(name);
    await page
      .getByRole("link", { name: `Visualizar ${name}`, exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name, exact: true }),
    ).toBeVisible();
    await expect(page.locator(".institutional-logos img")).toHaveCount(3);
    await expect(page.getByText("0007/2026", { exact: true })).toBeVisible();
    const id = new URL(page.url()).pathname.split("/").at(-1)!;
    const session = await (
      await page.request.get("/api/backend/auth/me")
    ).json();
    const result = await page.request.post(
      `/api/backend/acoes/${id}/beneficiarios`,
      {
        headers: {
          Origin: new URL(page.url()).origin,
          "X-CSRF-Token": session.csrf_token,
        },
        data: { nome: "Pessoa de teste institucional", local_indice: 0 },
      },
    );
    expect(result.status()).toBe(201);
    await page.reload();
    await page
      .getByRole("button", {
        name: "Emitir segunda via de Pessoa de teste institucional",
      })
      .click();
    const sheet = page.getByRole("dialog");
    await expect(
      sheet.getByRole("button", { name: "Imprimir segunda via" }),
    ).toBeEnabled();
    await expect(sheet.locator(".institutional-logos img")).toHaveCount(3);
    await page.emulateMedia({ media: "print" });
    await sheet
      .locator("[data-beneficiary-print]")
      .screenshot({
        path: `artifacts/institutional-${support}-${info.project.name}.png`,
      });
    await page.emulateMedia({ media: "screen" });
    await sheet.getByRole("button", { name: "Fechar", exact: true }).click();
    await page
      .getByRole("button", { name: "Editar ação", exact: true })
      .click();
    await form
      .getByLabel("Nome/título da emenda ou convênio")
      .fill("Identificação nova");
    await form
      .getByRole("button", { name: "Remover logo de órgão governamental" })
      .click();
    await form
      .getByRole("button", { name: "Salvar ação", exact: true })
      .click();
    await expect(form).not.toBeVisible();
    await expect(
      page.getByText("Identificação nova", { exact: true }),
    ).toBeVisible();
    await page
      .getByRole("button", {
        name: "Emitir segunda via de Pessoa de teste institucional",
      })
      .click();
    await expect(
      sheet.getByText("Instrumento sintético de impressão", { exact: true }),
    ).toBeVisible();
    await expect(sheet.locator(".institutional-logos img")).toHaveCount(3);
    await sheet.getByRole("button", { name: "Fechar", exact: true }).click();
    expect(
      (
        await (
          await page.request.get(`/api/backend/acoes/${id}/beneficiarios`)
        ).json()
      ).total,
    ).toBe(1);
  });
}

test("filtros institucionais no painel e erro de período recuperável", async ({
  page,
}) => {
  await login(page);
  await page.getByText("Filtrar indicadores", { exact: true }).click();
  await page.getByLabel("Início da ação a partir de").fill("2026-11-11");
  await page
    .getByLabel("Início da ação até", { exact: true })
    .fill("2026-11-10");
  await page.getByRole("button", { name: "Aplicar filtros" }).click();
  await expect(
    page.getByRole("alert").filter({ hasText: "Confira o período informado." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Limpar filtros" }).click();
  await expect(
    page.getByRole("heading", { name: "Ações por município" }),
  ).toBeVisible();
  if (!(await page.getByLabel("Autor da emenda", { exact: true }).isVisible()))
    await page.getByText("Filtrar indicadores", { exact: true }).click();
  await page
    .getByLabel("Autor da emenda", { exact: true })
    .fill("Autoria inexistente para teste");
  await page.getByRole("button", { name: "Aplicar filtros" }).click();
  await expect(
    page.getByRole("heading", { name: "O alcance começa com uma ação" }),
  ).toBeVisible();
});
