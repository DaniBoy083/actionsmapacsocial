import { test, expect, type Page, type BrowserContext } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

let sessionCookies: Awaited<ReturnType<BrowserContext["cookies"]>> | undefined;

async function login(page: Page) {
  if (sessionCookies) {
    await page.context().addCookies(sessionCookies);
    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: /Olá/ })).toBeVisible();
    return;
  }
  await page.goto("/login");
  await page
    .getByLabel("E-mail", { exact: true })
    .fill("admin@example.invalid");
  await page.getByLabel("Senha", { exact: true }).fill("Somente-teste-2026");
  await page.getByRole("button", { name: "Acessar plataforma" }).click();
  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByRole("heading", { name: /Olá/ })).toBeVisible();
  sessionCookies = await page.context().cookies();
}

function projection(empty = false, lifetime = 900_000) {
  const captured = new Date().toISOString();
  return {
    status: empty ? "empty" : "available",
    checked_at: captured,
    refresh_after_seconds: 60,
    generation: "9007199254740993",
    captured_at: captured,
    expires_at: new Date(Date.now() + lifetime).toISOString(),
    summary: {
      action_count: empty ? 0 : 2,
      participation_count: empty ? 0 : 21,
      people_count: empty ? 0 : 17,
      municipality_count: empty ? 0 : 2,
      undated_action_count: empty ? 0 : 1,
      unallocated: {
        action_count: empty ? 0 : 1,
        participation_count: empty ? 0 : 9,
        people_count: empty ? 0 : 7,
      },
    },
    municipalities: empty
      ? []
      : [
          {
            code: "2503209",
            name: "Cabedelo",
            action_count: 1,
            unallocated_action_count: 1,
            single_municipality_people: 0,
            single_municipality_participations: 0,
          },
          {
            code: "2507507",
            name: "João Pessoa",
            action_count: 2,
            unallocated_action_count: 1,
            single_municipality_people: 10,
            single_municipality_participations: 12,
          },
        ],
  };
}

test("mapa exige sessão no servidor e informa configuração ausente", async ({
  page,
  request,
}) => {
  const unauthenticated = await request.get("/api/backend/mapa-acoes");
  expect(unauthenticated.status()).toBe(401);
  expect(unauthenticated.headers()["cache-control"]).toBe("no-store");
  await page.goto("/mapa-acoes");
  await expect(page).toHaveURL(/login/);
  await login(page);
  await page.goto("/mapa-acoes");
  await expect(page.getByRole("status")).toContainText(
    "ainda não foi configurada",
  );
  await expect(page.locator("svg path[role=button]")).toHaveCount(0);
});

test("mapa municipal, totais sem duplicação, teclado, busca e acessibilidade", async ({
  page,
}, testInfo) => {
  await login(page);
  await page.route("**/api/backend/mapa-acoes", (route) =>
    route.fulfill({ json: projection() }),
  );
  await page.goto("/mapa-acoes");
  const map = page.getByRole("group", {
    name: "Presença nos municípios da Paraíba",
  });
  await expect(map.locator("path")).toHaveCount(223);
  await expect(page.locator(".published-map-legend")).toHaveCSS(
    "display",
    "flex",
  );
  await expect(page.locator(".published-map-legend i").first()).toHaveCSS(
    "width",
    "18px",
  );
  const totals = page.locator('[aria-label="Totais globais da Plataforma"]');
  await expect(totals).toContainText("2Ações");
  await expect(totals).toContainText("17Pessoas contempladas nas ações");
  const marker = map.getByRole("button", {
    name: "João Pessoa: 2 ações nesta exportação",
    exact: true,
  });
  await marker.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#municipality-details")).toBeFocused();
  await expect(page.locator("#municipality-details")).toContainText(
    "10 pessoas e 12 participações",
  );
  await page.getByLabel("Buscar município").fill("joao");
  await expect(page.getByRole("table").getByRole("row")).toHaveCount(2);
  await expect(totals).toContainText("2Ações");
  await page.getByLabel("Buscar município").fill("inexistente");
  await expect(
    page.getByText("Nenhum município corresponde à busca."),
  ).toBeVisible();
  await page.getByLabel("Buscar município").clear();
  await page.getByLabel("Selecionar município").click();
  await page.getByRole("option", { name: "Aguiar", exact: true }).click();
  await expect(page.locator("#municipality-details")).toContainText(
    "não comprova ausência histórica",
  );
  await expect(page.getByRole("listbox")).toHaveCount(0);
  const axe = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(axe.violations).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page
    .getByRole("heading", { name: "Mapa de ações", exact: true })
    .click();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: `artifacts/published-map-${testInfo.project.name}.png`,
    fullPage: true,
  });
});

test("paginação permanece válida quando uma atualização reduz os municípios", async ({
  page,
}) => {
  await login(page);
  let result = projection();
  result.municipalities.push(
    ...[
      ["2500205", "Aguiar"],
      ["2500304", "Alagoa Grande"],
      ["2500403", "Alagoa Nova"],
      ["2500502", "Alagoinha"],
    ].map(([code, name]) => ({
      code,
      name,
      action_count: 1,
      unallocated_action_count: 0,
      single_municipality_people: 0,
      single_municipality_participations: 0,
    })),
  );
  result.summary.action_count = 6;
  result.summary.municipality_count = 6;
  await page.route("**/api/backend/mapa-acoes", (route) =>
    route.fulfill({ json: result }),
  );
  await page.goto("/mapa-acoes");
  await page.getByRole("button", { name: "Go to page 2" }).click();
  await expect(page.getByRole("table").getByRole("row")).toHaveCount(2);
  result = projection();
  result.generation = "9007199254740994";
  await page.getByRole("button", { name: "Atualizar mapa" }).click();
  await expect(page.getByRole("table").getByRole("row")).toHaveCount(3);
  await page.setViewportSize({ width: 320, height: 900 });
  await expect
    .poll(() =>
      page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    )
    .toBeTruthy();
});

test("falha remove dados antigos, vazio comprovado é distinto de erro e geração antiga é recusada", async ({
  page,
}) => {
  await login(page);
  let result = projection();
  let fail = false;
  await page.route("**/api/backend/mapa-acoes", (route) =>
    fail
      ? route.fulfill({ status: 503, json: { detail: "Indisponível" } })
      : route.fulfill({ json: result }),
  );
  await page.goto("/mapa-acoes");
  await expect(page.getByRole("table")).toBeVisible();
  fail = true;
  await page.getByRole("button", { name: "Atualizar mapa" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Não foi possível atualizar",
  );
  await expect(page.getByRole("table")).toHaveCount(0);
  fail = false;
  result = projection(true);
  result.generation = "9007199254740994";
  await page.getByRole("button", { name: "Atualizar mapa" }).click();
  await expect(
    page.getByText("A exportação válida não contém ações publicadas."),
  ).toBeVisible();
  result = projection();
  await page.getByRole("button", { name: "Atualizar mapa" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Não foi possível atualizar",
  );
  await expect(page.getByRole("table")).toHaveCount(0);
});

test("expiração retira o mapa mesmo sem nova consulta", async ({ page }) => {
  await login(page);
  await page.route("**/api/backend/mapa-acoes", (route) =>
    route.fulfill({ json: projection(false, 4000) }),
  );
  await page.goto("/mapa-acoes");
  await expect(page.getByRole("table")).toBeVisible();
  await expect(page.getByRole("status")).toContainText(
    "A validade dos dados terminou",
    { timeout: 10_000 },
  );
  await expect(page.getByRole("table")).toHaveCount(0);
});
