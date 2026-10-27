import { defineConfig, devices } from "@playwright/test";
const frontendPort = process.env.ACTIONS_E2E_FRONTEND_PORT || "3310";
const backendPort = process.env.ACTIONS_E2E_BACKEND_PORT || "8310";
for (const port of [frontendPort, backendPort]) {
  if (!/^\d{4,5}$/.test(port) || Number(port) > 65535)
    throw new Error("Porta E2E inválida.");
}
const frontend = `http://localhost:${frontendPort}`;
const backend = `http://127.0.0.1:${backendPort}`;
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  reporter: [["list"], ["json", { outputFile: "artifacts/e2e-results.json" }]],
  use: {
    baseURL: frontend,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" },
    },
  ],
  webServer: [
    {
      command:
        "backend\\.venv\\Scripts\\python.exe backend/tests/browser_server.py",
      url: `${backend}/api/v1/health`,
      env: {
        ACTIONS_E2E_FRONTEND_PORT: frontendPort,
        ACTIONS_E2E_BACKEND_PORT: backendPort,
      },
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: `node node_modules/next/dist/bin/next start --port ${frontendPort}`,
      url: `${frontend}/login`,
      env: {
        ACTIONS_API_URL: backend,
        NEXT_TELEMETRY_DISABLED: "1",
      },
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
