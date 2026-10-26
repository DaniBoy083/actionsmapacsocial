import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function login(page: Page, admin = false) {
  await page.goto("/login");
  await page
    .getByLabel("E-mail", { exact: true })
    .fill(admin ? "admin@example.invalid" : "test@example.invalid");
  await page.getByLabel("Senha", { exact: true }).fill("Somente-teste-2026");
  await page.getByRole("button", { name: "Acessar plataforma" }).click();
  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByRole("heading", { name: /Olá/ })).toBeVisible();
}

test("acessibilidade automatizada do login, painel e modal", async ({
  page,
}) => {
  await page.goto("/login");
  let result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(result.violations).toEqual([]);
  await login(page);
  result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(result.violations).toEqual([]);
  await page.goto("/acoes");
  await page
    .getByRole("button", { name: "Cadastrar nova ação", exact: true })
    .first()
    .click();
  result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(result.violations).toEqual([]);
});

test("acesso institucional e página não encontrada", async ({
  page,
}, testInfo) => {
  await page.goto("/acoes");
  await expect(page).toHaveURL(/login/);
  await expect(page.getByRole("textbox")).toHaveCount(2);
  await expect(page.getByRole("combobox")).toHaveCount(0);
  await page.getByRole("button", { name: "Acessar plataforma" }).click();
  await expect(page.getByText("Informe um e-mail válido.")).toBeVisible();
  await page.screenshot({
    path: `artifacts/login-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await page.goto("/endereco-inexistente");
  await expect(
    page.getByRole("heading", { name: "Página não encontrada" }),
  ).toBeVisible();
});

test("cadastrar, editar, registrar beneficiário e arquivar ação com vários locais", async ({
  page,
}, testInfo) => {
  await login(page);
  await page.goto("/acoes");
  const name = `Ação ${testInfo.project.name} ${Date.now()}`;
  await page
    .getByRole("button", { name: "Cadastrar nova ação", exact: true })
    .first()
    .click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Nome da ação", { exact: false }).fill(name);
  await dialog.getByLabel("Município do local 1").click();
  await page.getByRole("option", { name: "João Pessoa", exact: true }).click();
  await dialog.getByLabel("Nome do local 1").fill("Unidade A");
  await dialog.getByRole("button", { name: "Adicionar local" }).click();
  await dialog.getByLabel("Município do local 2").click();
  await page
    .getByRole("option", { name: "Campina Grande", exact: true })
    .click();
  await dialog.getByRole("button", { name: "Salvar rascunho" }).click();
  await expect(dialog).not.toBeVisible();
  await page.getByLabel("Buscar por nome").fill(name);
  await expect(page.getByRole("row").filter({ hasText: name })).toBeVisible();
  await page.screenshot({
    path: `artifacts/actions-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await page
    .getByRole("button", { name: `Editar ${name}`, exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByLabel("Nome da ação", { exact: false })
    .fill(name + " revisada");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Salvar rascunho" })
    .click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await page
    .getByRole("link", { name: `Visualizar ${name} revisada`, exact: true })
    .click();
  await page
    .getByRole("button", { name: "Registrar beneficiário", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByLabel("Nome", { exact: false })
    .fill("Pessoa Sintética");
  await page.getByRole("button", { name: "Salvar beneficiário" }).click();
  await expect(
    page.getByRole("cell", { name: "Pessoa Sintética" }),
  ).toBeVisible();
  await page.goto("/acoes");
  await page.getByLabel("Buscar por nome").fill(name);
  await page
    .getByRole("button", { name: `Arquivar ${name} revisada`, exact: true })
    .click();
  await page.getByRole("button", { name: "Confirmar arquivamento" }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(
    page.getByRole("row").filter({ hasText: name }).getByText("Arquivada"),
  ).toBeVisible();
});

test("Administração não acessa diagnóstico técnico", async ({ page }) => {
  await login(page, true);
  await page.goto("/tecnologia/conexao");
  await expect(
    page.getByText(
      "Sem permissão. Esta página é exclusiva da equipe Tecnologia.",
    ),
  ).toBeVisible();
  expect(
    await page.evaluate(
      async () => (await fetch("/api/backend/tecnologia/saude")).status,
    ),
  ).toBe(403);
});

test("dados iniciais: prévia privada, revisão e importação idempotente", async ({
  page,
}, testInfo) => {
  await login(page);
  const destinationName = `Destino ${testInfo.project.name} ${Date.now()}`;
  const created = await page.evaluate(async (destinationName) => {
    const session = await (await fetch("/api/backend/auth/me")).json();
    return (
      await (
        await fetch("/api/backend/acoes", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": session.csrf_token,
          },
          body: JSON.stringify({
            nome: destinationName,
            locais: [{ municipio_ibge: "2507507", nome_local: "" }],
          }),
        })
      ).json()
    ).id;
  }, destinationName);
  await page.goto("/dados-iniciais");
  await page
    .getByRole("button", { name: "Preparar documento histórico" })
    .click();
  await expect(page.getByRole("heading", { name: /2 páginas/ })).toBeVisible();
  await expect(
    page.getByRole("img", { name: /Ficha histórica/ }),
  ).toBeVisible();
  await page.getByLabel("Ação de destino").click();
  await page
    .getByRole("option", { name: destinationName, exact: true })
    .click();
  await page
    .getByLabel("Nome conferido no documento")
    .fill("Pessoa de teste 1");
  await page.getByRole("button", { name: "Revisar correspondência" }).click();
  await expect(
    page.getByRole("button", { name: "Confirmar importação local" }),
  ).toBeDisabled();
  await page.getByRole("checkbox").check();
  await page
    .getByRole("button", { name: "Confirmar importação local" })
    .click();
  await expect(page.getByText(/1 registro incluído/)).toBeVisible();
  await page.goto(`/acoes/${created}`);
  await expect(
    page.getByRole("cell", { name: "Pessoa de teste 1" }),
  ).toBeVisible();
});
