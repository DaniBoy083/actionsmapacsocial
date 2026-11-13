import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function login(page: Page, role: string) {
  await page.goto("/acesso");
  await page
    .getByRole("button", { name: `Preencher acesso de ${role}`, exact: true })
    .click();
  await page
    .getByRole("button", { name: "Entrar na minha ação", exact: true })
    .click();
  await expect(page).toHaveURL(/\/operacao$/);
  await page
    .getByRole("link", {
      name: "Abrir DEMO — Saúde ocular em João Pessoa",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "DEMO — Saúde ocular em João Pessoa",
      exact: true,
    }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
}

for (const [role, person] of [
  ["Oftalmologista", "02"],
  ["Optometrista", "03"],
]) {
  test(`${role} acessa somente o caso designado e salva a ficha`, async ({
    page,
  }, info) => {
    await login(page, role);
    const own = `Pessoa fictícia DEMO ${person}`;
    const other = `Pessoa fictícia DEMO ${person === "02" ? "03" : "02"}`;
    await expect(
      page.getByRole("cell", { name: own, exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("cell", { name: other, exact: true }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("link", { name: /Agenda Digital|Visão geral|Conexão/ }),
    ).toHaveCount(0);
    for (const path of [
      "indicadores",
      "profissionais",
      "tecnologia/saude",
      "acoes",
    ]) {
      expect([401, 403]).toContain(
        (await page.request.get(`/api/backend/${path}`)).status(),
      );
    }
    await page
      .getByRole("button", { name: `Campos clínicos de ${own}`, exact: true })
      .click();
    const dialog = page.getByRole("dialog");
    const value = `Exemplo fictício ${info.project.name}`;
    await dialog.getByLabel("Esférico OD", { exact: true }).fill(value);
    await dialog
      .getByLabel("Tipo de sangue", { exact: true })
      .fill("Não informado");
    await dialog
      .getByRole("button", { name: "Salvar campos clínicos", exact: true })
      .click();
    await expect(dialog).not.toBeVisible();
    await page.reload();
    await page
      .getByRole("button", { name: `Campos clínicos de ${own}`, exact: true })
      .click();
    await expect(
      page.getByRole("dialog").getByLabel("Esférico OD", { exact: true }),
    ).toHaveValue(value);
    await page.screenshot({
      path: `artifacts/operational-${role}-${info.project.name}.png`,
      fullPage: true,
    });
    await page
      .getByRole("button", { name: "Fechar campos clínicos", exact: true })
      .click();
    await page.getByRole("button", { name: "Sair", exact: true }).click();
    await expect(page).toHaveURL(/\/acesso$/);
    expect(
      (await page.request.get("/api/backend/operacao/acoes")).status(),
    ).toBe(401);
  });
}

test("recepção cadastra e encaminha sem acesso clínico", async ({
  page,
}, info) => {
  await login(page, "Recepção");
  await expect(
    page.getByRole("button", { name: /Campos clínicos/ }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("cell", { name: "Pessoa fictícia DEMO 03", exact: true }),
  ).toHaveCount(0);
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page
    .getByRole("button", { name: "Registrar beneficiário", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  const name = `Pessoa sintética recepção ${info.project.name}`;
  await dialog.getByRole("textbox", { name: "Nome", exact: true }).fill(name);
  await dialog
    .getByRole("combobox", { name: "Local da participação", exact: true })
    .click();
  await page.getByRole("option", { name: /Unidade fictícia Centro/ }).click();
  await dialog
    .getByRole("button", { name: "Salvar beneficiário", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await page
    .getByRole("button", { name: `Encaminhar ${name}`, exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByLabel("Profissional responsável", { exact: true })
    .click();
  await page
    .getByRole("option", { name: "Oftalmologista fictício DEMO", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Salvar encaminhamento", exact: true })
    .click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  const actionId = page.url().split("/").at(-1);
  const people = await (
    await page.request.get(
      `/api/backend/operacao/acoes/${actionId}/beneficiarios`,
    )
  ).json();
  const target = people.items.find(
    (person: { nome: string }) => person.nome === name,
  );
  expect(
    (
      await page.request.get(
        `/api/backend/operacao/acoes/${actionId}/beneficiarios/${target.id}/clinica`,
      )
    ).status(),
  ).toBe(403);
  await page.screenshot({
    path: `artifacts/operational-reception-${info.project.name}.png`,
    fullPage: true,
  });
  await page.getByRole("button", { name: "Sair", exact: true }).click();
  await expect(page).toHaveURL(/\/acesso$/);
});

test("Administração gerencia acesso individual com confirmação de senha", async ({
  page,
}) => {
  await page.goto("/login");
  await page
    .getByRole("button", {
      name: "Preencher acesso de Administração",
      exact: true,
    })
    .click();
  await page
    .getByRole("button", { name: "Acessar plataforma", exact: true })
    .click();
  await expect(page).toHaveURL(/dashboard/);
  await page.goto("/profissionais");
  await page
    .getByRole("button", {
      name: "Gerenciar acesso de Recepcionista fictício DEMO",
      exact: true,
    })
    .click();
  const dialog = page.getByRole("dialog");
  await expect(
    dialog.getByRole("textbox", { name: "Usuário de acesso", exact: true }),
  ).toHaveValue("recepcao.demo");
  await dialog
    .getByLabel("Nova senha (opcional)", { exact: true })
    .fill("Demonstracao-local-2026!");
  await dialog
    .getByLabel("Sua senha institucional", { exact: false })
    .fill("Demonstracao-local-2026!");
  await dialog
    .getByRole("button", { name: "Salvar acesso", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await page.goto("/acoes");
  await page
    .getByRole("link", {
      name: "Visualizar DEMO — Saúde ocular em João Pessoa",
      exact: true,
    })
    .click();
  await page
    .getByRole("button", {
      name: "Designar atendimento de Pessoa fictícia DEMO 04",
      exact: true,
    })
    .click();
  await page
    .getByRole("dialog")
    .getByLabel("Profissional responsável pelo atendimento", { exact: true })
    .click();
  await page
    .getByRole("option", { name: "Oftalmologista fictício DEMO", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Salvar designação", exact: true })
    .click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
});
