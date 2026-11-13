import { expect, type Locator, type Page } from "@playwright/test";

export const institutionalFixture = {
  contratantes: [{ nome: "Contratante E2E sintético", tipo: "OUTRO" }],
  apoiadores: [
    { nome: "Apoiador E2E sintético", tipo: "OUTRO", modalidade: "PARCIAL" },
  ],
};

export async function fillInstitutionalLinks(page: Page, form: Locator) {
  await form
    .getByRole("textbox", { name: "Instituição contratante 1", exact: false })
    .fill("Contratante E2E sintético");
  await form
    .getByRole("textbox", { name: "Instituição apoiador 1", exact: false })
    .fill("Apoiador E2E sintético");
  await form.getByLabel("Modalidade de apoio 1", { exact: false }).click();
  await page
    .getByRole("option", { name: "Parcial", exact: true })
    .press("Enter");
  await expect(page.getByRole("listbox")).toHaveCount(0);
  await expect(
    form.getByRole("combobox", { name: "Modalidade de apoio 1", exact: false }),
  ).toContainText("Parcial");
}
