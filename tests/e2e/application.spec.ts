import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import path from "node:path";

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

test("login recusado informa credenciais inválidas sem alegar sessão expirada", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("E-mail", { exact: true }).fill("test@example.invalid");
  await page
    .getByLabel("Senha", { exact: true })
    .fill("senha-incorreta-sintetica");
  await page.getByRole("button", { name: "Acessar plataforma" }).click();
  await expect(
    page
      .getByRole("region", { name: "Entrar na plataforma" })
      .getByRole("alert"),
  ).toHaveText("Não foi possível entrar com essas credenciais.");
  await expect(
    page.getByText("Sua sessão expirou. Entre novamente."),
  ).toHaveCount(0);
});

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
  await page.evaluate(async () => {
    await Promise.all(
      document
        .getAnimations()
        .filter(
          (animation) => animation.effect?.getTiming().iterations !== Infinity,
        )
        .map((animation) => animation.finished.catch(() => {})),
    );
  });
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
  await dialog.getByRole("button", { name: "Salvar ação" }).click();
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
    .getByRole("button", { name: "Salvar ação" })
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

async function createDestination(page: Page, name: string) {
  return page.evaluate(async (name) => {
    const session = await (await fetch("/api/backend/auth/me")).json();
    const response = await fetch("/api/backend/acoes", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": session.csrf_token,
      },
      body: JSON.stringify({
        nome: name,
        locais: [{ municipio_ibge: "2508901" }],
      }),
    });
    return (await response.json()).id;
  }, name);
}

test("CSV enviado exige revisão, preserva conferência e registra na ação", async ({
  page,
}, testInfo) => {
  await login(page);
  const name = `Arquivo ${testInfo.project.name} ${Date.now()}`;
  const identifier = await createDestination(page, name);
  await page.goto("/dados-iniciais");
  await expect(page).toHaveURL(/\/importacoes$/);
  await expect(
    page.getByLabel("Selecionar arquivo PDF, CSV ou JSON"),
  ).toBeEnabled();
  await expect(
    page.getByRole("link", { name: "Indicadores", exact: true }),
  ).toHaveCount(0);
  await page.getByLabel("Selecionar arquivo PDF, CSV ou JSON").setInputFiles({
    name: "sintetico.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      "nome;municipio_residencia_ibge\nPessoa de teste por arquivo;2508901\nOutra pessoa de teste;\n",
    ),
  });
  await page.getByRole("button", { name: "Analisar arquivo" }).click();
  await expect(
    page.getByRole("heading", { name: "CSV · 2 registros" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Revisar lote (0)" }),
  ).toBeDisabled();
  await page
    .getByRole("combobox", { name: "Ação de destino", exact: true })
    .click();
  await page.getByRole("option", { name, exact: true }).click();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Próximo", exact: true }).click();
  await page.getByRole("button", { name: "Anterior", exact: true }).click();
  await expect(page.getByRole("checkbox")).toBeChecked();
  await expect(page.getByLabel("Nome conferido no documento")).toHaveValue(
    "Pessoa de teste por arquivo",
  );
  await page.getByRole("button", { name: "Revisar lote (1)" }).click();
  await expect(page.getByRole("table")).toContainText(
    "Pessoa de teste por arquivo",
  );
  await page
    .getByRole("button", { name: "Confirmar importação", exact: true })
    .click();
  await expect(page.getByText(/1 registro\(s\) incluído\(s\)/)).toBeVisible();
  await page.goto(`/acoes/${identifier}`);
  await expect(
    page.getByRole("cell", { name: "Pessoa de teste por arquivo" }),
  ).toBeVisible();
  await page.goto("/indicadores");
  await expect(
    page.getByRole("heading", { name: "Página não encontrada" }),
  ).toBeVisible();
});

test("PDF binário enviado permite prévia privada, rotação e revisão", async ({
  page,
}, testInfo) => {
  await login(page);
  await page.goto("/importacoes");
  await expect(
    page.getByLabel("Selecionar arquivo PDF, CSV ou JSON"),
  ).toBeEnabled();
  await page
    .getByLabel("Selecionar arquivo PDF, CSV ou JSON")
    .setInputFiles(path.resolve("tmp/e2e-import.pdf"));
  await page.getByRole("button", { name: "Analisar arquivo" }).click();
  await expect(
    page.getByRole("heading", { name: "PDF · 2 páginas" }),
  ).toBeVisible();
  const image = page.getByRole("img", { name: "Documento enviado, página 1" });
  await expect
    .poll(async () =>
      image.evaluate((img) => (img as HTMLImageElement).naturalWidth),
    )
    .toBeGreaterThan(0);
  await page.getByRole("button", { name: "Girar página" }).click();
  await expect(image).toHaveAttribute("src", /rotacao=90/);
  await expect
    .poll(async () =>
      image.evaluate((img) => (img as HTMLImageElement).naturalWidth),
    )
    .toBeGreaterThan(0);
  await page
    .getByLabel("Nome conferido no documento")
    .fill("Pessoa sintética conferida");
  await page.getByRole("checkbox").check();
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(result.violations).toEqual([]);
  await page.screenshot({
    path: `artifacts/importacao-${testInfo.project.name}.png`,
    fullPage: true,
  });
});
