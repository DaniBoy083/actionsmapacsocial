import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { institutionalFixture } from "./action-fixtures";

test("cadastrar profissional, atribuir local, registrar campos clínicos, consultar versão e revogar", async ({
  page,
}, info) => {
  await page.goto("/login");
  await page
    .getByLabel("E-mail", { exact: true })
    .fill("admin@example.invalid");
  await page.getByLabel("Senha", { exact: true }).fill("Somente-teste-2026");
  await page.getByRole("button", { name: "Acessar plataforma" }).click();
  await expect(page).toHaveURL(/dashboard/);
  await page.goto("/profissionais");
  const name = `Profissional sintético ${info.project.name} ${Date.now()}`;
  await page
    .getByRole("button", { name: "Cadastrar profissional", exact: true })
    .click();
  let dialog = page.getByRole("dialog");
  await dialog.getByLabel("Nome do profissional", { exact: false }).fill(name);
  await dialog.getByLabel("Categoria profissional").click();
  await page
    .getByRole("option", { name: "Oftalmologista", exact: true })
    .click();
  await dialog
    .getByLabel("Número do registro", { exact: false })
    .fill(`000${Date.now()}`);
  await dialog.getByLabel("UF do registro", { exact: false }).click();
  await page.getByRole("option", { name: "PB", exact: true }).click();
  await dialog.getByLabel("Conferência da habilitação registrada").check();
  await dialog
    .getByLabel("Referência da conferência de habilitação", { exact: false })
    .fill("Conferência sintética de teste");
  await dialog.getByLabel("Registro de campos clínicos autorizado").check();
  await dialog
    .getByLabel("Referência da autorização clínica", { exact: false })
    .fill("Autorização sintética de teste");
  await dialog
    .getByLabel("Vincular este profissional à minha identidade institucional")
    .check();
  let accessibility = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await dialog
    .getByRole("button", { name: "Salvar profissional", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await page.getByLabel("Buscar profissional por nome").fill(name);
  await expect(page.getByRole("row").filter({ hasText: name })).toBeVisible();
  const session = await (await page.request.get("/api/backend/auth/me")).json();
  const headers = {
    Origin: new URL(page.url()).origin,
    "X-CSRF-Token": session.csrf_token,
  };
  const actionResponse = await page.request.post("/api/backend/acoes", {
    headers,
    data: {
      nome: `Ação de campos clínicos ${name}`,
      locais: [
        { municipio_ibge: "2507507", nome_local: "Local sintético A" },
        { municipio_ibge: "2504009", nome_local: "Local sintético B" },
      ],
      institucional: {
        ...institutionalFixture,
        instrumento: {
          tipo: "EMENDA",
          nome: "Instrumento sintético clínico",
          numero: "0008",
        },
      },
    },
  });
  expect(actionResponse.status()).toBe(201);
  const action = await actionResponse.json();
  const personName = "Pessoa sintética do formulário clínico";
  expect(
    (
      await page.request.post(`/api/backend/acoes/${action.id}/beneficiarios`, {
        headers,
        data: { nome: personName, local_indice: 0 },
      })
    ).status(),
  ).toBe(201);
  await page.goto(`/acoes/${action.id}`);
  await page
    .getByRole("button", { name: "Atribuir profissional", exact: true })
    .click();
  dialog = page.getByRole("dialog");
  await dialog.getByLabel("Buscar profissional para atribuir").fill(name);
  await dialog.getByLabel("Profissional da equipe", { exact: false }).click();
  await page.getByRole("option").filter({ hasText: name }).click();
  await dialog.getByLabel("Todos os locais da ação").uncheck();
  await dialog
    .getByLabel("Local 1: Local sintético A", { exact: true })
    .check();
  await dialog
    .getByRole("button", { name: "Salvar atribuição", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await page
    .getByRole("button", {
      name: `Designar atendimento de ${personName}`,
      exact: true,
    })
    .click();
  dialog = page.getByRole("dialog");
  await dialog.getByLabel("Profissional responsável pelo atendimento").click();
  await page.getByRole("option").filter({ hasText: name }).click();
  await dialog
    .getByRole("button", { name: "Salvar designação", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  const clinicalButton = page.getByRole("button", {
    name: `Campos clínicos de ${personName}`,
    exact: true,
  });
  await expect(clinicalButton).toBeVisible();
  await clinicalButton.click();
  dialog = page.getByRole("dialog");
  await expect(
    dialog.getByText("Instrumento sintético clínico", { exact: true }),
  ).toBeVisible();
  await dialog.getByLabel("Glicose", { exact: true }).fill("medida sintética");
  await dialog
    .getByLabel("Pressão", { exact: true })
    .fill("registro sintético");
  await dialog
    .getByLabel("Tipo de sangue", { exact: true })
    .fill("valor sintético");
  await dialog.getByLabel("Esférico OD", { exact: true }).fill("-1,25");
  await dialog.getByLabel("Cilíndrico OD", { exact: true }).fill("-0,50");
  await dialog.getByLabel("Eixo OD", { exact: true }).fill("teste");
  await dialog
    .getByLabel("DP OD", { exact: true })
    .fill("transcrição sintética");
  await dialog.getByLabel("Esférico OE", { exact: true }).fill("-0,75");
  await dialog
    .getByLabel("Adição", { exact: true })
    .fill("valor informado sintético");
  await dialog
    .getByLabel("Lentes", { exact: true })
    .fill("LENTE_SINTETICA_ORIGINAL");
  await dialog
    .getByRole("button", { name: "Salvar campos clínicos", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await clinicalButton.click();
  await expect(dialog.getByLabel("Lentes", { exact: true })).toHaveValue(
    "LENTE_SINTETICA_ORIGINAL",
  );
  await expect(dialog.getByLabel("Cilíndrico OE", { exact: true })).toHaveValue(
    "",
  );
  await dialog
    .getByLabel("Esférico OD", { exact: true })
    .scrollIntoViewIfNeeded();
  await page.screenshot({
    path: `artifacts/clinical-fields-${info.project.name}.png`,
    fullPage: true,
  });
  accessibility = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await dialog
    .getByLabel("Lentes", { exact: true })
    .fill("LENTE_SINTETICA_REVISADA");
  await dialog
    .getByRole("button", { name: "Salvar campos clínicos", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await clinicalButton.click();
  await dialog.getByLabel("Número da versão para consulta").fill("1");
  await dialog
    .getByRole("button", { name: "Consultar versão", exact: true })
    .click();
  await expect(dialog.getByLabel("Lentes", { exact: true })).toHaveValue(
    "LENTE_SINTETICA_ORIGINAL",
  );
  await expect(
    dialog.getByRole("button", { name: "Salvar campos clínicos", exact: true }),
  ).toHaveCount(0);
  await dialog
    .getByRole("button", { name: "Fechar campos clínicos", exact: true })
    .click();
  const people = await (
    await page.request.get(`/api/backend/acoes/${action.id}/beneficiarios`)
  ).json();
  expect(people.total).toBe(1);
  const general = await page.request.get(
    `/api/backend/acoes/${action.id}/beneficiarios/${people.items[0].id}`,
  );
  expect(await general.text()).not.toContain("LENTE_SINTETICA");
  await page
    .getByRole("button", {
      name: `Histórico da atribuição de ${name}`,
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("dialog").getByText(/Local sintético A/),
  ).toBeVisible();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Fechar histórico" })
    .click();
  await page.goto("/profissionais");
  await page.getByLabel("Buscar profissional por nome").fill(name);
  await page
    .getByRole("button", { name: `Editar profissional ${name}`, exact: true })
    .click();
  dialog = page.getByRole("dialog");
  await dialog.getByLabel("Cadastro ativo", { exact: true }).uncheck();
  await dialog
    .getByLabel("Vincular este profissional à minha identidade institucional")
    .uncheck();
  await dialog
    .getByRole("button", { name: "Salvar profissional", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await page.goto(`/acoes/${action.id}`);
  await expect(clinicalButton).toHaveCount(0);
  await expect(
    page
      .getByRole("row")
      .filter({ hasText: name })
      .getByText("Revogada", { exact: true }),
  ).toBeVisible();
  expect(
    (
      await page.request.get(
        `/api/backend/acoes/${action.id}/beneficiarios/${people.items[0].id}/clinica`,
      )
    ).status(),
  ).toBe(403);
});
