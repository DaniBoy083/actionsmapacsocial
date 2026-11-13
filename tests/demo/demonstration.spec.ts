import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { execFileSync } from "node:child_process";

test("apresentação sintética, acesso restrito e segunda via identificada", async ({
  page,
}, testInfo) => {
  await page.goto("/login");
  await expect(
    page.getByText("Demonstração · dados fictícios", { exact: true }),
  ).toBeVisible();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page
    .getByRole("button", {
      name: "Preencher acesso de Administração",
      exact: true,
    })
    .click();
  await expect(page.getByLabel("E-mail", { exact: true })).toHaveValue(
    "admin@demo.invalid",
  );
  await page
    .getByRole("button", { name: "Acessar plataforma", exact: true })
    .click();
  await expect(page).toHaveURL(/dashboard/);
  await expect(
    page.getByRole("complementary", { name: "Modo de demonstração" }),
  ).toBeVisible();
  expect(
    (await page.request.get("/api/backend/tecnologia/saude")).status(),
  ).toBe(403);
  expect(
    (
      await page.request.get("/api/integracoes/v1/acoes/resumos", {
        headers: {
          Authorization: `Bearer acm_${"a".repeat(32)}_${"b".repeat(43)}`,
        },
      })
    ).status(),
  ).toBe(403);
  await page.screenshot({
    path: `artifacts/demo-${testInfo.project.name}-dashboard.png`,
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.goto("/acoes");
  await page
    .getByRole("link", {
      name: "Visualizar DEMO — Saúde ocular em João Pessoa",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "DEMO — Saúde ocular em João Pessoa",
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("button", {
      name: "Emitir segunda via de Pessoa fictícia DEMO 01",
      exact: true,
    })
    .click();
  const sheet = page.locator("[data-beneficiary-print]");
  await expect(sheet).toContainText(
    "DEMONSTRAÇÃO — DADOS FICTÍCIOS — SEM VALIDADE CLÍNICA",
  );
  await expect(
    page.getByRole("button", { name: "Imprimir segunda via", exact: true }),
  ).toBeEnabled();
  await page.emulateMedia({ media: "print" });
  await page.pdf({
    path: `artifacts/demo-${testInfo.project.name}-segunda-via.pdf`,
    format: "A4",
    printBackground: true,
  });
  execFileSync("backend/.venv/Scripts/python.exe", [
    "-c",
    "import pymupdf,sys; d=pymupdf.open(sys.argv[1]); assert len(d)==1; assert 'DADOS FICT' in d[0].get_text()",
    `artifacts/demo-${testInfo.project.name}-segunda-via.pdf`,
  ]);
  await page.screenshot({
    path: `artifacts/demo-${testInfo.project.name}-print.png`,
    fullPage: true,
  });
  await page.emulateMedia({ media: "screen" });
  await page.getByRole("button", { name: "Fechar", exact: true }).click();
  await page.getByRole("button", { name: "Sair", exact: true }).click();
  await expect(page).toHaveURL(/login/);
  expect((await page.request.get("/api/backend/acoes")).status()).toBe(401);
});
